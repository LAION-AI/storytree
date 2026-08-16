"""Prompt construction — the single source of truth for both backends.

The Hyprlab/Grok backend sends these strings to an API. The agent backend
writes the very same strings to a file for a spawned Claude Code agent to
execute. Neither backend is allowed its own prompt text: if the two paths
produced different instructions, comparing them would be meaningless.
"""

from __future__ import annotations

import json
from typing import Any

from .craft import CRAFT_CHECKS, CRAFT_SHEET
from .plotembedding import rubric_text
from .schemas import (
    NARRATIVE_VECTOR_GROUPS, PLOT_TYPES, SCHEMAS, STATE_DIMENSIONS,
)

STAGES = ["story_root", "expose", "plots", "entities", "events", "scenes", "prose"]


def _json(obj: Any, indent: int = 1) -> str:
    return json.dumps(obj, indent=indent, ensure_ascii=False)


# --------------------------------------------------------------------------
# House rules — prepended to every stage
# --------------------------------------------------------------------------

SYSTEM = """\
You are a narrative architect. You build stories as explicit, machine-readable
structure before a single line of prose exists: a story root, an exposé, plots,
entity dossiers, a causal event graph, scene definitions with beats, and only
then prose.

You are working inside a strict pipeline. Each layer may reference every layer
above it and may never contradict one. You produce exactly one layer per call.

STANDING RULES

1. OUTPUT. Return one JSON document and nothing else — no prose preamble, no
   markdown fence, no commentary. It must satisfy the schema you are given.

2. NO ARRAYS IN PATCHABLE REGIONS. Anything that might later be revised is an
   object keyed by a stable id, never an array. JSON Pointer addresses arrays
   by position, so inserting one element silently re-targets every pointer
   written after it. Use {"b01": {...}, "b02": {...}}, not [{...}, {...}].
   Arrays are permitted only for flat, declarative lists of strings (aliases,
   tags, id references) and for beats, which are append-only and never patched.

3. SENTENCE ADDRESSABILITY. Every block of freeform prose inside an entity
   profile is decomposed one sentence per key: {"b01": {"text": "<one
   sentence>", "when": "...", "tags": [...]}}. No string inside a profile may
   run past 180 characters. A backstory is usually never revised — but the
   story must be able to revise it, which means every sentence of it needs its
   own address.

4. STATE IS DECLARED BEFORE IT IS CHANGED. An entity may only be changed
   through a state variable its own dossier declares. If a later layer needs a
   variable that does not exist, that is a fault in the dossier, not a licence
   to invent one mid-flight.

5. NOTHING FLOATS, NOTHING IS INVENTED. Every event serves a plot. Every plot
   has an agent, a goal, resistance, and an outcome. A candidate plot without
   all four is a motif, not a plot, and belongs in the narrative vector.
   Returning fewer, better-founded items is correct behaviour, not incomplete
   work.

6. NO DIRECT SPEECH below the exposé. Event actions and beat texts are flat,
   third-person, present-neutral descriptions. Render dialogue as reported
   semantics and illocutionary force: not «"You lied to me," she said» but «she
   accuses him of having lied, framing it as a betrayal of the family rather
   than of herself, and demands an admission rather than an apology». These
   layers are the preimage of the prose, not a draft of it.

7. IDS ARE STABLE AND TYPED. ch-NN characters and creatures, lo-NN locations,
   ob-NN objects, gr-NN groups, cn-NN concepts, pl-NN plots, ev-NNN events,
   sc-NNN scenes. Zero-padded. Never reuse or renumber an id once issued.
"""


def _strip_descriptions(node, keep_depth: int = 0):
    """Drop `description` fields below a depth. The prose instructions above the
    schema already carry them, and duplicating 76 rubric entries into the JSON
    costs thousands of tokens for no added constraint."""
    if isinstance(node, dict):
        out = {}
        for k, v in node.items():
            if k == "description" and keep_depth <= 0:
                continue
            out[k] = _strip_descriptions(v, keep_depth - 1)
        return out
    if isinstance(node, list):
        return [_strip_descriptions(v, keep_depth) for v in node]
    return node


def _schema_block(stage: str) -> str:
    schema = SCHEMAS[stage]
    if stage == "story_root":
        # The plot-embedding rubric is printed in full above; the schema only
        # needs to state the shape.
        schema = dict(schema)
        props = dict(schema["properties"])
        props["plot_embedding"] = _strip_descriptions(props["plot_embedding"], keep_depth=1)
        schema["properties"] = props
    return f"SCHEMA (your output must validate against this):\n{_json(schema)}"


