"""Folding beats into world states.

The world state is a single JSON document keyed by entity id:

    {"ch-01": {<the whole L3 dossier>}, "lo-01": {...}, ...}

At t0 it *is* the L3 entity layer, unmodified. Every subsequent state is
reached by applying RFC 6902 ops, and every op is authored by exactly one beat.
That single-authorship rule is what makes the whole thing reconstructable:

    world_state(T) = apply(world_state_t0, concat(beat.ops for beats before T))

Event-level and scene-level patches are *derived* views over the same beat ops,
grouped differently — an event's patch is the ops of its beats wherever those
beats live, a scene's patch is the ops of its beats in scene order. Neither is
authored separately, so neither can drift from the other.

Canonical order
---------------
Beats are folded in story time: sorted by (event.story_time.index,
scene.discourse_index, beat.beat). For this to agree with the order a reader
experiences inside a single scene, a scene's beats must have non-decreasing
event indices — the validator enforces that (rule G14).
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any

from . import jsonpatch


@dataclass
class BeatRef:
    """One beat, located in both the scene order and the story-time order."""
    scene_id: str
    event_id: str
    beat_no: int
    discourse_index: int
    story_index: int
    beat: dict

    @property
    def key(self) -> str:
        return f"{self.scene_id}#b{self.beat_no}"

    @property
    def ops(self) -> list[dict]:
        return [change["op"] for change in self.beat.get("changes", [])]


@dataclass
class Fold:
    """The result of replaying a story's beats over the t0 world state."""
    world_t0: dict
    order: list[BeatRef]
    states_after: dict[str, dict] = field(default_factory=dict)   # beat key -> world state
    states_before: dict[str, dict] = field(default_factory=dict)  # beat key -> world state
    errors: list[str] = field(default_factory=list)
    final: dict = field(default_factory=dict)

    # -- derived patch views -------------------------------------------------

    def event_patch(self, event_id: str) -> list[dict]:
        ops: list[dict] = []
        for ref in self.order:
            if ref.event_id == event_id:
                ops.extend(ref.ops)
        return ops

    def scene_patch(self, scene_id: str) -> list[dict]:
        ops: list[dict] = []
        for ref in sorted(
            (r for r in self.order if r.scene_id == scene_id), key=lambda r: r.beat_no
        ):
            ops.extend(ref.ops)
        return ops

    def plot_patch(self, plot_id: str, events: dict) -> list[dict]:
        ops: list[dict] = []
        for ref in self.order:
            event = events.get(ref.event_id, {})
            if plot_id in event.get("plots", []):
                ops.extend(ref.ops)
        return ops

    # -- point-in-time queries ----------------------------------------------

    def state_before_beat(self, scene_id: str, beat_no: int) -> dict:
        return self.states_before.get(f"{scene_id}#b{beat_no}", self.world_t0)

    def state_after_beat(self, scene_id: str, beat_no: int) -> dict:
        return self.states_after.get(f"{scene_id}#b{beat_no}", self.world_t0)

    def state_entering_scene(self, scene_id: str) -> dict:
        refs = [r for r in self.order if r.scene_id == scene_id]
        if not refs:
            return self.world_t0
        first = min(refs, key=lambda r: r.beat_no)
        return self.states_before[first.key]

    def state_leaving_scene(self, scene_id: str) -> dict:
        refs = [r for r in self.order if r.scene_id == scene_id]
        if not refs:
            return self.world_t0
        last = max(refs, key=lambda r: r.beat_no)
        return self.states_after[last.key]

    def state_entering_event(self, event_id: str) -> dict:
        refs = [r for r in self.order if r.event_id == event_id]
        if not refs:
            return self.world_t0
        return self.states_before[refs[0].key]

    def state_after_event(self, event_id: str) -> dict:
        refs = [r for r in self.order if r.event_id == event_id]
        if not refs:
            return self.world_t0
        return self.states_after[refs[-1].key]

    def state_at(self, marker: str) -> dict:
        """Resolve 'ev-007', 'sc-003', 'sc-003#b2', or 't0' to a world state."""
        if marker in ("t0", "start", ""):
            return self.world_t0
        if marker in ("end", "final"):
            return self.final
        if "#b" in marker:
            scene_id, beat = marker.split("#b", 1)
            return self.state_after_beat(scene_id, int(beat))
        if marker.startswith("ev-"):
            return self.state_after_event(marker)
        if marker.startswith("sc-"):
            return self.state_leaving_scene(marker)
        raise KeyError(f"cannot resolve time marker {marker!r}")

    # -- per-entity history --------------------------------------------------

    def entity_history(self, entity_id: str) -> list[dict]:
        prefix = f"/{entity_id}/"
        history: list[dict] = []
        for ref in self.order:
            for change in ref.beat.get("changes", []):
                if change["op"]["path"].startswith(prefix):
                    history.append({
                        "scene": ref.scene_id,
                        "beat": ref.beat_no,
                        "event": ref.event_id,
                        "story_index": ref.story_index,
                        "path": change["op"]["path"],
                        "variable": change.get("variable"),
                        "dimension": change.get("dimension"),
                        "before": change.get("before"),
                        "after": change.get("after"),
                        "magnitude": change.get("magnitude"),
                        "beat_text": ref.beat.get("text", ""),
                    })
        return history


