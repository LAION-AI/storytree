# Scene-layer experiments — raw data and method

Every number from the scene-layer optimisation campaign, with the method that
produced it, in enough detail to reproduce or to dispute. Written for later use
as paper material, so it records what was tried and failed alongside what worked.

Companion to [`12-swarm-results.md`](12-swarm-results.md) (the narrative) and
[`experiments/EXP-004-scene-variants.md`](experiments/EXP-004-scene-variants.md)
(the rubric protocol).

---

## 1. Task

Given one scene of a screenplay, produce a structured node recording who is
present, what changes, what in the text shows each change, and — in later
variants — what the people in it want, feel and conceal.

**The target is not reproduction.** A node may use entirely different words from
the source, surface something the text leaves implicit, or omit incidental
detail, and still be correct. It may not get the core of the scene, its dramatic
function, or its given constraints wrong. This is why word overlap is used only
as a floor and never as the headline.

## 2. Materials

| | |
|---|---|
| Model | Qwen3.8-27B-Uncensored-FP8, one copy per GPU |
| Serving | vLLM, 8 × A100-80GB, ports 8100–8107 |
| Decoding | temperature 0.7, thinking disabled via `chat_template_kwargs` |
| Schema | enforced by grammar (`response_format: json_schema`) |
| Source | one feature screenplay, 224 parsed scenes, 133,937 characters cleaned |
| Code | `distill/scene_variants.py` |

Scene-length distribution of the source, which several design decisions depend on:

| statistic | words |
|---|---|
| n scenes | 224 |
| median | 45.0 |
| mean | 105 |
| 25th pct | 22 |
| 75th pct | 125 |
| 90th pct | 270 |
| max | 714 |

**The median scene is 45 words.** Half the work is shorter than three sentences,
which turns out to drive most of what follows.

## 3. Sample

Fifteen scenes, fixed before the first run and never changed, chosen to spread
across acts and across the length distribution:

| scene | act | words | speaker cues |
|---|---|---|---|
| sc-003 | I | 157 | 1 |
| sc-008 | I | 204 | 1 |
| sc-015 | I | 12 | 0 |
| sc-024 | I | 23 | 0 |
| sc-039 | I | 270 | 1 |
| sc-056 | I | 12 | 1 |
| sc-075 | II | 342 | 7 |
| sc-097 | II | 59 | 2 |
| sc-113 | II | 30 | 0 |
| sc-129 | II | 76 | 3 |
| sc-148 | II | 511 | 3 |
| sc-164 | II | 57 | 2 |
| sc-182 | III | 237 | 3 |
| sc-200 | III | 26 | 1 |
| sc-215 | III | 27 | 1 |

Fifteen is small. Every claim below is reported with that in mind, and the
rubric evaluator was explicitly authorised to return *indistinguishable* — which
it did, once.

## 4. Variants

| | context given | mind pass | notes |
|---|---|---|---|
| **V0** | scene + ~100,000 chars of script | — | the original production prompt |
| **V1** | scene + 2 neighbours | — | length calibration; outside inference forbidden; location/time/speakers bound in schema; evidence must be verbatim |
| **V2** | V1, then minds | always | pass B sees 3 scenes back **and 1 forward** |
| **V3** | V1, then minds | always | pass B sees 3 back and the **6 following events**, never a later scene |
| **V4** | V1, then minds | if ≥150 words | may return an empty `minds` list; `grounding` checked against `basis` |
| **V5** | V1, then minds | if ≥2 speaker cues, or 1 cue and ≥ the work's own 75th percentile | + instruction on stated-but-unremarked concealment |

### Why V3 exists

This reconstruction produces **training data**, so the context in each example
must match what a model will hold when it generates. At top-down generation time
the event layer above a scene already exists and may be shown in full, including
later events; the following scenes do not exist yet and must not be. V2 withheld
later events and showed a later scene — wrong on both counts, in opposite
directions, and only one of the two looks like caution.

### Why V5 exists

V4's gate is an absolute word count fitted to this screenplay. Measured: a
150-word threshold opens on 22% of these 224 scenes. On a work whose median scene
is 200 words the same threshold opens on nearly everything and the gate stops
gating. V5 replaces it with a signal that means the same thing in any screenplay —
whether there is an exchange — plus a percentile drawn from the work itself.

