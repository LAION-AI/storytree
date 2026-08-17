# The swarm's first two runs, and what they showed

Written 17 August 2026. Companion to [`../distill/WHITEPAPER-SWARM.md`](../distill/WHITEPAPER-SWARM.md)
(the design), [`experiments/EXP-003-swarm-first-run.md`](experiments/EXP-003-swarm-first-run.md)
(the evaluation protocol), and [`../distill/swarm.py`](../distill/swarm.py) (the code).

**One-line summary: the architecture does what it was built to do, the
implementation did not, and the second run is honest but not yet good.**

---

## 1. What was built

The top-down pipeline wrote a story root first and everything else beneath it.
Four rubric passes traced its worst failures to that single decision: nine
entities declared where thirty to forty were needed, then all twenty-two events
at the one location that existed, then an ending placing a character somewhere
her own state model could not hold her. No individual call was wrong. **A thin
superstructure strangles every layer beneath it, silently, while passing every
schema check.**

The swarm inverts the direction. Eight stages, all parallel within themselves:

| Stage | Units | What it does |
|---|---|---|
| 1 | 224 | one agent per scene, blind of any tree |
| 2 | 56 | event boundaries by sliding window, three passes |
| 3 | 37 | one draft per event, each speculating about a plot that does not exist yet |
| 4 | 8 | plots induced from those speculations, one doctor per plot |
| 5 | 4 | canonical entity lists — agents, locations, objects, concepts |
| 6 | 40 | one profile per entity |
| 7 | 1 | the story root, written last |
| 8 | 7 | exposé plus five single-criterion doctors |

Three rules govern the code, each one earned by an earlier failure:

1. **Anything decidable from data on disk is decided in code.** A model asked
   whether a speaker is in a scene will sometimes get it wrong; a function will
   not.
2. **One narrow task per call.** Models divide a fixed output budget across
   whatever is requested rather than scaling to it.
3. **Never grade against a list this apparatus generated.** That measures
   compliance, not correctness.

---

## 2. The first run: 373 of 373 calls succeeded, and it was worthless

18.4 minutes for the whole 224-scene screenplay. Every call returned valid JSON.
The protocol recorded 71 check violations across eight stages, which looked like
a good first result.

It was not a result at all. An evaluation pass found this line:

```python
text = script[scene.start:scene.end] if hasattr(scene, "start") else ""
```

`Scene` carries `start_char` and `end_char`. There is no `start`. So `hasattr`
returned False for all 224 scenes, the guard substituted an empty string, and
**every agent received a blank scene** — writing fluent, schema-valid nodes from
the surrounding script alone.

Measured against the screenplay rather than against anything the harness
authored:

| | |
|---|---|
| Quoted evidence spans occurring in the scene they describe | **5.2%** (10 of 193) |
| Nodes best-matching their own scene by word overlap | **7.1%** (16 of 224) |
| Same, for the third act | **0 of 42** |

A second bug compounded it. `script[:120000]` on a 140,172-character file
**deleted the entire third act** — 42 scenes that no agent ever saw. Nodes were
produced for all of them anyway, and nothing in the protocol recorded the
truncation.

### The lesson, which is not "check your attribute names"

A guard that substitutes empty input for missing input is worse than no guard.
It converts a crash — loud, immediate, unmissable — into a confident wrong
answer that passes every downstream check. Every stage below stage 1 then worked
correctly on fabricated input, which is why the run looked healthy: stage 2
grouped the hallucinated scenes faithfully, stage 5 unified their invented
names, stage 8 wrote a synopsis of a story that had been reconstructed from
recall.

**Absent input must stop the run.** That is now an assertion, not a guard.

---

## 3. The canary

The evaluation suggested a check costing one call per run: give one agent a
deliberately blank scene. Anything it writes is recall, because it has nothing
else to write from.

It fired on its first execution:

```
canary (blank scene): model WROTE ANYWAY — recall is reaching the output
```

That is the whole mechanism of the failure in one line. The model does not
decline when it has no input; it produces something plausible. Given a famous
film, plausible and correct look identical from inside the pipeline.

This check would have caught the bug at scene two rather than after a full run
and an evaluation pass.

---

## 4. The corrected run

