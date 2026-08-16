"""Scaffolded transition assembly, for models with a fixed effort budget per call.

Diagnosis this was built from
-----------------------------
Measuring glm-5.2 against the transition schema showed a clean, repeatable
pattern. Output length stayed near 28,000 characters no matter what was asked
of it, and completeness fell as the number of deep structures rose:

    1 psychology block  →  1/1 carried a trajectory,  5 schema violations
    2 psychology blocks →  0/2 carried a trajectory, 16 schema violations
    4 psychology blocks →  2/4 carried a trajectory, 41 violations, and two of
                           the four were hollow: `entity: null` with one field
                           out of eleven filled

So the model does not scale its output to the requirement. It has a budget, it
divides it, and past roughly two parallel deep structures it starts emitting
placeholder shells that are shaped like answers. The `{"ref": "sc-004"}`
response that ended one run is the same behaviour across calls rather than
within one.

The remedy follows from the diagnosis rather than from hope: **ask for one deep
structure per call.** Each call then sits inside the budget, and the assembly
happens in code where it cannot degrade.

    call 1        craft, situation, interaction, decision   (no psychology)
    call 2..n+1   ONE psychology block, one per character
    call n+2      dynamics for the non-mind entities
    call n+3      continuity
    assemble      mechanically, then validate, then repair what still fails

Two smaller measures address the other observed failures: an explicit id roster
with a prohibition on inventing names, and a repair pass that feeds the actual
schema violations back rather than asking again and hoping.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from . import jsonschema_mini as js
from .transitions import (
    CONTINUITY_SCHEMA, CRAFT_SCHEMA, DYNAMICS_SCHEMA, PSYCH_SCHEMA,
    SPECIMEN_SCHEMA, TRANSITION_SCHEMA,
)


def _j(o, indent=1):
    return json.dumps(o, indent=indent, ensure_ascii=False)


# --------------------------------------------------------------------------

ID_DISCIPLINE = """\
IDS ARE FIXED AND YOU MAY NOT INVENT THEM.

Every entity you refer to must be one of the ids listed below, spelled exactly.
Not the character's name from the page, not the id with the name appended, not
an id you think would be sensible. If a figure on screen has no id in this list,
they are not an entity in this graph and you refer to them inside prose only,
never in an `entity` field.

VALID IDS
{roster}
"""

BUDGET_NOTE = """\
This call asks for ONE thing. Spend the whole of your effort on it. Do not
summarise, do not hedge, and do not leave a field for later — there is no later,
this is the only pass over this piece.
"""


@dataclass
class ScaffoldResult:
    transition: dict
    calls: int = 0
    violations_before_repair: int = 0
    violations_after_repair: int = 0
    repaired: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def _norm(x: str) -> str:
    return "".join(c for c in (x or "").lower() if c.isalnum())


def characters_in_scene(entities: dict, scene, events: dict | None = None,
                        *, cap: int = 4) -> tuple[list[str], list[str]]:
    """Who to write a psychology block for, and who could not be resolved.

    The first version matched a scene's speaker cues against canonical names by
    loose substring and nothing else. On a scene with two speakers it found one,
    so the scaffolded run analysed one fewer character than the single-call run
    it was meant to beat — a regression introduced by the harness rather than by
    the method.

    Three sources are needed, not one: the speaker cues, the aliases (a script
    says LIEUTENANT where the dossier says a name), and the participants the
    event layer already recorded for this scene. Anything still unmatched is
    returned separately rather than silently dropped, because an unresolvable
    speaker is a gap in the entity layer and should be visible.
    """
    people = {eid: e for eid, e in entities.items()
              if e.get("type") in ("character", "creature")}
    by_key: dict[str, str] = {}
    for eid, e in people.items():
        for label in [e.get("canonical_name", "")] + list(e.get("aliases") or []):
            if _norm(label):
                by_key[_norm(label)] = eid

    found: list[str] = []
    unresolved: list[str] = []
    for cue in getattr(scene, "speakers", []) or []:
        key = _norm(cue)
        hit = by_key.get(key)
        if not hit:                                  # partial, both directions
            hit = next((eid for k, eid in by_key.items()
                        if k and (k in key or key in k) and len(k) > 3), None)
        if hit:
            if hit not in found:
                found.append(hit)
        else:
            unresolved.append(cue)

    # the event layer already decided who is in this scene; trust it too
    for ev in (events or {}).values():
        if getattr(scene, "scene_id", None) in (ev.get("scenes") or []):
            for pid in ev.get("participants") or []:
                if pid in people and pid not in found:
                    found.append(pid)

    if not found:                                    # never analyse nobody
        found = [eid for eid, e in people.items() if e.get("salience") == "major"][:2]

    order = {"major": 0, "supporting": 1, "minor": 2, "mentioned": 3}
    found.sort(key=lambda eid: order.get(people[eid].get("salience"), 9))
    return found[:cap], unresolved


def roster_text(entities: dict, focus: list[str] | None = None) -> str:
    rows = []
    for eid, e in sorted(entities.items()):
        mark = "  <- in this scene" if focus and eid in focus else ""
        rows.append(f"  {eid:<10} {e.get('type','?'):<9} {e.get('canonical_name','?')}{mark}")
    return "\n".join(rows)


# --------------------------------------------------------------------------
# The individual calls
# --------------------------------------------------------------------------

def craft_prompt(node_id: str, ctx: dict, env: dict | None, roster: str) -> str:
    sub = {k: v for k, v in TRANSITION_SCHEMA["properties"].items()
           if k in ("target", "situation", "craft", "interaction", "decision")}
    schema = {"type": "object", "properties": sub,
              "required": ["target", "situation", "craft", "interaction", "decision"],
              "additionalProperties": False}
    return f"""\
