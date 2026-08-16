"""Flattened, transition-driven generation.

The original pipeline emits one *layer* per call: all the plots at once, all the
entities at once. This module emits one *node* per call, and puts a deliberate
reasoning transition in front of every one of them:

    story_root
      └─ transition → expose
           └─ transition → pl-01
                └─ transition → pl-02
                     └─ transition → ch-01
                          └─ … → ev-001 → ev-002 → …

Each node is generated in two calls:

  1. TRANSITION — reads the whole graph so far and reasons its way to what must
     come next, filling the schema in `transitions.py`. This is the artifact the
     corpus is actually for.
  2. NODE — generated *from the transition*, so the node is provably a
     consequence of stated reasoning rather than of a private scratchpad.

Splitting the two costs an extra call per node and is worth it: it makes the
reasoning auditable, it makes (state, transition, node) a clean supervised
triple, and it lets a bad transition be caught before it contaminates a node.

Entity dossiers may additionally be built in passes (`--entity-passes`), each
pass with its own transition, so the deep interior of a major character is
reasoned into place rather than emitted in one breath.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path

from . import jsonschema_mini, prompts, timeline, transitions as T, validate
from .backends import AwaitingAgent, Backend, BackendError
from .schemas import ENTITY_SCHEMA, EVENT_SCHEMA, PLOT_SCHEMA, SCHEMAS

# --------------------------------------------------------------------------
# Context assembly — what a node is allowed to see
# --------------------------------------------------------------------------

def _j(o, indent=1):
    return json.dumps(o, indent=indent, ensure_ascii=False)


def entity_digest(entities: dict) -> dict:
    """Entities compressed to what a downstream node actually needs."""
    return {
        eid: {
            "name": e.get("canonical_name"),
            "type": e.get("type"),
            "salience": e.get("salience"),
            "plots": e.get("plots"),
            "want": (e.get("profile") or {}).get("want"),
            "wound": (e.get("profile") or {}).get("wound"),
            "values": (e.get("profile") or {}).get("values"),
            "state_variables": {
                k: {"kind": v.get("kind"), "dimension": v.get("dimension"),
                    "init": v.get("init"),
                    **({"range": v["range"]} if "range" in v else {}),
                    **({"domain": v["domain"]} if "domain" in v else {})}
                for k, v in (e.get("state_variables") or {}).items()
            },
            "arc": e.get("arc"),
        }
        for eid, e in entities.items()
    }


def event_digest(events: dict) -> dict:
    return {
        eid: {
            "t": (e.get("story_time") or {}).get("index"),
            "label": (e.get("story_time") or {}).get("label"),
            "primary_plot": e.get("primary_plot"),
            "plots": e.get("plots"),
            "bindings": e.get("plot_bindings"),
            "summary": e.get("summary"),
            "participants": e.get("participants"),
            "location": e.get("location"),
            "state_changes": [
                {"entity": c.get("entity"), "variable": c.get("variable"),
                 "before": c.get("before"), "after": c.get("after")}
                for c in (e.get("state_changes") or [])
            ],
            "caused_by": e.get("caused_by"), "causes": e.get("causes"),
        }
        for eid, e in events.items()
    }


def live_state(entities: dict, events: dict) -> dict:
    """Entity states after every event generated so far."""
    if not events:
        return {eid: (e.get("state") or {}) for eid, e in entities.items()}
    state = {eid: dict(e.get("state") or {}) for eid, e in entities.items()}
    for eid in sorted(events, key=lambda x: (events[x].get("story_time") or {}).get("index", 0)):
        for c in events[eid].get("state_changes") or []:
            if c.get("entity") in state and c.get("variable"):
                state[c["entity"]][c["variable"]] = c.get("after")
    return state


# --------------------------------------------------------------------------
# The work plan
# --------------------------------------------------------------------------

@dataclass
class NodeTask:
    kind: str          # story_root | expose | plot | entity | event
    node_id: str
    ordinal: int
    brief: str = ""    # what this specific node is for
    passes: int = 1

    @property
    def tag(self) -> str:
        return f"{self.kind}.{self.node_id}"


def plan_nodes(root: dict, plots_doc: dict | None, entities_doc: dict | None,
               *, entity_passes: int = 1) -> list[NodeTask]:
    """The flattened order in which nodes are produced."""
    tasks: list[NodeTask] = []
    c = root.get("constraints") or {}

    n_plots = c.get("plot_count") or 2
    for i in range(1, n_plots + 1):
        tasks.append(NodeTask("plot", f"pl-{i:02d}", i))

    if plots_doc:
        # Entities are whatever the plots forward-declared, plus the ones the
        # plots imply. The declared ones are known; the rest are planned by the
        # cast-planning step at run time.
        declared: list[str] = []
        for p in plots_doc.get("plots", []):
            for ref in (p.get("agent") or []) + (p.get("resistance") or []):
                if not ref.startswith("pl-") and ref not in declared:
                    declared.append(ref)
        for i, eid in enumerate(sorted(declared), start=1):
            tasks.append(NodeTask("entity", eid, i, passes=entity_passes))

    if entities_doc:
        n_events = c.get("event_count_target") or 12
        for i in range(1, n_events + 1):
            tasks.append(NodeTask("event", f"ev-{i:03d}", i))

    return tasks


# --------------------------------------------------------------------------
# Prompts for the two calls
# --------------------------------------------------------------------------

TRANSITION_SYSTEM = """\
You are a narrative architect, and your reasoning is the product.