Four fixes: read the right attribute and assert non-empty; window the context
around the scene rather than truncating the head of the file; add a
correspondence check; add the canary.

| Stage | Time | Calls | Output tokens | Violations |
|---|---|---|---|---|
| 1 · scenes | 6.3 min | 224/224 | 97,475 | 285 |
| 2 · boundaries | 1.5 min | 56/56 | 32,043 | 1 |
| 3 · events | 4.6 min | 38/38 | 54,553 | 58 |
| 4 · plots | 5.5 min | 8/8 | 5,296 | 1 |
| 5 · entities | 5.5 min | 5/5 | 38,389 | 0 |
| 6 · profiles | 1.7 min | 40/40 | 36,147 | 1 |
| 7 · root | 0.5 min | 1/1 | 741 | 0 |
| 8 · exposé | 0.4 min | 7/7 | 3,140 | 0 |
| **total** | **20.5 min** | **373/373** | **268,087** | |

### Did the fix work? Partly, and the honest number is uncomfortable

| Measure | Run 1 (blank scenes) | Run 2 (real scenes) |
|---|---|---|
| Content-word overlap with the correct scene ≥30% | 6% | **25%** |
| Node matches its own scene better than a random one | — | **56%** |

The fourfold rise shows real text is reaching the model and changing what it
writes. But 25% is weak, and **56% is barely above the 50% a coin would give.**

This is not yet a working reconstruction. It is a pipeline that now receives its
input correctly and still leans heavily on something other than that input.

Two candidate explanations, neither yet tested:

- **Context dominance.** A scene may be 200 characters against a 100,000-character
  context window. The scene is there; it is also 0.2% of what the model is
  reading.
- **Recall.** The canary proves the model will write without input. With a famous
  film it may prefer recall even when input is present.

These are distinguishable by one experiment: run the same pipeline on
`reconstruct/runs/tideline`, a synthetic script no model can have memorised. If
correspondence rises there, the problem is recall. If it does not, it is context
dominance. That experiment is cheap and has not been run.

---

## 5. A fifth measurement bug, in a check written the same day

Stage 1 reported 285 violations, 216 of them "no evidence span occurs in the
scene it describes". Before reporting that as a quality finding, the check
itself was examined.

The schema asked for `evidence: "What in the scene shows this."` — an invitation
to *describe*. The model described:

> "She slowly puts her hands behind her head in response to the BIG COP's command."

The check tested whether that string occurred **verbatim** in the scene. It does
not, because it is a paraphrase, correctly produced as instructed. So 216 of the
285 violations were the harness marking compliant output wrong.

This is the **fifth** instance in this project of the same failure shape:

| # | Check | What it actually did |
|---|---|---|
| 1 | trajectory flatness | tested a field the schema never had |
| 2 | leak detector | tokenised raw JSON, so punctuation blocked every match |
| 3 | grounding | read another schema's field names |
| 4 | arm comparison | averaged over different node counts and compared the results |
| 5 | correspondence | tested for a quote where the schema asked for a paraphrase |

**Every one produced a confident number computed over the wrong thing, and not
one failed loudly.** Three were caught by an independent evaluator, one by
recomputing arithmetic, one by reading the schema next to the check.

The fix here was to change the *contract*, not the check: `evidence` now demands
a verbatim span of at least 25 characters copied from the scene. That makes
correspondence exactly decidable rather than statistically estimated — and the
next measurement will mean something.

---

## 6. What the inversion does prove

Set aside the implementation. The architectural claim was that reading first
prevents the under-declaration that strangles everything below. On that, the
evidence is clear:

| | Top-down | Swarm |
|---|---|---|
| Location entities | **1** | **23** |
| Concept entities | **0** | **13** |
| Events carrying a reversal | 0 of 22 | **11 of 37** |
| Total entities | 36 | 104 |

The top-down run could not move its story to a second location because only one
existed. It could not track the antagonist's humiliation because he had three
state variables. Neither constraint appears here: the layers that need places and
mechanisms have places and mechanisms, because they were derived from scenes that
actually contain them.

**And it is fast.** 20.5 minutes for a 224-scene feature, 373 calls, none failed.
The equivalent top-down run with a feedback loop was estimated at 19 hours. The
difference is not hardware — it is that every stage is parallel within itself.

