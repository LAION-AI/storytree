"""Reconstruction: given a finished screenplay, rebuild every layer above it.

The forward system invents a story and writes it down. This one is handed the
writing and has to recover the structure that would have produced it — story
root, exposé, plots, dossiers, events, scene definitions — such that every scene
node owns exactly one passage of the real script.

The interesting constraint is on the reasoning.

    THE TRANSITION IS BLIND.   THE NODE MAY CHEAT.

A transition written with the finished script in view is worthless as training
data: it is hindsight wearing the costume of deliberation, and it teaches a
model to sound like it is deciding while actually copying. So the transition
call never receives the script text. It sees only the layers reconstructed so
far and a thin *envelope* of deterministic metadata — how many scenes remain,
which location the next one is set in, who speaks in it — and from that it must
argue forward: what should happen next, for this audience, in this genre, given
these people in these states, and why now.

The node call then receives that reasoning *and* the actual passage, and writes
the node that matches what the script really does.

Because the two calls are separated, the gap between them can be measured. Every
node records a `divergence`: where the blind forecast matched the real scene,
where it missed, and what the miss reveals. That comparison is not a by-product —
it is the most valuable thing the pipeline produces, because it is a forecasting
record that no amount of post-hoc annotation can fake.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from . import screenplay as sp
from .craft import CRAFT_CHECKS, CRAFT_SHEET
from .plotembedding import rubric_text
from .summaries import SUMMARY_SPEC
from .schemas import ENTITY_SCHEMA, EVENT_SCHEMA, PLOT_SCHEMA, SCENE_SCHEMA, SCHEMAS
from .transitions import TRANSITION_SCHEMA


def _j(o, indent=1):
    return json.dumps(o, indent=indent, ensure_ascii=False)


# --------------------------------------------------------------------------
# System prompts — two different jobs, deliberately incompatible
# --------------------------------------------------------------------------

BLIND_SYSTEM = """\
You are a narrative architect reasoning FORWARD, with no knowledge of how the
story turns out.

You are building a work one node at a time. Before each node you write a
TRANSITION: a deliberate, fully externalized argument from everything already
established to what must come next.

THIS IS THE RULE THAT MATTERS: you have not read the finished work. It does not
exist yet. You are deciding, not recalling.

- Never write "the script does X", "as it turns out", "we later learn", or any
  phrase implying you know the outcome.
- Never justify a choice by its consequences downstream. You do not know them.
- You may be given thin factual metadata about the shape of the next unit —
  which location it occupies, who is present, roughly how long it runs. Treat
  that as a production constraint you have been handed, the way a writer is told
  a scene must play in one room with two actors. Reason about what to DO with
  it. Do not treat it as evidence of what happens.
- Where you are uncertain, say what you would need to know and commit anyway.
  A transition that hedges is not a decision.

Everything else follows the standing requirements: craft first, then a full
psychological account of everyone materially involved — perception across every
channel, appraisal against that character's own values, the social norms in
force, theory of mind to three degrees per pair with the error named, urges,
impairments, deliberate analysis, felt versus expressed with the leakage — then
trajectory in phases with perceivable triggers, then the entities that are not
minds, then continuity with sources cited.

Be specific. Generic psychology is the failure mode.

Return one JSON document conforming to the schema. No prose outside it."""


SIGHTED_SYSTEM = """\
You are recovering the structure of a finished screenplay.

You are given: the layers reconstructed so far, a TRANSITION containing the
reasoning that was done blind, and the actual passage of the script this node
corresponds to.

Your job is to write the node that describes WHAT THE SCRIPT ACTUALLY DOES.

- The script is the authority. Where the blind reasoning predicted something the
  script does not do, the script wins, without exception.
- Use the transition's vocabulary and its psychological reading wherever the
  script bears it out. That is what keeps the reconstructed layers coherent with
  each other rather than being a pile of independent summaries.
- Record the gap honestly in `divergence`. A node claiming the forecast was
  perfect is almost always wrong and destroys the value of the comparison.
- Obey the standing schema rules: state variables must be declared before they
  are changed, prose blocks inside profiles are decomposed one sentence per key,
  no arrays in patchable regions, and no direct speech in event actions or beat
  texts — report dialogue as semantics and illocutionary force even though you
  can see the actual lines.