# --------------------------------------------------------------------------
# Per-stage user prompts
# --------------------------------------------------------------------------

def story_root_prompt(brief: str, options: dict) -> str:
    return f"""\
STAGE 1 of 7 — STORY ROOT (layers L0 + L1)

Everything downstream is derived from this document, so it is the one place
where taste is expressed as parameters rather than as prose. Be decisive: a
root that hedges produces a story that hedges.

{CRAFT_SHEET}

THE BRIEF
{brief.strip()}

REQUESTED SHAPE
{_json(options)}

WHAT TO PRODUCE

- Bibliographic and editorial identity: genre, audience, setting, point of
  view, style. `style.forbidden_tics` is your instruction to your future self
  at the prose stage — name the habits this particular story must not fall
  into.
- `setting.rules_of_the_world`: hard constraints no later layer may violate.
  For a fantasy, this is where magic gets a cost and a limit. Rules that cannot
  be violated are what make later events feel earned rather than convenient.
- `plot_embedding`: the fixed coordinate system below. Score EVERY key. This is
  the corpus-wide control surface, so honesty matters more than flattery — a
  work strong in five genres is a work; a work strong in twenty is a work that
  has not been scored.

{rubric_text()}

- `state_dimensions`: choose the subset of the closed vocabulary this work
  actually needs, from {STATE_DIMENSIONS}. Every state change in the story will
  be typed with one of them. Enable domain extensions only if the genre uses
  them.
- `constraints`: honour the requested shape exactly. plot_count in particular
  is a hard number, not a suggestion.
- `keep_in_mind`: standing notes every later layer must respect — tonal
  guardrails, a motif to plant, a thing the ending depends on. Include at least
  one note that names the story's CORE CONFLICT and one that names the
  CRUCIBLE binding the principals together.

{_schema_block("story_root")}
"""


def expose_prompt(root: dict) -> str:
    return f"""\
STAGE 2 of 7 — EXPOSÉ (layer L2)

{CRAFT_CHECKS}

STORY ROOT
{_json(root)}

WHAT TO PRODUCE

Work in this order, and do not deviate from it:

1. `ending_first`. Decide how the story ends, what the resolution costs, and
   what the final image is — BEFORE you write a single sentence of the
   synopsis. This is the whole point of the stage. A synopsis written
   front-to-back degrades into "and then, and then, and then"; a synopsis
   written toward a known ending has a spine.

2. `synopsis`. A full-spoiler condensation of 450-550 words that gives the
   ending away. Split it ONE SENTENCE PER KEY — s01, s02, s03, ... Each entry
   carries the sentence, its dramatic `function`, and `story_time_rank`, the
   position of that beat in STORY time (which may differ from the order you
   present it in).

   It must state, in chronological story order: the initial situation and the
   disturbance to it; the protagonist's goal and why it matters; the principal
   obstacles and who supplies them; the two or three turns that reframe the
   problem; the climax; the resolution and its cost; and one sentence per
   subplot.

   The sentence keys are load-bearing. Every plot in the next stage will claim
   the sentences it is responsible for, and a sentence no plot claims is a
   promise the story does not keep.

3. `jacket_copy`. 120-150 words in the register of the work, withholding the
   ending. This is the marketing artifact.

4. `plot_summary_short` (150-250 words — a HARD ceiling; count them, and cut
   subplot detail rather than exceed it) and `plot_summary_long` (700-1200
   words). These are NOT marketing copy and NOT the synopsis reformatted. They
   are the plain encyclopedia account of what happens, written for a person who
   knows nothing about this story and wants to understand it.

   Neutral third person, present tense, strictly chronological, ending given
   away. Name people and places. Say what happens and what it causes. No
   rhetorical questions, no "but will she succeed?", no atmosphere, no
   withholding, no register performance — you are informing, not seducing.
   Explain a rule of the world the first time it matters, in half a sentence,
   and move on.

   The long one covers every plot and the fate of every significant character,
   in paragraphs broken by movement. Test for both: if a reader finishes and
   cannot say how the story ends and why, you have written a teaser instead of
   a summary, and it is wrong.

{_schema_block("expose")}
"""


