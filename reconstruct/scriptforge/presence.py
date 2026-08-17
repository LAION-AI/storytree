"""Presence assertions: is everyone where they are supposed to be, and only there?

Four passes of rubric evaluation kept surfacing the same family of failure, in
different costumes:

    a specimen giving six lines to someone not in the scene
    a specimen deleting a character who is in the scene
    a state change recorded for a character who is not present
    an event placing a character somewhere the brief puts elsewhere
    22 of 22 events at one location because only one location existed
    a protagonist ejected into a physical world she cannot occupy

All six are the same question — *who and what is present, and where* — and all
six are decidable from files on disk. None of them needs a judge.

What this module adds beyond `grounding.py`
-------------------------------------------
`grounding` binds the roster into the schema and checks the specimen against it.
That covers who *speaks*. It does not cover:

  - characters the analysis discusses, reasons about, or moves state for,
    without their being in the scene at all
  - the location, checked as a fact rather than as keyword overlap
  - entities referenced across a whole layer that never appear anywhere
  - a character asserted to be in two places at one story time

The distinction that took a rubric pass to see: **speaking, being present, and
being discussed are three different sets**, and conflating them produced both a
false clean sheet and a mandated error. A character can be present without
speaking, discussed without being present, and — this is the one that bites —
have state moved without being either.

Guidance, not just detection
----------------------------
Detection alone has a poor record here. A prompt clause fixed a local field and
regressed a global one; schema binding fixed what a clause could not. So each
assertion carries the sentence that would have prevented it, and
`briefing_for()` assembles those into a short, level-appropriate note that is
injected as the model descends from general to specific layers. The model is
told what the checker will check, in the terms the checker uses, at the moment
it is about to write the thing being checked.
"""

from __future__ import annotations

import json


def _norm(s) -> str:
    return "".join(c for c in str(s or "").lower() if c.isalnum())


# --------------------------------------------------------------------------
# The three sets, kept apart on purpose
# --------------------------------------------------------------------------

def presence_sets(scene, entities: dict, events: dict | None = None) -> dict:
    """Who speaks, who is present, who may legitimately be discussed.

    speaking   the script's own speaker cues, resolved to ids where possible.
               Ground truth. Nothing else may be given a line.
    present    speaking, plus participants the event layer records for this
               scene. These may act and have state moved.
    referable  present, plus anyone a present character could plausibly think
               about — established entities. These may appear in theory of mind
               and in the analysis, but may not act.
    """
    by_key = {}
    for eid, e in entities.items():
        for label in [e.get("canonical_name", "")] + list(e.get("aliases") or []):
            if _norm(label):
                by_key[_norm(label)] = eid

    speaking, unresolved = [], []
    for cue in getattr(scene, "speakers", []) or []:
        hit = by_key.get(_norm(cue))
        if hit is None:
            hit = next((eid for k, eid in by_key.items()
                        if k and (k in _norm(cue) or _norm(cue) in k) and len(k) > 3), None)
        if hit:
            if hit not in speaking:
                speaking.append(hit)
        else:
            unresolved.append(cue)

    present = list(speaking)
    sid = getattr(scene, "scene_id", None)
    for ev in (events or {}).values():
        if sid and sid in (ev.get("scenes") or []):
            for pid in ev.get("participants") or []:
                if pid in entities and pid not in present:
                    present.append(pid)

    return {"speaking": speaking, "unresolved_cues": unresolved,
            "present": present, "referable": sorted(entities),
            "location": getattr(scene, "location", None),
            "time_of_day": getattr(scene, "time_of_day", None)}


# --------------------------------------------------------------------------
# Assertions. Each returns (violation, the sentence that prevents it).
# --------------------------------------------------------------------------

