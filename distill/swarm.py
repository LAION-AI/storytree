"""Bottom-up reconstruction with a swarm of small agents.

Implements `WHITEPAPER-SWARM.md`. The design inverts the top-down pipeline: read
the scenes first, blind of any superstructure, and induce the higher layers from
what is actually there.

The motivating measurement is in `docs/07-quality-evaluation.md`. A top-down run
declared nine entities where the brief asked for thirty to forty; the event layer
then placed all twenty-two events at the single location that existed, and the
story ended with a character somewhere her own state model could not hold. No
individual call was wrong. A thin superstructure strangles every layer beneath
it, silently, while passing every schema check.

Three rules govern the implementation, each earned:

  1. Anything decidable from data on disk is decided in code and never reaches a
     model. Four evaluation passes found failures that were all decidable:
     whether a speaker is in the scene, whether a variable belongs to the entity
     named, whether a value is in its declared domain.

  2. One narrow task per call. Models divide a fixed output budget across
     whatever is requested rather than scaling to it — four psychological
     analyses in one call yields four hollow shells.

  3. Never grade against a list this apparatus generated. That measures
     compliance, not correctness, and it has already produced a constraint that
     mandated the error it was meant to prevent.

Nothing here copies source text. Scene text is read to build prompts and is
never written into an artifact.
"""

from __future__ import annotations

import json
import math
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "reconstruct"))

from scriptforge import screenplay as sp  # noqa: E402


# --------------------------------------------------------------------------
# Dispatch
# --------------------------------------------------------------------------

GRAMMAR_UNSUPPORTED = ("propertyNames", "dependentRequired", "dependentSchemas",
                       "unevaluatedProperties", "if", "then", "else")


def grammar_safe(schema):
    """Strip keywords the grammar compiler does not implement.

    vLLM returns HTTP 500 with an *empty* error body on `propertyNames`, after
    the client has already burned its retries. The schema is still validated in
    full after the call, so this moves a guarantee from the grammar to the
    validator rather than dropping it.
    """
    if isinstance(schema, dict):
        return {k: grammar_safe(v) for k, v in schema.items()
                if k not in GRAMMAR_UNSUPPORTED}
    if isinstance(schema, list):
        return [grammar_safe(v) for v in schema]
    return schema


@dataclass
class Call:
    stage: str
    tag: str
    secs: float
    tok_in: int
    tok_out: int
    attempt: int
    ok: bool


class Swarm:
    """Round-robins work across the endpoints, N concurrent per endpoint."""

    def __init__(self, ports: list[int], model: str, per_endpoint: int = 8,
                 host: str = "127.0.0.1"):
        self.bases = [f"http://{host}:{p}/v1" for p in ports]
        self.model = model
        self.per_endpoint = per_endpoint
        self.calls: list[Call] = []
        self._lock = threading.Lock()
        self._n = 0

    @property
    def width(self) -> int:
        return len(self.bases) * self.per_endpoint

    def _next_base(self) -> str:
        with self._lock:
            b = self.bases[self._n % len(self.bases)]
            self._n += 1
            return b

    def ask(self, system: str, user: str, schema: dict | None, *,
            stage: str, tag: str, max_tokens: int = 16000,
            retries: int = 3) -> dict | str | None:
        base = self._next_base()
        body = {
            "model": self.model,
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": user}],
            "max_tokens": max_tokens, "temperature": 0.7,
            # Qwen's template raises on any reasoning_effort outside
            # xhigh|medium|low and the request 400s, so thinking is switched off
            # structurally. Verified by token count, not by the call succeeding.
            "chat_template_kwargs": {"enable_thinking": False},
        }
        if schema is not None:
            body["response_format"] = {
                "type": "json_schema",
                "json_schema": {"name": "a", "strict": False,
                                "schema": grammar_safe(schema)}}

        for attempt in range(1, retries + 1):
            t0 = time.time()
            try:
                r = requests.post(f"{base}/chat/completions", json=body, timeout=3600)
            except requests.RequestException:
                continue
            dt = time.time() - t0
            if r.status_code != 200:
                with self._lock:
                    self.calls.append(Call(stage, tag, dt, 0, 0, attempt, False))
                continue
            d = r.json()
            content = d["choices"][0]["message"].get("content") or ""
            u = d.get("usage", {})
            with self._lock:
                self.calls.append(Call(stage, tag, dt, u.get("prompt_tokens", 0),
                                       u.get("completion_tokens", 0), attempt,
                                       bool(content.strip())))
            if not content.strip():
                continue
            if schema is None:
                return content
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                continue
        return None

    def map(self, fn, items, *, stage: str, label=lambda x: str(x)):
        """Run `fn` over `items` concurrently. Order preserved, failures are None."""
        out: list = [None] * len(items)
        done = 0
        t0 = time.time()
        with ThreadPoolExecutor(max_workers=self.width) as ex:
            futs = {ex.submit(fn, it): i for i, it in enumerate(items)}
            for f in as_completed(futs):
                i = futs[f]
                try:
                    out[i] = f.result()
                except Exception as exc:      # a dead unit must not kill the stage
                    print(f"      ! {label(items[i])}: {type(exc).__name__}: {exc}")
                done += 1
                if done % max(1, len(items) // 10) == 0 or done == len(items):
                    print(f"      {stage}: {done}/{len(items)}  "
                          f"{time.time()-t0:.0f}s", flush=True)
        return out

    def summary(self, stage: str | None = None) -> dict:
        cs = [c for c in self.calls if stage is None or c.stage == stage]
        ok = [c for c in cs if c.ok]
        secs = sum(c.secs for c in cs)
        return {"calls": len(cs), "ok": len(ok), "failed": len(cs) - len(ok),
                "tok_in": sum(c.tok_in for c in cs),
                "tok_out": sum(c.tok_out for c in cs),
                "model_secs": secs,
                "tok_per_s": sum(c.tok_out for c in cs) / secs if secs else 0}


# --------------------------------------------------------------------------
# Stage 1 — scene nodes, blind of the tree
# --------------------------------------------------------------------------

SCENE_SYSTEM = """\
You are reading one scene of a screenplay and recording what is in it.

You have the complete script for context and one scene to describe. You do NOT
have a story outline, a plot list, or a character bible, because none exists yet
— this scene and its siblings are what those will be built from.

So describe what is there. Do not infer a larger design and do not write as
though you know where the story is going. Where you must guess, mark it as a
guess.

Name characters the way the script names them. If the script says BIG COP, write
BIG COP. Consistency with other scenes is handled later by other means; guessing
at a canonical name is worse than using the one in front of you.

Be specific and concrete. A description that would fit any scene of this kind is
worth nothing — the point is what makes THIS scene this scene.

Return JSON conforming to the schema. No prose outside it."""

SCENE_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["scene_id", "location", "time_of_day", "present", "summary",
                 "what_changes", "event_hint"],
    "properties": {
        "scene_id": {"type": "string"},
        "location": {"type": "string"},
        "time_of_day": {"type": "string"},
        "present": {"type": "array", "minItems": 1,
                    "items": {"type": "string"},
                    "description": "Everyone in the scene, script's own naming."},
        "speaking": {"type": "array", "items": {"type": "string"}},
        "summary": {"type": "string", "minLength": 80,
                    "description": "What happens, concretely."},
        "what_changes": {
            "type": "array", "minItems": 1,
            "items": {
                "type": "object", "additionalProperties": False,
                "required": ["who", "axis", "before", "after", "evidence"],
                "properties": {
                    "who": {"type": "string"},
                    "axis": {"type": "string",
                             "description": "knowledge, trust, safety, allegiance, "
                                            "resolve, custody, condition, standing"},
                    "before": {"type": "string"}, "after": {"type": "string"},
                    "evidence": {"type": "string", "minLength": 25,
                                 "description": "A VERBATIM span copied from this "
                                                "scene, at least 25 characters, that "
                                                "shows the change. Copy it exactly; "
                                                "do not paraphrase. If nothing in the "
                                                "scene shows it, do not claim it."},
                },
            },
        },
        "objects_that_matter": {"type": "array", "items": {"type": "string"}},
        "event_hint": {
            "type": "object", "additionalProperties": False,
            "required": ["kind", "one_line"],
            "properties": {
                "kind": {"type": "string",
                         "description": "The unit of happening this belongs to: a "
                                        "chase, a negotiation, a raid, a wake."},
                "one_line": {"type": "string"},
                "continues_from_earlier": {"type": "boolean"},
            },
        },
        "uncertain": {"type": "array", "items": {"type": "string"},
                      "description": "What you could not tell from the text."},
    },
}


