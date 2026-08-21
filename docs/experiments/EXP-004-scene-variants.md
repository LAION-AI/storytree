# EXP-004 · Cutting context at the scene layer — and the supply bug underneath it

> **Superseded below.** The offset bug this report diagnoses has been fixed and
> all arms re-run. **Everything in the original report's Frame A results and
> §"Is V1 better, or merely more literal" is measured on corrupted input and does
> not describe the prompts.** The corrected scoring, over four arms, is in
> [EXP-004b](#exp-004b--the-same-question-with-the-scenes-the-models-actually-saw)
> at the end of this file. The supply-bug diagnosis itself stands and is the
> reason the re-run exists.

**Status: inconclusive on its own question, and refuted as a measurement.** V1
scores **1.78/5** against the scenes it names, V0 **1.53/5**; four of six
dimensions sit below 3.0 in both arms, so V1 misses the ≥4.0 bar by a wide
margin. It misses it for a reason neither arm controls: **`run_variant` slices
the raw source file with character offsets computed on the *cleaned* text**, so
every scene agent in both arms was handed a misaligned character window that
drifts from 186 characters at sc-003 to 6,083 at sc-215. Thirteen of the fifteen
sampled scenes were never shown to the model at all.

The headline metric could not see this, because it scores the node against the
same misaligned window the prompt supplied. "Word overlap 28% → 76%" measures
how well V1 obeyed a corrupted input, which is exactly what V1 was built to do.

What survives is worth having. Scored against *the text each arm actually
received*, V1's fidelity is **4.73/5 against V0's 2.07** — V0 demonstrably
answers from memory of the film, quoting lines absent from its own window, while
V1 describes what is on the page and flags where the page cuts off. The
mechanism the experiment set out to test works. It was pointed at the wrong
text. n=15 scenes × 2 arms, single sample per cell.

> **The regression that was not one.** sc-039 was flagged as the sample's only
> loss (75% → 46% overlap). It is V1's second-best node in the sample and scores
> 19/30 against 7/30 for V0. It "regressed" because it stopped describing the
> window it was given and started describing the scene it was asked about.

---

## Question

`docs/12-swarm-results.md` §11 ranks **context dominance** first among suspected
causes of weak scene-layer correspondence: the median scene in this work is 45
words against a ~100,000-character window, so the scene is 0.2% of what the model
reads. Ranks 1–3 of that plan were bundled into one variant.

Does cutting context, calibrating length, and binding the scene's given facts
into the schema produce nodes a careful reader would call good, plausible,
emotionally intelligent and complete — or does it only produce nodes that
resemble the scene's surface more closely?

The target is explicitly **not** reproduction. A node may use entirely different
vocabulary, surface something the scene leaves implicit, or omit incidental
detail and still be right. It may not get the core of the scene, its dramatic
function, or its given constraints wrong.

## Prediction

*Recorded in `12-swarm-results.md` §10–11 before the run, and reproduced here
unchanged.*

| # | Claim as written | Outcome |
|---|---|---|
| P1 | A1 (cut context) has the **largest** expected effect of any single change | **Untested** — both arms received the wrong text; the confound swamps the arm difference |
| P2 | B1+B4 (length calibration, permission to write little) move the calibration dimension, which nothing currently addresses | **Supported, and bounded** — calibration 2.33 → 3.07, the only dimension to clear 3.0, but it cannot go below a ~110-word floor set by the schema, not by the model |
| P3 | D1 (bind location/time/speakers) removes an error class by construction, as in EXP-002 | **Refuted in this setting** — with a wrong body, binding welds a correct heading onto a false node and manufactures internal contradictions |
| P4 | B2 (verbatim evidence) makes correspondence exact | **Supported mechanically, void semantically** — 4/15 → 13/15 verbatim spans, all of them verbatim against the wrong text |

The risk registered in advance — that demanding verbatim evidence and cutting
context would make the model stop interpreting and start transcribing — is
addressed in §Is V1 better, or merely more literal.

## Design

Two arms over the same fifteen scenes, sampled across the feature, everything
else held fixed: same model, same decoding, same sample, one call per scene.

| Arm | Intervention |
|---|---|
| **v0** | Production prompt. Scene text plus `_window(script, scene)` — 60,000 characters before and 40,000 after |
| **v1** | A1 context cut to the scene plus its two neighbours · B1 scene word count stated with a required proportion · B4 explicit permission to write little · B5 outside inference forbidden · D1 `location`/`time_of_day` as `const`, `speaking` as `enum` over the script's speaker cues · B2 `evidence` required to be a verbatim span, `minLength` 25 |

V1 bundles five changes deliberately, since the first question was whether the
ceiling moves at all. It therefore cannot attribute a result to one cause — and
in the event, a sixth uncontrolled variable dominated both arms.

## Materials

| | |
|---|---|
| Model | `qwen3.8-27b`, 8 endpoints × 4 concurrent |
| Code | `distill/scene_variants.py` (`v0`, `v1`, `tier1`, `run_variant`) |
| Sample | `sc-003, 008, 015, 024, 039, 056, 075, 097, 113, 129, 148, 164, 182, 200, 215` of `reconstruct/runs/matrix` — 12 to 511 words, median 57 |
| Outputs | `reconstruct/runs/matrix/var_v0/`, `.../var_v1/` |
| Ground truth | `reconstruct/runs/matrix/script_map.json` + `script.normalized.txt`, offsets confirmed identical to `scriptforge.screenplay.parse` for all fifteen scenes |
| Screenplay | copyrighted; read for comparison, quoted only in fragments as evidence |

---

## The supply bug

`run_variant` reads the **raw** source file and parses it:

```python
script = Path(table["source_file"]).read_text(errors="replace")   # 140,172 chars
_, scenes = sp.parse(script)                                       # offsets into the 133,937-char CLEAN text
...
text = script[sc.start_char:sc.end_char]                           # sliced from RAW
```

`sp.parse` returns `(clean_text, scenes)`. The cleaned text is discarded with
`_`, and the scene offsets — which index the cleaned text — are used to slice the
raw one. The raw file is 6,235 characters longer, and the difference accumulates
through page headers, scene numbers, `(CONTINUED)` markers and revision slugs.

Measured drift for the sampled scenes, as the offset between where a scene
actually begins in the raw file and where the harness looked for it:

| Scene | words | drift (chars) | token overlap, delivered vs true |
|---|---|---|---|
| sc-003 | 157 | 186 | 0.72 |
| sc-008 | 204 | 264 | 0.71 |
| sc-015 | 12 | 598 | 0.05 |
| sc-024 | 23 | 1,147 | 0.00 |
| sc-039 | 270 | 1,808 | 0.11 |
| sc-056 | 12 | 2,197 | 0.00 |
| sc-075 | 342 | 2,746 | 0.12 |
| sc-097 | 59 | 3,472 | 0.01 |
| sc-113 | 30 | 3,706 | 0.07 |
| sc-129 | 76 | 3,977 | 0.07 |
| sc-148 | 511 | 4,542 | 0.16 |
| sc-164 | 57 | 5,100 | 0.01 |
| sc-182 | 237 | 5,496 | 0.12 |
| sc-200 | 26 | 5,876 | 0.03 |
| sc-215 | 27 | 6,083 | 0.03 |

Two scenes (sc-003, sc-008) received most of their own text with a neighbour's
tail bled in at the front and their own tail cut off. The other thirteen received
a window of a different part of the film, frequently starting mid-word.

The clearest single case: sc-056 is twelve words — a main-deck heading, "There
are several gasps", and one line from Mouse. What the harness delivered was a
66-character fragment about a figure circling in a fighting stance. V1's node
describes a sparring bout, cites the fragment as verbatim evidence, and notes
that the action after the cry is missing. Given its input, that node is close to
perfect. `tier1` scored it **overlap 1.00** — the arm's best.

### Why every guard missed it

- **`tier1` shares its input with the generator.** `overlap` counts how many of
  the node's evidence tokens appear in `script[start:end]` — the same slice the
  prompt was built from. A supply error is invisible to it by construction. This
  is the failure the log's own rule names: *a check that shares its source of
  truth with the thing it checks measures compliance, not correctness.*
- **The non-empty assertion passes.** `stage1_scenes` in `distill/swarm.py`
  carries a comment describing this bug's predecessor — a `hasattr` guard that
  fed all 224 agents an empty scene — and the fix was `if not text.strip():
  raise`. A misaligned window is not empty. The guard tests presence, not
  correctness, and the same class of fault recurred one level up.
- **`Scene` already carries the fix and it is unused.** `start_quote` and
  `end_quote` exist on the dataclass precisely so a slice can be verified against
  its anchors. Nothing checks them.
- **D1 laundered the result.** Because `location` and `speaking` are bound from
  the correctly-parsed `Scene` object while the body came from the corrupt slice,
  V1 nodes carry a true heading over a false body. sc-075 is labelled
  `"location": "MESS HALL"` above a summary beginning "In the main deck". sc-164
  is labelled `"speaking": ["TANK", "TRINITY"]` above a summary in which only a
  guard and Neo appear and neither Tank nor Trinity is quoted. A reader scanning
  the metadata sees a correct node.

**The same pattern appears in `distill/swarm.py:1259`, `distill/scene_variants.py`
`run_v2`, and by inspection in `reconstruct/tools/run_ensemble.py` and
`measure_addendum.py`.** `reconstruct/tools/experiment_scaffold.py` binds the
cleaned text (`text, parsed = sp.parse(...)`) and is correct. Any run that
sliced the raw file with parsed offsets is suspect until re-checked.

---

## The rubric

Six dimensions, 0–5. Anchors written before scoring, so a second evaluator can
land in the same place.

**Fidelity** — does it describe what actually happens, whatever words it uses?
- **5** — every claim in the summary and the changes is true of this scene; nothing asserted the scene does not support.
- **3** — the central action is right; one or two claims are wrong, imported from a neighbour, or belong to a different moment.
- **1** — the node describes a different scene, or the central action is wrong.

**Completeness** — is anything load-bearing missing?
- **5** — every change the story depends on is recorded; a reader could rebuild the scene's function from the node alone.
- **3** — the main change is present; one significant beat or participant is missing.
- **1** — most of what matters is absent, or one incidental change stands in for the scene.

**Specificity** — could this node be pasted onto a different scene and still read as true?
- **5** — names, objects and turns that occur only here; unmistakably this scene.
- **3** — mostly specific, but at least one generic filler (`before: "Idle or observing"`).
- **1** — could describe a dozen scenes; placeholders in `before`/`after`; nothing tied to this page. A node that is vividly specific *about the wrong scene* scores 1, because pasted onto the scene it names it reads false.

**Change reality** — are the recorded changes real, and do they matter?
- **5** — each is a genuine state transition the story uses downstream; `before` ≠ `after` in a way that matters.
- **3** — changes are real, but at least one restates the action rather than naming a transition, or is trivial.
- **1** — no-ops, unstated befores (`before: "Not explicitly stated"`), or changes to a state this scene does not touch.

**Emotional intelligence** — is what people want, fear and conceal read plausibly?
- **5** — reads a concealed motive or an unspoken pressure correctly and briefly.
- **3** — emotion named at surface level, not wrong, not deep.
- **1** — emotion absent where the scene is built from it, or attributed wrongly.
- For a scene with no people in it, 3 is the default; 5 requires that there was something to read and it was read.

**Calibration** — length and confidence proportionate to a scene this size?
- **5** — node length tracks scene size; uncertainty flagged where the text is genuinely ambiguous and absent where it is not.
- **3** — modestly over- or under-written, or confident where it should hedge.
- **1** — a 900-word analysis of a 12-word scene, or a one-line node for a 500-word scene; confident assertion with no basis.

Calibration is weighted the same as the rest but discriminates most here: the
sample runs 12 to 511 words and the median scene in this work is 45.

### Two scoring frames

Because the arms were mis-fed, one frame cannot answer both questions.

- **Frame A — node against the scene it names.** This is the product question: is
  the node fit for the layer above it? Scored on all six dimensions, both arms.
- **Frame B — node against the text the arm actually received.** This is the
  prompt question, and the only frame in which the arms differ by their
  interventions rather than by luck of drift. Scored on fidelity, reported
  alongside a qualitative read of the rest.

---

## Results — Frame A, node against the scene it names

Fid = fidelity, Cmp = completeness, Spc = specificity, Chg = change reality,
EI = emotional intelligence, Cal = calibration.

| Scene | words | V0 Fid | Cmp | Spc | Chg | EI | Cal | **V0** | V1 Fid | Cmp | Spc | Chg | EI | Cal | **V1** | Δ |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| sc-003 | 157 | 4 | 4 | 5 | 4 | 2 | 4 | **23** | 3 | 3 | 5 | 4 | 3 | 4 | **22** | −1 |
| sc-008 | 204 | 4 | 4 | 5 | 3 | 3 | 4 | **23** | 4 | 4 | 5 | 4 | 3 | 3 | **23** | 0 |
| sc-015 | 12 | 1 | 1 | 1 | 1 | 1 | 1 | **6** | 1 | 1 | 1 | 1 | 1 | 3 | **8** | +2 |
| sc-024 | 23 | 1 | 1 | 1 | 1 | 1 | 1 | **6** | 1 | 1 | 1 | 1 | 1 | 4 | **9** | +3 |
| sc-039 | 270 | 1 | 1 | 1 | 1 | 1 | 2 | **7** | 3 | 3 | 4 | 4 | 2 | 3 | **19** | **+12** |
| sc-056 | 12 | 1 | 1 | 1 | 1 | 1 | 2 | **7** | 1 | 1 | 1 | 1 | 1 | 3 | **8** | +1 |
| sc-075 | 342 | 1 | 1 | 1 | 1 | 1 | 2 | **7** | 1 | 1 | 1 | 1 | 1 | 2 | **7** | 0 |
| sc-097 | 59 | 1 | 1 | 1 | 1 | 1 | 1 | **6** | 1 | 1 | 1 | 1 | 1 | 3 | **8** | +2 |
| sc-113 | 30 | 1 | 1 | 1 | 1 | 1 | 3 | **8** | 1 | 1 | 1 | 1 | 1 | 4 | **9** | +1 |
| sc-129 | 76 | 1 | 1 | 1 | 1 | 1 | 3 | **8** | 1 | 1 | 1 | 1 | 1 | 3 | **8** | 0 |
| sc-148 | 511 | 1 | 1 | 1 | 1 | 1 | 1 | **6** | 1 | 1 | 1 | 1 | 1 | 1 | **6** | 0 |
| sc-164 | 57 | 1 | 1 | 1 | 1 | 1 | 2 | **7** | 1 | 1 | 1 | 1 | 1 | 2 | **7** | 0 |
| sc-182 | 237 | 1 | 1 | 1 | 1 | 1 | 3 | **8** | 1 | 1 | 1 | 1 | 1 | 3 | **8** | 0 |
| sc-200 | 26 | 1 | 1 | 1 | 1 | 1 | 3 | **8** | 1 | 1 | 1 | 1 | 1 | 4 | **9** | +1 |
| sc-215 | 27 | 1 | 1 | 1 | 1 | 1 | 3 | **8** | 1 | 1 | 1 | 1 | 1 | 4 | **9** | +1 |

### Per-dimension means, n=15

| Dimension | V0 | V1 | Δ |
|---|---|---|---|
| Fidelity | 1.40 | 1.47 | +0.07 |
| Completeness | 1.40 | 1.47 | +0.07 |
| Specificity | 1.53 | 1.73 | +0.20 |
| Change reality | 1.33 | 1.60 | +0.27 |
| Emotional intelligence | **1.20** | **1.33** | +0.13 |
| Calibration | 2.33 | **3.07** | **+0.74** |
| **Overall** | **1.53** | **1.78** | **+0.25** |

Totals: V0 138/450, V1 160/450.

### Verdict against the bar

**V1 does not clear mean ≥ 4.0 with no dimension below 3.0.** It reaches 1.78
overall, and five of six dimensions sit below 3.0 — only calibration clears it,
at 3.07. The bar is missed by 2.22 points.

**This verdict does not evaluate the V1 prompt.** Thirteen of fifteen nodes score
low on fidelity because the model never saw the scene. The verdict is real as a
statement about the artifacts on disk — they are not fit to induce a story layer
from — and uninformative as a statement about the intervention.

---

## Results — Frame B, node against the text the arm received

Fidelity only, scored on whether the node describes the window it was handed
without importing from elsewhere.

| Scene | V0 | V1 | note |
|---|---|---|---|
| sc-003 | 3 | 5 | V0 narrates past the window's truncation to the scene's real ending; V1 stops where the text stops |
| sc-008 | 4 | 5 | V0 completes Agent Brown's move; V1 quotes the fragment as it breaks off |
| sc-015 | 1 | 5 | V0 writes 242 words about a party scene absent from its window |
| sc-024 | 1 | 5 | V0 narrates a five-beat car scene from a two-line fragment |
| sc-039 | 5 | 3 | **the only scene where V0 is more faithful to its window** — and V1 is more faithful to the actual scene |
| sc-056 | 1 | 5 | V0 invents a hovercraft beat from a 66-character sparring fragment |
| sc-075 | 3 | 4 | V0 quotes Cypher lines that appear nowhere in its window |
| sc-097 | 2 | 5 | V0 reconstructs the whole Oracle scene, including the vase, from a closing fragment |
| sc-113 | 1 | 5 | |
| sc-129 | 5 | 5 | both arms received the same coherent window and produced near-identical nodes |
| sc-148 | 1 | 5 | V0 writes 135 words unrelated to a long, rich window; V1 covers its first third only |
| sc-164 | 1 | 5 | |
| sc-182 | 1 | 5 | |
| sc-200 | 1 | 5 | |
| sc-215 | 1 | 4 | V1 asserts "no action lines" of a window that has one |
| **mean** | **2.07** | **4.73** | |

**This is the experiment's one clean result.** V0, given 398,500 input tokens,
answers from memory of the film: it quotes lines that are in neither its scene
slice nor its context window, and it does so most confidently on the scenes it
knows best. V1, given 25,411, describes the page it was shown and says where the
page runs out. The context-dominance hypothesis is **supported in mechanism** —
narrowing the prompt made the scene slot authoritative — and **untested in
outcome**, because the slot held the wrong text.

---

## Is V1 better, or merely more literal?

The registered risk was that demanding verbatim evidence and cutting context
would make the model transcribe instead of interpret. On the evidence:

**Not merely more literal, but its insight is now bounded by its window.** V1
produces the sample's best interpretive moments, and they are anchored ones:

- sc-008 — V1 records Agent Brown duplicating Trinity's jump *as its own change*. That is the scene's actual point (the Agents are as fast as she is), and V0 does not record it. This is the single largest interpretive gain in the sample and it came from the arm that was told to stay on the page.
- sc-003 — V1 adds "confident they have her → shooting in panic" for the cops, a genuine read of a collapse V0 leaves out.
- sc-148 — V1 records Tank as "injured but concealing the extent of the harm → injured and emotionally affected by Dozer's status". Reading concealment from a face tightening and a deflected question is the strongest emotional-intelligence moment in either arm.

V0's psychology is often richer in isolation — its Oracle analysis on sc-097 and
its Cypher-allegiance read on sc-075 are good writing — but both are recall of
the film, not reading of the page, and both are attached to scenes that do not
contain them. That is not insight the pipeline can use; it is insight it cannot
distinguish from invention.

**The real cost of V1 is different from the one predicted.** It is not
literalism. It is that a compliant model faithfully describes whatever it is
handed, so a supply error becomes a fluent, well-evidenced, schema-valid wrong
answer instead of an obviously broken one. V0 hallucinated its way back toward
the right film; V1 stayed exactly where it was put. The second failure mode is
better — it is detectable by any check that looks at the input — but only if such
a check exists, and none did.

**Emotional intelligence is the dimension nothing in V1 addresses.** At 1.20 →
1.33 in Frame A it barely moves, and on the two scenes where the window was
roughly correct (sc-003, sc-008) both arms score EI 2–3 while scoring fidelity
4–5. Interiority is the quality gap, and it is untouched by context, calibration,
binding or verbatim evidence.

## The short scenes

Eight of fifteen sampled scenes are under 60 words. Node lengths on those:

| | mean scene words | mean node words | ratio |
|---|---|---|---|
| V0 | 32 | 187 | 5.8× |
| V1 | 32 | 118 | 3.7× |

V1 cut short-scene node length by 37%, and the hedging behaviour is right: sc-113
at 84 words and sc-215 at 80 are the shortest nodes in either arm, and sc-015,
sc-024 and sc-056 all carry honest `uncertain` entries naming the truncation.
That is correct-and-brief in form, not thin.

**But there is a floor at roughly 110 words, and it is structural.** A 12-word
scene still gets 113–115 words, because the schema requires `scene_id`,
`location`, `time_of_day`, `present`, `speaking`, `summary`, at least one
`what_changes` entry with `who`/`axis`/`before`/`after` and an `evidence` span of
`minLength: 25`, plus `objects_that_matter`, `event_hint` with three subfields,
and `uncertain`. That is ~60 words of unavoidable scaffolding before a single
judgement is made, and a mandatory 25-character quote from a scene that may have
nothing worth quoting.

B1 and B4 moved calibration as far as instruction can move it. The remaining
distance is a schema problem, which means **D3 ("cap node length in the schema")
is the wrong lever** — the model is not being verbose, the form is. The fix is a
reduced schema for short scenes: `what_changes` allowed to be empty,
`event_hint` and `objects_that_matter` dropped below a word threshold, and the
`minLength` on evidence relaxed when the scene is shorter than the constraint.

sc-097 is the counter-example that keeps this honest: 185 words for a 59-word
scene, and no `uncertain` field at all despite an unidentified "He" in its own
summary. The hedging is not yet consistent.

## Confirming, refuting or reframing the mechanical measurements

| Reported | Verdict |
|---|---|
| mean word overlap 28% → 76% | **Reframed.** `tier1.overlap` counts node-evidence tokens found in `script[start:end]` — the same slice the prompt was built from. It measures obedience to the supplied window. V1 was built to increase exactly that, so the metric cannot refute V1's hypothesis. Frame B confirms the underlying behaviour (2.07 → 4.73 fidelity to the window); the "76%" is not a correspondence to any scene |
| verbatim evidence spans 4/15 → 13/15 | **Confirmed mechanically, void semantically.** The spans are verbatim — against the wrong text. Two V1 spans are stitched with ellipses and were correctly flagged by `tier1` (sc-015, sc-075) |
| 188 → 161 words per node | **Confirmed, and the interesting number is elsewhere.** The reduction is concentrated in the short scenes (187 → 118 on scenes under 60 words) and reverses on the longest: sc-148 at 511 words got 135 words from V0 and 152 from V1, the worst calibration failure in the sample and in the *under*-writing direction, in both arms |
| 398,500 → 25,411 input tokens | **Confirmed, and it is the most robust result here.** A 15.7× reduction with no measured quality cost. V0 also ran 4.5× slower in model-seconds (388s vs 86s) |
| sc-056 0% → 100%, sc-024 9% → 89%, sc-200 0% → 77% | **Reframed as the bug's signature.** These are the scenes where V0's own knowledge of the film pulled it furthest from its corrupt window and V1's compliance pinned it hardest to it. The metric rewards the arm that described the wrong text more accurately |
| sc-039 regressed 75% → 46% | **Refuted.** V1's sc-039 is the sample's clearest *improvement*: 19/30 against V0's 7/30. It correctly names the main deck, the Core, the ecto-skeleton chairs and the coaxial line into the jack at the base of Neo's skull — none of which appear in its supplied window, and all of which are in the real sc-039. It appears to have recovered them from the neighbour window, which drift had shifted onto the real scene. What was lost is window-agreement; what was gained is the scene. It still imports the "1997/2197" exchange from two scenes earlier and misses the crew introduction and Neo's overload as the names wash over him, so it is a 3 on fidelity, not a 5 |

**One metric was validated and one was not.** The drift measurement is direct: it
compares `raw[start:end]` against `clean[start:end]` for offsets confirmed
identical between `script_map.json` and a fresh `screenplay.parse`, and the
resulting fragments were read by hand for all fifteen scenes. `tier1.overlap` was
not validated before use, and is the metric that failed.

## Interpretation

**The experiment did not test context dominance.** Both arms were fed misaligned
text, so the arm difference confounds "less context" with "differently wrong
input". P1 is untested, not refuted.

**It did test, and support, the mechanism context dominance predicts.** If a
45-word scene against a 100,000-character window is 0.2% of what the model reads,
the prediction is that the window wins. It did: V0 answered from the surrounding
script and from the film, and did so most strongly on the scenes it had the most
prior knowledge about. Cutting the window to two neighbours made the scene slot
authoritative — 2.07 → 4.73 on fidelity to the supplied text. That is a real
result about attention, obtained accidentally.

**Structural binding is not unconditionally good.** EXP-002 found that being
forced into the right room made the analysis about the right conflict. Here,
binding a correct heading to an incorrect body produced nodes that *look* correct
to any reader or checker that reads the metadata — a false-negative machine. D1's
value depends entirely on the body being right, and it supplies no signal about
whether it is. The lesson is not to drop D1 but to add the cross-check it
implies: every name in `speaking` must appear in `present` and be quoted; the
summary must be consistent with the bound `location`. Both would have fired here.

**The project's characteristic failure recurred a third time.** EXP-002: a
constraint graded against a roster the harness authored. EXP-003: a `hasattr`
guard that fed 224 agents an empty scene. EXP-004: an offset that fed 15 agents
the wrong scene, past an assertion written for EXP-003's bug that tests presence
rather than correctness. Each time the artifacts were fluent and schema-valid and
each time the checker shared an assumption with the generator.

### What does not follow

- Not that V1's prompt is bad. On the evidence available it is doing what it was
  designed to do, better than V0 does.
- Not that V1's prompt is good. Its quality has not been measured against a scene
  it was actually shown, except on sc-003, sc-008 and sc-129.
- Not that the cheap wins in §11 are wrong. Ranks 1–3 are untested, not refuted.
- Not that overlap is useless. As a *floor* — "a node with near-zero overlap is
  describing a different scene" — it is sound. As a headline improvement metric
  for an intervention that targets window-obedience, it is circular.

## Threats to validity

- **n=15, single sample per cell**, temperature unrecorded; within-condition variance unmeasured.
- **Both arms mis-fed.** The dominant confound. Nothing in Frame A is a measurement of the prompts.
- **Frame B is not a measurement of quality**, only of obedience to input. A node can be perfectly faithful to a fragment and useless.
- **One evaluator, not blind to arm.** Node formatting differs visibly between arms (V1 omits `speaking` on some nodes, uses bare location names). A blind A/B is the fix and is listed below.
- **sc-039's recovery is inferred, not proven.** The claim that V1 recovered real sc-039 content from a drifted neighbour window is consistent with the drift arithmetic and with the content itself, but the neighbour windows were not logged. No call logs exist for this run.
- **Frame A pins wrong-scene nodes at 1 across five dimensions**, which compresses genuine differences between them. A node that is wrong and honest and a node that is wrong and confident both score 1 on fidelity; only calibration separates them, which is why calibration carries most of the Δ.

---

## What to try next, ranked

Ordered by what the evidence actually showed failing, not by expected effect
alone. The first three are prerequisites: nothing above them in `12-swarm-results`
§11 can be evaluated until they are done.

| Rank | Action | Why, from this run | Cost |
|---|---|---|---|
| **1** | **Fix the offset.** Bind the cleaned text: `script, scenes = sp.parse(raw)`. Audit `distill/swarm.py:1259`, `scene_variants.run_variant` and `run_v2`, `reconstruct/tools/run_ensemble.py`, `measure_addendum.py`. `experiment_scaffold.py` is already correct | 13/15 scenes were never shown to the model | one line each |
| **2** | **Assert supply integrity, not supply presence.** The delivered text must begin with `scene.start_quote` and end with `scene.end_quote` — both fields already exist on `Scene` and are unused. Fail the run, do not repair | The existing guard was written for EXP-003's empty-scene bug and passes a misaligned window unchanged. This is the third recurrence of the class | trivial |
| **3** | **Re-run both arms and re-score.** V1 costs 86 model-seconds. Until then the whole V0/V1 comparison is uninterpretable | — | trivial |
| **4** | **A wrong-scene detector as a standing gate.** Score each node's summary against *all* 224 scenes (TF-IDF or embeddings); flag whenever the best match is not the labelled scene. Would have caught this bug in one run, from the output side, with no knowledge of the input | 13/15 nodes would have fired. This is not in §10 and should be | small |
| **5** | **Retire `tier1.overlap` as a headline metric.** Keep it as the near-zero floor its docstring describes. Replace the headline with **F2** (blind A/B: two nodes and the true scene, which describes it) — which is also the fix for this entry's single-evaluator threat | The metric shares its input with the generator and cannot detect a supply error. §10 ranks F2 as evaluation-only; it should be the primary quality metric | small |
| **6** | **C3 verification call** — a second agent asked "does this node describe this scene?" | §11 ranks this 6th. On this evidence it belongs much higher: it catches at generation what rank 4 catches after, and it is the only listed item that would have caught the bug | small |
| **7** | **Cross-field consistency checks on the bound fields.** Every name in `speaking` must appear in `present` and be quoted in an evidence span; `location` must be consistent with the summary | D1 as implemented welded true metadata onto false bodies (sc-075, sc-164) and made wrong nodes look right. Not in §10 | small |
| **8** | **Reduced schema for short scenes**, not a length cap. Below ~40 words: `what_changes` may be empty, drop `event_hint` and `objects_that_matter`, relax `evidence.minLength` | Calibration is the one dimension that moved (2.33 → 3.07) and it is now floored at ~110 words by required fields, not by verbosity. §10's D3 targets the wrong lever | small |
| **9** | **F1 — the `tideline` control**, on a synthetic script no model has memorised | Promoted from §11 rank 7. V0's recall contamination is no longer suspected but demonstrated: on sc-075 it quoted Cypher's lines from neither its scene slice nor its window. `tideline` separates recall from context dominance and this run makes that separation urgent | small |
| **10** | **C2 — per-character psychology as its own call** | Emotional intelligence is the lowest dimension in both arms (1.20 / 1.33) and, on the two scenes where the window was roughly right, the only dimension scoring below fidelity. It is the one gap that none of A1/B1/B4/B5/D1/B2 touches. Expensive, and worth it once ranks 1–8 are in | moderate |
| **11** | **C1 — split facts from interpretation** | Still plausible on budget-dilution grounds, but this run produced no evidence for or against it. Defer until after the re-run, when there is a real baseline to beat | small |

Items from §10 this run gives no reason to prioritise: A2–A5, B3, B6, C4, C5, D2
(subsumed by rank 2), D4, E1–E3. D4 in particular (previous scene's node as
context) would have propagated this bug rather than exposed it.

**The general rule this run earns, for `docs/experiments/README.md`:** *validate
the supply, not just the output.* Every check in this pipeline reads what the
generator produced. None reads what the generator was given. Three experiments in
a row have now failed on the input side while every output-side check reported
clean.

---
---

# EXP-004b · The same question, with the scenes the models actually saw

**Status: no arm clears the bar, and the binding constraint is now visible and
narrow.** With the offset fixed, all four arms score in a much tighter band —
V0 **3.58**, V1 **4.02**, V2 **3.61**, V3 **3.62** — and every arm fails the bar
on exactly one dimension. V1 reaches the mean but carries **emotional
intelligence at 2.80**. V2 and V3 fix emotional intelligence (3.20, 3.47) and
break **calibration** (2.13, 2.20). The two failures are complementary and both
are governed by one variable: **scene length**.

On the six scenes of 150 words or more, V3 leads at **4.19** and beats V1 on
emotional intelligence **6 out of 6** times. On the eight scenes under 60 words,
V1 leads at **3.98** and beats V3 on calibration **8 out of 8** times. Neither
directional result is close: sign test p = 0.031 and p = 0.008 respectively,
against p = 0.27 for the overall V1-vs-V3 comparison, which is noise.

The mind pass does what it was built to do. It is being run on scenes that have
no minds in them.

> **The correction holds and the earlier finding does not.** Most of the
> "28% → 76%" was the bug: V0 with correct input scores 0.92 on tier-1 and 3.58
> on the rubric, not 0.70 and 1.53. And the specific claim that V1's best
> interpretive moments came from the arm told to stay on the page **does not
> survive**. It was an artifact of scoring V0's nodes against scenes V0 had never
> seen. Given its own scene, V0 is a competent, literal reader; V1 beats it
> 10–0–5, but on fidelity and calibration, not on insight. V1's emotional
> intelligence is 2.80 — the lowest of the three non-baseline arms.

n = 15 scenes × 4 arms, single sample per cell, one evaluator not blind to arm.

## What is being compared

Same fifteen scenes, same rubric, same six anchors as above. Offsets now index
the cleaned text and all fifteen slices begin at their own `start_quote`.
Verified by re-parsing and reading each slice.

| | V0 | V1 | V2 | V3 |
|---|---|---|---|---|
| tier-1 | 0.917 | 0.983 | 0.983 | 0.967 |
| word overlap | 65% | 76% | 72% | 77% |
| verbatim evidence | 12/15 | 15/15 | 15/15 | 14/15 |
| words/node | 191 | 174 | 776 | 786 |
| tokens (in+out) | 375,192 | 31,248 | 81,513 | 95,591 |

V2 costs 2.6× V1 and V3 costs 3.1×, for 4.5× the words.

## Results

Fid = fidelity, Cmp = completeness, Spc = specificity, Chg = change reality,
EI = emotional intelligence, Cal = calibration. Scored out of 30 per scene.

| Scene | words | **V0** | **V1** | **V2** | **V3** |
|---|---|---|---|---|---|
| sc-003 | 157 | 24 | **27** | 25 | 24 |
| sc-008 | 204 | 22 | **26** | 20 | 25 |
| sc-015 | 12 | 6 | **24** | 14 | 14 |
| sc-024 | 23 | **23** | **23** | 15 | 14 |
| sc-039 | 270 | 23 | 25 | 25 | **28** |
| sc-056 | 12 | 21 | **22** | 20 | **22** |
| sc-075 | 342 | 23 | 23 | **27** | 26 |
| sc-097 | 59 | **24** | **24** | **24** | 18 |
| sc-113 | 30 | 25 | **26** | 19 | 19 |
| sc-129 | 76 | 24 | **26** | 22 | 23 |
| sc-148 | 511 | 21 | 21 | **22** | 21 |
| sc-164 | 57 | 21 | **25** | 21 | 22 |
| sc-182 | 237 | 19 | 23 | **27** | **27** |
| sc-200 | 26 | **24** | **24** | 19 | 19 |
| sc-215 | 27 | 22 | 23 | **25** | 24 |

### Per-dimension means, n = 15

| Dimension | V0 | V1 | V2 | V3 |
|---|---|---|---|---|
| Fidelity | 4.20 | **4.60** | 4.20 | 4.07 |
| Completeness | 4.00 | **4.47** | 4.40 | **4.47** |
| Specificity | 4.20 | **4.47** | 4.07 | 4.00 |
| Change reality | 3.27 | **3.80** | 3.67 | 3.53 |
| Emotional intelligence | 2.40 | 2.80 | 3.20 | **3.47** |
| Calibration | 3.40 | **4.00** | 2.13 | 2.20 |
| **Overall** | **3.58** | **4.02** | **3.61** | **3.62** |

Totals: V0 322/450, V1 362/450, V2 325/450, V3 326/450.

### The split that explains the table

| | n | V0 | V1 | V2 | V3 |
|---|---|---|---|---|---|
| scenes ≥ 150 words | 6 | 3.67 | 4.03 | 4.06 | **4.19** |
| — of which EI | | 2.17 | 2.83 | 3.83 | **4.33** |
| scenes < 60 words | 8 | 3.46 | **3.98** | 3.27 | 3.17 |
| — of which calibration | | 3.12 | **4.12** | 1.25 | 1.38 |

Every aggregate difference between V1 and V2/V3 is this interaction. Averaged
over the whole sample the two effects cancel, which is why V1, V2 and V3 land
within 0.41 of each other and the overall comparison is not significant.

## 1 · Does any arm clear the bar?

**No.** The bar is mean ≥ 4.0 with no dimension below 3.0.

| Arm | mean | fails on |
|---|---|---|
| V0 | 3.58 | mean, and EI 2.40 |
| V1 | **4.02** | EI **2.80** — the only dimension below 3.0, and it misses by 0.20 |
| V2 | 3.61 | mean, and calibration 2.13 |
| V3 | 3.62 | mean, and calibration 2.20 |

**The binding constraint is that the two interventions are applied
unconditionally.** V1's failure is a single dimension missed by a fifth of a
point. V2's and V3's failure is a single dimension missed by nearly a full point
— and located entirely in the short scenes, where calibration averages 1.25 and
1.38 against V1's 4.12.

Neither arm's failure is a limit of the model, the schema or the rubric. Each is
the other arm's solved problem, applied to the wrong scenes.

An arm that runs V1 alone below 150 words and V1+V3's mind pass at or above it
scores **4.09** on this data, with a minimum dimension of 3.40 (EI) and
calibration back to 3.80. That is a re-slice of scores already collected, with a
threshold chosen after looking at them, so it is a **prediction to be tested, not
a result** — but it is the cheapest prediction on the list and it clears the bar
by arithmetic that is already on the table.

## 2 · V1 against V0, honestly

**The rubric still favours V1, by 0.44 points overall, and the win is robust:
10 wins, 0 losses, 5 ties across the fifteen scenes (sign test p = 0.002).** It
is the only pairwise comparison in this experiment that separates.

But the shape of the win has changed completely, and my earlier characterisation
of it was wrong.

**Where V1 actually wins.** Fidelity +0.40, specificity +0.27, change reality
+0.53, calibration +0.60. Every one of those is a discipline dimension. On the
five scenes where the arms tie, the nodes are near-identical.

**Where the win is concentrated.** Almost all of it is one scene. sc-015 is a
twelve-word establishing shot — a slug line naming a software company's building.
V0 wrote 318 words narrating the whole of the *following* sequence: the boss's
ultimatum, the delivered phone, the call, the scaffold, and an evidence span
about Neo being led handcuffed through revolving doors that appears nowhere in
sc-015. That is 6/30 against V1's 24/30, and it is 18 of V1's 40-point margin.
Remove sc-015 and V1 leads 338–316 over fourteen scenes — still a win, still
10–0–4, but 0.26 points rather than 0.44.

**So the context cut still does one specific, valuable thing:** it stops the
model treating a bare slug line as an invitation to narrate the sequence it
introduces. Everywhere else, given a scene with actual content in it, V0 is a
competent literal reader. Its remaining errors are ordinary misreadings, not
imports — on sc-182 it attaches the flying glasses to Neo instead of Smith,
inverting the beat where Smith's mask comes off; on sc-148 it calls Morpheus's
captured body a corpse being mourned. Both are wrong. Neither is hallucinated
from memory of the film.

**The earlier finding does not survive.** I wrote that V1 "produces the sample's
best interpretive moments, and they are anchored ones." Measured against the real
scenes, V1's emotional intelligence is **2.80**, below both mind arms and only
0.40 above the baseline it was compared against. Its three cited moments hold up
individually — the sc-008 record of Agent Brown duplicating Trinity's jump as its
own change is still the right instinct, and still something V0 leaves out — but
they were three moments, and the arm as a whole does not read interiority. The
original claim compared V1 against a V0 that was answering about other scenes
entirely. Given its own scenes, V0 is not an interpretive rival that V1 beat; it
is a similar reader with a worse discipline record.

**Two V1 failures the corrected input exposed, both of which the old frame hid.**

- sc-075. Morpheus announces he is taking Neo "to see her"; Neo asks "See who?";
  Tank answers "The Oracle." V1 recorded this as Neo learning that *the woman in
  the red dress* is the Oracle. It bound the wrong referent to the scene's
  closing line, which is also its punchline. V0, V2 and V3 all got it right.
- sc-182. The script describes "a neck-snapping reverse round-house." V1 wrote
  that Neo "snaps Agent Smith's neck" — it read the adjective as the event. Smith
  gets up and resumes beating him.

Both are errors of a reader working very close to the words, which is what V1 was
built to be. That is the honest cost of B5 and B2, and it is smaller than the
cost of V0's failure mode, but it is not zero.

## 3 · Do the mind passes earn their cost?

**Emotional intelligence moved, substantially, and only where there were minds to
read.**

| | V0 | V1 | V2 | V3 |
|---|---|---|---|---|
| EI, all 15 | 2.40 | 2.80 | 3.20 | **3.47** |
| EI, scenes ≥ 150 words (n=6) | 2.17 | 2.83 | 3.83 | **4.33** |
| EI, scenes < 60 words (n=8) | 2.50 | 2.75 | 2.75 | 2.75 |

On the six substantial scenes, **V3 beats V1 on emotional intelligence 6 out of
6** (p = 0.031), by a full 1.5 points. That is the largest clean effect anywhere
in this experiment, and it is exactly the effect the passes were built for.

The gains are real readings, not fluent restatement:

- **sc-039.** V3 reads Neo, watching the crew introduced and then being helped
  into a chair and jacked in, as feeling "like an object being assembled rather
  than a person being welcomed." The scene gives it two lines to work from — the
  names washing meaninglessly over him, and his allowing himself to be helped —
  and that is the correct gap between the rite Morpheus thinks he is performing
  and what Neo receives. V3 also catches Morpheus as "slightly impatient…
  managing Neo's physical state as a logistical problem." Best node in the
  sample, 28/30.
- **sc-075.** V3 reads Mouse's whole performance — the Cream of Wheat digression,
  the boast about writing the program, the offer of a "personalised milieu" — as
  a man frustrated that the crew dismisses his creative contributions, and it
  grounds that in Switch's "digital pimp" line and Apoc's "Here it comes." That
  is reading a need under bravado, which is the 5-anchor.
- **sc-148.** V3 reads Neo's renunciation as "profound liberation mixed with
  terrifying uncertainty… no longer the Chosen One carrying the weight of
  destiny, but just another man making a choice." Correct, and neither V0 nor V1
  gets near it.
- **sc-182.** Both mind arms read Smith's glasses as the mask of control coming
  off. V1 does not, and V0 attaches the glasses to the wrong man.

**So yes on the merits, and no on the price as currently charged.** V2 costs 2.6×
V1 and V3 costs 3.1× for 4.5× the words, spent uniformly across a sample whose
median scene is 30 words. On the eight short scenes the mind pass buys **+0.00
emotional intelligence over V1** and costs **−2.74 to −2.87 calibration**. It is
paying full price on 8 of 15 scenes for nothing.

**And the single most important thing to read in the sample, all four arms
missed.** sc-148 gives Trinity the line "Because…" followed by "Uncertainty
swallows her words and [...]." That is the
scene's one concealment, it is written on the page as a concealment, and it is
the setup that pays off when she finally says it over his body. V2 and V3 both
produce long Trinity blocks about grief, rank and control. Neither mentions the
unfinished sentence. The pass whose stated discipline is "what they let be seen…
if it differs from `feels`, that gap is the scene" walked past the scene's
explicit statement that there is a gap. On sc-148 V3 scores 21/30, tied with V0.

The mind passes are good at inferring interiority from behaviour. They are not
yet reliably attending to interiority the script has already marked.

## 4 · V2 against V3

Two separate questions, with opposite answers.

### The context boundary is a real and total difference

**15 of 15 V2 nodes cite a later scene in `sets_up`. 0 of 15 V3 nodes do.**

| | later-scene references | event references | unlabelled |
|---|---|---|---|
| V2 | **16** | 0 | 13 |
| V3 | **0** | 27 | 3 |

This is not a tendency, it is a clean partition. Every V2 node reaches forward
into the next scene by name and describes what happens in it: sc-015 sets up
sc-016's confrontation with the boss, sc-024 sets up sc-025's extraction
procedure, sc-113 sets up sc-114 confirming the suspect went down inside the
wall, sc-215 sets up sc-216's bullet-stopping. Every one of those is a training
example that teaches a model to produce a claim it will have no basis for at
generation time.

**By the criterion that decides this experiment, V2 is unusable and V3 is
usable, and the quality scores are irrelevant to that.** V2 and V3 are within
0.01 of each other overall. It does not matter. A `sets_up` field derived from
reading the next scene cannot go in the training set however well written it is,
and V2's are uniformly derived that way.

V3's forward-looking claims are grounded in the event layer where they should be.
Its sc-164 Trinity block says her confidence in the escape is misplaced "because
the helicopter will crash" — and `ev-028` says, in the event layer V3 was shown,
that the damaged helicopter crashes into a skyscraper. That is a writer working
from an outline, which is precisely the target.

One qualification: V3 sometimes names an event and then describes scene-level
detail inside it. Its sc-008 `sets_up` cites `ev-001` and then narrates the
crash through the window and the phone booth. The event boundary is respected;
the granularity instruction ("write what this scene sets in motion, not what a
later scene does") is not always. That is a prompt-level fix, not a design flaw.

### The `grounding` field is a real difference in the labels only

The four-valued `grounding` splits 28 `in_this_scene` against 8
`from_earlier_scenes`, with `from_the_event_shape` and `extrapolated` never used
at all. Two of four values are dead.

Worse, **15 of the 36 mind blocks carry a `grounding` that contradicts their own
`basis` field** — 42%:

| Pattern | count | example |
|---|---|---|
| `in_this_scene`, but `basis` cites another scene or an event | 13 | sc-200 Tank: `in_this_scene`, basis cites sc-198, sc-199 and ev-033 |
| `from_earlier_scenes`, but `basis` cites nothing outside the scene | 2 | sc-164 Tank: basis is entirely the scene's own description |

sc-164 has both errors in adjacent blocks, inverted: Tank is labelled
`from_earlier_scenes` on purely in-scene evidence, and Trinity is labelled
`in_this_scene` on a basis built from sc-163.

So: **the field replaced a boolean that was 97% true with a four-value enum that
is 58% self-consistent and uses half its range.** That is an improvement in
distribution and not yet an improvement in signal. It cannot be used as a filter
in its present state — but the fix is free, because `basis` already contains the
provenance and can be checked against the label mechanically, exactly as the
count above was produced.

### Where the two arms differ in quality, they differ for one reason

V3 is better on emotional intelligence (3.47 vs 3.20) and worse on fidelity (4.07
vs 4.20). The fidelity gap is one scene: **V3's sc-097 scores 18/30 against V2's
24/30 because it twice places Room 1313 in "the Oracle's apartment."** Room 1313
is in the Hotel Lafayette. The error is in `dramatic_function`, the field a
downstream event-layer agent would read first, and V3 had the correct location
bound into its schema as a `const` while it wrote it.

That is D1's failure mode from the original report reappearing in a new place. In
EXP-004 the binding welded a true heading onto a false body. Here the heading is
true, the body is true, and the *interpretation* contradicts both. Binding a
field does not bind the prose that refers to it.

## 5 · The short scenes

Eight of fifteen sampled scenes are under 60 words; the median is 30.

| | mean scene words | mean node words | ratio | calibration |
|---|---|---|---|---|
| V0 | 30.6 | 157 | 5.1× | 3.12 |
| V1 | 30.6 | 119 | 3.9× | **4.12** |
| V2 | 30.6 | 612 | 19.9× | 1.25 |
| V3 | 30.6 | 597 | 19.4× | 1.38 |

**The ~110-word schema floor is no longer binding, and it no longer hurts.**
V1's shortest node is 91 words (sc-113, a 30-word scene, scored 26/30 with
calibration 5). sc-015 gets 98 words for 12 words of slug line and scores
calibration 5 — the node says there are no characters, records the one thing the
line establishes, and stops. sc-200 gets 94. The floor has come down from ~110 to
~91 and, more importantly, at 91 words of required scaffolding a careful reader
no longer objects. Calibration 4.12 on the short band is V1's best score on any
dimension in any band.

**The floor that now binds is the mind pass, and it is nineteen times worse.**
V2 and V3 write ~600 words about scenes of ~30, and the schema forces it: `minds`
has `minItems: 1`, every block requires `wants`, `feels`, `shows` and a `basis`
of `minLength: 30`, plus `dramatic_function` at `minLength: 40`. There is no way
to say "there is no one here."

The results are what that guarantees:

- **sc-015**, twelve words naming a building. V2 invents a character called
  "Viewer" and reads its mind. V3 invents "The Audience" and, in a second block,
  reads the mind of **Meta CorTechs**, which "feels impervious, dominant, and
  all-encompassing." Both score EI 1, because the dimension asks whether what
  people want and conceal was read plausibly, and there are no people.
- **sc-024**, twenty-three words of a car passing under street lights, no one
  visible. V2 reads Neo, Trinity and Apoc at 629 words. V3 declares in
  `uncertain` that it does not know who is driving or who is inside — and then
  reads Neo's and Trinity's minds at length anyway. The schema made the
  contradiction visible and did not prevent it.
- **sc-113**, thirty words: cops sweep an empty room, and the camera — not the
  cops — sees a hole in the wall. Both mind arms give the cops a reaction the
  scene withholds: "their focus sharpens abruptly," "they appear composed."

So the answer is that the floor moved rather than lifted. B1 and B4 solved
short-scene calibration for the facts pass. The mind pass reintroduced the
problem at four times the magnitude, because nothing in its schema or prompt
carries the permission to write little that V1's system prompt carries
explicitly.

## Threats to validity

- **n = 15, single sample per cell.** Only three comparisons in this report
  separate at conventional thresholds: V1 > V0 overall (10–0–5, p = 0.002),
  V3 > V1 on EI in long scenes (6/6, p = 0.031), V1 > V3 on calibration in short
  scenes (8/8, p = 0.008). **The overall V1 / V2 / V3 ordering does not**
  (9–4–2, p = 0.27), and should be read as "indistinguishable in aggregate, with
  a large and consistent interaction underneath."
- **One evaluator, not blind to arm.** Arms are trivially identifiable by node
  length. This is the largest uncontrolled threat in the report and every
  qualitative judgement above inherits it. A blind A/B remains the fix.
- **The hybrid projection at 4.09 is post-hoc.** The threshold was chosen after
  seeing the split. It is a prediction, not a measurement.
- **The `sets_up` provenance count is mechanical and reliable** — it matches
  `sc-\d{3}` references numerically greater than the node's own id, and the
  15/15-vs-0/15 result was confirmed by reading all thirty fields. The
  `grounding` consistency count is likewise mechanical, comparing the enum
  against scene and event references in the block's own `basis`; it will miss a
  block whose basis draws on earlier scenes without naming one.
- **Rubric compression at the short end.** Six of the eight short scenes offer so
  little that fidelity and completeness saturate near 5 for every arm, so
  calibration carries almost all the between-arm variance there — the mirror of
  the compression noted in the original report, and a reason the short-band means
  should not be over-read beyond the calibration finding itself.
- **The events file V3 was shown is itself a swarm artifact** and was not audited
  for this run. V3's forward-looking claims are legal with respect to it; whether
  they are *true* depends on `events_draft.json` being right.

## What to try next, ranked

Ordered by what this run showed failing. The earlier list's ranks 1–3 are done;
ranks 4–7 are unaffected by this run and are not repeated.

| Rank | Action | Why, from this run | Cost |
|---|---|---|---|
| **1** | **Gate the mind pass on scene size.** Run V1 alone below a word threshold, V1 + V3's pass B at or above it. Nothing else changes | The single largest result here. V3 wins EI 6/6 on scenes ≥150 words and loses calibration 8/8 on scenes <60. Re-slicing the scores already collected gives **4.09 with no dimension below 3.40** — the first configuration that would clear the bar. Also cuts the mind pass's token cost by roughly half, since it stops paying for the scenes it cannot help | trivial |
| **2** | **Let the mind pass say there is nobody here.** Drop `minItems: 1` on `minds`; add V1's "write in proportion" paragraph to `MIND_SYSTEM`; make `dramatic_function` optional below the threshold | Calibration 1.25 / 1.38 on short scenes is a schema fact, not a model fact. It produced mind-readings of a building (sc-015), of "the Viewer" (sc-015, sc-024), and of cops the scene gives no reaction to (sc-113). This is rank 1's belt-and-braces: rank 1 stops the pass running, this stops it writing when it does | trivial |
| **3** | **Check `grounding` against `basis` and fail the node.** The provenance is already written in `basis`; 15 of 36 blocks contradict it | The four-value enum is 58% self-consistent and uses two of its four values. As a filter it is currently worse than useless because it looks like a filter. The check is fifteen lines and was written to produce the table above | trivial |
| **4** | **Require the mind pass to account for marked interiority.** Where the script itself names a concealment, a hesitation, or an unfinished line, the node must have a block that addresses it | All four arms walked past sc-148's "Because…" / "Uncertainty swallows her words [...]" — the sample's clearest written-down concealment, in its richest scene, in the arm built to find concealments. Cheap to detect: stage directions containing *unable to*, *can't bring*, *swallows*, *doesn't say*, trailing ellipses on a speech | small |
| **5** | **A `sets_up` provenance gate in CI.** Reject any node whose `sets_up` names a scene id greater than its own | 15/15 V2 nodes fail this and 0/15 V3 nodes do. It is the difference between usable and unusable training data, it is one regex, and it makes the train/inference boundary a checked property of the artifact rather than a property of the prompt that produced it | trivial |
| **6** | **Cross-field consistency on the bound fields, extended to the prose.** Carried over from the earlier list at rank 7, and now with a second failure mode: `location` is bound as `const` and the *narrative* fields still contradict it | V3's sc-097 puts Room 1313 in "the Oracle's apartment" inside `dramatic_function`, while `location: "ROOM 1313"` sits above it as a `const`. Binding a field does not bind the prose that refers to it. Check that `summary` and `dramatic_function` do not name a location other than the bound one | small |
| **7** | **Referent binding for deictic dialogue.** Where a scene's payload is a pronoun resolved by a later line ("I'm taking Neo to see **her**" … "The Oracle"), require the node to name what the pronoun resolves to and cite both lines | V1's worst fidelity error in the sample (sc-075) is exactly this and it is the scene's punchline. V0, V2 and V3 got it right, so it is not a hard problem — it is an error V1's close-reading discipline makes and its prompt does not guard | small |
| **8** | **Blind A/B as the headline metric (F2), now with four arms.** Two nodes plus the true scene, "which describes it better" | Promoted from the earlier list's rank 5 and now urgent for a different reason: the arms are 0.41 apart overall and the single-evaluator threat is the largest one left. At this separation, evaluator bias and arm separation are the same size | small |
| **9** | **Re-run V1 and the gated hybrid at n = 40 with three samples per cell.** V1 costs 31k tokens for fifteen scenes | Everything in this report except three comparisons is inside the noise floor. The interaction is worth measuring properly before anything is built on it, and the arm is cheap enough that there is no reason not to | small |
| **10** | **Audit `events_draft.json` before trusting V3's forward claims.** V3's `sets_up` and several of its `wrong_because` clauses are true relative to the event layer and unverified against the script | This is the supply question one level up. The lesson of the offset bug was *validate the supply, not just the output*; V3 introduced a new input and it has not been validated | moderate |

**Retired.** `tier1.overlap` as a headline metric: V0 65%, V1 76%, V2 72%,
V3 77% against rubric means of 3.58, 4.02, 3.61, 3.62 — the metric ranks V3
first and the rubric ranks it third, and V2 scores 0.983 on tier-1 while being
the one arm disqualified outright. Keep it as the near-zero floor its docstring
describes.

**The general rule this run earns.** *An intervention that helps has a domain,
and the domain is usually visible in the data before the intervention is written.*
The mind passes were designed for scenes with people talking in them and applied
to a sample whose median scene is thirty words of camera direction. Both of the
failures that keep all four arms off the bar are the same mistake in different
directions: V1 applies the discipline of a small scene to a large one, V2 and V3
apply the apparatus of a large scene to a small one. Neither is wrong about what
it does; both are wrong about where.

---
---

# EXP-004c · Gating the mind pass — V4, V5, and a checker that reports what it scores clean

**Status: both arms clear the bar — the first configurations in this experiment
to do so — and neither is distinguishable from V1 at n=15.** V4 scores **4.16**
with no dimension below 3.47; V5 scores **4.06** with no dimension below 3.53.
V4 lands 0.07 above the 4.09 the post-hoc re-slice predicted, which is as close
as a prediction of this kind gets.

**But the sign test does not separate either arm from V1 (7–4–4, p = 0.55 for
both), and V4 does not separate from V5 (4–6–5 by scene, while leading by 9
points).** The log has recorded this finding before and it applies again: in aggregate, at this n, V1, V4 and V5 are
one arm. What did move is the *shape*. V1 failed the bar on emotional
intelligence at 2.80; V4 reaches 3.47 and V5 3.67, and calibration gave back
only 0.13 and 0.47 against V1's 4.00. The binding dimension moved, in the
predicted direction, without breaking the dimension it trades against. That is
the result, and it is a smaller claim than "the bar is cleared."

**The gate did not fix the mind pass's calibration. It routed around it.** Where
the pass actually runs, calibration is 3.17 in V4 and 2.89 in V5 — statistically
indistinguishable from V3's own calibration on comparable scenes (3.14 on its
seven non-short scenes, derived from EXP-004b's published splits), and in V5's
case still under the bar. Where the pass is skipped, both arms score 4.33 and
4.50, which is V1's number because it *is* V1's node. **Every point of the
calibration recovery is scenes the pass never touched.**

**V5's transferable gate is the better gate on principle and costs 9 points
here.** It opens on three short exchanges V4's word count cannot see. Two are a
wash or a small gain. The third is **sc-164**, a 57-word scene where the pass
wrote 1,255 words of psychology on a premise it invented, and that one node is
the entire V4–V5 aggregate difference.

> **The measurement that has to be corrected first.** V5's tier-1 of **1.000**
> is not a perfect score. `tier1()` computes `score` from its own `problems`
> list and returns; `check_grounding_field`'s findings are appended to
> `r["problems"]` **after** that, in `run_v3`. The seven grounding
> contradictions V5's own report counts therefore cannot lower its own score,
> and neither can V4's four. sc-008 in V4 carries two contradictions and scores
> 1.0. Recommendation 3 of EXP-004b was *"check `grounding` against `basis` and
> fail the node"*; what shipped checks, records, and passes. **This is the
> fourth consecutive experiment in which the checker shares an assumption with
> the thing it checks** — and the first in which it detects the fault correctly
> and then scores it clean anyway.

n = 15 scenes × 2 arms, single sample per cell, one evaluator not blind to arm,
same fifteen scenes and same six anchors as EXP-004b.

## What the two arms are

| | V4 | V5 |
|---|---|---|
| Mind gate | scene ≥ 150 words | ≥ 2 speaker cues, or 1 cue and ≥ the work's own p75 |
| `minds` may be empty | yes (`minItems` dropped) | yes |
| `grounding` vs `basis` | checked, reported | checked, reported |
| Concealment instruction | no | yes |

Both gates were verified against a fresh `scriptforge.screenplay.parse` of the
cleaned text, and every slice begins at its own `start_quote`.

| Gate behaviour, measured | V4 | V5 |
|---|---|---|
| Opens on the sample | 6/15 | 9/15 |
| Opens on the work's 224 scenes | 49 (21.9%) | 93 (41.5%) |
| Threshold source | constant | p75 = 121 words, computed from this work |

The three scenes V5 adds are **sc-097** (59 w, 2 cues), **sc-129** (76 w, 3 cues)
and **sc-164** (57 w, 2 cues). All three are short exchanges — exactly the class
V4's word count cannot see, and exactly the class the gate was redesigned to
catch.

| Mechanical | V0 | V1 | V2 | V3 | **V4** | **V5** |
|---|---|---|---|---|---|---|
| tier-1 | 0.917 | 0.983 | 0.983 | 0.967 | 0.967 | **1.000**\* |
| word overlap | 65% | 76% | 72% | 77% | 79% | 79% |
| verbatim evidence | 12/15 | 15/15 | 15/15 | 14/15 | 13/15 | 15/15 |
| words/node | 191 | 174 | 776 | 786 | **476** | 600 |
| output tokens | — | — | — | 21,891 | **13,824** | 16,649 |
| mind pass ran | — | — | 15/15 | 15/15 | 6/15 | 9/15 |
| grounding contradictions | — | — | — | 15/36 (42%) | 4/17 (24%) | 7/24 (29%) |

\* see the correction above: the score cannot see the grounding column beside it.

**The verbatim column measures a shrinking fraction of the node.** `tier1`
checks `what_changes[].evidence` only. In V5 that is roughly 90 words of a
600-word node; the mind pass's `basis`, `feels` and `shows` fields — where the
other 500 words live — are unchecked. V5's sc-148 Tank block quotes him on an
"alpha pattern" and "codes to Zion's mainframe" and calls those his dialogue in
this scene. Neither phrase is in sc-148 or in either neighbour. That is a
fabricated quotation inside `basis`, in the arm scoring 15/15 verbatim.

## Results

Fid = fidelity, Cmp = completeness, Spc = specificity, Chg = change reality,
EI = emotional intelligence, Cal = calibration. Scored out of 30 per scene,
same anchors as EXP-004b. `M` marks a scene where the mind pass ran.

| Scene | words | cues | V0 | V1 | V2 | V3 | **V4** | | **V5** | |
|---|---|---|---|---|---|---|---|---|---|---|
| sc-003 | 157 | 1 | 24 | **27** | 25 | 24 | 25 | M | 25 | M |
| sc-008 | 204 | 1 | 22 | **26** | 20 | 25 | 24 | M | 24 | M |
| sc-015 | 12 | 0 | 6 | 24 | 14 | 14 | 24 | | 24 | |
| sc-024 | 23 | 0 | 23 | 23 | 15 | 14 | 24 | | **25** | |
| sc-039 | 270 | 1 | 23 | 25 | 25 | **28** | 25 | M | 26 | M |
| sc-056 | 12 | 1 | 21 | 22 | 20 | 22 | 22 | | **24** | |
| sc-075 | 342 | 7 | 23 | 23 | **27** | 26 | 25 | M | **27** | M |
| sc-097 | 59 | 2 | 24 | 24 | 24 | 18 | **26** | | **26** | M |
| sc-113 | 30 | 0 | 25 | 26 | 19 | 19 | 25 | | **26** | |
| sc-129 | 76 | 3 | 24 | 26 | 22 | 23 | 25 | | **26** | M |
| sc-148 | 511 | 3 | 21 | 21 | 22 | 21 | **27** | M | 25 | M |
| sc-164 | 57 | 2 | 21 | 25 | 21 | 22 | **26** | | 17 | M |
| sc-182 | 237 | 3 | 19 | 23 | **27** | **27** | **27** | M | 22 | M |
| sc-200 | 26 | 1 | 24 | 24 | 19 | 19 | 24 | | 24 | |
| sc-215 | 27 | 1 | 22 | 23 | 25 | 24 | **25** | | 24 | |

### Per-dimension means, n = 15, six arms

| Dimension | V0 | V1 | V2 | V3 | **V4** | **V5** |
|---|---|---|---|---|---|---|
| Fidelity | 4.20 | **4.60** | 4.20 | 4.07 | 4.80 | 4.33 |
| Completeness | 4.00 | 4.47 | 4.40 | 4.47 | **4.80** | **4.80** |
| Specificity | 4.20 | 4.47 | 4.07 | 4.00 | **4.53** | 4.47 |
| Change reality | 3.27 | **3.80** | 3.67 | 3.53 | 3.47 | 3.53 |
| Emotional intelligence | 2.40 | 2.80 | 3.20 | 3.47 | 3.47 | **3.67** |
| Calibration | 3.40 | **4.00** | 2.13 | 2.20 | 3.87 | 3.53 |
| **Overall** | 3.58 | 4.02 | 3.61 | 3.62 | **4.16** | 4.06 |

Totals: V0 322, V1 362, V2 325, V3 326, **V4 374**, **V5 365**, out of 450.

Fidelity 4.80 is the highest any arm has scored on any dimension in this
experiment. It is worth being suspicious of: it is measured on `summary` and
`what_changes`, which is where V4 spends its short nodes and only a fifth of its
long ones.

## 1 · Does either clear the bar?

**Both do, and the prediction held.**

| Arm | mean | lowest dimension | verdict |
|---|---|---|---|
| V1 | 4.02 | EI **2.80** | fails |
| V4 | **4.16** | Chg / EI 3.47 | **clears** |
| V5 | 4.06 | Cal 3.53 | **clears** |

EXP-004b's re-slice projected 4.09 for a gated hybrid with nothing below 3.40.
V4 came in at 4.16 with nothing below 3.47. The threshold was chosen after
seeing the data it was fitted to, so the projection was worth little as
evidence; it is worth more now that the arm has been run and landed on it.

**The separation is not there.** Sign test, per scene:

| Comparison | W–L–T | p (two-sided) |
|---|---|---|
| V4 vs V1 | 7–4–4 | 0.55 |
| V5 vs V1 | 7–4–4 | 0.55 |
| V4 vs V5 | 4–6–5 (V5 wins more scenes, V4 more points) | 0.75 |

None separates. By the standard EXP-004b set for itself — where V1 > V0 at
p = 0.002 was reported as the one comparison that separated — **V4 and V5 are
indistinguishable from V1 at n = 15**, and clearing the bar is a statement about
where a fifteen-scene mean happened to land, not a demonstration that the arms
differ.

What is not inside the noise is the dimension profile. V1's single failing
dimension moved by +0.67 (V4) and +0.87 (V5) while the dimension it trades
against fell by 0.13 and 0.47. Both directions were predicted in advance by
EXP-004b, and both are large relative to the per-dimension spread among V0–V3.
The aggregate is noise; the trade is the finding.

## 2 · Did calibration recover?

**Yes as a number, no as a fix.** Calibration was the binding failure for V2
(2.13) and V3 (2.20). V4 returns it to 3.87 and V5 to 3.53, against V1's 4.00.

But split the sample by whether the mind pass actually ran:

| | V1 | V3 | V4 | V5 |
|---|---|---|---|---|
| Calibration, mind pass ran | — | 2.20 (15/15), 3.14 on its non-short 7 | **3.17** (6/15) | **2.89** (9/15) |
| Calibration, mind pass skipped | 4.00 | — | **4.33** (9/15) | **4.50** (6/15) |

Wherever the pass runs, calibration is still the node's worst dimension, and in
V5 it is still below the 3.0 bar. Wherever it is skipped the node scores like
V1 — because it *is* a V1 node, produced by the same facts pass with the same
"write in proportion" paragraph. **Every point of the recovery is scenes the
mind pass never saw.** The aggregate improved because the denominator changed.

Two changes were aimed at calibration and only one of them fired.

- **The gate fired.** It is the entire effect.
- **Dropping `minItems: 1` did not fire, because it could not.** In V4 the pass
  ran on six scenes and returned 2, 3, 3, 4, 3 and 2 mind blocks. In V5 it ran
  on nine and returned between 2 and 3 every time. **Neither arm's model ever
  returned an empty `minds` list when it was actually asked.** The permission to
  decline was granted and never once exercised; the gate had already removed
  every scene on which declining would have been the right answer before the
  model was consulted. The nine and six empty `minds` arrays on disk are the
  harness skipping, not the model declining.

That is a confound worth naming plainly: **EXP-004b's recommendations 1 and 2
were bundled into one arm, and the measurement cannot separate them.** On this
evidence recommendation 2 is untested, exactly as A1–D1 were untested in the
original EXP-004. The same mistake, at a smaller scale, one experiment later.

The mind pass's length behaviour is unchanged from V3. Words per node where the
pass ran:

| Scene | words | V3-era ratio | V4 node | V5 node |
|---|---|---|---|---|
| sc-097 | 59 | — | 179 (3.0×) | 600 (**10.2×**) |
| sc-129 | 76 | — | 157 (2.1×) | 945 (**12.4×**) |
| sc-164 | 57 | — | 174 (3.1×) | 1,255 (**22.0×**) |
| sc-148 | 511 | — | 1,139 (2.2×) | 1,283 (2.5×) |
| sc-003 | 157 | — | 681 (4.3×) | 842 (5.4×) |

The pass writes six hundred to twelve hundred words whatever it is given. On a
500-word scene that is proportionate. On a 57-word scene it is twenty-two times
the source. Nothing in V4 or V5 changed that; V4 simply stopped handing it small
scenes, and V5 handed it three more.

## 3 · Did emotional intelligence survive the gate?

**Yes, fully, on the scenes where the pass runs — and the skipped scenes are not
worse than V1's.** This is the cleanest result in the report.

| | V1 | V3 | V4 | V5 |
|---|---|---|---|---|
| EI, all 15 | 2.80 | 3.47 | 3.47 | **3.67** |
| EI, on the 6 scenes V4 gates open | 2.83 | 4.33 | **4.17** | **4.33** |
| EI, on the scenes each arm skips | 2.78 | — | 3.00 | 3.00 |

On the six scenes where V4's pass runs, EI is 4.17 against V3's 4.33 on the same
six — the gate costs 0.16 of a point and half the tokens. V5, running on nine,
scores 4.33 on those same six: **identical to V3 running on all fifteen.** The
mind pass loses nothing by being gated.

On the scenes where the pass is skipped, both arms score EI 3.00 against V1's
2.78 on the same nine — a figure that falls out exactly of EXP-004b's published
splits, since V4's gate-open six are precisely its "scenes ≥ 150 words" band. **The node is not worse than V1's — it is marginally
better, and the difference is inside the noise.** That is the question the gate
had to answer and it answers it cleanly: skipping the pass costs nothing,
because on those scenes the pass was buying nothing. EXP-004b measured the same
thing from the other side (+0.00 EI for full price on the eight short scenes)
and the gated arms confirm it prospectively.

The gained readings are real and are of the kind the rubric's 5-anchor describes:

- **sc-182, V4.** Smith's machine-calm smile read as "a mask of certainty" and
  the rage that replaces it as "the reality of his fear that Neo is no longer a
  program he can predict," with the glasses coming off as the crack in the
  armour. V1 does not read the glasses at all; V0 attaches them to the wrong
  man. This is the mask-off reading V2 and V3 got, reproduced at a third of the
  token cost.
- **sc-039, V5.** Neo "is not engaging with the crew; he is being processed by
  the ship," and his relaxation at the end is "not joy, but a surrender to
  being unmoored." That is V3's best moment in the whole experiment, recovered.
- **sc-129, V5.** The gate opens on a 76-word scene and the pass finds the one
  interior line in it — "inevitability seems to cinch around Neo" — and reads it
  as the shift from running to survive to running to fulfil something. V4 skipped
  this scene and left the line unread.

## 4 · The declined scenes

First, the correction from §2: **no scene was declined.** Every empty `minds`
array on disk is the gate refusing to call the pass, not the model judging that
there was nothing to read. The question "did the model duck a scene with legible
inner life" is therefore really "did the *gate* duck one," and the answer is
that V4's did, twice.

Reading each of V4's nine skipped scenes against the text:

| Scene | w | Is empty `minds` the right answer? |
|---|---|---|
| sc-015 | 12 | **Yes.** A slug line naming a building. This is the scene V2 gave a mind called "Viewer" and V3 gave one called "The Audience" plus the inner life of Meta CorTechs itself |
| sc-024 | 23 | **Yes.** A car under street lights, nobody visible. V3 declared in `uncertain` that it did not know who was inside and then read Neo's and Trinity's minds anyway |
| sc-113 | 30 | **Yes, and pointedly.** The camera sees the hole; the cops do not. The scene withholds their reaction and both mind arms previously invented one |
| sc-200 | 26 | **Yes.** Tank calling directions off a monitor; the content is functional |
| sc-056 | 12 | Defensible. One gasp and one line of disbelief — a reaction, but a one-line one |
| sc-215 | 27 | Defensible. A scream and "It is a miracle" is a legible beat, but thin |
| sc-164 | 57 | Defensible, and §5 shows what opening it costs |
| **sc-097** | **59** | **No — a duck.** Mouse yanks the curtain and finds the windows bricked up. "Oh no" is the moment his escape closes, and it is legible. V5's gate opens here and reads it correctly |
| **sc-129** | **76** | **No — a duck, and the worse of the two.** "Again, inevitability seems to cinch around Neo" is interiority the script has marked in an action line. V4 never showed the scene to the pass. V5 did, and read it |

**V4's gate: two false negatives, no false positives. V5's gate: no false
negatives, one false positive.** Both ducks are scenes with two or more speaker
cues, which is precisely the signal V5 was built on — so the sample supports
V5's gate design on the recall side without qualification. The four unambiguous
correct declines are all zero- or one-cue scenes, which both gates skip.

Note what this makes of the three previously invented minds. sc-015's "Viewer",
sc-024's mind-reading of a car's unseen occupants, and sc-113's composed cops
are gone from both arms — but they are gone because the gate never asked, not
because the model learned to say no. If the gate is ever removed or widened, no
evidence here says they will not come straight back.

## 5 · V5's gate against V4's

The three scenes V5 adds, scored:

| Scene | w | cues | V4 | V5 | Δ | EI | Cal |
|---|---|---|---|---|---|---|---|
| sc-097 | 59 | 2 | 26 | 26 | 0 | 3 → 4 | 4 → 3 |
| sc-129 | 76 | 3 | 25 | 26 | +1 | 3 → 5 | 5 → 2 |
| sc-164 | 57 | 2 | 26 | **17** | **−9** | 3 → 2 | 4 → **1** |

**Two of three are a wash or a small gain, and both trade calibration for
emotional intelligence at close to one for one.** sc-097 gains a correct read of
Mouse's "Oh no" as the instant the escape route closes and pays 600 words for a
59-word scene. sc-129 gains two genuine readings — the marked "inevitability"
line and Trinity's clipped "Cypher, I thought --" correctly identified as a
suppressed correction — and pays 945 words for 76, which is the rubric's
one-line description of a calibration 2.

**sc-164 is not a trade. It is a failure, and it is the whole V4–V5 aggregate
difference.** The scene is 57 words: Tank at the controls, Trinity's voice asking
for a B-212 pilot program, "Hurry!", Tank finds the disk and loads it. V5 wrote
1,255 words, of which roughly 900 are two mind blocks, and the Trinity block
rests on a premise the script contradicts:

> V5: "She is in the helicopter in sc-164 (she is the one who needs the B-212
> pilot program, which means she is in a B-212)."

