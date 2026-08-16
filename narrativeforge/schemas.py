"""JSON Schemas for the seven generative layers.

These serve three masters at once:

1. They are handed to the Hyprlab/Grok backend as ``response_format.json_schema``
   so the API constrains decoding.
2. They are pasted into the prompt for the agent backend, which has no
   constrained decoding and must be told the shape in words.
3. They are checked locally by ``jsonschema_mini`` for *both* backends, so the
   two paths are held to a byte-identical standard.

Layer map (inverse of the whitepaper's analysis pipeline)
--------------------------------------------------------
    L0/L1  story_root  genre, audience, style, narrative vector   (the "story root")
    L2     expose      jacket copy + sentence-addressable synopsis
    L4     plots       cause-and-effect chains, declared spine steps
    L3     entities    dossiers == the world state at t0, patchable
    L5     events      causal DAG, declares which state must change
    L6     scenes      beats, each carrying the RFC 6902 ops that realize it
    T6     prose       the leaves of the graph

Note the deliberate 4-before-3: in the *analysis* direction the whitepaper
extracts entities before plots (you cannot record a delta against an undeclared
variable). In the *generation* direction the plots come first, because a cast
invented before its plots is a cast of people with nothing to do. Entities are
then written to serve the plots, and it is the entity layer that declares the
state variables the later layers are permitted to touch.
"""

from __future__ import annotations

from .plotembedding import PLOT_EMBEDDING_SCHEMA

# --------------------------------------------------------------------------
# Closed vocabularies
# --------------------------------------------------------------------------

STATE_DIMENSIONS = [
    "physiological", "emotional", "epistemic", "psychological", "social",
    "material", "spatial", "legal", "reputational", "world",
    # domain extensions, enabled per genre
    "magical", "technological", "political",
]

PLOT_TYPES = [
    "external_main", "relationship", "growth_internal", "antagonist",
    "investigation", "intrigue", "survival", "institutional", "epochal",
    "thematic", "rivalry", "mentor", "descent_tragic", "frame_recursive",
]

PLOT_OUTCOMES = ["success", "partial_success", "failure", "transformation_of_goal"]

ENTITY_TYPES = ["character", "creature", "location", "object", "group", "concept"]

BEAT_TYPES = [
    "action", "reaction", "dialogue", "discovery", "decision", "revelation",
    "reversal", "conflict", "transition", "reflection",
]

NARRATIVE_MODES = ["scene", "summary", "reflection", "frame"]

SALIENCE = ["major", "supporting", "minor", "mentioned"]

# The narrative vector (L1). Modal dimensions are bipolar: 0 == first pole,
# 100 == second pole. All others are intensities.
NARRATIVE_VECTOR_GROUPS: dict[str, list[str]] = {
    "affective": [
        "suspense", "dread", "melancholy", "warmth", "comedy", "awe",
        "disgust", "catharsis",
    ],
    "modal": [
        "realism_to_fantastication", "interiority_to_exteriority",
        "plot_to_character_driven", "dialogue_to_description",
        "linearity", "ambiguity_of_resolution",
    ],
    "generic": [
        "thriller", "romance", "mystery", "coming_of_age", "tragedy", "satire",
        "adventure", "horror", "procedural", "war", "domestic_drama",
    ],
    "thematic": [
        "moral_clarity", "institutional_critique", "faith_transcendence",
        "class", "gender", "technology",
    ],
}


# --------------------------------------------------------------------------
# Schema helpers
# --------------------------------------------------------------------------

def _obj(props: dict, *, required: list[str] | None = None, extra=False, desc: str | None = None) -> dict:
    schema: dict = {
        "type": "object",
        "properties": props,
        "required": required if required is not None else list(props),
        "additionalProperties": extra,
    }
    if desc:
        schema["description"] = desc
    return schema


def _map(value_schema: dict, *, desc: str | None = None, pattern: str | None = None) -> dict:
    """An id-keyed object. The patchable stand-in for an array."""
    schema: dict = {"type": "object", "additionalProperties": value_schema}
    if desc:
        schema["description"] = desc
    if pattern:
        schema["propertyNames"] = {"pattern": pattern}
    return schema


def _arr(item_schema: dict, *, desc: str | None = None, min_items: int | None = None) -> dict:
    schema: dict = {"type": "array", "items": item_schema}
    if desc:
        schema["description"] = desc
    if min_items is not None:
        schema["minItems"] = min_items
    return schema


