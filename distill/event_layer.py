#!/usr/bin/env python3
"""Build the event layer from finished scene nodes, bottom-up.

The scene layer is the only layer in this project measured against the source. Everything
above it is induced from what the scenes already say, which is the direction that worked:
reading scenes first and inducing upward produced 23 locations against 1 and 11 reversals
against 0 when the top-down pipeline was tried the other way round.

**One caveat on "bottom-up", found by a judge and verified: it is not pure.** The scene nodes
carry an `event_hint` from an earlier 18-event artifact, and 48 of 224 of them cite `ev-XXX`
ids inside `minds` and `sets_up`. Those ids belong to that older segmentation, not to the one
this module produces, so a scene may reference an event id that means something different
here. The layer is therefore induced from scenes that were already told roughly where the
event boundaries were — weaker than a clean bottom-up claim, and stated rather than implied.

An event is a run of consecutive scenes that belong together as one unit of story. Three
stages:

  1. `segment`  — a model reads scene summaries in a window and proposes the boundaries.
                  Boundaries only; no content is written yet, so the decision is cheap and
                  a bad one is cheap to redo.
  2. `compose`  — one agent per event writes the node from its scenes' own state changes.
  3. `verify`   — each event is checked against its neighbours for continuity.

The scene layer's own scoring says where the difficulty is. `change_reality` has been the
weakest dimension for every system tested (2.6-3.4), and the event rubric's V1 and V3 ask
the same question harder: every declared change must land on a declared variable and every
involved entity needs entry state, change and exit state. So the composer is given the
scenes' state changes as its raw material rather than their prose, and the schema requires
the triple rather than requesting it.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

sys.path.insert(0, "/home/deployer/laion/project-alexandria/screenplay/src")
from screenplay_ku.client import EndpointPool, run_parallel  # noqa: E402
from screenplay_ku.kuschema import grammar_safe  # noqa: E402

SYSTEM = (
    "You build the event layer of a story graph from finished scene analyses. An event is a "
    "run of consecutive scenes that function as one unit of story. You work only from what "
    "the scenes record; you never invent material they do not contain. You return only valid "
    "JSON."
)

# `safety` added after the first run: judges found duplicate `knowledge` registers inside
# one entity used to smuggle a second axis, and the axis being smuggled was almost always
# exposure to danger. Giving it its own name removes the collision instead of policing it.
REGISTERS = ["physical", "positional", "knowledge", "relational", "emotional", "status", "safety"]


# ----------------------------------------------------------------- 1. segment

_SEGMENT = """\
Below are consecutive scenes from one screenplay, each with what it contains.

Group them into EVENTS. An event is a run of adjacent scenes that belong together as one unit
of story — a confrontation and its immediate aftermath, a journey and its arrival, a plan and
its execution. Cutting between two locations during one continuous action is **one** event,
not two.

Judge boundaries by change, not by location. A new event starts where the story's situation
has changed enough that what follows is answering a different question than what came before.

Rules:
  - Every scene belongs to exactly one event. No gaps, no overlaps.
  - Events are runs of *consecutive* scenes; use the ids exactly as listed.
  - Typical events run 2-8 scenes. A single-scene event is legitimate when the scene is a
    pivot; a fifteen-scene event usually means a boundary was missed.
  - `why_here` must name what changed at the boundary, not restate the scene.

SCENES:
{scenes}
"""


def segment_schema(scene_ids: Sequence[str]) -> Dict[str, Any]:
    ref = {"type": "string", "enum": list(scene_ids)}
    return {
        "type": "object",
        "properties": {"events": {"type": "array", "minItems": 1, "items": {
            "type": "object",
            "properties": {
                "first_scene": ref,
                "last_scene": ref,
                "working_title": {"type": "string", "minLength": 8},
                "why_here": {"type": "string", "minLength": 20},
            },
            "required": ["first_scene", "last_scene", "working_title", "why_here"],
            "additionalProperties": False,
        }}},
        "required": ["events"],
        "additionalProperties": False,
    }


# ----------------------------------------------------------------- 2. compose

_COMPOSE = """\
Write the event node for the scenes below.

You are not summarising the scenes. You are recording what the *event* does to the story:
what state everything involved enters in, what changes, what state it leaves in.

## The state triple — the part most often done badly

For **every** entity involved, record `entry`, `change` and `exit` across the registers that
apply: {registers}.

