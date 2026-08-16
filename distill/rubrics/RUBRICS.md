# Distillation rubrics

**Generated from the JSON in this directory by `render_md.py`. Edit the JSON, not this file.**

Every node type takes the seven universal dimensions (A–G) plus its own. Reconstruction runs additionally take R1 and R2. The gate for every node type is the same: **every dimension ≥ 3 and the mean ≥ 4**.

The universal dimensions and R1/R2 are reproduced *verbatim* from `docs/07-quality-evaluation.md`. That is deliberate: scores from this pipeline are only comparable with the GLM-5.2 and Qwen3.8-27B passes already recorded there if a 3 means the same thing in all of them. Everything else here is new.

---

## Universal dimensions (apply to every node type)

**Provenance.** Verbatim from docs/07-quality-evaluation.md §1.2. Do not re-word: scores are only comparable across the GLM/Qwen passes and this pipeline if a 3 means the same thing in all of them.

**Posture.** Hard marking. 3 is 'acceptable, would survive review with notes', not 'good'. A layer that fills every schema slot correctly and adds no judgement scores 3 at best on the dimensions that matter.

**Scoring rules:**

- Integers 1-5 only. No half points.
- Every score requires one sentence of evidence naming a specific field or quoting text. A score without a field reference is not a score.
- Score the node as delivered, not as it could be read charitably.
- Where a fault is caused by an upstream layer, score whether this node propagated it without flagging, and record the upstream cause in commentary.

#### A · Internal consistency

*Does the node contradict itself?*


| | |
|---|---|
| **1** | Load-bearing self-contradiction: a field asserts something another field of the same node denies, and a downstream consumer following either would break. Actors named in prose are absent from the participant list; a declared change has identical before and after. |
| **3** | Coherent on the spine, with peripheral drift: a label that does not match the content it labels, a date or ordering that does not survive arithmetic, one field written to a different draft than its neighbours. |
| **5** | Every field survives cross-checking against every other field of the node, including arithmetic on dates, sums, ranges and enumerations. |

#### B · Referential integrity

*Do the node's pointers resolve, in both directions?*


| | |
|---|---|
| **1** | Most identifiers do not resolve to any declared entity/plot/step, or the node names abstractions in a slot the schema reserves for ids. The graph edge is broken. |
| **3** | All pointers resolve, but the node is under- or over-declared: a relationship the node participates in is not listed, or a required self-identifier is missing while the containing key supplies it by accident. |
| **5** | Every id resolves, every reciprocal declaration exists in the target node, and the node's own identifier is present and correct. |

#### C · Specificity (the transplant test)

*Paste this node into a different work, changing only proper nouns. Does it still fit?*


| | |
|---|---|
| **1** | It fits anywhere. Category vocabulary and stock phrasing throughout — 'she is driven by her past', 'the conflict escalates', 'he must confront his fears'. Nothing in it could only be true of this story. |
| **3** | Mixed. The nouns are this story's; the claims about them are generic. Traits are listed as abstractions ('precision, integrity, duty') rather than as behaviours with a shape. |
| **5** | Transplanting it produces nonsense, because its content is welded to particulars — an observable behaviour, a measurement, a physical detail, a prohibition specific to this person or place. |

#### D · Schema and instruction compliance

*Does it obey the contract it was handed — including the instructions that are not schema-enforceable?*


| | |
|---|---|
| **1** | A hard schema violation (missing required field, value outside a closed enum), or total non-compliance with an instruction the prompt singles out as the failure it exists to prevent. |
| **3** | Schema-valid and mostly compliant, with one clear breach of a stated standing rule that the validator does not catch (a forbidden tic, a length budget, a register rule). |
| **5** | Schema-valid, and the unenforceable instructions are visibly obeyed — including the ones the model could have skipped without detection. |

#### E · Dramatic competence

*Judged against the craft sheet the pipeline itself injects (Frey I & II + screen craft).*


| | |
|---|---|
| **1** | Fails the Mamet test outright: nobody wants anything from anybody, nothing is at risk, no value flips. Or the opposition is a wall rather than an agent. A 'blah-blah' unit the craft sheet says should be deleted. |
| **3** | A real conflict exists and something changes, but the movement is sequential rather than escalating, or the resistance is declared and never acts, or the unit takes the timid option where a harder one was available. |
| **5** | Insistence versus resistance with both sides at maximum capacity; the pressure rises by a measurable step; a named value flips; the opposition's position is one a reader could hold. |

#### F · Psychological plausibility

*Are the minds in this node people, or are they mechanisms with feelings attached?*


| | |
|---|---|
| **1** | Motivation is asserted, not traced. States are labelled ('she was afraid', 'he felt guilty') rather than produced. Characters know things about themselves no person knows about themselves. |
| **3** | Coherent and defensible, but mostly re-description: the psychology restates the behaviour it is supposed to explain, with no mechanism connecting wound to habit to choice. |
| **5** | Traits trace to causes; what is felt and what is expressed differ and the gap leaks; the character's self-model is wrong in a way that will cost them something. |

#### G · Independent-writer band (the anti-fake dimension)

*In band: given exactly these inputs, could a different competent writer have landed here? Load-bearing: could they have produced this WITHOUT the inputs?*


