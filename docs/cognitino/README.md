# The CogniTino approach — an abstraction layer for the scene level

This folder records a change of strategy for the storytree scene layer, and its result.

**The short version.** Six scene-layer variants (V0–V5) were tried, all doing the same thing:
ask one model to write a whole scene node — observable facts and inner life together — in one
pass. V4 and V5 cleared the quality bar at 4.16 and 4.06, but neither separated from the much
simpler V1 at 4.02, and the weakest dimension across every arm was **emotional intelligence**
(2.40 → 3.67). Seven attempts at the same shape produced the same ceiling.

This is a different shape. The scene node is built in **two layers by two different systems**,
and the split is the point:

```
  Project Alexandria  ──►  what the screenplay STATES        (Perception layer)
                              beats, entities, state changes, ordered
                                        │
                                        ▼  grounded_in pointers
  CogniTino           ──►  what it IMPLIES                   (Abstraction layer)
                              mental states, theory of mind, authorial intent
```

The resulting object is called a **Scene Community** — see
[scene-communities.md](scene-communities.md). The name is literal rather than decorative: in
the storytree *tree* it is one node at the scene layer, but its internal structure is a
densely interconnected subgraph that is sparsely connected to anything outside it, which in
graph terms is a community. Two views of one object; the tree says where the scene sits, the
graph says what it is made of.

It is the union of `perception` (the Knowledge Unit) and `abstraction` (evidence-linked
inferences about minds). Nothing in the abstraction layer may exist without a pointer into the
perception layer.

---

## Why this might beat V0–V5

The V-series asked one model, in one pass, to be both a faithful recorder and an insightful
reader. Those are opposing dispositions — the first is penalised for going beyond the text,
the second is worthless if it does not. The measured consequence was visible across all six
arms: fidelity and completeness ran ~4.5, emotional intelligence ran ~3.0.

The same finding appeared once already in this project and was acted on once already:
splitting facts from minds into pass A and pass B took emotional intelligence 2.80 → 3.67.
This is that split taken to its conclusion — the two passes become two *systems* with
different contracts, different schemas, and different checks.

It also directly targets the rubric dimensions that have never scored well:

| Rubric dimension | What the abstraction layer supplies |
|---|---|
| **S2** beat-level mental simulation | `mental_state` objects per beat, per character |
| **S3** whole life — characters are not puppets | `entity_trait`, `relationship`, and cross-scene arcs |
| **S4** perception across senses | `mental_state` covering perception, physiology, place |
| **F** psychological plausibility | `theory_of_mind`, nested, with falsifiers |
| **S1** state-change justification | `authorial_intent` and `consequence` naming what a change serves |

**The hypothesis was tested blind and it failed.** CogniTino scores **3.20** against V5's
3.76, V4's 3.64 and V1's 3.57 — significantly worse on all three (p ≤ 0.003), and it clears
the bar on none of the fifteen scenes. Emotional intelligence, the dimension the whole design
was aimed at, lands at **2.80** — below what the single-pass V-series already reached.

The diagnosis is a design error rather than a refutation of the architecture: the abstraction
windows are five scenes wide, so each scene gets a fifth of the attention, and 23% of scenes
came back with no inference about anyone's mind at all. The neighbouring layer's own
experiments in this same session had already measured narrower windows as the fix.

A second finding matters more than the first: blind scoring puts **V1, V4 and V5 all below
4.0 as well**, roughly 0.4 under their published figures. The bar the handshake records as
cleared has not, under blind conditions, been cleared by anything.

**The diagnosis was then tested and the fix produced exactly nothing.** Two-scene windows
raised objects per scene from 2.6 to 4.0 and cut the no-mind-object gap from 23% to 8%, and
the score moved **0.000** (p = 0.98): emotional intelligence gained 0.40, calibration lost
0.47. The 23% gap turned out to be partly correct restraint, and the rule I wrote against it
forced inner life onto twelve-word scenes.

Against the strongest arm the whole deficit is one dimension: CogniTino **beats V4 on
emotional intelligence** (+0.37) and loses **−1.13 on calibration**. Against V5 it loses on
all six — V5 does the same job better and shorter.