Return one JSON document conforming to the schema. No prose outside it."""


# --------------------------------------------------------------------------
# The envelope: what a blind call is allowed to know
# --------------------------------------------------------------------------

def envelope(scene: sp.Scene, remaining: int, total: int) -> dict:
    """Deterministic production metadata — shape, never content.

    Everything here comes from the slug line and from counting, never from
    reading the scene. A writer handed this knows the room and the cast; they do
    not know what happens in it.
    """
    return {
        "position": f"scene {scene.index} of {total}",
        "scenes_remaining_after_this": remaining,
        "setting": {"interior_exterior": scene.kind, "location": scene.location,
                    "time_of_day": scene.time_of_day},
        "on_screen": scene.speakers,
        "approximate_length_words": scene.word_count,
        "dialogue_ratio": scene.dialogue_ratio,
        "note": ("This is the shape you have been given, not evidence of content. "
                 "Decide what should happen here."),
    }


def script_overview(summary: dict, headings: list[dict]) -> dict:
    """The only script-derived facts the upper layers may see up front.

    Reconstructing a story root needs the shape of the whole thing — how long,
    how many scenes, how many speakers, which locations recur. That is
    structural, and withholding it would make the task impossible rather than
    honest. The dialogue itself is never included here.
    """
    return {
        "scene_count": summary["scenes"],
        "estimated_pages_a4": summary["estimated_pages_a4"],
        "estimated_runtime_min": summary["estimated_runtime_min"],
        "mean_dialogue_ratio": summary["mean_dialogue_ratio"],
        "speakers": summary["distinct_speakers"],
        "locations": summary["locations"],
        "scene_headings": [{"scene_id": h["scene_id"], "heading": h["heading"],
                            "speakers": h["speakers"], "words": h["words"]} for h in headings],
    }


# --------------------------------------------------------------------------
# Upper layers — these DO see the script, because they describe the whole work
# --------------------------------------------------------------------------

def story_root_prompt(script_text: str, overview: dict, options: dict) -> str:
    return f"""\
RECONSTRUCT THE STORY ROOT (layers L0 + L1)

You are given a finished screenplay. Recover the root it would have been written
from: the identity, the audience, the register, the rules its world obeys, and
its position in the plot-embedding coordinate system.

This is description, not judgement. Score the work as it is, not as it might
have been. If the script is uneven, the root records what it is actually doing.

{CRAFT_SHEET}

STRUCTURAL OVERVIEW
{_j(overview)}

REQUESTED SHAPE
{_j(options)}

THE SCREENPLAY
{script_text}

WHAT TO PRODUCE

- Identity, audience, setting, point of view, style, as the script demonstrates
  them. `style.dialogue_ratio` should match the measured ratio above.
- `setting.rules_of_the_world`: the constraints the script actually obeys.
  Recover them from what does and does not happen. A rule nobody tests is not a
  rule; a rule the script breaks is not a rule either — record what holds.
- `style.forbidden_tics`: the habits this script conspicuously avoids.
- `plot_embedding`: score every key on the rubric below. Most keys in most works
  are 0. Be decisive and score honestly low.

{rubric_text()}

- `constraints`: fill these with the MEASURED shape of the work — the real scene
  count, the real word count — not with a target.
- `keep_in_mind`: the standing notes that would have had to exist for this
  script to come out the way it did. Include one naming the core conflict and
  one naming the crucible.

{_schema_block('story_root')}
"""


def _schema_block(stage: str) -> str:
    return f"SCHEMA (your output must validate against this):\n{_j(SCHEMAS[stage])}"


def expose_prompt(root: dict, script_text: str, overview: dict) -> str:
    return f"""\
RECONSTRUCT THE EXPOSÉ (layer L2)

{CRAFT_CHECKS}

STORY ROOT (already reconstructed)
{_j(root)}

STRUCTURAL OVERVIEW
{_j(overview)}

THE SCREENPLAY
{script_text}

WHAT TO PRODUCE

1. `ending_first` — how it ends, what the resolution costs, the final image.
2. `synopsis` — 450-550 words, one sentence per key (s01, s02, …), chronological
   in STORY time, ending given away. Later layers cite these keys, so each must
   be a single, self-contained claim.
3. `jacket_copy` — 120-150 words in the register of the work, withholding the end.
4. THE PLOT SUMMARIES.

{SUMMARY_SPEC}

{_schema_block('expose')}
"""


def plots_prompt(root: dict, expose: dict, script_text: str, overview: dict) -> str:
    return f"""\
RECONSTRUCT THE PLOT DECOMPOSITION (layer L4)

{CRAFT_CHECKS}

STORY ROOT
{_j(root)}

EXPOSÉ
{_j(expose)}

STRUCTURAL OVERVIEW
{_j(overview)}

THE SCREENPLAY
{script_text}

WHAT TO PRODUCE

The plots this script actually runs. A plot is a chain of cause and effect in
which an agent pursues an outcome against resistance, terminating in success,
failure, or transformation of the goal.

- Extract, do not invent. If the script carries three plots, return three. A
  chain you cannot give a goal, a resistance and an outcome is a motif, not a
  plot, and does not belong here.