You are building a story one node at a time. Before each node you write a
TRANSITION: a deliberate, fully externalized reasoning trace that argues from
everything already established to the node that must come next.

A transition is not a summary of thinking you did somewhere else. It IS the
thinking, put on the page on purpose, to be read by other people and used as
training data. Write so that a reader can reconstruct your judgement without
access to you.

WHAT EVERY TRANSITION MUST DO

1. CRAFT FIRST. Before any psychology, say what the declared target audience
   needs here, what the genre leads a reader to expect, what the theme and
   register demand, what dramatic function this node performs, why it happens
   now and could not have happened earlier, and which alternatives you rejected
   and why. A choice with no rejected alternative was not a choice.

2. A FULL PSYCHOLOGICAL ACCOUNT for every character or creature materially
   involved:
   - Perception across all seven channels, as THAT entity has it. Two people in
     one room do not perceive the same room. Say what they fail to notice.
   - Appraisal against that character's own declared values, with the
     self-conscious emotion named precisely and the somatic marker it produces
     before any thought arrives.
   - The social norms actually in force here, how the people present would
     judge the act, how the absent audience (the village, the dead, the
     institution) still constrains it, and which norm wins when two conflict.
   - THEORY OF MIND TO THREE DEGREES, for each other entity that matters, in
     both directions: what A believes about B; what A believes B believes about
     A; what A believes B believes A believes. Then say where that model is
     WRONG and what the error will cost. A theory of mind that is always
     accurate produces no drama.
   - Urges: cravings, physical needs, conscious psychological needs, and the
     unconscious ones the character would deny.
   - Impairments acting from outside the will: physical, medical, magical,
     chemical, coercive, cognitive — and their net effect on what this
     character is capable of here.
   - Deliberate analysis: how the problem has been framed (usually where the
     real error is), the options weighed with predicted outcomes and costs, the
     reasoning in this character's own idiom — a smith reasons in weights and
     heat, not in abstractions.
   - Control: what is FELT, what is EXPRESSED, why they diverge, and what leaks
     through the control anyway. Another character can only read the leakage.
   - Intention, then the action actually taken.

3. TRAJECTORY, NOT SNAPSHOT. A node spans time. Nobody is the same at the end
   of an event as at its start. Give the phases each entity moves through
   inside this unit, each with the specific perceivable trigger that causes the
   shift. At least two phases per character; an entity identical at the end did
   not participate.

4. THE ENTITIES THAT ARE NOT MINDS. Objects, locations, groups and concepts
   have states and trajectories too. What forces act on them here; which axes
   move (custody, control, cohesion, credence, condition, meaning); how they
   change in phases; and what the thing MEANS to the characters afterwards that
   it did not mean before. An object whose meaning never moves is set dressing.

5. CONTINUITY. Cite your sources: every established fact you rely on names the
   node id or JSON pointer it came from. Name the world rules and standing
   notes you had to obey. Name the contradictions this node could plausibly
   have introduced and say how you avoided them.

6. THE SPECIMEN EXCHANGE. Before you commit, draft six to ten lines of the
   ACTUAL DIALOGUE at the moment you have called the turning point — real lines
   as they would be spoken, each with its subtext. Then read them back cold and
   check every risk you listed against them: does the exchange actually avoid
   that risk, and which line proves it?

   Everything above this point is unfalsifiable until somebody speaks. An
   immaculate analysis and a dead scene look identical on paper, and this is the
   only cheap way to tell them apart. If the two speakers could swap lines
   without anyone noticing, say so and fix it — that failure is invisible from
   inside and obvious from outside.