| | |
|---|---|
| **1** | Out of band and not load-bearing: the node ignores explicit constraints it was handed and contains nothing the inputs supplied. Arbitrary and generic at once. |
| **3** | In band, but the inputs did little work: this is the first and most obvious move available, essentially a restatement of the layer above in the local vocabulary. |
| **5** | In band, and unreachable without the inputs: the node makes a choice that is defensible, non-obvious, and demonstrably derived from a specific thing established upstream. |

---

## ROOT node — the story root

**Notes.** Reconstruction node: R1 (fidelity of inference, sighted reading) also applies — see reconstruction.json. The ROOT is written sighted, so R1 is scored as accuracy against the source, never as blind-forecast coherence.

Inherits the **universal** dimensions (A–G).

**Gate:** every dimension ≥ 3 and mean ≥ 4.0; at most 5 rounds, then quarantine and record.

#### RT1 · Genre precision

*Is the genre named at a resolution that constrains anything?*


| | |
|---|---|
| **1** | A one-word bucket — 'fantasy', 'action', 'thriller'. Names a shelf, not a work. Two hundred other films fit the same label. |
| **3** | A compound label with a modifier ('cyberpunk action thriller') that narrows the field but still admits dozens of works, and does not name the specific conventions this work honours or refuses. |
| **5** | A nuanced compound naming the tradition, the register, and at least one convention the work deliberately violates, such that a reader could predict this work's shape from the label alone and would be surprised by the wrong films matching it. |

#### RT2 · Audience identification

*Are the target audiences correctly and distinctly identified?*


| | |
|---|---|
| **1** | One undifferentiated audience, or an audience the work demonstrably does not serve. 'General audiences' for a work with a hard content profile. |
| **3** | A plausible primary audience with the right age band and content flags, but the secondary audiences are absent or are restatements of the primary in different words. |
| **5** | Two or more genuinely distinct groups, each with its own stated reason for engaging (what that group is there for is different per group), consistent with the work's actual content, register and difficulty. |

#### RT3 · Elevator pitch — dual test

*Does the pitch match the script AND work standalone? Both halves must pass.*


| | |
|---|---|
| **1** | Fails either half hard: describes a story the script does not tell, or requires prior knowledge of the work to parse ('Neo learns the truth about the Matrix' — meaningless cold). |
| **3** | Accurate to the script and comprehensible cold, but generic in shape — a logline that would fit the genre's median entry; or it withholds so much that a cold reader cannot tell what the work is about. |
| **5** | Every clause checks out against the script, and a reader who has never heard of the work understands the world, the protagonist's problem, and what is at stake, in a few sentences, with no unexplained proper nouns. |

#### RT4 · Entity roster — coverage and description

*Are the cast and important entities identified, and does each one-to-three-sentence description earn its place?*


| | |
|---|---|
| **1** | The roster misses entities the work cannot be described without, or is padded with entities that influence nothing. Descriptions are role labels ('the mentor', 'the villain'). |
| **3** | The load-bearing characters and locations are present, but non-character entity classes (groups, objects, concepts, systems, conditions) are under-represented, and several descriptions state function rather than content. |
| **5** | Every entity whose removal would change the plot is present, across all classes; each description says what the entity concretely is and what it does to the story, and would let a reader recognise it in the script. |

#### RT5 · Plot identification

*Are the right plots identified, and are they plots rather than themes or summaries?*


| | |
|---|---|
| **1** | Fewer than the four required kinds (main-character, character-growth, relationship, antagonist), or the 'plots' are themes, settings, or a single plot cut into pieces. |
| **3** | The four kinds are present and separable, but one is a thin restatement of another, or a plot the work obviously runs (a side-character line, a social theme) is missing. |
| **5** | All required kinds plus the work's genuinely distinct additional lines; each is separable — you could remove one and name exactly what stops working — and each has a different agent, clock or arena. |

#### RT6 · Per-plot description

*For EACH plot: do its one-to-three sentences state a causal chain?*

**Scored per item** over `plots[]` — one score per element, reported individually and as a mean.


| | |
|---|---|
| **1** | A topic, not a chain: 'the story of his growth'. No agent, no opposition, no consequence. Or a chronology joined by 'and then'. |
| **3** | Agent, want and obstacle are present, but the chain is stated at one level of abstraction above the events — a reader could not say which scenes belong to it. |
| **5** | Within three sentences: who wants what, what specifically resists, what it costs, and how it resolves — with each clause following causally from the last, and the chain assignable to concrete scenes. |

#### RT7 · Writing style — the unnamed-author test

*Does the style description let a writer reproduce the register without being told whose it is?*


| | |
|---|---|
| **1** | Adjectives only: 'fast-paced, gritty, atmospheric'. True of a thousand works. Or it names an author instead of describing the style. |
| **3** | Names pacing and dialogue register with some specificity, but gives no prohibition, no sentence-level habit, and no test a draft could fail. |
| **5** | Covers pacing, dialogue register, atmosphere, and the introspective/terse axis with at least one falsifiable handle each — a thing the prose does, a thing it never does — such that a competent writer given only this description would produce recognisably this register, and no author is named. |

#### RT8 · Dramatic structure

*Are act/chapter count, turning points, plot points and climax placed where the work actually puts them?*


| | |
|---|---|
| **1** | A template asserted over the work (a generic three-act with 25/50/25 splits) that the script's own scene positions contradict, or no structure at all. |
| **3** | The act count is right and the climax is roughly located, but turning points are named without positions, or positions are given that do not match the measured scene indices. |
| **5** | Act/chapter count, each turning point and plot point, and the climax are placed at positions that check out against the work's own measured scene ordering, and the placement is what the exposé length budget is then derived from. |