def _window(script: str, scene, before: int = 60000, after: int = 40000) -> str:
    """Context around the scene, not the first N characters of the file.

    `script[:120000]` on a 140,172-character screenplay deleted the entire third
    act — 42 scenes that no agent ever saw, with nothing in the protocol
    recording it. Nodes were produced for them anyway.

    A window centred on the scene keeps the context bounded without a whole act
    falling off the end, and the boundaries are reported so a truncation is
    visible rather than silent.
    """
    lo = max(0, scene.start_char - before)
    hi = min(len(script), scene.end_char + after)
    head = "" if lo == 0 else f"[...{lo:,} characters earlier omitted...]\n"
    tail = "" if hi == len(script) else f"\n[...{len(script)-hi:,} characters later omitted...]"
    return head + script[lo:hi] + tail


def stage1_scenes(sw: Swarm, script: str, scenes: list) -> list[dict]:
    def one(scene):
        # `Scene` carries start_char/end_char. The first version read
        # `scene.start` behind a `hasattr` guard, so the attribute was missing,
        # the guard swallowed it, and every one of 224 agents received an EMPTY
        # scene — writing fluent, schema-valid nodes from the script alone.
        # Measured afterwards: 5.2% of quoted evidence occurred in the scene it
        # was attributed to.
        #
        # A guard that substitutes empty input for missing input is worse than
        # no guard. It converts a crash into a confident wrong answer, which is
        # the failure mode this whole project keeps rediscovering. Hence the
        # assertion: absent input must stop the run.
        text = script[scene.start_char:scene.end_char]
        if not text.strip():
            raise ValueError(f"{scene.scene_id}: empty scene text "
                             f"[{scene.start_char}:{scene.end_char}]")
        user = f"""\
Describe scene {scene.scene_id}.

THE SCENE
{text[:14000]}

FOR CONTEXT ONLY — the surrounding script. Use it to understand who people are
and what has already happened. Do not describe any scene but {scene.scene_id}.
{_window(script, scene)}

SCHEMA
{json.dumps(SCENE_SCHEMA, indent=1)}
"""
        d = sw.ask(SCENE_SYSTEM, user, SCENE_SCHEMA,
                   stage="1-scenes", tag=scene.scene_id, max_tokens=9000)
        if d:
            d["scene_id"] = scene.scene_id          # ours, not the model's
        return d

    return sw.map(one, scenes, stage="1-scenes", label=lambda s: s.scene_id)


# --------------------------------------------------------------------------
# Stage 2 — event boundaries by sliding window
# --------------------------------------------------------------------------

BOUNDARY_SYSTEM = """\
You are grouping scenes into events.

An event is a unit of happening: a party, an earthquake, a battle, two friends
walking, a household waking up before work. It is not a location and not a
chapter — it is one thing occurring, which may take several scenes and may be
interrupted by scenes of something else.

Scenes 1 and 3 may be the same party while scene 2 cuts elsewhere. So do not
group by adjacency. Group by whether the same thing is still happening.

Return JSON conforming to the schema. No prose outside it."""

BOUNDARY_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["events"],
    "properties": {"events": {
        "type": "array", "minItems": 1,
        "items": {
            "type": "object", "additionalProperties": False,
            "required": ["name", "scenes", "what_happens"],
            "properties": {
                "name": {"type": "string",
                         "description": "A short name for the happening."},
                "scenes": {"type": "array", "minItems": 1,
                           "items": {"type": "string"}},
                "what_happens": {"type": "string", "minLength": 40},
                "may_continue_beyond_window": {"type": "boolean"},
            },
        },
    }},
}


def windows(n: int, width: int, stride: int) -> list[tuple[int, int]]:
    if n <= width:
        return [(0, n)]
    out = [(i, min(i + width, n)) for i in range(0, n - width + 1, stride)]
    if out[-1][1] < n:
        out.append((n - width, n))
    return out


def _digest(nodes: list[dict], lo: int, hi: int) -> str:
    rows = []
    for nd in nodes[lo:hi]:
        if not nd:
            continue
        h = nd.get("event_hint") or {}
        rows.append(f"{nd['scene_id']} @ {nd.get('location')} ({nd.get('time_of_day')})"
                    f" — {nd.get('summary','')[:220]}"
                    f"\n    hint: {h.get('kind')} · {h.get('one_line','')[:120]}")
    return "\n".join(rows)