7. AT LEAST ONE REJECTED ALTERNATIVE MUST HAVE BEEN CLOSE. If every option you
   list loses by a mile, you did not decide — you narrated a decision already
   made. Mark the close one and say what single fact would have flipped it.

Be specific to THIS story. Generic psychology is the failure mode — if a
sentence could appear in a transition for a different story, delete it and
write the one that could not.

Return one JSON document conforming to the schema. No prose outside it."""


NODE_SYSTEM = prompts.SYSTEM + """

ADDITIONAL RULE FOR THIS MODE

You are given a TRANSITION: the reasoning that has already been done for this
node. The node you produce must be the faithful consequence of it. Where the
transition names a state change, the node records that change. Where the
transition names an action, the node contains it. You are not re-deciding — you
are rendering a decision that has been made, into the schema.

If the transition and the schema genuinely conflict, follow the schema and keep
as much of the transition's substance as the schema permits."""


def transition_prompt(task: NodeTask, ctx: dict, pass_no: int = 1, pass_of: int = 1) -> str:
    kind_brief = {
        "plot": """\
You are about to write PLOT {id}. A plot is a chain of cause and effect in which
an agent pursues an outcome against resistance, terminating in success, failure,
or transformation of the goal. It is not a theme and not a character.

Reason about: which agent, which goal, what resists it, what is at stake, and
the ordered spine of steps. Where a step of this plot must be caused by a step
of an already-written plot, say so and say why the two genuinely constrain each
other — competing for the same person, the same hour, the same resource.

The psychology blocks here should cover the agent and the principal resistance
as they stand ACROSS the whole plot: not one moment, but the arc — where each
begins, what changes them, where each ends. Trajectory phases are plot stages.""",
        "entity": """\
You are about to write the dossier for ENTITY {id}.

Reason about who or what this is, what the plots need it to be, and — most
importantly — which state variables it must declare. A variable nothing ever
changes is dead weight; a change with no variable to land on will block the
event layer later. Look at the plot spines and ask, for each step, what is
different afterwards and in whom.

For a character or creature: give the full psychological account as this entity
stands AT THE OPENING OF THE STORY, and let the trajectory phases be the arc it
will travel across the whole work.

For a location, object, group or concept: the psychology array may be empty, but
the dynamics array must not be. Reason about what it is, who controls it, what
it permits and forbids, and how it will change hands or meaning.""",
        "event": """\
You are about to write EVENT {id}.

An event happens at a locatable point in story time and changes at least one
declared state variable of at least one entity. Reason about which plot step is
due, who is present, what collides, and what is different afterwards.

The trajectory matters especially here: an event has duration. Give the phases
the participants move through inside it, each with its perceivable trigger.
The state changes you name in `decision.state_changes_implied` become the
event's declared changes, so their `before` values must be the values those
variables actually hold right now — read them off the live state given below.""",
        "expose": """\
You are about to write the EXPOSÉ.

Decide the ending FIRST — how it ends, what the resolution costs, what the final
image is — and only then reason forward to the synopsis. A synopsis written
front-to-back degrades into "and then, and then"; one written toward a known
ending has a spine.

The psychology blocks should cover the principal figures as the whole story will
treat them, with trajectory phases spanning the entire work.""",
    }.get(task.kind, "Reason your way to the next node.")

    pass_note = ""
    if pass_of > 1:
        stages = {
            1: "PASS 1 of {n}: the outward and the physical. Demographics, appearance, "
               "voice and speech, habits and tells, competences, limitations, health. "
               "What anyone meeting this entity would observe in an hour.",
            2: "PASS 2 of {n}: the interior and the history. Backstory decomposed one "
               "sentence per key, wound, want, need, values, fears, moral axis, "
               "problem-solving style, coping strategies. Reason about how the outward "
               "facts already fixed in pass 1 are produced by this history.",
            3: "PASS 3 of {n}: the machinery. State variables and their initial values, "
               "relationships with valences, the arc. Reason about what must be able to "
               "MOVE in this entity for the plots to be possible at all.",
        }
        pass_note = "\n\n" + stages.get(pass_no, "PASS {p} of {n}.").format(n=pass_of, p=pass_no) + \
            "\n\nWhat earlier passes established is given below and is FIXED. Do not " \
            "contradict it; build on it."

    return f"""\
TRANSITION → {task.node_id}   ({task.kind}, node {task.ordinal})

{kind_brief.format(id=task.node_id)}{pass_note}

═══════════════════════════════════════════════════════════════════════
EVERYTHING ESTABLISHED SO FAR
═══════════════════════════════════════════════════════════════════════

STORY ROOT
{_j(ctx.get('root'))}

EXPOSÉ
{_j(ctx.get('expose')) if ctx.get('expose') else '(not yet written)'}

PLOTS WRITTEN SO FAR
{_j(ctx.get('plots')) if ctx.get('plots') else '(none yet)'}

ENTITIES WRITTEN SO FAR
{_j(ctx.get('entities')) if ctx.get('entities') else '(none yet)'}

EVENTS WRITTEN SO FAR
{_j(ctx.get('events')) if ctx.get('events') else '(none yet)'}

LIVE STATE AT THIS POINT IN STORY TIME
{_j(ctx.get('live_state')) if ctx.get('live_state') else '(no state yet)'}

{ctx.get('extra', '')}

═══════════════════════════════════════════════════════════════════════

Produce the transition for {task.node_id} now. Fill every field the schema
requires. Depth is the point: a thin transition is a failed transition.

SCHEMA
{_j(T.TRANSITION_SCHEMA)}
"""