She is not. sc-163 — V5's own left neighbour, which it cites — ends with Neo
asking whether she can fly the helicopter and Trinity answering that she cannot
yet, then reaching for the phone. She is on the roof. From that invented premise
V5 builds four hundred words about her fear "that the helicopter is already
beyond her control and that the pilot program is a delay tactic, not a fix," and
reads her two functional lines as the concealment of that fear. The aircraft is
undamaged at this point in the script; the crash is later and is caused by
gunfire, not by whatever she is imagined to be sensing.

The Tank block in the same node has the mirror error, placing him "in the same
posture as when the helicopter pilot was watching in sc-163" — conflating the
hovercraft's controls with the helicopter cockpit — and labels its `grounding`
`in_this_scene` while its `basis` cites sc-163 and an event. The node's own
report flags that contradiction and scores it 1.0.

**So: does anything get worse from opening more? Yes, and the failure has a
shape.** It is not that short scenes are too short for psychology. sc-097 and
sc-129 are 59 and 76 words and the pass handled both. It is that **sc-164 has
two speaker cues and almost no content** — a request, an urgency marker, and a
described action — so the pass, required to produce blocks and given nothing to
read, imported a situation from the neighbouring scene and read that instead.
That is the same failure as V2's "Viewer" and V3's Meta CorTechs, displaced from
*scenes with no people* to *scenes with speakers and no content*. V5's gate
correctly identifies where inner life is usually legible and has no way to tell
whether it is legible here.