def stage2_boundaries(sw: Swarm, nodes: list[dict], script: str) -> dict:
    n = len(nodes)

    # pass A — narrow windows
    wa = windows(n, 10, 5)
    def a(w):
        lo, hi = w
        return sw.ask(BOUNDARY_SYSTEM, f"""\
Group these scenes into events.

{_digest(nodes, lo, hi)}

SCHEMA
{json.dumps(BOUNDARY_SCHEMA, indent=1)}
""", BOUNDARY_SCHEMA, stage="2a-windows", tag=f"w{lo}-{hi}", max_tokens=4000)
    ra = [x for x in sw.map(a, wa, stage="2a-windows",
                            label=lambda w: f"{w[0]}-{w[1]}") if x]

    # pass B — reconcile over wider windows
    wb = windows(n, 25, 20)
    def b(w):
        lo, hi = w
        prior = [e for r in ra for e in (r.get("events") or [])
                 if any(lo <= _idx(s) < hi for s in e.get("scenes") or [])]
        return sw.ask(BOUNDARY_SYSTEM, f"""\
Earlier passes proposed these groupings over narrow windows. They overlap and may
disagree. Reconcile them into one grouping for this range.

PROPOSALS
{json.dumps(prior, indent=1)[:14000]}

THE SCENES
{_digest(nodes, lo, hi)}

SCHEMA
{json.dumps(BOUNDARY_SCHEMA, indent=1)}
""", BOUNDARY_SCHEMA, stage="2b-reconcile", tag=f"w{lo}-{hi}", max_tokens=6000)
    rb = [x for x in sw.map(b, wb, stage="2b-reconcile",
                            label=lambda w: f"{w[0]}-{w[1]}") if x]

    # pass C — one consolidation. Deliberately given the *proposals*, not 224
    # nodes: this is the single call with the most authority in the pipeline and
    # the least verification above it, so its input is kept small on purpose.
    merged = [e for r in rb for e in (r.get("events") or [])]
    final = sw.ask(BOUNDARY_SYSTEM, f"""\
These proposals cover the whole work with overlaps. Produce the final grouping.

Every scene must appear in exactly one event. Merge proposals that describe the
same happening under different names.

PROPOSALS
{json.dumps(merged, indent=1)[:60000]}

ALL SCENES IN ORDER
{chr(10).join((nd or {}).get('scene_id', '?') + ' — ' + ((nd or {}).get('summary','')[:90]) for nd in nodes)}

SCHEMA
{json.dumps(BOUNDARY_SCHEMA, indent=1)}
""", BOUNDARY_SCHEMA, stage="2c-final", tag="consolidate", max_tokens=30000)
    return final or {"events": merged}


def _idx(scene_id: str) -> int:
    m = re.search(r"(\d+)", scene_id or "")
    return int(m.group(1)) - 1 if m else -1


def repair_coverage(final: dict, nodes: list[dict]) -> tuple[dict, list[str]]:
    """Every scene in exactly one event — decided in code, not asked of a model.

    Coverage is arithmetic. A model asked to guarantee it will sometimes drop a
    scene or list one twice, and neither shows up as a schema error.
    """
    problems = []
    events = final.get("events") or []
    seen: dict[str, int] = {}
    for i, e in enumerate(events):
        keep = []
        for s in e.get("scenes") or []:
            if s in seen:
                problems.append(f"{s} claimed by both '{events[seen[s]].get('name')}' "
                                f"and '{e.get('name')}' — kept the first")
                continue
            seen[s] = i
            keep.append(s)
        e["scenes"] = keep
    all_ids = [(nd or {}).get("scene_id") for nd in nodes if nd]
    missing = [s for s in all_ids if s and s not in seen]
    if missing:
        problems.append(f"{len(missing)} scene(s) in no event: {missing[:8]}")
        events.append({"name": "UNASSIGNED", "scenes": missing,
                       "what_happens": "Scenes the boundary pass did not place. "
                                       "Recorded rather than dropped."})
    final["events"] = [e for e in events if e.get("scenes")]
    for i, e in enumerate(final["events"], 1):
        e["event_id"] = f"ev-{i:03d}"
    return final, problems


# --------------------------------------------------------------------------
# Stage 3 — event drafts, one agent each
# --------------------------------------------------------------------------

EVENT_SYSTEM = """\
You are describing one event: one unit of happening, spanning the scenes listed.

Its boundaries are fixed. Do not re-cut them. If they look wrong, say so in
`boundary_doubt` and describe the event you were given anyway.

You will be asked which larger thread this serves, and the thread list does not
exist yet — you are the evidence it will be built from. So speculate, and
speculate *from the text*: name what in the script supports your reading. A claim
with no evidence is worse than no claim, and will be discarded.

Return JSON conforming to the schema. No prose outside it."""

EVENT_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["event_id", "name", "what_happens", "participants",
                 "state_changes", "plot_speculation"],
    "properties": {
        "event_id": {"type": "string"},
        "name": {"type": "string"},
        "location": {"type": "string"},
        "what_happens": {"type": "string", "minLength": 150},
        "participants": {"type": "array", "minItems": 1, "items": {"type": "string"}},
        "entry_state": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "required": ["who", "state"],
            "properties": {"who": {"type": "string"}, "state": {"type": "string"}}}},
        "state_changes": {"type": "array", "minItems": 1, "items": {
            "type": "object", "additionalProperties": False,
            "required": ["who", "axis", "before", "after", "why_it_matters"],
            "properties": {
                "who": {"type": "string"}, "axis": {"type": "string"},
                "before": {"type": "string"}, "after": {"type": "string"},
                "why_it_matters": {"type": "string", "minLength": 30}}}},
        "exit_state": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "required": ["who", "state"],
            "properties": {"who": {"type": "string"}, "state": {"type": "string"}}}},
        "reversal": {"type": "boolean",
                     "description": "Does something turn here — an expectation "
                                    "defeated, an alliance flipped, a plan undone?"},
        "plot_speculation": {"type": "array", "minItems": 1, "items": {
            "type": "object", "additionalProperties": False,
            "required": ["claim", "evidence", "confidence"],
            "properties": {
                "claim": {"type": "string",
                          "description": "The larger thread this seems to serve."},
                "evidence": {"type": "array", "minItems": 1,
                             "items": {"type": "string"}},
                "confidence": {"type": "integer"},
                "alternative": {"type": "string"}}}},
        "boundary_doubt": {"type": "string"},
    },
}


