"""The transition layer: reasoning as a first-class node of the story graph.

The pipeline as first built generated a whole layer per call — all the plots at
once, all the entities at once. That is efficient and it is the wrong shape for
what this corpus is for. A layer generated in one emission has no addressable
account of *why* each element is what it is, and the thing worth training on is
precisely that account.

So generation is flattened to one node per call:

    story_root → expose → pl-01 → pl-02 → ch-01 → ch-02 → … → ev-001 → ev-002 → …

and every node is preceded by a TRANSITION — a deliberate, written-out
reasoning trace that reads everything already established and argues its way to
the next node. The pair (state-so-far, transition, node) is the supervised
triple this whole system exists to produce.

Two things distinguish a transition from a model's private scratchpad:

1. It is *externalized on purpose*. The native reasoning trace an API returns is
   a by-product optimized for the model's own use; a transition is written to
   be read, and is held to a schema that forces coverage of things a private
   trace skips whenever it can get away with it.

2. It is *trajectorial*. A character does not enter an event in one state and
   leave in the same one, and a transition that describes a single frozen
   moment cannot explain a node that spans an hour of story time. Every psych
   block therefore carries `trajectory`: the phases the entity moves through
   inside this unit, each with its trigger.

Non-character entities get the same treatment in `entity_dynamics`. An object
changes custody and meaning; a location changes who controls it and what it
permits; a group changes cohesion and belief. Those are state changes with
causes, and the causes belong in the trace.
"""

from __future__ import annotations

# --------------------------------------------------------------------------
# Vocabularies
# --------------------------------------------------------------------------

NODE_KINDS = ["story_root", "expose", "plot", "entity", "event", "scene"]

CONTROL_MODES = ["spontaneous", "inhibited", "mixed", "compelled", "dissociated"]

IMPAIRMENT_CHANNELS = ["physical", "medical", "magical", "chemical", "coercive", "cognitive"]

SENSES = ["sight", "sound", "touch", "smell", "taste", "interoception", "proprioception"]

# Entities that are not minds still have dynamics; these are the axes they move on.
DYNAMIC_AXES = {
    "object": ["custody", "condition", "meaning", "visibility", "function"],
    "location": ["control", "access", "atmosphere", "population", "condition"],
    "group": ["cohesion", "belief", "resources", "leadership", "posture"],
    "concept": ["credence", "reach", "authority", "contestation"],
    "creature": ["condition", "disposition", "position", "drive"],
}


def _o(props, required=None, extra=False, desc=None):
    s = {"type": "object", "properties": props,
         "required": required if required is not None else list(props),
         "additionalProperties": extra}
    if desc:
        s["description"] = desc
    return s


def _s(desc=None):
    return {"type": "string", "description": desc} if desc else {"type": "string"}


def _arr(item, desc=None, mn=None):
    s = {"type": "array", "items": item}
    if desc:
        s["description"] = desc
    if mn:
        s["minItems"] = mn
    return s


_INT = {"type": "integer"}
_SCORE = {"type": "integer", "minimum": 0, "maximum": 100}
_BIPOLAR = {"type": "integer", "minimum": -100, "maximum": 100}


# --------------------------------------------------------------------------
# Craft: why this node, here, for this reader
# --------------------------------------------------------------------------

CRAFT_SCHEMA = _o({
    "audience_need": _s("What the declared target audience needs from the story at this "
                        "point — not what the plot needs. Cite the audience band."),
    "genre_convention": _s("What the genre leads a reader to expect here, and whether this "
                           "node satisfies, delays, or deliberately refuses that expectation."),
    "theme_and_style": _s("What the story root's theme, register and forbidden tics demand "
                          "of this node specifically."),
    "dramatic_function": _s("The function this node performs in the structure: what it sets "
                            "up, pays off, reverses, or closes."),
    "tension_management": _o({
        "entering": _SCORE, "leaving": _SCORE,
        "how": _s("What actually raises or releases pressure here, mechanically."),
    }),
    "why_now": _s("Why this node happens at this point in story time and could not have "
                  "happened earlier. If it could have, the ordering is wrong."),
    "why_not_otherwise": _arr(_o({
        "alternative": _s("A different node that could plausibly have gone here."),
        "rejected_because": _s(),
        "nearly_chosen": {"type": "boolean",
                          "description": "True if this was a close call."},
        "what_would_flip_it": _s("What single fact about the story would have to be "
                                 "different for this option to win. If nothing would, the "
                                 "option was never live and does not belong in the list."),
    }), "Alternatives considered and rejected. AT LEAST ONE must have nearly_chosen=true: "
        "if every option loses by a mile, you were not deciding, you were narrating a "
        "decision already made. A margin is what makes it a choice.", mn=2),
    "promises": _o({
        "made": _arr(_s(), "questions or expectations this node opens"),
        "kept": _arr(_s(), "earlier promises this node pays off"),
    }),
}, desc="Craft-level rationale. Answers 'why does this belong in THIS story for THIS reader'.")


