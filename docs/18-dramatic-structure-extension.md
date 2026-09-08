# 18 — Dramatic-Structure Extension

> **Implementation note (2026-09).** This proposal has been implemented, with
> one deliberate change: the analysis lives in a **separate drama structure
> layer** (`<tree>/drama/drama_structure.json`, generator
> `distill/drama_structure_layer.py`), not as a `meta.dramatic_structure`
> subtree. Rationale and the as-built design:
> [20 — The Drama Structure Layer](20-drama-structure-layer.md). The schema
> ideas, evaluation rubric and phase plan below otherwise still apply.

## Purpose

StoryTree already reconstructs a screenplay bottom-up:

```text
screenplay -> scenes -> events -> meta -> entities -> plots -> exposé -> root
```

This proposal adds a *non-destructive, optional* dramatic-structure analysis to
that path.  It answers questions such as:

- Which structural lens best describes this film: three-act, five-act,
  sequence, episodic, nonlinear, or another form?
- Where are the inciting incident, thresholds, reversals, midpoint, crisis,
  climax, denouement, and (where applicable) kiss-off?
- What does the exposition establish, and when is it completed or reframed?
- Which Hero's-Journey patterns are supported, ambiguous, absent, or simply
  not applicable?

The extension must describe the screenplay, not coerce it into a preferred
template.  A classical three-act answer is one possible conclusion, never a
default to be filled in without evidence.

For the expanded controlled vocabulary, recognition criteria, Hero's-Journey
maps, archetypal functions, and agent procedure, see the companion
[Dramaturgy Cheat Sheet](19-dramaturgy-cheatsheet.md).

## Placement in the bottom-up pipeline

Insert one new optional Meta substep after the existing `meta_section` and
`meta_perspectives` work and before downstream entity/plot synthesis:

```text
screenplay -> scenes -> events -> meta_section/meta_perspectives
           -> meta_dramatic_structure
           -> entities -> plots -> exposé -> root
```

`meta_dramatic_structure` consumes the existing event graph and concise meta
findings.  Its claims are grounded in event and scene identifiers; it does not
need a second, unconstrained read of the entire screenplay.  That preserves the
current bottom-up provenance and makes every structural claim inspectable.

It is deliberately a *subtree of Meta*, rather than a new mandatory global
layer.  Existing StoryTrees remain valid when the field is absent.

### What each existing layer should do

| Layer | Change | Requires a new model adapter? |
| --- | --- | --- |
| Scene facts / minds | No schema change. Retain precise local setup, wants, rules, and changes that later substantiate exposition and turns. | No |
| Events | No generative schema change. Add deterministic `screen_position` and retain scene/event provenance. | No |
| Meta | Add optional `dramatic_structure`; this is the only new generative step. | **Yes: `meta_dramatic_structure`** |
| Entities | Optionally project involvement at an anchor (for example, who crosses a threshold or makes the climax decision). References only; do not duplicate analysis. | No initially |
| Plots | Produce a deterministic plot-to-anchor/act coverage view from the event references. Plot discovery and chaining remain unchanged. | No initially |
| Exposé | Render a short, evidence-linked structural-beat paragraph from Meta when useful. | Only after evaluation shows the current exposé cannot use the projection well |
| Root | Mirror the selected structural shape in one compact field, with anchor references. | Only after evaluation shows the current root cannot use the projection well |

The first training iteration therefore needs **one additional LoRA**, not a
retraining of the twelve existing adapters.  Exposé and root are optional
follow-up adapters, not prerequisites.

## Versioned schema

Use an optional, versioned namespace at `meta.dramatic_structure`.  IDs below
are references to existing objects, never duplicated free-text events.

```json
{
  "version": "1.0",
  "mode": {
    "primary_lens": "three_act",
    "chronology": "linear",
    "confidence": 0.84,
    "alternatives": [
      {"lens": "sequence", "confidence": 0.53, "why_not_primary": "..."}
    ]
  },
  "exposition": {
    "dramatic_question": "...",
    "initial_world": "...",
    "established": [
      {
        "function": "want",
        "claim": "...",
        "event_ids": ["ev-003"],
        "scene_ids": ["sc-004"]
      }
    ],
    "closes_or_reframes_at": {
      "anchor_id": "ds-02",
      "event_ids": ["ev-012"]
    }
  },
  "anchors": [
    {
      "id": "ds-02",
      "kind": "inciting_incident",
      "event_ids": ["ev-012"],
      "scene_ids": ["sc-019"],
      "screen_position": 0.14,
      "story_position": 0.14,
      "change": "...",
      "evidence": "...",
      "confidence": 0.86,
      "alternatives": []
    }
  ],
  "acts": [
    {
      "id": "act-1",
      "label": "Setup and commitment",
      "lens": "three_act",
      "start_anchor_id": null,
      "end_anchor_id": "ds-03",
      "dramatic_question": "...",
      "state_delta": "...",
      "confidence": 0.79
    }
  ],
  "archetypal_patterns": [
    {
      "framework": "hero_journey",
      "stage": "call_to_adventure",
      "status": "supported",
      "anchor_ids": ["ds-02"],
      "evidence": "...",
      "counterevidence": null
    }
  ],
  "flags": ["nonlinear-ordering"]
}
```

Allowed `primary_lens` values should initially be `three_act`, `five_act`,
`sequence`, `episodic`, `nonlinear`, `framed`, `ensemble`, and `ambiguous`.
`kind` is an extensible controlled vocabulary: `inciting_incident`,
`act_break`, `threshold`, `midpoint`, `pinch`, `reversal`, `crisis`, `climax`,
`denouement`, `kiss_off`, and `reframing_reveal` are the initial set.

