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

### The scene-turn ledger

The most reliable input to macro analysis is a compact ledger of local changes.
For every scene or event, state the *initial charged condition*, the pressure,
the tactic, the outcome, and the *terminal charged condition*.  “They talk in a
café” is a setting description; “a daughter tries to obtain forgiveness,
conceals a fact, and leaves with the relationship changed from guarded contact
to open rupture” is a dramatic unit.

| Field | Question the agent should answer | Example of a useful value axis |
| --- | --- | --- |
| `focal_agent` | Whose immediate objective gives this unit its dramatic direction? | A detective, a couple, a family, an institution, or no single agent. |
| `objective` | What does the focal agent want *in this unit*, not in the whole film? | Obtain access, prevent disclosure, win trust, escape, delay, expose. |
| `opposition` | Who/what prevents the objective and by what method? | Rival, institutional rule, weather, contradictory desire, missing knowledge. |
| `tactic_shift` | What changes when the first tactic fails? | Charm -> threat; concealment -> confession; flight -> cooperation. |
| `entry_value` | What condition is initially positive/negative/unstable? | Trust, safety, status, freedom, knowledge, belonging, moral integrity. |
| `exit_value` | What is materially different at the end? | Trust -> suspicion; safe -> exposed; ignorance -> knowledge. |
| `cost_or_irreversibility` | What cannot simply be reset? | Evidence is released, a promise is made, a bridge is burned, a death occurs. |
| `causal_outgoing_edge` | Which later choice or condition exists because of this one? | The failed negotiation makes the illegal plan necessary. |

The ledger is a *derived analytic view*.  It must point to existing scene/event
data and never replace it.  It makes “nothing happens” testable: a scene can
be atmospheric, comic, or observational and still be valuable, but an agent
should not call it a plot turn without a traceable change.

### Value shifts are multi-dimensional

Several values can turn at once, and the same event can be positive for one
character and disastrous for another.  Record the affected perspective instead
of flattening the event to “good” or “bad.”  Useful polarity families include:

- **External condition:** life/death, safety/danger, freedom/confinement,
  wealth/privation, order/chaos, success/failure.
- **Interpersonal condition:** trust/betrayal, intimacy/distance,
  belonging/exile, authority/subordination, loyalty/abandonment.
- **Epistemic condition:** truth/lie, knowledge/ignorance, certainty/doubt,
  recognition/misrecognition.
- **Ethical condition:** justice/injustice, integrity/compromise,
  responsibility/evasion, care/cruelty.
- **Inner condition:** agency/helplessness, self-acceptance/shame,
  hope/despair, coherence/fragmentation.

Avoid treating a value map as a universal sentiment score.  A criminal gaining
power may be a positive tactical change and a negative ethical one; the
analysis should say which axis and whose perspective it means.

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

### Modes of exposition and their dramatic effect

Exposition is strongest when it also creates present-tense pressure.  The agent
should identify *how* a fact reaches the audience, because delivery method
changes function and may later explain a reveal.

| Delivery mode | What it does well | Risk / distinction |
| --- | --- | --- |
| `dramatised_action` | Lets a rule, relationship, skill, or wound be inferred from conflict | Do not invent a rule merely because an action is visually striking. |
| `goal_conflict` | Explains history while people pursue incompatible immediate aims | Often preferable to treating dialogue as “information dump.” |
| `selective_dialogue` | Makes status, ideology, relationship, and necessary facts available efficiently | A character saying something does not prove it is true. |
| `object_or_setting` | Encodes prior life through costume, space, document, ritual, technology, or damage | Record only if later action relies on the information. |
| `demonstration` | Establishes genre rule by an instance of it | Distinguish a general rule from a one-off exception. |
| `flashback_or_embedded_account` | Supplies prior causal information under a present trigger | Track speaker reliability and what the return changes. |
| `voice_over_or_title_card` | Gives framing, time, attitude, or facts not otherwise dramatised | It may be ironic or partial, not neutral truth. |
| `withholding` | Preserves mystery, surprise, or restricted perspective | Absence is intentional only when later form/evidence supports that reading. |

The useful question is not “has the film explained enough?” but “what must the
audience know *now* in order to understand the objective, the risk, the irony,
or the coming change?”  A later reveal can be fair when the earlier work gives
the audience meaningful questions and does not contradict established facts.

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

### Anchor relationships and permissible overlap

One event can legitimately perform several functions.  For example, a
discovery can be both `recognition` and `midpoint`; a final confrontation can
be `crisis`, `climax`, and `reversal`; a final image can be both `denouement`
and `kiss_off`.  Do not create duplicate narrative facts.  Represent one
anchored event with several `functions`, explaining each separately.

Conversely, do not collapse distinct events merely because a beat-sheet would
put them near each other.  The inciting disturbance (a problem enters the
protagonist’s life) and the commitment (the protagonist chooses a costly
response) are often separate.  The crisis (the final value-choice) and climax
(the action that settles the question) are also often separate.

An anchor is **global** only if it reorients the principal dramatic question or
multiple major threads.  A local plot turn belongs in the Plot projection or a
sequence rather than being inflated into a film-level `act_break`.

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