# --------------------------------------------------------------------------
# Psychology: one block per character or creature
# --------------------------------------------------------------------------

PERCEPTION_SCHEMA = _o({
    "sight": _s(), "sound": _s(), "touch": _s(), "smell": _s(), "taste": _s(),
    "interoception": _s("Bodily sensation from inside: heartbeat, nausea, cold in the hands, "
                        "the ache of an old injury."),
    "proprioception": _s("Where the body is, what it is braced against, what it is doing."),
    "attention": _s("Of everything available, what this entity is actually attending to — "
                    "and what it is failing to notice."),
}, desc="The sensorium as this entity has it right now. Concrete and particular to the "
        "scene; two characters in one room do not perceive the same room.")

APPRAISAL_SCHEMA = _o({
    "value_at_stake": _s("Which of this character's declared values is engaged."),
    "valence": {**_BIPOLAR, "description": "-100 aversive to +100 appetitive"},
    "arousal": _SCORE,
    "self_conscious_emotion": _s("Shame, guilt, pride, humiliation, vindication — named "
                                 "precisely, or 'none' if genuinely absent."),
    "moral_reading": _s("How this character reads the moral shape of what is happening, "
                        "in their own terms, not the author's."),
    "somatic_marker": _s("The bodily signature the appraisal produces before any thought "
                         "arrives."),
}, desc="Value-based appraisal — the ventromedial evaluation. What this MEANS to this "
        "character given who they are, prior to deliberation.")

NORMS_SCHEMA = _o({
    "norms_in_force": _arr(_s(), "The specific social rules operating in this place, with "
                                 "these people, at this moment."),
    "how_others_would_judge": _s("What the people present would think of the act if they saw it."),
    "how_absent_others_would_judge": _s("The offstage audience that still constrains behaviour: "
                                        "the village, the dead, the institution."),
    "standing_at_risk": _s("What social position this character stands to lose or gain."),
    "norm_conflict": _s("Where two norms in force contradict each other, and which one wins here."),
})

TOM_SCHEMA = _o({
    "other": _s("The entity id this tower of belief is about."),
    "d1": _s("What THIS character believes about the other. (A → B)"),
    "d2": _s("What this character believes the other believes about them. (A → B → A)"),
    "d3": _s("What this character believes the other believes they believe — about the "
             "other or about a third party. (A → B → A → C). This is where deception, "
             "shame and negotiation actually live."),
    "accuracy": _s("Where this model of the other is WRONG, and what the error will cost. "
                   "A theory of mind that is always correct produces no drama."),
}, desc="Higher-order theory of mind to three degrees, per other entity.")

URGES_SCHEMA = _o({
    "cravings": _s("Appetitive pulls: food, warmth, drink, contact, the substance."),
    "physical_needs": _s("Sleep, water, heat, rest, the pressure of an untreated injury."),
    "psych_needs_conscious": _s("What this character knows they want from this moment."),
    "psych_needs_unconscious": _s("What they are actually pursuing and would deny."),
    "avoidances": _s("What they are steering away from without admitting it."),
})

IMPAIRMENT_SCHEMA = _o({
    "physical": _s("Injury, exhaustion, cold, age. 'none' if none."),
    "medical": _s("Illness, chronic condition, withdrawal. 'none' if none."),
    "magical": _s("Bindings, geas, enchantment, a levy being paid. 'none' if none."),
    "chemical": _s("Drink, drug, potion, poison. 'none' if none."),
    "coercive": _s("Threat, obligation, debt, blackmail — pressure from another agent."),
    "cognitive": _s("What this character cannot currently think clearly about, and why."),
    "net_effect": _s("How the sum of these changes what this character is capable of here."),
}, desc="Everything limiting or acting on this entity from outside its own will.")

DELIBERATION_SCHEMA = _o({
    "framing": _s("How this character has framed the problem to themselves — which is "
                  "usually where the real error is."),
    "options_weighed": _arr(_o({
        "option": _s(),
        "predicted_outcome": _s(),
        "cost": _s(),
    }), mn=2),
    "reasoning": _s("The explicit chain of practical reasoning, in this character's own "
                    "idiom. A smith reasons in weights and heat, not in abstractions."),
    "chosen_because": _s(),
    "known_unknowns": _s("What this character knows they do not know, and how they are "
                         "hedging against it."),
}, desc="Deliberate analysis — the dorsolateral evaluation. Slow, effortful, verbal.")