- `agent` and `resistance` name entity ids you are declaring now; the dossier
  layer will write exactly these.
- `spine`: the ordered steps as the script plays them, keyed st1, st2, …, each
  with a dramaturgical `function` and an `intent`.
- `because`: where a step of one plot is caused by a step of another. This is
  what distinguishes a woven script from a braided one; record it where it is
  really there and nowhere else.
- `covers_synopsis`: which exposé sentences each plot is answerable for.

{_schema_block('plots')}
"""


def entities_prompt(root: dict, expose: dict, plots: dict, script_text: str) -> str:
    return f"""\
RECONSTRUCT THE ENTITY DOSSIERS (layer L3)

{CRAFT_CHECKS}

STORY ROOT
{_j(root)}

EXPOSÉ
{_j(expose)}

PLOTS
{_j(plots)}

THE SCREENPLAY
{script_text}

WHAT TO PRODUCE

The dossiers. This object IS the world state at the opening of the script, so it
is the most consequential document in the reconstruction.

- Every entity the plots forward-declared, plus the locations, objects, groups
  and standing beliefs the script gives causal weight to.
- `profile`: recovered from what the script shows. EVERY factual sentence must
  carry a `source` in its tags saying where it comes from, in one of exactly
  three forms:
      "seen:sc-014"   the script shows this, in that scene
      "said:sc-014"   a character asserts it there — which is not the same as it
                      being true, and you must not silently upgrade it
      "inferred"      you concluded it; the script does not state it
  A sentence you cannot label with one of these does not belong in the dossier.

  This is the failure this instruction exists to prevent: a reconstruction that
  states a recalled detail in exactly the same confident register as an observed
  one. If you find yourself writing a fact you are recalling from the wider work
  rather than reading off this script, either locate it and cite the scene, or
  tag it "inferred", or leave it out. Smooth, unflagged fabrication is the worst
  thing this layer can produce, because everything downstream trusts it. Every prose block is a sentence map
  keyed one sentence per key, nothing over 180 characters.
- `state_variables`: THE CRITICAL FIELD. Declare exactly the variables the
  script's events actually move. Read the script for what is different about a
  character at the end of a scene, and give that a name, a kind, a dimension and
  an initial value. A variable nothing in the script changes should not exist; a
  change with no variable to land on will block the event layer.
- `state`: the values as the script opens, mirroring every declared `init`.

{_schema_block('entities')}
"""


# --------------------------------------------------------------------------
# Per-node prompts
# --------------------------------------------------------------------------

OUTCOME_BEARING = ("expose", "synopsis", "ending_first", "plot_summary_short",
                   "plot_summary_long", "jacket_copy")


def blind_context(ctx: dict, upto_step: dict | None = None) -> dict:
    """Strip everything a writer at this point could not know.

    A review found the hole this closes. The blind call was being handed the
    reconstructed exposé — and that exposé was derived from the finished script,
    so it names the outcome at beat resolution. One trace duly argued straight
    from it: "rejected_because: The synopsis requires her escape here". The scene
    text never leaked, but the answer key did, which makes the forecast worth
    less than it looked.

    So: no synopsis, no ending, no summaries. Plot spines are truncated to the
    steps already discharged, because a spine recovered from the whole film is
    itself a description of the ending.
    """
    out = {k: v for k, v in ctx.items() if k not in OUTCOME_BEARING}
    plots = ctx.get("plots") or []
    if plots and upto_step:
        trimmed = []
        for p in plots:
            reached = upto_step.get(p.get("plot_id"))
            spine = p.get("spine") or {}
            keep = {k: v for k, v in spine.items()
                    if reached is None or v.get("step", 0) <= reached}
            q = {k: v for k, v in p.items()
                 if k not in ("spine", "outcome", "resolution_step")}
            q["spine_so_far"] = keep
            q["outcome"] = "not yet decided"
            trimmed.append(q)
        out["plots"] = trimmed
    return out


def blind_transition_prompt(kind: str, node_id: str, ctx: dict, env: dict | None) -> str:
    task = {
        "event": ("You are about to decide EVENT {id}. What happens next at this point in story "
                  "time, to whom, and what changes as a result?"),
        "scene": ("You are about to decide SCENE {id}. How is the next movement of this story "
                  "staged — who is in the room, what collides, and what is different at the end?"),
    }.get(kind, "Decide node {id}.")

    return f"""\
TRANSITION → {node_id}   ({kind})

{task.format(id=node_id)}

You have NOT read the finished work. Reason forward from what is established
below to what must come next. Do not describe; decide.

═══════════════════════════════════════════════════════════════════════
ESTABLISHED SO FAR
═══════════════════════════════════════════════════════════════════════

