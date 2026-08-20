# How the scoring works

*An explainer for readers new to this project. No background assumed.*

Every number reported in these documents comes from one instrument: six questions asked of a
scene analysis, each answered with a whole number from 0 to 5. This page explains what the
questions are, what the numbers mean, and — just as importantly — what they cannot tell you.

---

## What is being scored

The pipeline reads a screenplay and produces, for each scene, a structured **scene analysis**:
who is present, what happens, what changes, what people want and conceal, what the scene sets
up. The analysis is what gets scored, always **against the actual scene text**. A judge reads
the real page from the screenplay and then asks whether the analysis is true of it.

That last point is what separates this from most LLM evaluation. The judge is not asked
whether the analysis *sounds* plausible. It is asked whether it is *correct about a specific
page*, which the judge has in front of it.

---

## The scale: what 0 to 5 mean

The scale is deliberately harsh, and the harshness is the point. Its calibration is:

| | |
|---|---|
| **5** | Nothing to fix. A competent professional would sign this off unchanged. |
| **4** | Good. One small thing an editor would query. |
| **3** | **Acceptable — "would survive review with notes."** Not good. Adequate. |
| **2** | A real defect that a downstream consumer would trip over. |
| **1** | Fails at the thing the dimension asks about. |
| **0** | The dimension cannot apply, or nothing was produced. |

**3 is the anchor to understand.** A scene analysis that fills every required field correctly,
contains no errors, and adds no judgement scores **3 at best** on the dimensions that matter.
It is not a middling grade meaning "fine". It means *this is the floor of usable*.

This is why the scores in this project cluster between 3.0 and 4.0 and why nothing has yet
averaged 4.0 across all six. That is not the pipeline failing — it is the scale doing what it
was built to do. A generous scale would have called the work finished long ago and hidden
every difference we later measured.

**Whole numbers only.** No 3.5. A judge that cannot decide between 3 and 4 must commit,
which forces the reasoning to be explicit.

**Every score carries evidence.** The judge must write one sentence naming the specific field
it is scoring or quoting the text it checked against. A score without that is not a score.

---

## A naming collision to know about

The scene layer's six experimental conditions are called **V0–V5**. The event layer's rubric
dimensions are *also* called **V1–V5**. They are unrelated: scene-V5 is a way of prompting,
event-V5 is the question "is the mental state recorded at both endpoints?".

Where both could appear, this documentation writes scene conditions as `scene-V4` and event
dimensions by name. The ids in the code are unchanged, because renaming them would invalidate
every recorded score.

## The six dimensions

### 1. Fidelity — *is it true of this scene?*

Does the analysis describe what actually happens on this page?

- **5** — every claim is true of this scene; nothing asserted that the scene does not support
- **3** — the central action is right; one or two claims are wrong, or imported from a
  neighbouring scene, or belong to a different moment
- **1** — describes a different scene, or gets the central action wrong

The most damaging failure here is **knowledge attribution**: crediting a character with
knowing something the story has not yet told them. In *The Matrix* the analyses repeatedly
recorded Neo as "believing he is the One" *after* the Oracle has told him he is not. That one
false premise then propagates into everything built on top of it, which is why it is treated
as a serious error rather than a detail.

### 2. Completeness — *is anything load-bearing missing?*

- **5** — every change the story depends on is recorded; a reader could rebuild the scene's
  function from the analysis alone
- **3** — the main change is present; one significant beat or participant is missing
- **1** — most of what matters is absent, or an incidental detail stands in for the scene

### 3. Specificity — *could this be pasted onto a different scene?*

The transplant test. If the analysis would read as true of a dozen other scenes, it is
worthless even if every sentence in it is defensible.

- **5** — names, objects and turns that occur only here; unmistakably this scene
- **3** — mostly specific, but with at least one piece of filler like `before: "Idle or
  observing"`
- **1** — could describe any scene; placeholders throughout

A special case: an analysis that is **vividly specific about the wrong scene scores 1**,
because pasted onto the scene it names, it reads false.