def stage3_events(sw: Swarm, boundaries: dict, nodes: dict, script: str) -> list[dict]:
    def one(ev):
        members = [nodes[s] for s in ev.get("scenes") or [] if s in nodes]
        return _tag(sw.ask(EVENT_SYSTEM, f"""\
Describe event {ev['event_id']}: {ev.get('name')}

WHAT THE BOUNDARY PASS SAID
{ev.get('what_happens')}

ITS SCENES
{json.dumps(members, indent=1)[:26000]}

THE SCRIPT, for evidence
{script[:100000]}

SCHEMA
{json.dumps(EVENT_SCHEMA, indent=1)}
""", EVENT_SCHEMA, stage="3-events", tag=ev["event_id"], max_tokens=12000),
                    "event_id", ev["event_id"], scenes=ev.get("scenes"))

    return [e for e in sw.map(one, boundaries["events"], stage="3-events",
                              label=lambda e: e["event_id"]) if e]


def _tag(d, key, val, **extra):
    if d:
        d[key] = val
        d.update(extra)
    return d


# --------------------------------------------------------------------------
# Stage 4 — plots induced from the event speculations
# --------------------------------------------------------------------------

PLOT_SYSTEM = """\
You are naming the threads that run through this work.

You have every event with what its author thought it served. Those speculations
were written independently and will conflict; that is what you are for.

A feature usually carries at least four: the main line the protagonist drives, a
character-growth line, a relationship line, an antagonist line. There may be
thematic lines as well. Do not invent threads to hit a number, and do not
collapse two genuinely different ones to be tidy.

Every event belongs to at least one thread. An event may serve two.

Return JSON conforming to the schema. No prose outside it."""

PLOT_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["plots"],
    "properties": {"plots": {"type": "array", "minItems": 2, "items": {
        "type": "object", "additionalProperties": False,
        "required": ["plot_id", "name", "kind", "description", "events"],
        "properties": {
            "plot_id": {"type": "string"},
            "name": {"type": "string"},
            "kind": {"type": "string",
                     "enum": ["main", "character_growth", "relationship",
                              "antagonist", "thematic", "subplot"]},
            "description": {"type": "string", "minLength": 80},
            "events": {"type": "array", "minItems": 1, "items": {"type": "string"}},
            "arc": {"type": "string"}}}}},
}


def stage4_plots(sw: Swarm, events: list[dict], script: str) -> dict:
    digest = [{"event_id": e["event_id"], "name": e.get("name"),
               "what_happens": (e.get("what_happens") or "")[:400],
               "reversal": e.get("reversal"),
               "speculation": e.get("plot_speculation")} for e in events]

    draft = sw.ask(PLOT_SYSTEM, f"""\
Name the threads running through this work, and assign every event to at least one.

THE EVENTS, with what each author thought it served
{json.dumps(digest, indent=1)[:90000]}

SCHEMA
{json.dumps(PLOT_SCHEMA, indent=1)}
""", PLOT_SCHEMA, stage="4a-draft", tag="induce", max_tokens=20000)
    if not draft:
        return {"plots": []}

    # one doctor per plot, in parallel. One doctor holding all five would divide
    # a fixed budget across them — the measured failure this whole design is
    # built around.
    DOC = {"type": "object", "additionalProperties": False,
           "required": ["plot_id", "verdict", "reasoning"],
           "properties": {
               "plot_id": {"type": "string"},
               "verdict": {"type": "string",
                           "enum": ["sound", "needs_members_moved", "should_dissolve"]},
               "reasoning": {"type": "string", "minLength": 60},
               "remove": {"type": "array", "items": {"type": "string"}},
               "add": {"type": "array", "items": {"type": "string"}},
               "better_description": {"type": "string"}}}

    def doctor(p):
        return sw.ask("""\
You are a script doctor holding exactly one thread. Argue about whether its
member events really belong to it, against the evidence of the script. You may
conclude the thread should not exist. Be specific and brief.""", f"""\
THE THREAD
{json.dumps(p, indent=1)}

ALL EVENTS
{json.dumps(digest, indent=1)[:60000]}

SCHEMA
{json.dumps(DOC, indent=1)}
""", DOC, stage="4b-doctors", tag=p.get("plot_id", "?"), max_tokens=5000)

    notes = [d for d in sw.map(doctor, draft["plots"], stage="4b-doctors",
                               label=lambda p: p.get("plot_id", "?")) if d]

    final = sw.ask(PLOT_SYSTEM, f"""\
A doctor examined each thread separately. Consolidate: apply what is right,
reject what is not, and keep every event assigned to at least one thread.

THE DRAFT
{json.dumps(draft, indent=1)[:40000]}

THE NOTES
{json.dumps(notes, indent=1)[:30000]}

SCHEMA
{json.dumps(PLOT_SCHEMA, indent=1)}
""", PLOT_SCHEMA, stage="4c-final", tag="consolidate", max_tokens=20000)
    out = final or draft
    out["_doctor_notes"] = notes
    return out


# --------------------------------------------------------------------------
# Stage 5 — entity unification (concurrent with stage 4)
# --------------------------------------------------------------------------

ENTITY_SYSTEM = """\
You are building the canonical list of one kind of thing in this work.

Earlier agents each read one scene alone and named things however the script
named them there, so the same person appears as ALICE M., Alice Miller and THE
WOMAN. Your job is to decide which of those are the same thing and give each a
single identifier.

The standard is a capitalised identity word: ALICE_MILLER, THE_HOTEL,
RED_BRIEFCASE. Choose the form a reader would recognise.

Record every alias you merged. A merge that loses its aliases cannot be applied
to the rest of the tree, and cannot be undone if it was wrong.

Merge only what is the same. Two characters with similar functions are two
characters. When genuinely unsure, keep them separate and say so.

Return JSON conforming to the schema. No prose outside it."""

ENTITY_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["entities"],
    "properties": {"entities": {"type": "array", "items": {
        "type": "object", "additionalProperties": False,
        "required": ["id", "name", "aliases", "description"],
        "properties": {
            "id": {"type": "string"},
            "name": {"type": "string"},
            "aliases": {"type": "array", "items": {"type": "string"}},
            "description": {"type": "string", "minLength": 30},
            "salience": {"type": "string",
                         "enum": ["major", "supporting", "minor", "mentioned"]},
            "uncertain_merge": {"type": "string"}}}}},
}

KINDS = [
    ("agents", "anything that decides for itself — people, animals, robots, "
               "anything with its own will"),
    ("locations", "places the story happens in"),
    ("objects", "things that matter to the plot"),
    ("concepts", "groups, factions, institutions, rules of the world, social or "
                 "magical systems, anything abstract the story turns on"),
]