_STR = {"type": "string"}
_INT = {"type": "integer"}
_NUM = {"type": "number"}
_BOOL = {"type": "boolean"}
_ANY = {}
_SCORE = {"type": "integer", "minimum": 0, "maximum": 100}
_ID_LIST = _arr(_STR)


# --------------------------------------------------------------------------
# L0 + L1 — Story Root
# --------------------------------------------------------------------------

_VECTOR_ENTRY = _obj({
    "score": _SCORE,
    "intent": {"type": "string", "description": "<=25 words: what this level is FOR in this story"},
})

STORY_ROOT_SCHEMA = _obj({
    "story_id": _STR,
    "title": _STR,
    "form": {"enum": ["novel", "novella", "short_story", "screenplay", "teleplay"]},
    "language": _STR,
    "logline": {"type": "string", "description": "one sentence, max 40 words, no spoilers"},
    "premise": {"type": "string", "description": "3-5 sentences: the story in the abstract"},
    "genre_primary": _STR,
    "genre_secondary": _ID_LIST,
    "audience": _obj({
        "age_band": {"enum": ["children", "middle_grade", "young_adult", "adult"]},
        "reading_level": {"enum": ["simple", "middle", "upper", "literary"]},
        "content_flags": _ID_LIST,
        "reader_promise": {"type": "string", "description": "what the reader is owed by the last page"},
    }),
    "setting": _obj({
        "period": _STR,
        "places": _ID_LIST,
        "world_type": {"enum": ["realist", "historical", "low_fantasy", "high_fantasy",
                                "science_fiction", "magical_realist", "speculative"]},
        "rules_of_the_world": _arr(_STR, desc="hard constraints the story may not violate"),
    }),
    "pov": _obj({
        "person": {"enum": ["first", "third_limited", "third_omniscient", "second"]},
        "narrators": _INT,
        "tense": {"enum": ["past", "present"]},
    }),
    "style": _obj({
        "register": {"enum": ["plain", "elevated", "vernacular", "lyrical", "clinical", "wry"]},
        "sentence_length": {"enum": ["short", "medium", "long", "varied"]},
        "dialogue_ratio": {"type": "number", "minimum": 0, "maximum": 1},
        "figurative_density": {"enum": ["low", "medium", "high"]},
        "chronology": {"enum": ["linear", "non_linear", "framed"]},
        "prose_touchstones": _arr(_STR, desc="named comparables for voice, not for plot"),
        "forbidden_tics": _arr(_STR, desc="prose habits the prose layer must avoid"),
    }),
    "plot_embedding": PLOT_EMBEDDING_SCHEMA,
    "state_dimensions": _arr(
        {"enum": STATE_DIMENSIONS},
        desc="the closed vocabulary this work's state changes may use",
    ),
    "constraints": _obj({
        "target_word_count": _INT,
        "plot_count": _INT,
        "scene_count_target": _INT,
        "event_count_target": _INT,
        "must_include": _ID_LIST,
        "must_avoid": _ID_LIST,
    }),
    "keep_in_mind": _arr(_STR, desc="standing notes every later layer must respect"),
}, extra=True)

# Runs produced before the plot embedding landed carry `narrative_vector`
# instead. Both are accepted; `plot_embedding` is what new work must produce.
LEGACY_NARRATIVE_VECTOR_SCHEMA = _obj({
    group: _obj({dim: _VECTOR_ENTRY for dim in dims})
    for group, dims in NARRATIVE_VECTOR_GROUPS.items()
})


# --------------------------------------------------------------------------
# L2 — Exposé
# --------------------------------------------------------------------------

SYNOPSIS_FUNCTIONS = [
    "initial_situation", "disturbance", "goal", "stakes", "obstacle",
    "turn", "climax", "resolution", "cost", "subplot", "theme",
]

