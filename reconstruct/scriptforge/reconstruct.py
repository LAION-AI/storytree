"""The reconstruction driver.

    S0  parse        deterministic — anchor table, no model involved
    S1  story_root   from the whole script
    S2  expose       from the whole script
    S3  plots        from the whole script
    S4  entities     from the whole script; declares the state variables
    S5  events       the causal DAG over the whole script
    S6  scenes       ONE NODE PER PARSED SCENE, each preceded by a blind
                     transition and followed by a sighted node
    S7  bind         prose attached by reference to the anchor table

Only S6 runs the two-call blind/sighted split, because that is where a forecast
is meaningful: the upper layers describe the work as a whole, and there is
nothing to predict about a thing you are summarising.

Artifacts land in the same shape the forward pipeline produces, so the viewer,
the validator, the fold and the co-writer all work on a reconstruction without
knowing it is one. The differences are additive: every scene node carries
`bound_scene_id` and `divergence`, and the project carries `script_map.json`.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path

from . import reverse, screenplay as sp, timeline, validate
from .backends import AwaitingAgent, Backend, BackendError
from .nodegen import entity_digest, event_digest, live_state
from .schemas import SCHEMAS
from .transitions import TRANSITION_SCHEMA, grade, score_transition


@dataclass
class ReconResult:
    stages: list[str] = field(default_factory=list)
    scenes_bound: int = 0
    transitions: int = 0
    divergence: list[dict] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    pending: list[dict] = field(default_factory=list)


class Reconstructor:
    def __init__(self, project, backend: Backend, script_path: Path, *,
                 options: dict | None = None, blind_transitions: bool = True,
                 inline_prose: bool = False, verbose: bool = True):
        self.project = project
        self.backend = backend
        self.script_path = Path(script_path)
        self.options = options or {}
        self.blind_transitions = blind_transitions
        self.inline_prose = inline_prose
        self.verbose = verbose
        self.project.ensure()
        self.tdir = self.project.root / "transitions"
        self.tdir.mkdir(parents=True, exist_ok=True)
        self._text: str | None = None
        self._scenes: list[sp.Scene] | None = None

    def log(self, m):
        if self.verbose:
            print(m, flush=True)

    # -- S0 ------------------------------------------------------------------

    def parse_script(self, *, force: bool = False) -> tuple[str, list[sp.Scene]]:
        if self._text is not None and not force:
            return self._text, self._scenes

        raw = self.script_path.read_text(encoding="utf-8", errors="replace")
        text, scenes = sp.parse(raw)
        table = sp.anchor_table(text, scenes)
        problems = sp.verify(text, scenes, table)

        self.log(f"  · parse       {len(scenes)} scenes · "
                 f"{sp.summarize(scenes)['estimated_pages_a4']} A4 pages · "
                 f"coverage {table['coverage']:.0%}")
        for p in problems:
            self.log(f"      ! {p}")
        if any("no scenes found" in p for p in problems):
            raise BackendError("the file does not parse as a screenplay")

        table["source_file"] = str(self.script_path.resolve())
        table["summary"] = sp.summarize(scenes)
        table["problems"] = problems
        (self.project.root / "script_map.json").write_text(
            json.dumps(table, indent=1, ensure_ascii=False) + "\n")
        # a normalized copy so offsets stay meaningful even if the source moves
        (self.project.root / "script.normalized.txt").write_text(text)

        self._text, self._scenes = text, scenes
        return text, scenes

    def script_map(self) -> dict:
        return json.loads((self.project.root / "script_map.json").read_text())

    # -- S1..S4 --------------------------------------------------------------

    def _overview(self) -> dict:
        text, scenes = self.parse_script()
        return reverse.script_overview(sp.summarize(scenes),
                                       [dict(sp.scene_digest([s])[0], heading=s.heading)
                                        for s in scenes])

    def run_upper(self, *, force: bool = False) -> None:
        text, _ = self.parse_script()
        overview = self._overview()

        specs = [
            ("story_root", lambda: reverse.story_root_prompt(text, overview, self.options)),
            ("expose", lambda: reverse.expose_prompt(self.project.load("story_root"), text, overview)),
            ("plots", lambda: reverse.plots_prompt(self.project.load("story_root"),
                                                   self.project.load("expose"), text, overview)),
            ("entities", lambda: reverse.entities_prompt(self.project.load("story_root"),
                                                         self.project.load("expose"),
                                                         self.project.load("plots"), text)),
        ]
        for stage, build in specs:
            if self.project.load(stage) is not None and not force:
                self.log(f"  · {stage:<11} present, skipping")
                continue
            prompt = build()
            self.log(f"  · {stage:<11} reconstructing ({len(prompt):,} prompt chars)")
            doc = self.backend.complete_json(reverse.SIGHTED_SYSTEM, prompt,
                                             SCHEMAS[stage], stage=stage, tag=f"recon.{stage}")
            self.project.save(stage, doc)
            errs = validate.validate_artifact(stage, doc)
            if errs:
                self.log(f"      schema: {len(errs)} issue(s) — {errs[0][:100]}")

    # -- S5 ------------------------------------------------------------------

    def run_events(self, *, force: bool = False) -> None:
        if self.project.load("events") is not None and not force:
            self.log("  · events      present, skipping")
            return
        text, scenes = self.parse_script()
        root = self.project.load("story_root")
        plots = self.project.load("plots")
        ents = self.project.load("entities")

        prompt = f"""\
