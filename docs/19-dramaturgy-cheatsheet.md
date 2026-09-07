# 19 — Dramaturgy Cheat Sheet for `meta.dramatic_structure`

> **Purpose.** This is a working reference for an analysis agent.  It explains
> which dramatic concepts may be represented in the optional
> `meta.dramatic_structure` subtree, how to recognise them from StoryTree
> evidence, and when to leave them unset.  It is not a screenplay formula.
>
> **Companion document:** [18 — Dramatic-Structure Extension](18-dramatic-structure-extension.md)
> defines the pipeline placement and versioned contract.  This document expands
> its vocabulary and analysis policy.

## 1. Non-negotiable analysis rules

1. **Describe before naming.** Identify what changes, who acts, why it matters,
   and cite the event/scene.  Attach a term such as `midpoint` only if the
   function is supported.
2. **Frameworks are lenses, not facts.** A film may fit several lenses, none
   cleanly, or deliberately resist them.  Record alternatives and confidence.
3. **Function beats percentile.** “It happens at 50%” is not evidence for a
   midpoint.  Position is a weak cue; a changed strategy, stakes, knowledge,
   commitment, or direction is stronger evidence.
4. **Preserve two orders.** `screen_position` is the order in which the audience
   receives information; `story_position` is chronology where it can be
   reconstructed.  Flashbacks, frames, parallel stories, and revelations make
   the difference meaningful.
5. **No invented psychology.** Call a desire, fear, wound, need, archetype, or
   theme only when it is enacted, stated, or robustly implied by multiple
   StoryTree nodes.  Mark the rest `ambiguous` or omit it.
6. **Every material claim needs provenance.** Cite `event_ids` and normally
   `scene_ids`; `evidence` says *why this evidence supports the function*, not
   merely what happens.
7. **Do not duplicate lower layers.** Scene facts, event changes, entities, and
   plots remain the source.  Meta records the cross-event pattern and stable
   references.

### Evidence status

Use these statuses on interpretive items:

| Status | Meaning | Agent action |
| --- | --- | --- |
| `observed` | Directly enacted or explicitly stated in cited material | State it compactly. |
| `supported_inference` | The interpretation follows from two or more cited changes | Explain the causal link and give confidence. |
| `ambiguous` | Plausible competing readings remain | Name the alternatives; do not select a winner by default. |
| `absent` | The framework asks for something that the film does not meaningfully supply | This is a valid result. |
| `not_applicable` | The concept itself does not fit the work, medium, or selected lens | Do not force a substitute. |

## 2. Where dramatic information lives in StoryTree

| StoryTree object | What it can establish | What Meta should derive from it |
| --- | --- | --- |
| Scene facts / minds | Local goal, conflict, revelation, emotional or relational change, setup/payoff material | Evidence for an anchor; scene-level exposition functions; local turning beats. |
| Event | A causally coherent run of scenes, before/after change, participants, consequences | Primary evidence unit for a turn, sequence, act boundary, escalation, reversal, or resolution. |
| Meta section / perspectives | Central tensions, different character/world views, recurring questions | Thematic argument, point-of-view structure, value conflicts, framing of the dramatic question. |
| Entity | Stable wants, states, relations, transformation and contradiction | Character arc, relationship arc, protagonist/antagonist pressure; never a clinical diagnosis. |
| Plot | A/B/C threads and their event spines | Thread onset, escalation, convergence, braid, discharge, and its relation to global anchors. |
| Exposé / root | Condensed whole-story interpretation | Downstream consumer of the grounded structural analysis, never its source of truth. |

The correct direction remains bottom-up: **scene -> event -> meta analysis ->
downstream projection**.  The screenplay is accessed directly only at the scene
layer, as specified by [the StoryTree structure document](storytree-structure.md).

## 3. Proposed expanded Meta contract

All fields are optional.  Prefer a short evidence-linked array over broad,
unfalsifiable prose.