## 5. Measurement

Two tiers. Tier 1 is mechanical and gates tier 2; tier 2 decides.

### Tier 1 — decidable from the text

| check | what it catches |
|---|---|
| every `present` name occurs in the scene or its speaker cues | invented cast |
| at least one evidence span occurs **verbatim** in the scene | wrong-scene nodes |
| no change where `before == after` | changes that change nothing |
| content-word overlap ≥ 10% | a floor, not a quality measure |
| `grounding` agrees with the block's own `basis` *(V4 onward)* | a provenance field that contradicts the sentence beside it |

### Tier 2 — the rubric

Opus-5, six dimensions, 0–5, anchored at 1/3/5, applied per scene with the scene
in view. **Fidelity, completeness, specificity, change reality, emotional
intelligence, calibration.**

Calibration was added because of the sample's shape: a 900-word analysis of a
12-word scene is a failure even if every sentence in it is defensible, and no
other dimension catches that.

**Bar: mean ≥ 4.0 with no dimension below 3.0.**

## 6. Raw tier-1 results

| | V0 | V1 | V2 | V3 | V4 | V5 |
|---|---|---|---|---|---|---|
| tier-1 score | 0.917 | 0.983 | 0.983 | 0.967 | 0.967 | 1.000 |
| word overlap | 65% | 76% | 72% | 77% | 79% | 79% |
| verbatim evidence | 12/15 | 15/15 | 15/15 | 14/15 | 13/15 | 15/15 |
| words per node | 191 | 174 | 776 | 786 | 476 | 600 |
| output tokens | 6,579 | 6,310 | 21,520 | 21,891 | 13,824 | 16,649 |
| mind pass ran | — | — | — | — | 6/15 | 9/15 |
| grounding contradictions | — | — | — | — | 4 | 7 |

**A comparability warning about the `clean` count**, which is why it is not in
the table above. The grounding check was added at V4 and writes into the same
problem list `clean` is computed from. V4 reads 10/15 against V3's 13/15, which
looks like a regression and is not one — on the basis the earlier arms were
scored on, V4 is also 13/15. Any table comparing `clean` across V3 and V4 is
comparing two definitions.

## 7. Raw rubric results

| | V0 | V1 | V2 | V3 |
|---|---|---|---|---|
| **overall mean** | 3.58 | **4.02** | 3.61 | 3.62 |
| lowest dimension | emotional intelligence 2.40 | emotional intelligence 2.80 | calibration 2.13 | calibration 2.20 |

No arm clears the bar. Each fails on exactly one dimension, and the two failures
are opposites: V1 is too thin on inner life, V2 and V3 write too much for short
scenes.

### The result that matters more than the means

| comparison | outcome |
|---|---|
| scenes ≥ 150 words, V3 vs V1 on emotional intelligence | **6–0**, p = 0.031 |
| scenes < 60 words, V1 vs V3 on calibration | **8–0**, p = 0.008 |
| all scenes, V1 vs V3 overall | 9–4–2, **p = 0.27 — indistinguishable** |
| all scenes, V1 vs V0 overall | 10–0–5, p = 0.002 |

The difference between V1 and V3 is entirely an interaction with scene length,
and it is large exactly where the aggregate is noise. **Reporting only the means
would have shown nothing.**

### The one total separation in the whole comparison

| | V2 | V3 |
|---|---|---|
| nodes citing a later scene in `sets_up` | **15/15** | **0/15** |

This disqualifies V2 as training data regardless of how it reads, and it is the
only measure on which any two arms separate completely.

## 8. Errors found in the measurement itself

Recorded because they are the most transferable finding here. Seven instances,
all the same shape: **a confident number computed over the wrong thing, none
failing loudly.**

| # | check | what it actually did | caught by |
|---|---|---|---|
| 1 | trajectory flatness | tested a field the schema never had | reading the data |
| 2 | leak detector | tokenised raw JSON, so punctuation blocked every match | an independent reader |
| 3 | grounding | read another schema's field names | an independent reader |
| 4 | arm comparison | averaged over different node counts, then compared | recomputing |
| 5 | correspondence | tested for a quote where the schema asked for a paraphrase | reading the schema beside the check |
| 6 | scene slicing | sliced the raw file with offsets into the cleaned text — 13 of 15 scenes never reached the model, and the overlap metric could not see it because it compared against the same corrupted slice | an independent reader |
| 7 | clean count | a new check written into the list an older count is derived from | recomputing |