def assert_presence(tr: dict, sets: dict, entities: dict) -> list[dict]:
    """Every presence claim in a transition, checked against the sets."""
    out: list[dict] = []

    def bad(kind, msg, guidance):
        out.append({"kind": kind, "violation": msg, "guidance": guidance})

    speaking = set(sets["speaking"]) | set(sets["unresolved_cues"])
    present = set(sets["present"]) | set(sets["unresolved_cues"])

    # -- who was given lines --
    lines = (tr.get("specimen") or {}).get("lines") or []
    said = [l.get("speaker") for l in lines if isinstance(l, dict)]
    for s in sorted(set(said) - speaking):
        bad("speaks_but_absent",
            f"{s!r} is given dialogue but does not speak in this scene",
            "Only the speaker cues in the slug line may be given lines. A character "
            "who is present but silent stays silent.")
    for s in sorted(speaking - set(said)):
        bad("present_but_silent",
            f"{s!r} speaks in this scene but is given no lines",
            "Every cued speaker must appear in the exchange. Dropping one removes "
            "the opposition the scene is built on.")

    # -- who had state moved --
    for i, c in enumerate((tr.get("decision") or {}).get("state_changes_implied") or []):
        if not isinstance(c, dict):
            continue
        eid = c.get("entity")
        if eid and eid not in present:
            where = "not in this scene at all" if eid in entities else "not a declared entity"
            bad("state_moved_offstage",
                f"state change {i} moves {eid!r}, who is {where}",
                "A character who is not in the scene cannot change during it. "
                "Off-screen consequences belong to a later event, not this one.")

    # -- who was analysed --
    for p in tr.get("psychology") or []:
        eid = p.get("entity") if isinstance(p, dict) else None
        if eid and eid not in present:
            bad("analysed_but_absent",
                f"a psychology block was written for {eid!r}, who is not in the scene",
                "Analyse the people in the room. Someone absent may be thought "
                "*about* — that belongs in another character's theory of mind.")

    # -- where it happens --
    b = tr.get("binding") or {}
    if b.get("location") and sets.get("location") and b["location"] != sets["location"]:
        bad("wrong_location",
            f"binding says {b['location']!r}, the scene is {sets['location']!r}",
            "The location is a fact you were handed. If your idea needs a "
            "different room, the idea is wrong.")
    if b.get("on_screen"):
        # the grammar does not enforce maxItems, so a repeated roster gets through
        seen = b["on_screen"]
        for s in sorted(set(seen) - present):
            bad("binding_lists_absent",
                f"binding lists {s!r} as on screen, who is not",
                "on_screen is a record of who is there, not a wish list.")
        dupes = {x for x in seen if seen.count(x) > 1}
        for s in sorted(dupes):
            bad("binding_repeats",
                f"binding lists {s!r} {seen.count(s)} times",
                "List each person once.")

    return out


def assert_layer_presence(events: dict, entities: dict, plots: list | None = None,
                          brief_locations: list[str] | None = None) -> list[dict]:
    """Presence across a whole event layer — the failures a single node cannot show.

    Two of the worst findings in this project were only visible at layer scale:
    every event at one location because only one location entity existed, and a
    character ejected into a place her own dossier could not hold. Neither node
    was individually wrong.
    """
    out: list[dict] = []

    def bad(kind, msg, guidance):
        out.append({"kind": kind, "violation": msg, "guidance": guidance})

    evs = list(events.values()) if isinstance(events, dict) else list(events or [])
    locs = [e.get("location") for e in evs if isinstance(e, dict) and e.get("location")]
    distinct = sorted(set(locs))

    if locs and len(distinct) == 1 and len(evs) > 5:
        bad("single_location",
            f"all {len(evs)} events are at {distinct[0]!r}",
            "A story that happens in one room is a play. Check whether the "
            "location layer is under-populated — an event cannot be placed "
            "somewhere that has no entity.")

    loc_entities = [eid for eid, e in entities.items() if e.get("type") == "location"]
    if len(loc_entities) < 2 and len(evs) > 5:
        bad("too_few_locations",
            f"only {len(loc_entities)} location entit(ies) declared for {len(evs)} events",
            "Declare a location entity for every place the story visits before "
            "writing events, or the event layer has no legal way to move.")

    # a character in two places at one story time
    by_time: dict = {}
    for e in evs:
        if not isinstance(e, dict):
            continue
        t = (e.get("story_time") or {}).get("index")
        if t is None:
            continue
        for p in e.get("participants") or []:
            key = (p, t)
            prev = by_time.get(key)
            if prev and prev != e.get("location"):
                bad("bilocation",
                    f"{p!r} is at both {prev!r} and {e.get('location')!r} at story time {t}",
                    "One body, one place, one moment.")
            by_time[key] = e.get("location")

    # a state variable whose domain includes a place the character cannot be
    for eid, e in entities.items():
        for var, spec in (e.get("state_variables") or {}).items():
            dom = (spec or {}).get("domain") if isinstance(spec, dict) else None
            if not dom or "location" not in var.lower():
                continue
            known = {_norm(x) for x in distinct} | {
                _norm(entities[l].get("canonical_name")) for l in loc_entities}
            for val in dom:
                if _norm(val) and _norm(val) not in known and len(known) > 1:
                    bad("domain_names_unknown_place",
                        f"{eid}.{var} may be {val!r}, which is not a declared location",
                        "A location a character may occupy must exist as an entity. "
                        "Declaring it only in a domain lets the story go somewhere "
                        "that was never built.")
                    break

    return out


