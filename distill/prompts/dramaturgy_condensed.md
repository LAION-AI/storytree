# Dramaturgy reference (condensed, prompt-injected)

This is the working reference the drama-structure analyst sees in its context
on every call. It is condensed from `docs/19-dramaturgy-cheatsheet.md`; when
editing, keep the two consistent. It must stay compact — it rides along in
every prompt of every pass.

## Rules (non-negotiable)

1. DESCRIBE BEFORE NAMING. First identify what changes, who acts, why it
   matters, citing the event/scene. Only then attach a term like `midpoint`.
2. FRAMEWORKS ARE LENSES, NOT FACTS. A film may fit several lenses, none
   cleanly, or deliberately resist them. Record alternatives. `ambiguous` is
   a better answer than an invented act break.
3. FUNCTION BEATS PERCENTILE. "It happens at 50%" is not evidence for a
   midpoint. Evidence is a changed strategy, stake, knowledge, commitment or
   direction.
4. TWO ORDERS. Screen order = how the audience receives information; story
   order = chronology. Flashbacks, frames and reveals make them differ; that
   is a feature to record, not a defect.
5. NO INVENTED PSYCHOLOGY. Claim a desire, wound, need or archetype only when
   it is enacted, stated, or robustly implied by multiple cited nodes.
6. EVERY MATERIAL CLAIM NEEDS PROVENANCE: event ids, scene ids, and a
   grounding sentence saying WHY the evidence supports the function — not
   merely what happens.
7. SMALLEST VALID REPRESENTATION. A tight linear film may need five anchors
   and two acts. Do not pad with Hero's-Journey stages, sequences or
   diagnostics that add no grounded explanatory value.

Evidence statuses: `observed` (directly enacted/stated) ·
`supported_inference` (follows from 2+ cited changes) · `ambiguous`
(competing readings remain — name them, do not pick a winner by default).
`absent` and `not_applicable` are valid, informative results.

## Anchor vocabulary (function, never fixed location)

| kind | function | strong signal | do NOT confuse with |
|---|---|---|---|
| opening_situation | establishes initial tone/value/state | meaningfully contrasts with the ending | any first scene |
| hook | creates curiosity/concern before full context | a reason to follow exists early | the inciting incident |
| inciting_incident | disturbs equilibrium, poses the dramatic question | demands a consequential response | an ordinary bad day that changes nothing |
| debate_or_refusal | tests whether the protagonist engages | hesitation, cost appraisal, failed avoidance | a mandatory beat — many films omit it |
| commitment_threshold | old equilibrium becomes unavailable | strategy/identity/cost changes, retreat harder | merely travelling somewhere new |
| act_break | ends a movement, changes the governing question | next act cannot proceed by the same logic | any scene near 25/75% |
| first_trial | first real test of the new pursuit | gap between plan and opposition shows | generic early obstacle |
| progressive_complication | escalates cost, risk, scope or opposition | later action must differ from earlier | repetition at the same level |
| pinch_point | concentrates antagonist pressure | central obstacle becomes vivid and costly | a required page-count marker |
| midpoint | reverses or reorients the central pursuit | knowledge/commitment/stakes change the second half | the literal middle; a loud scene without strategic change |
| reversal | fortune/meaning turns opposite, prepared by causality | earlier action's consequence flips its direction | a random unsupported twist |
| recognition | discovery of identity/relation/truth changes choice | knowledge alters fortune, often with reversal | a mere audience reminder |
| reframing_reveal | revises the reading of PAST events | new info changes a material interpretation | any exposition dump |
| all_is_lost | apparent loss of the central path/person/value | plan fails, cost peaks before the final choice | a temporary obstacle |
| crisis | the decisive dilemma: incompatible goods force a choice | protagonist must choose what they VALUE | the climax (often separate, later) |
| climax | the action that settles the primary question | causally prepared, irreversible change | the loudest or last scene by default |
| false_ending | credible resolution overturned by remaining stakes | a deeper final movement becomes necessary | a sequel hook |
| denouement | consequences and the new equilibrium become legible | practical/emotional effects discharged | any slow scene after the climax |
| kiss_off | final sharp gesture sealing tone/meaning | resonance or irony after resolution | a mandatory final joke |
| cliffhanger | ends a unit withholding an imminent outcome | serial form demands continuation | any open ending |