**Six of seven were found by re-deriving a number rather than by any check in the
pipeline.** For the autonomy question this is the central result: nothing in the
system detected any of them.

Number 6 is the most instructive. The metric shared its source of truth with the
generator, so a node faithfully describing a corrupted input scored *high* — and
the variant under test had been designed to increase faithfulness to the supplied
text. The published claim of 28% → 76% was largely that artifact; corrected, the
baseline scores 65% and the real effect is 0.98 against 0.92.

## 9. Reproducing

```bash
python3 distill/scene_variants.py --variant v5 --out <dir>
```

Writes one JSON node per sample scene plus `_tier1.json` with every mechanical
measure. The sample is hard-coded so arms remain comparable. Rubric scoring is a
separate pass; anchors are in `experiments/EXP-004-scene-variants.md`.

## 10. What is not established

- **V4 and V5 are not yet rubric-scored.** Their tier-1 numbers are real; their
  quality is not measured.
- **The predicted 4.09 for V4 is a post-hoc fit**, produced by re-slicing scores
  already collected using a threshold derived from the same data.
- **n = 15, one screenplay, one evaluator, one sample per cell** at temperature
  0.7. Within-condition variance is unmeasured and may exceed several of the
  differences reported.
- **The source is a well-known film.** Nothing in the design detects a model
  reproducing a received summary rather than reading structure. A synthetic
  control script exists on disk and the comparison has not been run.

---

## 11. Run status, 17 August

The rubric pass for V4 and V5 is **blocked** — the evaluator hit a weekly account
limit that resets 19 August. No V4 or V5 scoring exists; the partial file from
that run contains none.

All outputs are on disk and the arms remain comparable, so the pass resumes
without re-running anything.

### What can be said without the rubric

| | V0 | V1 | V2 | V3 | V4 | V5 |
|---|---|---|---|---|---|---|
| tier-1 | 0.917 | 0.983 | 0.983 | 0.967 | 0.967 | **1.000** |
| word overlap | 65% | 76% | 72% | 77% | 79% | **79%** |
| verbatim evidence | 12/15 | 15/15 | 15/15 | 14/15 | 13/15 | **15/15** |
| words per node | 191 | 174 | 776 | 786 | 476 | 600 |
| mind blocks per scene | 0 | 0 | 2.3 | 2.4 | 1.1 | 1.6 |
| output tokens | 6.6k | 6.3k | 21.5k | 21.9k | 13.8k | 16.6k |

V5 is the first arm to reach a perfect tier-1 score with 15/15 verbatim evidence,
at 76% of V3's tokens. **That is a floor, not a quality result** — tier-1 was
built to catch nodes describing the wrong scene, and a perfect score means only
that none does.

### One check that could be run, and what it does not prove

The rubric found that every arm missed a concealment the source states outright
in the sample's richest scene. V5 adds an instruction naming exactly that case.
Searching the four arms' nodes for that scene:

| arm | mind blocks | concealment vocabulary present |
|---|---|---|
| V1 | 0 | one term |
| V3 | 3 | none |
| V4 | 3 | one term |
| **V5** | 3 | **three terms** |

All three V5 blocks record a gap between what a character feels and what they
show, each grounded in the scene itself.

**This is keyword presence, not comprehension.** It shows the instruction changed
the vocabulary the model reaches for. Whether it caught *the* concealment the
evaluator identified — as opposed to producing concealment-flavoured language
around a different moment — a keyword search cannot distinguish, and treating it
as though it could would be the eighth entry in §8's table. The rubric decides
this, and it has not run.

---

## 12. Rubric results for V4 and V5, and two faults in my own harness

### Both clear the bar. Neither separates from V1.