# --------------------------------------------------------------------------

def world_state_t0(entities_doc: dict) -> dict:
    """The L3 entity layer, used directly as the initial world state."""
    return copy.deepcopy(entities_doc.get("entities", {}))


def beat_order(events_doc: dict, scenes_doc: dict) -> list[BeatRef]:
    events = events_doc.get("events", {})
    scenes = scenes_doc.get("scenes", {})
    refs: list[BeatRef] = []
    for scene_id, scene in scenes.items():
        discourse = scene.get("discourse_index", 0)
        for beat in scene.get("beats", []):
            event_id = beat.get("event_id", "")
            event = events.get(event_id, {})
            story_index = event.get("story_time", {}).get("index", 10**6)
            refs.append(BeatRef(
                scene_id=scene_id,
                event_id=event_id,
                beat_no=beat.get("beat", 0),
                discourse_index=discourse,
                story_index=story_index,
                beat=beat,
            ))
    refs.sort(key=lambda r: (r.story_index, r.discourse_index, r.beat_no))
    return refs


def fold(entities_doc: dict, events_doc: dict, scenes_doc: dict) -> Fold:
    """Replay every beat over the t0 world state, checkpointing as we go."""
    world = world_state_t0(entities_doc)
    result = Fold(world_t0=copy.deepcopy(world), order=beat_order(events_doc, scenes_doc))

    current = world
    for ref in result.order:
        result.states_before[ref.key] = copy.deepcopy(current)
        try:
            current = jsonpatch.apply_patch(current, ref.ops)
        except jsonpatch.JsonPatchError as exc:
            result.errors.append(f"{ref.key} ({ref.event_id}): patch does not apply — {exc}")
        result.states_after[ref.key] = copy.deepcopy(current)

    result.final = current
    return result


def project(world: dict, declared: dict) -> dict:
    """Pull the same shape as a declared entry/exit_states block out of `world`.

    `declared` is {entity_id: {variable: value}}. Variables are looked up in the
    entity's `state` map first, then as a JSON Pointer relative to the entity.
    """
    out: dict[str, dict] = {}
    for entity_id, variables in declared.items():
        entity = world.get(entity_id)
        if entity is None:
            out[entity_id] = {"__missing_entity__": True}
            continue
        row: dict[str, Any] = {}
        for name in variables:
            state = entity.get("state", {})
            if name in state:
                row[name] = state[name]
            elif jsonpatch.exists(entity, "/" + name.replace(".", "/")):
                row[name] = jsonpatch.resolve(entity, "/" + name.replace(".", "/"))
            else:
                row[name] = "__undeclared__"
        out[entity_id] = row
    return out