EXPOSE_SCHEMA = _obj({
    "ending_first": _obj({
        "ending": {"type": "string", "description": "decided BEFORE the opening sentence is written"},
        "cost": {"type": "string", "description": "what the resolution costs, concretely"},
        "final_image": _STR,
    }, desc="§3.3: determine the ending first, which is what prevents 'and then, and then'"),
    "jacket_copy": {"type": "string", "description": "120-150 words, in the register of the work, withholds the ending"},
    "plot_summary_short": {
        "type": "string",
        "description": (
            "150-250 words. A plain, chronological account of what happens, written for "
            "someone who has never encountered this story and wants to know what it is "
            "about — the way an encyclopedia summarises a plot, not the way a jacket sells "
            "one. Neutral third person, present tense, no rhetorical questions, no teasing, "
            "no withheld ending. Name the characters and say plainly what they do and what "
            "results. If a reader finishes this and still does not know how it ends, it has "
            "failed."
        ),
    },
    "plot_summary_long": {
        "type": "string",
        "description": (
            "700-1200 words. The same register as plot_summary_short, at the length of a "
            "full encyclopedia plot section. Chronological, complete, spoilers included. "
            "Cover every plot and the fate of every significant character. Use paragraph "
            "breaks by movement or act. Explain the world's rules the first time they "
            "matter, in passing, without stopping to lecture. This is the artifact a person "
            "reads to understand the whole story without reading the story."
        ),
    },
    "synopsis": _map(
        _obj({
            "text": {"type": "string", "description": "ONE sentence"},
            "function": {"enum": SYNOPSIS_FUNCTIONS},
            "story_time_rank": {"type": "integer", "description": "order in STORY time, not discourse time"},
        }),
        desc="450-550 words total, split one sentence per key: s01, s02, ... Every later "
             "layer cites these keys, which is what makes synopsis claims traceable.",
        pattern="^s[0-9]{2,3}$",
    ),
    "synopsis_word_count": _INT,
}, desc="L2. The full-spoiler condensation is the important half; the jacket copy is the marketing artifact.")


# --------------------------------------------------------------------------
# L4 — Plot decomposition
# --------------------------------------------------------------------------

PLOT_SCHEMA = _obj({
    "plot_id": {"type": "string", "description": "pl-01, pl-02, ..."},
    "type": {"enum": PLOT_TYPES},
    "title": _STR,
    "agent": _arr(_STR, desc="entity ids that pursue the goal (forward-declared; L3 must define them)"),
    "resistance": _arr(_STR, desc="entity ids and/or plot ids that supply resistance"),
    "goal": {"type": "string", "description": "a concrete outcome pursued, not a theme or a mood"},
    "stakes": {"type": "string", "description": "what is lost if the goal is not reached"},
    "outcome": {"enum": PLOT_OUTCOMES},
    "spine": _map(
        _obj({
            "step": _INT,
            "function": {"type": "string", "description": "e.g. state_of_rupture, forced_proximity, point_of_no_return"},
            "intent": {"type": "string", "description": "what must happen at this step, 1-2 sentences"},
            "because": _arr(_STR, desc="cross-plot causes, formatted 'pl-01:st3'; empty for the first step"),
        }),
        desc="ordered by .step; keys st1, st2, ... Events bind to these steps later.",
        pattern="^st[0-9]{1,2}$",
    ),
    "resolution_step": {"type": "string", "description": "the spine key at which this plot terminates"},
    "thematic_function": _STR,
    "screen_time_share": {"type": "number", "minimum": 0, "maximum": 1},
    "interference": _arr(_obj({
        "with": _STR,
        "kind": _STR,
    }), desc="how this plot competes with another for the agent, the clock, or the reader"),
    "covers_synopsis": _arr(_STR, desc="synopsis sentence keys this plot is responsible for"),
})

PLOTS_SCHEMA = _obj({
    "plots": _arr(PLOT_SCHEMA, min_items=1),
}, desc="L4. Nothing floats: a candidate without goal + resistance + outcome is a motif, not a plot.")


# --------------------------------------------------------------------------
# L3 — Entity dossiers  ==  the world state at t0
# --------------------------------------------------------------------------

SENTENCE_MAP = _map(
    _obj({
        "text": {"type": "string", "description": "ONE sentence"},
        "when": {"type": "string", "description": "when in the entity's history, or 'standing'"},
        "tags": _ID_LIST,
    }, required=["text"], extra=True),
    desc="Freeform prose decomposed one sentence per key (b01, b02, ...) so that any "
         "single sentence is addressable by JSON Pointer and can be patched later.",
)

