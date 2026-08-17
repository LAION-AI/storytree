# 8. Stage 6 — entity profiles, author and critic

Stages 4 and 5 rejoin here. This is the first stage that needs both: a profile has
to declare which plots its entity serves, and it has to be written against a
canonical identity that no longer drifts. Everything below it — 224 scene nodes,
thirty event drafts, the boundary list — is already fixed and readable.

The shape is three calls per entity:

```
6a  author    1 agent per entity   writes the full profile
6b  critic    1 agent per profile  argues against it, with script evidence
6c  revision  the author again     revises against the critique
```

At an entity count in the thirties that is roughly 105 calls and ~350,000 output
tokens, about 2 minutes of wall time — **assumed figures** against the measured
2,812 tok/s aggregate in `reports/qwen-local-deployment.md`. It is the third-largest
stage by volume, behind the two scene stages.

---

## 8.1 One agent per entity

The reason is the same measurement that shapes every other stage
(`05-model-behaviour.md` §1), and here it is nearly a direct hit rather than an
extrapolation: the experiment that produced the budget-dilution table varied how
many *psychological analyses* were requested in one call, and a character profile is
the same kind of object.

| Requested in one call | Complete blocks | Carried a trajectory | Schema violations |
|---|---|---|---|
| 1 | 1 of 1 | 1 of 1 | 5 |
| 2 | 0 of 2 | 0 of 2 | 16 |
| 4 | 2 of 4 | 2 of 4 | 41 |

At four, two were hollow — `entity: null`, one field filled out of eleven — while
output length stayed near 28,000 characters throughout. A stage that wrote all
thirty entity dossiers in one call would return thirty names and perhaps four
dossiers, and would pass a permissive schema check while doing it.

Each author agent receives: the full script, the entity's identity record from stage
5 with its complete occurrence list, every scene node and event draft in which it
appears, the plot list, and the craft sheet. It does not receive other entities'
profiles. Relationships are written from each side independently and reconciled at
the boundary check, which finds the disagreements rather than papering over them —
two characters who each believe they are the one being protected is a real and
interesting state, and a pipeline that averages it away has lost something.

---

## 8.2 The profile fields

From `ENTITY_SCHEMA` in `narrativeforge/schemas.py`. The top level is fixed:

| Field | Purpose |
|---|---|
| `entity_id`, `type`, `canonical_name`, `aliases` | identity, carried from stage 5 |
| `salience` | major / supporting / minor / mentioned |
| `plots` | plot ids this entity serves |
| `profile` | the dossier — nested, freely structured, type-specific |
| `relationships` | keyed by the *other* entity's id: kind, valence −100..100, notes |
| `state_variables` | **the only variables later layers may modify** |
| `state` | live values at t0; keys must match `state_variables`, values equal their `init` |
| `arc` | start state and end state in one line each |

`profile` is type-specific and the schema names what each type carries: characters
and creatures get demographics, appearance, voice and speech, habits and tells,
backstory, wound, want, need, values, fears, competences, limitations, problem-solving
style, coping strategies, health, moral axis. Locations get geography, atmosphere,
control, access, significance. Objects get provenance, description, function,
symbolic load, custody. Groups get membership, hierarchy, goals, resources, cohesion.
Concepts get content, believers, authority, causal power.

Three hard rules apply inside `profile`, and they are checkable in code:

- **Every prose block is a sentence map.** Freeform prose is decomposed one sentence
  per key — `b01`, `b02` — each with `text`, optionally `when` and `tags`. This is
  what makes any single sentence of a backstory addressable by JSON Pointer and
  therefore patchable by a later layer. A paragraph is not patchable; a numbered
  sentence is.
- **No string inside `profile` exceeds 180 characters.** A field that wants to be
  longer wants to be a sentence map.
- **No arrays of objects.** Arrays reorder, and a JSON Pointer into a reordered
  array points at something else. Maps with stable keys do not have this problem.

### `speech_signature`, required of anything that talks

A sub-object with five fields, and the schema's own justification is the argument:
*two characters whose lines could be swapped without anyone noticing are one
character wearing two names.*