#### RT9 · Human-experience topics and dilemmas

*Are the central topics ones any reader relates to, and are they this work's rather than the genre's?*


| | |
|---|---|
| **1** | Genre furniture mistaken for theme ('the fight against the machines'), or an abstraction list with no dilemma in it ('freedom, destiny, love'). |
| **3** | Real human topics named (poverty, curiosity, greed, obligation), but stated as topics rather than as dilemmas — no competing goods, nothing a reader could come down on either side of. |
| **5** | Each topic is stated as a dilemma with two defensible sides, is demonstrably what the work spends its screen time on, and connects to a specific plot or character rather than floating above the work. |

#### RT10 · Identification value of the protagonist

*Are BOTH halves supplied — what the audience would admire, and what vulnerabilities open their heart?*


| | |
|---|---|
| **1** | Only one half, or neither. A flawless competence list (nobody identifies with perfection) or a catalogue of failures with nothing to want to be (nobody wants to be a loser). Or the two halves are the same trait restated. |
| **3** | Both halves present but generic: a stock virtue and a stock wound, either of which would fit any protagonist in the genre, with no link between them. |
| **5** | A named strength, virtue or competence the audience would want for themselves, and a weakness they recognise in themselves, with the two mechanically connected — the strength costs something, or the flaw is the price of the virtue. For a villainous protagonist the admirable term is competence, intelligence or style, and it is named as such. |

---

## EXPOSÉ node

Inherits the **universal** dimensions (A–G).

**Gate:** every dimension ≥ 3 and mean ≥ 4.0; at most 5 rounds, then quarantine and record.

**Length budget:** ~300 words per act (three-act feature ~= 900 words); ~200 words per chapter for a novel. Derived from `ROOT.dramatic_structure`, tolerance ±15%. Budget is checked mechanically before the judge is called; a breach outside tolerance is a D=1 and the artifact is returned to the author without spending a judge call.

#### X1 · Cold comprehensibility

*Can a reader who has never heard of this story follow it end to end?*


| | |
|---|---|
| **1** | Assumes the reader knows the work: unexplained proper nouns, references to 'the ship' or 'the device' before either exists, pronouns without antecedents. |
| **3** | Followable with effort. One or two places require the reader to hold an unexplained term until it is defined later. |
| **5** | Every proper noun, faction and object is introduced before it is used, and a cold reader could retell the plot afterwards. |

#### X2 · World explained only where it matters

*Is the worldbuilding load-bearing, or is it padding?*


| | |
|---|---|
| **1** | Either a worldbuilding essay that the plot never uses, or no world at all where the plot depends on a rule the reader is never told. |
| **3** | The needed rules are present but arrive with surplus: physics, politics or religion explained past the point where the plot consumes them. |
| **5** | Every world fact stated is later used by an event in the exposé, and every event that depends on a world fact has that fact already stated. Nothing else is there. |

#### X3 · Entity introduction in context

*Is each important entity introduced as this reader would need it, with no prior knowledge assumed?*


| | |
|---|---|
| **1** | Entities appear mid-sentence as if already known, or are introduced by role label only. |
| **3** | Characters are introduced adequately; locations, groups and objects appear without introduction and have to be inferred. |
| **5** | Each important entity gets its introduction at first use, in context, at the length its importance warrants — and the protagonist gets more than the courier. |

#### X4 · Causal chain honouring every plot — implicitly

*Does every plot from the ROOT get discharged by events, without ever being named as a plot?*


| | |
|---|---|
| **1** | Plots are named ('the relationship plot then develops'), or one or more ROOT plots leave no trace in the exposé at all. |
| **3** | All plots are traceable, but at least one is discharged in a single clause rather than by a chain, or the exposé steps out to label a thread. |
| **5** | Every ROOT plot is carried by concrete events in correct story order, each connected to the next by because/therefore, and no plot is ever named as such. |

#### X5 · Structural conformity

*Does the exposé follow the ROOT's dramatic structure — acts, turning points, plot points?*


| | |
|---|---|
| **1** | The declared structure and the exposé's shape do not correspond; the climax is where the ROOT says the midpoint is, or acts have no visible boundary. |
| **3** | Act boundaries are discernible and roughly proportioned, but a declared turning point is missing or lands in the wrong act. |
| **5** | Each act occupies its stated share, each declared turning point appears at its position and does turn something, and the climax falls where the ROOT places it. |

#### X6 · In-world jargon glossed

*Are artifacts, powers, technologies and coined terms explained enough to follow?*


| | |
|---|---|
| **1** | Coined terms used as if standard English. The reader must guess what the central technology does. |
| **3** | The central term is glossed; secondary coinages are not, or are glossed after their first load-bearing use. |
| **5** | Every coined term is glossed at first use in a clause, not a paragraph, and the gloss is sufficient to follow every later use. |

#### X7 · Processing fluency / readability

*Does it read cleanly on the first pass, without backtracking?*


| | |
|---|---|
| **1** | Requires re-reading: garden-path sentences, three clauses of subordination, referents that resolve backwards, or a paragraph that must be held in memory before it makes sense. |
| **3** | Mostly fluent with local snags — one overloaded sentence, one ambiguous pronoun, one list that outruns working memory. |
| **5** | First-pass readable throughout. Information arrives in the order the reader needs it; each sentence is resolvable when it ends. |

