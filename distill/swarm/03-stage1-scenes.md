# 3 · Stage 1 — the blind scene agent

One agent per scene. It receives the complete script and one scene's text. It
returns a scene node. It does not know that a story root, a plot list, an entity
table or an event layer exist, because at the moment it runs, none of them do.

All 224 run at once. Nothing in stage 1 depends on anything else in stage 1.

---

## 3.1 Two different blindnesses, on opposite axes

The word *blind* already has a meaning in this codebase and it is not this one, so
the distinction has to be made before anything else.

The existing reconstruction pipeline (`docs/03-reconstruction.md`) writes its
deliberation blind **to the scene text**. `BLIND_SYSTEM` gets the layers above plus
the scene's outer envelope — location, time of day, roster, approximate length —
and must decide what should happen. `SIGHTED_SYSTEM` then binds that decision to
the real text. The rule exists because a model that knows the outcome can justify it
effortlessly, and such analyses read as profound and contain nothing.

Stage 1 is blind on the other axis.

| | old blind transition | stage 1 |
|---|---|---|
| Sees the scene text | **no** | **yes** |
| Sees the superstructure | **yes** | **no** |
| Task | decide what should happen | record what is there |
| Product | a falsifiable forecast | a structural reading |

These are different artifacts for different purposes and neither replaces the other.
The forecast is the scientific yield of the old pipeline — the only falsifiable
prediction in the whole procedure. The stage-1 node is not a prediction at all. It
is an observation, and its value is that it is an observation nobody has told the
observer what to see.

A consequence worth recording as a limitation up front: **stage 1 nodes cannot be
used as evidence that the model understood anything.** The model has the script. Its
scene node being correct is a reading-comprehension result, not an insight result.
If the corpus is also meant to produce blind-forecast training triples, those must
be generated on a separate channel with its own context filter, and the second
descent (§10) must not be allowed to contaminate them. That channel is out of scope
here and the interaction is **unmeasured**.

---

## 3.2 Why blindness to the superstructure is required

The one-sentence version: the whole point of stage 1 is to **induce** structure from
what is there, and an agent handed a superstructure will **confirm** it instead.

That is not a supposition. It is the single most reproducible finding in
`docs/07-quality-evaluation.md`.

**Measured — the independent-writer dimension.** Dimension G asks two questions of
every node: could a different competent writer have landed here given exactly these
inputs, and could they have produced this *without* the inputs. Mean across all nine
scored nodes: **2.33 out of 5**, the weakest of the seven universal dimensions by a
wide margin. The anchor for 3 reads "essentially a restatement of the layer above in
the local vocabulary". Node 5's commentary is blunter: a one-line prompt "write a
character dossier for Neo from *The Matrix*" produces the same document, and "the
four reconstructed layers above it contributed nothing detectable".

**Measured — an agent will follow the layer above over the text in front of it.**
Node 7 was given a scene envelope whose `on_screen` roster listed exactly one
character, `BIG COP`. It wrote a full psychological block for Trinity and gave her
six lines. It had a reason: `lo-01.profile.significance.b01`, in the dossier it was
handed, says *"Trinity escapes through Room 303 in the opening."* An upstream claim
beat the roster. Across all three transitions, **0 of 3 specimens honour the
envelope's `on_screen` roster** — described in the evaluation as "a single,
reproducible, mechanically checkable failure and the most actionable finding".

**Measured — under-declaration upstream removes options downstream, silently.** The
forward arm's event layer placed 22 of 22 events at the only location that existed,
including four that the brief puts outside the simulation entirely. There was no
legal value meaning "outside". A scene agent handed a nine-entity table would
behave the same way: it would map what it read onto what it was permitted to say,
and the residue would vanish without a trace.

Stage 1 is the layer that has to notice the residue. It cannot notice it if it has
been handed a vocabulary that excludes it.