NODE_SCHEMAS = {
    "plot": {"type": "object", "properties": {"plot": PLOT_SCHEMA},
             "required": ["plot"], "additionalProperties": False},
    "entity": {"type": "object", "properties": {"entity": ENTITY_SCHEMA},
               "required": ["entity"], "additionalProperties": False},
    "event": {"type": "object", "properties": {"event": EVENT_SCHEMA},
              "required": ["event"], "additionalProperties": False},
}


def node_prompt(task: NodeTask, ctx: dict, transition: dict) -> str:
    key = {"plot": "plot", "entity": "entity", "event": "event"}[task.kind]
    return f"""\
NODE → {task.node_id}   ({task.kind})

The reasoning for this node has been done. Render it into the schema.

THE TRANSITION
{_j(transition)}

═══════════════════════════════════════════════════════════════════════
CONTEXT (for ids, spellings and consistency — the transition governs content)
═══════════════════════════════════════════════════════════════════════

STORY ROOT
{_j({k: ctx['root'].get(k) for k in ('title','form','language','genre_primary','audience','setting','pov','style','state_dimensions','constraints','keep_in_mind')})}

PLOTS SO FAR
{_j(ctx.get('plots')) if ctx.get('plots') else '(none)'}

ENTITIES SO FAR
{_j(ctx.get('entities')) if ctx.get('entities') else '(none)'}

EVENTS SO FAR
{_j(ctx.get('events')) if ctx.get('events') else '(none)'}

LIVE STATE
{_j(ctx.get('live_state')) if ctx.get('live_state') else '(none)'}

{ctx.get('extra', '')}

═══════════════════════════════════════════════════════════════════════

Return {{"{key}": {{...}}}} — one node, conforming to the schema.

Every state change you record must name a variable that the relevant entity's
dossier actually declares, and every `before` value must be the value that
variable holds right now according to the live state above.

SCHEMA
{_j(NODE_SCHEMAS[task.kind])}
"""


# --------------------------------------------------------------------------
# The generator
# --------------------------------------------------------------------------