#### X8 · Protagonist likeability and the open heart

*Does the exposé show what makes the protagonist likeable and what opens the audience's heart?*


| | |
|---|---|
| **1** | The protagonist is a plot function. Nothing in the exposé would make a reader want them to succeed. |
| **3** | Sympathy is asserted rather than produced — the exposé says they are principled or lonely instead of showing the moment that demonstrates it. |
| **5** | At least one concrete moment in the chain earns admiration and at least one exposes vulnerability, and both are events the script actually contains. |

#### X9 · Human-experience topics woven in

*Are the ROOT's topics present in the events rather than announced?*


| | |
|---|---|
| **1** | Topics are absent, or stated as thesis sentences the events do not support. |
| **3** | Topics are visible in the events but only for one or two of them; the rest are asserted or dropped. |
| **5** | Each ROOT topic surfaces through at least one event where a character pays for it, and no sentence exists solely to state the theme. |

---

## ENTITY node — one character, location, object, group or concept per node

Inherits the **universal** dimensions (A–G).

**Gate:** every dimension ≥ 3 and mean ≥ 4.0; at most 5 rounds, then quarantine and record.

**Applicability by entity kind:**

| kind | dimensions |
|---|---|
| character | E1, E2, E3, E4, E5, E6, E7 |
| location | E1, E3, E8 |
| object | E1, E3, E8 |
| group | E1, E3, E8 |
| concept | E1, E3, E8 |

#### E1 · t0 discipline

*Is this the entity before anything happens?*

**Source.** docs/07 §1.3, unchanged


| | |
|---|---|
| **1** | The dossier knows the ending. Outcome facts sit in the same fields and the same confident register as opening facts, so any consumer is handed the resolution. |
| **3** | Opening state is broadly correct, but the story's thesis or the arc's destination has been written into a t0 field (need, limitations) where it removes the uncertainty the middle runs on. |
| **5** | The entity before anything happens. Everything forward-looking is confined to `arc`, and the declared state variables genuinely start where the story starts. |

#### E2 · Voice separability

*Could a reader sort unattributed lines?*

**Source.** docs/07 §1.3, unchanged


| | |
|---|---|
| **1** | No speech signature, or one whose contents are true of any careful/laconic/wry character. |
| **3** | A signature exists and names a register, but gives no prohibition and no stress behaviour — enough to describe the voice, not enough to reproduce or falsify it. |
| **5** | Five testable handles including a real `never_says` and a real `under_stress`; a reader handed unattributed lines could sort them. |

#### E3 · Attribute completeness

*Are the required profile fields present AND filled with content rather than category words?*


| | |
|---|---|
| **1** | Required fields missing, or filled with the field name restated ('problem-solving strategy: solves problems pragmatically'). Physical description is a stock type. |
| **3** | All fields present; roughly half carry real content and the rest are single adjectives. Big Five given as labels with no behavioural consequence. |
| **5** | Every required field carries a claim that could be false: an age with a consequence, a build and face specific enough to cast, a coping strategy you could watch someone execute, Big Five scores each tied to an observable habit, education and intellectual capability that predict how this person reasons under pressure. |

#### E4 · Relationship matrix

*Is there an individual relationship to every other declared character, asymmetric where it should be?*


| | |
|---|---|
| **1** | Relationships listed for a favoured few, or one blanket statement covering the cast. Missing edges to characters this one demonstrably interacts with. |
| **3** | Every declared character is covered, but several entries are one-word labels ('ally', 'rival') and the matrix is symmetric where the story is not — A's view of B is B's view of A restated. |
| **5** | An entry per other declared character; each states what this character wants from that one, what they believe that one thinks of them, and what they would never say to them; asymmetries are explicit and consequential. |

#### E5 · Backstory causality and addressability

*Does the backstory produce the present-day person, and is it decomposed one claim per key?*


| | |
|---|---|
| **1** | A chronology of events with no consequence, or a free-text block that cannot be patched (multi-sentence values under one key), or a backstory that contradicts a declared trait. |
| **3** | Decomposed correctly and roughly causal, but the chain runs event→trait in one hop: a childhood incident is asserted to have produced a trait with no intervening habit or belief. |
| **5** | Several hundred words from childhood forward, one self-contained claim per key, each patchable; at least two traits trace wound → belief → habit → present behaviour, and at least one belief the character holds is visibly wrong. |

#### E6 · Off-cliché roundness

*Does the character have interests, habits and textures the plot does not need?*


| | |
|---|---|
| **1** | Every stated trait serves the plot. The character is a role with a name — a soldier who likes soldiering. |
| **3** | One or two non-plot details, but they are decorative (a hobby that never affects anything and reveals nothing) or they are the genre's standard-issue quirk. |
| **5** | At least two interests, habits or tastes that the plot does not use, that cut against the character's type, and that a reader would remember — and at least one of them makes a scene harder rather than easier. |

#### E7 · Internal conflict

*Is there a real internal conflict — usually competing goals — with a cost either way?*


| | |
|---|---|
| **1** | No internal conflict declared, or a false one where one side obviously wins ('wants to do the right thing but is afraid'). |
| **3** | Two goals named that genuinely compete, but the reader can already tell which will lose, or the conflict never touches the declared state variables. |
| **5** | Two goods the character cannot both have, each with a named cost, each defensible; the conflict is expressed in declared state variables so a later scene can move it. |

#### E8 · Non-mind entity dynamics