TRANSITION → {node_id}   ·  PART 1 of several: THE CRAFT ARGUMENT

{BUDGET_NOTE}
You are deciding what should happen next. You have NOT read the finished work.
Do not describe; decide. Never write "the script does X", "as it turns out", or
anything implying you know the outcome.

Produce ONLY the craft reasoning: where the story stands, what this node is for,
why now, which alternatives you rejected and which one was close, what collides
here, and what you therefore decide. The psychological analysis is a SEPARATE
call and you must not attempt it here.

{ID_DISCIPLINE.format(roster=roster)}

ESTABLISHED SO FAR
{_j(ctx.get('root'))}

PLOTS
{_j(ctx.get('plots'))}

WHAT HAS HAPPENED
{_j(ctx.get('prior')) if ctx.get('prior') else '(this is the opening)'}

LIVE STATE
{_j(ctx.get('live_state'))}

{'PRODUCTION ENVELOPE — the shape you were handed, not evidence of content' if env else ''}
{_j(env) if env else ''}

SCHEMA
{_j(schema)}
"""


def psych_prompt(node_id: str, entity_id: str, entity: dict, ctx: dict,
                 craft: dict, roster: str) -> str:
    return f"""\
TRANSITION → {node_id}   ·  PSYCHOLOGY OF ONE CHARACTER: {entity_id}

{BUDGET_NOTE}
This call covers **{entity_id} and nobody else**. Other characters get their own
calls. Do not write about them except where their presence acts on this one.

Fill EVERY field. The one that is skipped most often, and the one that matters
most, is `trajectory`: this character does not stand still for the length of the
unit. Give the phases they move through, each with the specific perceivable
thing that triggers the shift, at least two and preferably four. A single frozen
moment is not a trajectory and will be rejected.

Also required and also frequently skipped: theory of mind to THREE degrees for
each other character who matters here, and the `accuracy` field saying where
that model of the other person is WRONG and what the error will cost. A theory
of mind that is always right produces no drama.

{ID_DISCIPLINE.format(roster=roster)}

THIS CHARACTER'S DOSSIER
{_j(entity)}

THE CRAFT REASONING ALREADY DONE FOR THIS NODE
{_j(craft)}

LIVE STATE
{_j(ctx.get('live_state'))}