STATE_VARIABLE_SCHEMA = _obj({
    "kind": {"enum": ["scalar", "enum", "text", "bool"]},
    "description": _STR,
    "dimension": {"enum": STATE_DIMENSIONS},
    "range": _arr(_NUM, desc="[min, max] for scalar; omit otherwise"),
    "domain": _arr(_STR, desc="permitted values for enum; omit otherwise"),
    "init": _ANY,
}, required=["kind", "description", "dimension", "init"], extra=True)

ENTITY_SCHEMA = _obj({
    "entity_id": {"type": "string", "description": "ch-01 character/creature, lo-01 location, ob-01 object, gr-01 group, cn-01 concept"},
    "type": {"enum": ENTITY_TYPES},
    "canonical_name": _STR,
    "aliases": _ID_LIST,
    "salience": {"enum": SALIENCE},
    "plots": _arr(_STR, desc="plot ids this entity serves"),
    "profile": {
        "type": "object",
        "description": (
            "Nested, freely structured dossier. Type-specific: characters/creatures carry "
            "demographics, appearance, voice_and_speech, habits_and_tells, backstory, wound, "
            "want, need, values, fears, competences, limitations, problem_solving_style, "
            "coping_strategies, health, moral_axis. Locations carry geography, atmosphere, "
            "control, access, significance. Objects carry provenance, description, function, "
            "symbolic_load, custody. Groups carry membership, hierarchy, goals, resources, "
            "cohesion. Concepts carry content, believers, authority, causal_power. "
            "HARD RULE: every prose block is a sentence map (see backstory); no string inside "
            "profile may exceed 180 characters; no arrays of objects."
        ),
        "properties": {
            "backstory": SENTENCE_MAP,
            "speech_signature": _obj({
                "sentence_shape": _STR,
                "vocabulary_domain": {"type": "string", "description":
                    "What they reach for metaphors from — the trade, the body, money, scripture."},
                "verbal_tic": _STR,
                "never_says": {"type": "string", "description":
                    "A word, register or move this person will not use, even under pressure."},
                "under_stress": {"type": "string", "description":
                    "How the voice changes when they are cornered — shorter, more formal, cruder, silent."},
            }, desc="How to tell this person apart with the attributions removed. Two "
                    "characters whose lines could be swapped without anyone noticing are "
                    "one character wearing two names.", extra=True),
        },
        # speech_signature is required of characters and creatures only, which a
        # shared schema cannot express — validate.py enforces it by type.
        "required": ["backstory"],
        "additionalProperties": True,
    },
    "relationships": _map(
        _obj({
            "kind": _STR,
            "valence": {"type": "integer", "minimum": -100, "maximum": 100},
            "notes": SENTENCE_MAP,
        }, required=["kind", "valence"], extra=True),
        desc="keyed by the OTHER entity's id",
    ),
    "state_variables": _map(
        STATE_VARIABLE_SCHEMA,
        desc="the ONLY variables later layers may modify for this entity; snake_case keys",
    ),
    "state": {
        "type": "object",
        "description": "live values at t0; keys must match state_variables exactly, values must equal their .init",
        "additionalProperties": True,
    },
    "arc": _obj({
        "start_state": _STR,
        "end_state": _STR,
    }),
}, required=["entity_id", "type", "canonical_name", "aliases", "salience", "plots",
             "profile", "relationships", "state_variables", "state", "arc"], extra=True)

ENTITIES_SCHEMA = _obj({
    "entities": _map(ENTITY_SCHEMA, desc="keyed by entity_id; this object IS the world state at t0"),
}, desc="L3. Events are defined as state changes OF entities, so nothing may be modified "
        "later that is not declared here.")


# --------------------------------------------------------------------------
# L5 — Event chain
# --------------------------------------------------------------------------

EVENT_STATE_CHANGE_SCHEMA = _obj({
    "entity": _STR,
    "variable": {"type": "string", "description": "a key of that entity's state_variables"},
    "path": {"type": "string", "description": "JSON Pointer into the world state, e.g. /ch-01/state/oath_intact"},
    "dimension": {"enum": STATE_DIMENSIONS},
    "before": _ANY,
    "after": _ANY,
    "magnitude": {"enum": [10, 25, 50, 75, 100], "description":
        "How much this change matters, on five anchored steps — NOT a free scale. "
        "10 a flicker that leaves no mark · 25 a real but recoverable shift · "
        "50 something that changes how they act from here · 75 a reordering of what "
        "they want · 100 irreversible. A number between these steps is false precision: "
        "nobody can tell 55 from 60, and pretending otherwise makes the corpus noisier, "
        "not richer."},
}, required=["entity", "variable", "path", "dimension", "before", "after", "magnitude"])