### 4. Change reality — *are the recorded changes real, and do they matter?*

The pipeline records state changes as `before → after`. This dimension asks whether those are
genuine transitions.

- **5** — each is a real state transition the story uses later
- **3** — changes are real, but at least one restates the action rather than naming a
  transition, or is trivial
- **1** — no-ops, unstated befores (`before: "Not explicitly stated"`), or changes to a state
  this scene never touches

The distinction that trips every arm:

```
not a change   door: closed → open           (that is the action, restated)
a change       neo.trust: provisional → staked  (later scenes depend on which side of it we are on)
```

**This is the weakest dimension across every system tested**, typically 2.6–3.4. Nothing has
yet fixed it, and it appears to be a defect in the node contract rather than in any model.

### 5. Emotional intelligence — *is what people want, fear and conceal read plausibly?*

- **5** — reads a concealed motive or an unspoken pressure correctly, and briefly
- **3** — emotion named at surface level; not wrong, not deep
- **1** — emotion absent where the scene is built from it, or attributed wrongly

Naming an emotion is not enough:

> **weak** — "Trinity is tense during the escape."
> **strong** — "Trinity keeps working the trace after the line is compromised, which means she
> has decided the information outweighs her own extraction, and she has told no one."

For a scene with no people in it, 3 is the default — inventing an inner life where there is
none is not rewarded.

### 6. Calibration — *is the length and confidence proportionate?*

- **5** — length tracks scene size; uncertainty flagged where the text is genuinely ambiguous
  and absent where it is not
- **3** — modestly over- or under-written, or confident where it should hedge
- **1** — a 900-word analysis of a 12-word scene, or a one-line node for a 500-word scene;
  confident assertion with no basis

This dimension exists because of the material. Scenes in this screenplay run from **12 to 511
words**, and the median is **45**. Without calibration, a system could score well on every
other dimension by writing exhaustively about everything — and several did exactly that.
Calibration is the dimension that has most often decided the outcome here.

---

## The bar

**Mean ≥ 4.0 across all six dimensions, and no single dimension below 3.0.**

The second half is doing real work: an analysis averaging 4.2 but scoring 2 on fidelity does
**not** pass. One serious defect is not redeemed by strength elsewhere.

Across three blind evaluations, **no system has cleared this bar as an average**. The best
arms clear it on 6–8 of 15 individual scenes.

---

## How a comparison is run

1. **Fixed sample.** Fifteen scenes, chosen once, spread across the film and across scene
   lengths, then frozen. Re-picking it would make new numbers incomparable with old ones.
2. **Blind labelling.** Systems are relabelled `arm-A`, `arm-B`… under a seeded shuffle. The
   key mapping labels to systems is written to a **separate directory the judges never read**.
3. **One shape.** Both systems' output is mapped onto the same field names, so a judge cannot
   identify a system by the shape of its output rather than its quality.
4. **Three independent judges**, five scenes each, each reading the real screenplay.
5. **Un-blind and test.** Scores are joined to the key afterwards, and differences are tested
   with a **paired bootstrap over scenes** — comparing both systems on the *same* scene and
   resampling, which controls for some scenes simply being harder than others.

## What the numbers cannot tell you

**A difference smaller than about 0.25 is probably noise.** Judge variance between rounds has
moved the same system's mean by up to 0.24 — larger than several differences that earlier
reports in this project treated as findings.

**Blind is not the same as fair.** Blinding here is label-level. Systems producing genuinely
different objects can sometimes be told apart by a careful judge from the shape of what they
produce. Where that is true it is stated rather than claimed away.

**n = 15 is small.** A result at p = 0.05 on fifteen scenes is a reason to run it again, not a
conclusion. The one result in this project that reproduced on a second, disjoint sample
(Ornith vs Qwen) is the only one worth treating as established.

**The judges are the same model family as some of the systems being judged.** A shared blind
spot would be invisible to this design.

**Recognition is not reconstruction.** These scores measure whether an analysis is correct
about a page. They do not measure whether a story could be rebuilt from it.