RECONSTRUCT THE EVENT CHAIN (layer L5)

An event is something that happens at a locatable point in story time and
changes at least one declared state variable of at least one entity. Events are
NOT scenes: one event may span several scenes, one scene may contain several.

STORY ROOT
{json.dumps({k: root.get(k) for k in ('title','form','genre_primary','setting','state_dimensions','keep_in_mind')}, indent=1, ensure_ascii=False)}

PLOTS
{json.dumps(plots, indent=1, ensure_ascii=False)}

THE ONLY VARIABLES THAT EXIST
{json.dumps(entity_digest(ents.get('entities', {})), indent=1, ensure_ascii=False)}

THE SCENE INDEX (headings only)
{json.dumps([{'scene_id': s.scene_id, 'heading': s.heading, 'speakers': s.speakers} for s in scenes], indent=1, ensure_ascii=False)}

THE SCREENPLAY
{text}

WHAT TO PRODUCE

The causal DAG this script actually runs. For each event: story_time.index
ascending, exactly one primary_plot, the plot spine steps it discharges,
participants and location as entity ids, a summary, an `action` of 60-160 words
in flat third person with NO direct speech, and `state_changes` naming declared
variables with the values they actually hold before and after.

`scenes` on each event lists the parsed scene ids where it plays — use the ids
from the scene index above. Every parsed scene must be named by at least one
event, and every event must name at least one scene.

Extract what is there. Do not invent events the script does not contain.