def plots_prompt(root: dict, expose: dict) -> str:
    plot_count = root.get("constraints", {}).get("plot_count", "as many as the story needs")
    return f"""\
STAGE 3 of 7 — PLOT DECOMPOSITION (layer L4)

{CRAFT_CHECKS}

STORY ROOT
{_json(root)}

EXPOSÉ
{_json(expose)}

WHAT TO PRODUCE

Exactly {plot_count} plots. A plot is defined operationally and narrowly:

    a chain of cause and effect in which an agent pursues an outcome against
    resistance, and which terminates in success, failure, or transformation of
    the goal.

It is not a theme, not a mood, not a character. Classify each into one of:
{', '.join(PLOT_TYPES)}.

For each plot:

- `agent` and `resistance` name entity ids. You are forward-declaring the cast
  here — the next stage writes dossiers for exactly these ids, so choose them
  deliberately and keep the numbering tight (ch-01, ch-02, ...). Resistance may
  also name another plot, when what obstructs this goal is the pursuit of that
  one.
- `spine`: the ordered steps of the chain, keyed st1, st2, st3, ... Each step
  gets a `function` (a dramaturgical label such as state_of_rupture,
  forced_proximity, point_of_no_return, false_victory) and an `intent` of one
  or two sentences saying what must happen there. Do not name events yet; the
  event layer binds itself to these steps.
- `because`: this is what separates a woven story from a braided one. When a
  step of this plot is caused by a step of another, record it as "pl-01:st3".
  Subplots that run in parallel and never touch are the standard failure of
  machine-made fiction; at least one cross-plot `because` is required, and the
  two plots must genuinely constrain each other — competing for the same agent,
  the same hour, the same resource.
- `covers_synopsis`: the synopsis sentence keys this plot is answerable for.
  Between them, the plots must cover every sentence of the synopsis.
- `outcome` and `resolution_step`: how and where it ends. Not every plot may
  succeed.

{_schema_block("plots")}
"""


def entities_prompt(root: dict, expose: dict, plots: dict) -> str:
    referenced = sorted({
        ref
        for plot in plots.get("plots", [])
        for ref in plot.get("agent", []) + plot.get("resistance", [])
        if not ref.startswith("pl-")
    })
    return f"""\
STAGE 4 of 7 — ENTITY DOSSIERS (layer L3)

{CRAFT_CHECKS}

STORY ROOT
{_json(root)}

EXPOSÉ
{_json(expose)}

PLOTS
{_json(plots)}

WHAT TO PRODUCE

The dossiers. This object IS the world state at t0 — the initial value of every
variable the rest of the story will modify — so it is the most consequential
document in the pipeline.

The plot layer forward-declared these ids, and every one of them needs a
dossier: {referenced}

Add the entities the plots imply but did not name: the locations the action
needs, the objects that carry causal weight, the factions and standing beliefs
that act on people. An entity is anything noteworthy enough to influence a
plot — do not inventory the furniture, but do give a dossier to anything a
state change could ever attach to. Characters and creatures share a type; a
person, a talking wolf and a construct are all modelled the same way.

For each entity:

- `profile`: a deep, freely nested dossier. Characters and creatures carry
  demographics, appearance, voice_and_speech, habits_and_tells, backstory,
  wound, want, need, values, fears, competences, limitations,
  problem_solving_style, coping_strategies, health, moral_axis. Locations carry
  geography, atmosphere, control, access, significance. Objects carry
  provenance, description, function, symbolic_load, custody. Groups carry
  membership, hierarchy, goals, resources, cohesion. Concepts carry content,
  believers, authority, causal_power.

  Write it richly — this is where the story's raw material lives, and later
  layers can only spend what you deposit here. But obey rule 3 without
  exception: every prose block is a sentence map, keyed b01/a01/v01/..., one
  sentence per key, nothing over 180 characters. Prefer a dozen short
  addressable sentences to one long unaddressable paragraph.

- `relationships`: keyed by the other entity's id, with a `kind`, a `valence`
  from -100 to 100, and sentence-mapped `notes`. Relationships between
  locations, objects and people are legitimate and often the useful ones.

- `state_variables`: THE MOST IMPORTANT FIELD. Declare the named variables
  that events are permitted to modify for this entity, and nothing else will
  be modifiable. Each gets a `kind` (scalar / enum / text / bool), a
  `description`, a `dimension` from {STATE_DIMENSIONS}, a `range` for scalars
  or a `domain` for enums, and an `init` value.

  Choose variables that will actually move. A variable nothing ever changes is
  dead weight; a change with no variable to land on will block the event layer.
  Look at the plot spines and ask, for each step, what is different afterwards
  and in whom. Major characters typically want 4-7 variables; a location or an
  object 1-3. Include at least one variable per entity that the ending needs.

- `state`: the live values at t0. Every key must appear in state_variables and
  every value must equal that variable's `init`. This redundancy is checked
  mechanically.

- `arc`: one line on where the entity starts and where it ends up.

{_schema_block("entities")}
"""