*For a location, object, group or concept: what forces act on it, and what changes its meaning?*

**Applies to.** ['location', 'object', 'group', 'concept']


| | |
|---|---|
| **1** | A description with no dynamics. A room's dimensions; a faction's name and size. Nothing that could change. |
| **3** | Dynamics stated in the abstract ('the city is under pressure') with no mechanism and no declared variable that could move. |
| **5** | Named forces with directions, at least one declared state variable that the story will move, and a stated way the entity's meaning to the characters can invert. |

---

## PLOT node — one plot per node

**Measured context.** P1 and P2 are the two weakest type-specific dimensions in the existing evaluation (both 2.50 mean for GLM, P1 2.00 for Qwen). Expect to spend revision rounds here.

Inherits the **universal** dimensions (A–G).

**Gate:** every dimension ≥ 3 and mean ≥ 4.0; at most 5 rounds, then quarantine and record.

#### P1 · Spine causality

**Source.** docs/07 §1.3, unchanged


| | |
|---|---|
| **1** | 'And then, and then.' Steps are a chronology; remove one and the rest still work. `because` is empty or decorative. |
| **3** | Causality is real in places — usually late in the spine — but early steps are sequential and cross-plot `because` links are missing where causes plainly exist. |
| **5** | Each step requires its predecessor; the cross-plot `because` links are the actual load path and could not be deleted without the spine collapsing. |

#### P2 · Resistance reality

**Source.** docs/07 §1.3, unchanged


| | |
|---|---|
| **1** | Resistance is a list. No declared opponent takes an action anywhere in the spine, or the 'opponents' are abstractions with no dossier and no agency. |
| **3** | Resistance acts, but reactively and without a stated motive a reader could sympathise with; the force balance favours the agent throughout. |
| **5** | The opposition counters with equal force and cunning, has a logical and sympathisable motive, and its moves appear as spine steps. |

#### P3 · Separability

*Is this a distinct plot, or a facet of another one?*


| | |
|---|---|
| **1** | Removing this plot changes nothing, or removing it also removes another declared plot because they are the same chain seen twice. |
| **3** | Distinct, but shares its agent, its clock and its arena with another plot, so the two rise and fall together. |
| **5** | Removing it breaks something nameable that no other plot supplies, and it differs from every sibling in at least one of agent, clock or arena. |

#### P4 · Scene assignability

*Could a reader assign concrete scenes to this plot's steps?*


| | |
|---|---|
| **1** | The spine sits at a level of abstraction where no scene could be assigned to any step. |
| **3** | Most steps are assignable; one or two are summary statements covering an unbounded stretch of the work. |
| **5** | Every step names an action specific enough that the scenes discharging it can be identified, and the step count is proportionate to the work's length. |

#### P5 · Cost of outcome

*Does resolution cost something nameable?*


| | |
|---|---|
| **1** | `outcome: success` with no cost — the goal was written narrow enough to be achievable for free. |
| **3** | A cost is stated but is generic ('it takes a toll') or is paid by someone the reader has no stake in. |
| **5** | The resolution costs a named thing the agent wanted, declared as a state change, paid by someone the reader cares about. |

---

## EVENT node — one event per node

**Measured context.** V1 (change reality) scored 1.00 mean for GLM across two nodes — both event nodes independently declared state changes with before == after, in different runs on different material. It is a mechanical check; run it in code before spending a judge call.

Inherits the **universal** dimensions (A–G).

**Gate:** every dimension ≥ 3 and mean ≥ 4.0; at most 5 rounds, then quarantine and record.

**Mechanical prechecks** — run in code before a judge call is spent; a failure returns the artifact to the author with the failing assertion as the instruction:

- Every state change lands on a variable declared in the entity layer.
- before != after for every declared change.
- Exactly one parent plot; every referenced entity id resolves.
- Magnitudes sit on the anchored scale.

#### V1 · Change reality

**Source.** docs/07 §1.3, unchanged


| | |
|---|---|
| **1** | The declared changes do not change anything: before equals after, or magnitudes are off the anchored scale, or nothing belonging to the protagonist moves in a unit that is supposed to be about them. |
| **3** | Real changes on real variables, but at least one is padding, or a magnitude is defensible only loosely, or a change the prose obviously implies is not declared. |
| **5** | Every declared change is a change, lands on a declared variable, sits on an anchored magnitude a reader could defend, and the set is complete with respect to the action. |

#### V2 · Externalisation

**Source.** docs/07 §1.3, unchanged


| | |
|---|---|
| **1** | Interiors narrated as interiors; direct speech in a field that forbids it; state changes no camera could record. |
| **3** | Predominantly external, with a labelled interior or a summary where an act was available. |
| **5** | Everything is photographable or audible; dialogue is reported as semantics and illocutionary force even where the writer can see the lines. |

#### V3 · State triple completeness

*For every involved entity: initial state, the change, and the ending state — across mental, emotional, social and physical registers.*


| | |
|---|---|
| **1** | One register only (usually physical), or entities involved in the event with no state recorded at all. |
| **3** | All involved entities have entry and exit states, but two or more registers are empty for most of them, and the empty ones are empty because they were not considered rather than because nothing moved. |
| **5** | Each involved entity has entry state, change and exit state; every register is either filled or explicitly marked unchanged with a reason; the exit state of each is the entry state the next event will consume. |

#### V4 · Outward effect

*Does the node say how the event affects things outside itself?*


