# Rubric scores, what they show, and where to go next

Status: 18 August 2026. Six scene-layer variants, scored by an Opus-5 evaluator
on six anchored dimensions across a fixed fifteen-scene sample.

Companion to [`13-scene-experiments-data.md`](13-scene-experiments-data.md) (raw
data and method) and [`experiments/EXP-004-scene-variants.md`](experiments/EXP-004-scene-variants.md)
(the evaluator's own reports).

**Headline: two configurations clear the quality bar, neither separates from a
third statistically, and the remaining headroom is not where I expected it.**

---

## 1. The scores

### Per dimension, all six arms, n = 15

| Dimension | V0 | V1 | V2 | V3 | **V4** | **V5** |
|---|---|---|---|---|---|---|
| Fidelity | 4.20 | 4.60 | 4.20 | 4.07 | **4.80** | 4.33 |
| Completeness | 4.00 | 4.47 | 4.40 | 4.47 | **4.80** | **4.80** |
| Specificity | 4.20 | 4.47 | 4.07 | 4.00 | **4.53** | 4.47 |
| Change reality | 3.27 | **3.80** | 3.67 | 3.53 | 3.47 | 3.53 |
| Emotional intelligence | 2.40 | 2.80 | 3.20 | 3.47 | 3.47 | **3.67** |
| Calibration | 3.40 | **4.00** | 2.13 | 2.20 | 3.87 | 3.53 |
| **Overall** | 3.58 | 4.02 | 3.61 | 3.62 | **4.16** | 4.06 |

Bar: mean ≥ 4.0 with no dimension below 3.0. **V4 and V5 are the first two arms
to clear it.**

### Per scene, out of 30

`M` marks a scene where the mind pass ran.

| Scene | words | cues | V0 | V1 | V2 | V3 | V4 | V5 |
|---|---|---|---|---|---|---|---|---|
| sc-003 | 157 | 1 | 24 | **27** | 25 | 24 | 25 M | 25 M |
| sc-008 | 204 | 1 | 22 | **26** | 20 | 25 | 24 M | 24 M |
| sc-015 | 12 | 0 | **6** | 24 | 14 | 14 | 24 | 24 |
| sc-024 | 23 | 0 | 23 | 23 | 15 | 14 | 24 | **25** |
| sc-039 | 270 | 1 | 23 | 25 | 25 | **28** | 25 M | 26 M |
| sc-056 | 12 | 1 | 21 | 22 | 20 | 22 | 22 | **24** |
| sc-075 | 342 | 7 | 23 | 23 | **27** | 26 | 25 M | **27** M |
| sc-097 | 59 | 2 | 24 | 24 | 24 | 18 | **26** | **26** M |
| sc-113 | 30 | 0 | 25 | 26 | 19 | 19 | 25 | **26** |
| sc-129 | 76 | 3 | 24 | 26 | 22 | 23 | 25 | **26** M |
| sc-148 | 511 | 3 | 21 | 21 | 22 | 21 | **27** M | 25 M |
| sc-164 | 57 | 2 | 21 | 25 | 21 | 22 | **26** | 17 M |
| sc-182 | 237 | 3 | 19 | 23 | **27** | **27** | **27** M | 22 M |
| sc-200 | 26 | 1 | 24 | 24 | 19 | 19 | 24 | 24 |
| sc-215 | 27 | 1 | 22 | 23 | 25 | 24 | **25** | 24 |

### Statistical position

| comparison | outcome |
|---|---|
| V4 vs V1 | 7–4–4, **p = 0.55** |
| V5 vs V1 | 7–4–4, **p = 0.55** |
| V4 vs V5 | 4–6–5 |
| V1 vs V0 | 10–0–5, p = 0.002 |

**At n = 15, V1, V4 and V5 are one arm.** Only the V1-over-V0 gap survives a
significance test. What is defensible is the *shape*: emotional intelligence
moved 2.80 → 3.47/3.67 while calibration gave back 0.13/0.47.

---

## 2. Three things the per-scene table shows that the means hide

### 2.1 Routing between existing arms is nearly exhausted

An oracle that picks the best arm for every scene scores **4.31**. V4 scores
4.16. **Perfect routing is worth +0.16** — less than the noise between arms.

| arm | total /450 | mean | scenes won |
|---|---|---|---|
| V0 | 322 | 3.58 | 1 |
| V1 | 362 | 4.02 | 6 |
| V2 | 325 | 3.61 | 3 |
| V3 | 326 | 3.62 | 2 |
| **V4** | **374** | **4.16** | 7 |
| V5 | 365 | 4.06 | 8 |
| **oracle** | **388** | **4.31** | — |

This kills a whole family of proposals. Smarter gates, per-scene arm selection,
ensembling the six — all of it competes for 0.16 points. **The ceiling is not in
choosing between these arms.**

### 2.2 The real ceiling is short scenes, and it is a hard wall

Even the oracle leaves **62 of 450 points** unreachable. Where?

| scene | words | cues | best of any arm | gap to 30 |
|---|---|---|---|---|
| sc-200 | 26 | 1 | 24 | **6** |
| sc-056 | 12 | 1 | 24 | **6** |
| sc-015 | 12 | 0 | 24 | **6** |
| sc-215 | 27 | 1 | 25 | **5** |
| sc-024 | 23 | 0 | 25 | **5** |
| sc-164 | 57 | 2 | 26 | 4 |
| … | | | | |
| sc-039 | 270 | 1 | 28 | 2 |

**All five worst-ceiling scenes are 12–27 words with 0–1 speaker cues. None is
an exchange.** Median 23 words.

Two readings, and they imply opposite fixes:

- **The rubric is asking short scenes for something they cannot have.** A
  twelve-word slug line has no emotional intelligence to read and no change
  reality to speak of, so it is scored against a rubric designed for scenes that
  do. If so, the fix is in the measurement, not the pipeline.
- **A twelve-word scene is the wrong unit.** In a work whose median scene is 45
  words, many "scenes" are shots. Their meaning lives at the event level, and
  asking for a self-contained node is asking the wrong question.

**These are distinguishable by one cheap test** and it has not been run: score
five short scenes *as beats inside their event node* rather than as scenes, and
see whether the ceiling moves.

### 2.3 One gate error cost nine points

V5's regressions against V4:

| scene | V4 → V5 | why |
|---|---|---|
| sc-164 | 26 → **17** | gate opened, pass wrote 1,255 words on a premise the previous scene contradicts |
| sc-182 | 27 → 22 | both gate open — sampling noise |
| sc-148 | 27 → 25 | both gate open — sampling noise |
| sc-215 | 25 → 24 | neither gates open — noise |

**sc-164 alone is the entire V4–V5 difference.** V5's gate has perfect recall
(zero false negatives against V4's two) and one false positive: two speaker cues
in a scene with nothing to read.

The pattern is worth stating generally: **a gate that opens wrongly is far more
expensive than one that closes wrongly.** A skipped scene falls back to a good
V1 node; a wrongly opened one gets 1,255 words of confident invention.

---

## 3. Proposals

Ordered by expected effect per hour. Effects are labelled *predicted* unless
measured.

### Obvious — these follow directly from the findings

| # | Change | Rationale | Cost |
|---|---|---|---|
| **P1** | **Gate on ≥2 cues AND an exchange** — require alternating speakers, not just two names | V5's only failure; recovers ~9 points on one scene of fifteen | Trivial |
| **P2** | **Verify the mind pass against the previous scene** before accepting it | sc-164's invention is contradicted by sc-163, which the pass already receives | Small |
| **P3** | **Extend verbatim checking to `minds[].basis`** | 80% of a V5 node was unverified; already fixed, needs re-measuring | Done, unmeasured |
| **P4** | **Make the grounding check gate** | already fixed; V5's 1.000 was a score that could not see its own contradictions | Done, unmeasured |

### Non-obvious — these come from the ceiling analysis

| # | Change | Rationale | Cost |
|---|---|---|---|
| **P5** | **Stop treating short scenes as scenes.** Fold sub-40-word scenes into their event as beats and score them there | Five of fifteen scenes have a hard ~24/30 ceiling and all are short. This is the single largest pool of unreachable points | Moderate |
| **P6** | **Length-normalise the rubric** — or drop EI and change-reality for scenes with nothing to read | If the ceiling is a measurement artifact rather than a pipeline limit, every arm has been mis-scored on a third of the sample | Small |
| **P7** | **Two samples per scene, keep the one that passes tier-1.** At 45 tok/s the second sample is nearly free | Within-condition variance is unmeasured and may exceed several reported differences | Small |
| **P8** | **Blind A/B at n=40, three samples per cell** — strip `_mind_pass`, which currently labels the arm on every node | Nothing in three reports separates statistically. This is the only step that converts any of it into evidence | Moderate |

### Creative — worth trying, less certain

| # | Idea | Why it might work |
|---|---|---|
| **C1** | **Let the mind pass see the *event* it belongs to and nothing else of the future.** It already does; extend to letting it *revise* the event's entry/exit state where the scene contradicts it | The event layer is currently write-once. A scene that disproves its parent event should be able to say so |
| **C2** | **A second reader whose only job is to find what the first missed.** Not a critic scoring the node — a reader given the scene and the node and asked "what is in the scene that is not in this?" | The concealment all six arms walked past was *stated in the text*. A finding-pass is a different task from a scoring-pass |
| **C3** | **Adversarial paraphrase test for specificity.** Take a node, swap the character names, and ask a model which scene it describes. If it still matches, the node is generic | Specificity is currently judged by a human-like reader. This makes it mechanical and cheap |
| **C4** | **Let the model write the scene back.** From the node alone, regenerate the scene; compare to the original by semantic similarity | Directly measures completeness in the way the target actually cares about — semantic adequacy, not word overlap |
| **C5** | **Cross-scene consistency as a stage.** After all nodes exist, one pass reads each character's nodes in order and flags contradictions | No current check looks across scenes. State drift is exactly what the graph was built to prevent, and nothing measures it |
| **C6** | **Distil the gate.** Train a tiny classifier on (scene → does the mind pass help?) using the rubric deltas already collected | 90 labelled examples exist. A learned gate would transfer better than either hand-written rule |

---

## 4. Toward an autonomous pipeline

The quality bar is now cleared. **Autonomy is blocked by something else**, and
the evidence for it is unambiguous.

### Eight measurement errors, none caught by the pipeline

| # | Check | What it actually did | Caught by |
|---|---|---|---|
| 1 | trajectory flatness | tested a field the schema never had | reading data |
| 2 | leak detector | tokenised raw JSON; punctuation blocked every match | a reader |
| 3 | grounding | read another schema's field names | a reader |
| 4 | arm comparison | averaged over different node counts, then compared | recomputing |
| 5 | correspondence | tested for a quote where the schema asked for paraphrase | reading the schema |
| 6 | scene slicing | sliced the raw file with cleaned-text offsets — 13 of 15 scenes never reached the model | a reader |
| 7 | clean count | new check written into a list an older count derives from | recomputing |
| 8 | grounding gate | appended after the score was fixed, so contradictions could not lower it | a reader |

**Six of eight were found by an outside reader; two by recomputing. Zero by any
check in the system.**

For a hundred books unattended, the requirement is not that nothing breaks. It is
that **when something breaks, a number moves.** Only one mechanism in this
project satisfies that by construction: the blank-scene canary, which has no
input, so anything it produces is evidence of a specific failure.

### What autonomy needs, concretely

| | Mechanism | Status |
|---|---|---|
| **1** | Canary per stage — an input that should produce nothing | scene layer only |
| **2** | Every check verified against a case it must fail | none |
| **3** | Cross-arm numbers computed by one function, not per-arm code | partial |
| **4** | Supply integrity asserted, not supply presence | scene layer only |
| **5** | Cross-scene consistency pass | absent (C5) |
| **6** | Regenerate-and-compare as an end-to-end check | absent (C4) |

Item 2 is the one that would have caught most of the eight. **A check that has
never been shown to fail is not a check** — it is an assertion about the author's
intentions. Every one of the eight passed silently on data it should have
rejected, and a single negative test case per check would have exposed them.

### The honest position

Scene layer: **clears the bar, does not separate from a simpler configuration,
and rests on one non-blind evaluator reading fifteen scenes once.** The next
measurement should be blind and larger; the next engineering should be negative
test cases for every check.

Autonomy over a hundred books is not a quality problem any more. It is an
observability problem, and the score is currently 0 of 8.