```json
{
  "dramatic_structure": {
    "version": "1.1",
    "analysis_scope": {
      "screenplay_form": "feature_film",
      "narration_mode": "linear|nonlinear|parallel|framed|episodic|anthology|ambiguous",
      "primary_lens": "three_act|five_act|eight_sequence|kishotenketsu|archplot|miniplot|antiplot|ensemble|ambiguous",
      "alternatives": [{"lens": "...", "confidence": 0.0, "evidence": "..."}]
    },
    "dramatic_core": {
      "central_dramatic_question": "...",
      "controlling_idea": {"claim": "value changes because cause", "status": "supported_inference"},
      "value_at_stake": ["love", "truth", "freedom"],
      "premise_or_argument": "...",
      "audience_promises": ["..."],
      "genre_engine": ["..."],
      "clock_or_urgency": [{"kind": "deadline", "event_ids": ["ev-..."], "status": "observed"}]
    },
    "exposition": {"...": "see section 5"},
    "anchors": [{"...": "see section 6"}],
    "acts": [{"...": "see section 7"}],
    "sequences": [{"...": "see section 8"}],
    "character_and_relationship_arcs": [{"...": "see section 10"}],
    "plot_braid": {"...": "see section 11"},
    "narration_and_information_design": {"...": "see section 12"},
    "archetypal_patterns": [{"...": "see sections 13–14"}],
    "motifs_and_payoffs": [{"...": "see section 15"}],
    "ending": {"...": "see section 16"},
    "diagnostics": [{"code": "...", "severity": "note|warning", "evidence": "..."}]
  }
}
```

`controlling_idea`, `premise_or_argument`, and `audience_promises` are
interpretations, never inferred facts.  They require evidence and must not be
manufactured merely because a schema field exists.

## 4. Fundamental units: beat, scene, sequence, act, story

| Unit | Useful definition for analysis | Recognition test | Meta representation |
| --- | --- | --- | --- |
| Beat | An action/reaction exchange that shifts immediate pressure or tactic | Someone pursues, meets resistance, adjusts | Usually stays below Meta; cite via scene/event only if it is decisive. |
| Scene | A relatively continuous unit in which conflict changes at least one value | Compare entry vs exit: power, knowledge, intimacy, safety, freedom, etc. | Scene evidence and local function. |
| Event | A causal unit of one or more scenes that produces a meaningful change | Could it be summarised as one irreversible-or-costly development? | Main anchor evidence. |
| Sequence | Several scenes/events united by one immediate objective or problem and escalating to a peak | A coherent mini-arc: pursuit, trial, investigation, escape, courtship, heist | Named cluster with start/end events, objective, outcome, and value shift. |
| Act | A larger movement of sequences ending in a major reorientation | After its terminal event, strategy, stakes, world, commitment, or question cannot simply continue as before | Act range, terminal anchor, dramatic question, state delta. |
| Story | The selected arrangement of changes that advances a central dramatic question | The final event resolves, transforms, refuses, or reframes that question | Root/exposé consume the Meta result. |

An event that merely repeats the same value, tactic, and consequence is not a
turn.  A quiet scene can be a turn if knowledge, commitment, or relationship
meaning changes.

## 5. Exposition: what the audience must understand

Exposition is **not the opening minutes** and not synonymous with backstory. It
is the controlled delivery of information that lets the audience understand
the present dramatic situation.

### Record these functions

| Function | What to look for | Why it matters |
| --- | --- | --- |
| `world_rule` | Social, physical, genre, institutional, or moral rule that constrains action | Establishes what is possible and costly. |
| `baseline` | The initial equilibrium, routine, wound, relationship, or status quo | Makes disruption and transformation legible. |
| `protagonist_want` | A concrete pursued objective or lack | Gives action direction. |
| `need_or_misbelief` | A recurring inner limitation or false rule the story pressures | Optional; distinguish it from a stated want. |
| `stakes` | What is gained/lost and for whom | Makes conflict consequential. |
| `opposition` | Antagonist, system, relationship, self-conflict, or environment | Establishes the pressure source. |
| `inciting_disturbance` | Event that destabilises the baseline and creates a question | Starts the main movement. |
| `promise_of_premise` | Genre/world situation the film appears to promise it will explore | Helps explain why later sequences belong. |
| `information_gap` | Material intentionally withheld from the audience or character | Supports mystery, surprise, or dramatic irony analysis. |

For each entry record `claim`, `function`, `event_ids`, `scene_ids`,
`delivery_mode` (`action`, `dialogue`, `image`, `document`, `flashback`,
`voice_over`, `withheld`), `audience_knows_when`, and `status`.

### Exposition diagnosis

- `opens_in_motion`: the film begins near a live conflict; prior context is
  supplied later.
- `delayed_inciting_incident`: valid when the setup itself carries pressure or
  a secondary thread holds attention; not automatically a defect.
- `exposition_reframed`: later evidence changes what the opening meant.
- `exposition_completed`: the audience has enough to grasp the central
  question; it need not have received every fact.

Do not flag “information delivered late” as a problem unless it prevents a
coherent reading or violates a deliberate mystery/point-of-view design.

## 6. Structural anchors: controlled vocabulary