Four rules make this useful rather than decorative:

  - **Set `moved` honestly.** `true` if the register changed, `false` if it did not. When
    `false`, fill `unchanged_because` with the reason and make `exit` **identical to
    `entry`** — asserting a new exit state on a register you just said did not move is a
    contradiction, and it is the single most common defect in this layer.
  - **`exit` must follow from `entry` plus `change`.** A reader should be able to check the
    arithmetic. If they cannot, one of the three is wrong.
  - **Never write "not stated" as an entry.** You are given the previous event's exit states
    below. An entity's entry state IS its previous exit state unless something between them
    changed it. Chaining these is the whole point of the layer; a placeholder breaks the
    chain for every event that follows.
  - **The thing the event turns on needs a state triple.** If the event pivots on a wall
    giving way or a phone being cut, that wall or phone is an entity with an entry, a change
    and an exit — not a location string. Name it in `turns_on_entity` and give it a triple.

## What counts as a change

Not the action restated. A change lands on a named variable and later scenes depend on which
side of it we are on.

  not a change   location: hotel -> rooftop        (that is the action)
  not a change   entry: "not stated"               (an unstated entry is not an entry)
  a change       trinity.status: hunted -> extracted, and the pursuit now has a target it lost

## Externalisation

Everything you record must be **photographable or audible**. Report speech as what was
communicated — asserted, refused, revealed — never as quoted lines, and never as narrated
interior.

The `knowledge`, `emotional` and `safety` registers describe states, so record them by their
**evidence**: what the character does or says that shows the state, not the state asserted
from nowhere. "Learns the line is traced — she stops working and looks up" is external.
"Feels dread" is not.

`reading` is the one interior field, and it is for **this character's mind**: what they feel
versus what they show, what they believe about someone else, what they are concealing. It is
not for commentary about the document. "Neo is the unwitting subject of a test" is a note
about the screenplay; "Neo believes he is being offered a choice he has already made" is a
reading of Neo.

## Uncertainty travels

The scenes below may flag things they could not determine. **Carry those forward in
`carried_uncertainty` rather than resolving them.** If a scene says it is unclear whether a
character handed over the phone, the event does not get to assert that she did. Silently
promoting an uncertainty to a fact is worse than either recording it or omitting it, because
it launders a doubt into a claim that everything downstream will inherit.

## Entities

**Anything whose state changes is an entity**, not only people. A wall that gives way, a
phone line that is cut, a ship that loses power — if the scenes record a change to it, and
especially if the event turns on it, it gets a state triple. Putting it in `locations`
instead leaves the pivot of your event with no state at all.

One key per entity, spelled the same way throughout. Do not use a collective label like "the
others" for two different groups in one node — if the escaping crew and the police who seize
someone are both present, they are two entities with two names. `participants` must list
exactly the entities that have state triples: no more, no fewer.

## Outward effect

`affects_outside` names what this event changes for things not in it: a plot it advances, a
character elsewhere whose position it worsens, a resource it spends. If the event genuinely
changes nothing outside itself, say so — that is a real property of a transitional event.