---

## 7. What is worse than the top-down pipeline

Two things, recorded because a one-sided report is not worth having:

**Stage 5 produces a flat list, not a typed graph.** 104 entities with no
salience ordering, an antagonist split across two identifiers, and alias strings
whose canonical form depends on capitalisation. The top-down run produced 36
typed, patch-addressable entities. Fewer, but usable by the fold.

**Stage 8 stops early.** The exposé reaches roughly two thirds of the story and
stops. The top-down exposé reaches the end, and the only structural difference is
that its schema requires an `ending_first` field. That is a one-line fix and it
demonstrates the general point: schema requirements outperform instructions.

---

## 8. Where this leaves the question of autonomy

Not ready, and for a reason worth stating precisely.

Everything that failed in these two runs failed **silently**. The empty scenes,
the deleted third act, the paraphrase-versus-quote mismatch — none of them
produced an error, a warning, or an anomalous number. The first run reported 71
violations across 373 successful calls and looked like a good day's work.

For an autonomous run over a hundred books, the requirement is not that nothing
goes wrong. It is that when something goes wrong, **a number moves**. The canary
is the first check in this system that satisfies that requirement by
construction: it has no input, so anything it produces is evidence of a specific
failure.

The next three steps, cheapest first:

1. **Run the corrected pipeline on `tideline`**, the synthetic script. Separates
   recall from context dominance and costs one run.
2. **Re-measure correspondence** with the verbatim-span contract, which makes the
   number exact.
3. **Give stage 5 a type system and stage 8 an `ending_first` field** — both
   one-line schema changes that address measured deficits against the top-down
   arm.

---

## Reproducing

```bash
python3 distill/swarm.py reconstruct/runs/matrix --out <dir> --per-endpoint 8
```

Eight vLLM endpoints on ports 8100–8107, one Qwen3.8-27B copy per A100. The
run's own protocol lands at `<dir>/protocol.json` with per-stage timings, token
counts and check violations.

The broken first run is kept at `reconstruct/runs/matrix/swarm_v1_empty_scenes`
as evidence rather than deleted.

*Source screenplays are read for structure and never copied into artifacts;
committed outputs contain structural fields only.*

---

# Part II — Optimising the scene layer

Added 17 August 2026. Everything below this line is the optimisation campaign:
what was tried, what it did, and what was learned. Written as it happens, so
failed attempts stay in.

## 9. The target, restated — and why the earlier metric was wrong

The goal is **not** to reproduce the screenplay's own sentences. It is to produce
a structure that a careful reader — or an Opus-class agent applying a rubric —
would call good, plausible, emotionally intelligent and complete.

A scene node may use entirely different words from the script, mention things the
script leaves implicit, or omit incidental detail, and still be right. What it
may not do is get the **core of the scene**, its **dramatic function**, or its
**given constraints** wrong.

This makes §4's headline number — 25% content-word overlap — a measurement of the
wrong thing. Word overlap tests paraphrase distance, and paraphrase distance is
not the target. It survives only as a **cheap negative signal**: a node with
near-zero overlap is probably describing a different scene, which is worth
catching. It says nothing useful above that floor.

### The evaluation method, defined before optimising

**Fixed sample, fifteen scenes**, chosen once and never changed, spread across
acts and lengths so an improvement cannot be an artifact of easy cases:

```
sc-003  sc-008  sc-015  sc-024  sc-039     act I
sc-056  sc-075  sc-097  sc-113  sc-129     act I/II
sc-148  sc-164  sc-182  sc-200  sc-215     act II/III
```

Lengths run from 12 to 511 words. **The median scene in this work is 45 words** —
which matters enormously and is discussed in §10.

**Two tiers of measurement**, and only the second decides anything:

*Tier 1 — mechanical, runs in seconds, gates the expensive tier.*

| Check | Why |
|---|---|
| Node produced at all | |
| Every `present` name occurs in the scene or its speaker cues | roster reality |
| At least one evidence span occurs verbatim in the scene | correspondence floor |
| No change where `before == after` | a change that changes nothing |
| Word overlap ≥ 10% | catches wrong-scene nodes only |