Every anchor should contain `id`, `kind`, `event_ids`, `scene_ids`,
`screen_position`, optional `story_position`, `change`, `function`,
`evidence`, `status`, `confidence`, and `alternatives`.

| Anchor kind | Function, not fixed location | Strong recognition signal | Common confusion |
| --- | --- | --- | --- |
| `opening_image_or_situation` | Establishes initial tone, value, image, or state | It meaningfully contrasts with/refines ending or premise | Any first scene. |
| `hook` | Creates audience curiosity, concern, anticipation, or surprise | It gives a reason to follow before full context exists | The inciting incident. It may be earlier/later/different. |
| `inciting_incident` | Disturbs equilibrium and poses the central dramatic question | It demands or provokes a consequential response | A precursor, invitation, or ordinary bad day that changes nothing. |
| `debate_or_refusal` | Tests whether the protagonist will engage | Hesitation, alternatives, cost appraisal, refusal, or failed avoidance | A mandatory beat; many films omit it. |
| `commitment` / `threshold` | Choice or event makes the old equilibrium unavailable | Strategy, setting, identity, or cost changes; retreat is materially harder | Merely travelling to a new location. |
| `act_break` | Ends one large movement and changes the story's governing question or strategy | The next act cannot proceed by the same logic | Any scene around 25/75%. |
| `first_trial` | First meaningful test of the new pursuit | Reveals a gap between plan and opposition | Generic early obstacle. |
| `progressive_complication` | Escalates cost, risk, scope, intimacy, or opposition | Later action must be riskier/different than earlier action | Repetition at the same dramatic level. |
| `pinch_point` | Concentrates threat/pressure, often revealing antagonist force | Makes the central obstacle vivid and costly | A required “page-37/page-62” marker. |
| `midpoint` | Reverses or significantly reorients the central pursuit | New knowledge, commitment, apparent victory/defeat, stake increase, or role reversal changes the second half | The literal middle; a big action scene without strategic change. |
| `reversal` / `peripeteia` | A probable/necessary change toward the opposite fortune or meaning | Earlier action’s consequence turns its expected direction | Random surprise or unsupported twist. |
| `recognition` / `anagnorisis` | Crucial discovery of identity, relation, truth, cause, or self | Knowledge changes choice/fortune, often combined with reversal | Mere audience reminder. |
| `reframing_reveal` | Revises the audience's reading of past events | New information changes a material interpretation | Any exposition dump. |
| `all_is_lost` / `major_setback` | The apparent loss of the central path, person, value, or resource | Existing plan fails and cost peaks before final choice | A temporary obstacle without changed stakes. |
| `crisis` | The decisive dilemma: incompatible goods/costs require a choice | The protagonist must choose what they value, not just execute | The climax itself. Crisis often precedes it. |
| `climax` | The decisive action/confrontation that settles the primary dramatic question | It is causally prepared and changes fortune or meaning irreversibly | Loudest scene, final fight, or last chronological event by default. |
| `false_climax` / `false_ending` | An apparent resolution that makes a deeper final movement necessary | A credible end is overturned by remaining causal stakes | A simple sequel hook. |
| `denouement` / `aftermath` | Shows consequences and the new equilibrium | Unresolved practical/emotional/social effects are discharged | A slow scene after any climax. |
| `kiss_off` | The final sharp image, action, line, reversal, or emotional button | It seals tone/meaning after resolution, often with resonance or irony | A mandatory final joke. |
| `cliffhanger` | Ends a unit by withholding imminent outcome under acute pressure | A question demands continuation, common in serial form | Any unresolved ending. |

### Causality test for a turning point

For a candidate anchor ask:

1. What valued condition changed (`safe -> exposed`, `trust -> betrayal`,
   `ignorance -> knowledge`)?
2. Whose objective, strategy, or relationship state changes because of it?
3. What later event would be different if it were removed?
4. Does the screenplay prepare the result by probability/necessity, even if it
   surprises?  If not, consider `coincidence`, `deus_ex_machina`, or leave the
   interpretation open.

## 7. Act and macro-structure lenses

Select at most one `primary_lens`; list credible alternatives.  Never report
all models as simultaneously true merely because they can be overlaid.

