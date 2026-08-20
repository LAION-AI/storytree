#!/usr/bin/env python3
"""Derive an event's skeleton from its member scenes, before any model is asked anything.

The standing principle for every layer above scenes: **establish the facts procedurally,
then let the model interpret on top of them.** Anything computable from the layer below is
computed, not requested. The model is asked only for what code cannot do — condensing a run
of changes into one arc, reading what it means, and saying how it connects outward.

Three builds of the event layer justify this. Build 1 and 2 asked the model to name its own
entities, decide which register moved, and cite its own evidence, and the judges found
exactly the failures that invites: a police unit given the ship operator's state, a register
marked `moved` from a value to the same value, an event turning on a phone that appears
nowhere in its entity list. None of those are judgement failures. They are bookkeeping
failures on facts the scene layer had already recorded correctly.

So the scaffold below computes, per event:

  * the **entity roster** — the union of everyone present and everything that changes,
    including non-persons, canonicalised. The model may not add to it or remove from it.
  * per entity, the **scenes it actually appears in** — which makes an evidence pointer
    checkable rather than decorative.
  * per entity, the **change ledger**: every `what_changes` the scene layer recorded for it,
    in scene order, with its axis and evidence. This is the raw material of the state triple,
    and it means `moved` is derivable rather than asserted.
  * the **mind material** the scene layer already found, so interiority is condensed from
    what was established rather than re-invented.
  * the **carried uncertainty** — every scene-level doubt, so it travels instead of being
    silently promoted to fact.
"""

from __future__ import annotations

import re
from collections import OrderedDict
from typing import Any, Dict, List, Optional, Sequence

# The scene layer's `axis` vocabulary is free-form. These map the common ones onto the event
# layer's registers so the ledger can be filed under the right heading without a model call.
# Anything unrecognised is kept verbatim and shown to the model as `axis` — a wrong guess
# here would be worse than no guess, because it would silently file a change under a register
# it does not belong to.
_AXIS_TO_REGISTER = {
    "knowledge": "knowledge", "belief": "knowledge", "understanding": "knowledge",
    "awareness": "knowledge", "information": "knowledge",
    "location": "positional", "position": "positional", "positional": "positional",
    "movement": "positional",
    "condition": "physical", "physical": "physical", "health": "physical",
    "injury": "physical", "body": "physical",
    "emotional": "emotional", "emotion": "emotional", "feeling": "emotional",
    "mood": "emotional", "resolve": "emotional", "morale": "emotional",
    "relationship": "relational", "relational": "relational", "trust": "relational",
    "loyalty": "relational", "alliance": "relational",
    "status": "status", "role": "status", "standing": "status", "authority": "status",
    "possessions": "status", "agency": "status",
    "safety": "safety", "danger": "safety", "exposure": "safety", "threat": "safety",
    "security": "safety",
}


def _norm(name: str) -> str:
    return re.sub(r"\s+", " ", (name or "").strip())


def _key(name: str) -> str:
    """Fold case and common decorations so `NEO`, `Neo` and `Neo (V.O.)` are one entity."""
    n = _norm(name).casefold()
    n = re.sub(r"\s*\((v\.?o\.?|o\.?s\.?|cont'?d)\)\s*", " ", n)
    return n.strip(" .,-")


def canonical_roster(scene_nodes: Sequence[Dict[str, Any]]) -> Dict[str, str]:
    """Map every spelling seen in these scenes to one canonical form.

    The most frequent spelling wins, with a preference for title case over shouting, because
    screenplay speaker cues are upper-case and the prose is not.
    """
    counts: Dict[str, Dict[str, int]] = {}
    for node in scene_nodes:
        names = list(node.get("present") or [])
        names += [c.get("who") for c in node.get("what_changes") or [] if c.get("who")]
        names += [m.get("who") for m in node.get("minds") or [] if isinstance(m, dict) and m.get("who")]
        names += list(node.get("objects_that_matter") or [])
        for raw in names:
            name = _norm(str(raw))
            if not name:
                continue
            counts.setdefault(_key(name), {}).setdefault(name, 0)
            counts[_key(name)][name] += 1
    mapping = {}
    for variants in counts.values():
        winner = max(variants, key=lambda v: (variants[v], not v.isupper(), len(v)))
        for v in variants:
            mapping[v] = winner
    return mapping