CONTROL_SCHEMA = _o({
    "mode": {"enum": CONTROL_MODES},
    "felt": _s("What is actually being experienced."),
    "expressed": _s("What is being shown on the face, in the voice, in the body."),
    "divergence_reason": _s("Why felt and expressed differ. 'aligned' if they do not — but "
                            "check honestly, because alignment is rarer than it looks."),
    "leakage": _s("What escapes the control anyway: the hand, the pause, the word chosen "
                  "a half-second late. This is what another character can actually read."),
    "inhibited_impulse": _s("What this character wanted to do and did not."),
}, desc="The gap between the interior and the performance. Dialogue lives in this gap.")

TRAJECTORY_STEP = _o({
    "phase": _s("A named stage within this unit — e.g. 'on entering', 'after the admission', "
                "'once the door closes'."),
    "shift": _s("What changes about this entity's state during this phase."),
    "trigger": _s("The specific perceivable thing that causes the shift."),
    "state_delta": _o({
        "variable": _s("A declared state variable, if this phase moves one."),
        "from": _s(), "to": _s(),
    }, required=[], extra=True),
})

PSYCH_SCHEMA = _o({
    "entity": _s(),
    "entering_state": _s("Where this character is, in themselves, as the unit opens."),
    "perception": PERCEPTION_SCHEMA,
    "appraisal": APPRAISAL_SCHEMA,
    "social_norms": NORMS_SCHEMA,
    "theory_of_mind": _arr(TOM_SCHEMA, "One tower per other entity that matters here.", mn=1),
    "urges": URGES_SCHEMA,
    "impairments": IMPAIRMENT_SCHEMA,
    "deliberation": DELIBERATION_SCHEMA,
    "control": CONTROL_SCHEMA,
    "intention": _s("What this character is trying to bring about."),
    "action": _s("What they actually do in this unit."),
    "trajectory": _arr(TRAJECTORY_STEP,
                       "How this character moves THROUGH the unit. At least two phases — an "
                       "entity that is identical at the end of an event as at the start did "
                       "not participate in it.", mn=2),
    "leaving_state": _s("Where this character is, in themselves, as the unit closes."),
    "unresolved": _s("What this character is left carrying that the unit did not settle."),
}, desc="A full psychological account for one character or creature across this unit.")


# --------------------------------------------------------------------------
# Dynamics: everything that is not a mind
# --------------------------------------------------------------------------

DYNAMICS_SCHEMA = _o({
    "entity": _s(),
    "kind": {"enum": ["object", "location", "group", "concept", "creature"]},
    "entering_state": _s(),
    "forces_acting": _arr(_s(), "What is acting on this entity in this unit — hands, weather, "
                                "belief, law, heat, time.", mn=1),
    "axis_changes": _arr(_o({
        "axis": _s("e.g. custody, control, cohesion, credence, condition, meaning"),
        "from": _s(), "to": _s(),
        "caused_by": _s(),
    }), mn=1),
    "trajectory": _arr(TRAJECTORY_STEP, "How it changes across the unit, in phases.", mn=1),
    "leaving_state": _s(),
    "significance_shift": _s("What this entity MEANS to the characters after this unit that "
                             "it did not mean before. An object whose meaning never moves is "
                             "set dressing, not an entity."),
}, desc="Objects, locations, groups and concepts have states and trajectories too. A relic "
        "changes hands and meaning; a village changes what it believes it is owed.")


# --------------------------------------------------------------------------
# Continuity: what this node inherits and must not break
# --------------------------------------------------------------------------

CONTINUITY_SCHEMA = _o({
    "established_facts_used": _arr(_o({
        "fact": _s(),
        "source": _s("The node id or pointer this fact comes from — e.g. 'ev-005', "
                     "'/ch-02/profile/backstory/b04', 'root.rules_of_the_world[3]'."),
        "how_used": _s(),
    }), "Everything already established that this node depends on. Cite sources.", mn=1),
    "constraints_honoured": _arr(_s(), "World rules and standing notes this node had to "
                                       "obey, named specifically.", mn=1),
    "contradictions_checked": _arr(_o({
        "risk": _s("A contradiction this node could plausibly have introduced."),
        "avoided_by": _s(),
    }), mn=1),
    "state_preconditions": _arr(_o({
        "entity": _s(), "variable": _s(),
        "must_be": _s("The value this variable must already hold for this node to be possible."),
    }), "The state this node assumes. Checked mechanically against the fold."),
    "forward_commitments": _arr(_s(), "What later nodes are now obliged to deal with."),
})