| Lens | Shape | Suitable evidence | Caution |
| --- | --- | --- | --- |
| `three_act` (setup / confrontation / resolution) | Baseline and disturbance -> extended pursuit/complication -> final choice and consequences | Two major reorientations, a central pursuit, an ending that answers it | Typical proportions are conventions, not validation. |
| `five_act` / Freytag | Exposition -> rising action -> climax -> falling action -> denouement | Classical/dramatic rise-fall pattern, substantial post-climax unraveling | Freytag describes particular tragic drama; modern screen climax is often near the end. |
| `eight_sequence` | Eight mini-arcs, commonly two per broad act-half | Strong sequence objectives and local peaks | Do not invent eight empty bins. |
| `Save_the_Cat_15` | Opening image, theme, setup, catalyst, debate, break into two, B story, promise, midpoint, bad guys close in, all is lost, dark night, break into three, finale, final image | Explicit genre-engine beats and protagonist choice | A planning beat sheet, not an empirical universal. Use only supported terms. |
| `archplot` | Active protagonist, external conflict, causally connected continuous time, closed ending | Clear goal-driven causality and closure | Do not treat it as a quality hierarchy. |
| `miniplot` | Internal conflict, multiple/passive protagonists, open ending | Relationship/inner change and deliberately limited external causality | “Quiet” does not mean structureless. |
| `antiplot` | Discontinuity, chance, nonlinearity, unresolved/contradictory reality | Form itself challenges conventional causal expectations | Describe the actual organising principle; do not use as a catch-all. |
| `kishotenketsu` | Introduction (`ki`) -> development (`shō`) -> turn/recontextualisation (`ten`) -> conclusion (`ketsu`) | A non-conflict-centred shift or juxtaposition reorganises meaning | Do not retrofit Western act breaks or antagonist conflict. |
| `episodic` | Linked episodes with a cumulative concern, journey, setting, or character | Episodes have local completion; overall arc may be weak/open | Identify the binding principle. |
| `parallel` / `ensemble` | Multiple protagonists/threads whose meanings converge, contrast, or braid | Distinct thread spines and intersections | There may be several local climaxes, not one protagonist. |
| `framed` | Outer story contains/recontextualises inner narrative | Frame changes interpretation or stakes of embedded tale | Track both levels and their joins. |
| `nonlinear` | Story chronology differs materially from disclosure order | Flashbacks, flashforwards, loops, reconstruction, fragmented disclosure | Store both positions; temporal disorder is not a defect. |

### Classical dramatic concepts

Aristotelian analysis adds useful optional labels:

- `complication` — movement from the beginning to the change in fortune;
  `unraveling` — from that change to the end.
- `peripeteia` — reversal; `anagnorisis` — recognition; `pathos` — a painful or
  destructive action.  The first two are strongest when they arise from the
  action rather than arbitrary information or machinery.
- `hamartia` — an error/misjudgment that contributes to catastrophe; do not
  flatten it into “fatal personality defect.”
- `catharsis` — a proposed audience effect (often pity/fear), therefore label
  as an interpretive effect, not an event fact.

## 8. Sequence analysis

Use `sequences` only when there is a real intermediate unit.  A sequence entry
may include:

```json
{
  "id": "seq-03",
  "label": "The investigation closes in",
  "event_ids": ["ev-021", "ev-022", "ev-023"],
  "objective": "...",
  "opposition": "...",
  "escalation": "...",
  "culminating_event_id": "ev-023",
  "outcome": "...",
  "value_shift": "trust -> suspicion",
  "thread_ids": ["plot-a"],
  "evidence_status": "supported_inference"
}
```

Useful sequence families include pursuit, investigation, courtship, training,
trial, infiltration, escape, heist, journey, siege, negotiation, public
performance, and homecoming.  These are descriptive labels, not genres.

## 9. Dramatic engine: goals, conflict, stakes, escalation

| Concept | Recognition | Meta field / question |
| --- | --- | --- |
| External goal | Concrete objective the focal character can pursue | What does the character try to obtain, prevent, prove, escape, protect, or change? |
| Internal need | Capacity or understanding the character lacks and is pressured to develop | Does the external pursuit repeatedly expose a stable limitation? Mark inference. |
| Misbelief | A seemingly protective but false rule that generates self-defeating choice | What earlier-formed belief makes current actions costly? Do not diagnose trauma without evidence. |
| Antagonistic force | Person, group, system, environment, relationship, or self that actively frustrates a goal | Who/what resists, and by what methods or values? An obstacle is not necessarily an antagonist. |
| Central conflict | Durable collision of incompatible wants/values | What cannot both sides have at once? |
| Stakes | Consequence of success/failure at personal, interpersonal, social, existential levels | What changes if the goal is lost? Who bears it? |
| Clock | Deadline, expiring opportunity, pursuit, biological/social time limit | What makes delay costly? Is the deadline enacted or only implied? |
| Gap | Difference between a character's expected outcome and the world’s response | Does each response force a less safe or more costly next action? |
| Progressive complication | Escalation in risk, scope, opposition, intimacy, moral cost, or irreversibility | Is later action genuinely more difficult/different than earlier action? |
| Choice under pressure | A decision revealing value/character when alternatives carry costs | What must be sacrificed, and what does the choice reveal? |

