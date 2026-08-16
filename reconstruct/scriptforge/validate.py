"""Deterministic validation of a generated story graph.

The whitepaper's constraints C1-C10 are written for the *analysis* direction,
where a source text exists and every node anchors to a character span. In the
*generation* direction there is no source, so span anchoring (C6) is replaced by
graph-completeness and budget rules, and everything else carries over — most
importantly C5 (state continuity), which becomes stronger here because the state
is not merely described, it is computed by folding patches.

Every failure carries a stable rule id and a message written to be fed straight
back to a model as a repair instruction.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from . import jsonpatch, jsonschema_mini, timeline
from .schemas import SCHEMAS, STATE_DIMENSIONS

SPEECH_MARKS = re.compile(r"[\"“”]|(?<![A-Za-z])'(?=[A-Z])")
MAX_PROFILE_STRING = 180


@dataclass
class Finding:
    rule: str
    severity: str          # "error" | "warning"
    where: str
    message: str

    def __str__(self) -> str:
        return f"[{self.severity.upper():7}] {self.rule} @ {self.where}: {self.message}"


@dataclass
class Report:
    findings: list[Finding] = field(default_factory=list)
    fold: timeline.Fold | None = None

    def add(self, rule: str, severity: str, where: str, message: str) -> None:
        self.findings.append(Finding(rule, severity, where, message))

    def error(self, rule: str, where: str, message: str) -> None:
        self.add(rule, "error", where, message)

    def warn(self, rule: str, where: str, message: str) -> None:
        self.add(rule, "warning", where, message)

    @property
    def errors(self) -> list[Finding]:
        return [f for f in self.findings if f.severity == "error"]

    @property
    def warnings(self) -> list[Finding]:
        return [f for f in self.findings if f.severity == "warning"]

    @property
    def ok(self) -> bool:
        return not self.errors

    def summary(self) -> str:
        return f"{len(self.errors)} error(s), {len(self.warnings)} warning(s)"

    def as_text(self, limit: int | None = None) -> str:
        rows = self.errors + self.warnings
        if limit is not None:
            rows = rows[:limit]
        return "\n".join(str(f) for f in rows) or "clean"


def _words(text: str) -> int:
    return len(text.split())


def _has_direct_speech(text: str) -> bool:
    return bool(SPEECH_MARKS.search(text or ""))


# --------------------------------------------------------------------------
# Per-artifact schema conformance
# --------------------------------------------------------------------------

def validate_artifact(stage: str, doc: dict) -> list[str]:
    schema = SCHEMAS.get(stage)
    if schema is None:
        return []
    return jsonschema_mini.validate(doc, schema)


# --------------------------------------------------------------------------
# Whole-graph validation
# --------------------------------------------------------------------------

def validate_story(
    root: dict | None = None,
    expose: dict | None = None,
    plots_doc: dict | None = None,
    entities_doc: dict | None = None,
    events_doc: dict | None = None,
    scenes_doc: dict | None = None,
    prose: dict[str, str] | None = None,
) -> Report:
    report = Report()

    plots = {p["plot_id"]: p for p in (plots_doc or {}).get("plots", [])}
    entities = (entities_doc or {}).get("entities", {})
    events = (events_doc or {}).get("events", {})
    scenes = (scenes_doc or {}).get("scenes", {})

    if entities and events and scenes:
        report.fold = timeline.fold(entities_doc, events_doc, scenes_doc)

    _check_entities(report, entities)
    _check_plots(report, plots, expose, entities, events)
    _check_events(report, events, plots, entities)
    _check_scenes(report, scenes, events, plots, entities)
    _check_state_continuity(report, scenes, events, entities)
    _check_declaration_vs_realization(report, events, scenes)
    _check_budgets(report, root, expose, events, scenes)
    _check_prose(report, scenes, prose or {})
    _check_continuity_facts(report, scenes)
    _check_t0_leakage(report, entities)
    _check_theatre(report, scenes)
    _check_voices(report, entities)

    return report


# -- G22..G25: the gaps a review found by reading, not by running ------------

CONSCIOUS_ORDER = ["absent", "asleep", "unconscious", "awake"]


def _check_continuity_facts(report: Report, scenes: dict) -> None:
    """G22 — plain physical facts must not contradict between consecutive scenes.

    Declared state variables cover what the story tracks on purpose. This covers
    what it must not contradict by accident: a character asleep at the end of one
    scene and mid-conversation at the start of the next, an object in two hands.
    A review found exactly that class of error sitting inside a graph that passed
    every other check, which is how a validator earns the name continuity
    vocabulary rather than continuity machinery.
    """
    ordered = sorted(scenes, key=lambda s: scenes[s].get("discourse_index", 0))
    for prev_id, next_id in zip(ordered, ordered[1:]):
        prev = scenes[prev_id].get("continuity_facts") or {}
        nxt = scenes[next_id]
        entry = set(nxt.get("present") or [])
        for eid, fact in prev.items():
            if not isinstance(fact, dict):
                continue
            # someone left asleep who is immediately on stage needs a reason
            if fact.get("conscious") in ("asleep", "unconscious") and eid in entry:
                same_time = (nxt.get("story_time_label") or "") == \
                            (scenes[prev_id].get("story_time_label") or "")
                if same_time:
                    report.error("G22.wake", f"{prev_id}->{next_id}",
                                 f"{eid} is {fact['conscious']} at the end of {prev_id} but "
                                 f"present in {next_id} at the same story time")
            if fact.get("present") is False and eid in entry:
                report.warn("G22.present", f"{prev_id}->{next_id}",
                            f"{eid} is recorded absent at the end of {prev_id} and present "
                            f"in {next_id}; if they arrive, the scene should show it")
        # an object cannot be held by two people at once
        holders: dict[str, str] = {}
        for eid, fact in prev.items():
            for obj in (fact.get("holding") or []) if isinstance(fact, dict) else []:
                if obj in holders:
                    report.error("G22.custody", prev_id,
                                 f"{obj} is held by both {holders[obj]} and {eid}")
                holders[obj] = eid


def _check_t0_leakage(report: Report, entities: dict) -> None:
    """G23 — a dossier describes the opening, not the ending.

    An entity profile that already knows how the story turns out has had the
    ending folded back into its own starting state, which quietly removes the
    uncertainty the middle is supposed to generate.
    """
    tells = ("ending", "finale", "climax", "resolution", "will die", "will leave",
             "at the end", "eventually")
    for eid, entity in entities.items():
        for pointer, text in _walk_strings(entity.get("profile", {}), f"/{eid}/profile"):
            low = text.lower()
            for t in tells:
                if t in low:
                    report.warn("G23", pointer,
                                f"the t0 dossier appears to know the ending ({t!r}); a "
                                f"starting state that contains its own outcome removes the "
                                f"uncertainty the story runs on")
                    break
        for key, item in (entity.get("profile", {}).get("backstory") or {}).items():
            if isinstance(item, dict) and any(
                    t in (tag or "").lower() for tag in (item.get("tags") or [])
                    for t in ("ending", "climax", "finale")):
                report.warn("G23.tag", f"{eid}.profile.backstory.{key}",
                            "a t0 backstory sentence is tagged with the ending")


def _walk_strings(node, path=""):
    if isinstance(node, str):
        yield path, node
    elif isinstance(node, dict):
        for k, v in node.items():
            yield from _walk_strings(v, f"{path}/{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from _walk_strings(v, f"{path}/{i}")


def _check_theatre(report: Report, scenes: dict) -> None:
    """G24 — an ethics of the scene is not a theatre of it.

    If nobody in the whole work ever interrupts, takes a cheap shot, or says the
    thing they cannot take back, every character is behaving impeccably and the
    result is competent and inert.
    """
    if not scenes:
        return
    bad = [s for s in scenes.values()
           if (s.get("someone_behaves_badly") or {}).get("what")]
    share = len(bad) / len(scenes)
    if share < 0.2:
        report.warn("G24", "scenes",
                    f"only {len(bad)} of {len(scenes)} scenes contain anyone behaving badly. "
                    f"Everyone is impeccable, which reads as an ethics of the scene and no "
                    f"theatre of it — somebody should interrupt, be unfair, or say the "
                    f"unforgivable thing")


def _check_voices(report: Report, entities: dict) -> None:
    """G25 — two characters who could swap lines are one character twice."""
    sigs: dict[str, list[str]] = {}
    for eid, e in entities.items():
        if e.get("type") not in ("character", "creature"):
            continue
        sig = (e.get("profile") or {}).get("speech_signature")
        if not sig:
            if e.get("salience") in ("major", "supporting"):
                report.warn("G25", eid, "no speech_signature — nothing distinguishes this "
                                        "character's voice from anyone else's")
            continue
        key = " | ".join(str(sig.get(k, "")).lower()[:60] for k in
                         ("sentence_shape", "vocabulary_domain", "verbal_tic"))
        sigs.setdefault(key, []).append(eid)
    for key, ids in sigs.items():
        if len(ids) > 1 and key.strip(" |"):
            report.warn("G25.same", ", ".join(ids),
                        "these characters share a speech signature; with attributions "
                        "removed their lines would be interchangeable")


# -- L3 --------------------------------------------------------------------

def _check_entities(report: Report, entities: dict) -> None:
    for eid, entity in entities.items():
        if entity.get("entity_id") != eid:
            report.error("G8.key", eid, f"entity_id {entity.get('entity_id')!r} does not match its key")

        declared = entity.get("state_variables", {})
        state = entity.get("state", {})

        # G17 — state must mirror state_variables exactly at t0.
        for name, spec in declared.items():
            if name not in state:
                report.error("G17", f"{eid}.state", f"declared variable {name!r} has no value in `state`")
            elif state[name] != spec.get("init"):
                report.error(
                    "G17", f"{eid}.state.{name}",
                    f"t0 value {state[name]!r} != declared init {spec.get('init')!r}",
                )
            if spec.get("dimension") not in STATE_DIMENSIONS:
                report.error("G4.dim", f"{eid}.state_variables.{name}",
                             f"dimension {spec.get('dimension')!r} is outside the closed vocabulary")
            _check_value_domain(report, f"{eid}.state.{name}", spec, state.get(name))
        for name in state:
            if name not in declared:
                report.error("G17", f"{eid}.state", f"{name!r} has a value but is not declared in state_variables")

        if not declared:
            report.warn("G4.novars", eid, "entity declares no state variables, so nothing can happen to it")

        profile = entity.get("profile", {})

        # G12 — arrays are unpatchable in practice; keep them out.
        for pointer in jsonpatch.assert_no_arrays(profile, f"/{eid}/profile"):
            report.error("G12", pointer,
                         "array inside a patchable region — use an id-keyed object instead, "
                         "because JSON Pointer addresses arrays by index and indices shift")

        # G13 — force the sentence-addressability the whole design rests on.
        _check_sentence_decomposition(report, eid, profile, f"/{eid}/profile")
        backstory = profile.get("backstory")
        if not isinstance(backstory, dict) or not backstory:
            report.error("G13.backstory", f"{eid}.profile.backstory",
                         "backstory must be a non-empty sentence map {b01: {text: ...}, ...}")
        else:
            for key, item in backstory.items():
                if not isinstance(item, dict) or "text" not in item:
                    report.error("G13.backstory", f"{eid}.profile.backstory.{key}",
                                 "each backstory entry must be an object with a `text` field")

        for other, rel in entity.get("relationships", {}).items():
            if other not in entities:
                report.error("G8", f"{eid}.relationships", f"relationship points at unknown entity {other!r}")
            if other == eid:
                report.warn("G8.self", eid, "entity has a relationship to itself")


def _check_sentence_decomposition(report: Report, eid: str, node, pointer: str) -> None:
    if isinstance(node, str):
        if len(node) > MAX_PROFILE_STRING:
            report.error(
                "G13", pointer,
                f"prose block of {len(node)} chars inside `profile` — decompose it into a "
                f"sentence map {{k01: {{text: ...}}}} so each sentence is individually patchable",
            )
    elif isinstance(node, dict):
        for key, value in node.items():
            _check_sentence_decomposition(report, eid, value, f"{pointer}/{key}")


def _check_value_domain(report: Report, where: str, spec: dict, value) -> None:
    kind = spec.get("kind")
    if kind == "scalar" and isinstance(spec.get("range"), list) and len(spec["range"]) == 2:
        lo, hi = spec["range"]
        if isinstance(value, (int, float)) and not (lo <= value <= hi):
            report.error("G20", where, f"value {value} outside declared range [{lo}, {hi}]")
    if kind == "enum" and isinstance(spec.get("domain"), list) and spec["domain"]:
        if value not in spec["domain"]:
            report.error("G20", where, f"value {value!r} outside declared domain {spec['domain']}")
    if kind == "bool" and not isinstance(value, bool):
        report.error("G20", where, f"value {value!r} is not a boolean")


# -- L4 --------------------------------------------------------------------

def _check_plots(report: Report, plots: dict, expose: dict | None, entities: dict, events: dict) -> None:
    if not plots:
        return
    events_by_plot: dict[str, list[str]] = {pid: [] for pid in plots}
    bound_steps: dict[str, set[str]] = {pid: set() for pid in plots}
    for eid, event in events.items():
        for pid in event.get("plots", []):
            events_by_plot.setdefault(pid, []).append(eid)
        for binding in event.get("plot_bindings", []):
            bound_steps.setdefault(binding.get("plot", ""), set()).add(binding.get("step", ""))

    for pid, plot in plots.items():
        # G2 — a plot with one event is an incident.
        if events and len(events_by_plot.get(pid, [])) < 2:
            report.error("G2", pid, f"plot has {len(events_by_plot.get(pid, []))} event(s); a plot needs at least 2")

        spine = plot.get("spine", {})
        if not spine:
            report.error("G2.spine", pid, "plot has no spine")
        resolution = plot.get("resolution_step")
        if resolution and resolution not in spine:
            report.error("G2.res", pid, f"resolution_step {resolution!r} is not a spine key")

        steps = sorted(spine.items(), key=lambda kv: kv[1].get("step", 0))
        seen_numbers = [item.get("step") for _, item in steps]
        if len(set(seen_numbers)) != len(seen_numbers):
            report.error("G2.spine", pid, f"duplicate spine step numbers {seen_numbers}")

        for key, step in spine.items():
            if events and key not in bound_steps.get(pid, set()):
                report.error("G2.bind", f"{pid}.spine.{key}",
                             f"spine step {key!r} ({step.get('function')}) is not discharged by any event")
            for because in step.get("because", []):
                if ":" not in because:
                    report.error("G2.because", f"{pid}.spine.{key}",
                                 f"because entry {because!r} must be formatted 'pl-XX:stN'")
                    continue
                other_plot, other_step = because.split(":", 1)
                if other_plot not in plots:
                    report.error("G7", f"{pid}.spine.{key}", f"because references unknown plot {other_plot!r}")
                elif other_step not in plots[other_plot].get("spine", {}):
                    report.error("G7", f"{pid}.spine.{key}",
                                 f"because references unknown step {other_step!r} of {other_plot}")

        for ref in plot.get("agent", []) + plot.get("resistance", []):
            if ref.startswith("pl-"):
                if ref not in plots:
                    report.error("G7", pid, f"resistance names unknown plot {ref!r}")
            elif entities and ref not in entities:
                report.error("G8", pid, f"names entity {ref!r}, which has no dossier in L3")

    # G9 — every synopsis claim must be owned by a plot.
    if expose:
        synopsis = expose.get("synopsis", {})
        covered: set[str] = set()
        for pid, plot in plots.items():
            claims = plot.get("covers_synopsis", [])
            if not claims:
                report.warn("G9", pid, "plot claims no synopsis sentences")
            for key in claims:
                if key not in synopsis:
                    report.error("G9", pid, f"covers_synopsis names unknown synopsis key {key!r}")
                covered.add(key)
        for key in synopsis:
            if key not in covered:
                report.warn("G9.orphan", f"expose.synopsis.{key}",
                            "synopsis sentence is not covered by any plot — either it is not a "
                            "story claim, or a plot is missing")


# -- L5 --------------------------------------------------------------------

def _check_events(report: Report, events: dict, plots: dict, entities: dict) -> None:
    if not events:
        return
    indices: dict[int, str] = {}
    for eid, event in events.items():
        if event.get("event_id") != eid:
            report.error("G8.key", eid, "event_id does not match its key")

        idx = event.get("story_time", {}).get("index")
        if idx in indices:
            report.error("G16", eid, f"story_time.index {idx} is already used by {indices[idx]}")
        indices[idx] = eid

        # G1 — exactly one parent plot, at least one plot.
        primary = event.get("primary_plot")
        listed = event.get("plots", [])
        if not listed:
            report.error("G1", eid, "event serves no plot; if it serves no chain it is mis-conceived")
        if primary not in listed:
            report.error("G1", eid, f"primary_plot {primary!r} is not among plots {listed}")
        for pid in listed:
            if plots and pid not in plots:
                report.error("G7", eid, f"references unknown plot {pid!r}")

        for binding in event.get("plot_bindings", []):
            pid, step = binding.get("plot"), binding.get("step")
            if plots and pid not in plots:
                report.error("G7", eid, f"plot_binding references unknown plot {pid!r}")
            elif plots and step not in plots[pid].get("spine", {}):
                report.error("G7", eid, f"plot_binding references unknown step {step!r} of {pid}")
            if pid not in listed:
                report.error("G1.bind", eid, f"binds to plot {pid!r} which is not in its own plots list")

        # G8 — referential integrity against L3.
        for ref in event.get("participants", []) + [event.get("location")]:
            if ref and entities and ref not in entities:
                report.error("G8", eid, f"references entity {ref!r}, which has no dossier in L3")

        # G4 — every event changes something, against declared variables only.
        changes = event.get("state_changes", [])
        if not changes:
            report.error("G4", eid, "event declares no state change, so by definition it is not an event")
        for i, change in enumerate(changes):
            where = f"{eid}.state_changes[{i}]"
            target, variable = change.get("entity"), change.get("variable")
            if entities:
                entity = entities.get(target)
                if entity is None:
                    report.error("G8", where, f"unknown entity {target!r}")
                elif variable not in entity.get("state_variables", {}):
                    report.error("G4", where,
                                 f"{variable!r} is not declared in {target}'s state_variables "
                                 f"(declared: {sorted(entity.get('state_variables', {}))})")
            expected_path = f"/{target}/state/{variable}"
            if change.get("path") != expected_path:
                report.warn("G4.path", where,
                            f"path {change.get('path')!r} is not the canonical {expected_path!r}")
            if change.get("before") == change.get("after"):
                report.error("G4.noop", where, "before == after, which is not a change")

        # G10 — the corpus is a derived representation, not a script.
        if _has_direct_speech(event.get("action", "")):
            report.error("G10", f"{eid}.action",
                         "contains quotation marks; render speech as reported semantics and "
                         "illocutionary force instead")

    _check_causal_graph(report, events)


def _check_causal_graph(report: Report, events: dict) -> None:
    # G3 — mutual consistency of the two edge lists.
    for eid, event in events.items():
        for other in event.get("causes", []):
            if other not in events:
                report.error("G7", eid, f"causes unknown event {other!r}")
            elif eid not in events[other].get("caused_by", []):
                report.error("G3.sym", eid, f"declares it causes {other}, but {other} does not list it in caused_by")
        for other in event.get("caused_by", []):
            if other not in events:
                report.error("G7", eid, f"caused_by unknown event {other!r}")
            elif eid not in events[other].get("causes", []):
                report.error("G3.sym", eid, f"declares it is caused by {other}, but {other} does not list it in causes")
        if not event.get("caused_by") and not event.get("is_root"):
            report.error("G3.root", eid, "has no cause but is not marked is_root")
        if not event.get("causes") and not event.get("is_sink"):
            report.error("G3.sink", eid, "causes nothing but is not marked is_sink")

    # G3 — causes must not run backwards in story time.
    for eid, event in events.items():
        here = event.get("story_time", {}).get("index", 0)
        for other in event.get("caused_by", []):
            if other in events:
                there = events[other].get("story_time", {}).get("index", 0)
                if there >= here:
                    report.error("G3.time", eid,
                                 f"is caused by {other}, which happens at or after it "
                                 f"(index {there} >= {here})")

    # G3 — acyclicity, by DFS colouring.
    colour: dict[str, int] = {}

    def visit(node: str, trail: list[str]) -> None:
        colour[node] = 1
        for nxt in events.get(node, {}).get("causes", []):
            if nxt not in events:
                continue
            if colour.get(nxt) == 1:
                cycle = " -> ".join(trail[trail.index(nxt):] + [nxt]) if nxt in trail else f"{node} -> {nxt}"
                report.error("G3.cycle", node, f"causal cycle: {cycle}")
            elif colour.get(nxt, 0) == 0:
                visit(nxt, trail + [nxt])
        colour[node] = 2

    for eid in events:
        if colour.get(eid, 0) == 0:
            visit(eid, [eid])

    # G3 — weak connectivity.
    if len(events) > 1:
        adjacency: dict[str, set[str]] = {eid: set() for eid in events}
        for eid, event in events.items():
            for other in event.get("causes", []) + event.get("caused_by", []):
                if other in adjacency:
                    adjacency[eid].add(other)
                    adjacency[other].add(eid)
        start = next(iter(events))
        seen = {start}
        stack = [start]
        while stack:
            node = stack.pop()
            for nxt in adjacency[node]:
                if nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
        for eid in events:
            if eid not in seen:
                report.error("G3.orphan", eid, "event is disconnected from the causal graph")


# -- L6 --------------------------------------------------------------------

def _check_scenes(report: Report, scenes: dict, events: dict, plots: dict, entities: dict) -> None:
    if not scenes:
        return
    covered_events: set[str] = set()
    discourse: dict[int, str] = {}

    for sid, scene in scenes.items():
        if scene.get("scene_id") != sid:
            report.error("G8.key", sid, "scene_id does not match its key")

        idx = scene.get("discourse_index")
        if idx in discourse:
            report.error("G16", sid, f"discourse_index {idx} is already used by {discourse[idx]}")
        discourse[idx] = sid

        # G6 — exactly one parent event.
        primary_event = scene.get("primary_event")
        listed_events = scene.get("events", [])
        if primary_event not in listed_events:
            report.error("G6", sid, f"primary_event {primary_event!r} is not among events {listed_events}")
        for ev in listed_events:
            if events and ev not in events:
                report.error("G7", sid, f"references unknown event {ev!r}")
            covered_events.add(ev)

        # G7 — the primary edges must form a tree: scene -> event -> plot.
        primary_plot = scene.get("primary_plot")
        if primary_plot not in scene.get("plots", []):
            report.error("G7.plot", sid, f"primary_plot {primary_plot!r} is not among plots {scene.get('plots')}")
        if events and primary_event in events:
            parent_plot = events[primary_event].get("primary_plot")
            if primary_plot != parent_plot:
                report.error("G7.tree", sid,
                             f"primary_plot {primary_plot!r} disagrees with the primary_event's "
                             f"primary_plot {parent_plot!r}; the primary edges must form one tree")

        for ref in scene.get("present", []) + scene.get("offstage_referenced", []) + [scene.get("location"), scene.get("pov")]:
            if ref and entities and ref not in entities:
                report.error("G8", sid, f"references entity {ref!r}, which has no dossier in L3")

        beats = scene.get("beats", [])
        if not beats:
            report.error("G18", sid, "scene has no beats")
        if not any(beat.get("changes") for beat in beats):
            report.error("G18", sid, "no beat in this scene changes any state; the scene does not earn its place")

        # G14 — beats must not run backwards in story time inside one scene.
        last_index = -1
        for beat in beats:
            ev = beat.get("event_id")
            if events and ev not in events:
                report.error("G7", f"{sid}#b{beat.get('beat')}", f"beat belongs to unknown event {ev!r}")
                continue
            if ev not in listed_events:
                report.error("G6.beat", f"{sid}#b{beat.get('beat')}",
                             f"beat belongs to event {ev!r}, which the scene does not list in `events`")
            if events:
                index = events[ev].get("story_time", {}).get("index", 0)
                if index < last_index:
                    report.error("G14", f"{sid}#b{beat.get('beat')}",
                                 f"beat belongs to event {ev} (story index {index}) after a beat at "
                                 f"index {last_index}; beats inside a scene must not run backwards")
                last_index = max(last_index, index)

            if _has_direct_speech(beat.get("text", "")):
                report.error("G10", f"{sid}#b{beat.get('beat')}",
                             "beat text contains quotation marks; report speech, do not quote it")

    # G6 — bidirectional completeness.
    for eid in events:
        if eid not in covered_events:
            report.error("G6.uncovered", eid, "event is realized by no scene")

    ordered = sorted(discourse)
    if ordered and ordered != list(range(ordered[0], ordered[0] + len(ordered))):
        report.warn("G16.gap", "scenes", f"discourse_index values are not contiguous: {ordered}")


# -- C5, the important one -------------------------------------------------

def _check_state_continuity(report: Report, scenes: dict, events: dict, entities: dict) -> None:
    if not (scenes and events and entities):
        return
    fold_result = timeline.fold({"entities": entities}, {"events": events}, {"scenes": scenes})

    # G11 — the patches must actually apply.
    for message in fold_result.errors:
        report.error("G11", "fold", message)

    for ref in fold_result.order:
        before = fold_result.states_before[ref.key]
        after = fold_result.states_after[ref.key]
        for i, change in enumerate(ref.beat.get("changes", [])):
            where = f"{ref.scene_id}#b{ref.beat_no}.changes[{i}]"
            op = change.get("op", {})
            path = op.get("path", "")

            # G5 — the declared `before` must equal what is actually there.
            if op.get("op") in ("replace", "remove", "test"):
                if not jsonpatch.exists(before, path):
                    report.error("G5.path", where, f"path {path!r} does not exist in the world state at this point")
                else:
                    actual = jsonpatch.resolve(before, path)
                    if actual != change.get("before"):
                        report.error(
                            "G5", where,
                            f"declares before={change.get('before')!r} at {path}, but the state "
                            f"folded from every prior beat holds {actual!r}. Either an earlier beat "
                            f"left it somewhere else, or this beat's `before` is wrong.",
                        )
            if op.get("op") == "add" and jsonpatch.exists(before, path):
                report.warn("G5.add", where, f"`add` at {path!r}, which already exists; did you mean `replace`?")

            # G5 — and the declared `after` must equal what the op produced.
            if op.get("op") in ("add", "replace", "copy", "move"):
                if jsonpatch.exists(after, path):
                    actual = jsonpatch.resolve(after, path)
                    if actual != change.get("after"):
                        report.error("G5.after", where,
                                     f"declares after={change.get('after')!r}, but the op writes {actual!r}")

            # G26 — an identity patch is a change that changes nothing.
            if change.get("before") == change.get("after"):
                report.error("G26.noop", where,
                             f"before and after are both {change.get('before')!r} — this beat "
                             f"claims a change and performs none")
            if op.get("op") == "replace" and jsonpatch.exists(before, path) and \
                    jsonpatch.resolve(before, path) == op.get("value"):
                report.error("G26.identity", where,
                             f"replaces {path} with the value it already holds")

            # G20 — stay inside the declared domain, at every point in time.
            entity = entities.get(change.get("entity"), {})
            spec = entity.get("state_variables", {}).get(change.get("variable"))
            if spec and jsonpatch.exists(after, path):
                _check_value_domain(report, where, spec, jsonpatch.resolve(after, path))

    # G5 — declared scene entry/exit states must equal the folded state.
    for sid, scene in scenes.items():
        for label, declared in (("entry_states", scene.get("entry_states", {})),
                                ("exit_states", scene.get("exit_states", {}))):
            world = (fold_result.state_entering_scene(sid) if label == "entry_states"
                     else fold_result.state_leaving_scene(sid))
            actual = timeline.project(world, declared)
            for entity_id, variables in declared.items():
                for name, value in variables.items():
                    got = actual.get(entity_id, {}).get(name)
                    if got == "__undeclared__":
                        report.error("G4", f"{sid}.{label}.{entity_id}",
                                     f"{name!r} is not a declared state variable of {entity_id}")
                    elif got != value:
                        report.error(
                            "G5.scene", f"{sid}.{label}.{entity_id}.{name}",
                            f"declares {value!r}, but folding every beat up to this point yields {got!r}",
                        )


def _check_declaration_vs_realization(report: Report, events: dict, scenes: dict) -> None:
    """G15 — L5 declares what must change; L6 must realize exactly that."""
    if not (events and scenes):
        return
    realized: dict[str, set[tuple[str, str]]] = {eid: set() for eid in events}
    for scene in scenes.values():
        for beat in scene.get("beats", []):
            ev = beat.get("event_id")
            if ev not in realized:
                continue
            for change in beat.get("changes", []):
                realized[ev].add((change.get("entity"), change.get("variable")))

    for eid, event in events.items():
        declared = {(c.get("entity"), c.get("variable")) for c in event.get("state_changes", [])}
        for entity_id, variable in sorted(declared - realized[eid]):
            report.error("G15.unrealized", eid,
                         f"declares a change to {entity_id}.{variable}, but no beat of this event "
                         f"carries a patch op for it")
        for entity_id, variable in sorted(realized[eid] - declared):
            report.error("G15.undeclared", eid,
                         f"a beat changes {entity_id}.{variable}, which this event never declared in "
                         f"state_changes; add the declaration or move the change to another event")


# -- budgets ---------------------------------------------------------------

def _check_budgets(report: Report, root: dict | None, expose: dict | None,
                   events: dict, scenes: dict) -> None:
    if expose:
        jacket = _words(expose.get("jacket_copy", ""))
        if not 100 <= jacket <= 170:
            report.warn("G19", "expose.jacket_copy", f"{jacket} words, target 120-150")
        synopsis = sum(_words(s.get("text", "")) for s in expose.get("synopsis", {}).values())
        if not 380 <= synopsis <= 650:
            report.warn("G19", "expose.synopsis", f"{synopsis} words, target 450-550")
        for key, sentence in expose.get("synopsis", {}).items():
            text = sentence.get("text", "")
            if text.count(".") > 2:
                report.warn("G19.sentence", f"expose.synopsis.{key}",
                            "looks like more than one sentence; one sentence per key is what makes "
                            "synopsis claims individually addressable")

    for eid, event in events.items():
        count = _words(event.get("action", ""))
        if not 45 <= count <= 200:
            report.warn("G19", f"{eid}.action", f"{count} words, target 60-160")
        if _words(event.get("summary", "")) > 35:
            report.warn("G19", f"{eid}.summary", "longer than 30 words")

    for sid, scene in scenes.items():
        for beat in scene.get("beats", []):
            count = _words(beat.get("text", ""))
            if not 18 <= count <= 90:
                report.warn("G19", f"{sid}#b{beat.get('beat')}", f"{count} words, target 25-70")
        if scene.get("tension_in") == scene.get("tension_out"):
            report.warn("G19.tension", sid, "tension_in == tension_out; the scene does not move the needle")

    if root:
        target = root.get("constraints", {}).get("scene_count_target")
        if target and scenes and abs(len(scenes) - target) > max(2, target * 0.35):
            report.warn("G19.count", "scenes", f"{len(scenes)} scenes against a target of {target}")
        target = root.get("constraints", {}).get("plot_count")
        if target and root.get("_plot_count") and root["_plot_count"] != target:
            report.warn("G19.count", "plots", "plot count differs from the story root's constraint")


def _check_prose(report: Report, scenes: dict, prose: dict[str, str]) -> None:
    if not prose:
        return
    for sid in scenes:
        if sid not in prose:
            report.warn("G21", sid, "scene has no prose leaf")
    for sid, text in prose.items():
        if sid not in scenes:
            report.error("G21", sid, "prose exists for a scene that is not defined")
            continue
        target = scenes[sid].get("target_words") or 0
        count = _words(text)
        if target and not (target * 0.55 <= count <= target * 1.7):
            report.warn("G21.len", sid, f"prose is {count} words against a target of {target}")
