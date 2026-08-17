# EXP-004 · Cutting context at the scene layer — and the supply bug underneath it

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
