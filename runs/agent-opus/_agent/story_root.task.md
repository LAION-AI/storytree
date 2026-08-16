# Task packet — `story_root`

You are executing one stage of a structured narrative generation pipeline.
Follow the instructions below exactly. They are the same instructions the API
backend receives; you are the executor, not the author of the process.

**When you are done, write your output to this exact path and nothing else:**

```
/home/deployer/laion/bookwriter/runs/agent-opus/_agent/story_root.out.json
```

The file must contain **one JSON document and nothing else** — no markdown
fence, no preamble, no trailing prose. It will be parsed mechanically and
validated against the schema below; a wrapper of any kind will fail the parse.
Write it with the Write tool in a single call.


Do not write any other file. Do not print the result to the transcript. Do not
ask for confirmation. Do not add commentary to the output file.

---

## System instructions

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


---

## Stage instructions

STAGE 1 of 7 — STORY ROOT (layers L0 + L1)

Everything downstream is derived from this document, so it is the one place
where taste is expressed as parameters rather than as prose. Be decisive: a
root that hedges produces a story that hedges.

THE BRIEF
# Brief — a short fantasy test piece

A deliberately ordinary secondary-world fantasy, chosen so that the *machinery*
is what gets tested rather than the ingenuity of the premise. Both backends
receive this identical brief.

## Premise

A blacksmith's apprentice in a mountain village is sent to recover a relic
stolen by raiders before the midwinter rite, at which the relic must be
presented or the village forfeits the protection it has paid for in iron for
three generations.

She succeeds in recovering it. What she also discovers is that the relic is a
forgery, and that the person who forged it is the master who raised her — who
did it forty years ago, for reasons that were good at the time and are not
defensible now.

## What must be true

- Low fantasy. Magic exists, is expensive, and is not a solution to anything.
  Whatever the relic does, it does at a price somebody pays.
- The village is poor and the arrangement it lives under is exploitative. Do
  not make the raiders the only antagonist.
- The apprentice is competent at her craft and bad at deciding what she owes
  people. That is the tension.
- Two plots and no more:
  1. an **external / main** plot — recover the relic before the rite;
  2. a **relationship** plot — the apprentice and the master, and what the
     forgery does to it.
  The two must genuinely constrain each other: pursuing one must cost the
  other. At least one cross-plot `because` link is required in each direction
  if the structure supports it.
- The ending is not a triumph and not a tragedy. Someone chooses, and pays.

## Register

Plain, concrete, workmanlike prose. Forge detail, weather, weight of things.
No prophecies, no chosen ones, no ancient evil awakening. Third person limited,
past tense, one narrator.

REQUESTED SHAPE
{
 "form": "short_story",
 "language": "en",
 "target_word_count": 7000,
 "plot_count": 2,
 "scene_count_target": 8,
 "event_count_target": 14,
 "entity_count_guidance": "6-10 entities: 3-4 characters, 2-3 locations, 1-2 objects, 1 group or concept",
 "beats_per_scene": "3-6",
 "note": "A small test run. Prefer a tight, fully-discharged structure over scale."
}

WHAT TO PRODUCE

- Bibliographic and editorial identity: genre, audience, setting, point of
  view, style. `style.forbidden_tics` is your instruction to your future self
  at the prose stage — name the habits this particular story must not fall
  into.
- `setting.rules_of_the_world`: hard constraints no later layer may violate.
  For a fantasy, this is where magic gets a cost and a limit. Rules that cannot
  be violated are what make later events feel earned rather than convenient.
- The narrative vector: score every one of these dimensions 0-100 and give each
  a justification of at most 25 words saying what that level is FOR:
  affective: suspense, dread, melancholy, warmth, comedy, awe, disgust, catharsis
  modal: realism_to_fantastication, interiority_to_exteriority, plot_to_character_driven, dialogue_to_description, linearity, ambiguity_of_resolution
  generic: thriller, romance, mystery, coming_of_age, tragedy, satire, adventure, horror, procedural, war, domestic_drama
  thematic: moral_clarity, institutional_critique, faith_transcendence, class, gender, technology
  Modal dimensions are bipolar — 0 means the first pole named, 100 the second.
  A score without a reason is noise; the vector is a control surface, and every
  later layer will be steered by it.
- `state_dimensions`: choose the subset of the closed vocabulary this work
  actually needs, from ['physiological', 'emotional', 'epistemic', 'psychological', 'social', 'material', 'spatial', 'legal', 'reputational', 'world', 'magical', 'technological', 'political']. Every state change in the story will
  be typed with one of them. Enable domain extensions only if the genre uses
  them.