**Round 3 went back to V4 and deepened it in place** — V4's node untouched, a second pass
added alongside for inner life, theory of mind and justified causal links. It is the worst
arm of all three rounds: **3.63 → 2.57**. Emotional intelligence gained +0.07; fidelity lost
2.20 and calibration 3.07. Two measurable design errors: 20% of its causal links run backwards
through time (the scene index was never bound in the schema), and the pass ran identically on
every scene, putting 7.6 KB of analysis on a 27-word one.

**Nothing beats plain V4.** Across three blind rounds V4 and V5 are indistinguishable from
each other and every extension scores below both.

Full numbers, all three rounds, costs and limits in [`results.md`](results.md).

---

## What runs

Implementation lives in the Alexandria repository, because it builds on the KU layer:
`project-alexandria/screenplay/src/screenplay_ku/cognitino/`.

| Stage | Module | Parallelism |
|---|---|---|
| Perception | Alexandria KU extraction, best config (`narrow` windows + `detail` prompt) | 30 windows |
| Generation | one agent per 5 scenes drafts abstraction objects | 45 in parallel |
| Researcher | each agent searches for supporting **and contradicting** evidence | 45 × 2 rounds |
| Semantic connection | pairwise merge tree: 5 → 10 → 20 → 40 scenes | parallel per level |
| Editor | canonical entity naming, running map | **sequential by necessity** |

Every abstraction object carries `grounded_in` (beat references, schema-enforced),
`confidence` (ordinal), `assumptions`, and `falsifier`.

## Documents

| | |
|---|---|
| [**scene communities**](scene-communities.md) | **what the object is, explained for outsiders** |
| [**examples**](examples.md) | **three complete Scene Communities, as produced** |
| [adaptation](../../../project-alexandria/screenplay/docs/08-cognitino-adaptation.md) | what was taken from CogniTino, narrowed, added, and changed — with attribution |
| [results](results.md) | rubric scores against V0–V5, and what they support |
| [`reference/CogniTino-whitepaper.pdf`](../../reference/CogniTino-whitepaper.pdf) | the source paper |

## Source

CogniTino: *Bridging Implicit and Explicit Knowledge through Semantic Knowledge Graphs*,
whitepaper, 22 pp. The Perception/Abstraction distinction, the traceability principle, the
object taxonomy and the five-module decomposition are its. The narrative-specific object
types, schema-level grounding enforcement, the falsifier requirement, the merge tree, and the
seven checks are additions — see the adaptation document for the boundary.

---

## Evaluation harness — errors made, and what they cost

Recorded because the harness is the part most likely to be reused, and because three of
these were caught only by the judges reporting them rather than by any check.

| # | Error | Consequence |
|---|---|---|
| 1 | Exported the 17-dimension node rubric, not the six-dimension rubric that produced the V0–V5 scores | First-round numbers were not comparable to V4 = 4.16 at all. Caught before reporting. |
| 2 | `KEY.json` left in the directory the judges were told to read from | Two of three judges saw the arm→system mapping and reported it. Blind compromised; batch discarded, key moved to a separate vault. |
| 3 | Normalisation joined the abstraction arm's ordered beats into one string | Destroyed the structure the rubric asks about, and would have scored an arm down for a property the *normaliser* removed. |
| 4 | Regenerated the pack directory while a judge was still reading it | Deleted that judge's in-progress score file mid-run. |

Errors 2 and 4 are operational; 1 and 3 would have produced confident wrong numbers, which
is the failure mode this project keeps meeting. In particular **3 is the same species as the
eight measurement errors in the handshake** — an apparatus quietly measuring something other
than what it claims — committed inside the harness built to avoid them.

Two rules follow, and they are cheap:

- **Never point a judge at a directory that contains the answer key.** Withheld means
  physically absent, not merely unmentioned.
- **Never mutate a directory a running agent is reading.** Regenerate into a new path.

### What the blinding can and cannot do

Blinding here is **label-level, not structural**. The arms are different systems producing
genuinely different objects: the abstraction arm carries beat-reference evidence and
falsifiers on its mind entries, and a careful judge could infer from that which arm is new.
Removing those fields would hide the properties actually under evaluation, so they stay and
the limitation is stated rather than papered over.

One finding survived the discarded round and is worth keeping because it is
rubric-independent: **every arm scores 1 on off-scene life and on perception across senses**,
because no arm's schema has a slot for either. That is a defect in the node contract, not in
any variant, and no arm flagged it.