# --------------------------------------------------------------------------
# Guidance that descends with the work
# --------------------------------------------------------------------------

LEVEL_NOTES = {
    "root": """\
--- WHAT WILL BE CHECKED BELOW THIS LEVEL ---

Everything you name here becomes the closed vocabulary for every layer beneath.
Anything you leave out cannot be written about later, and anything you leave out
will be *forced* into whatever you did declare.

Two failures traced directly to a thin root in this project:
  - Nine entities were declared where the brief asked for thirty to forty. The
    event layer then placed all 22 events at the single location that existed.
  - An antagonist was given three state variables, so his humiliation and
    contempt had nowhere to live and were silently dropped.

Declare a location entity for every place the story visits. Declare a concept
entity for every mechanism the plot turns on. Under-declaring is not economy,
it is a wall the lower layers hit.""",

    "entities": """\
--- WHAT WILL BE CHECKED BELOW THIS LEVEL ---

The state variables you declare here are the only ones any event or scene may
move, and the domains you give them are the only values those variables may
take. Both are enforced mechanically, not judged.

Two rules that cost real errors:
  - Write initial values in the *same shape* as the domain. A domain of bare
    strings with an init of {"status": "..."} can never match, and every later
    change silently misses. This invalidated an entire state layer while passing
    every schema check.
  - Give a character enough variables to carry what the story does to them. A
    variable a scene needs and cannot find is a change that does not get
    recorded at all.

If a character can be in more than one place, every place in that domain must
exist as its own location entity.""",

    "events": """\
--- WHAT WILL BE CHECKED HERE AND BELOW ---

Checked mechanically, no judgement involved:
  - every participant resolves to a declared entity
  - every state change names a variable that entity owns, and a value inside
    that variable's declared domain
  - before != after; a change that changes nothing is not a change
  - a character is in one place at one story time
  - every causal reference points at a real event

Checked because it has failed before:
  - if every event is at one location, the location layer is too thin
  - a character cannot be moved to a place that has no entity""",

    "scene": """\
--- WHAT WILL BE CHECKED IN THIS SCENE ---

Three sets, and they are not the same set:
  SPEAKING   the cues in the slug line. Only these may be given dialogue.
  PRESENT    speaking, plus whoever the event layer places here. These may act
             and may have state moved.
  REFERABLE  everyone established. These may be thought about, and nothing else.

Conflating them has produced both a hollow node that reported success and a
constraint that mandated the error it was meant to prevent. Specifically:
  - a character with no lines who is cued is a deleted character, not a quiet one
  - a state change for someone not in the room is a change that cannot happen
  - a psychology block for someone absent belongs in another character's theory
    of mind instead

The location is a fact. If your idea needs a different room, the idea is wrong.""",
}


def briefing_for(level: str, sets: dict | None = None,
                 vocabulary: dict | None = None) -> str:
    """The level note, plus the concrete facts for this particular unit.

    Injected as the model descends. General guidance at the top of the tree,
    the actual closed sets at the bottom — so by the time it is writing a scene
    it has been told, in the checker's own words, exactly what is about to be
    verified.
    """
    parts = [LEVEL_NOTES.get(level, "")]
    if sets:
        parts.append(f"""
THIS UNIT, CONCRETELY
  location   {sets.get('location')!r} at {sets.get('time_of_day')!r}
  speaking   {sets.get('speaking') or []}  {'+ unresolved cues ' + str(sets['unresolved_cues']) if sets.get('unresolved_cues') else ''}
  present    {sets.get('present') or []}
  referable  {len(sets.get('referable') or [])} established entities""")
    if vocabulary:
        rows = [f"    {eid}.{var}: {spec.get('current')!r} -> one of "
                f"[{', '.join(spec['domain']) if spec.get('domain') else 'free text'}]"
                for eid, vs in vocabulary.items() for var, spec in vs.items()]
        parts.append("\nTHE ONLY STATE CHANGES THAT CAN BE RECORDED\n" + "\n".join(rows))
    return "\n".join(p for p in parts if p)


def format_violations(vios: list[dict]) -> str:
    """Violations as feedback a model can act on — each with its remedy."""
    if not vios:
        return ""
    lines = ["The following were checked mechanically and failed:"]
    for v in vios:
        lines.append(f"  - {v['violation']}")
        lines.append(f"    {v['guidance']}")
    return "\n".join(lines)