def events_prompt(root: dict, expose: dict, plots: dict, entities: dict) -> str:
    inventory = {
        eid: {
            "name": entity.get("canonical_name"),
            "type": entity.get("type"),
            "state_variables": {
                name: {"kind": spec.get("kind"), "dimension": spec.get("dimension"),
                       "init": spec.get("init"),
                       **({"range": spec["range"]} if "range" in spec else {}),
                       **({"domain": spec["domain"]} if "domain" in spec else {})}
                for name, spec in entity.get("state_variables", {}).items()
            },
        }
        for eid, entity in entities.get("entities", {}).items()
    }
    target = root.get("constraints", {}).get("event_count_target", "as many as the spines need")
    return f"""\
STAGE 5 of 7 — EVENT CHAIN (layer L5)

{CRAFT_CHECKS}

STORY ROOT
{_json(root)}

PLOTS
{_json(plots)}

THE ONLY VARIABLES THAT EXIST
{_json(inventory)}

WHAT TO PRODUCE

A directed acyclic graph of about {target} events, ordered by story time.

An event is something that happens at a locatable point in story time and
changes at least one declared state variable of at least one entity. If nothing
changes, it is not an event — it is scenery.

Events are NOT scenes and must not be written as if they were. An earthquake
felt in four places is one event across four scenes; a kitchen-table
conversation containing a confession, a refusal and a threat is one scene
containing three events. The scene layer comes next and will do that mapping.

For each event:

- `story_time.index`: unique and ascending in story time. Leave gaps of 1 so
  later insertion is possible.
- `primary_plot`: EXACTLY ONE. This is the event's parent in the story tree.
  `plots` lists every plot it serves and must contain the primary. An event
  that serves two plots at once is the good kind of event; an event that serves
  none is a fault.
- `plot_bindings`: which spine steps this event discharges, as
  {{"plot": "pl-01", "step": "st3"}}. Between them, the events must discharge
  EVERY spine step of EVERY plot. A step no event discharges is a promise the
  structure makes and the story never keeps.
- `state_changes`: DECLARATIONS of what this event alters. Each names an
  entity, one of that entity's declared variables, the canonical JSON Pointer
  `/<entity_id>/state/<variable>`, the dimension, the value `before`, the value
  `after`, and a `magnitude` 0-100 for how much this matters.

  `before` must be the value that variable actually holds at this point in
  story time — that is, the `after` of the most recent earlier event that
  touched it, or its `init` if none did. Track this as you go. It will be
  checked by folding every patch in the finished story, and a contradiction
  here is the single most common way this kind of structure fails.

  The scene layer will realize each of these declarations with an actual patch
  operation, and it may realize no others. Declare precisely.
- `caused_by` / `causes`: the causal edges, mutually consistent — if A lists B
  in `causes`, B must list A in `caused_by`. Causes must precede effects in
  story time. Events with no cause set `is_root`, events causing nothing set
  `is_sink`; the graph must otherwise be connected and acyclic. `causal_note`
  says in one sentence why this event was possible only now.
- `action`: 60-160 words, third person, NO direct speech, no atmosphere.

{_schema_block("events")}
"""