```
sentence_shape      long and subordinate, or short and flat
vocabulary_domain   what they reach for metaphors from — the trade, the body,
                    money, scripture
verbal_tic          the thing they do that nobody else does
never_says          a word, register or move this person will not use, even
                    under pressure
under_stress        how the voice changes when cornered — shorter, more formal,
                    cruder, silent
```

`never_says` and `under_stress` are the two that do work at stage 10, when scene
agents write beats. A positive description of a voice is easy to write and hard to
apply; a prohibition is directly checkable against a line of dialogue, and a
stress transform tells the scene agent what changes when the pressure lands.

---

## 8.3 State variables, and the finding that matters most here

`state_variables` is the field that decides what the rest of the story is able to
say about this entity. **Later layers may only modify variables declared here.**
Every event state change, every beat-level patch, every fold of the timeline runs
through this vocabulary. A variable that does not exist cannot be changed, and a
change that cannot be recorded did not happen as far as the graph is concerned.

The measured failure is in `docs/07-quality-evaluation.md` §21. The film's
antagonist was declared with three variables: `pursuit_phase`,
`escape_desire_revealed`, `status`. The scene-level clerk recording state changes
filled in its `not_expressible` field to say that Smith's **contempt, nausea and
humiliation** "are internal states not covered by the available variables". Three
variables for the film's antagonist.

The evaluator's verdict is the sentence to keep: **"The clerk is honest; the dossier
is thin."** Nothing downstream was wrong. Every check passed. The humiliation simply
had nowhere to live, and so the story's account of its antagonist is a story in
which he is never humiliated.

That failure arrives from the same place as the 9-entity result in §15.3 — a thin
superstructure written before anyone read the scenes — and it is the same failure
one layer down. In the bottom-up order the author has already read every scene the
entity appears in and every event draft that moves it, so the operative instruction
is inverted: **declare a variable for every state the events actually move.** The
event drafts of stage 3 wrote their state changes in free vocabulary precisely so
that this stage could count them.

Two practical rules follow:

- A variable that no event touches is not automatically wrong — an entity can have
  a stable property that matters — but a *majority* of untouched variables means the
  author wrote a character sheet rather than a state model.
- An event state change that no declared variable can express is a hard finding at
  the boundary. The `not_expressible` report from the clerk is the same signal
  arriving too late to act on; here it arrives while the dossier is still open.

Whether the inverted order actually produces fatter, better-fitted variable sets is
**unmeasured**. It is the mechanism by which it should, and the count of
`not_expressible` reports at stage 10 is the direct comparison against the top-down
arms already on disk.

---

## 8.4 The critic

One agent per profile, adversarial, holding the profile, the full script, the
entity's scene nodes and event drafts, and the craft sheet. Its single binding
constraint:

**Every objection must cite the script.**

An objection without a citation is deleted before the author sees it. This is the
same rule as stage 3's evidence array and it exists for the same reason: the failure
mode of a critic agent is not silence, it is fluent generic criticism. "The wound
could be more specific", "the voice needs more distinctiveness", "consider deepening
the internal conflict" — all true of almost every profile ever written, all costless
to produce, and all unactionable. A citation forces the critique to be about *this*
entity in *this* script.

The critic returns objections in a fixed shape:

```
claim       what is wrong with the profile
citation    the script text that shows it
severity    blocking | substantive | minor
remedy      what the profile should say instead
```

`severity: blocking` is reserved for a profile that contradicts the script — a
contradicted fact, a variable set that cannot express a change the events declare, a
`state` value that does not match its own `init`. Those must be fixed. Substantive
and minor objections are arguments the author may refuse, in writing.

### What the critic checks

The twelve items of `CRAFT_CHECKS` in `narrativeforge/craft.py` are written for
scene nodes; the subset that applies to a dossier, plus the character-specific
material from the full sheet:

1. **Three dimensions, and the third produced by the first two.** Egri via Frey:
   physiological, sociological, psychological. *Trace every trait to its root. If you
   cannot say what made a character this way, you do not know him and his motivation
   will read as arbitrary.* The critic's question is whether the psychology follows
   from the biography or floats above it.