| | |
|---|---|
| **1** | The event is sealed. Nothing outside it changes, and no later event is made possible or impossible. |
| **3** | An effect is claimed in general terms ('this raises the stakes') without naming what specifically becomes available, blocked, or more expensive. |
| **5** | Names at least one thing that becomes possible, one that becomes impossible or costlier, and one off-screen party who would react — each traceable to a declared entity or plot. |

#### V5 · Mental simulation — endpoints

*For each involved character at beginning and end (and in between where it matters): thought, feeling, intent, perception, expression, beliefs about other minds; displayed vs felt; internal conflict; competing goals; social concerns; higher-order theory of mind.*


| | |
|---|---|
| **1** | States labelled, not produced. Theory of mind absent or first-degree only ('he knows she is angry'). Displayed and felt are the same value everywhere. |
| **3** | Both endpoints present for the main characters with a real felt/displayed gap somewhere, but theory of mind stops at degree two, the secondary characters get one line each, and no error is named in anyone's model of anyone. |
| **5** | Both endpoints for every materially involved character; at least one theory-of-mind tower reaching degree three with the error in it named and costed; displayed and felt differ where they should and the leak is specified; competing goals and social concerns are the ones this character would actually have. |

---

## SCENE node — one scene per node, assembled from scaffolded sub-calls

**Assembly.** Scaffolded: craft -> one psychology block per character -> specimen exchange -> non-mind dynamics -> continuity, assembled mechanically. Never request more than one deep structure per call (docs/05 §1). The judge scores the assembled node; revision instructions are routed to the sub-call that owns the failing dimension.

**Measured context.** T1 (envelope discipline) is the worst-scoring type dimension in the corpus: 1.67 mean for GLM, 1.00 for Qwen, and 0/3 roster compliance for both models. docs/07 §12.4 concludes these are missing assertions, not prompt problems — enforce mechanically before scoring.

Inherits the **universal** dimensions (A–G).

**Gate:** every dimension ≥ 3 and mean ≥ 4.0; at most 5 rounds, then quarantine and record.

**Mechanical prechecks** — run in code before a judge call is spent; a failure returns the artifact to the author with the failing assertion as the instruction:

- Every speaker in the specimen is on the scene's on_screen roster.
- Every dynamics block names the scene's own location id.
- Every state change names a variable declared for that entity.
- Word count within the envelope's stated band.
- Node is not degenerate: >= 400 words, required top-level keys present.

#### T1 · Envelope discipline

**Source.** docs/07 §1.3, unchanged


| | |
|---|---|
| **1** | The envelope is ignored. The forecast is scaled to a sequence when the budget is a beat, gives lines to characters not on the roster, or writes psychology for someone not present. |
| **3** | The envelope is cited in the analysis and honoured in shape, but breached in one specific (roster, ratio, or length). |
| **5** | Every number and name in the envelope is treated as binding, and the node is visibly shaped by the constraint rather than merely acknowledging it. |

#### T2 · Deliberation honesty

**Source.** docs/07 §1.3, unchanged

**Measured context.** Qwen's worst dimension (2.00 vs GLM 4.33): flip conditions always 'if this were a different work', confidence 90-95 on forecasts wrong in location, character and event. EXP-001 clause A moved confidence 95->85 and 90->65 on n=2.


| | |
|---|---|
| **1** | Alternatives all lose by a mile; no near-miss; the flip condition restates the rejection. Risks unfalsifiable. The decision was made before the list was written. |
| **3** | The required near-miss exists and is genuinely close, but the flip conditions are generic (a different genre, a different story) rather than a single fact about this story. |
| **5** | At least one alternative was live, the flip condition is one specific established fact, risks are testable, and at least one risk is honestly marked unmitigated. |

#### T3 · Specimen craft and self-correction

**Source.** docs/07 §1.3, unchanged


| | |
|---|---|
| **1** | Lines are paraphrase or statement-of-intent; no subtext; the swap test is skipped or passed by assertion; the self-examination congratulates the analysis. |
| **3** | Real lines with real subtext, but the swap test is declined on a technicality and the self-examination confirms rather than revises. |
| **5** | Lines that could be spoken; the swap test is actually run against two voices with cited evidence; the self-examination overturns something the analysis above it asserted. |

#### S1 · State-change justification

*Does EVERY state change name the plot it serves and the dramaturgical goal it serves? Nothing shown may be arbitrary.*


| | |
|---|---|
| **1** | Changes are declared with no justification, or the justification is the change restated ('her trust drops because she trusts him less'). |
| **3** | Each change names a plot, but the dramaturgical goal is a category word ("raises tension", "develops character") that would fit any change in any scene. |
| **5** | Each change names (a) the specific plot and step it discharges and (b) the dramaturgical function at this position in the declared structure — setup for a named later payoff, reversal of a named earlier value, a cost that makes a named later choice harder. A reader could delete the change and say exactly which later thing stops working. |

#### S2 · Beat-level mental simulation

*Is the full mental model present at scene start, scene end, and at every beat carrying an important state change?*


| | |
|---|---|
| **1** | One psychological block for the whole scene, or blocks that do not move between start and end. |
| **3** | Start and end are covered per character, but the beats in between are summarised, so the moment where the change actually happens is not modelled. |
| **5** | Start, end, and every important-change beat carry the full model per involved character — thought, feeling, intent, perception, expression, beliefs about other minds, displayed vs felt, internal conflict, competing goals, social concerns, higher-order theory of mind — and the trajectory across beats has perceivable triggers rather than a smooth interpolation. |