def scenes_prompt(root: dict, plots: dict, entities: dict, events: dict,
                  chunk: list[str], live_state: dict, previous_tail: str = "",
                  scene_start: int = 1) -> str:
    chunk_events = {eid: events["events"][eid] for eid in chunk}
    dossiers = {
        eid: {
            "name": entity.get("canonical_name"),
            "type": entity.get("type"),
            "state_variables": entity.get("state_variables", {}),
        }
        for eid, entity in entities.get("entities", {}).items()
    }
    carry = f"""
PREVIOUSLY (the tail of the scenes already written — do not repeat them)
{previous_tail}
""" if previous_tail else ""

    return f"""\
STAGE 6 of 7 — SCENE DEFINITIONS (layer L6)

This is the deepest structural layer and the preimage of the prose. Flat
register: no style, no atmosphere, no direct speech. Its job is to be a
complete specification of what happens, such that the prose stage never has to
invent anything and never has to remember anything.

STORY ROOT (style and vector, for pacing decisions only)
{_json({k: root.get(k) for k in ("title", "form", "pov", "style", "narrative_vector", "keep_in_mind")})}

PLOTS
{_json(plots)}

ENTITIES AND THEIR PERMITTED VARIABLES
{_json(dossiers)}

THE LIVE WORLD STATE AS THIS BATCH BEGINS
{_json(live_state)}

EVENTS TO REALIZE IN THIS BATCH
{_json(chunk_events)}
{carry}
WHAT TO PRODUCE

Scenes numbering from sc-{scene_start:03d}, covering every event in this batch.

- `primary_event`: EXACTLY ONE — the scene's parent in the story tree.
  `events` lists every event the scene realizes and must contain the primary.
  `primary_plot` must equal the primary event's `primary_plot`; the primary
  edges scene -> event -> plot form one spanning tree over the whole story.
- `discourse_index`: the order the reader meets the scene, which need not be
  story order.
- `entry_states`: for every entity present, the values of the variables this
  scene will touch or depend on, AS THEY ACTUALLY ARE on arrival. Read them off
  the live world state above and off any earlier scene in this same batch. This
  is checked by folding every patch in the story; a guess here fails.

- `beats`: the ordered units of change. A beat is an action-reaction pair that
  shifts something. Typically 3-7 per scene. Each beat carries:
    * `event_id` — the ONE event it belongs to. A scene may contain beats from
      several events, but within a scene the beats must not run backwards in
      story time.
    * `text` — 25-70 words, flat third person, no direct speech, reported
      illocutionary force.
    * `changes` — THE PATCHES. This is where state actually moves, and beats
      are the only place in the entire pipeline that authors a change. Each
      change names the entity, the variable, the dimension, the `before` value,
      the `after` value, a `magnitude`, and `op`: a literal RFC 6902 operation,

          {{"op": "replace", "path": "/ch-01/state/oath_intact", "value": false}}

      The path is a JSON Pointer into the world state, whose top level is keyed
      by entity id. `before` must equal what the pointer holds when this beat
      begins; `after` must equal what the op writes. Ops may also reach outside
      `/state` — patching `/ch-02/relationships/ch-01/valence`, or adding a
      sentence to `/ch-01/profile/backstory/b07` when the story reveals
      something about the past — but only variables declared in
      `state_variables` may be changed under `/state`.

      Between them, the beats of an event must realize exactly the changes that
      event declared: every declaration realized, and nothing beyond them.
      Setup beats may carry an empty `changes` list, but a scene in which
      nothing at all changes has not earned its place.

- `exit_states`: the same shape as entry_states, after the last beat. It must
  equal entry_states with this scene's patches applied.
- `tension_in` / `tension_out`, `dramatic_function`, `questions_opened` (keyed
  q01, q02, ...) and `questions_closed` (keys opened by earlier scenes).
- `target_words`: the prose budget for this scene.

{_schema_block("scenes")}
"""


SCREENPLAY_INSTRUCTIONS = """\
Write it as a SCREENPLAY SCENE in standard spec format. Roughly 70% dialogue,
30% action — this is a fast read, and the page should look like one.

FORMAT, exactly:

    INT. THE FORGE-HOUSE - NIGHT

    Action lines in the present tense. Third person, objective. What a
    camera sees and a microphone hears, nothing else.

                        WILLA
                (setting the bar down)
              Dialogue goes here.

                        ORREN
              And here.

- Slug line first, in capitals: INT. or EXT., the location, a dash, and one of
  DAY / NIGHT / DAWN / DUSK / CONTINUOUS. Use the location's plain name.
- Action lines: present tense, 1-3 lines each, never more than four. Break a
  long block into several short ones. A character's name is CAPITALIZED on
  first appearance only.
- Character cues are indented and capitalized. Parentheticals only when the
  reading is not obvious from the line — sparingly, one or two per page at
  most.
- Dialogue carries the scene. Every beat that moves a state variable should
  move it in what people say to each other, or in what they refuse to say.
- No camera directions (no ANGLE ON, no PUSH IN, no WE SEE), no unfilmable
  interiority (never «she remembers», «she decides» — show the decision), no
  novelistic description. If it cannot be photographed or recorded, it does not
  go on the page.
- Use (CONT'D), (O.S.) and (V.O.) only where genuinely needed. No MORE/CONT'D
  page-break artifacts.
- Do not number the scene, do not write FADE IN / CUT TO, do not add a title.

Indentation is what makes it readable: action flush left, character cues about
20 spaces in, parentheticals about 16, dialogue about 10. Keep it consistent
across every scene of the script — this is one document.
"""