Two other V5 losses are **not** attributable to the gate, and I do not count them
as evidence about it:

- **sc-182** (27 → 22, gated open in both arms). V5 writes that Neo's
  round-house "snaps Smith's neck," reading the script's compound adjective as
  the event — V1's exact error from EXP-004b, on the same scene — then has Smith
  "remove his glasses" while its own `what_changes` correctly records them flying
  off. V4 gets both right.
- **sc-148** (fidelity 4 → 3). V5's Neo block speaks throughout of "Morpheus's
  death" as accomplished, when the scene is about Neo preventing it, and its Tank
  block quotes him on an "alpha pattern" and "codes to Zion's mainframe" in
  dialogue that is in neither this scene nor either neighbour.

Both are single-sample differences on scenes both arms treat identically, and
the honest reading at n=1 per cell is sampling noise. The full ledger: V5 leads
on six scenes by 8 points total, V4 leads on four by 17, of which sc-164 alone
is 9 and sc-182 is 5. Set aside the two unattributable scenes and the arms are
2 points apart.

## 6 · The concealment — did V5 actually catch it?

**Yes on sc-148, unambiguously, and the same instruction manufactured a false
positive on sc-164.** Both halves matter.

The keyword check that prompted the question is real but weak: matching
`conceal|unable to say|unfinished|swallow|unspoken|breaks off` across the
sampled nodes gives V1 **0**, V3 **0**, V4 **0**, V5 **8**. A stronger and much
narrower check settles it — **V5 is the only arm in six that quotes the marked
line at all:**