A variant failing tier 1 badly is not sent to tier 2. Judging costs real tokens
and a node describing the wrong scene does not need a rubric to reject.

*Tier 2 — Opus-5 rubric, the actual target.* Six dimensions, 0–5, anchored at
1/3/5, applied per scene with the scene text in view:

| Dimension | Question |
|---|---|
| **Fidelity** | Does this describe what happens, whatever words it uses? |
| **Completeness** | Is anything load-bearing missing? |
| **Specificity** | Could this node be pasted onto a different scene? |
| **Change reality** | Are the recorded changes real, and do they matter? |
| **Emotional intelligence** | Is what people want, fear and conceal read plausibly? |
| **Calibration** | Is the node's length and confidence proportionate to a scene this size? |

The last dimension exists because of the sample's shape. Half these scenes are
under 60 words. A 900-word analysis of a 12-word scene is a failure even if every
sentence in it is defensible, and no other dimension catches that.

**The bar to move on to the next layer: mean ≥ 4.0 with no dimension below 3.0**,
on the same fixed fifteen. Until then the scene layer is the only thing being
worked on.

---

## 10. Brainstorm — the full palette

Everything worth trying, before ranking. Effect is a guess and labelled as such;
cost is measured in what it takes to implement and run.

### A · Context

| # | Idea | Expected effect | Cost |
|---|---|---|---|
| A1 | **Cut the script context drastically** — scene plus two neighbours instead of 100k chars | **Large.** The median scene is 45 words against a 100,000-character window: the scene is 0.2% of what the model reads. This is the single most likely cause of weak correspondence | Trivial |
| A2 | No script context at all — scene only | Large, direction unknown; may lose who people are | Trivial |
| A3 | Structured context instead of prose: the scene-heading list, not the text | Moderate; keeps orientation at a fraction of the tokens | Small |
| A4 | Put the scene **last** in the prompt rather than first | Moderate; recency is usually stronger than primacy | Trivial |
| A5 | Repeat the scene text after the schema, so it brackets the instructions | Small–moderate | Trivial |

### B · Prompting

| # | Idea | Expected effect | Cost |
|---|---|---|---|
| B1 | **Length calibration**: state the scene's word count and require proportion | Moderate–large on the calibration dimension, which nothing currently addresses | Trivial |
| B2 | **Verbatim-quote evidence** (already changed) — makes correspondence exact | Moderate | Done |
| B3 | One worked example of a good node for a short scene | Moderate; few-shot usually beats instruction for format | Small |
| B4 | Explicit permission to write little: "a 12-word scene may need two changes and no psychology" | Moderate | Trivial |
| B5 | Forbid inference from outside the scene: "if it is not on this page, it is not in your node" | Moderate; directly targets recall | Trivial |
| B6 | Ask for a one-line "what this scene is doing in the story" separate from what happens | Small–moderate; may improve dramatic-function scores | Trivial |

### C · Scaffolding

| # | Idea | Expected effect | Cost |
|---|---|---|---|
| C1 | **Split into two calls**: literal facts first, then interpretation conditioned on them | Large if budget dilution applies here as it did elsewhere | Small |
| C2 | Per-character psychology as its own call, as the ensemble does | Large on emotional intelligence, at 2–4× the calls | Moderate |
| C3 | **Verification call**: a second agent asks "does this node describe this scene?" and returns a verdict | Moderate; catches wrong-scene nodes at generation time | Small |
| C4 | Retry with the mechanical violations fed back | Moderate; proven to work elsewhere in this project | Small |
| C5 | Beat-level decomposition before the node | Moderate–large on completeness; more calls | Moderate |

### D · Structural enforcement

| # | Idea | Expected effect | Cost |
|---|---|---|---|
| D1 | **Bind location and time as `const`**, speakers as `enum` — proven in EXP-002 | Moderate; removes a whole error class by construction | Small |
| D2 | Require `evidence` to be a span the checker can find, and reject at generation | Moderate | Small |
| D3 | Cap node length as a function of scene length in the schema | Moderate on calibration | Small |
| D4 | Give the previous scene's node as context for continuity | Small–moderate; risks propagating errors | Small |