PROSE_INSTRUCTIONS = """\
Write it as finished prose in the point of view and tense named on the style
card.

- Realize every beat in order. A beat is not a paragraph — some take a line,
  some take a page.
- Here you may finally use direct speech, interiority, atmosphere and image.
  That is what this layer is for; the layers above deliberately withheld them.
"""


def prose_prompt(root: dict, scene: dict, entities: dict, events: dict,
                 entry_world: dict, previous_tail: str = "",
                 fmt: str = "auto") -> str:
    present = scene.get("present", []) + [scene.get("location")]
    cast = {
        eid: entities["entities"][eid]
        for eid in present
        if eid and eid in entities.get("entities", {})
    }
    style = {k: root.get(k) for k in ("title", "language", "pov", "style", "setting", "audience")}
    style["narrative_vector"] = root.get("narrative_vector")
    style["keep_in_mind"] = root.get("keep_in_mind")

    entry = {
        eid: entry_world.get(eid, {}).get("state", {})
        for eid in present if eid
    }
    scene_events = {eid: events["events"][eid] for eid in scene.get("events", []) if eid in events.get("events", {})}
    carry = f"""
THE END OF THE PREVIOUS SCENE (continue from here; do not recap it)
...{previous_tail}
""" if previous_tail else ""

    if fmt == "auto":
        fmt = "screenplay" if root.get("form") in ("screenplay", "teleplay") else "prose"
    body = SCREENPLAY_INSTRUCTIONS if fmt == "screenplay" else PROSE_INSTRUCTIONS
    unit = "of screen time" if fmt == "screenplay" else "of finished prose"

    return f"""\
STAGE 7 of 7 — {'SCREENPLAY' if fmt == 'screenplay' else 'PROSE'} ({scene.get('scene_id')})

You are writing the leaf of the graph. Everything above it has already been
decided, and none of it is yours to revise.

{CRAFT_CHECKS}

STYLE CARD
{_json(style)}

THE CAST AND SETTING OF THIS SCENE, IN FULL
{_json(cast)}

THE EVENTS THIS SCENE REALIZES
{_json(scene_events)}

WORLD STATE ON ENTERING THE SCENE
{_json(entry)}

THE SCENE DEFINITION
{_json(scene)}
{carry}
WHAT TO PRODUCE

Roughly {scene.get('target_words', 900)} words {unit} in {root.get('language', 'English')}.
The scene is carried by {scene.get('pov')}; what the audience follows is what
that character is doing and wanting here.

{body}
- Realize every beat in order. The beats are what happens; how it happens is
  yours.
- The state changes are not optional and not decorative. Where a beat moves a
  variable, the page must dramatize that movement so the audience registers it,
  without ever naming the variable.
- Honour `style.forbidden_tics`. Honour the tension curve: this scene runs from
  {scene.get('tension_in')} to {scene.get('tension_out')}.
- Do not summarize, foreshadow beyond what the scene definition opens, or
  resolve a question the definition does not close.

Return the scene text only — no commentary, no markdown headers, no fences.
"""


def repair_prompt(stage: str, doc: dict, findings: list[str]) -> str:
    return f"""\
REPAIR — layer `{stage}`

The document below failed deterministic validation. Fix it.

DOCUMENT
{_json(doc)}

VIOLATIONS
{chr(10).join('- ' + f for f in findings)}

WHAT TO PRODUCE

A `diagnosis` naming the real cause of each violation, and a `patch`: a list of
RFC 6902 operations that will be applied mechanically to the document above and
then re-validated.

Fix causes, not symptoms. If a state continuity error says a value folded to
something other than what was declared, decide which of the two is right for
the story and correct that one — do not paper over it by loosening a
declaration somewhere else. If a spine step is undischarged, the honest fix is
usually a missing event, not a deleted step.

Paths are JSON Pointers into the document exactly as shown. Remember that array
indices shift as you edit: emit ops against the ORIGINAL document, in an order
where that holds.

{_schema_block("repair")}
"""


# --------------------------------------------------------------------------

BUILDERS = {
    "story_root": story_root_prompt,
    "expose": expose_prompt,
    "plots": plots_prompt,
    "entities": entities_prompt,
    "events": events_prompt,
    "scenes": scenes_prompt,
    "prose": prose_prompt,
    "repair": repair_prompt,
}