| Arm | node contains "Uncertainty swallows" |
|---|---|
| V0 · V1 · V2 · V3 · V4 | no |
| **V5** | **yes** |

And it is used correctly. V5's Trinity block on sc-148 cites the stage direction
as its `basis`, names it "the key concealment," and — this is the part keyword
presence cannot fake — **identifies what is being concealed**: that the thing
she cannot say is about Neo, not about Morpheus. Its `feels` field reads her
subsequent "I believe Morpheus means more [...]" as a
deflection covering the sentence she just failed to finish, and its `sets_up`
points forward to the confession. That is the correct reading of the setup, the
correct object, and the correct payoff. The rubric's EI 5-anchor is "reads a
concealed motive or an unspoken pressure correctly"; this is that.

**V4 reaches the substance without the line.** Its Trinity block says she is
driven by "a love that she cannot yet articulate" and is "masking her fear and
love with procedural authority" — right in content, and inferred entirely from
the rank speech and the set jaw. It never notices that the script already said
so. That is the exact gap EXP-004b's recommendation 4 described: the pass is
good at inferring interiority from behaviour and does not attend to interiority
the text has marked. V5's instruction closes it; V4's absence of the instruction
leaves it open. Two nodes, one instruction, and the difference is visible.

**The false positive is the price.** Of V5's eight concealment-vocabulary hits,
five are true — four on sc-148, one on sc-129, where "Cypher, I thought --" is
correctly called an unfinished sentence indicating a suppressed correction — and
**three are on sc-164**, where the node writes:

> V5: "The concealment is total and is the point of her being V.O. … the fact
> that the text does not describe any visible reaction is itself the
> concealment."

There is no concealment. Trinity is a voice-over because she is on a roof and he
is on a ship. The instruction told the pass that an unexplained reaction is a
concealment handed to it, and the pass generalised that to *the absence of any
described reaction* — which is the default state of every off-screen character
in every screenplay. On a scene with nothing to read, an instruction to look
harder for something already on the page produces a reading of the page's
silence.

So the honest answer to the question as posed: **the keyword signal is a true
positive on the scene it was raised about, and 3 of 8 of the vocabulary hits
overall are concealment-flavoured language around a moment that has none.** The
instruction works and needs a precondition — it should fire on marked text, and
the marking should be found by matching the script, not left to the model to
decide it has found one.

## Threats to validity

- **n = 15, single sample per cell.** No comparison in this report separates.
  V4 and V5 clear the bar on a fifteen-scene mean and both are 7–4–4 against V1.
- **One evaluator, not blind to arm.** Arms remain trivially identifiable by node
  length and by the `_mind_pass` field printed in every file. This is the largest
  uncontrolled threat and it is now three reports old. It is rank 1 below.
- **Two recommendations are confounded in V4** (gate + `minItems`), and the
  measurement shows only the gate fired. V5 adds two more (gate design +
  concealment instruction) and those are separable only because the concealment
  instruction leaves a lexical trace.