@dataclass
class ForgeResult:
    nodes_written: list[str] = field(default_factory=list)
    transitions_written: list[str] = field(default_factory=list)
    scores: dict = field(default_factory=dict)
    pending: list[dict] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class Forge:
    """Node-at-a-time generation with reasoning transitions."""

    def __init__(self, project, backend: Backend, *, brief: str = "", options: dict | None = None,
                 entity_passes: int = 1, verbose: bool = True, max_repairs: int = 1):
        self.project = project
        self.backend = backend
        self.brief = brief
        self.options = options or {}
        self.entity_passes = entity_passes
        self.verbose = verbose
        self.max_repairs = max_repairs
        self.project.ensure()
        self.tdir = self.project.root / "transitions"
        self.tdir.mkdir(parents=True, exist_ok=True)

    def log(self, m):
        if self.verbose:
            print(m, flush=True)

    # -- storage -----------------------------------------------------------

    def _tpath(self, node_id, pass_no=1, of=1):
        return self.tdir / (f"{node_id}.json" if of == 1 else f"{node_id}.p{pass_no}.json")

    def load_transition(self, node_id, pass_no=1, of=1):
        p = self._tpath(node_id, pass_no, of)
        return json.loads(p.read_text()) if p.exists() else None

    def save_transition(self, node_id, doc, pass_no=1, of=1):
        self._tpath(node_id, pass_no, of).write_text(_j(doc) + "\n")

    # -- context -----------------------------------------------------------

    def context(self, upto_kind: str, upto_id: str | None = None) -> dict:
        p = self.project
        root = p.load("story_root") or {}
        expose = p.load("expose")
        plots_doc = p.load("plots") or {"plots": []}
        entities_doc = p.load("entities") or {"entities": {}}
        events_doc = p.load("events") or {"events": {}}

        entities = entities_doc.get("entities", {})
        events = events_doc.get("events", {})
        ctx = {
            "root": root,
            "expose": expose,
            "plots": plots_doc.get("plots") or None,
            "entities": entity_digest(entities) or None,
            "events": event_digest(events) or None,
            "live_state": live_state(entities, events) if entities else None,
        }
        return ctx

    # -- one node ----------------------------------------------------------

    def forge_node(self, task: NodeTask, result: ForgeResult) -> None:
        existing = self._existing_node(task)
        if existing is not None:
            self.log(f"  · {task.node_id:<9} present, skipping")
            return

        ctx = self.context(task.kind, task.node_id)
        ctx["extra"] = self._extra_for(task)

        # ---- pass structure (entities only) ----
        of = task.passes if task.kind == "entity" else 1
        merged: dict = {}
        for pass_no in range(1, of + 1):
            tr = self.load_transition(task.node_id, pass_no, of)
            if tr is None:
                self.log(f"  · {task.node_id:<9} transition"
                         + (f" pass {pass_no}/{of}" if of > 1 else ""))
                if merged:
                    ctx["extra"] = self._extra_for(task) + \
                        f"\n\nWHAT EARLIER PASSES ESTABLISHED FOR {task.node_id} (FIXED)\n{_j(merged)}"
                t0 = time.time()
                tr = self.backend.complete_json(
                    TRANSITION_SYSTEM,
                    transition_prompt(task, ctx, pass_no, of),
                    T.TRANSITION_SCHEMA,
                    stage=f"transition.{task.kind}",
                    tag=f"transition.{task.node_id}" + (f".p{pass_no}" if of > 1 else ""),
                )
                self.save_transition(task.node_id, tr, pass_no, of)
                sc = T.score_transition(tr)
                verdict, gaps = T.grade(sc)
                result.scores[f"{task.node_id}" + (f".p{pass_no}" if of > 1 else "")] = \
                    {"score": sc, "verdict": verdict, "gaps": gaps, "secs": round(time.time() - t0)}
                self.log(f"      {sc['words']:,} words · {verdict}"
                         + (f" · gaps: {'; '.join(gaps)}" if gaps else ""))
                result.transitions_written.append(task.node_id)
            merged = tr  # last pass's transition drives the node

        # ---- the node itself ----
        self.log(f"  · {task.node_id:<9} node")
        doc = self.backend.complete_json(
            NODE_SYSTEM, node_prompt(task, ctx, merged), NODE_SCHEMAS[task.kind],
            stage=f"node.{task.kind}", tag=f"node.{task.node_id}",
        )
        self._store_node(task, doc, result)

    def _extra_for(self, task: NodeTask) -> str:
        if task.kind == "entity":
            return (f"THIS NODE: the dossier for {task.node_id}. It was forward-declared by "
                    f"the plot layer, so the plots already assume it exists.")
        if task.kind == "event":
            root = self.project.load("story_root") or {}
            n = (root.get("constraints") or {}).get("event_count_target") or 12
            plots = (self.project.load("plots") or {}).get("plots", [])
            undischarged = []
            events = (self.project.load("events") or {}).get("events", {})
            bound = {(b.get("plot"), b.get("step"))
                     for e in events.values() for b in (e.get("plot_bindings") or [])}
            for p in plots:
                for k in (p.get("spine") or {}):
                    if (p["plot_id"], k) not in bound:
                        undischarged.append(f"{p['plot_id']}:{k} "
                                            f"({(p['spine'][k].get('function') or '')})")
            return (f"THIS NODE: event {task.node_id} of about {n}.\n"
                    f"SPINE STEPS STILL UNDISCHARGED (every one must be bound by some event "
                    f"before the story is complete):\n  " + "\n  ".join(undischarged or ["none"]))
        return ""

    def _existing_node(self, task: NodeTask):
        if task.kind == "plot":
            for p in (self.project.load("plots") or {}).get("plots", []):
                if p.get("plot_id") == task.node_id:
                    return p
        elif task.kind == "entity":
            return ((self.project.load("entities") or {}).get("entities") or {}).get(task.node_id)
        elif task.kind == "event":
            return ((self.project.load("events") or {}).get("events") or {}).get(task.node_id)
        return None

    def _store_node(self, task: NodeTask, doc: dict, result: ForgeResult) -> None:
        p = self.project
        if task.kind == "plot":
            cur = p.load("plots") or {"plots": []}
            node = doc.get("plot") or {}
            node.setdefault("plot_id", task.node_id)
            cur["plots"] = [x for x in cur["plots"] if x.get("plot_id") != task.node_id] + [node]
            cur["plots"].sort(key=lambda x: x.get("plot_id", ""))
            p.save("plots", cur)
        elif task.kind == "entity":
            cur = p.load("entities") or {"entities": {}}
            node = doc.get("entity") or {}
            node.setdefault("entity_id", task.node_id)
            cur["entities"][task.node_id] = node
            p.save("entities", cur)
        elif task.kind == "event":
            cur = p.load("events") or {"events": {}}
            node = doc.get("event") or {}
            node.setdefault("event_id", task.node_id)
            cur["events"][task.node_id] = node
            p.save("events", cur)
        result.nodes_written.append(task.node_id)

        errs = jsonschema_mini.validate(node, NODE_SCHEMAS[task.kind]["properties"][task.kind])
        if errs:
            self.log(f"      schema: {len(errs)} issue(s) — {errs[0][:90]}")
            result.errors.extend(f"{task.node_id}: {e}" for e in errs[:5])

    # -- the run -----------------------------------------------------------

    def run(self, *, kinds: list[str] | None = None, limit: int | None = None) -> ForgeResult:
        result = ForgeResult()
        p = self.project

        # story root and exposé keep the layer prompts — they are single nodes anyway.
        if p.load("story_root") is None:
            self.log("  · story_root node")
            doc = self.backend.complete_json(
                prompts.SYSTEM, prompts.story_root_prompt(self.brief, self.options),
                SCHEMAS["story_root"], stage="story_root", tag="story_root")
            p.save("story_root", doc)
            result.nodes_written.append("story_root")

        if p.load("expose") is None:
            root = p.load("story_root")
            tr = self.load_transition("expose")
            if tr is None:
                self.log("  · expose    transition")
                ctx = {"root": root, "extra": ""}
                task = NodeTask("expose", "expose", 0)
                tr = self.backend.complete_json(
                    TRANSITION_SYSTEM, transition_prompt(task, ctx),
                    T.TRANSITION_SCHEMA, stage="transition.expose", tag="transition.expose")
                self.save_transition("expose", tr)
                sc = T.score_transition(tr); v, g = T.grade(sc)
                result.scores["expose"] = {"score": sc, "verdict": v, "gaps": g}
                self.log(f"      {sc['words']:,} words · {v}")
                result.transitions_written.append("expose")
            self.log("  · expose    node")
            doc = self.backend.complete_json(
                NODE_SYSTEM,
                prompts.expose_prompt(root) + f"\n\nTHE TRANSITION ALREADY REASONED FOR THIS NODE\n{_j(tr)}",
                SCHEMAS["expose"], stage="expose", tag="expose")
            p.save("expose", doc)
            result.nodes_written.append("expose")

        root = p.load("story_root") or {}
        done = 0
        while True:
            tasks = plan_nodes(root, p.load("plots"), p.load("entities"),
                               entity_passes=self.entity_passes)
            todo = [t for t in tasks
                    if (kinds is None or t.kind in kinds) and self._existing_node(t) is None]
            if not todo:
                break
            task = todo[0]
            try:
                self.forge_node(task, result)
            except AwaitingAgent as a:
                result.pending.append({"tag": a.tag, "packet": a.packet_path,
                                       "output": a.output_path, "kind": a.kind})
                return result
            except BackendError as exc:
                result.errors.append(f"{task.node_id}: {exc}")
                self.log(f"      FAILED: {exc}")
                break
            done += 1
            if limit and done >= limit:
                break

        return result