`screen_position` is normalized screenplay order.  `story_position` is optional
and only used where chronological ordering is meaningfully recoverable.  This
distinction is essential for flashbacks, frames, and mosaic narratives.

Hero's-Journey entries are not required to form a complete cycle.  Each stage
must explicitly be `supported`, `ambiguous`, `absent`, or `not_applicable`;
the latter two are valid, informative outputs.

## Bottom-up implementation plan

### Phase 0 — contract and deterministic projections

1. Add the schema, JSON validator, controlled vocabularies, and reference
   resolution checks.
2. Compute event `screen_position` deterministically from the ordered event
   sequence.  Do not ask an LLM to count pages or infer an index already
   available in the graph.
3. Add read-only projections for the explorer: scene/event -> anchor, plot ->
   anchor/act coverage, entity -> anchor involvement.  These are joins, not
   copied prose.
4. Leave the new field absent for legacy trees; no migration rewrite is needed.

### Phase 1 — create training and evaluation data

There are no trustworthy act labels merely because an event falls near 25%,
50%, or 75% of a script.  Build labels from the existing screenplay, scene,
event, and meta evidence:

1. Start with the high-quality English trees, preserving film-level held-out
   splits; then broaden by genre only after checking label quality.
2. Have two independent structured labelers propose lens, anchors, exposition,
   acts, and restrained archetype statuses.
3. Reconcile disagreements with an adjudication pass.  Sample every lens and
   genre for human review, especially nonlinear and ensemble cases.
4. Store evidence references and negative/ambiguous examples.  A film without
   a meaningful midpoint or kiss-off is useful training data.
5. Reserve a film-level blind test set.  No scenes, events, or scripts from a
   held-out film may enter prompt exemplars or adapter training.

### Phase 2 — one adapter, same inference conventions

Train `meta_dramatic_structure` with the same base model, rank-64 LoRA
configuration, context policy, and checkpoint/evaluation discipline used by
the current pipeline adapters.  Its prompt contains the compact ordered event
digest, relevant Meta findings, and schema instructions; its target is only
the validated subtree above.

Use one to two epochs initially.  Reject a checkpoint that improves formatting
but weakens grounding on the held-out set.  This keeps the change isolated:
the existing scene, event, entity, plot, exposé, and root adapters can continue
to serve current trees unchanged.

### Phase 3 — downstream consumption, only where it demonstrably helps

First render deterministic structural projections in the UI and evaluator.
Then measure whether the existing Exposé and Root adapters incorporate those
projections accurately.  Retrain only the specific consumer that fails:

- `expose_structural` if a compact account of exposition, turns, climax, and
  resolution is consistently missing or wrong;
- `root_structural` if the one-sentence/compact root framing should expose the
  overall structural shape.

This is at most two targeted follow-up LoRAs.  Do not retrain Plot or Entity
adapters simply to copy information that can be joined from Meta.

## Evaluation

Run structural evaluation separately from—and alongside—the existing
layer-quality evaluation.  Judges see the screenplay-derived evidence and the
candidate subtree, but not the source label or model identity.

### Automatic invariants

- Every cited scene/event/anchor reference resolves.
- Anchor event order agrees with `screen_position` unless the selected lens or
  a flag explicitly permits a chronology exception.
- Act boundaries are contiguous in screen order for linear lenses.
- Every substantive structural claim has evidence references.
- Unsupported required Hero's-Journey stages are rejected rather than guessed.

### Human/judge rubric (1–5)

1. **Lens appropriateness** — does the selected form fit this film without
   forcing a template?
2. **Anchor fidelity** — are turns, crisis, climax, and ending grounded in the
   cited events and their causal changes?
3. **Act segmentation** — are boundaries useful descriptions of changing
   dramatic conditions rather than percentile guesses?
4. **Exposition analysis** — does it identify world, want, stakes, conflict,
   and the point at which the initial situation changes?
5. **Archetype restraint** — are patterns evidence-based and are absences or
   ambiguity admitted where appropriate?
6. **Cross-layer consistency** — do plots, exposé, and root agree with the
   referenced structure without duplicating or contradicting it?

Report scores by genre, selected lens, script length, and chronology type—not
only as one global average.  Compare any new consumer adapter only on the
shared evaluation set and rubric.

## Top-down counterpart

The forward path should use the same data contract as a *soft planning aid*,
not turn analysis into a mandatory blueprint:

```text
brief -> root -> exposé -> structural_plan -> plots -> entities/events/scenes
```

`structural_plan` uses the same schema with planned rather than observed
anchors.  It can state desired turns, target stakes, optional archetypal
patterns, and alternative shapes.  Plot/event/scene generation may revise a
plan only by recording a compatible alternative or a deliberate deviation.
After a forward tree is generated, run the normal bottom-up analyzer and
compare the observed `dramatic_structure` with the intended plan.  This makes
structural drift measurable without altering the core StoryTree topology.

## Recommended rollout

1. Land the schema, validator, and explorer projections.
2. Label and validate a small, deliberately diverse pilot set.
3. Train and evaluate only `meta_dramatic_structure`.
4. Enable it as an optional stage in bottom-up construction.
5. Add Exposé and/or Root adapters only if the measured downstream benefit
   justifies them.

This keeps both directions compatible, preserves old trees, and gives act,
exposition, climax, ending, and archetype claims a concrete evidentiary path
back to scenes and events.