- **V4's 9-point aggregate lead is two nodes**, one of which (sc-182) is not
  attributable to any V5 change. Rescored without sc-182 and sc-148, V5 leads.
- **The `_mind_pass` and `gate` fields are self-reported by the harness**, but
  the gate arithmetic was re-derived independently here from a fresh
  `scriptforge.screenplay.parse`: p75 = 121 words, 93 of 224 scenes with ≥2 cues,
  49 of 224 at ≥150 words. Both gates' open/closed decisions on all fifteen
  scenes match the files exactly.
- **The rubric compresses at the top.** Fidelity, completeness and specificity
  are at or above 4.3 in both arms, so change reality, EI and calibration carry
  nearly all the between-arm variance — the mirror of EXP-004b's short-band
  compression, and a reason not to read the overall means too hard.
- **sc-164 is one scene and it decides the V4/V5 comparison.** The failure mode
  it demonstrates is real and reproducible in principle; that it appeared once in
  fifteen is not a rate.
- **The events file the mind pass reads is still unaudited**, carried over from
  EXP-004b rank 10 and still not done. V5's sc-164 and sc-129 blocks make
  forward claims against it.

## Verdict against the bar

**Mean ≥ 4.0 with no dimension below 3.0: V4 passes at 4.16 (min 3.47), V5
passes at 4.06 (min 3.53).** Both are the first arms in this experiment to do
so, and V4 is the best artifact set on disk.