2. **The ruling passion.** One central motivating force that is the sum of all the
   drives, present in the profile and consistent with what the entity does across
   its occurrence list.
3. **Inner conflict, named as two forces.** *A character with no inner conflict
   produces only pity, never engagement — and the work is melodrama.* The critic
   requires the two forces named and requires that the script show them pulling.
4. **Stereotype broken by contradiction, not by novelty.** The nun who loves comic
   books, not the whore with the heart of gold. And the contradiction must affect
   behaviour somewhere in the script, or it is decoration.
5. **The antagonist's motive is human, not villainous.** *Never give the antagonist
   a villain's motive when a human one will do* — the opposition must have a point
   of view that is logical, reasonable and sympathisable. This is a live failure in
   the measured runs: `docs/07-quality-evaluation.md` §8 records a generated scene
   that established the antagonist as the ceiling of power by pre-flattening his
   opponent, *flat in the specific way the injected craft sheet warns against — an
   antagonist with no equal force opposite him.* Injecting the sheet is not
   sufficient; something has to check against it.
6. **Maximum capacity.** *Would he really?* checked against the biography, and *what
   else could he do that is more ingenious?* A low-capacity character is fine;
   the idiot in the attic is not.
7. **Voice distinguishable with attributions removed.** Against `speech_signature`,
   and against the entity's actual lines in the script.
8. **The variable set can carry what the events do.** §8.3. This is the check with
   the clearest measured motivation and it is the one most likely to be skipped,
   because it is bookkeeping rather than craft.

For locations, objects, groups and concepts the craft criteria mostly do not apply
and the critic's job narrows to fidelity and sufficiency: does the profile
contradict the script, and can its state variables express what the events do to it.
That asymmetry is fine. A location does not need a ruling passion.

---

## 8.5 Revision, and its acceptance test

The author receives its own profile, the surviving objections, and revises once.
One round, not a loop.

The reason is measured and it is one of the more useful findings in
`05-model-behaviour.md` §5. A repair loop was observed live going from 89 validation
errors to 126 and **saving the result anyway**. Three separate bugs, all fixed, and
the general lesson stated at the end: *a self-correction step needs an acceptance
test, or it is just another way to introduce errors.*

So the revision is accepted only if it is not worse:

- schema violations after ≤ schema violations before
- every `blocking` objection is either resolved or explicitly refused with a reason
- no previously-satisfied check now fails
- the revision is not a stub (`05-model-behaviour.md` §4 — a document under 200
  bytes of JSON is a retry, not a node)

A revision that fails the test is rejected and the pre-revision profile is kept.
That is exactly the behaviour that produced `repair rejected: 0 -> 6 schema
error(s), reverting` twice in a live run, both of which would previously have been
saved as damage.

A second critic round is available but off by default. There is no measurement
showing a second round helps, and there is a measurement showing that unchecked
iteration hurts.

---

## 8.6 Boundary check before stage 7

Decidable from data:

- every entity referenced anywhere in the tree has a profile
- every `state` key matches a `state_variables` key exactly, and every value equals
  its declared `init`
- every scalar variable's `init` lies inside its declared `range`; every enum's
  `init` lies inside its `domain`
- every event state change names an entity that exists and a variable that entity
  declares, at a value inside that variable's domain — the value-domain half of this
  was an explicit recommendation in `docs/07-quality-evaluation.md` §17 after a
  grounding post-check caught **1 of 6** real state-change violations by checking
  ownership only
- every relationship key is a real entity id
- every `plots` entry is a real plot id
- every string inside `profile` is ≤180 characters; no arrays of objects; every
  prose block is a sentence map
- `speech_signature` present for every `character` and `creature` — the shared
  schema cannot express a per-type requirement, so `validate.py` enforces it
- **every location named in a scene node resolves to a location entity**, and no
  single location carries more than ~60% of events

The last line is the collapsed-ontology guard from §15.4, restated at the layer that
can actually act on it.