EVENT: {title}
{previous}
SCENES ({count}):
{scenes}
"""


def compose_schema(entity_ids: Sequence[str], scene_ids: Sequence[str]) -> Dict[str, Any]:
    ent = ({"type": "string", "enum": list(entity_ids)} if entity_ids
           else {"type": "string", "minLength": 1})
    return {
        "type": "object",
        "properties": {
            "title": {"type": "string", "minLength": 8},
            "summary": {"type": "string", "minLength": 40},
            "action": {"type": "string", "minLength": 60},
            "participants": {"type": "array", "items": ent, "minItems": 1},
            "locations": {"type": "array", "items": {"type": "string"}},
            "state_triples": {"type": "array", "minItems": 1, "items": {
                "type": "object",
                "properties": {
                    "entity": ent,
                    # The full set, every time. The first run let registers go missing
                    # rather than be marked unchanged, which is indistinguishable from an
                    # omission — the exact failure `unchanged_because` exists to prevent.
                    "registers": {"type": "array", "minItems": len(REGISTERS),
                                  "maxItems": len(REGISTERS), "items": {
                        "type": "object",
                        "properties": {
                            "register": {"type": "string", "enum": REGISTERS},
                            # `moved` makes the changed/unchanged distinction machine-readable.
                            # The first run expressed it four different ways across four nodes
                            # (null, empty string, "not applicable —", reason stuffed into
                            # `change`), so no validator could tell the two apart. A boolean
                            # can only be read one way.
                            "moved": {"type": "boolean"},
                            "entry": {"type": "string", "minLength": 3},
                            "change": {"type": "string", "minLength": 3},
                            "exit": {"type": "string", "minLength": 3},
                            "unchanged_because": {"type": ["string", "null"]},
                            "evidence_scene": {"type": "string", "enum": list(scene_ids)},
                        },
                        "required": ["register", "moved", "entry", "change", "exit",
                                     "unchanged_because", "evidence_scene"],
                        "additionalProperties": False,
                    }},
                    "reading": {"type": ["string", "null"]},
                },
                "required": ["entity", "registers", "reading"],
                "additionalProperties": False,
            }},
            # Typed rather than free-form. As a bare list it delivered only whatever the
            # model happened to think of — one item for some events, none of the three
            # useful kinds for others. Three named slots ask three different questions.
            "affects_outside": {
                "type": "object",
                "properties": {
                    "enables": {"type": "string", "minLength": 15},
                    "blocks_or_costs": {"type": "string", "minLength": 15},
                    "off_screen_reactor": {"type": "string", "minLength": 15},
                },
                "required": ["enables", "blocks_or_costs", "off_screen_reactor"],
                "additionalProperties": False,
            },
            "turns_on": {"type": "string", "minLength": 20},
            # The thing an event turns on must itself have a recorded state. In the first
            # run ev-030 turned on a bulging wall that had been demoted to a `locations`
            # string, so the pivot of the event carried no state at all.
            "turns_on_entity": {"type": "string", "minLength": 2},
            "carried_uncertainty": {"type": "array", "items": {
                "type": "object",
                "properties": {
                    "what": {"type": "string", "minLength": 10},
                    "from_scene": {"type": "string", "enum": list(scene_ids)},
                },
                "required": ["what", "from_scene"],
                "additionalProperties": False,
            }},
        },
        "required": ["title", "summary", "action", "participants", "locations",
                     "state_triples", "affects_outside", "turns_on", "turns_on_entity",
                     "carried_uncertainty"],
        "additionalProperties": False,
    }


# --------------------------------------------------------------- 2b. reconcile

_RECONCILE = """\
The state triples below are final: they have been validated, chained to the previous event,
and de-duplicated. The node's prose was written *alongside* them and now disagrees with them.

Rewrite `summary`, `action` and `turns_on` so they say exactly what the triples say — no more,
no less. Where the prose claimed something the triples do not support, drop it. Where a triple
records something load-bearing the prose omits, add it.

One node in the first run summarised a character as fighting "to a standstill" while its own
physical exit recorded him "beaten, staggered, and buried". The triples are the record; the
prose is a reading of it, and a reading that contradicts its own record is worse than no
reading at all.

Keep everything external: reported speech, no quoted lines, no narrated interior.

TITLE: {title}
STATE TRIPLES:
{triples}

CURRENT PROSE (may be wrong):
  summary: {summary}
  action: {action}
  turns_on: {turns_on}
"""


def reconcile_schema() -> Dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "summary": {"type": "string", "minLength": 40},
            "action": {"type": "string", "minLength": 60},
            "turns_on": {"type": "string", "minLength": 20},
        },
        "required": ["summary", "action", "turns_on"],
        "additionalProperties": False,
    }


def reconcile_all(pool: EndpointPool, events: Sequence[Dict], *, workers: int = 2,
                  progress=None) -> Dict[str, Any]:
    """Rewrite the prose from the finished triples.

    Composition writes prose and triples in one call, so the two can drift apart, and the
    deterministic repairs above then change the triples underneath prose that was already
    written. This closes that gap: the triples are the record and the prose is derived from
    them, in that order.
    """
    def work(event):
        compact = [{"entity": t["entity"], "reading": t.get("reading"),
                    "registers": [{"register": r["register"], "moved": r.get("moved"),
                                   "entry": r["entry"], "change": r["change"], "exit": r["exit"]}
                                  for r in t.get("registers") or [] if r.get("moved")]}
                   for t in event.get("state_triples") or []]
        r = pool.call(SYSTEM, _RECONCILE.format(
            title=event.get("title"), triples=json.dumps(compact, ensure_ascii=False, indent=1),
            summary=event.get("summary"), action=event.get("action"),
            turns_on=event.get("turns_on")),
            schema=grammar_safe(reconcile_schema()), max_tokens=3072)
        return event["event_id"], _parse(r.text)

    out = run_parallel(list(events), work, max_workers=workers, on_done=progress)
    by = {e["event_id"]: e for e in events}
    applied = 0
    for item in out:
        if isinstance(item, Exception):
            continue
        eid, payload = item
        node = by.get(eid)
        if not node:
            continue
        for key in ("summary", "action", "turns_on"):
            if payload.get(key):
                node.setdefault("prose_before_reconcile", {})[key] = node.get(key)
                node[key] = payload[key]
        applied += 1
    return {"reconciled": applied, "of": len(events)}


# ------------------------------------------------------------------ 3. verify

_VERIFY = """\
Two adjacent events from one story. You do NOT have the screenplay — judge them as a reader
with only these nodes would, which is the position everything downstream is in.