#### S3 · Whole life — characters are not puppets

*Do the people in this scene have lives outside it, and does that show?*

**Why it exists.** The designed-against failure mode: models let characters act only toward the obvious goal and react only to the obvious threat. Real people in a scene are also connected to people who are not in it.


| | |
|---|---|
| **1** | Every character is a function of this scene's conflict. Nobody wants anything unrelated, nobody is distracted, nobody owes anyone anything off-screen, nobody has a body. Delete the plot and the characters cease to exist. |
| **3** | One or two off-scene attachments named (a mentioned relative, a stated obligation) but they are inert — they never affect what anyone does, says, or notices in this scene, and the same list would fit any scene these characters are in. |
| **5** | At least three distinct classes present and consequential — an absent relationship exerting pressure; an unfinished errand, obligation or debt; a private worry unrelated to the scene's conflict; a bodily need; an ordinary micro-distraction — and at least one of them measurably changes a line, a timing, an omission or an attention allocation inside this scene. What is off-screen is specific to this character at this hour of this day, not a generic 'has a family'. |

Checkable items — the judge counts how many are present *and consequential*:

- an absent person exerting pressure (someone they owe a call, want to please, fear the judgement of)
- an errand, obligation or task they meant to do and have not
- a work or family obligation with a clock on it
- a private worry not caused by this scene's conflict
- a bodily state: hunger, cold, exhaustion, pain, needing the toilet, a healing injury
- an ordinary micro-distraction: a noise, an itch, a song stuck, a phone in a pocket
- a fear of what a specific named person will think

#### S4 · Perception across senses

*Is scene-level perception recorded across all channels, and is it this character's perception rather than the camera's?*


| | |
|---|---|
| **1** | Vision only, or an inventory of what is in the room rather than what is perceived. |
| **3** | Two or three channels covered, identically for every character present. |
| **5** | Every channel that is available is recorded, and what each character notices differs by their state, expertise and attention — including what one of them fails to notice, with a reason. |

#### S5 · Prose discipline (when prose is written)

**Source.** docs/10-prose-system-prompt.md

**Applies when.** the node includes drafted prose or a specimen exchange


| | |
|---|---|
| **1** | Multiple banned constructions: somatic tells, voice-modifier dialogue tags, 'not just X but Y', theme statements, tricolons for emphasis. |
| **3** | Ban list respected but the restraint register is overused — more than one silence beat, 'long time', hand placement or clock time in the same scene. |
| **5** | Clean against the ban list, restraint capped at one instance per scene, and at least one fresh concrete image that names an actual object, material or measurement. |

---

## HINDSIGHT TRACE node — the post-hoc derivation written after an artifact passes

**What it is.** Once an artifact passes its gate, the author writes a derivation from the source material to the finished artifact, in the voice of someone who never received judge feedback but intuitively knew what to do and what traps to avoid. It must cover what NOT to do, using the actual problems hit in earlier rounds. Its purpose is fine-tuning data that teaches a model to avoid those traps directly, without needing a judge.

**Honesty note.** This is deliberately hindsight wearing the costume of deliberation — the thing docs/03-reconstruction.md forbids in blind reasoning. It is admissible here only because the trace is training data for a generation policy, never evidence about the model's inference. Every trace is stored with `is_hindsight: true` and the round history that produced it, so it can never be mistaken for a forecast.

Inherits the **universal** dimensions (A–G).

**Gate:** every dimension ≥ 3 and mean ≥ 4.0; at most 5 rounds, then quarantine and record.

#### H1 · Derivation validity

*Does the trace actually derive the artifact from the source, or does it announce the artifact and rationalise?*


| | |
|---|---|
| **1** | Starts from the conclusion. 'The genre is X because the work is X.' No step could have come out differently. |
| **3** | A real derivation for the spine, but the specific choices that made this artifact good arrive without a reason — the trace explains the obvious and asserts the non-obvious. |
| **5** | Each substantive choice is reached from evidence a reader can check in the source, and at least one step shows the evidence that would have forced a different choice. |

#### H2 · Trap coverage — fidelity to what actually went wrong

*Does the trace warn against the specific failures this artifact's earlier rounds actually contained?*


| | |
|---|---|
| **1** | No traps, or generic writing advice ('avoid clichés'). The trace could have been written before the loop ran. |
| **3** | Some traps named and they are real, but they are the easy ones; at least one dimension that scored below 3 in an early round is not addressed anywhere. |
| **5** | Every dimension that scored below the gate in any round is represented by a named trap, phrased as a temptation with its reason ('the obvious move here is X, which fails because Y'), and each is recognisable as what the earlier draft actually did. |

#### H3 · No-feedback voice

*Is the trace clean of any trace of the judge?*


| | |
|---|---|
| **1** | References the critique directly: 'the feedback said', 'after revision', 'in the second round', 'score', 'rubric', 'dimension'. |
| **3** | No direct reference, but the shape gives it away — the trace walks the rubric's dimensions in order, or corrects itself mid-derivation in a way only feedback would produce. |
| **5** | Reads as one continuous act of judgement by a writer who has done this before. Traps are anticipated, never repaired. |

#### H4 · Learning coverage

*For this node type, does the trace reflect what the artifact had to get right?*