Analyse conflict across `inner`, `interpersonal`, `institutional_or_social`,
`environmental`, and `fate_or_chance` levels.  A complex story can turn several
at once; do not assume external action is primary.

## 10. Character and relationship arcs

These are Meta-level patterns grounded in entity state changes and event
evidence—not substitutes for entity profiles.

```json
{
  "subject_entity_id": "ch-01",
  "arc_type": "positive_change|negative_change|flat_conviction|revelatory|corruptive|cyclical|ambiguous",
  "initial_operating_belief": "...",
  "pressure_points": ["ds-02", "ds-06"],
  "decisive_choice_anchor_id": "ds-08",
  "terminal_state": "...",
  "evidence": [{"event_ids": ["ev-..."], "claim": "..."}],
  "status": "supported_inference"
}
```

| Pattern | Recognition | Caveat |
| --- | --- | --- |
| `positive_change` | The character relinquishes/revises a limiting belief and acts differently under final pressure | Change is not necessarily moral improvement. |
| `negative_change` / `corruptive` | Pressure confirms or deepens destructive value/strategy | Avoid treating tragedy as failed writing. |
| `flat_conviction` | The protagonist changes the world/others by holding a tested core conviction | “Flat” means stable, not shallow. |
| `revelatory` | The key change is perception/knowledge rather than behaviour | Recognition can be the climax. |
| `cyclical` | Ending deliberately returns to/echoes opening with altered or unaltered meaning | State whether cycle is irony, failure, stability, or ambiguity. |

For relationships, analyse `bond_type`, `initial_contract`, `shared_goal_or_value`,
`fault_line`, `turning_events`, `terminal_relation`, and `function` (ally,
foil, love story, mentor bond, family conflict, rivalry).  A B story often
tests or expresses the theme through a relationship, but that is an analysis
to prove, not a required slot.

## 11. Plot braid, subplots, convergence, and counterpoint

The plot layer owns thread membership.  Meta should only describe the pattern:

- `A_story`: main throughline that most directly carries the central dramatic
  question.
- `B_story`: substantial relational/thematic counterline; may offer the
  knowledge, cost, or ally needed for the final movement.
- `C_story` and `subplot`: independent but relevant threads; note their theme,
  pressure, and discharge.
- `braid`: threads alternate and influence each other rather than merely sit
  beside each other.
- `convergence`: separate threads cause or illuminate one decisive movement.
- `counterpoint`: two threads contrast values or outcomes without necessarily
  causally meeting.
- `plant` / `payoff`: earlier introduced element becomes consequential later;
  record setup and payoff events, not just the object.

For each substantial thread, record `onset_event_id`, `escalation_events`,
`crossings_with_threads`, `anchor_coverage`, `discharge_event_id`, and
`unresolved_status`.  A subplot is not defective merely because it ends open;
report its relation to the central question.

## 12. Narration, time, point of view, and audience knowledge

### Time and ordering

| Device | Recognition and representation |
| --- | --- |
| Flashback / analepsis | A later screen segment depicts earlier story time. Store trigger, temporal span, and what present belief it changes. |
| Flashforward / prolepsis | A screen segment depicts later story time. Store whether it promises, warns, or reframes outcome. |
| Frame narrative | An outer situation motivates/colours an inner account. Record frame-to-inner and return-to-frame anchors. |
| Parallel timeline | Two or more chronological strands alternate. Keep a timeline per strand; only claim simultaneity if evidence supports it. |
| Loop / repetition | Repeated event/time with changing awareness, action, or meaning. Record invariant and changed variable. |
| Restricted narration | Audience knows approximately what a focal character knows. Record meaningful exceptions. |
| Omniscient / multi-perspective narration | Audience receives information across multiple focal domains. Analyse how ordering builds comparison or irony. |

### Information effects

- `mystery`: audience lacks an answer and wants discovery.
- `surprise`: audience and character learn consequential information together.
- `dramatic_irony`: audience knows a relevant fact that a character does not;
  tension arises from anticipated collision.
- `suspense`: audience understands an impending risk/outcome but timing or
  escape remains uncertain.
- `reveal`: information changes a decision or meaning; classify its causal
  effect, not only its content.