There is a real cost. Blind of the tree, a stage-1 agent cannot say what a scene is
*for* — it can describe a dramatic function locally ("a refusal that costs the
refuser standing") but not a structural one ("the midpoint reversal of plot 2").
That is the depth the old pipeline occasionally produced. It is not lost, it is
**deferred**: stage 10 rewrites every scene with the finished tree in hand, and §10
argues that this is when the depth becomes producible on purpose rather than by
luck.

---

## 3.3 What the agent is handed

Three things, in this order:

1. **The complete script**, verbatim. Byte-identical across all 224 calls.
2. **A binding block** of facts already known from parsing.
3. **The scene's own text**, sliced by anchor.

**Why the full script, if the point is blindness.** The script is not a
superstructure; it is the evidence. Blindness here means not being handed somebody
else's *reading* of the work. Withholding the work itself would produce a different
and worse failure — a scene cannot be read in isolation, because a callback needs
its setup, a name needs its introduction, and a reversal needs the thing it
reverses. There is also a mechanical reason: an identical 40,000-token prefix across
224 calls should cost prefill once (§12; prefix caching measured at 48.9× on
time-to-first-token, but **not measured across concurrent slots** — the pipeline's
largest unverified assumption).

**Why a binding block rather than an instruction.** EXP-002 is the experiment that
settles this. Same model, same scenes, same scaffold; the only change was moving
`scene_id`, `location` and `time_of_day` into the schema as `const`, and the
speaker set into an enum, emitted as the *first* property so the model writes the
ground truth into its own context before it reasons.

| Arm | n | In the right location | Off-roster speakers |
|---|---|---|---|
| baseline | 3 | 1/3 | 2 |
| +4,561 chars of instruction | 2 | **0/2** | 2 |
| **schema binding** | 3 | **3/3** | **0** |

The instruction arm was *worse than baseline* on location. All measured. The
generalisation the experiment supports is narrow but firm: **a grammar refuses what
a request only discourages**, and staying in the right room is a global consistency
property that an instruction cannot reach.

EXP-002 also carries two corrections that stage 1 must inherit, because they were
bugs that manufactured the failure they were meant to prevent:

- **The roster is the script's own speaker cues**, resolved to ids where possible —
  not `characters_in_scene()`, which unions cues with event participants. On sc-001
  the script had one speaking cue and the enum had three, so the schema *mandated*
  that two absent characters be listed as present, and the model complied. Stage 1
  has no event participants to union with, which removes this failure by
  construction.
- **No `minItems`/`maxItems` on the roster.** A fixed length does not verify
  presence, it mandates it. Silence has to be checked in both directions: speakers
  who should not be there, and roster members given nothing.

---

## 3.4 The node schema

The existing `SCENE_SCHEMA` in `narrativeforge/schemas.py` is the target shape, and
stage 1 emits a strict subset of it. The subset is defined by one rule: **a field is
in stage 1 if and only if it is derivable from the script alone.**

Everything `SCENE_SCHEMA` requires that is *not* derivable is exactly the set of
fields that name the tree:

| Field in `SCENE_SCHEMA` | Why it is not available at stage 1 |
|---|---|
| `primary_event`, `events` | the event layer is stage 2 |
| `primary_plot`, `plots` | the plot layer is stage 4 |
| `entry_states`, `exit_states` | keyed by declared state variables; the entity layer is stages 5–6 |
| `beats[].event_id` | same as `primary_event` |
| `target_words` | a budget the exposé and root allocate |
| `chapter` | a discourse division the exposé fixes |

Stage 1 emits, instead:

```
scene_id            const, from parsing
discourse_index     const, from parsing
location            const, from the slug line
time_of_day         const, from the slug line
narrative_mode      enum: scene | summary | reflection | frame

present             the surface forms, verbatim, as the script writes them
mentioned           entities referred to but not present, verbatim
summary             <= 30 words
action              third person, no direct speech, 60-160 words

changes             [ { who, dimension, before, after, magnitude } ]
dramatic_function   free text, LOCAL only
tension_in          0-100
tension_out         0-100
questions_opened    q01, q02, ...
questions_closed    keys opened by earlier scenes, if identifiable
continuity_facts    per present entity: present, conscious, position, holding, condition
someone_behaves_badly   who, what   (may be empty)

event_hint          free text: what larger unit of happening this appears to belong to
```

Four notes on the differences, each of which is load-bearing.

**`changes` names variables freely.** There is no entity layer, so there are no
declared variables and nothing to check ownership against. This is the case EXP-002
deliberately left unenforced for a different reason — "enumerating the union of all
entities' variables would permit exactly the failure worth catching while looking
like enforcement" — and at stage 1 it is not a choice at all. The consequence is
that stage 1's `changes` are *claims*, not writes, and §11 is explicit that they
must be treated as such until the entity layer exists to receive them.

**`magnitude` is bound to the five anchors as an enum, and stage 1 is the stage most
likely to break it.** The relevant measurement is the sharpest single result in the
evaluation:

| Arm | Magnitudes on an anchor |
|---|---|
| forward (inventing) | **127 / 127** |
| reconstruction (describing a source) | **19 / 84** |

Same schema file, same closed enum, same week. The evaluator's generalisation:
**formal compliance degrades under grounding load.** Stage 1 is pure grounding load
— 224 agents describing a source text — so the prior is that free-text magnitude
would be abandoned wholesale. Binding it as a decode-time enum is the EXP-002 fix
applied to the failure that EXP-002's own result predicts.

**`event_hint` is the one speculative field**, and it is the seed for stage 2. It is
free text, one or two sentences, and the agent is told to reason from what it can
see rather than to invent a label. It is not binding on anything.

**`dramatic_function` is explicitly local.** An agent asked for a structural function
without a structure will produce one anyway — that is what a fluent model does — and
the measured tell is node 4's `interference` fields, which described thematic
relations where the schema asked for competition for the agent and the clock. A
field that invites a confident answer the inputs cannot support is a field that
manufactures the leakage the design exists to remove.

---

## 3.5 What stage 1 deliberately does not produce

The full transition contract in `narrativeforge/transitions.py` — `CRAFT_SCHEMA`,
`PSYCH_SCHEMA` with its eleven fields, `TOM_SCHEMA` to three degrees, `DYNAMICS_SCHEMA`,
`CONTINUITY_SCHEMA` — is not requested at stage 1. Two independent reasons, and both
are decisive on their own.

**It is structurally unavailable.** Read what `CRAFT_SCHEMA` actually asks for:
`audience_need` ("cite the audience band"), `genre_convention`, `theme_and_style`
("what the story root's theme, register and forbidden tics demand of this node"),
`why_now` ("why this node happens at this point in story time and could not have
happened earlier"). Every one of those references a story root that does not exist
until stage 7. An agent asked to fill them at stage 1 has no honest option.

**It would dilute the budget.** The measurement is `docs/05-model-behaviour.md` §1:
requesting four deep structures in one call yielded 2 of 4 complete, two of them
hollow (`entity: null`, one field filled of eleven) and 41 schema violations — at
the *same* total output length as requesting one. Restructuring into one deep
structure per call took the same scene from 18.0 violations and 1 of 7 complete
blocks to **0.0 violations and 6 of 6**, at an 80% token cost. Stage 1 asks 224
agents for one shallow structure each. That is the same principle applied at the
level of the pipeline rather than the scene.

The psychology arrives at stage 10, on a node that knows what it is for. §10 argues
that this ordering is why the depth becomes reproducible.

---

## 3.6 Divergent naming, and why it is tolerated here

224 independent agents will not agree on names. One writes `ALICE M.`, another
`Alice Miller`, a third `THE WOMAN IN THE DOORWAY` because that is the cue the
script uses in scene 6. This is accepted at stage 1 and repaired procedurally at
stage 5.

**Why not just hand them a canonical list.** Because producing one requires having
read the work, which is what stage 1 is for. A canonical list at stage 1 is a
superstructure by another name, and it carries the same failure mode: a
nine-name list handed to 224 agents does not produce nine-name consistency, it
produces 224 agents silently mapping everyone they read onto the nearest of nine
names. That is the location failure of §1 repeated one layer down, and it would be
*less* visible, because a name that resolves looks correct.

**Why divergence is cheap here specifically.** Because most of the merge is
decidable from data and must never reach a model at all (§11). Screenplay speaker
cues are literal strings in the source. If stage 1 records the surface form
**verbatim, exactly as the script writes it**, then the large majority of aliases
collapse by exact string match before any agent is involved. What is left for stage
5 is the genuinely hard residue: a character named in action lines who never speaks,
one person under two cues, a cue that is a role rather than a name, and the
distinction between a group and its members.

This is the reason the schema asks for `present` as surface forms rather than as
guessed identifiers. An agent asked to normalise a name is being asked to make a
merge decision alone, with one scene of evidence, 224 times, with no way to see the
other 223 decisions. That is the worst possible place to put that decision. Stage 5
makes it four times, with everything in view.

**Consistency within a node is still required**, and it is checkable: every name in
`changes.who` and in `continuity_facts` must appear in `present` or `mentioned`. That
is a set-membership test on one document and belongs in code.

---

## 3.7 Where this stage is most likely to be wrong

Three things, in order of how much they would cost:

1. **Magnitude compliance.** The prior from the measured 19/84 is bad and the
   mitigation (enum binding) is untested at this scale. If it fails, stage 1's
   `changes` become unusable as quantities while remaining usable as claims, and
   everything downstream that reads magnitude — the reversal floor, the
   scalar-change floor, the tension curve — degrades.
2. **`event_hint` correlated error.** Thirty agents guessing independently can still
   guess the same wrong thing, because they share a model and a prior about what
   stories are made of. Stage 2's three passes are designed against disagreement,
   not against agreement that is uniformly wrong. This is **unmeasured** and §14
   treats it as the design's most under-examined assumption.
3. **Silent thinness.** A 27B model asked for a 60–160 word `action` will produce
   one. Whether it produces a *reading* or a paraphrase is not schema-checkable, and
   the measured specificity score (C = 4.67, the model's strongest dimension) says
   the paraphrase will be vivid. Vividness is not the same as having noticed
   anything, and no counter in this pipeline currently distinguishes them.