def build_scaffold(scene_ids: Sequence[str], scene_nodes: Sequence[Dict[str, Any]],
                   previous_exits: Optional[Dict[str, Dict[str, str]]] = None,
                   canon: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """Everything about this event that can be known without asking a model.

    `canon` should be built over the **whole film**, not this event. Folded per-event, a
    character who happens to be written `NEO` in all five member scenes has nothing to fold
    into and stays shouting, which then reads as a different entity to the next event. The
    roster only unifies if it sees every spelling in the work.
    """
    order = {sid: i for i, sid in enumerate(scene_ids)}
    canon = canon if canon is not None else canonical_roster(scene_nodes)
    entities: "OrderedDict[str, Dict[str, Any]]" = OrderedDict()

    def slot(raw_name: str) -> Dict[str, Any]:
        name = canon.get(_norm(str(raw_name)), _norm(str(raw_name)))
        if name not in entities:
            entities[name] = {"entity": name, "appears_in": [], "is_person": True,
                              "changes": [], "mind_material": [],
                              "entry_from_previous_event": (previous_exits or {}).get(name)}
        return entities[name]

    objects = set()
    for node in scene_nodes:
        sid = node.get("scene_id")
        for raw in node.get("present") or []:
            entry = slot(raw)
            if sid not in entry["appears_in"]:
                entry["appears_in"].append(sid)
        for raw in node.get("objects_that_matter") or []:
            entry = slot(raw)
            entry["is_person"] = False
            objects.add(entry["entity"])
            if sid not in entry["appears_in"]:
                entry["appears_in"].append(sid)
        for change in node.get("what_changes") or []:
            if not change.get("who"):
                continue
            entry = slot(change["who"])
            axis = _norm(str(change.get("axis") or ""))
            entry["changes"].append({
                "scene": sid,
                "axis": axis,
                "register": _AXIS_TO_REGISTER.get(axis.casefold()),
                "before": change.get("before"),
                "after": change.get("after"),
                "evidence": change.get("evidence"),
            })
            if sid not in entry["appears_in"]:
                entry["appears_in"].append(sid)
        for mind in node.get("minds") or []:
            if not isinstance(mind, dict) or not mind.get("who"):
                continue
            entry = slot(mind["who"])
            entry["mind_material"].append({
                "scene": sid,
                **{k: v for k, v in mind.items() if k != "who" and v},
            })

    for entry in entities.values():
        entry["appears_in"].sort(key=lambda s: order.get(s, 0))
        entry["changes"].sort(key=lambda c: order.get(c["scene"], 0))
        # Registers the scene layer already witnessed a change on. `moved` is then a fact to
        # be transcribed rather than a judgement to be made — which is what stops it from
        # being set on a register whose entry and exit say the same thing.
        entry["registers_with_recorded_change"] = sorted(
            {c["register"] for c in entry["changes"] if c["register"]})

    # Trim the roster to entities that carry information. An entity the scene layer recorded
    # no change for, that appears in a single scene, is a walk-on: a build-1 judge found
    # exactly these being handed eighteen empty fields each ("another woman in white"). They
    # are kept in `background` so nothing is lost, but they do not get a state triple.
    keep, background = [], []
    for entry in entities.values():
        significant = (
            bool(entry["changes"])                    # something about it changed
            or len(entry["appears_in"]) > 1           # it persists across the event
            or not entry["is_person"]                 # objects are here because they matter
            or bool(entry["mind_material"])           # the scene layer read its mind
            or entry.get("entry_from_previous_event")  # it carries state in
        )
        (keep if significant else background).append(entry)
    entities = OrderedDict((e["entity"], e) for e in keep)

    uncertainty = []
    for node in scene_nodes:
        for item in node.get("uncertain") or []:
            uncertainty.append({"scene": node.get("scene_id"), "what": item})

    return {
        "scene_ids": list(scene_ids),
        "entities": list(entities.values()),
        "background": [e["entity"] for e in background],
        "objects": sorted(objects),
        "carried_uncertainty": uncertainty,
        "counts": {
            "entities": len(entities),
            "background_dropped": len(background),
            "with_recorded_changes": sum(1 for e in entities.values() if e["changes"]),
            "objects": len(objects),
            "mind_material": sum(len(e["mind_material"]) for e in entities.values()),
            "uncertainties": len(uncertainty),
        },
    }


def exits_by_entity(event_node: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
    """The exit state of every entity, per register, for chaining into the next event."""
    out: Dict[str, Dict[str, str]] = {}
    for triple in event_node.get("state_triples") or []:
        name = triple.get("entity")
        if not name:
            continue
        regs = triple.get("registers")
        pairs = regs.items() if isinstance(regs, dict) else [
            (r.get("register"), r) for r in regs or []]
        out[name] = {rn: slot.get("exit") for rn, slot in pairs if slot and slot.get("exit")}
    return out


def render_scaffold(scaffold: Dict[str, Any]) -> str:
    """The scaffold as the composer sees it: a filled roster, not a blank form."""
    lines = ["ENTITY ROSTER — computed from the member scenes. Complete and closed:",
             "every entity below needs a state triple, and no entity outside it may be added.",
             ""]
    for entry in scaffold["entities"]:
        kind = "person" if entry.get("is_person") else "object"
        lines.append("• {}  [{}]  appears in: {}".format(
            entry["entity"], kind, ", ".join(entry["appears_in"]) or "—"))
        if entry.get("entry_from_previous_event"):
            lines.append("    entry state carried from the previous event:")
            for reg, val in entry["entry_from_previous_event"].items():
                lines.append("      {:<11} {}".format(reg, val))
        if entry["changes"]:
            lines.append("    changes the scene layer recorded, in order:")
            for c in entry["changes"]:
                reg = c["register"] or "?({})".format(c["axis"])
                lines.append("      [{}] {:<11} {}  ->  {}".format(
                    c["scene"], reg, (c["before"] or "")[:70], (c["after"] or "")[:70]))
            lines.append("    => registers with a recorded change: {}".format(
                ", ".join(entry["registers_with_recorded_change"]) or "none typed"))
        else:
            lines.append("    no change recorded by the scene layer")
        if entry["mind_material"]:
            lines.append("    what the scene layer already found about this mind:")
            for m in entry["mind_material"][:4]:
                bits = "; ".join("{}: {}".format(k, str(v)[:80])
                                 for k, v in m.items() if k != "scene")
                lines.append("      [{}] {}".format(m["scene"], bits[:200]))
        lines.append("")
    if scaffold.get("background"):
        lines.append("PRESENT BUT NOT TRACKED — one appearance, nothing recorded as changing.")
        lines.append("Mention them in the prose if they matter; they get no state triple:")
        lines.append("  " + ", ".join(scaffold["background"][:25]))
        lines.append("")
    if scaffold["carried_uncertainty"]:
        lines.append("UNRESOLVED IN THE SCENES — carry these forward, do not resolve them:")
        for u in scaffold["carried_uncertainty"]:
            lines.append("  [{}] {}".format(u["scene"], str(u["what"])[:150]))
    return "\n".join(lines)