EVENT_SCHEMA = _obj({
    "event_id": {"type": "string", "description": "ev-001, ev-002, ..."},
    "story_time": _obj({
        "index": {"type": "integer", "description": "unique, ascending in STORY time"},
        "label": {"type": "string", "description": "e.g. 'day 3, dusk'"},
        "duration_min": _INT,
    }),
    "primary_plot": {"type": "string", "description": "EXACTLY one parent plot"},
    "plots": _arr(_STR, desc="all plots served; must contain primary_plot", min_items=1),
    "plot_bindings": _arr(_obj({
        "plot": _STR,
        "step": {"type": "string", "description": "a spine key of that plot, e.g. st3"},
    }), desc="which spine steps this event discharges"),
    "location": {"type": "string", "description": "a location entity id"},
    "participants": _arr(_STR, min_items=1),
    "summary": {"type": "string", "description": "<=30 words"},
    "action": {"type": "string", "description": "third person, NO direct speech, 60-160 words"},
    "state_changes": _arr(EVENT_STATE_CHANGE_SCHEMA, min_items=1,
                          desc="DECLARATIONS. The scene layer must realize each of these with a patch op."),
    "caused_by": _arr(_STR, desc="event ids; empty only for designated roots"),
    "causes": _arr(_STR, desc="event ids; empty only for designated sinks"),
    "causal_note": _STR,
    "reversal": _BOOL,
    "plot_function": _STR,
    "is_root": _BOOL,
    "is_sink": _BOOL,
}, required=["event_id", "story_time", "primary_plot", "plots", "plot_bindings", "location",
             "participants", "summary", "action", "state_changes", "caused_by", "causes",
             "causal_note", "reversal", "plot_function", "is_root", "is_sink"])

EVENTS_SCHEMA = _obj({
    "events": _map(EVENT_SCHEMA, desc="keyed by event_id", pattern="^ev-[0-9]{3}$"),
}, desc="L5. A directed acyclic graph over story time. Events and scenes are NOT identified "
        "with one another: one event may span several scenes, one scene may contain several events.")


# --------------------------------------------------------------------------
# L6 — Scene definitions (beats + the actual patches)
# --------------------------------------------------------------------------

PATCH_OP_SCHEMA = _obj({
    "op": {"enum": ["add", "remove", "replace", "move", "copy", "test"]},
    "path": {"type": "string", "description": "RFC 6901 pointer into the world state"},
    "value": _ANY,
    "from": _STR,
}, required=["op", "path"], extra=False)

BEAT_CHANGE_SCHEMA = _obj({
    "entity": _STR,
    "variable": _STR,
    "dimension": {"enum": STATE_DIMENSIONS},
    "before": _ANY,
    "after": _ANY,
    "magnitude": {"enum": [10, 25, 50, 75, 100], "description":
        "How much this change matters, on five anchored steps — NOT a free scale. "
        "10 a flicker that leaves no mark · 25 a real but recoverable shift · "
        "50 something that changes how they act from here · 75 a reordering of what "
        "they want · 100 irreversible. A number between these steps is false precision: "
        "nobody can tell 55 from 60, and pretending otherwise makes the corpus noisier, "
        "not richer."},
    "op": PATCH_OP_SCHEMA,
}, required=["entity", "variable", "dimension", "before", "after", "magnitude", "op"])

BEAT_SCHEMA = _obj({
    "beat": {"type": "integer", "description": "1-based, ordered within the scene"},
    "event_id": {"type": "string", "description": "the ONE event this beat belongs to"},
    "type": {"enum": BEAT_TYPES},
    "text": {"type": "string", "description": "flat third person, 25-70 words, NO direct speech. "
                                              "Render dialogue as reported semantics and illocutionary force."},
    "participants": _arr(_STR, min_items=1),
    "changes": _arr(BEAT_CHANGE_SCHEMA,
                    desc="the RFC 6902 ops that actually mutate the world state; may be empty for "
                         "setup beats, but every scene must contain at least one non-empty changes list"),
}, required=["beat", "event_id", "type", "text", "participants", "changes"])