- `constraints`: honour the requested shape exactly. plot_count in particular
  is a hard number, not a suggestion.
- `keep_in_mind`: standing notes every later layer must respect — tonal
  guardrails, a motif to plant, a thing the ending depends on.

SCHEMA (your output must validate against this):
{
 "type": "object",
 "properties": {
  "story_id": {
   "type": "string"
  },
  "title": {
   "type": "string"
  },
  "form": {
   "enum": [
    "novel",
    "novella",
    "short_story",
    "screenplay",
    "teleplay"
   ]
  },
  "language": {
   "type": "string"
  },
  "logline": {
   "type": "string",
   "description": "one sentence, max 40 words, no spoilers"
  },
  "premise": {
   "type": "string",
   "description": "3-5 sentences: the story in the abstract"
  },
  "genre_primary": {
   "type": "string"
  },
  "genre_secondary": {
   "type": "array",
   "items": {
    "type": "string"
   }
  },
  "audience": {
   "type": "object",
   "properties": {
    "age_band": {
     "enum": [
      "children",
      "middle_grade",
      "young_adult",
      "adult"
     ]
    },
    "reading_level": {
     "enum": [
      "simple",
      "middle",
      "upper",
      "literary"
     ]
    },
    "content_flags": {
     "type": "array",
     "items": {
      "type": "string"
     }
    },
    "reader_promise": {
     "type": "string",
     "description": "what the reader is owed by the last page"
    }
   },
   "required": [
    "age_band",
    "reading_level",
    "content_flags",
    "reader_promise"
   ],
   "additionalProperties": false
  },
  "setting": {
   "type": "object",
   "properties": {
    "period": {
     "type": "string"
    },
    "places": {
     "type": "array",
     "items": {
      "type": "string"
     }
    },
    "world_type": {
     "enum": [
      "realist",
      "historical",
      "low_fantasy",
      "high_fantasy",
      "science_fiction",
      "magical_realist",
      "speculative"
     ]
    },
    "rules_of_the_world": {
     "type": "array",
     "items": {
      "type": "string"
     },
     "description": "hard constraints the story may not violate"
    }
   },
   "required": [
    "period",
    "places",
    "world_type",
    "rules_of_the_world"
   ],
   "additionalProperties": false
  },
  "pov": {
   "type": "object",
   "properties": {
    "person": {
     "enum": [
      "first",
      "third_limited",
      "third_omniscient",
      "second"
     ]
    },
    "narrators": {
     "type": "integer"
    },
    "tense": {
     "enum": [
      "past",
      "present"
     ]
    }
   },
   "required": [
    "person",
    "narrators",
    "tense"
   ],
   "additionalProperties": false
  },
  "style": {
   "type": "object",
   "properties": {
    "register": {
     "enum": [
      "plain",
      "elevated",
      "vernacular",
      "lyrical",
      "clinical",
      "wry"
     ]
    },
    "sentence_length": {
     "enum": [
      "short",
      "medium",
      "long",
      "varied"
     ]
    },
    "dialogue_ratio": {
     "type": "number",
     "minimum": 0,
     "maximum": 1
    },
    "figurative_density": {
     "enum": [
      "low",
      "medium",
      "high"
     ]
    },
    "chronology": {
     "enum": [
      "linear",
      "non_linear",
      "framed"
     ]
    },
    "prose_touchstones": {
     "type": "array",
     "items": {
      "type": "string"
     },
     "description": "named comparables for voice, not for plot"
    },
    "forbidden_tics": {
     "type": "array",
     "items": {
      "type": "string"
     },
     "description": "prose habits the prose layer must avoid"
    }
   },
   "required": [
    "register",
    "sentence_length",
    "dialogue_ratio",
    "figurative_density",
    "chronology",
    "prose_touchstones",
    "forbidden_tics"
   ],
   "additionalProperties": false
  },
  "narrative_vector": {
   "type": "object",
   "properties": {
    "affective": {
     "type": "object",
     "properties": {
      "suspense": {
       "type": "object",
       "properties": {
        "score": {
         "type": "integer",
         "minimum": 0,
         "maximum": 100
        },
        "intent": {
         "type": "string",
         "description": "<=25 words: what this level is FOR in this story"
        }
       },
       "required": [
        "score",
        "intent"
       ],
       "additionalProperties": false
      },
      "dread": {
       "type": "object",
       "properties": {
        "score": {
         "type": "integer",
         "minimum": 0,
         "maximum": 100
        },
        "intent": {
         "type": "string",
         "description": "<=25 words: what this level is FOR in this story"
        }
       },
       "required": [
        "score",
        "intent"
       ],
       "additionalProperties": false
      },
      "melancholy": {
       "type": "object",
       "properties": {
        "score": {
         "type": "integer",
         "minimum": 0,
         "maximum": 100
        },
        "intent": {
         "type": "string",
         "description": "<=25 words: what this level is FOR in this story"
        }
       },
       "required": [
        "score",
        "intent"
       ],
       "additionalProperties": false
      },
      "warmth": {
       "type": "object",
       "properties": {
        "score": {
         "type": "integer",
         "minimum": 0,
         "maximum": 100
        },
        "intent": {
         "type": "string",
         "description": "<=25 words: what this level is FOR in this story"
        }
       },
       "required": [
        "score",
        "intent"
       ],
       "additionalProperties": false
      },
      "comedy": {
       "type": "object",
       "properties": {
        "score": {
         "type": "integer",
         "minimum": 0,
         "maximum": 100
        },
        "intent": {
         "type": "string",
         "description": "<=25 words: what this level is FOR in this story"
        }
       },
       "required": [
        "score",
        "intent"
       ],
       "additionalProperties": false
      },
      "awe": {
       "type": "object",
       "properties": {
        "score": {
         "type": "integer",
         "minimum": 0,
         "maximum": 100
        },
        "intent": {
         "type": "string",
         "description": "<=25 words: what this level is FOR in this story"
        }
       },
       "required": [
        "score",
        "intent"
       ],
       "additionalProperties": false
      },
      "disgust": {
       "type": "object",
       "properties": {
        "score": {
         "type": "integer",
         "minimum": 0,
         "maximum": 100
        },
        "intent": {
         "type": "string",
         "description": "<=25 words: what this level is FOR in this story"
        }
       },
       "required": [
        "score",
        "intent"
       ],
       "additionalProperties": false
      },
      "catharsis": {
       "type": "object",
       "properties": {
        "score": {
         "type": "integer",
         "minimum": 0,
         "maximum": 100
        },
        "intent": {
         "type": "string",
         "description": "<=25 words: what this level is FOR in this story"
        }
       },
       "required": [
        "score",
        "intent"
       ],
       "additionalProperties": false
      }
     },
     "required": [
      "suspense",
      "dread",
      "melancholy",
      "warmth",
      "comedy",
      "awe",
      "disgust",
      "catharsis"
     ],
     "additionalProperties": false
    },
    "modal": {
     "type": "object",
     "properties": {
      "realism_to_fantastication": {
       "type": "object",
       "properties": {
        "score": {
         "type": "integer",
         "minimum": 0,
         "maximum": 100
        },
        "intent": {
         "type": "string",
         "description": "<=25 words: what this level is FOR in this story"
        }
       },
       "required": [
        "score",
        "intent"
       ],
       "additionalProperties": false
      },
      "interiority_to_exteriority": {
       "type": "object",
       "properties": {
        "score": {
         "type": "integer",
         "minimum": 0,
         "maximum": 100
        },
        "intent": {
         "type": "string",
         "description": "<=25 words: what this level is FOR in this story"
        }
       },
       "required": [
        "score",
        "intent"
       ],
       "additionalProperties": false
      },
      "plot_to_character_driven": {
       "type": "object",
       "properties": {
        "score": {
         "type": "integer",
         "minimum": 0,
         "maximum": 100
        },
        "intent": {
         "type": "string",
         "description": "<=25 words: what this level is FOR in this story"
        }
       },
       "required": [
        "score",
        "intent"
       ],
       "additionalProperties": false
      },
      "dialogue_to_description": {
       "type": "object",
       "properties": {
        "score": {
         "type": "integer",
         "minimum": 0,
         "maximum": 100
        },
        "intent": {
         "type": "string",
         "description": "<=25 words: what this level is FOR in this story"
        }
       },
       "required": [
        "score",
        "intent"
       ],
       "additionalProperties": false
      },
      "linearity": {
       "type": "object",
       "properties": {
        "score": {
         "type": "integer",
         "minimum": 0,
         "maximum": 100
        },
        "intent": {
         "type": "string",
         "description": "<=25 words: what this level is FOR in this story"
        }
       },
       "required": [
        "score",
        "intent"
       ],
       "additionalProperties": false
      },
      "ambiguity_of_resolution": {
       "type": "object",
       "properties": {
        "score": {
         "type": "integer",
         "minimum": 0,
         "maximum": 100
        },
        "intent": {
         "type": "string",
         "description": "<=25 words: what this level is FOR in this story"
        }
       },
       "required": [
        "score",
        "intent"
       ],
       "additionalProperties": false
      }
     },
     "required": [
      "realism_to_fantastication",
      "interiority_to_exteriority",
      "plot_to_character_driven",
      "dialogue_to_description",
      "linearity",
      "ambiguity_of_resolution"
     ],
     "additionalProperties": false
    },
    "generic": {
     "type": "object",
     "properties": {
      "thriller": {
       "type": "object",
       "properties": {
        "score": {
         "type": "integer",
         "minimum": 0,
         "maximum": 100
        },
        "intent": {
         "type": "string",
         "description": "<=25 words: what this level is FOR in this story"
        }
       },
       "required": [
        "score",
        "intent"
       ],
       "additionalProperties": false
      },
      "romance": {
       "type": "object",
       "properties": {
        "score": {
         "type": "integer",
         "minimum": 0,
         "maximum": 100
        },
        "intent": {
         "type": "string",
         "description": "<=25 words: what this level is FOR in this story"
        }
       },
       "required": [
        "score",
        "intent"
       ],
       "additionalProperties": false
      },
      "mystery": {
       "type": "object",
       "properties": {
        "score": {
         "type": "integer",
         "minimum": 0,
         "maximum": 100
        },
        "intent": {
         "type": "string",
         "description": "<=25 words: what this level is FOR in this story"
        }
       },
       "required": [
        "score",
        "intent"
       ],
       "additionalProperties": false
      },
      "coming_of_age": {
       "type": "object",
       "properties": {
        "score": {
         "type": "integer",
         "minimum": 0,
         "maximum": 100
        },
        "intent": {
         "type": "string",
         "description": "<=25 words: what this level is FOR in this story"
        }
       },
       "required": [
        "score",
        "intent"
       ],
       "additionalProperties": false
      },
      "tragedy": {
       "type": "object",
       "properties": {
        "score": {
         "type": "integer",
         "minimum": 0,
         "maximum": 100
        },
        "intent": {
         "type": "string",
         "description": "<=25 words: what this level is FOR in this story"
        }
       },
       "required": [
        "score",
        "intent"
       ],
       "additionalProperties": false
      },
      "satire": {
       "type": "object",
       "properties": {
        "score": {
         "type": "integer",
         "minimum": 0,
         "maximum": 100
        },
        "intent": {
         "type": "string",
         "description": "<=25 words: what this level is FOR in this story"
        }
       },
       "required": [
        "score",
        "intent"
       ],
       "additionalProperties": false
      },
      "adventure": {
       "type": "object",
       "properties": {
        "score": {
         "type": "integer",
         "minimum": 0,
         "maximum": 100
        },
        "intent": {
         "type": "string",
         "description": "<=25 words: what this level is FOR in this story"
        }
       },
       "required": [
        "score",
        "intent"
       ],
       "additionalProperties": false
      },
      "horror": {
       "type": "object",
       "properties": {
        "score": {
         "type": "integer",
         "minimum": 0,
         "maximum": 100
        },
        "intent": {
         "type": "string",
         "description": "<=25 words: what this level is FOR in this story"
        }
       },
       "required": [
        "score",
        "intent"
       ],
       "additionalProperties": false
      },
      "procedural": {
       "type": "object",
       "properties": {
        "score": {
         "type": "integer",
         "minimum": 0,
         "maximum": 100
        },
        "intent": {
         "type": "string",
         "description": "<=25 words: what this level is FOR in this story"
        }
       },
       "required": [
        "score",
        "intent"
       ],
       "additionalProperties": false
      },
      "war": {
       "type": "object",
       "properties": {
        "score": {
         "type": "integer",
         "minimum": 0,
         "maximum": 100
        },
        "intent": {
         "type": "string",
         "description": "<=25 words: what this level is FOR in this story"
        }
       },
       "required": [
        "score",
        "intent"
       ],
       "additionalProperties": false
      },
      "domestic_drama": {
       "type": "object",
       "properties": {
        "score": {
         "type": "integer",
         "minimum": 0,
         "maximum": 100
        },
        "intent": {
         "type": "string",
         "description": "<=25 words: what this level is FOR in this story"
        }
       },
       "required": [
        "score",
        "intent"
       ],
       "additionalProperties": false
      }
     },
     "required": [
      "thriller",
      "romance",
      "mystery",
      "coming_of_age",
      "tragedy",
      "satire",
      "adventure",
      "horror",
      "procedural",
      "war",
      "domestic_drama"
     ],
     "additionalProperties": false
    },
    "thematic": {
     "type": "object",
     "properties": {
      "moral_clarity": {
       "type": "object",
       "properties": {
        "score": {
         "type": "integer",
         "minimum": 0,
         "maximum": 100
        },
        "intent": {
         "type": "string",
         "description": "<=25 words: what this level is FOR in this story"
        }
       },
       "required": [
        "score",
        "intent"
       ],
       "additionalProperties": false
      },
      "institutional_critique": {
       "type": "object",
       "properties": {
        "score": {
         "type": "integer",
         "minimum": 0,
         "maximum": 100
        },
        "intent": {
         "type": "string",
         "description": "<=25 words: what this level is FOR in this story"
        }
       },
       "required": [
        "score",
        "intent"
       ],
       "additionalProperties": false
      },
      "faith_transcendence": {
       "type": "object",
       "properties": {
        "score": {
         "type": "integer",
         "minimum": 0,
         "maximum": 100
        },
        "intent": {
         "type": "string",
         "description": "<=25 words: what this level is FOR in this story"
        }
       },
       "required": [
        "score",
        "intent"
       ],
       "additionalProperties": false
      },
      "class": {
       "type": "object",
       "properties": {
        "score": {
         "type": "integer",
         "minimum": 0,
         "maximum": 100
        },
        "intent": {
         "type": "string",
         "description": "<=25 words: what this level is FOR in this story"
        }
       },
       "required": [
        "score",
        "intent"
       ],
       "additionalProperties": false
      },
      "gender": {
       "type": "object",
       "properties": {
        "score": {
         "type": "integer",
         "minimum": 0,
         "maximum": 100
        },
        "intent": {
         "type": "string",
         "description": "<=25 words: what this level is FOR in this story"
        }
       },
       "required": [
        "score",
        "intent"
       ],
       "additionalProperties": false
      },
      "technology": {
       "type": "object",
       "properties": {
        "score": {
         "type": "integer",
         "minimum": 0,
         "maximum": 100
        },
        "intent": {
         "type": "string",
         "description": "<=25 words: what this level is FOR in this story"
        }
       },
       "required": [
        "score",
        "intent"
       ],
       "additionalProperties": false
      }
     },
     "required": [
      "moral_clarity",
      "institutional_critique",
      "faith_transcendence",
      "class",
      "gender",
      "technology"
     ],
     "additionalProperties": false
    }
   },
   "required": [
    "affective",
    "modal",
    "generic",
    "thematic"
   ],
   "additionalProperties": false,
   "description": "modal dimensions are bipolar: 0 = first pole, 100 = second pole"
  },
  "state_dimensions": {
   "type": "array",
   "items": {
    "enum": [
     "physiological",
     "emotional",
     "epistemic",
     "psychological",
     "social",
     "material",
     "spatial",
     "legal",
     "reputational",
     "world",
     "magical",
     "technological",
     "political"
    ]
   },
   "description": "the closed vocabulary this work's state changes may use"
  },
  "constraints": {
   "type": "object",
   "properties": {
    "target_word_count": {
     "type": "integer"
    },
    "plot_count": {
     "type": "integer"
    },
    "scene_count_target": {
     "type": "integer"
    },
    "event_count_target": {
     "type": "integer"
    },
    "must_include": {
     "type": "array",
     "items": {
      "type": "string"
     }
    },
    "must_avoid": {
     "type": "array",
     "items": {
      "type": "string"
     }
    }
   },
   "required": [
    "target_word_count",
    "plot_count",
    "scene_count_target",
    "event_count_target",
    "must_include",
    "must_avoid"
   ],
   "additionalProperties": false
  },
  "keep_in_mind": {
   "type": "array",
   "items": {
    "type": "string"
   },
   "description": "standing notes every later layer must respect"
  }
 },
 "required": [
  "story_id",
  "title",
  "form",
  "language",
  "logline",
  "premise",
  "genre_primary",
  "genre_secondary",
  "audience",
  "setting",
  "pov",
  "style",
  "narrative_vector",
  "state_dimensions",
  "constraints",
  "keep_in_mind"
 ],
 "additionalProperties": false
}

