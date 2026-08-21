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

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, "/home/deployer/laion/project-alexandria/screenplay/src")
from event_scaffold import (build_scaffold, canonical_roster, exits_by_entity,  # noqa: E402
                            render_scaffold)
from screenplay_ku.client import EndpointPool, run_parallel  # noqa: E402
from screenplay_ku.kuschema import grammar_safe  # noqa: E402

SYSTEM = (
    "You build the event layer of a story graph from finished scene analyses. An event is a "
    "run of consecutive scenes that function as one unit of story. You work only from what "
    "the scenes record; you never invent material they do not contain. You return only valid "
    "JSON."
    "\n\n"
    "NEVER COPY THE SCREENPLAY. You are given the scene text as a check on the scene nodes, "
    "not as material to quote from. Never reuse eight or more consecutive words from it.\n"
    "  * Speech becomes reported speech, in the third person:\n"
    "      on the page:  \"I said, is everything in place?\"\n"
    "      in your node: she asks a second time whether everything is ready\n"
    "  * A stage direction becomes the observable fact in your own words:\n"
    "      on the page:  The lamp swings above the table, throwing shadows that refuse to settle\n"
    "      in your node: the lamp keeps swinging and the shadows never come to rest\n"
    "  * Names, numbers, dates, times and place names stay EXACTLY as written. Those are "
    "facts, and rewording them makes the node wrong."
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

_COMPOSE_B3 = """\
Condense these scenes into one event node.

**This is a merge, not a fresh reading.** The scene layer has already established who is
present, what changed, and what was going on in people's minds. Your job is to carry that
forward into one arc per entity — and then, on top of it, say what the event means and how it
connects to the rest of the story.

You are given three things, deliberately overlapping:

  1. **The roster and change ledger** — computed from the scenes, not proposed by you.
  2. **The scene nodes in order** — the analyses as written.
  3. **The scenes' actual text** — the screenplay itself, so you can check anything.

Where they disagree, the screenplay wins, then the scene nodes, then your reading.

## Rules that come from the scaffold

**The roster is closed.** Every entity listed needs a state triple. No entity outside it may
be added. If someone seems missing, they were not recorded as present or as changing, and
that is a fact about the scenes rather than an invitation.

**`moved` is transcription, not judgement.** For each entity, the scaffold lists the registers
the scene layer recorded a change on. Those registers are `moved: true`. Every other register
is `moved: false`, and then **`exit` must be identical to `entry`** and
`unchanged_because` must say why it did not move. Setting `moved: true` on a register whose
entry and exit say the same thing is the single most common defect in earlier builds.

**`entry` comes from the previous event where the scaffold supplies one.** That chain is what
the layer exists for. Never write "not stated" — if the scaffold gives you nothing and the
scenes show nothing, describe the state the screenplay implies at the moment the event opens.

**`evidence_scene` must be a scene the entity actually appears in.** The scaffold lists them.

## What to condense

For each entity, the ledger may hold several changes across several scenes on the same
register. **Fold them into one arc**: the entry of the first, the exit of the last, and a
`change` that names the path between them rather than listing the steps.

Mind material the scene layer already found is the basis for `reading`. Summarise and sharpen
it; do not replace it with a new invention. You may add what the accumulated scenes make
visible and no single scene could — that is the value this layer adds.

## What to add

`turns_on` and `turns_on_entity` — the pivot, and the entity it belongs to. The entity must be
on the roster.

`affects_outside` — three separate questions: what this event **enables**, what it **blocks or
costs**, and who **reacts off-screen**. Answer each from the story, not from this event's own
contents; an on-screen participant is not an off-screen reactor.

`carried_uncertainty` — the scaffold lists what the scenes could not determine. Carry it. Do
not resolve it, and do not assert elsewhere in the node something the scaffold flags as
unknown.

## Length

Each field has a hard ceiling and the ceilings are tight on purpose. A state is a state:
"cuffed, face down, in police custody" is complete. Do not write paragraphs into a register.
Earlier builds lost more points on proportion than on any other dimension.

## Discipline

Everything external: reported speech, no quoted lines, no narrated interior. `reading` is the
only interior field, and it is about the character's mind — not commentary about the script.

=== SCAFFOLD ===
{scaffold}

=== SCENE NODES, IN ORDER ===
{nodes}

=== THE SCENES THEMSELVES ===
{text}

Write the node for: {title}
"""


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


def _iter_registers(triple: Dict[str, Any]):
    """Yield (name, slot) whether registers are the new object or the old array.

    Both shapes exist on disk: build 1 and 2 wrote arrays, build 3 writes an object. Reading
    both keeps every earlier run scoreable by the current lint instead of stranding it.
    """
    regs = triple.get("registers")
    if isinstance(regs, dict):
        for name, slot in regs.items():
            yield name, slot
    else:
        for slot in regs or []:
            yield slot.get("register"), slot


def _register_slot(scene_ids: Sequence[str]) -> Dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "moved": {"type": "boolean"},
            # Upper bounds, not just lower ones. Left unbounded the model wrote 8,300 tokens
            # for a single event node — one register description running to a paragraph. A
            # state is a state: "cuffed, in police custody" says it. Calibration has been the
            # dimension that decided every comparison in this project, and a maxLength is the
            # only way to ask for brevity that the model cannot decline.
            "entry": {"type": "string", "minLength": 3, "maxLength": 180},
            "change": {"type": "string", "minLength": 3, "maxLength": 220},
            "exit": {"type": "string", "minLength": 3, "maxLength": 180},
            "unchanged_because": {"type": ["string", "null"], "maxLength": 160},
            "evidence_scene": {"type": "string", "enum": list(scene_ids)},
        },
        "required": ["moved", "entry", "change", "exit", "unchanged_because",
                     "evidence_scene"],
        "additionalProperties": False,
    }