- `unreliable_account`: report only when the text supplies evidence of conflict
  between account and reality, not because the narrator is unlikeable.

## 13. Hero's Journey: two related but distinct maps

The monomyth is a comparative interpretive framework, **not a universal
screenplay requirement**.  Use it only when the focal character's departure,
transformation, and return genuinely organise the work.  For every stage use
`supported`, `ambiguous`, `absent`, or `not_applicable` and cite anchors.

### Campbell’s 17-stage monomyth

| Movement | Stage | Functional recognition |
| --- | --- | --- |
| Departure | `call_to_adventure` | A disturbance/opportunity invites departure from the ordinary world. |
| Departure | `refusal_of_the_call` | Fear, duty, disbelief, or attachment resists the journey. |
| Departure | `supernatural_aid` | Guidance/resource beyond ordinary capacity appears; may be literal or a strongly analogous aid. |
| Departure | `crossing_first_threshold` | Commitment enters a qualitatively different world/order. |
| Departure | `belly_of_the_whale` | Symbolic severance/initial ordeal marks full departure; optional and often too interpretive to assert. |
| Initiation | `road_of_trials` | Repeated tests, allies, enemies, and adaptation. |
| Initiation | `meeting_with_the_goddess` | Encounter with unconditional value/wholeness; use with care, not as gendered literalism. |
| Initiation | `woman_as_temptress` | Temptation away from path; label only when text truly fits, otherwise use neutral `temptation_or_diversion`. |
| Initiation | `atonement_with_the_father` | Confrontation/reconciliation with ultimate authority; use neutral `authority_confrontation` where apt. |
| Initiation | `apotheosis` | Enlarged understanding/capacity changes the hero’s relation to the quest. |
| Initiation | `ultimate_boon` | The sought gift, solution, knowledge, or achievement is obtained. |
| Return | `refusal_of_the_return` | Resistance to bringing transformation back. |
| Return | `magic_flight` | Return escape/pursuit; optional literal form. |
| Return | `rescue_from_without` | External help enables return. |
| Return | `crossing_return_threshold` | Integrates transformed knowledge into ordinary/social world. |
| Return | `master_of_two_worlds` | Competence/identity spans former and transformed worlds. |
| Return | `freedom_to_live` | Ending releases fear/attachment to the future; interpret cautiously. |

### Vogler’s practical 12-stage screenwriting map

| # | Stage | Function | Recognition cue |
| --- | --- | --- | --- |
| 1 | `ordinary_world` | Baseline before transformation | The protagonist’s normal conditions and lack are legible. |
| 2 | `call_to_adventure` | Disturbance/invitation | A new problem, want, or possibility breaks routine. |
| 3 | `refusal` | Cost and resistance | The character hesitates, avoids, or cannot yet commit. |
| 4 | `meeting_with_mentor` | Preparation or reframing | A figure, relationship, lesson, or resource changes readiness. |
| 5 | `crossing_first_threshold` | Entry/commitment | The character takes an action that makes the journey real. |
| 6 | `tests_allies_enemies` | Learning the special world | Trials reveal rules, opponents, bonds, tactics. |
| 7 | `approach_to_inmost_cave` | Move toward central danger/truth | Planning, infiltration, intimacy, or narrowing toward ordeal. |
| 8 | `ordeal` | Central life/death or identity crisis | Apparent death, devastating loss, core confrontation, or irreversible risk. |
| 9 | `reward` | Gain after ordeal | Prize, reconciliation, knowledge, survival, or changed relation. |
| 10 | `road_back` | Return pressure / recommitment | Consequences of the gain force a final movement. |
| 11 | `resurrection` | Final test that demonstrates change | The protagonist acts under ultimate pressure using transformed understanding. |
| 12 | `return_with_elixir` | Consequence shared with world | New value/knowledge/resource is integrated or offered. |

Do not silently substitute a vaguely similar scene.  For example, a teacher may
be a mentor in a relationship sense without the work having a Hero's Journey.

## 14. Archetypal functions (not fixed character types)

An archetype may be carried by several people, an institution, a temporary
role, or an aspect of the focal character.  It may change hands.  Record
`function`, `carrier_entity_ids`, `active_anchors`, `evidence`, `status`, and
`role_shift` rather than declaring an essential identity.