### E · Model and decoding

| # | Idea | Expected effect | Cost |
|---|---|---|---|
| E1 | Lower temperature for the factual pass | Small–moderate | Trivial |
| E2 | Turn thinking **on** for stage 1 only | Unknown; measured elsewhere as no quality gain at 6× cost | Trivial to try |
| E3 | Two samples per scene, pick by mechanical score | Moderate at 2× cost | Small |

### F · Evaluation itself

| # | Idea | Expected effect | Cost |
|---|---|---|---|
| F1 | **Run the same pipeline on `tideline`**, a synthetic script no model can have memorised | Diagnostic, not an improvement: separates recall from context dominance | Small |
| F2 | Blind A/B — show a judge two nodes and the scene, ask which describes it | Strong signal, cheap per comparison | Small |
| F3 | Regenerate-the-scene test: from the node alone, can a model produce something recognisable? | Strong signal on completeness | Moderate |

---

## 11. Ranked plan

Ordered by expected effect per hour of work, not by expected effect alone.

| Rank | Try | Why first |
|---|---|---|
| **1** | **A1** — cut context to the scene plus neighbours | Largest suspected cause, trivial to implement, and one run answers it |
| **2** | **B1 + B4** — length calibration and permission to write little | Half the sample is under 60 words; nothing currently tells the model that |
| **3** | **D1** — bind location, time and speakers | Already proven in EXP-002; removes an error class rather than discouraging it |
| **4** | **C1** — split facts from interpretation | Budget dilution is the most reliable finding in this project |
| **5** | **B5** — forbid outside inference | Directly targets what the canary proved is happening |
| **6** | **C3** — verification call | Catches at generation what the checks catch after |
| **7** | **F1** — the `tideline` control | Diagnostic; tells us whether the remaining gap is recall or capability |
| **8** | **C2** — per-character psychology | Largest expected quality gain, but the most expensive, and only worth it once the cheap wins are in |

Ranks 1–3 are all trivial or small and can go in one variant. That is variant **V1**;
everything after is decided by what V1 measures.

---

## 12. V1 — context dominance confirmed, decisively

The first variant bundles ranks 1–3 of the plan: context cut from ~100,000
characters to the scene plus its two neighbours (A1), length calibration and
explicit permission to write little (B1, B4), outside inference forbidden (B5),
and location/time/speakers bound into the schema (D1).

Bundling means V1 cannot attribute its result to a single cause. That is
deliberate — the first question is whether the ceiling moves at all.

### Tier 1, both variants, same fifteen scenes

| Measure | V0 | V1 |
|---|---|---|
| Tier-1 score | 0.70 | **0.95** |
| Clean nodes (of 15) | 4 | **12** |
| Mean word overlap with the correct scene | 28% | **76%** |
| Nodes with a verbatim evidence span | 4/15 | **13/15** |
| Words per node | 188 | **161** |
| Model seconds | 388 | **86** |
| Input tokens | 398,500 | **25,411** |

**It is better, 4.5× faster and 15.7× cheaper at the same time.** That combination
is rare enough to be suspicious, so the per-scene breakdown matters more than the
means.

### The effect is concentrated in the short scenes, exactly as predicted

| Scene | Words | V0 | V1 |
|---|---|---|---|
| sc-056 | 12 | 0% | **100%** |
| sc-015 | 12 | 10% | **67%** |
| sc-024 | 23 | 9% | **89%** |
| sc-200 | 26 | 0% | **77%** |
| sc-215 | 27 | 0% | **56%** |
| sc-113 | 30 | 14% | **88%** |
| sc-164 | 57 | 3% | **75%** |
| sc-097 | 59 | 17% | **75%** |
| sc-129 | 76 | 86% | 88% |
| sc-003 | 157 | 52% | 85% |
| sc-008 | 204 | 73% | 85% |
| sc-182 | 237 | 17% | **86%** |
| sc-039 | 270 | 75% | **46%** ← regression |
| sc-075 | 342 | 39% | 72% |
| sc-148 | 511 | 33% | 60% |

Every scene under 60 words was at or near zero correspondence under V0 and is
now well above it. **The median scene in this work is 45 words**, so this is not
an edge case — it is most of the screenplay.