Return a single object — the psychology block for {entity_id}, nothing else.

SCHEMA
{_j(PSYCH_SCHEMA)}
"""


def specimen_prompt(node_id: str, craft: dict, psych: list[dict], roster: str) -> str:
    return f"""\
TRANSITION → {node_id}   ·  THE SPECIMEN EXCHANGE

{BUDGET_NOTE}
Everything reasoned so far is unfalsifiable until somebody speaks. An immaculate
analysis and a dead scene look identical on paper. Write the lines and find out.

Draft six to ten lines of the ACTUAL DIALOGUE at the moment the craft reasoning
calls the turning point — real lines as they would be spoken, each with its
subtext. Then read them back cold and check every risk the reasoning listed
against them: does the exchange avoid it, and which line proves it?

If the two speakers could swap lines without anyone noticing, say so plainly and
say what you are changing. That failure is invisible from inside.

{ID_DISCIPLINE.format(roster=roster)}

THE CRAFT REASONING
{_j(craft)}

THE PSYCHOLOGY
{_j([{k: p.get(k) for k in ('entity', 'intention', 'action', 'control')} for p in psych])}

SCHEMA
{_j(SPECIMEN_SCHEMA)}
"""


def dynamics_prompt(node_id: str, ctx: dict, craft: dict, roster: str) -> str:
    return f"""\
TRANSITION → {node_id}   ·  THE ENTITIES THAT ARE NOT MINDS

{BUDGET_NOTE}
Objects, locations, groups and concepts have states and trajectories too. What
forces act on them here, which axes move — custody, control, cohesion, credence,
condition, meaning — how they change in phases, and what the thing MEANS to the
characters afterwards that it did not mean before. An object whose meaning never
moves is set dressing, not an entity.

{ID_DISCIPLINE.format(roster=roster)}

THE CRAFT REASONING
{_j(craft)}

Return an ARRAY of dynamics blocks, one per non-mind entity that changes or
exerts force here.

SCHEMA FOR EACH ELEMENT
{_j(DYNAMICS_SCHEMA)}
"""


def continuity_prompt(node_id: str, ctx: dict, craft: dict, psych: list[dict]) -> str:
    return f"""\
TRANSITION → {node_id}   ·  CONTINUITY

{BUDGET_NOTE}
Cite your sources. Every established fact this node leans on names the node id
or JSON pointer it came from. Name the world rules you had to obey, and name the
contradictions this node could plausibly have introduced and how you avoided
them.

WHAT WAS DECIDED
{_j(craft.get('decision', craft))}

WHO IS INVOLVED
{_j([p.get('entity') for p in psych])}

ESTABLISHED MATERIAL YOU MAY CITE
{_j(ctx.get('prior')) if ctx.get('prior') else '(nothing prior)'}

SCHEMA
{_j(CONTINUITY_SCHEMA)}
"""


def repair_prompt(node_id: str, part: str, doc: dict, violations: list[str], schema: dict) -> str:
    return f"""\
REPAIR → {node_id} · {part}

The document below is missing required content. Return the COMPLETE corrected
document, not a patch and not only the missing pieces.

Fix exactly these violations and change nothing else:
{chr(10).join('  - ' + v for v in violations[:30])}

A field is not satisfied by a placeholder. If `trajectory` is missing, it needs
real phases with real triggers; if an entity id is wrong, it needs the right one
from the roster, not a renaming of the wrong one.

THE DOCUMENT
{_j(doc)}

SCHEMA
{_j(schema)}
"""


# --------------------------------------------------------------------------

def assemble(node_id: str, kind: str, craft_part: dict, psych: list[dict],
             dynamics: list[dict], specimen: dict, continuity: dict) -> dict:
    out = dict(craft_part)
    out.setdefault("target", {"kind": kind, "node_id": node_id, "ordinal": 0})
    out["psychology"] = psych
    out["dynamics"] = dynamics
    out["specimen"] = specimen
    out["continuity"] = continuity
    return out


def validate_part(doc, schema) -> list[str]:
    return js.validate(doc, schema)