Report only defects visible in the nodes themselves:

  `state_breaks`  — an entity leaving the earlier event in one state and entering the later
                    one in a different state, with nothing accounting for the difference.
  `contradictions` — the two nodes asserting incompatible things.
  `missing_links` — an outward effect claimed by the earlier event that the later event
                    plainly realises, and neither says so.

Empty arrays are the correct answer for a clean join. Do not invent work.

EARLIER: {a}

LATER: {b}
"""


def verify_schema() -> Dict[str, Any]:
    item = lambda extra: {  # noqa: E731
        "type": "object",
        "properties": dict({"detail": {"type": "string", "minLength": 20}}, **extra),
        "required": ["detail"] + list(extra),
        "additionalProperties": False,
    }
    return {
        "type": "object",
        "properties": {
            "state_breaks": {"type": "array", "maxItems": 10,
                             "items": item({"entity": {"type": "string"},
                                            "register": {"type": "string"}})},
            "contradictions": {"type": "array", "maxItems": 10, "items": item({})},
            "missing_links": {"type": "array", "maxItems": 10, "items": item({})},
        },
        "required": ["state_breaks", "contradictions", "missing_links"],
        "additionalProperties": False,
    }


# --------------------------------------------------------------------- driver


def _parse(text: str) -> Dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.S)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        a, b = text.find("{"), text.rfind("}")
        if a >= 0 and b > a:
            return json.loads(text[a:b + 1])
        raise


def load_scenes(directory: Path) -> List[Dict[str, Any]]:
    out = []
    for path in sorted(directory.glob("sc-*.json")):
        try:
            node = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        node.setdefault("scene_id", path.stem)
        out.append(node)
    out.sort(key=lambda n: n["scene_id"])
    return out


def brief(node: Dict[str, Any], full: bool = False) -> Dict[str, Any]:
    out = {
        "scene_id": node.get("scene_id"),
        "location": node.get("location"),
        "present": node.get("present"),
        "summary": node.get("summary"),
        "what_changes": node.get("what_changes"),
        # Passed through, not dropped. The first run's `brief()` filtered these out before
        # the composer ever saw them, and the composer then asserted the flagged readings as
        # fact — a doubt laundered into a claim purely by my projection.
        "uncertain": node.get("uncertain"),
        "objects_that_matter": node.get("objects_that_matter"),
    }
    if full:
        out["minds"] = node.get("minds")
        out["dramatic_function"] = node.get("dramatic_function")
    return out


def segment_all(pool: EndpointPool, scenes: Sequence[Dict], *, window: int = 24,
                overlap: int = 4, workers: int = 4) -> List[Dict[str, Any]]:
    """Propose boundaries in overlapping windows, then stitch deterministically.

    Windows overlap so a boundary near an edge is seen by two agents; the stitch keeps the
    first proposal and drops any that would overlap it, so the result tiles by construction
    rather than by the model being asked nicely to tile.
    """
    chunks = []
    step = window - overlap
    for start in range(0, len(scenes), step):
        part = scenes[start:start + window]
        if len(part) >= 2:
            chunks.append(part)
        if start + window >= len(scenes):
            break

    def work(part):
        ids = [s["scene_id"] for s in part]
        prompt = _SEGMENT.format(scenes=json.dumps([brief(s) for s in part],
                                                   ensure_ascii=False, indent=1))
        r = pool.call(SYSTEM, prompt, schema=grammar_safe(segment_schema(ids)), max_tokens=4096)
        return _parse(r.text).get("events") or []

    results = run_parallel(chunks, work, max_workers=workers)
    index = {s["scene_id"]: i for i, s in enumerate(scenes)}
    proposed = []
    for r in results:
        if isinstance(r, Exception):
            continue
        for e in r:
            a, b = index.get(e.get("first_scene")), index.get(e.get("last_scene"))
            if a is None or b is None or b < a:
                continue
            proposed.append({"a": a, "b": b, "title": e["working_title"], "why": e["why_here"]})
    proposed.sort(key=lambda x: (x["a"], -x["b"]))

    events, cursor = [], 0
    for p in proposed:
        if p["a"] < cursor:
            continue
        if p["a"] > cursor:  # gap: absorb the skipped scenes into this event
            p = dict(p, a=cursor)
        events.append(p)
        cursor = p["b"] + 1
    if cursor < len(scenes):  # tail
        events.append({"a": cursor, "b": len(scenes) - 1,
                       "title": "closing run", "why": "tail after the last proposed boundary"})
    return [{"event_id": "ev-{:03d}".format(i + 1),
             "scene_ids": [s["scene_id"] for s in scenes[e["a"]:e["b"] + 1]],
             "working_title": e["title"], "why_here": e["why"]}
            for i, e in enumerate(events)]


def compose_all(pool: EndpointPool, events: Sequence[Dict], by_id: Dict[str, Dict],
                *, workers: int = 2, progress=None,
                previous: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    previous = previous or {}
    def work(ev):
        nodes = [by_id[s] for s in ev["scene_ids"] if s in by_id]
        ents = sorted({p for n in nodes for p in (n.get("present") or [])})
        prev = previous.get(ev["event_id"])
        prev_block = ""
        if prev:
            prev_block = ("PREVIOUS EVENT'S EXIT STATES — an entity's entry state is its exit\n"
                          "state here unless something changed it:\n"
                          + json.dumps(prev, ensure_ascii=False, indent=1) + "\n")
        prompt = _COMPOSE.format(
            registers=", ".join(REGISTERS), title=ev["working_title"], count=len(nodes),
            previous=prev_block,
            scenes=json.dumps([brief(n, full=True) for n in nodes], ensure_ascii=False, indent=1))
        r = pool.call(SYSTEM, prompt,
                      schema=grammar_safe(compose_schema(ents, ev["scene_ids"])),
                      max_tokens=12288)
        node = _parse(r.text)
        node["event_id"] = ev["event_id"]
        node["scene_ids"] = ev["scene_ids"]
        node["boundary_reason"] = ev["why_here"]
        return node

    out = run_parallel(list(events), work, max_workers=workers, on_done=progress)
    return [n for n in out if not isinstance(n, Exception)]


def verify_all(pool: EndpointPool, events: Sequence[Dict], *, workers: int = 2,
               progress=None) -> List[Dict[str, Any]]:
    def small(e):
        return {"event_id": e["event_id"], "title": e.get("title"),
                "summary": e.get("summary"),
                # `change` and `unchanged_because` are included deliberately. The first
                # version projected only entry/exit, so the verifier could not see the
                # unchanged/exit contradictions that turned out to be the layer's most
                # common defect — a check blind to the field it should police.
                "state_triples": [{"entity": t["entity"],
                                   "registers": [{"register": r["register"],
                                                  "moved": r.get("moved"),
                                                  "entry": r["entry"], "change": r["change"],
                                                  "unchanged_because": r.get("unchanged_because"),
                                                  "exit": r["exit"]} for r in t["registers"]]}
                                  for t in e.get("state_triples") or []],
                "affects_outside": e.get("affects_outside")}

    pairs = list(zip(events, events[1:]))

    def work(pair):
        a, b = pair
        r = pool.call(SYSTEM, _VERIFY.format(a=json.dumps(small(a), ensure_ascii=False, indent=1),
                                             b=json.dumps(small(b), ensure_ascii=False, indent=1)),
                      schema=grammar_safe(verify_schema()), max_tokens=4096)
        p = _parse(r.text)
        p["between"] = [a["event_id"], b["event_id"]]
        return p

    out = run_parallel(pairs, work, max_workers=workers, on_done=progress)
    return [x for x in out if not isinstance(x, Exception)]


_PLACEHOLDER = re.compile(
    r"^\s*(not stated|unstated|unknown|n/?a|not specified|not recorded|none|"
    r"unchanged|not applicable|no change)\b", re.I)

# An "unchanged" that immediately concedes an exception is not an unchanged. Judges found
# this in three of four events: the reason field denies the change and then grants it.
_CONCESSION = re.compile(r"\b(beyond|except|other than|aside from|apart from|save for)\b", re.I)


def lint(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Count the defects that are decidable without a model, and name where they are.

    Every item here was found by a judge reading nodes by hand. None of them needs judgement
    to detect, so none of them should ever again cost a judge's attention: a check that a
    machine can run is a check a human should not be spending a rubric pass on.
    """
    report = {"placeholder_entries": 0, "conceding_unchanged": 0, "unmoved_with_exit": 0,
              "quotes_outside_reading": 0, "participants_mismatch": 0,
              "missing_registers": 0, "examples": []}

    def note(kind, event, detail):
        if len(report["examples"]) < 20:
            report["examples"].append({"kind": kind, "event": event, "detail": detail[:110]})

    for event in events:
        declared = {t.get("entity") for t in event.get("state_triples") or []}
        if declared != set(event.get("participants") or []):
            report["participants_mismatch"] += 1
        for triple in event.get("state_triples") or []:
            seen = {r.get("register") for r in triple.get("registers") or []}
            missing = set(REGISTERS) - seen
            if missing:
                report["missing_registers"] += len(missing)
            for reg in triple.get("registers") or []:
                if _PLACEHOLDER.match(reg.get("entry") or ""):
                    report["placeholder_entries"] += 1
                    note("placeholder_entry", event.get("event_id"),
                         "{}.{}: {}".format(triple.get("entity"), reg.get("register"),
                                            reg.get("entry")))
                because = reg.get("unchanged_because") or ""
                if because and _CONCESSION.search(because):
                    report["conceding_unchanged"] += 1
                    note("conceding_unchanged", event.get("event_id"), because)
                if reg.get("moved") is False and (reg.get("exit") or "").strip() != (reg.get("entry") or "").strip():
                    report["unmoved_with_exit"] += 1
            for field in ("registers",):
                for reg in triple.get(field) or []:
                    for key in ("entry", "change", "exit"):
                        if '"' in (reg.get(key) or "") or "\u201c" in (reg.get(key) or ""):
                            report["quotes_outside_reading"] += 1
                            note("quote_outside_reading", event.get("event_id"),
                                 "{}.{}".format(triple.get("entity"), reg.get("register")))
    return report