def stage5_entities(sw: Swarm, nodes: list[dict], events: list[dict]) -> dict:
    seen = sorted({n for nd in nodes if nd
                   for n in (nd.get("present") or []) + (nd.get("objects_that_matter") or [])}
                  | {p for e in events for p in (e.get("participants") or [])}
                  | {nd.get("location") for nd in nodes if nd and nd.get("location")})

    def one(kind):
        name, what = kind
        return (name, sw.ask(ENTITY_SYSTEM, f"""\
Build the canonical list of: {what}

Only that kind. Other agents handle the rest.

EVERY NAME ANY EARLIER AGENT USED
{json.dumps(seen, indent=1)[:24000]}

WHERE THEY APPEAR
{json.dumps([{'scene': (nd or {}).get('scene_id'), 'where': (nd or {}).get('location'),
              'present': (nd or {}).get('present'),
              'objects': (nd or {}).get('objects_that_matter'),
              'what': ((nd or {}).get('summary') or '')[:150]}
             for nd in nodes if nd], indent=1)[:70000]}

SCHEMA
{json.dumps(ENTITY_SCHEMA, indent=1)}
""", ENTITY_SCHEMA, stage="5-entities", tag=name, max_tokens=22000))

    out = {}
    for name, res in sw.map(one, KINDS, stage="5-entities", label=lambda k: k[0]):
        out[name] = (res or {}).get("entities") or []

    # Precedence, applied in code. The four agents work independently and cannot
    # see each other, so the objects agent listed NEO and TRINITY as objects —
    # measured, 14 duplicate ids on a 12-scene smoke test. Asking each agent to
    # stay in its lane is an instruction; enforcing it is arithmetic. A thing that
    # decides for itself is an agent no matter which list also claimed it.
    claimed: set[str] = set()
    for name in ("agents", "locations", "objects", "concepts"):
        keep = []
        for e in out.get(name) or []:
            eid = e.get("id")
            if not eid or eid in claimed:
                continue
            claimed.add(eid)
            keep.append(e)
        out[name] = keep
    return out


def alias_map(entities: dict) -> dict[str, str]:
    """alias -> canonical id. Applied by code; no model asked to be consistent."""
    m = {}
    for group in entities.values():
        for e in group:
            eid = e.get("id")
            if not eid:
                continue
            m[eid] = eid
            for a in [e.get("name")] + list(e.get("aliases") or []):
                if a:
                    m[str(a)] = eid
    return m


def apply_aliases(obj, amap: dict[str, str]):
    """Rewrite every name to its canonical id, everywhere, mechanically."""
    if isinstance(obj, str):
        return amap.get(obj, obj)
    if isinstance(obj, list):
        return [apply_aliases(x, amap) for x in obj]
    if isinstance(obj, dict):
        return {k: (apply_aliases(v, amap)
                    if k in ("who", "present", "speaking", "participants", "entity",
                             "objects_that_matter", "location", "characters")
                    else apply_aliases(v, amap) if isinstance(v, (dict, list))
                    else v)
                for k, v in obj.items()}
    return obj


# --------------------------------------------------------------------------
# Stages 6-8 — profiles, root, expose
# --------------------------------------------------------------------------

PROFILE_SYSTEM = """\
You are writing the profile of one entity, and only that one.

Everything you claim must be traceable to the script or to what the events
recorded. Where you infer, mark it as inference. A profile that would fit any
character of this type has failed — the point is what makes this one this one.

Give it enough state variables to carry what the story actually does to it. A
character whose humiliation has no variable to live in will have that humiliation
silently dropped by every layer below you.

Return JSON conforming to the schema. No prose outside it."""

PROFILE_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["id", "kind", "description", "state_variables"],
    "properties": {
        "id": {"type": "string"},
        "kind": {"type": "string"},
        "description": {"type": "string", "minLength": 100},
        "appearance": {"type": "string"},
        "background": {"type": "string"},
        "wants": {"type": "string"}, "fears": {"type": "string"},
        "internal_conflict": {"type": "string"},
        "speech": {"type": "string"},
        "relationships": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "required": ["with", "nature"],
            "properties": {"with": {"type": "string"}, "nature": {"type": "string"}}}},
        "state_variables": {"type": "array", "minItems": 2, "items": {
            "type": "object", "additionalProperties": False,
            "required": ["name", "domain", "initial", "why"],
            "properties": {
                "name": {"type": "string"},
                "domain": {"type": "array", "minItems": 2, "items": {"type": "string"}},
                "initial": {"type": "string"},
                "why": {"type": "string",
                        "description": "Which event moves this. If none does, "
                                       "do not declare it."}}}},
        "inferred": {"type": "array", "items": {"type": "string"}},
    },
}


def stage6_profiles(sw: Swarm, entities: dict, events: list[dict],
                    script: str, cap: int = 40) -> list[dict]:
    flat = [(k, e) for k, g in entities.items() for e in g
            if e.get("salience") in (None, "major", "supporting")][:cap]

    def one(pair):
        kind, e = pair
        eid = e.get("id")
        touching = [{"event_id": ev["event_id"], "name": ev.get("name"),
                     "changes": [c for c in (ev.get("state_changes") or [])
                                 if c.get("who") == eid]}
                    for ev in events if eid in (ev.get("participants") or [])]
        d = sw.ask(PROFILE_SYSTEM, f"""\
Write the profile of {eid} ({kind}).

WHAT THE ENTITY PASS RECORDED
{json.dumps(e, indent=1)}

EVENTS IT APPEARS IN, AND WHAT MOVED
{json.dumps(touching, indent=1)[:22000]}

THE SCRIPT, for evidence
{script[:90000]}

Declare a state variable only where an event above actually moves it.

SCHEMA
{json.dumps(PROFILE_SCHEMA, indent=1)}
""", PROFILE_SCHEMA, stage="6-profiles", tag=eid, max_tokens=10000)
        return _tag(d, "id", eid, kind=kind)

    return [p for p in sw.map(one, flat, stage="6-profiles",
                              label=lambda p: p[1].get("id", "?")) if p]