### Structural form by medium and seriality

The same vocabulary can analyse a feature, episode, television season, play,
or short, but the unit of resolution changes.  `screenplay_form` and
`analysis_scope` must be set before interpreting a cliffhanger or climax.

| Form | Common organising behaviour | What the Meta agent should record |
| --- | --- | --- |
| Short film | One concentrated situation/value shift; exposition may be compressed or deferred | Whether the ending reframes the setup; do not demand subplots or three full acts. |
| Feature | One dominant question can hold several sequences and substantial aftermath | Main spine plus secondary threads; possible three-/five-act or other lens. |
| Television episode | Teaser, act-outs, and a local episode question may coexist with a season arc | `episode_arc` versus `serial_arc`; mark act-out cliffhangers separately from final resolution. |
| Pilot | Must establish repeatable engine as well as local story | `series_engine`, ensemble roles, future-question hooks; do not call all open threads defects. |
| Season / serial | Multiple episode climaxes can lead to an arc climax | Scope anchors to season level and retain episode boundaries. |
| Stage play | Entrances/exits, intervals, scenes, and five-act traditions may shape structure | Separate actual textual turn from externally imposed interval. |
| Anthology | Each segment may have an independent core, joined by a theme/frame | Segment-level analyses plus the frame/binding principle. |

For a serial work, do not use `unresolved_thread` when the text clearly
defers resolution to a later episode/season.  Use `deferred_to_scope` and name
the current scope instead.

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

### Sequence escalation patterns

An agent should state *how* a sequence rises rather than merely labelling it
“more intense.”  Common patterns are:

- `obstacle_ladder`: each attempt encounters a stronger or differently shaped
  barrier;
- `narrowing_options`: legal, safe, or relational alternatives disappear;
- `expanding_scope`: private trouble affects family, institution, community,
  or world;
- `deepening_cost`: tactics begin to compromise a relationship, value, or
  self-image;
- `information_reversal`: the goal stays but its true conditions are revealed;
- `time_compression`: a clock or pursuit makes delay progressively impossible;
- `role_reversal`: pursuer becomes pursued, teacher becomes learner, dependent
  becomes protector, or power changes hands;
- `convergence`: independent threads begin to causally collide.

The absence of a rising ladder is not automatically a weakness: a meditative,
episodic, or anti-plot work may organize interest through contrast, recurrence,
observation, or accumulating thematic resonance instead.

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

### Agency, causality, and coincidence

`protagonist_agency` describes the relation between a focal agent’s choice and
the causal chain; it is not a moral score.  Use `high`, `mixed`, `low`, or
`distributed` with evidence.

- `high`: important later conditions are consequences of the character’s
  choices under pressure.
- `mixed`: external events create the problem, but consequential choices shape
  response and ending.
- `low`: events mainly happen to the focal character; this may be appropriate
  to tragedy, social realism, horror, or an intentionally powerless viewpoint.
- `distributed`: an ensemble, institution, group, or several protagonists share
  causality; do not manufacture one “real” hero.

Coincidence can credibly *create* a problem, especially in an inciting
disturbance.  It is more structurally suspicious when it solves the central
problem without earlier causal preparation.  The agent should document the
causal chain, not apply this as a blanket prohibition.

### Stakes map and escalation graph

Where the evidence supports it, Meta can encode a compact cross-event map:

```json
{
  "stakes_map": {
    "focal_question": "Can the family remain together without accepting the lie?",
    "layers": [
      {"level": "personal", "at_risk": "self-respect", "event_ids": ["ev-014"]},
      {"level": "interpersonal", "at_risk": "trust within the family", "event_ids": ["ev-019"]},
      {"level": "social", "at_risk": "public standing", "event_ids": ["ev-027"]}
    ],
    "escalation_edges": [
      {"from_event_id": "ev-014", "to_event_id": "ev-019", "change": "private concealment becomes relational betrayal"}
    ]
  }
}
```

This is not a demand that every film have three escalating scales.  It is a
way to explain visible escalation without hiding it in general prose.

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

### Characterisation versus dramatic character

Distinguish a character’s **characterisation** (occupation, costume, habit,
biography, manner of speech) from their **dramatic character** (the choice they
make when values conflict and consequences are real).  Both belong in the
Entity layer; Meta uses them only to explain recurring pressure and change.

For each focal character, an agent may ask:

1. What does this person pursue when the story begins?
2. What do they believe will protect or complete them?
3. What contradiction, blind spot, duty, attachment, or value makes the goal
   costly?
4. Which events test that operating rule rather than merely inconvenience them?
5. At the crisis, what choice is made between meaningful costs?
6. What final action demonstrates continuity, revision, collapse, or an
   unresolved relation to that rule?

This produces an analytical arc without asserting authorial intention or
medical/psychological fact.

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

### Plot-thread function taxonomy

In addition to A/B/C priority, classify what a thread *does* for the whole:

| Thread function | How it supports the whole | Recognition test |
| --- | --- | --- |
| `causal_spine` | Carries the actions most directly answering the central question | Removing it collapses the principal chain. |
| `thematic_counterpoint` | Tests the same value conflict through different people/outcome | Its ending changes the meaning of the A story. |
| `relationship_mirror` | Makes an internal or social issue concrete in a bond | Turning events force intimacy, loyalty, separation, or repair. |
| `pressure_source` | Supplies recurring opposition, deadline, institutional force, or consequence | It raises cost/constraint across other threads. |
| `world_context` | Shows the wider system, history, or community affected by action | It changes interpretation or stakes rather than merely adding colour. |
| `mystery_information` | Controls discovery and recontextualisation | It supplies questions/answers that alter choices. |
| `relief_or_rhythm` | Varies tension, tone, and pace while retaining meaningful relation | It returns in a patterned way and affects the whole’s emotional shape. |

“Comic relief” is not automatically disposable.  A comic thread can provide
counterpoint, expose hierarchy, carry theme, or make later pathos legible.

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

### Point of view, focalisation, and sympathy

Record three distinct things:

- **Narrative access:** whose perceptions, memories, and withheld information
  shape what the audience can know?
- **Dramatic focalisation:** through whose immediate objective and risk does a
  sequence create pressure?
- **Audience alignment:** with whom is the audience encouraged to spend time,
  concern, or identification?

They often overlap, but not always.  A film can focalise a villain’s plan while
aligning sympathy elsewhere; an ensemble can distribute access and concern.
Do not reduce point of view to camera presence or screen time alone.

### Mystery, suspense, surprise: a practical test

For every claimed information effect, make a small knowledge table:

| Time | Audience knows | Focal character knows | Consequence anticipated |
| --- | --- | --- | --- |
| Before event | ... | ... | ... |
| After disclosure | ... | ... | ... |

If the audience knows a threat that the character does not and waits for them
to encounter it, `dramatic_irony`/`suspense` may be supported.  If neither
knows and both discover together, it is nearer `surprise`.  If the audience
lacks an answer and pursues its solution over time, it is `mystery`.  These can
coexist, but they should not be asserted as decorative labels.

## 12a. Genre, tone, and the promise of premise

Genre is an audience-facing contract about sources of interest and likely
pressure, not a substitute for a plot.  A screenplay can be hybrid; list
`primary`, `secondary`, and `confidence` rather than forcing a single shelf
label.  Meta should record the observable **genre engine**—the recurring kind
of question, obstacle, experience, or payoff promised by early events.

| Genre engine | Typical dramatic question / evidence to seek | Structural caution |
| --- | --- | --- |
| Mystery / detective | What happened, who did it, why, and can truth be proved? Evidence is discovered, tested, reinterpreted. | A revelation must alter causality/meaning; do not call all delayed facts clues. |
| Thriller | Can danger be identified, avoided, or overcome before time runs out? Threat, clock, and narrowing options recur. | “More danger” needs changing proximity/cost, not volume alone. |
| Horror | Can characters survive/contact/understand a destabilising threat? Rules, violation, dread, and exposure are patterned. | Fear may be atmospheric; do not demand a heroic victory. |
| Romance | Can a desired bond be formed, recognised, repaired, or ethically refused? Relationship turns carry primary stakes. | A partnership is not necessarily romance; identify mutual emotional contract. |
| Comedy | Can a social/identity contradiction be exposed and reorganised? Misrecognition, escalation, reversal, and restoration may drive it. | Do not label any humorous scene “comic structure.” |
| Tragedy | How does a choice, error, value conflict, or social force lead to irreversible loss? Reversal/recognition/catastrophe may concentrate. | A sad ending alone is not tragedy. |
| Melodrama | How do moral/emotional stakes become legible through heightened relationships, sacrifice, and reversal? | Heightened expression is a style, not evidence of shallowness. |
| Action / adventure | Can a goal be reached amid physical opposition, traversal, and escalating set-pieces? | Set-pieces require causal objective/outcome to be turns. |
| Heist / caper | Can an operation be planned, assembled, executed, and survive complication? | The “plan” may be a false surface; record reversals of competence/loyalty. |
| Coming-of-age | Can a young focal character revise identity, belonging, or responsibility? | Biological age is not enough; track an enacted transition. |
| Social realism | How do institutions/material conditions shape agency and relationships? | Limited agency can be central form rather than deficient plotting. |
| Musical | How do performance numbers externalise desire, conflict, fantasy, community, or transformation? | A number may advance state, reveal inner conflict, or pause action deliberately. |

Tone (`comic`, `tragic`, `romantic`, `satirical`, `ironic`, `melancholic`,
`suspenseful`, etc.) is a pattern of treatment and audience effect.  It is not
proven by one joke, death, or dark image.  Record shifts when a tonal turn
reframes the meaning of prior material.

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

### How to use the monomyth responsibly

The Hero's Journey is most informative when it explains a *pattern of change*
that ordinary act vocabulary misses: departure from a familiar order, repeated
tests in a changed order, an ordeal/revelation, and a difficult integration of
what was gained.  It is less useful for a procedural investigation, domestic
ensemble, social panorama, static-character comedy, tragedy without return, or
works built around collective rather than individual agency.

The following distinctions prevent common false positives:

| Do not equate | Why | Better question |
| --- | --- | --- |
| `inciting_incident` with `call_to_adventure` | A disturbance can happen without inviting a departure or quest. | Is a new path/world explicitly or functionally offered? |
| `act_break` with `crossing_first_threshold` | A plot reorientation can occur inside the same social/world order. | Has return to the former mode become materially difficult or impossible? |
| any hardship with `ordeal` | Trials can be preparatory and reversible. | Is this a central confrontation with death, identity, loss, or irreversible cost? |
| any prize with `reward` / `boon` | A tactical win may not transform the journey. | Does the gain solve, expose, or reframe the core quest? |
| final fight with `resurrection` | Spectacle alone does not demonstrate transformed action. | Does the final test require the character to act from changed understanding? |
| an ending at home with `return_with_elixir` | Physical return need not integrate or share a transformed value. | What, if anything, is brought back into the original world? |

For nonconforming work, store a short explanation such as: “Hero's-Journey
lens not applicable: the ensemble has no singular departure-return arc; the
organising form is parallel social counterpoint.”  This is more useful than a
table full of forced `absent` stages.

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

### Role movement and character systems

Archetypal function is time-dependent.  A seeming `mentor` can become a
`shadow`; an apparent `threshold_guardian` can become an `ally`; a `trickster`
can expose the rigidity of both hero and antagonist.  Record this as a role
transition with the evidence that revises the audience/focal-character model:

```json
{
  "function": "shapeshifter",
  "carrier_entity_ids": ["ch-07"],
  "role_shifts": [
    {
      "from": "ally",
      "to": "antagonistic_force",
      "anchor_id": "ds-05",
      "basis": "The cited event reveals an incompatible goal and changes the protagonist's strategy."
    }
  ],
  "status": "supported_inference"
}
```

Character systems can also be analysed without archetypal language:

- `foil`: makes a focal character’s value or strategy visible by contrast;
- `double`: offers a parallel possible self/outcome, often more structurally
  precise than “shadow”;
- `confidant`: receives information that externalises an inner conflict;
- `gatekeeper`: controls access to a resource, institution, or social world;
- `witness`: observes, validates, misreads, or records a consequential action;
- `chorus_or_community`: supplies a collective norm, commentary, or pressure;
- `catalyst`: changes other characters while undergoing little change itself.

These labels require proof of function over multiple events.  A character may
have no named system role and still be dramatically essential.

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

### Theme analysis: an evidentiary method

Theme is not a one-word topic and not a moral lesson imposed on a film.  Start
with repeated **value conflict**, not with an abstract noun.  For example,
instead of reporting “theme: family,” identify a proposition or unresolved
question such as “Does loyalty to family require complicity, or can care demand
truth?”  Then test it against actions in different threads.

1. List the values that turn repeatedly (for example, belonging versus
   independence; truth versus protection; justice versus mercy).
2. Identify the strongest proponents of competing positions and the costs each
   position produces.
3. Examine the crisis, climax, and denouement: what does the ending enact,
   complicate, punish, reward, or leave unresolved?
4. State a `controlling_idea` only when the causal ending pattern is clear;
   otherwise keep an open `thematic_question` or competing readings.
5. Cite cross-thread evidence.  One speech can articulate a theme but does not
   prove the whole work adopts it.

Useful output fields:

```json
{
  "thematic_argument": {
    "questions": ["..."],
    "value_conflicts": [
      {"positive": "truth", "negative_or_cost": "belonging", "event_ids": ["ev-...", "ev-..."]}
    ],
    "positions": [
      {"carrier": "ch-01", "position": "...", "tested_by": ["ds-04", "ds-08"]}
    ],
    "ending_relation": "affirms|qualifies|ironises|refuses_to_resolve|ambiguous",
    "status": "supported_inference"
  }
}
```

### Motif and image-pattern analysis

Do not turn every repeated object into a symbol.  A motif becomes analytically
useful when recurrence changes, contrasts, or accumulates meaning in relation
to plot/character/value shifts.  Record:

- `literal_function`: what the image/object/action is in the story world;
- `occurrences`: ordered event/scene references, not a quotation collection;
- `variation`: what changes in context, owner, state, or associated value;
- `structural_function`: setup, callback, transition marker, memory trigger,
  irony, or final image rhyme;
- `interpretive_reading`: optional, confidence-labelled, grounded in pattern.

An `image_rhyme` links opening and ending through a transformed or echoed image
without requiring a literal repetition.  It can make the final state legible,
but is not required for a coherent ending.

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

### Resolution, denouement, and kiss-off in more detail

The **resolution** is the causal settling of a central question: an arrest,
choice, separation, reconciliation, death, departure, public disclosure,
acceptance, or refusal may do it.  The **denouement** lets consequences become
legible: Who now knows what? Which relationship/state/world order remains?
What costs have not vanished?  The **kiss-off** is a final concise gesture that
may crystallise or complicate the meaning after the practical resolution.

The three can be one event or substantially separated.  A serious analysis
should state their relationship, for example:

- “The climax resolves the external pursuit; the denouement shows that the
  relationship cost remains; the final image ironises apparent victory.”
- “No conventional denouement: the abrupt cut is a deliberate open-ending
  gesture, leaving the central ethical question unresolved.”