{reverse._schema_block('events')}
"""
        self.log(f"  · events      reconstructing ({len(prompt):,} prompt chars)")
        doc = self.backend.complete_json(reverse.SIGHTED_SYSTEM, prompt,
                                         SCHEMAS["events"], stage="events", tag="recon.events")
        self.project.save("events", doc)

    # -- S6: the two-call split ---------------------------------------------

    def _ctx(self, upto_scene_index: int) -> dict:
        docs = self.project.load_all()
        ents = (docs["entities"] or {}).get("entities", {})
        events = (docs["events"] or {}).get("events", {})
        scenes_so_far = (self.project.load("scenes") or {}).get("scenes", {})
        prior = {sid: {"heading": s.get("story_time_label"),
                       "function": s.get("dramatic_function"),
                       "last_beat": (s.get("beats") or [{}])[-1].get("text", "")}
                 for sid, s in scenes_so_far.items()}
        return {
            "root": docs["story_root"],
            "expose": {k: v for k, v in (docs["expose"] or {}).items()
                       if k in ("ending_first", "synopsis")},
            "plots": (docs["plots"] or {}).get("plots"),
            "entities": entity_digest(ents),
            "events": event_digest(events),
            "prior": prior or None,
            "live_state": self._live(ents, scenes_so_far),
        }

    def _steps_reached(self) -> dict:
        """The highest spine step each plot has actually reached so far."""
        events = (self.project.load("events") or {}).get("events", {})
        scenes_done = set((self.project.load("scenes") or {}).get("scenes", {}))
        reached: dict[str, int] = {}
        plots = {p["plot_id"]: p for p in (self.project.load("plots") or {}).get("plots", [])}
        for ev in events.values():
            if not (set(ev.get("scenes") or []) & scenes_done):
                continue
            for b in ev.get("plot_bindings") or []:
                spine = plots.get(b.get("plot"), {}).get("spine", {})
                n = (spine.get(b.get("step")) or {}).get("step")
                if n is not None:
                    reached[b["plot"]] = max(reached.get(b["plot"], 0), n)
        return reached

    def _live(self, ents: dict, scenes_so_far: dict) -> dict:
        if not scenes_so_far:
            return {eid: e.get("state", {}) for eid, e in ents.items()}
        fold = timeline.fold({"entities": ents}, self.project.load("events") or {"events": {}},
                             {"scenes": scenes_so_far})
        return {eid: e.get("state", {}) for eid, e in fold.final.items()}

    def run_scenes(self, *, limit: int | None = None, force: bool = False) -> ReconResult:
        result = ReconResult()
        text, scenes = self.parse_script()
        table = self.script_map()
        existing = (self.project.load("scenes") or {"scenes": {}})["scenes"]
        done = 0

        for scene in scenes:
            node_id = scene.scene_id
            if node_id in existing and not force:
                continue
            if limit and done >= limit:
                break

            ctx = self._ctx(scene.index)
            env = reverse.envelope(scene, len(scenes) - scene.index, len(scenes))
            # what the blind call may see is strictly less than what the node sees
            reached = self._steps_reached()
            blind_ctx = reverse.blind_context(ctx, reached)

            # ---- blind ----
            tr = None
            tpath = self.tdir / f"{node_id}.json"
            if self.blind_transitions:
                if tpath.exists():
                    tr = json.loads(tpath.read_text())
                else:
                    self.log(f"  · {node_id}     blind transition")
                    try:
                        tr = None
                        for attempt in (1, 2):
                            cand = self.backend.complete_json(
                                reverse.BLIND_SYSTEM,
                                reverse.blind_transition_prompt("scene", node_id, blind_ctx, env),
                                TRANSITION_SCHEMA, stage="transition.blind",
                                tag=f"blind.{node_id}" + ("" if attempt == 1 else f".retry{attempt}"))
                            why = _degenerate(cand)
                            if not why:
                                tr = cand
                                break
                            self.log(f"      rejected: {why}"
                                     + (" — retrying" if attempt == 1 else " — giving up"))
                            result.errors.append(f"{node_id}: degenerate transition ({why})")
                        if tr is None:
                            continue          # no transition beats a fake one
                        tpath.write_text(json.dumps(tr, indent=1, ensure_ascii=False) + "\n")
                        sc = score_transition(tr)
                        verdict, gaps = grade(sc)
                        leak = _leakage(tr)
                        self.log(f"      {sc['words']:,} words · {verdict}"
                                 + (f" · LEAKAGE: {leak[0]}" if leak else ""))
                        if leak:
                            result.errors.append(f"{node_id}: blind trace leaked hindsight — {leak[0]}")
                        result.transitions += 1
                    except AwaitingAgent as a:
                        result.pending.append({"tag": a.tag, "packet": a.packet_path,
                                               "output": a.output_path}); return result

            # ---- sighted ----
            self.log(f"  · {node_id}     node (bound to {scene.word_count} words of script)")
            meta = dict(table["scenes"][node_id], scene_id=node_id)
            try:
                doc = self.backend.complete_json(
                    reverse.SIGHTED_SYSTEM,
                    reverse.scene_node_prompt(node_id, ctx, tr or {}, meta, scene.text(text)),
                    reverse.SCENE_NODE_SCHEMA, stage="scene.node", tag=f"node.{node_id}")
            except AwaitingAgent as a:
                result.pending.append({"tag": a.tag, "packet": a.packet_path,
                                       "output": a.output_path}); return result

            node = doc.get("scene") or {}
            node.setdefault("scene_id", node_id)
            node["bound_scene_id"] = node_id
            existing[node_id] = node
            self.project.save("scenes", {"scenes": existing})
            result.scenes_bound += 1
            done += 1

            d = node.get("divergence") or {}
            if d:
                result.divergence.append({"scene": node_id,
                                          "quality": d.get("forecast_quality"),
                                          "missed": len(d.get("missed") or [])})
                self.log(f"      forecast quality {d.get('forecast_quality')} · "
                         f"{len(d.get('missed') or [])} missed")

        return result

    # -- S7 ------------------------------------------------------------------

    def bind_prose(self) -> int:
        """Attach the script's own text to each scene node.

        By default this stores a reference — the anchor plus the span — rather
        than a copy, so the derived project stays a description of the script and
        the script stays in the user's file. `--inline-prose` opts into embedding
        the passages for offline viewing.
        """
        text, scenes = self.parse_script()
        table = self.script_map()
        recovered = sp.split_by_anchors(text, table)
        nodes = (self.project.load("scenes") or {"scenes": {}})["scenes"]

        refs = {}
        n = 0
        for sid, node in nodes.items():
            bound = node.get("bound_scene_id", sid)
            if bound not in recovered:
                continue
            refs[sid] = {
                "bound_scene_id": bound,
                "start_char": table["scenes"][bound]["start_char"],
                "end_char": table["scenes"][bound]["end_char"],
                "start_quote": table["scenes"][bound]["start_quote"],
                "end_quote": table["scenes"][bound]["end_quote"],
                "words": table["scenes"][bound]["word_count"],
            }
            if self.inline_prose:
                (self.project.prose_dir / f"{sid}.md").write_text(recovered[bound].strip() + "\n")
            n += 1
        (self.project.root / "prose_refs.json").write_text(
            json.dumps(refs, indent=1, ensure_ascii=False) + "\n")
        return n

    # -- checks specific to reconstruction -----------------------------------

    def check_binding(self) -> list[str]:
        problems = []
        table = self.script_map()
        nodes = (self.project.load("scenes") or {"scenes": {}})["scenes"]
        parsed = set(table["scenes"])
        bound = {}
        for sid, node in nodes.items():
            b = node.get("bound_scene_id")
            if not b:
                problems.append(f"{sid}: no bound_scene_id")
            elif b not in parsed:
                problems.append(f"{sid}: bound to {b}, which is not a parsed scene")
            elif b in bound:
                problems.append(f"{sid} and {bound[b]} both claim {b} — binding must be one to one")
            else:
                bound[b] = sid
        for p in sorted(parsed - set(bound)):
            problems.append(f"{p}: parsed from the script but no node owns it")
        return problems


MIN_TRANSITION_WORDS = 400
REQUIRED_TOP_LEVEL = ("craft", "decision")


def _degenerate(tr) -> str:
    """Catch a response that is shaped like an answer but carries nothing.

    glm-5.2 was observed returning the literal document {"ref": "sc-004"} — nine
    tokens, finish_reason "stop", no error anywhere. A pipeline that accepts that
    writes a fake transition to disk and keeps going, which is worse than
    failing, because the gap is then invisible.
    """
    if not isinstance(tr, dict):
        return f"not an object ({type(tr).__name__})"
    missing = [k for k in REQUIRED_TOP_LEVEL if k not in tr]
    if missing:
        return f"missing {', '.join(missing)}; keys were {sorted(tr)[:6]}"
    words = len(json.dumps(tr, ensure_ascii=False).split())
    if words < MIN_TRANSITION_WORDS:
        return f"only {words} words"
    return ""


_HINDSIGHT = [
    "the script", "the screenplay", "as it turns out", "we later learn",
    "later in the film", "in the finished", "the writer chose", "eventually reveals",
    "it is revealed that", "we find out",
]


def _leakage(transition: dict) -> list[str]:
    """Catch a blind trace that peeked.

    Crude but effective: a transition written as if the outcome were unknown has
    no reason to refer to the script as an object or to narrate downstream
    consequences as fact.
    """
    blob = json.dumps(transition, ensure_ascii=False).lower()
    return [phrase for phrase in _HINDSIGHT if phrase in blob]