def merge_duplicate_keys(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Fold duplicate entity keys and duplicate registers inside one entity.

    The first run produced two `state_triples` entries both keyed `the others` inside one
    event, with disjoint referents, and entities carrying two `knowledge` registers that
    contradicted each other. Both are structurally impossible to read: a consumer looking up
    an entity or a register gets whichever copy it happens to hit first.

    Merging rather than dropping, because either copy may carry the better content. A
    conflict is recorded rather than silently resolved — a duplicate key with disjoint
    referents is a real defect and the artifact should say so instead of hiding it.
    """
    report = {"entities_merged": 0, "registers_merged": 0, "conflicts": []}
    for event in events:
        by_entity: Dict[str, Dict[str, Any]] = {}
        for triple in event.get("state_triples") or []:
            name = (triple.get("entity") or "").strip()
            if name not in by_entity:
                by_entity[name] = triple
                continue
            report["entities_merged"] += 1
            report["conflicts"].append({"event": event.get("event_id"), "entity": name,
                                        "kind": "duplicate entity key"})
            target = by_entity[name]
            seen = {r.get("register") for r in target.get("registers") or []}
            for reg in triple.get("registers") or []:
                if reg.get("register") not in seen:
                    target.setdefault("registers", []).append(reg)
                    seen.add(reg.get("register"))
            if triple.get("reading") and not target.get("reading"):
                target["reading"] = triple["reading"]

        for triple in by_entity.values():
            kept: Dict[str, Any] = {}
            for reg in triple.get("registers") or []:
                key = reg.get("register")
                if key in kept:
                    report["registers_merged"] += 1
                    report["conflicts"].append({"event": event.get("event_id"),
                                                "entity": triple.get("entity"),
                                                "kind": "duplicate register: {}".format(key)})
                    # Keep the one that actually moved; an unmoved duplicate carries less.
                    if reg.get("moved") and not kept[key].get("moved"):
                        kept[key] = reg
                else:
                    kept[key] = reg
            triple["registers"] = list(kept.values())
        event["state_triples"] = list(by_entity.values())
    return report


def chain_and_validate(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Repair the three defects that are decidable without a model.

    Composition is parallel, so no event can see its predecessor's exits while it is being
    written. Rather than serialise the whole layer to fix that — 55 events at two minutes
    each — the chain is closed afterwards, deterministically. All three repairs are
    mechanical, and each is recorded so the artifact does not silently look better than the
    generation was.

    1. **Placeholder entries.** `entry: "Not stated."` where the previous event recorded an
       exit for the same entity and register. The chain exit(N) = entry(N+1) is the property
       the layer exists to provide, and a placeholder breaks it for everything downstream.
    2. **The unchanged/exit contradiction.** A register marked `moved: false` that still
       asserts an exit different from its entry says two incompatible things at once. The
       entry is the one supported by the previous state, so the exit yields.
    3. **`participants` out of step with `state_triples`.** They disagreed in every node of
       the first run. The triples are the substance, so they define the list.
    """
    report = {"entries_chained": 0, "contradictions_fixed": 0, "participants_synced": 0,
              "placeholders_left": 0}
    last_exit: Dict[tuple, str] = {}

    for event in events:
        for triple in event.get("state_triples") or []:
            entity = triple.get("entity")
            for reg in triple.get("registers") or []:
                key = (entity, reg.get("register"))

                if _PLACEHOLDER.match(reg.get("entry") or "") and key in last_exit:
                    reg["entry"] = last_exit[key]
                    reg["entry_source"] = "chained_from_previous_event"
                    report["entries_chained"] += 1
                elif _PLACEHOLDER.match(reg.get("entry") or ""):
                    report["placeholders_left"] += 1

                if reg.get("moved") is False and (reg.get("exit") or "").strip() != (reg.get("entry") or "").strip():
                    reg["exit_asserted"] = reg["exit"]
                    reg["exit"] = reg["entry"]
                    reg["exit_source"] = "reset: register marked unmoved"
                    report["contradictions_fixed"] += 1

                if reg.get("exit"):
                    last_exit[key] = reg["exit"]

        declared = sorted({t.get("entity") for t in event.get("state_triples") or []
                           if t.get("entity")})
        if declared != sorted(event.get("participants") or []):
            event["participants"] = declared
            report["participants_synced"] += 1
    return report


def canonicalise_entities(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Fold case variants of the same entity together.

    The composer writes `Neo` in one event and `NEO` in the next, because each event is
    written by its own agent and screenplay speaker cues are upper-case. The verifier then
    reports the two as separate entities with unexplained state, which is a false finding
    produced by the pipeline rather than a defect in the story.

    Done deterministically rather than by a model: this is a spelling question with a
    correct answer, and an LLM call would add cost, latency and the possibility of merging
    two entities that merely look alike. The most frequent capitalisation wins, so the form
    the model chose most often is the one that survives.
    """
    from collections import Counter
    counts: Counter = Counter()
    for event in events:
        for triple in event.get("state_triples") or []:
            counts[triple["entity"]] += 1
        for name in event.get("participants") or []:
            counts[name] += 1

    groups: Dict[str, List[str]] = {}
    for name in counts:
        groups.setdefault(name.strip().casefold(), []).append(name)
    mapping = {}
    for variants in groups.values():
        if len(variants) < 2:
            continue
        winner = max(variants, key=lambda v: (counts[v], v[:1].isupper()))
        for v in variants:
            if v != winner:
                mapping[v] = winner

    applied = 0
    for event in events:
        event["participants"] = sorted({mapping.get(p, p) for p in event.get("participants") or []})
        for triple in event.get("state_triples") or []:
            if triple["entity"] in mapping:
                triple["entity"] = mapping[triple["entity"]]
                applied += 1
    return {"variants_folded": len(mapping), "renames_applied": applied,
            "entities_before": len(counts), "entities_after": len(groups),
            "mapping": mapping}


def main() -> int:
    ap = argparse.ArgumentParser(description="Build the event layer from scene nodes")
    ap.add_argument("--scenes-dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--ports", default="8110,8111")
    ap.add_argument("--model", default="ornith-1.5-397b")
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--window", type=int, default=24)
    ap.add_argument("--skip-verify", action="store_true")
    a = ap.parse_args()

    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    started = time.time()
    scenes = load_scenes(Path(a.scenes_dir))
    if not scenes:
        print("no scene nodes in {}".format(a.scenes_dir)); return 2
    by_id = {s["scene_id"]: s for s in scenes}
    print("scenes: {}".format(len(scenes)), flush=True)

    pool = EndpointPool([int(p) for p in a.ports.split(",")], a.model,
                        temperature=0.5, max_tokens=12288, timeout=1800)
    bad = [p for p, ok in pool.health() if not ok]
    if bad:
        print("unhealthy endpoints: {}".format(bad)); return 2

    prog = lambda d, t, r: print("    [{}/{}]{}".format(  # noqa: E731
        d, t, " !" if isinstance(r, Exception) else ""), flush=True) if d % 3 == 0 or d == t else None

    print("\nstage 1 — segmenting", flush=True)
    events = segment_all(pool, scenes, window=a.window, workers=a.workers)
    sizes = [len(e["scene_ids"]) for e in events]
    covered = sum(sizes)
    print("  {} events | scenes/event min {} max {} mean {:.1f} | coverage {}/{}".format(
        len(events), min(sizes), max(sizes), covered / len(events), covered, len(scenes)),
        flush=True)
    (out / "segmentation.json").write_text(json.dumps({"events": events}, indent=1),
                                           encoding="utf-8")

    print("\nstage 2 — composing {} events".format(len(events)), flush=True)
    nodes = compose_all(pool, events, by_id, workers=a.workers, progress=prog)
    print("  {} composed ({} failed)".format(len(nodes), len(events) - len(nodes)), flush=True)

    canon = canonicalise_entities(nodes)
    merged = merge_duplicate_keys(nodes)
    if merged["entities_merged"] or merged["registers_merged"]:
        print("duplicate keys: {} entities merged, {} registers merged".format(
            merged["entities_merged"], merged["registers_merged"]), flush=True)
    chain = chain_and_validate(nodes)
    lint_report = lint(nodes)
    print("lint: {} placeholder entries, {} conceding-unchanged, {} unmoved-with-exit, "
          "{} quotes outside reading, {} missing registers".format(
              lint_report["placeholder_entries"], lint_report["conceding_unchanged"],
              lint_report["unmoved_with_exit"], lint_report["quotes_outside_reading"],
              lint_report["missing_registers"]), flush=True)
    print("chain repair: {} entries chained, {} unmoved-exit contradictions fixed, "
          "{} participant lists synced, {} placeholders left".format(
              chain["entries_chained"], chain["contradictions_fixed"],
              chain["participants_synced"], chain["placeholders_left"]), flush=True)
    print("\nentity canonicalisation: {} variants folded, {} renames, {} -> {} entities".format(
        canon["variants_folded"], canon["renames_applied"],
        canon["entities_before"], canon["entities_after"]), flush=True)

    print("\nstage 2b — reconciling prose to the finished triples", flush=True)
    rec = reconcile_all(pool, nodes, workers=a.workers, progress=prog)
    print("  {}/{} reconciled".format(rec["reconciled"], rec["of"]), flush=True)

    findings = []
    if not a.skip_verify and len(nodes) > 1:
        print("\nstage 3 — verifying {} joins".format(len(nodes) - 1), flush=True)
        findings = verify_all(pool, nodes, workers=a.workers, progress=prog)
        tally = {k: sum(len(f.get(k) or []) for f in findings)
                 for k in ("state_breaks", "contradictions", "missing_links")}
        print("  {}".format(tally), flush=True)

    triples = sum(len(n.get("state_triples") or []) for n in nodes)
    registers = sum(len(t.get("registers") or []) for n in nodes
                    for t in n.get("state_triples") or [])
    (out / "events.json").write_text(json.dumps({"events": nodes}, indent=1), encoding="utf-8")
    (out / "protocol.json").write_text(json.dumps({
        "seconds": round(time.time() - started, 1),
        "scenes": len(scenes), "events": len(nodes),
        "scenes_per_event": {"min": min(sizes), "max": max(sizes),
                             "mean": round(covered / len(events), 2)},
        "coverage": "{}/{}".format(covered, len(scenes)),
        "state_triples": triples, "register_entries": registers,
        "canonicalisation": canon,
        "chain_repair": chain,
        "duplicate_merge": merged,
        "reconcile": rec,
        "lint": lint_report,
        "affects_outside": sum(len(n.get("affects_outside") or []) for n in nodes),
        "verify": findings,
    }, indent=1), encoding="utf-8")

    print("\n{} events, {} state triples, {} register entries in {:.0f}s".format(
        len(nodes), triples, registers, time.time() - started))
    print("wrote {}".format(out / "events.json"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