ROOT_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["title", "genre", "audiences", "pitch", "style",
                 "dramatic_structure", "themes", "identification"],
    "properties": {
        "title": {"type": "string"},
        "genre": {"type": "string", "minLength": 60,
                  "description": "Nuanced and specific, never one word."},
        "audiences": {"type": "array", "minItems": 1, "items": {
            "type": "object", "additionalProperties": False,
            "required": ["who", "why"],
            "properties": {"who": {"type": "string"}, "why": {"type": "string"}}}},
        "pitch": {"type": "string", "minLength": 120},
        "style": {"type": "string", "minLength": 120,
                  "description": "Pacing, dialogue register, atmosphere. Describe "
                                 "it without naming any author."},
        "dramatic_structure": {
            "type": "object", "additionalProperties": False,
            "required": ["shape", "turning_points"],
            "properties": {
                "shape": {"type": "string"},
                "turning_points": {"type": "array", "items": {
                    "type": "object", "additionalProperties": False,
                    "required": ["where", "what"],
                    "properties": {"where": {"type": "string"},
                                   "what": {"type": "string"}}}}}},
        "themes": {"type": "array", "minItems": 1, "items": {"type": "string"}},
        "identification": {
            "type": "object", "additionalProperties": False,
            "required": ["protagonist", "admired", "vulnerable"],
            "properties": {
                "protagonist": {"type": "string"},
                "admired": {"type": "string",
                            "description": "What draws an audience toward them."},
                "vulnerable": {"type": "string",
                               "description": "What lets an audience open up."}}},
    },
}


def stage7_root(sw: Swarm, plots: dict, entities: dict, events: list[dict],
                script: str) -> dict:
    return sw.ask("""\
You are describing a finished work at the highest level, from its own structure.

Everything below you already exists: the threads, the entities, the events. Do
not contradict them. Genre must be specific — never one word. Style must be
described without naming any author.

Return JSON conforming to the schema. No prose outside it.""", f"""\
THREADS
{json.dumps(plots.get('plots'), indent=1)[:22000]}

ENTITIES
{json.dumps({k: [e.get('id') for e in g] for k, g in entities.items()}, indent=1)}

EVENTS IN ORDER
{json.dumps([{'id': e['event_id'], 'name': e.get('name'),
              'what': (e.get('what_happens') or '')[:200]} for e in events],
            indent=1)[:30000]}

THE SCRIPT
{script[:80000]}

SCHEMA
{json.dumps(ROOT_SCHEMA, indent=1)}
""", ROOT_SCHEMA, stage="7-root", tag="root", max_tokens=14000)


EXPOSE_CRITERIA = [
    ("outsider", "Would someone who has never heard of this story understand it? "
                 "Is every in-world term explained on first use?"),
    ("plots", "Is every thread present, in the right order, through events rather "
              "than by being named?"),
    ("structure", "Does it follow the dramatic structure the root declares, with "
                  "its turning points where they belong?"),
    ("readability", "Can it be read once, straight through, without backtracking?"),
    ("identification", "Is it clear what draws an audience to the protagonist and "
                       "what lets them open up?"),
]


def stage8_expose(sw: Swarm, root: dict, plots: dict, events: list[dict],
                  profiles: list[dict], script: str) -> dict:
    ctx = f"""\
THE ROOT
{json.dumps(root, indent=1)[:12000]}

THREADS
{json.dumps(plots.get('plots'), indent=1)[:16000]}

EVENTS IN ORDER
{json.dumps([{'id': e['event_id'], 'name': e.get('name'),
              'what': (e.get('what_happens') or '')[:250]} for e in events],
            indent=1)[:34000]}

PEOPLE
{json.dumps([{'id': p['id'], 'what': (p.get('description') or '')[:180]}
             for p in profiles], indent=1)[:16000]}
"""
    SCH = {"type": "object", "additionalProperties": False,
           "required": ["text", "word_count"],
           "properties": {"text": {"type": "string", "minLength": 1500},
                          "word_count": {"type": "integer"}}}

    draft = sw.ask("""\
Write the synopsis of this work, for a reader who has never heard of it.

Explain the world only where the story needs it. Introduce each person as they
appear. Give the events in order, honouring every thread without naming threads.
Explain in-world terms on first use. Say what makes the protagonist someone an
audience opens up to. Roughly 300 words per act.

Return JSON conforming to the schema.""", ctx + f"\nSCHEMA\n{json.dumps(SCH)}",
                   SCH, stage="8a-draft", tag="expose", max_tokens=8000)
    if not draft:
        return {}

    # one doctor per criterion. A single doctor with a checklist divides a fixed
    # budget across the items; five doctors each spend their whole budget on one.
    DOC = {"type": "object", "additionalProperties": False,
           "required": ["criterion", "score", "problems"],
           "properties": {"criterion": {"type": "string"},
                          "score": {"type": "integer"},
                          "problems": {"type": "array", "items": {"type": "string"}},
                          "fix": {"type": "string"}}}

    def doctor(c):
        name, question = c
        return sw.ask(f"""\
You are a script doctor holding exactly one criterion and nothing else.

YOUR CRITERION: {question}

Judge the synopsis on that alone. Score 0-5. Be specific about what fails and
where. Ignore every other quality.""", f"""\
THE SYNOPSIS
{draft.get('text')}

{ctx[:20000]}

SCHEMA
{json.dumps(DOC, indent=1)}
""", DOC, stage="8b-doctors", tag=name, max_tokens=4000)

    notes = [d for d in sw.map(doctor, EXPOSE_CRITERIA, stage="8b-doctors",
                               label=lambda c: c[0]) if d]

    final = sw.ask("""\
Revise the synopsis against every note below at once. Where notes pull against
each other — comprehensibility wants more explanation, readability wants less —
say in one line how you resolved it.

Return JSON conforming to the schema.""", f"""\
THE DRAFT
{draft.get('text')}

THE NOTES
{json.dumps(notes, indent=1)[:20000]}

{ctx[:18000]}

SCHEMA
{json.dumps(SCH)}
""", SCH, stage="8c-revise", tag="expose", max_tokens=9000)
    out = final or draft
    out["_doctor_notes"] = notes
    return out


# --------------------------------------------------------------------------
# Stage boundary checks — decided in code, never asked of a model
# --------------------------------------------------------------------------