- “The post-climax revelation reclassifies the prior apparent resolution as a
  false ending and creates a second, shorter causal movement.”

Avoid calling the final chronological scene the climax simply because it is
last.  Conversely, do not refuse a quiet final recognition as climax merely
because there is no spectacle.

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

### Quality dimensions for a dramatic-structure node

Use this rubric to evaluate a generated `meta.dramatic_structure` node.  It is
for evidence-based review, not a substitute for the existing StoryTree layer
rubrics.

| Dimension | A strong node | Common failure |
| --- | --- | --- |
| Grounding | Every major claim resolves to scenes/events and accurately describes their change | Elegant labels with no source references or references that do not support the claim. |
| Causal reasoning | Turns explain altered objectives, tactics, stakes, knowledge, or outcomes | Beat-sheet positions are mistaken for causality. |
| Lens fit | Selects the least-forcing form and names alternatives/ambiguity | Treats three acts or Hero's Journey as universal. |
| Scope control | Distinguishes local sequence/plot turns from global anchors and current scope from serial deferral | Inflates every obstacle into a midpoint or treats season hooks as defects. |
| Temporal accuracy | Keeps discourse and chronology distinct; represents frames/parallel stories | Sorts flashbacks as if they were present action. |
| Character/relationship discipline | Identifies enacted choices and arc pressure without mind-reading | Diagnoses people, attributes unsupported motives, or calls every friend a mentor. |
| Theme and imagery restraint | Derives patterns across events and permits ambiguity | Reduces theme to a topic or makes every prop a symbol. |
| Usefulness | A later adapter or human can navigate the film, inspect claims, and compare alternatives | Verbose plot retelling or opaque theoretical jargon. |

## 17a. Failure modes and repair policy

The system should not silently “repair” a screenplay analysis by inventing a
classical pattern.  When a required property cannot be established, preserve
the uncertainty in JSON and emit a narrow diagnostic.

| Failure mode | Why it happens | Correct repair |
| --- | --- | --- |
| Position anchoring | Model learns page-percentage heuristics | Re-run anchor reasoning from event value/strategy changes; retain position as only a secondary cue. |
| Summary masquerading as analysis | Long text repeats events without relating them | Require `change`, `function`, and causal outgoing effect for every anchor. |
| Single-hero bias | Framework priors ignore ensembles/institutions | Use `distributed` agency, thread-level focal agents, and ensemble/parallel lens. |
| Over-psychologising | Model fills “need/wound/misbelief” fields speculatively | Require explicit enactment or repeated evidence; otherwise omit/mark ambiguous. |
| Archetype overfit | Stock labels are easy to generate | Apply archetypal pass last and demand role evidence over time. |
| False precision | Exact percentages/confidence simulate certainty | Use bounded confidence and uncertainty reasons; omit numerical precision unsupported by evidence. |
| Chronology collapse | Events are sorted by disclosure despite flashbacks | Preserve `screen_position`, `story_position`, and separate timeline branches. |
| Duplicate evidence | Same event is rewritten into every Meta field | Reference shared anchor IDs and offer short field-specific rationale only. |
| Premature defect diagnosis | Atypical form is treated as bad structure | First identify lens, scope, genre engine, and intended information design. |

## 17b. Minimal versus rich output

The agent should choose the smallest valid representation.  A short,
linear, tightly focused film may need only a core question, five anchors, two
acts or a simple form label, an exposition note, and ending relation.  A long
ensemble mystery may need multiple timelines, sequence clusters, a plot braid,
information effects, several local climaxes, and alternatives.

Minimum viable node:

```json
{
  "analysis_scope": {"primary_lens": "three_act", "narration_mode": "linear"},
  "dramatic_core": {"central_dramatic_question": "..."},
  "anchors": [
    {"kind": "inciting_incident", "event_ids": ["ev-..."], "change": "..."},
    {"kind": "commitment", "event_ids": ["ev-..."], "change": "..."},
    {"kind": "midpoint", "event_ids": ["ev-..."], "change": "..."},
    {"kind": "crisis", "event_ids": ["ev-..."], "change": "..."},
    {"kind": "climax", "event_ids": ["ev-..."], "change": "..."}
  ],
  "ending": {"central_question_result": "..."}
}
```

Do not pad this minimum with `Hero's Journey`, motif, or diagnostics fields
unless they add grounded explanatory value.  A rich node must remain an index
into StoryTree, not become a second free-form screenplay summary.

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

## 19. Core conflict, pressure, and the constricted option-space

This section adds a stricter causal vocabulary for the analysis of conflict and
suspense.  It is compatible with the existing Event and Meta layers: every
claim must be a derived pattern over goals, resistance, choices, state changes,
and audience information—not a free-floating label.

### The core conflict is not just the loudest conflict

A screenplay can contain fights, arguments, romantic setbacks, institutional
barriers, comic frictions, and subplots without all of them being the **core
conflict**.  The core conflict is the collision whose outcome most directly
settles, transforms, or deliberately leaves open the main dramatic question.
It normally has a focal agent or distributed focal group, a continuing goal or
value, a credible opposing force, and a chain of consequences that reaches the
climax.