# --------------------------------------------------------------------------
# The transition envelope
# --------------------------------------------------------------------------

SPECIMEN_SCHEMA = _o({
    "moment": _s("The exact beat this exchange belongs to — the one you have called the "
                 "turning point of the unit."),
    "lines": _arr(_o({
        "speaker": _s(),
        "line": _s("What they actually say. Real dialogue, in their own idiom, not a "
                   "paraphrase and not a summary of intent."),
        "subtext": _s("What they mean and are not saying."),
    }), "Six to ten lines. Write them as they would be spoken.", mn=6),
    "what_this_exposes": _s("Read your own lines back cold. What do they reveal that the "
                            "analysis above did not — about the scene, or about your own "
                            "assumptions?"),
    "risks_checked": _arr(_o({
        "risk": _s("A risk you named earlier in this transition."),
        "does_the_exchange_avoid_it": {"type": "boolean"},
        "evidence": _s("Which line, and why."),
    }), "Every risk you listed, tested against the lines you just wrote. A risk you "
        "cannot test against them was too vague to be a risk.", mn=1),
    "voices_distinct": _s("If the two speakers could swap lines without anyone noticing, "
                          "say so here and say what you are changing. This is the most "
                          "common failure and the hardest to see from inside."),
}, desc="A specimen exchange. Everything above this field is unfalsifiable until somebody "
        "speaks — the analysis can be immaculate and the scene still dead. Writing the "
        "lines is the only way to find out which, and it is cheap.")


TRANSITION_SCHEMA = _o({
    "target": _o({
        "kind": {"enum": NODE_KINDS},
        "node_id": _s("The id of the node this transition produces."),
        "ordinal": _INT,
    }),
    "situation": _s("Where the story stands as this transition begins, in 3-6 sentences. "
                    "Written from the state, not from memory."),
    "craft": CRAFT_SCHEMA,
    "psychology": _arr(PSYCH_SCHEMA,
                       "One block per character or creature materially involved. For a node "
                       "with no characters in it (a location dossier, the story root), this "
                       "may be empty.", mn=0),
    "dynamics": _arr(DYNAMICS_SCHEMA,
                     "One block per non-mind entity that changes or exerts force here.", mn=0),
    "interaction": _o({
        "what_collides": _s("The specific opposition in this unit: whose want crosses whose."),
        "power_balance": _s("Who can compel what, and how that shifts during the unit."),
        "information_asymmetry": _s("Who knows what the other does not, and what that buys them."),
        "turning_point": _s("The exact moment the unit pivots, and what makes it pivot."),
    }),
    "specimen": SPECIMEN_SCHEMA,
    "continuity": CONTINUITY_SCHEMA,
    "decision": _o({
        "resolution": _s("What the node will therefore be, stated plainly."),
        "state_changes_implied": _arr(_o({
            "entity": _s(), "variable": _s(), "from": _s(), "to": _s(),
            "because": _s(),
        }), mn=0),
        "confidence": _SCORE,
        "risks": _arr(_s(), "Ways this node could be the wrong call."),
    }),
}, desc="One deliberate reasoning transition, producing exactly one node of the story graph.")


# Compact variant for cheap nodes (minor entities, setup events) where the full
# instrument is more expensive than the node is worth.
TRANSITION_LITE_SCHEMA = _o({
    "target": _o({"kind": {"enum": NODE_KINDS}, "node_id": _s(), "ordinal": _INT}),
    "situation": _s(),
    "craft": _o({
        "dramatic_function": _s(), "why_now": _s(), "theme_and_style": _s(),
        "why_not_otherwise": _arr(_o({"alternative": _s(), "rejected_because": _s()}), mn=1),
    }),
    "psychology": _arr(PSYCH_SCHEMA, mn=0),
    "dynamics": _arr(DYNAMICS_SCHEMA, mn=0),
    "continuity": _o({
        "established_facts_used": _arr(_o({"fact": _s(), "source": _s(), "how_used": _s()}), mn=1),
        "constraints_honoured": _arr(_s(), mn=1),
    }),
    "decision": _o({"resolution": _s(), "confidence": _SCORE}),
}, desc="A reduced transition for low-salience nodes.")


TRANSITION_SCHEMAS = {
    "full": TRANSITION_SCHEMA,
    "lite": TRANSITION_LITE_SCHEMA,
}


# --------------------------------------------------------------------------
# Quality scoring — a transition that ticks the boxes can still be empty
# --------------------------------------------------------------------------