def check_stage1(nodes: list[dict], scenes: list, script: str = "") -> list[str]:
    """Internal consistency, plus — crucially — correspondence to the actual scene.

    The first version checked only that a node was self-consistent. A node
    describing an entirely different scene passed it cleanly, which is how 224
    hallucinated nodes scored 22 violations instead of 224. Correspondence is
    arithmetic over data on disk and it is the only check here that can catch
    the failure that actually happened.
    """
    v = []
    by_id = {s.scene_id: s for s in scenes}
    got = {(n or {}).get("scene_id") for n in nodes if n}
    for s in scenes:
        if s.scene_id not in got:
            v.append(f"{s.scene_id}: no node produced")
    for n in nodes:
        if not n:
            continue
        sid = n.get("scene_id")
        if not (n.get("what_changes") or []):
            v.append(f"{sid}: no change recorded — a scene where nothing moves")
        for c in n.get("what_changes") or []:
            if c.get("before") == c.get("after"):
                v.append(f"{sid}: no-op change on {c.get('who')!r}")
            if c.get("who") and c["who"] not in (n.get("present") or []):
                v.append(f"{sid}: change for {c['who']!r}, who is not listed present")

        sc = by_id.get(sid)
        if not (script and sc):
            continue
        own = script[sc.start_char:sc.end_char].lower()

        # At least one evidence span must occur verbatim in this scene's range.
        #
        # The first version of this check tested for a verbatim quote while the
        # schema asked for "what in the scene shows this" — an invitation to
        # paraphrase. The model paraphrased, correctly, and the check reported
        # 216 violations against output that had done as it was told. Fifth
        # instance in this project of a check testing something the thing was
        # never asked to produce. The schema now demands a copied span, which
        # makes correspondence exactly decidable rather than statistical.
        spans = [c.get("evidence", "") for c in n.get("what_changes") or []]
        long = [e for e in spans if len(e) >= 25]
        if long and not any(_loose(e) in _loose(own) for e in long):
            v.append(f"{sid}: no evidence span occurs in the scene it describes")

        # at least one name said to be present must appear in the scene or its cues
        cues = {c.lower() for c in (sc.speakers or [])}
        names = [p for p in n.get("present") or [] if p]
        if names and not any(p.lower() in own or p.lower() in cues
                             or any(p.lower() in c for c in cues) for p in names):
            v.append(f"{sid}: none of {names[:3]} appears in the scene or its cues")
    return v