| Question | Evidence required | Do not mistake it for |
| --- | --- | --- |
| What does the focal agent/group seek, preserve, escape, prove, expose, or become? | Repeated scene/event objectives and choices | A one-scene desire. |
| What force, value, system, person, or self-conflict resists it? | Counteractions, constraints, incompatible aims, relation changes | A colourful minor obstacle. |
| Why can it not be solved once and forgotten? | Binding constraint, escalating cost, clock, duty, dependency, consequence | Mere narrative delay. |
| What development would collapse if this conflict vanished? | Downstream causal edges and the climax question | A local subplot that does not change the main line. |

Use `core_conflicts` as an array, not a singular field, for ensemble and
parallel work.  Each entry should say its scope (`global`, `thread`, `episode`,
`relationship`, `institutional`) and relation to any central question.

```json
{
  "core_conflicts": [
    {
      "id": "cc-01",
      "scope": "global",
      "focal_entity_ids": ["ch-01"],
      "goal_or_value": "...",
      "opposition": "...",
      "binding_constraints": ["bc-01"],
      "central_question": "...",
      "escalation_event_ids": ["ev-...", "ev-..."],
      "settlement_anchor_id": "ds-...",
      "status": "supported_inference"
    }
  ]
}
```

### Goal, obstacle, coercion, constraint, pressure, suspense

These terms must remain distinct:

| Term | Exact meaning | Strong recognition cue |
| --- | --- | --- |
| `goal_or_need` | A desired state, object, relation, action, identity, or value | A character repeatedly acts, sacrifices, or speaks to obtain/protect it. |
| `obstacle` | Something makes a goal harder to reach | A resource, opponent, rule, environment, or knowledge gap blocks a tactic. |
| `conflict` | Goals/values/courses of action are incompatible | Two active positions cannot both prevail without a change/loss. |
| `coercion` | A power demands an unwanted action or choice | Sanction, threat, dependency, force, institutional order, blackmail. |
| `reactance` | Resistance motivated by lost autonomy | After restriction, the focal agent also seeks to reclaim freedom/control. |
| `constraint` | The future option-space becomes smaller | Time, injury, exposure, loss, promise, resource depletion, irreversible action. |
| `action_pressure` | Deferral/inertia now has a real cost | The agent must choose, act, or accept an escalating loss. |
| `suspense` | Anticipation of uncertain consequential outcomes | Audience can foresee more than one meaningful future and wants the answer. |

An obstacle without a meaningful cost may be only friction.  A conflict without
a constraint may be indefinitely postponable.  Coercion may cause no dramatic
resistance if it happens to match the person's desire.  Suspense needs an
open future; an outcome that is virtually certain can still be tragic or
beautiful, but has less uncertainty-based tension.

### Binding constraints / the crucible

Use `binding_constraints` to explain why characters remain in a painful
conflict rather than simply leaving.  Valid evidence can include love, kinship,
care, work, debt, law, oath, shared mission, geography, physical confinement,
reputation, dependency, a deadline, a prior act's consequence, or a social
order.  A constraint must be situated in this screenplay, not a generic claim
that “family is complicated.”

```json
{
  "binding_constraints": [
    {
      "id": "bc-01",
      "kind": "dependency",
      "claim": "The focal character cannot abandon the conflict without exposing a dependent person to the stated harm.",
      "event_ids": ["ev-..."],
      "lost_options": ["leave_without_cost", "delay_decision"],
      "pressure_effect": "The conflict must be answered now rather than deferred.",
      "status": "observed"
    }
  ]
}
```

### Escalation versus repetition

For every major conflict run, ask whether each response changes the next
available action.  Escalation can be external (risk, scale, proximity,
opposition), interpersonal (trust, loyalty, status, intimacy), ethical (moral
cost), epistemic (new knowledge changes strategy), or internal (a former
self-protective rule becomes untenable).

Flag `static_conflict_risk` only when repeated moves remain at the same value,
tactic, leverage, and consequence.  Flag `unearned_escalation_risk` when a
leap in intensity has no prior bridge of motive, action, or circumstance.  A
ritual, farce, or intentionally oppressive repetition can be deliberate form;
then describe the pattern and its effect instead of declaring a failure.

## 20. Dilemmas, causal engines, and the Story Mind perspective map

### High-stakes dilemma

A genuine dilemma is more than “a difficult decision.”  It has two or more
credible options, each tied to a meaningful value/goal, where selecting one
destroys or seriously compromises the value attached to another.  The agent
must explain why the decision cannot be delayed or solved by an already
established painless third option.

| Required property | Test |
| --- | --- |
| Competing legitimate claims | Could an intelligent, humane person credibly defend each path from the screenplay's perspective? |
| Material loss | Does option A actually sacrifice the core benefit of B, and vice versa? |
| Constraint | What deadline, coercion, dependency, prior action, power relation, or physical limit prevents postponement? |
| Irreversible causality | Does the decision alter the state and force later events/aftermath? |
| Embodiment | Are the competing values carried by real characters, relations, institutions, and actions—not only abstract dialogue? |