The mechanism is now hard to dispute. At a 100,000-character window, a 12-word
scene is 0.01% of what the model reads. It was not ignoring the scene; the scene
was not meaningfully present. Everything the node contained had to come from
somewhere else, and the canary already showed where.

**One honest regression**: sc-039, a 270-word scene, fell from 75% to 46%. The
rubric pass is asked to look at that one specifically and say what was lost.

### What tier 1 cannot say

That V1 is *better*, only that it is more anchored to its scene. The risk of
demanding verbatim evidence and cutting context is that a model stops
interpreting and starts transcribing — a node can be perfectly faithful and
useless. That question belongs to the rubric, and the answer is in
[`experiments/EXP-004-scene-variants.md`](experiments/EXP-004-scene-variants.md).

### A note on what this cost to find

The V0 configuration was not careless. Handing a model the whole script for
context is the obvious thing to do, and it is what every earlier stage of this
project did. It was wrong for a reason that is only obvious once stated: **the
useful context is not the largest context.** A window centred on the unit of work
beat a window fifteen times its size, on every measure including cost.

---

## 13. V2 — two passes, because structure and mind want opposite context

V1 established that cutting context anchors a node to its scene. But a scene read
in isolation cannot say why someone conceals something, what they believe another
believes, or what a silence costs. That information is not on the page; it
accumulated across the scenes before it.

So the two are separated, because they want **opposite** context:

| Pass | Sees | Produces |
|---|---|---|
| **A · facts** | the scene plus two neighbours (V1 exactly) | who is present, what changes, verbatim evidence |
| **B · minds** | pass A's facts, plus three scenes back and one forward | wants, feels, shows, beliefs about others, what connects back, what it sets up, dramatic function |

Pass B is explicitly *allowed* to go beyond the observable — that is its job — but
it must build on pass A's facts rather than replace them, and must mark which
claims are inferences.

### Result

| Measure | V0 | V1 | V2 |
|---|---|---|---|
| Tier-1 score | 0.70 | 0.95 | **0.95** |
| Clean nodes (of 15) | 4 | 12 | **12** |
| Word overlap | 28% | 76% | **74%** |
| Verbatim evidence | 4/15 | 13/15 | **13/15** |
| Words per node | 188 | 161 | **768** |
| Output tokens | — | 5,853 | 21,654 (3.7×) |

**The anchoring survives the added depth.** V2 keeps every tier-1 property of V1
while producing 4.8× more content — 38 mind blocks across fifteen scenes, each
with a stated basis, plus explicit links backward and forward.

The links are specific rather than generic. For one 76-word scene, pass B named
which earlier scene primed the audience for what happens here, and which later
one this makes possible. A single-pass reading of that scene could not have
produced either.

### Two problems, recorded now rather than discovered later

**The `inferred` flag is useless as written.** 37 of 38 mind blocks are marked
`inferred: true` — 97%. A flag that is almost always true carries no information.
Either the model is being honest (mental states genuinely are not observable, so
everything is inference) or the field is decorative. Both readings make it
worthless as a filter, which is what it was for. It needs to become a *degree*
— what fraction of this reading rests on this scene versus on what came before —
or it should be dropped.

This is the same shape as the five measurement bugs in §5: a field that looks
like it discriminates and does not.

**Pass B sees the following scene.** `sets_up` claims are therefore partly
hindsight, not forecast. For a reconstruction feeding distillation that may be
acceptable — the whitepaper argues the case for a sighted author — but it is not
what a blind reader could produce, and any use of these nodes as forecasting data
would be invalid. Recorded here so it is not later mistaken for prediction.

### What this does not yet show

Whether the extra 600 words per node are *good*. Three tier-1 properties are
unchanged, so nothing mechanical distinguishes V1 from V2 — the entire difference
is content that only a reader can judge. That is the rubric's job, and it is the
same question as V1's: more, or better?


---

## 14. Correction — the V1 headline was largely a measurement artifact

The rubric pass found a bug in the harness that invalidates §12's headline, and
it is the sixth instance of this project's recurring class.