SCENE_SCHEMA = _obj({
    "scene_id": {"type": "string", "description": "sc-001, sc-002, ..."},
    "discourse_index": {"type": "integer", "description": "order the reader meets it; unique, ascending"},
    "chapter": _INT,
    "primary_event": {"type": "string", "description": "EXACTLY one parent event"},
    "events": _arr(_STR, desc="all events realized here; must contain primary_event", min_items=1),
    "primary_plot": {"type": "string", "description": "EXACTLY one parent plot; must equal the primary_event's primary_plot"},
    "plots": _arr(_STR, min_items=1),
    "story_time_label": _STR,
    "location": _STR,
    "pov": {"type": "string", "description": "entity id of the viewpoint character"},
    "narrative_mode": {"enum": NARRATIVE_MODES},
    "present": _arr(_STR, min_items=1),
    "offstage_referenced": _ID_LIST,
    "entry_states": _map(_map(_ANY), desc="{entity_id: {variable: value}} — MUST equal the folded "
                                          "world state on arrival; the validator checks this"),
    "beats": _arr(BEAT_SCHEMA, min_items=1),
    "exit_states": _map(_map(_ANY), desc="{entity_id: {variable: value}} after the last beat"),
    "dramatic_function": _STR,
    "tension_in": _SCORE,
    "tension_out": _SCORE,
    "questions_opened": _map(_STR, desc="q01, q02, ..."),
    "questions_closed": _arr(_STR, desc="question keys opened by earlier scenes"),
    "target_words": {"type": "integer", "description": "prose budget for this scene"},
    "continuity_facts": _map(_obj({
        "present": _BOOL,
        "conscious": {"enum": ["awake", "asleep", "unconscious", "absent"]},
        "position": {"type": "string", "description": "where in the location, plainly"},
        "holding": _ID_LIST,
        "condition": {"type": "string", "description": "visible physical condition"},
    }, required=["present", "conscious"], extra=True),
        desc="Plain physical facts at the END of this scene, keyed by entity id. Not "
             "atmosphere and not interpretation — the things a continuity supervisor "
             "writes down. Declared state variables cover what a story tracks on purpose; "
             "this covers what it must not contradict by accident, which is where "
             "continuity actually breaks."),
    "someone_behaves_badly": _obj({
        "who": _STR,
        "what": {"type": "string", "description":
            "An interruption, an unfair move, a cheap shot, something said that cannot be "
            "taken back, a refusal to give someone their moment."},
    }, required=[], extra=True,
       desc="Optional per scene, but a work in which nobody ever behaves badly is a work "
            "with an ethics and no theatre. If this scene is one of the polite ones, leave "
            "it empty — but the validator counts how many scenes are."),
}, required=["scene_id", "discourse_index", "chapter", "primary_event", "events", "primary_plot",
             "plots", "story_time_label", "location", "pov", "narrative_mode", "present",
             "offstage_referenced", "entry_states", "beats", "exit_states", "dramatic_function",
             "tension_in", "tension_out", "questions_opened", "questions_closed",
             "target_words", "continuity_facts"])

SCENES_SCHEMA = _obj({
    "scenes": _map(SCENE_SCHEMA, desc="keyed by scene_id", pattern="^sc-[0-9]{3}$"),
}, desc="L6. The preimage of the prose: no style, no atmosphere, no direct speech.")


# --------------------------------------------------------------------------
# Repair envelope (used by the reconcile stage)
# --------------------------------------------------------------------------

REPAIR_SCHEMA = _obj({
    "diagnosis": _arr(_obj({
        "violation": _STR,
        "cause": _STR,
        "fix": _STR,
    })),
    "patch": _arr(PATCH_OP_SCHEMA, desc="RFC 6902 ops applied to the named artifact document"),
}, desc="Returned by the reconcile stage. Applied mechanically, then re-validated.")


SCHEMAS: dict[str, dict] = {
    "story_root": STORY_ROOT_SCHEMA,
    "expose": EXPOSE_SCHEMA,
    "plots": PLOTS_SCHEMA,
    "entities": ENTITIES_SCHEMA,
    "events": EVENTS_SCHEMA,
    "scenes": SCENES_SCHEMA,
    "repair": REPAIR_SCHEMA,
}