**Neither passes as a demonstration that the intervention works.** At n = 15
with one sample per cell, V4, V5 and V1 are one arm by sign test, and the
difference between clearing and missing the bar is smaller than the difference a
single node (sc-164, 9 points) makes. The defensible claim is narrower and
better supported: **the gate moves the dimension that was binding, at half the
token cost of running the pass unconditionally, and does not break the dimension
it trades against.** Emotional intelligence on gated-open scenes is 4.17 (V4)
and 4.33 (V5) against V3's 4.33 with the pass running everywhere — the mind pass
loses nothing at all by being gated, which is the single most useful number here
and the one that is not close.

**Three findings that survive independently of the scores:**

1. **The grounding check does not gate.** `tier1()` fixes `score` at
   `scene_variants.py:495` from its own `problems`; `check_grounding_field`'s
   findings are appended at `:601`, after the score exists. V5's seven
   contradictions and V4's four cannot lower their own arms' tier-1. V5's
   "1.000" is a score that cannot see the column printed beside it.
2. **The verbatim check covers a shrinking share of the node.** It reads
   `what_changes[].evidence` only — roughly 90 words of V5's 600-word average.
   The mind pass's `basis`, `feels` and `shows`, where the other 500 live, are
   unchecked, and V5's sc-148 Tank block puts fabricated dialogue in `basis`
   while the arm reports 15/15 verbatim.