| | V0 | V1 | V2 | V3 | **V4** | **V5** |
|---|---|---|---|---|---|---|
| **overall** | 3.58 | 4.02 | 3.61 | 3.62 | **4.16** | **4.06** |
| fidelity | | | | | 4.80 | 4.33 |
| completeness | | | | | 4.80 | 4.80 |
| specificity | | | | | 4.53 | 4.47 |
| change reality | | | | | 3.47 | 3.53 |
| emotional intelligence | 2.40 | 2.80 | | | **3.47** | **3.67** |
| calibration | | | 2.13 | 2.20 | **3.87** | **3.53** |

V4 and V5 are the **first two configurations to clear mean ≥ 4.0 with nothing
below 3.0**, and V4 lands 0.07 from the re-slice prediction of 4.09.

**But neither separates from V1**: 7–4–4 each, p = 0.55. V4 against V5 is 4–6–5.
**At n = 15, V1, V4 and V5 are one arm.** The defensible claim is the shape and
not the mean: emotional intelligence moved 2.80 → 3.47/3.67 while calibration
gave back only 0.13/0.47.

### The gate is the only recommendation that was actually tested

Neither model returned an empty `minds` list once in fifteen opportunities. Every
empty array on disk is **the gate skipping**, not the model declining — the gate
removed each scene where declining would have been right before the model saw
it. Recommendations 1 and 2 are confounded, and only the first fired.

Calibration recovered the same way. Where the pass runs it scores 3.17 / 2.89 —
indistinguishable from V3's 3.14 on comparable scenes. Where it is skipped,
4.33 / 4.50, because there the node simply *is* V1's node. **Every point of the
recovery is scenes the pass never touched.**

### The gates compared

| | false negatives | false positives |
|---|---|---|
| V4, fixed 150 words | 2 (skipped scenes with legible interiority) | 0 |
| **V5, transferable** | **0** | 1 |

V5's one false positive is a 57-word scene with two cues and nothing to read; the
pass wrote 1,255 words on a premise the preceding scene contradicts. **That
single node is the entire V4–V5 difference.** The fix is a conjunct rather than a
replacement: two or more cues *and* an actual exchange.

### The concealment was real

V5 is the only arm of six to quote the marked line in the scene all four earlier
arms walked past, and it identifies the concealed object correctly. V4 reaches
the same substance by inference without noticing the text said so outright.

So the keyword result in §11 was pointing at something real — but the caveat
recorded there was still right, because the same instruction produced three
false-positive concealment readings on the scene above.

### Two faults in the harness, both mine

**The grounding check annotates instead of gating.** `tier1()` fixes `score` from
the problems it can see; `check_grounding_field` appends afterwards. So seven
contradictions sat in V5's problem list while its score read **1.000**. EXP-004b
asked for check-and-fail; what shipped was check-and-pass.

**The verbatim check covered a tenth of the node.** It read
`what_changes[].evidence` — about 90 words of V5's 600-word average — and never
`minds[].basis`, which is most of the rest. That is how an arm reporting 15/15
verbatim shipped a block with fabricated dialogue in an unchecked field.

### Corrected tier-1, rescored from disk

| arm | as shipped | **corrected** | verbatim, full node |
|---|---|---|---|
| V1 | 0.983 | **0.983** | 15/15 |
| V3 | 0.967 | **0.633** | 14/15 |
| V4 | 0.967 | **0.900** | 13/15 |
| V5 | **1.000** | **0.883** | 15/15 |

**V5's perfect score was a score that could not see the column beside it.**
Corrected, V1 leads tier-1 — though partly for a trivial reason worth naming: V1
produces no mind blocks, so it cannot have grounding contradictions. A check that
only applies to arms doing more work is not a fair ranking, and the tier-1
comparison across arms with and without a mind pass should be read as two
separate tables.

This is the **eighth** entry in §8, and the first I introduced while fixing
another one.

### The evaluator's own caveat, which I am recording rather than discounting

> one evaluator, not blind to arm, scoring arms whose design I wrote — same
> threat as the last two reports, now compounding

Three consecutive reports share an evaluator who knows which arm produced each
node and had a hand in specifying them. The next measurement should be blind
A/B — nodes stripped of the `_mind_pass` field that currently labels the arm on
every one of them — at a larger n and with several samples per cell. Until then,
"both clear the bar" is a result about fifteen scenes read once by someone who
knew what they were looking at.