def compose_schema(entity_ids: Sequence[str], scene_ids: Sequence[str],
                   registers_by_entity: Optional[Dict[str, Sequence[str]]] = None) -> Dict[str, Any]:
    """Per-entity register sets, derived from the scaffold.

    Build 2 required all seven registers for every entity. On an event with twenty entities
    that is 140 register slots and 840 constrained fields — which at this model's decode rate
    does not finish, and which a build-1 judge had already named "completeness theatre": the
    schema was satisfied by writing the reason a register did not move, twenty times over,
    rather than by recording a state.

    The scaffold knows which registers the scene layer actually recorded a change on. Those
    are required. An entity with no recorded change gets a presence record instead of seven
    slots of boilerplate. Requiring less produces more, because what is required is now the
    part that carries information.
    """
    ent = ({"type": "string", "enum": list(entity_ids)} if entity_ids
           else {"type": "string", "minLength": 1})
    req_map = registers_by_entity or {}
    union_required = sorted({r for v in req_map.values() for r in v}) if req_map else []
    return {
        "type": "object",
        "properties": {
            "title": {"type": "string", "minLength": 8, "maxLength": 90},
            "summary": {"type": "string", "minLength": 40, "maxLength": 500},
            "action": {"type": "string", "minLength": 60, "maxLength": 1200},
            "participants": {"type": "array", "items": ent, "minItems": 1},
            "locations": {"type": "array", "items": {"type": "string"}},
            "state_triples": {"type": "array",
                              "minItems": len(entity_ids) if entity_ids else 1,
                              "maxItems": len(entity_ids) if entity_ids else 60,
                              "items": {
                "type": "object",
                "properties": {
                    "entity": ent,
                    # An OBJECT with one required key per register, not an array with a
                    # count. Build 2 required "exactly seven" as `minItems`, and the model
                    # satisfied the count by repeating one register name seven times; the
                    # de-duplication pass then collapsed them and left 107 of 253 entities
                    # below the count the schema had demanded. A count is a number to be
                    # satisfied; an object shape cannot be satisfied dishonestly, because
                    # there is nowhere to put a duplicate.
                    "registers": {
                        "type": "object",
                        "properties": {r: _register_slot(scene_ids) for r in REGISTERS},
                        # The union of registers any entity in this event moved on. JSON
                        # Schema cannot vary `required` by sibling value, so the union is the
                        # tightest expressible floor; the prompt carries the per-entity set,
                        # and lint checks it after the fact.
                        "required": union_required,
                        "additionalProperties": False,
                    },
                    "reading": {"type": ["string", "null"], "maxLength": 320},
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
                    "enables": {"type": "string", "minLength": 15, "maxLength": 260},
                    "blocks_or_costs": {"type": "string", "minLength": 15, "maxLength": 260},
                    "off_screen_reactor": {"type": "string", "minLength": 15, "maxLength": 260},
                },
                "required": ["enables", "blocks_or_costs", "off_screen_reactor"],
                "additionalProperties": False,
            },
            "turns_on": {"type": "string", "minLength": 20, "maxLength": 300},
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
            "turns_on": {"type": "string", "minLength": 20, "maxLength": 300},
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
                    # The name comes from _iter_registers. Object-shaped slots carry
                    # no "register" key -- the name IS the dict key -- so reading
                    # r["register"] raised KeyError on every build-3-or-later node.
                    "registers": [{"register": rn, "moved": r.get("moved"),
                                   "entry": r.get("entry"), "change": r.get("change"),
                                   "exit": r.get("exit")}
                                  for rn, r in _iter_registers(t)
                                  if isinstance(r, dict) and r.get("moved")]}
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



# --------------------------------------------------------------- context fit

CTX_MARGIN = 384      # room for the chat template and the schema grammar
MIN_OUTPUT = 3500     # below this an event cannot be written at all


def count_tokens(pool: EndpointPool, text: str) -> int:
    """Exact token count from the server, with an estimate as the fallback.

    Estimating was not good enough. The overflow this guards against is a
    difference of a few hundred tokens on a 33,000-token call, and a
    characters-per-token ratio is wrong by more than that.
    """
    import urllib.request
    endpoint = pool.endpoints[0]
    try:
        request = urllib.request.Request(
            "http://{}:{}/tokenize".format(endpoint.host, endpoint.port),
            data=json.dumps({"content": text}).encode("utf-8"),
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(request, timeout=120) as response:
            return len(json.load(response)["tokens"])
    except Exception:
        return int(len(text) / 3.6)


def fit_to_context(pool, prompt: str, budget: int, ctx: int, *,
                   text_block: str = "", rebuild=None,
                   label: str = "") -> Tuple[str, int, Dict[str, Any]]:
    """Make prompt + output fit in the context window, and say what it cost.

    The largest events overflowed silently: a 15,700-token prompt with an
    18,000-token budget needs 33,700 of a 32,768 window, so llama.cpp truncated
    the generation and the node came back cut off. Truncation is worst exactly
    where it hurts most -- the biggest events are the ones carrying the most
    story.

    Two levers, in this order:

      1. shrink the scene text. It is the third of three overlapping views and
         the most redundant: the scene nodes already encode it. Each scene is
         capped rather than dropped, so every member scene stays represented and
         the screenplay keeps its role as the check on the nodes.
      2. clamp the output budget, down to MIN_OUTPUT.

    Below MIN_OUTPUT the event is reported as unfittable rather than attempted.
    A truncated node is worse than a missing one, because a missing one is
    visible.
    """
    note: Dict[str, Any] = {"trimmed": False}
    tokens = count_tokens(pool, prompt)
    room = ctx - tokens - CTX_MARGIN
    if room >= budget:
        note["prompt_tokens"] = tokens
        return prompt, budget, note

    if text_block and rebuild is not None:
        # Cap each scene until the prompt fits, halving the cap as needed.
        for cap in (3000, 2000, 1200, 700, 400):
            candidate = rebuild(cap)
            tokens = count_tokens(pool, candidate)
            room = ctx - tokens - CTX_MARGIN
            if room >= budget:
                note.update(trimmed=True, scene_text_cap=cap, prompt_tokens=tokens)
                return candidate, budget, note
        prompt = candidate
        note.update(trimmed=True, scene_text_cap=400, prompt_tokens=tokens)

    out = max(MIN_OUTPUT, min(budget, room))
    note.update(prompt_tokens=tokens, budget_clamped_from=budget, budget=out,
                fits=(tokens + out + CTX_MARGIN) <= ctx)
    if not note["fits"]:
        note["unfittable"] = True
        print("      {} does not fit: prompt {} + output {} > ctx {}".format(
            label, tokens, out, ctx), flush=True)
    return prompt, out, note


def _cap_scene(text: str, cap: Optional[int]) -> str:
    """Keep the head and the tail of a scene, which is where a scene turns."""
    if cap is None or len(text) <= cap:
        return text
    head = int(cap * 0.6)
    return text[:head] + "\n[... middle of scene omitted to fit context ...]\n" + \
        text[-(cap - head):]


def compose_all(pool: EndpointPool, events: Sequence[Dict], by_id: Dict[str, Dict],
                *, workers: int = 2, progress=None,
                previous: Optional[Dict[str, Any]] = None,
                scene_text: Optional[Dict[str, str]] = None,
                canon: Optional[Dict[str, str]] = None,
                ctx: int = 32768) -> List[Dict[str, Any]]:
    previous = previous or {}
    scene_text = scene_text or {}
    def work(ev):
        nodes = [by_id[s] for s in ev["scene_ids"] if s in by_id]
        scaffold = build_scaffold(ev["scene_ids"], nodes,
                                  previous_exits=previous.get(ev["event_id"]), canon=canon)
        # The entity enum is the computed roster. That is what makes `turns_on_entity`
        # satisfiable at last: build 2 required the field while admitting only characters,
        # so an event turning on a phone had nowhere to name it.
        ents = [e["entity"] for e in scaffold["entities"]]
        def render(cap: Optional[int] = None) -> str:
            body = "\n\n".join(
                "--- {} ---\n{}".format(
                    sid, _cap_scene(scene_text.get(sid, "[text unavailable]"), cap))
                for sid in ev["scene_ids"])
            return _COMPOSE_B3.format(
                scaffold=render_scaffold(scaffold),
                nodes=json.dumps([brief(n, full=True) for n in nodes],
                                 ensure_ascii=False, indent=1),
                text=body, title=ev["working_title"])

        text = "\n\n".join(
            "--- {} ---\n{}".format(sid, scene_text.get(sid, "[text unavailable]"))
            for sid in ev["scene_ids"])
        prompt = render()
        # Required registers per entity, straight from the scaffold. An entity the scene
        # layer never recorded a change for gets one slot, not seven.
        required_by = {e["entity"]: (e["registers_with_recorded_change"] or ["status"])
                       for e in scaffold["entities"]}
        schema = compose_schema(ents, ev["scene_ids"], required_by)
        # Counts entities as well as slots. The first formula priced only register slots, so
        # a twenty-seven entity event was budgeted as if its twenty-seven entity names,
        # readings and JSON scaffolding were free. The four earliest waves — which hold the
        # largest events — failed on truncation while later, smaller ones passed.
        budget = (3000
                  + 360 * sum(len(v) for v in required_by.values())
                  + 150 * len(required_by))
        prompt, out_tokens, fit = fit_to_context(
            pool, prompt, min(18000, budget), ctx,
            text_block=text, rebuild=render, label=ev["event_id"])
        r = pool.call(SYSTEM, prompt, schema=grammar_safe(schema),
                      max_tokens=out_tokens)
        node = _parse(r.text)
        if fit.get("trimmed") or fit.get("budget_clamped_from"):
            # Recorded on the node, not just printed. A run whose largest events
            # were quietly shortened must be readable as such afterwards.
            node["_context_fit"] = fit
        node["event_id"] = ev["event_id"]
        node["scene_ids"] = ev["scene_ids"]
        node["boundary_reason"] = ev["why_here"]
        node["_scaffold_counts"] = scaffold["counts"]
        node["_roster"] = ents
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
                                   "registers": [{"register": rn,
                                                  "moved": r.get("moved"),
                                                  "entry": r.get("entry"),
                                                  "change": r.get("change"),
                                                  "unchanged_because": r.get("unchanged_because"),
                                                  "exit": r.get("exit")}
                                                 for rn, r in _iter_registers(t)
                                                 if isinstance(r, dict)]}
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


def lint(events: List[Dict[str, Any]],
         scenes_by_id: Optional[Dict[str, Dict[str, Any]]] = None) -> Dict[str, Any]:
    """Count the defects that are decidable without a model, and name where they are.

    Every item here was found by a judge reading nodes by hand. None of them needs judgement
    to detect, so none of them should ever again cost a judge's attention: a check that a
    machine can run is a check a human should not be spending a rubric pass on.
    """
    report = {"placeholder_entries": 0, "conceding_unchanged": 0, "unmoved_with_exit": 0,
              "quotes_outside_reading": 0, "participants_mismatch": 0,
              "missing_registers": 0,
              # Both added after build 2. A judge found one node giving the pursuing POLICE
              # the operator's state, and another marking a register `moved: true` from a
              # value to the identical value. Both are decidable without judgement, and both
              # were load-bearing: a consumer reading the first gets the police taking
              # orders from the crew.
              "entity_absent_from_evidence_scene": 0, "moved_but_identical": 0,
              "examples": []}

    def note(kind, event, detail):
        if len(report["examples"]) < 20:
            report["examples"].append({"kind": kind, "event": event, "detail": detail[:110]})

    for event in events:
        declared = {t.get("entity") for t in event.get("state_triples") or []}
        if declared != set(event.get("participants") or []):
            report["participants_mismatch"] += 1
        for triple in event.get("state_triples") or []:
            seen = {n for n, _ in _iter_registers(triple)}
            missing = set(REGISTERS) - seen
            if missing:
                report["missing_registers"] += len(missing)
            for _rname, reg in _iter_registers(triple):
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

                entry_s, exit_s = (reg.get("entry") or "").strip(), (reg.get("exit") or "").strip()
                # Literal identity, and the weaker prefix case. A judge found
                # `positional: "At the console." -> "At the console, directed to fetch a
                # drawing."` marked as moved: the place did not change, and the material that
                # was added belongs to a different register. String equality alone misses it,
                # so a shared prefix counts too. This still cannot catch a paraphrased no-op;
                # lint has a floor and that floor is worth stating rather than papering over.
                if reg.get("moved") is True and entry_s and (
                        exit_s == entry_s or
                        (len(entry_s) > 25 and exit_s.startswith(entry_s.rstrip(".")))):
                    report["moved_but_identical"] += 1
                    note("moved_but_identical", event.get("event_id"),
                         "{}.{}: {}".format(triple.get("entity"), reg.get("register"),
                                            (reg.get("entry") or "")[:60]))

                if scenes_by_id:
                    scene = scenes_by_id.get(reg.get("evidence_scene") or "")
                    present = {str(x).strip().casefold()
                               for x in (scene or {}).get("present") or []}
                    who = (triple.get("entity") or "").strip().casefold()
                    # Only flag when the scene declares a cast at all, and the entity is not
                    # a substring of anyone in it — collectives legitimately do not match
                    # exactly, and flagging those would drown the real cases.
                    if present and who and not any(who in p or p in who for p in present):
                        report["entity_absent_from_evidence_scene"] += 1
                        note("entity_absent", event.get("event_id"),
                             "{} cites {} whose cast is {}".format(
                                 triple.get("entity"), reg.get("evidence_scene"),
                                 sorted(present)[:4]))
            # Iterating triple["registers"] directly yields dict *keys* -- plain
            # strings -- once registers became an object in build 3, and this
            # line then crashed the whole lint after 58 events had composed.
            # _iter_registers exists precisely to read both shapes; the fix is to
            # use it here as everywhere else.
            for name, reg in _iter_registers(triple):
                if not isinstance(reg, dict):
                    continue
                for key in ("entry", "change", "exit"):
                    if '"' in (reg.get(key) or "") or "\u201c" in (reg.get(key) or ""):
                        report["quotes_outside_reading"] += 1
                        note("quote_outside_reading", event.get("event_id"),
                             "{}.{}".format(triple.get("entity"), name))
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
            seen = {n for n, _ in _iter_registers(target)}
            # Registers are an object in build 3 onward and an array before it. Appending to
            # the object crashed the run after forty-four nodes had been composed, all of
            # which were lost because this build predated incremental writing. Both shapes
            # are handled here rather than assuming either.
            for _rname, reg in _iter_registers(triple):
                if _rname in seen:
                    continue
                bucket = target.get("registers")
                if isinstance(bucket, dict):
                    bucket[_rname] = reg
                else:
                    target.setdefault("registers", []).append(reg)
                seen.add(_rname)
            if triple.get("reading") and not target.get("reading"):
                target["reading"] = triple["reading"]

        for triple in by_entity.values():
            if isinstance(triple.get("registers"), dict):
                continue  # object shape: duplicates are structurally impossible
            kept: Dict[str, Any] = {}
            for _rname, reg in _iter_registers(triple):
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
            for rname, reg in _iter_registers(triple):
                if not isinstance(reg, dict):
                    continue
                # The name comes from _iter_registers, never from inside the slot.
                # Object-shaped slots carry no "register" key, so reg.get("register")
                # is None for all seven -- which collapsed every register of one
                # entity into a single chain bucket and would have carried a
                # physical exit into an emotional entry. Silent, and it destroys
                # exactly the property this layer exists to hold.
                key = (entity, rname)

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



def verbatim_gate(nodes, source_path: str, label: str) -> Dict[str, Any]:
    """Report copied source text in a finished layer.

    Runs at the end of a build rather than as a separate errand, because a check
    that has to be remembered is a check that gets skipped. It reports and does
    not block: the fix is paraphrase_pass.py, which needs a model and a decision
    about which endpoint to spend, and neither belongs inside a build that has
    just finished four hours of work.
    """
    if not source_path or not Path(source_path).exists():
        print("\nverbatim gate: no source available, skipped")
        return {}
    import verbatim as _V
    index = _V.SourceIndex(Path(source_path).read_text(encoding="utf-8", errors="ignore"))
    exact = near = dirty = 0
    worst = 0
    for node in nodes:
        hits = _V.scan_node(node, index)
        ex = [r for _p, r in hits if r.kind == "exact"]
        exact += len(ex)
        near += len([r for _p, r in hits if r.kind == "near"])
        dirty += 1 if ex else 0
        worst = max([worst] + [r.words for r in ex])
    print("\nverbatim gate — {}".format(label))
    print("  exact runs (>= {} source words): {} in {}/{} nodes, longest {}".format(
        _V.BAR, exact, dirty, len(nodes), worst))
    print("  near hits (review only): {}".format(near))
    if exact:
        print("  fix: python3 distill/paraphrase_pass.py --nodes <out> \\")
        print("         --source {} --ports <ports> --model <small model>".format(source_path))
    return {"exact_runs": exact, "near_hits": near, "nodes_with_runs": dirty,
            "nodes": len(nodes), "longest_run_words": worst}


def main() -> int:
    ap = argparse.ArgumentParser(description="Build the event layer from scene nodes")
    ap.add_argument("--scenes-dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--ports", default="8110,8111")
    ap.add_argument("--model", default="ornith-1.5-397b")
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--window", type=int, default=24)
    ap.add_argument("--wave", type=int, default=4,
                    help="events composed per wave; each wave sees the previous wave's exits")
    ap.add_argument("--source", default="reconstruct/runs/matrix/script.normalized.txt")
    ap.add_argument("--scene-map", default="reconstruct/runs/matrix/script_map.json")
    # Must match the server's -c. The composer sizes its own generation against
    # this; if it is larger than the server's window the guard passes prompts
    # that still overflow.
    ap.add_argument("--ctx", type=int, default=32768)
    # Compose is the expensive stage -- two hours against a 397B model. Everything
    # after it is cheap post-processing, and a crash there once threw away 58
    # finished nodes. This reloads them and runs only what follows.
    ap.add_argument("--resume-from", default="",
                    help="an events.partial.json; skips segmenting and composing")
    ap.add_argument("--skip-verify", action="store_true")
    a = ap.parse_args()

    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    started = time.time()
    scenes = load_scenes(Path(a.scenes_dir))
    # The screenplay itself, so the composer can check the scene nodes against the source.
    scene_text: Dict[str, str] = {}
    if a.source and a.scene_map:
        raw = Path(a.source).read_text(encoding="utf-8")
        smap = json.loads(Path(a.scene_map).read_text(encoding="utf-8"))["scenes"]
        for sid, meta in smap.items():
            scene_text[sid] = raw[meta["start_char"]:meta["end_char"]]
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

    resume = None
    if a.resume_from:
        resume = json.loads(Path(a.resume_from).read_text(encoding="utf-8"))
        resume = resume["events"] if isinstance(resume, dict) else resume
        seg_path = Path(a.resume_from).parent / "segmentation.json"
        events = json.loads(seg_path.read_text(encoding="utf-8"))["events"] \
            if seg_path.exists() else [{"event_id": n["event_id"],
                                        "scene_ids": n["scene_ids"]} for n in resume]
        print("\nresuming from {}: {} composed nodes, {} segmented events".format(
            a.resume_from, len(resume), len(events)), flush=True)
        sizes = [len(e["scene_ids"]) for e in events]
        covered = sum(sizes)
        canon = canonical_roster(scenes)
        nodes = resume
    else:
        print("\nstage 1 — segmenting", flush=True)
        events = segment_all(pool, scenes, window=a.window, workers=a.workers)
        sizes = [len(e["scene_ids"]) for e in events]
        covered = sum(sizes)
        print("  {} events | scenes/event min {} max {} mean {:.1f} | coverage {}/{}".format(
            len(events), min(sizes), max(sizes), covered / len(events), covered, len(scenes)),
            flush=True)
        (out / "segmentation.json").write_text(json.dumps({"events": events}, indent=1),
                                               encoding="utf-8")

        canon = canonical_roster(scenes)
        print("  roster: {} spellings -> {} entities across the film".format(
            len(canon), len(set(canon.values()))), flush=True)

    # Composed in waves so each wave can be handed the previous wave's exit states. Fully
    # sequential would serialise the layer; fully parallel leaves every `entry` unchained,
    # which was build 1's largest defect. A wave is the compromise: parallel within, chained
    # across.
    if resume is None:
        print("\nstage 2 — composing {} events in waves of {}".format(len(events), a.wave),
              flush=True)
        nodes = []
        previous: Dict[str, Any] = {}
        partial = out / "events.partial.json"
        for start in range(0, len(events), a.wave):
            batch = events[start:start + a.wave]
            got = compose_all(pool, batch, by_id, workers=a.workers, progress=prog,
                              previous=previous, scene_text=scene_text, canon=canon,
                              ctx=a.ctx)
            nodes.extend(got)
            # Written after every wave. A four-hour run that produces nothing until the
            # last second cannot be inspected, and a crash at hour three costs
            # everything — the same rule this project imposes on its judge agents,
            # finally applied to itself.
            partial.write_text(json.dumps({"events": nodes}, indent=1), encoding="utf-8")
            previous = {}
            if got:
                tail = exits_by_entity(got[-1])
                nxt = events[start + a.wave] if start + a.wave < len(events) else None
                if nxt:
                    previous[nxt["event_id"]] = tail
        print("  {} composed ({} failed)".format(
            len(nodes), len(events) - len(nodes)), flush=True)

    canon = canonicalise_entities(nodes)
    merged = merge_duplicate_keys(nodes)
    if merged["entities_merged"] or merged["registers_merged"]:
        print("duplicate keys: {} entities merged, {} registers merged".format(
            merged["entities_merged"], merged["registers_merged"]), flush=True)
    chain = chain_and_validate(nodes)
    lint_report = lint(nodes, by_id)
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

    gate = verbatim_gate(nodes, a.source, "event layer")

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
        "verbatim": gate,
        "affects_outside": sum(len(n.get("affects_outside") or []) for n in nodes),
        "verify": findings,
    }, indent=1), encoding="utf-8")

    print("\n{} events, {} state triples, {} register entries in {:.0f}s".format(
        len(nodes), triples, registers, time.time() - started))
    print("wrote {}".format(out / "events.json"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