STORY ROOT
{_j(ctx.get('root'))}

PLOTS, TRUNCATED TO WHAT HAS BEEN REACHED
(You are given the spine steps already discharged and nothing beyond them. The
outcome of each plot is not yet decided — deciding it is part of your job.)
{_j(ctx.get('plots'))}

ENTITIES AND THE VARIABLES THAT MAY MOVE
{_j(ctx.get('entities'))}

WHAT HAS ALREADY HAPPENED
{_j(ctx.get('prior')) if ctx.get('prior') else '(nothing yet — this is the opening)'}

LIVE STATE AT THIS MOMENT
{_j(ctx.get('live_state')) if ctx.get('live_state') else '(the opening state)'}

{'PRODUCTION ENVELOPE — the shape you have been handed, not evidence of content' if env else ''}
{_j(env) if env else ''}

═══════════════════════════════════════════════════════════════════════

Write the transition. Fill every field the schema requires; depth is the point.
Remember: you are deciding what should happen, not recalling what did.

SCHEMA
{_j(TRANSITION_SCHEMA)}
"""


SCENE_BINDING_NOTE = """\
BINDING RULE. This scene node corresponds to exactly one passage of the script,
given below and identified by `bound_scene_id`. Its beats must describe THAT
passage, in order, and nothing outside it. Do not merge in material from
adjacent scenes and do not summarise the whole act. The passage is the node's
territory and its boundary."""


def scene_node_prompt(node_id: str, ctx: dict, transition: dict,
                      scene_meta: dict, scene_text: str) -> str:
    return f"""\
RECONSTRUCT SCENE NODE {node_id}

{SCENE_BINDING_NOTE}

THE BLIND REASONING THAT WAS DONE FOR THIS NODE
{_j(transition)}

ENTITIES AND THEIR PERMITTED VARIABLES
{_j(ctx.get('entities'))}

EVENTS THIS SCENE MAY REALIZE
{_j(ctx.get('events'))}

LIVE WORLD STATE AS THIS SCENE OPENS
{_j(ctx.get('live_state'))}

SCENE METADATA (deterministic, from the parse)
{_j(scene_meta)}

═══════════════════════════════════════════════════════════════════════
THE ACTUAL PASSAGE — this is what the node must describe
═══════════════════════════════════════════════════════════════════════
{scene_text}
═══════════════════════════════════════════════════════════════════════

WHAT TO PRODUCE

The scene node, describing the passage above:

- `bound_scene_id` must be exactly "{scene_meta['scene_id']}".
- `beats`: the ordered units of change AS THE PASSAGE PLAYS THEM. Flat third
  person, 25-70 words each, NO direct speech even though you can see the lines —
  report what is said as semantics and illocutionary force.
- `changes`: the literal RFC 6902 operations that move declared state variables,
  with `before` equal to what the live state above actually holds.
- `entry_states` and `exit_states` read off the fold, not guessed.
- `divergence`: compare the blind transition against what the passage actually
  does. `predicted_correctly` — what the forecast got right. `missed` — what it
  did not anticipate. `why` — one sentence on what the miss reveals about the
  difference between a reasonable next move and this writer's actual move.
  Be honest; a claim of perfect prediction is almost always false and destroys
  the only reason the two calls were separated.

SCHEMA
{_j(SCENE_NODE_SCHEMA)}
"""


# Scene schema plus the two reconstruction-only fields.
SCENE_NODE_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["scene"],
    "properties": {
        "scene": {
            **SCENE_SCHEMA,
            "properties": {
                **SCENE_SCHEMA["properties"],
                "bound_scene_id": {
                    "type": "string",
                    "description": "The parsed script scene this node owns. Exactly one.",
                },
                "divergence": {
                    "type": "object", "additionalProperties": False,
                    "required": ["predicted_correctly", "missed", "why"],
                    "properties": {
                        "predicted_correctly": {"type": "array", "items": {"type": "string"}},
                        "missed": {"type": "array", "items": {"type": "string"}},
                        "why": {"type": "string"},
                        "forecast_quality": {
                            "type": "integer", "minimum": 0, "maximum": 100,
                            "description": "How close the blind reasoning came, 0-100.",
                        },
                    },
                },
            },
            "required": SCENE_SCHEMA["required"] + ["bound_scene_id", "divergence"],
        }
    },
}


__all__ = [
    "BLIND_SYSTEM", "SIGHTED_SYSTEM", "envelope", "script_overview",
    "story_root_prompt", "expose_prompt", "plots_prompt", "entities_prompt",
    "blind_transition_prompt", "scene_node_prompt", "SCENE_NODE_SCHEMA",
]