| Archetypal function | Dramatic role | Recognition cue | Avoid |
| --- | --- | --- | --- |
| `hero` / focal agent | Bears the main journey, choice, or audience alignment | Most consequential choices and costs accumulate around them | Equating protagonist with morally good. |
| `mentor` | Gives preparation, perspective, tool, protection, or challenge | Aid changes readiness/capacity | Labelling every older advisor a mentor. |
| `herald` | Announces disruption or call | Delivers/embodies change that starts motion | Confusing messenger with antagonist. |
| `threshold_guardian` | Tests readiness at a boundary | Blocks or conditions passage into new terrain | Treating any minor obstacle as one. |
| `ally` | Supports, complements, or tests the focal agent | Reliable shared action/knowledge under pressure | Assuming friendship equals plot function. |
| `shadow` | Embodies opposing force, feared possibility, repressed value, or rival goal | Reveals what the focal agent resists/becomes or must confront | Diagnosing a real person; this is narrative function. |
| `shapeshifter` | Produces productive uncertainty in allegiance/identity/meaning | The audience/focal agent has reason to revise trust | Calling a complex character “shapeshifter” solely because they develop. |
| `trickster` | Disrupts hierarchy, releases tension, exposes rigidity, or creates reversals | Comic/chaotic intervention changes the social order | Reducing it to comic relief. |
| `guardian_or_caretaker` | Protects continuity, home, vulnerable value, or dependent relation | Care creates stakes or a moral boundary | A gendered assumption. |
| `temptation_or_siren` | Offers a path away from tested commitment | Choice trades central value for short-term relief/power | Sexualising or gendering the function. |
| `double_or_foil` | Contrasts another viable value/strategy/outcome | Parallel situation reveals difference | Any secondary character. |
| `scapegoat` | Carries communal blame/cost | Group displaces conflict onto a vulnerable party | Asserting motive without group evidence. |

Jungian labels (`persona`, `shadow`, `anima`, `animus`, `self`) are optional
critical lenses, not clinical facts and not required output.  Prefer the
functional vocabulary above unless the text explicitly works at that symbolic
level.

## 15. Theme, premise, value, motif, setup, payoff, and irony

| Concept | Meaning for analysis | Recognition / field |
| --- | --- | --- |
| Subject | Broad topic: family, justice, grief, class, desire | `subjects`; descriptive only. |
| Theme | Recurring question/tension about a subject | State competing values and evidence across threads. |
| Premise | Compact causal proposition, often “trait/value leads to outcome” | `premise_or_argument`; interpretive, not necessarily author intent. |
| Controlling idea | A value changes in a particular direction **because** of a cause | `controlling_idea.claim`; derive from climax + ending, then test earlier evidence. |
| Dramatic question | Answerable story-level question created by the disturbance | What outcome must the climax resolve, refuse, or reframe? |
| Value | A human condition with polar charge: life/death, truth/lie, belonging/isolation, justice/injustice | Track changes, not only abstract words. |
| Motif | Repeated image, object, action, sound, phrase, setting, or situation that gathers meaning | Cite repetitions and evolving function; repetition alone is insufficient. |
| Symbol | Concrete element that carries meaning beyond literal role | Explain textual pattern; do not decode arbitrarily. |
| Plant / setup | Earlier introduced fact, object, rule, relationship, or choice prepared for later consequence | Link setup event(s) to payoff event(s) and state preparation quality. |
| Payoff | Consequential later use/answer of a planted element | Must change outcome/meaning, not just repeat an image. |
| Chekhov's gun | Particularly economical setup/payoff relation | Use descriptively; do not demand all details later pay off. |
| Red herring | Deliberate misleading cue within a mystery/investigation | Require evidence that the work invites and then redirects inference. |
| MacGuffin | Object/goal motivates action more than it matters in itself | Note if its internal specifics are secondary to relationships/conflict. |
| Dramatic irony | Audience knows consequentially more than a character | State who knows what, from when, and anticipated collision. |
| Situational irony | Outcome reverses expected relation through causality | State expectation, outcome, and causal bridge. |
| Poetic justice | Ending distributes consequence in a value-laden fitting way | Interpretive: do not confuse with legal justice. |
| Deus ex machina | Resolution arrives from insufficiently prepared external intervention | Flag only when the intervention resolves a central conflict without causal preparation. |

## 16. Endings and aftermath

Describe the ending along several independent axes:

| Axis | Values |
| --- | --- |
| Plot closure | `closed`, `partially_closed`, `open`, `deliberately_unresolved` |
| Central-question result | `affirmed`, `answered_negative`, `reframed`, `refused`, `ambiguous` |
| Fortune/value direction | `positive`, `negative`, `mixed`, `ironic`, `cyclical` |
| Character movement | `changed`, `unchanged_by_choice`, `changed_by_revelation`, `corrupted`, `unknown` |
| Social/world result | `restored`, `transformed`, `exposed_not_repaired`, `collapsed`, `unknown` |
| Final gesture | `denouement`, `kiss_off`, `cliffhanger`, `callback`, `reframing_reveal`, `image_rhyme`, `none` |