```json
{
  "dilemmas": [
    {
      "id": "dl-01",
      "scope": "global|thread|relationship",
      "focal_entity_ids": ["ch-..."],
      "option_a": {"value_or_goal": "...", "loss_if_chosen": "..."},
      "option_b": {"value_or_goal": "...", "loss_if_chosen": "..."},
      "constraint": "...",
      "why_deferral_fails": "...",
      "decision_anchor_id": "ds-...",
      "consequence_event_ids": ["ev-..."],
      "status": "observed|supported_inference"
    }
  ]
}
```

### Core inequity: “is” versus pressured “should”

An optional `core_inequity` states the gap that a film repeatedly pressures:
the actual situation and the required/desirable/feared alternative.  It is not
an assertion of objective morality and must preserve competing viewpoints.

```json
{
  "core_inequity": {
    "actual_condition": "...",
    "pressured_ideal_or_need": "...",
    "value_conflict": ["...", "..."],
    "focal_scopes": ["individual", "relationship", "institution"],
    "event_ids": ["ev-..."],
    "status": "supported_inference"
  }
}
```

Examples of *forms* of question include order/chaos, autonomy/obligation,
justice/mercy, truth/protection, belonging/independence, care/self-preservation,
and dignity/collective survival.  Always restate them in screenplay-specific
language; never reduce a culturally situated story to a generic label alone.

### Optional causal-engine patterns

The following labels help explain a whole pattern only when multiple causal
links support it:

- `value_domino`: a value-led choice creates collateral cost, requiring a
  harder version of the same or revised value in the next step;
- `stress_test`: escalating conditions test whether an ideology, strategy,
  relationship, or system can survive;
- `fractal_echo`: one conflict is echoed at individual, relationship, and
  societal scales, with meaningful structural linkage;
- `inversion_helix`: one figure's method transforms another, whose later
  changed stance forces the first to confront their original belief.

Do not infer an engine from repeated vocabulary alone.  The output must name
the events that form each causal edge.

### Dramatica-inspired four perspectives: optional and partial by design

This is an analytical lens, not a required StoryTree layer.  It can clarify a
work that examines one problem through several views:

| Perspective | Practical question | Candidate sources |
| --- | --- | --- |
| Objective Story (`they`) | What shared-system conflict/action affects the world of the story? | Events, plots, institutions, ensemble state. |
| Main Character (`I`) | What subjective pressure, blind spot, commitment, or coping pattern does a focal agent live through? | Entity arc, scene minds, choices under pressure. |
| Impact Character (`you`) | Who/what persistently embodies an alternative approach that challenges the focal agent? | Repeated contrast and relationship turns. |
| Relationship Story (`we`) | How does the bond between focal and impact forces change independently of their external task? | Shared events, relation state, mutual decisions. |

Use a `perspective_map` only when it adds explanatory value.  An ensemble may
have several focal pairs; a procedural may have no Impact Character; a film can
be `partial`, `weak`, or `not_applicable`.  Domains such as `situation`,
`activity`, `fixed_mind`, and `manipulation` are broad problem lenses and must
not be treated as psychological diagnoses.

## 21. Premise, character pressure, audience engagement, and contract

### Premise / controlling proposition

A premise is an optional causal compression of what the story demonstrates
about a character/value under its core conflict.  A useful form is:

```text
character trait, commitment, or value + tested conflict -> enacted consequence
```

It is neither a plot summary, genre label, author biography, nor compulsory
moral.  A work with unresolved or plural viewpoints may support only a
`thematic_question` or `thematic_constellation`, and ensemble work may have
multiple thread-level propositions.

When a proposition is emitted, validate it in this order:

1. infer a candidate from climax plus aftermath;
2. locate earlier events that make the causal chain probable;
3. test whether major threads support, complicate, or contradict it;
4. state the ending relation (`affirms`, `qualifies`, `ironises`, `refuses`,
   `ambiguous`) rather than overclaiming consensus.

### Character pressure profile

An entity profile describes a person; a Meta pressure profile explains what
makes their choices dramatically consequential.

```json
{
  "character_pressure_profiles": [
    {
      "entity_id": "ch-...",
      "enduring_drive": "...",
      "active_goal_shifts": [
        {"anchor_id": "ds-...", "from": "...", "to": "...", "trigger": "...", "cost": "..."}
      ],
      "capabilities_and_limits": ["..."],
      "inner_value_conflicts": ["..."],
      "decisive_choice_anchor_id": "ds-...",
      "agency": "high|mixed|low|distributed",
      "status": "supported_inference"
    }
  ]
}
```

An enduring drive may differ from the active goal of a particular scene; goal
shifts become meaningful when a trigger and price are visible.  “Maximum
capacity” is a continuity test: if a result relies on ignoring an established
ability/resource, record a narrowly evidenced question.  Do not mistake low
agency under oppression, tragedy, or systemic realism for automatically weak
construction.

### Sympathy, identification, empathy, and immersion

These are optional audience-effect hypotheses:

| Effect | Meaning | Evidence to capture |
| --- | --- | --- |
| `sympathy` | Concern for vulnerability, suffering, humiliation, loss, danger, isolation, or unfairness | Situation/predicament and its treatment. |
| `identification` | Desire that a character achieve a goal | Clear goal, understandable stake, value code, repair project, or relation. |
| `empathy` | Imaginative sharing of a felt subjective state | Embodied, sensory, relational, and viewpoint-specific presentation. |
| `transport` | Sustained absorption in the story world | Coherent detail, tone, access, emotion, and causal continuity. |

They must not be declared universal responses.  A morally compromised character
can still attract sympathy/identification through vulnerability, a code,
competence, care, repair, or a shared value conflict.  Conversely, deliberate
distance can be a valid aesthetic strategy.

### Audience contract and information fairness

Genre, tone, point of view, narrator reliability, and strong setup questions
make an implicit audience contract.  Store observable patterns, not market
assumptions:

- `genre_engine`: recurring kind of question, obstacle, experience, and
  anticipated payoff;
- `tone_register`: a sustained treatment pattern and any prepared shift;
- `reliability_contract`: reliable, restricted, unreliability signalled,
  contested, or unknown;
- `promise_payoff_links`: introduced expectation -> later answer/reframe;
- `information_fairness`: whether revelation revises prior evidence without
  contradicting it arbitrarily.

An unreliable account works as a form when its unreliability is part of the
established information design.  A mystery can withhold an answer; it should
not erase the significance of the evidence already offered without a prepared
recontextualisation.

## 22. Meta-layer build order and validation

### Recommended bottom-up pass order

1. Read ordered events and their before/after states; create a compact change
   ledger.
2. Extract active goals, resistance, options, constraints, and action pressure
   per focal thread.
3. Mark candidate core conflicts, core inequities, dilemmas, and suspense
   questions with event/scene references.
4. Identify escalation edges, local sequence peaks, global anchors, and the
   least-forcing macro lens.
5. Derive character pressure profiles, plot braid roles, audience-information
   patterns, theme/premise candidates, and ending relation.
6. Apply optional Story Mind perspectives, Hero's Journey, and archetypal
   functions only after the grounded core is complete.
7. Validate references, chronology, scope, duplicates, causal support, and
   uncertainty before emitting JSON.

### Cross-layer division of labour

| Need | Source / owner | Meta action |
| --- | --- | --- |
| Local scene objective, tactic, embodied pressure | Scene facts / minds | Cite; do not overwrite. |
| Causal unit and state change | Event | Use as primary anchor evidence. |
| State, desire, relation, capability | Entity | Derive pressure/arc only with evidence. |
| Thread membership/spine | Plot | Describe braid, function, convergence, and discharge. |
| World/theme perspectives | Existing Meta | Refine core inequity/perspective map. |
| Condensed story account | Exposé / root | Consume structural projection downstream. |

### Added validation invariants

- A `core_conflict` must cite at least two development events or explicitly be
  marked local/early/unfinished.
- A `binding_constraint` must state which option is lost or why delay fails.
- A `dilemma` must name a loss for each path; otherwise downgrade it to an
  `obstacle` or `decision`.
- An `escalation_edge` must identify a changed cost, tactic, information,
  power, scope, time, or irreversibility.
- A `suspense_question` must specify audience knowledge and at least two
  relevant possible outcomes, unless it is `dread` with an anticipated but
  unpreventable outcome.
- A `premise_proposition` must be tested against climax and aftermath; use a
  question when the ending does not support a conclusion.
- A `perspective_map` must be allowed to be partial/not applicable; never fill
  empty Dramatica slots.
- Every interpretation should retain status, confidence, alternatives where
  relevant, and references resolving to lower layers.

## 23. Top-down use without contaminating bottom-up analysis

The same concepts are useful to a generation/planning pipeline, but planned
intent must never be confused with observed structure.

```text
brief/root/exposé
  -> optional dramatic intent
  -> optional pressure, dilemma, and causal-engine plan
  -> plots/events/scenes
  -> bottom-up observed dramatic-structure analysis
  -> plan-versus-observation comparison
```

Top-down `dramatic_intent` may propose a central question, value conflict,
desired pressure progression, possible dilemma, thread roles, genre promise,
and desired ending relation.  Each must be `soft`, revisable, and clearly
versioned as *planned*.  After generation, the bottom-up layer reports only
what events/scenes support.  Drift may be valuable creative discovery rather
than an error; record it before deciding whether to revise the plan or tree.

## 24. Source notes and scope

This cheat sheet synthesises traditional poetics, screenwriting vocabulary, and
the reviewed `screenwriting-skills` collection.  The latter explicitly combines
Field, Snyder, McKee, Hoxter, Hicks, Chinese dramatic practice, character
conflict, premise/theme work, Chekhov, and Ozu; its skill texts are useful
craft guidance, not a universal ontology.  The Hero's-Journey material
distinguishes Campbell's comparative 17-stage monomyth from Vogler's practical
12-stage adaptation.

The current extension additionally distils James N. Frey's *How to Write a
Damn Good Novel* volumes I and II, an internal `Architecture of the Story Mind`
reference, and an internal text on conflict, coercion, action pressure, and
suspense.  Their prescriptive writing advice has been converted here into
optional evidence tests; it does not override StoryTree's bottom-up provenance
or force a particular dramatic tradition on a screenplay.

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