Causality test for every anchor: (1) what valued condition changed?
(2) whose objective/strategy/relationship changes because of it? (3) what
later event would differ if it were removed? (4) is it prepared by
probability/necessity? One event may carry several functions (a discovery can
be recognition AND midpoint) — one anchor, several functions, each explained.
Crisis and climax, disturbance and commitment, are OFTEN SEPARATE events.
A local plot turn is not a film-level anchor.

## Macro-structure lenses (pick ONE primary, list credible alternatives)

- `three_act` — setup / confrontation / resolution: two major reorientations,
  a central pursuit, an ending that answers it. Proportions are conventions,
  not validation.
- `five_act` — rise-fall with substantial post-climax unraveling.
- `eight_sequence` — eight mini-arcs with real objectives and local peaks.
  Do not invent eight empty bins.
- `archplot` — active protagonist, external conflict, continuous causal
  time, closed ending. `miniplot` — internal conflict, multiple/passive
  protagonists, open ending; quiet does not mean structureless. `antiplot` —
  discontinuity/chance/nonlinearity as the organising principle itself.
- `kishotenketsu` — ki/shō/ten/ketsu: a non-conflict shift or juxtaposition
  reorganises meaning. Do not retrofit Western act breaks onto it.
- `episodic` — linked episodes, local completion, a binding principle.
- `parallel_ensemble` — several threads/protagonists whose meanings braid or
  collide; several local climaxes are normal.
- `framed` — outer story recontextualises an inner one; track both levels.
- `nonlinear` — disclosure order differs materially from chronology; store
  both positions.
- `ambiguous` — the honest label when no lens is the least-forcing fit.

Narration modes: `linear | nonlinear | parallel | framed | episodic |
ambiguous`.

## Hero's Journey (Vogler 12) — apply LAST, and only if it adds power

Stages: ordinary_world, call_to_adventure, refusal, meeting_with_mentor,
crossing_first_threshold, tests_allies_enemies, approach_to_inmost_cave,
ordeal, reward, road_back, resurrection, return_with_elixir.

Every stage gets a status: `supported | ambiguous | absent | not_applicable`
— the last two are informative results, never failures. False-positive traps:
an inciting incident is not automatically a call_to_adventure (was a new
path/world offered?); an act break is not a threshold (has return become
materially impossible?); a hardship is not an ordeal (is it a central
confrontation with death/identity/irreversible cost?); a final fight is not a
resurrection (does the character act FROM changed understanding?). For
ensembles, procedurals or static-character comedy, say `not_applicable` with
one sentence why — that is more useful than twelve forced `absent` rows.

## Endings — independent axes

plot_closure: closed | partially_closed | open | deliberately_unresolved.
central_question_result: affirmed | answered_negative | reframed | refused |
ambiguous. fortune_direction: positive | negative | mixed | ironic |
cyclical. character_movement: changed | unchanged_by_choice |
changed_by_revelation | corrupted | unknown. final_gesture: denouement |
kiss_off | cliffhanger | callback | reframing_reveal | image_rhyme | none.

Resolution (causal settling), denouement (consequences become legible) and
kiss-off (final gesture) can be one event or far apart — state their
relationship explicitly. An ending can be open in plot while an emotional arc
completes. Never call the last scene the climax just because it is last.

## Sequence escalation patterns (name HOW it rises, or say it doesn't)

obstacle_ladder · narrowing_options · expanding_scope · deepening_cost ·
information_reversal · time_compression · role_reversal · convergence ·
none (a meditative or episodic work may organise interest through contrast,
recurrence or accumulation instead — that is not a defect).

## Diagnostics (pointers for an evaluator, never verdicts)

unclear_dramatic_question · low_escalation · unearned_turn ·
unresolved_thread · orphaned_setup · climax_question_mismatch ·
exposition_overload_risk · framework_overfit_risk.

## Procedure

1. Read the ordered events and their before→after changes; build a change
   ledger before applying any theory label.
2. Identify baseline, disturbance, central question, focal agents, stakes,
   clocks. Separate direct evidence from inference.
3. Mark candidate anchors with the causality test; keep alternatives.
4. Group real event runs into sequences; choose the LEAST-FORCING lens.
5. Apply Hero's Journey and archetypes last, statuses explicit.
6. Validate every reference; keep screen order and chronology distinct;
   base act labels on function, not percentage.