An ending can be open while an emotional arc is complete; it can be closed in
plot while morally unresolved.  Do not score closure as quality by itself.

## 17. Additional useful diagnostics (never automatic verdicts)

Diagnostics point an evaluator to evidence; they do not declare a screenplay
bad.

| Code | Evidence pattern that may justify it |
| --- | --- |
| `unclear_dramatic_question` | No grounded question emerges after the disturbance, or competing questions cannot be ranked. |
| `low_escalation` | Several successive events repeat equivalent tactics/costs without a changed condition. |
| `unearned_turn` | A major reversal/resolution lacks earlier causal preparation in scenes/events. |
| `unresolved_thread` | A substantial introduced plot is neither discharged nor deliberately left open. |
| `orphaned_setup` | A conspicuously emphasised setup has no identifiable later relevance; mark low confidence. |
| `protagonist_agency_ambiguous` | Outcome occurs largely around the focal agent; report form rather than assuming defect. |
| `climax_question_mismatch` | Final peak settles a different question than the one the exposition made central, without a documented reframing. |
| `exposition_overload_risk` | Consecutive explanation delivers material without current conflict/choice; diagnose only from observable pacing/function. |
| `perspective_gap` | A claimed audience-information effect is unsupported by narration order. |
| `framework_overfit_risk` | Label selected mainly by expected position, not causal/function evidence. |

## 18. Agent procedure

1. Read the ordered **events** and their `before -> after` changes; build a
   compact change ledger before applying any theory label.
2. Identify baseline, disturbance, central question(s), focal agents, central
   opposition, stakes, and clocks.  Separate direct evidence from inference.
3. Mark candidate anchors with causal tests.  Retain alternatives where two
   events plausibly perform the same function.
4. Group genuine event runs into sequences; then choose the **least forcing**
   macro lens.  `ambiguous` is better than an invented act break.
5. Analyse exposition delivery, thread braid, information order, character/
   relationship changes, setups/payoffs, and ending consequences.
6. Apply Hero's-Journey stages and archetypal functions **last** and only where
   they increase explanatory power.  Explicitly record absent/not-applicable
   stages rather than backfilling them.
7. Validate every reference, positions, act contiguity where appropriate, and
   contradictions with lower nodes.  Emit concise evidence-linked JSON.

### Final preflight checklist

- Does every anchor explain a changed value, choice, strategy, knowledge, or
  consequence?
- Would removing its cited event materially alter the claimed structure?
- Is screen order distinguished from chronology where needed?
- Are act labels based on function rather than percentage?
- Is the selected lens the simplest adequate description, with alternatives?
- Are protagonist, opposition, stakes, and theme treated as evidence-based
  patterns rather than stock roles?
- Are every Hero's-Journey/archetype claim optional and status-labelled?
- Are all cross-layer claims references rather than copied summaries?
- Does the ending analysis answer the actual dramatic question or document its
  deliberate reframing/open status?

## 19. Source notes and scope

This cheat sheet synthesises traditional poetics, screenwriting vocabulary, and
the reviewed `screenwriting-skills` collection.  The latter explicitly combines
Field, Snyder, McKee, Hoxter, Hicks, Chinese dramatic practice, character
conflict, premise/theme work, Chekhov, and Ozu; its skill texts are useful
craft guidance, not a universal ontology.  The Hero's-Journey material
distinguishes Campbell's comparative 17-stage monomyth from Vogler's practical
12-stage adaptation.

Useful public starting points:

- [Aristotle, *Poetics* (MIT Classics Archive)](https://classics.mit.edu/Aristotle/poetics.2.2.html)
- [Papalampidi, Keller & Lapata (2019), *Movie Plot Analysis via Turning Point Identification*](https://arxiv.org/abs/1908.10328)
- [jtydhr88/screenwriting-skills](https://github.com/jtydhr88/screenwriting-skills)
- [StoryTree Default Pipeline](00-DEFAULT-PIPELINE.md)
- [StoryTree structure and provenance rules](storytree-structure.md)

Historical frameworks contain culturally specific and sometimes dated terms.
Store them as named lenses, use neutral functional alternatives where possible,
and never use them to diagnose real people or declare one narrative tradition
inferior to another.