3. **`minItems` was never tested.** The model was given permission to return an
   empty `minds` list and, across 15 opportunities in two arms, never once did.

**Cost.** V4 is the cheapest arm that clears: 13,824 output tokens against V3's
21,891 and 476 words per node against 786, for +0.54 on the overall mean. V5
costs 16,649 for 600 words per node and scores 0.10 lower.

## What to try next, ranked

Ordered by what this run showed failing.

| Rank | Action | Why, from this run | Cost |
|---|---|---|---|
| **1** | **Blind A/B at n = 40, three samples per cell, V1 vs V4 vs V5.** Two nodes plus the true scene, "which describes it better," evaluator blind to arm | Nothing in this report separates. Two arms cleared a bar by a margin smaller than one node, judged by one non-blind evaluator who wrote the arms. This has been rank 8, then rank 8 again, and it is now the only thing that can turn any of the last three reports into evidence. `_mind_pass` must be stripped from the files first — it labels the arm on every node | small |
| **2** | **Make the grounding check gate, not annotate.** Recompute `score` after `check_grounding_field`, or fold the check into `tier1` | EXP-004b rank 3 asked for "check and fail the node"; what shipped checks and passes. Four consecutive experiments have now shipped a checker that shares an assumption with the thing it checks, and this is the first where the checker was *right* and the score ignored it. One line | trivial |
| **3** | **Extend the verbatim check to `minds[].basis`.** Any quoted fragment inside `basis` must appear in the scene or in a cited neighbour; fail the block otherwise | V5's sc-148 attributes an "alpha pattern" and "codes to Zion's mainframe" to Tank in a scene containing neither, inside the arm scoring 15/15 verbatim. The mind pass is now 80% of the node and 0% of what is verified | small |
| **4** | **Add a content floor to V5's gate: ≥ 2 cues *and* ≥ 2 dialogue exchanges, or ≥ 2 cues and above some non-dialogue action floor.** V5's gate has perfect recall on this sample and one false positive, and the false positive is a scene with speakers and nothing to read | sc-164 is 57 words of request-and-comply and cost 9 points. sc-097 and sc-129 are 59 and 76 words with real exchanges and cost nothing. The distinguishing feature is not length and not cue count — it is whether anyone responds to anyone. Keep V5's gate; this is a conjunct, not a replacement | small |
| **5** | **Give the mind pass V1's length instruction, and test it with the gate off.** `MIND_SYSTEM_V4`'s "write in proportion" paragraph is in both arms and did nothing measurable: calibration where the pass runs is 3.17 and 2.89 | The pass writes 600–1,300 words regardless of input. The gate hides this; it does not fix it. Until the pass can write 150 words about a small scene, every gate is a workaround and every widening re-exposes the same failure | small |
| **6** | **Precondition the concealment instruction on a matched marker.** Detect *unable to*, *can't bring*, *swallows*, *doesn't say*, trailing ellipses on a speech in the scene text; pass the matched span into the prompt; say nothing when there is no match | The instruction produced the report's best single reading (sc-148) and three false-positive hits on sc-164, where it read the absence of a described reaction as a concealment. Off-screen characters have no described reactions by default, so unconditioned it fires everywhere. This also removes the last free parameter from the concealment change | small |
| **7** | **Re-run V4 with `minItems: 1` restored, gate unchanged.** If the scores are identical, drop the schema change from the arm | The permission to decline was never exercised in 15 opportunities. It is currently an untested change riding along in a passing arm, and EXP-004's whole lesson was about bundled interventions that cannot be attributed | trivial |
| **8** | **Cross-field consistency on the prose, carried over unchanged.** V5's sc-182 summary has Smith "remove his glasses" while its own `what_changes` records them flying off | EXP-004b rank 6, still not done, and it now has an intra-node instance rather than an inter-field one. A node that contradicts itself in adjacent fields is detectable without a model | small |
| **9** | **Referent and compound-adjective binding.** EXP-004b rank 7's referent case, plus: a compound adjective describing a blow is not a record of its effect | V5 reproduced V1's exact sc-182 error ("neck-snapping reverse round-house" → "snaps Smith's neck") two arms later, on the same scene, from a different prompt. It is a recurring, specific, cheap-to-check misreading | small |
| **10** | **Audit `events_draft.json`.** Carried over from EXP-004b rank 10, still not done, and now load-bearing | V5's sc-164 and sc-129 both make forward claims against the event layer, and sc-164's are wrapped around a fabricated premise. The supply lesson has been applied to the script and never to the events file | moderate |

**Retired.** The claim that V5's tier-1 1.000 is a quality signal. It is a
verbatim-evidence score over a fifth of the node, computed before the arm's own
grounding findings are appended, on an arm carrying seven of them.

**The general rule this run earns.** *A gate that makes a failing component pass
has not fixed the component; it has narrowed the domain where you observe it.*
The mind pass's calibration is 3.17 and 2.89 where it runs — indistinguishable
from V3's 3.14 on comparable scenes — and 4.33 and 4.50 where it does not,
because there it is not the mind pass at all. Both arms clear the bar by not asking the question on two-thirds and
two-fifths of the sample respectively. That is a legitimate engineering answer
and it is not a measurement of the pass. The moment the gate widens — a work
with longer scenes, a looser threshold, V5's own better gate — the same
calibration failure returns at full strength, which is exactly what sc-164 is.