`sp.parse()` returns `(cleaned_text, scenes)`, and the scene offsets index the
**cleaned** text. The variant runner discarded the cleaned text and sliced the
**raw** file with those offsets. The two differ by 6,235 characters, so drift ran
from 186 characters at the first sample scene to 6,083 at the last.

**Thirteen of fifteen scenes were never shown to the model, in either arm.**

### Why the metric could not see it

`tier1.overlap` compares a node's evidence against the same slice the prompt was
built from. When that slice is wrong, a node faithfully describing it scores
*high*. So "28% → 76%" measured **obedience to a corrupted input** — and V1 was
explicitly designed to increase obedience to the supplied text.

A metric that shares its source of truth with the generator measures compliance,
not correctness. That is the rule this project wrote down after EXP-002 and then
broke again here.

### Re-run with correct slicing

| Measure | V0 broken | **V0 fixed** | V1 broken | **V1 fixed** | **V2 fixed** |
|---|---|---|---|---|---|
| Tier-1 score | 0.70 | **0.92** | 0.95 | **0.98** | **0.98** |
| Clean nodes (of 15) | 4 | **12** | 12 | **14** | **14** |
| Word overlap | 28% | **65%** | 76% | **76%** | 72% |
| Verbatim evidence | 4/15 | **12/15** | 13/15 | **15/15** | **15/15** |
| Words per node | 188 | 191 | 161 | 174 | 776 |

**Most of the claimed gain was the bug.** With correct input, V0 — the
configuration I called a failure — scores 0.92 and 65% overlap. The real effect of
the context cut is the narrower margin on the right: 0.98 against 0.92, 14 clean
nodes against 12, and **15/15 verbatim evidence against 12/15**.

That is a genuine improvement and a modest one. It is not the transformation §12
claimed.

### What survives unchanged

- **The 15.7× input-token reduction and 4.5× speedup.** Those follow from sending
  less context and are independent of what the context contained.
- **The mechanism.** The rubric pass measured fidelity against *the text each arm
  actually received* and found V0 2.07 against V1 4.73 — V0 answered partly from
  memory of the film even when its window contained the answer, V1 described what
  it was given and said where the page ran out. Context dominance is supported as
  a mechanism; its effect size on correct input is what has just been corrected
  downward.
- **V2's structure.** Anchoring survives the added depth on correct input too:
  identical tier-1 score and verbatim rate to V1, at 4.5× the content.

### The rubric verdict, on the corrupted run

**V0 1.53/5, V1 1.78/5** against a bar of 4.0 with no dimension below 3.0. Both
fail, and both were scored on nodes describing scenes the models never saw, so
the numbers bound nothing except how well a model writes about the wrong page.
The rubric must be re-run on the corrected outputs before any verdict stands.

One finding from it survives the bug, because it was measured against what each
arm actually received: **V1 is not merely more literal.** Its strongest
interpretive moments in the sample came from the arm instructed to stay on the
page. The predicted cost of demanding verbatim evidence — a model that
transcribes instead of reading — did not appear.

### The fix, and the class

`script, scenes = sp.parse(raw)` in five files. The same pattern was present in
`swarm.py`, `run_ensemble.py`, `measure_addendum.py` and `run_local_matrix.py`;
`experiment_scaffold.py` was already correct.

And a real guard, since the previous one checked only that the slice was
non-empty and passed a misaligned window unchanged:

```python
def _assert_supply(sid, scene, text):
    if not text.strip():
        raise ValueError(f"{sid}: empty scene text")
    q = (scene.start_quote or "").strip()
    if q and _loose(q[:40]) not in _loose(text[:400]):
        raise ValueError(f"{sid}: slice does not start with the scene's own anchor")
```

`Scene.start_quote` and `end_quote` already existed for exactly this and were
unused. **Presence is not integrity** — that is the third time a guard in this
project has checked the cheaper of the two.

### The sixth entry in the table

| # | Check | What it actually did |
|---|---|---|
| 6 | scene-correspondence overlap | compared node evidence against the corrupted slice the prompt was built from, so a faithful node scored high on the wrong scene |

Every one of the six produced a confident number over the wrong thing. Five were
caught by an independent reader; one by recomputing arithmetic. **None was caught
by the pipeline itself**, which is the finding that matters for the autonomy
question in §8.