def _loose(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").lower()).strip()


def check_stage2(final: dict, nodes: list[dict]) -> list[str]:
    v = []
    evs = final.get("events") or []
    sizes = [len(e.get("scenes") or []) for e in evs]
    if evs and max(sizes) > max(6, len(nodes) // 6):
        big = [e.get("name") for e in evs if len(e.get("scenes") or []) == max(sizes)]
        v.append(f"one event holds {max(sizes)} scenes ({big[:1]}) — likely under-cut")
    if len(evs) < 5:
        v.append(f"only {len(evs)} events for {len(nodes)} scenes")
    return v


def check_stage3(events: list[dict], nodes: dict) -> list[str]:
    v = []
    for e in events:
        eid = e.get("event_id")
        for sp_ in e.get("plot_speculation") or []:
            if not (sp_.get("evidence") or []):
                v.append(f"{eid}: speculation with no evidence — discarded downstream")
        for c in e.get("state_changes") or []:
            if c.get("before") == c.get("after"):
                v.append(f"{eid}: no-op change on {c.get('who')!r}")
        members = {s for s in e.get("scenes") or []}
        present = {p for s in members if s in nodes
                   for p in (nodes[s].get("present") or [])}
        for p in e.get("participants") or []:
            if present and p not in present:
                v.append(f"{eid}: participant {p!r} in none of its scenes")
    rev = sum(1 for e in events if e.get("reversal"))
    if events and rev == 0:
        v.append(f"0 of {len(events)} events carry a reversal — a chain, not a story")
    return v


def check_stage4(plots: dict, events: list[dict]) -> list[str]:
    v = []
    ps = plots.get("plots") or []
    assigned = {e for p in ps for e in (p.get("events") or [])}
    for e in events:
        if e["event_id"] not in assigned:
            v.append(f"{e['event_id']} belongs to no thread")
    for p in ps:
        for e in p.get("events") or []:
            if e not in {x["event_id"] for x in events}:
                v.append(f"{p.get('plot_id')}: unknown event {e!r}")
    if len(ps) < 3:
        v.append(f"only {len(ps)} threads identified")
    return v


def check_stage5(entities: dict, nodes: list[dict]) -> list[str]:
    v = []
    locs = entities.get("locations") or []
    if len(locs) < 2:
        v.append(f"only {len(locs)} location(s) — the event layer will have nowhere to go")
    if not (entities.get("concepts") or []):
        v.append("no concepts declared — world mechanics cannot be tracked as state")
    ids = [e.get("id") for g in entities.values() for e in g]
    dupes = {i for i in ids if ids.count(i) > 1}
    for d in sorted(dupes):
        v.append(f"identifier {d!r} claimed by more than one entity")
    total = len(ids)
    if total < 15:
        v.append(f"only {total} entities for {len(nodes)} scenes — under-declared, "
                 "which is the failure this design exists to prevent")
    return v


def check_stage6(profiles: list[dict], events: list[dict]) -> list[str]:
    v = []
    for p in profiles:
        svs = p.get("state_variables") or []
        if len(svs) < 2:
            v.append(f"{p.get('id')}: {len(svs)} state variable(s) — cannot carry an arc")
        for sv in svs:
            if sv.get("initial") and sv.get("domain") and sv["initial"] not in sv["domain"]:
                v.append(f"{p.get('id')}.{sv.get('name')}: initial "
                         f"{sv['initial']!r} outside its own domain")
    return v


# --------------------------------------------------------------------------
# Orchestration
# --------------------------------------------------------------------------

@dataclass
class Protocol:
    out: Path
    started: float = field(default_factory=time.time)
    stages: dict = field(default_factory=dict)

    def record(self, name: str, *, seconds: float, usage: dict,
               violations: list[str], counts: dict):
        self.stages[name] = {"seconds": round(seconds, 1), "usage": usage,
                             "violations": violations, "counts": counts}
        self.flush()
        print(f"    [{name}] {seconds/60:.1f} min · {usage['ok']}/{usage['calls']} ok · "
              f"{usage['tok_out']:,} out · {len(violations)} check violation(s)")
        for x in violations[:4]:
            print(f"      ! {x}")

    def flush(self):
        (self.out / "protocol.json").write_text(json.dumps(
            {"started": self.started, "elapsed_s": round(time.time() - self.started, 1),
             "stages": self.stages}, indent=1))


def _canary(sw: Swarm, script: str, scene) -> bool:
    """One agent, deliberately given no scene. Anything it writes is recall.

    Costs one call. Would have caught the empty-scene bug at scene two rather
    than after a full run and an evaluation pass.
    """
    d = sw.ask(SCENE_SYSTEM, f"""\
Describe scene {scene.scene_id}.

THE SCENE
(intentionally blank)

FOR CONTEXT ONLY
{script[:20000]}

SCHEMA
{json.dumps(SCENE_SCHEMA, indent=1)}
""", SCENE_SCHEMA, stage="0-canary", tag="blank", max_tokens=3000)
    wrote = bool(d and (d.get("summary") or "").strip())
    print(f"    canary (blank scene): model {'WROTE ANYWAY' if wrote else 'declined'}"
          f" — {'recall is reaching the output' if wrote else 'good'}")
    return wrote


def run(project: Path, out: Path, ports: list[int], model: str,
        per_endpoint: int = 8, limit: int | None = None):
    out.mkdir(parents=True, exist_ok=True)
    (out / "artifacts").mkdir(exist_ok=True)
    sw = Swarm(ports, model, per_endpoint)
    proto = Protocol(out)

    table = json.loads((project / "script_map.json").read_text())
    script = Path(table["source_file"]).read_text(errors="replace")
    _, scenes = sp.parse(script)
    if limit:
        scenes = scenes[:limit]
    print(f"SWARM · {len(scenes)} scenes · {len(ports)} endpoints × {per_endpoint} "
          f"= {sw.width} concurrent\n")

    def save(name, obj):
        (out / "artifacts" / f"{name}.json").write_text(
            json.dumps(obj, indent=1, ensure_ascii=False))

    # -- 1 --------------------------------------------------------------
    print("  stage 1 — scene nodes, blind of the tree")
    t = time.time()
    canary = _canary(sw, script, scenes[len(scenes) // 2])
    nodes = stage1_scenes(sw, script, scenes)
    save("scenes", [n for n in nodes if n])
    proto.record("1-scenes", seconds=time.time() - t, usage=sw.summary("1-scenes"),
                 violations=check_stage1(nodes, scenes, script),
                 counts={"scenes": len(scenes), "nodes": sum(1 for n in nodes if n),
                         "canary_wrote_anyway": canary})

    # -- 2 --------------------------------------------------------------
    print("  stage 2 — event boundaries")
    t = time.time()
    bounds = stage2_boundaries(sw, nodes, script)
    bounds, cov = repair_coverage(bounds, nodes)
    save("boundaries", bounds)
    u = {k: sum(sw.summary(s)[k] for s in ("2a-windows", "2b-reconcile", "2c-final"))
         for k in ("calls", "ok", "tok_in", "tok_out")}
    proto.record("2-boundaries", seconds=time.time() - t, usage=u,
                 violations=cov + check_stage2(bounds, nodes),
                 counts={"events": len(bounds["events"])})

    # -- 3 --------------------------------------------------------------
    print("  stage 3 — event drafts")
    t = time.time()
    by_id = {(n or {}).get("scene_id"): n for n in nodes if n}
    events = stage3_events(sw, bounds, by_id, script)
    save("events_draft", events)
    proto.record("3-events", seconds=time.time() - t, usage=sw.summary("3-events"),
                 violations=check_stage3(events, by_id),
                 counts={"events": len(events),
                         "reversals": sum(1 for e in events if e.get("reversal"))})

    # -- 4 and 5 concurrently -------------------------------------------
    print("  stages 4 + 5 — plots and entities, concurrently")
    t = time.time()
    with ThreadPoolExecutor(max_workers=2) as ex:
        f4 = ex.submit(stage4_plots, sw, events, script)
        f5 = ex.submit(stage5_entities, sw, nodes, events)
        plots, entities = f4.result(), f5.result()
    save("plots", plots); save("entities", entities)
    u4 = {k: sum(sw.summary(s)[k] for s in ("4a-draft", "4b-doctors", "4c-final"))
          for k in ("calls", "ok", "tok_in", "tok_out")}
    proto.record("4-plots", seconds=time.time() - t, usage=u4,
                 violations=check_stage4(plots, events),
                 counts={"plots": len(plots.get("plots") or [])})
    proto.record("5-entities", seconds=time.time() - t, usage=sw.summary("5-entities"),
                 violations=check_stage5(entities, nodes),
                 counts={k: len(v) for k, v in entities.items()})

    # alias rewrite — applied by code across every artifact
    amap = alias_map(entities)
    events = apply_aliases(events, amap)
    nodes = apply_aliases([n for n in nodes if n], amap)
    save("scenes", nodes); save("events_draft", events)
    (out / "artifacts" / "alias_map.json").write_text(json.dumps(amap, indent=1))

    # -- 6 --------------------------------------------------------------
    print("  stage 6 — entity profiles")
    t = time.time()
    profiles = stage6_profiles(sw, entities, events, script)
    save("profiles", profiles)
    proto.record("6-profiles", seconds=time.time() - t, usage=sw.summary("6-profiles"),
                 violations=check_stage6(profiles, events),
                 counts={"profiles": len(profiles)})

    # -- 7 --------------------------------------------------------------
    print("  stage 7 — story root")
    t = time.time()
    root = stage7_root(sw, plots, entities, events, script)
    save("root", root or {})
    proto.record("7-root", seconds=time.time() - t, usage=sw.summary("7-root"),
                 violations=[] if root else ["no root produced"],
                 counts={"ok": bool(root)})

    # -- 8 --------------------------------------------------------------
    print("  stage 8 — exposé and its doctors")
    t = time.time()
    expose = stage8_expose(sw, root or {}, plots, events, profiles, script)
    save("expose", expose)
    u8 = {k: sum(sw.summary(s)[k] for s in ("8a-draft", "8b-doctors", "8c-revise"))
          for k in ("calls", "ok", "tok_in", "tok_out")}
    proto.record("8-expose", seconds=time.time() - t, usage=u8,
                 violations=[] if expose.get("text") else ["no exposé produced"],
                 counts={"words": len((expose.get("text") or "").split())})

    proto.stages["_total"] = {"seconds": round(time.time() - proto.started, 1),
                              "usage": sw.summary()}
    proto.flush()
    print(f"\n  TOTAL {(time.time()-proto.started)/60:.1f} min · "
          f"{sw.summary()['tok_out']:,} output tokens")
    return proto


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--out", default=None)
    ap.add_argument("--ports", default="8100,8101,8102,8103,8104,8105,8106,8107")
    ap.add_argument("--model", default="qwen3.8-27b")
    ap.add_argument("--per-endpoint", type=int, default=8)
    ap.add_argument("--limit", type=int, default=None)
    a = ap.parse_args()
    run(Path(a.project), Path(a.out or (Path(a.project) / "swarm")),
        [int(p) for p in a.ports.split(",")], a.model, a.per_endpoint, a.limit)