| | |
|---|---|
| **1** | Covers one aspect and ignores the rest. |
| **3** | Covers most of the node type's required content but treats one required area as an afterthought. |
| **5** | Covers every area the node type's rubric scores — for a ROOT that means the pitch, the entities, the audiences, the genres, the identification value and the human-condition topics, each with a reason, not a mention. |

#### H5 · Transferability

*Does the trace yield a principle that generalises beyond this work?*


| | |
|---|---|
| **1** | Wholly work-specific; nothing a model could carry to a different story. |
| **3** | A generalisation is offered but is a truism, or is so general it constrains nothing. |
| **5** | At least one stated principle that is general, non-obvious, and falsifiable — it would tell a writer to do something different on a different story, and a counter-example could be constructed. |

---

## Reconstruction-only dimensions and the end-of-run fidelity evaluation

**Provenance.** R1 and R2 verbatim from docs/07-quality-evaluation.md §1.4. F1-F5 are new and are run once per script, after the scene layer completes, against the real screenplay.

**Applies to.** R1/R2: every node in a reconstruction run. F1-F5: the finished run as a whole.

#### R1 · Fidelity of inference

**Reading.** This pipeline's author is SIGHTED at every layer, so only the sighted reading applies. The blind reading is kept for comparison with the existing reconstruct/ pipeline.

*Sighted reading:*

| | |
|---|---|
| **1** | Confident false claims about the source; facts belonging to one character attributed to another; events reported that the document does not contain. |
| **3** | Substantially accurate with at least one clean false attribution stated in the same register as the verified material. |
| **5** | Every checkable claim checks out against the source text, including order and attribution. |

*Blind reading:*

| | |
|---|---|
| **1** | The forecast is incoherent with what was established, or forecasts the wrong unit. |
| **3** | A coherent forecast for a plausible scene that is not this one; the miss is legible and instructive. |
| **5** | A forecast that could have been the scene: consistent with every established fact, scaled to the unit, and wrong (if wrong) only in the way a good writer's second-best choice is wrong. |

#### R2 · Leakage resistance

**Reading.** For a sighted author, R2 asks whether knowledge from OUTSIDE this document got in unflagged — cultural knowledge of the film, its sequels, its criticism, its memes.


| | |
|---|---|
| **1** | Verbatim or near-verbatim reproduction of source material the node could not have seen, or an assertion sourced from the work's cultural reception rather than its text. |
| **3** | Outside knowledge is present but traceable to a layer the node was legitimately handed; the node uses it without flagging that it is reading rather than deciding. |
| **5** | Nothing in the node exceeds what its inputs support; where it invents, the invention is demonstrably wrong about the source, which is affirmative evidence of non-retrieval. |

#### F1 · Semantic match to real dialogue

**Scope.** run-level

**Computed.** For each scene with a specimen exchange: embedding similarity and human/judge rating of the specimen against the real lines at the same turning point, scored by dramatic function rather than wording.

**Note.** A different line achieving the same turn is a success. Verbatim agreement is a leak signal, not a quality signal — score it on F-dimensions and flag it on R2.


| | |
|---|---|
| **1** | Specimens serve a different function from the real lines in most scenes — different thing wanted, different value flipped. |
| **3** | The function matches in about half the scenes; where it misses, the miss is legible. |
| **5** | The dramatic function matches in the large majority, and where wording differs the difference is a defensible alternative rather than an error. |

#### F2 · Per-character speech-style match

**Scope.** run-level

**Computed.** Blind sorting task: unattributed specimen lines vs unattributed real lines, both assigned to characters by a judge that has only the reconstructed speech signatures.


| | |
|---|---|
| **1** | Specimen lines cannot be sorted above chance; the reconstruction did not capture voice. |
| **3** | Principals sortable, supporting cast not. |
| **5** | Sorting accuracy on specimens approaches sorting accuracy on the real lines. |

#### F3 · Event-order match

**Scope.** run-level

**Computed.** Kendall tau between the reconstructed event chain's story order and the source's actual order of the same events, plus a count of events invented and events missed.


| | |
|---|---|
| **1** | Order substantially scrambled, or a fabricated event contradicting the source (the Qwen sc-003 failure mode). |
| **3** | Order correct on the spine with local transpositions; no fabrications. |
| **5** | Order matches, no fabrications, and every omission is a deliberate compression the exposé accounts for. |

#### F4 · Dramatic-pacing match

**Scope.** run-level

**Computed.** Compare declared turning-point / plot-point / climax positions against the source's measured scene positions; compare per-act scene counts and dialogue ratios.


| | |
|---|---|
| **1** | Declared structure and measured structure disagree by more than one act on the climax. |
| **3** | Climax and midpoint within tolerance; secondary turning points drift. |
| **5** | Every declared structural position lands within tolerance of the measured position, and act proportions match. |

#### F5 · Hidden-state benchmark answerability

**Why it exists.** This is the point of the whole exercise: with the hidden models reconstructed at quality, a model can be given only the script and asked 'at what point does Alice feel X while expressing Y'.

**Scope.** run-level

**Computed.** Sample N questions of the form (character, felt state, displayed state) -> which scene/beat; check the reconstruction answers them uniquely, and that a competent reader of the script agrees.


| | |
|---|---|
| **1** | Most questions have no answer in the reconstruction, or several equally good answers. |
| **3** | Questions about principals at act boundaries are answerable; mid-act and supporting-cast questions are not. |
| **5** | The reconstruction supplies a unique, script-defensible answer for the large majority of sampled questions, including supporting characters and mid-act beats. |

---