def score_transition(tr: dict) -> dict:
    """Structural depth metrics. Cheap, deterministic, and unfoolable by length."""
    psych = tr.get("psychology") or []
    dyn = tr.get("dynamics") or []

    tom_towers = sum(len(p.get("theory_of_mind") or []) for p in psych)
    tom_d3 = sum(1 for p in psych for t in (p.get("theory_of_mind") or [])
                 if (t.get("d3") or "").strip())
    tom_wrong = sum(1 for p in psych for t in (p.get("theory_of_mind") or [])
                    if (t.get("accuracy") or "").strip())
    traj_phases = sum(len(p.get("trajectory") or []) for p in psych)
    dyn_phases = sum(len(d.get("trajectory") or []) for d in dyn)
    divergent = sum(1 for p in psych
                    if (p.get("control", {}).get("divergence_reason") or "").strip().lower()
                    not in ("", "aligned", "none", "n/a"))
    senses = sum(1 for p in psych for k in SENSES
                 if (p.get("perception", {}).get(k) or "").strip())
    impair = sum(1 for p in psych for k in IMPAIRMENT_CHANNELS
                 if (p.get("impairments", {}).get(k) or "").strip().lower() not in ("", "none", "n/a"))
    options = sum(len(p.get("deliberation", {}).get("options_weighed") or []) for p in psych)
    facts = len((tr.get("continuity") or {}).get("established_facts_used") or [])
    cited = sum(1 for f in ((tr.get("continuity") or {}).get("established_facts_used") or [])
                if (f.get("source") or "").strip())
    alts = len((tr.get("craft") or {}).get("why_not_otherwise") or [])
    close = sum(1 for a in ((tr.get("craft") or {}).get("why_not_otherwise") or [])
                if a.get("nearly_chosen"))
    spec = tr.get("specimen") or {}
    spec_lines = len(spec.get("lines") or [])
    risks_tested = len(spec.get("risks_checked") or [])

    return {
        "characters": len(psych),
        "nonmind_entities": len(dyn),
        "tom_towers": tom_towers,
        "tom_depth3": tom_d3,
        "tom_with_error": tom_wrong,
        "trajectory_phases": traj_phases,
        "dynamics_phases": dyn_phases,
        "felt_expressed_divergence": divergent,
        "sense_channels_filled": senses,
        "impairments_active": impair,
        "options_weighed": options,
        "facts_cited": facts,
        "facts_with_source": cited,
        "alternatives_rejected": alts,
        "alternatives_nearly_chosen": close,
        "specimen_lines": spec_lines,
        "risks_tested_against_dialogue": risks_tested,
        "words": len(_flatten_text(tr).split()),
    }


def _flatten_text(node) -> str:
    if isinstance(node, str):
        return node
    if isinstance(node, dict):
        return " ".join(_flatten_text(v) for v in node.values())
    if isinstance(node, list):
        return " ".join(_flatten_text(v) for v in node)
    return ""


def grade(score: dict) -> tuple[str, list[str]]:
    """Turn the metrics into a pass/warn verdict with named gaps."""
    # An empty psychology list is not a thin document, it is an absent one.
    # Scored by summing over the blocks, zero blocks produced a clean sheet and
    # a `pass`. Fail it explicitly before any other rule runs.
    if not score.get("characters"):
        return "fail", ["no psychology block was produced at all"]
    gaps = []
    if score["characters"] and score["tom_depth3"] < score["characters"]:
        gaps.append("not every character reasons to the third degree")
    if score["characters"] and score["trajectory_phases"] < 2 * score["characters"]:
        gaps.append("trajectories are snapshots, not arcs")
    if score["characters"] and score["sense_channels_filled"] < 4 * score["characters"]:
        gaps.append("sensorium thin")
    if score["facts_cited"] and score["facts_with_source"] < score["facts_cited"]:
        gaps.append("facts asserted without a source pointer")
    if score["alternatives_rejected"] < 2:
        gaps.append("fewer than two alternatives — not a decision")
    if score.get("alternatives_nearly_chosen", 0) < 1:
        gaps.append("every alternative lost by a mile — the choice was already made")
    if score.get("specimen_lines", 0) < 6:
        gaps.append("no specimen exchange — the analysis is untested until someone speaks")
    if score.get("risks_tested_against_dialogue", 0) < 1:
        gaps.append("risks never checked against the actual lines")
    if score["characters"] and score["tom_with_error"] == 0:
        gaps.append("every theory of mind is correct — no dramatic irony available")
    verdict = "pass" if not gaps else ("warn" if len(gaps) <= 2 else "thin")
    return verdict, gaps
