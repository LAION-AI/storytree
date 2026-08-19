# Results — blind evaluation against V1 / V4 / V5

**The CogniTino approach lost, significantly, on every comparison.** The hypothesis in
[README.md](README.md) — that splitting perception from abstraction would lift the
dimensions the V-series never scored well on — is refuted by this run.

Recorded in full because a negative result that cost this much compute is worth more written
down than repeated.

---

## The numbers

Fifteen scenes (the frozen V-series sample), four arms, blind labels, three independent Opus
judges scoring the **same six-dimension rubric** used for V0–V5, with the source scene read
from the screenplay for every judgement.

| Arm | System | Fidelity | Complete | Specific | Change | **Emotional** | Calib | **Mean** |
|---|---|---|---|---|---|---|---|---|
| arm-A | **V5** | 3.87 | 4.13 | 4.73 | 2.87 | **3.60** | 3.33 | **3.76** |
| arm-C | **V4** | 4.13 | 3.73 | 4.47 | 2.87 | 2.93 | 3.73 | **3.64** |
| arm-B | **V1** | 4.33 | 3.47 | 4.53 | 2.87 | 2.13 | 4.07 | **3.57** |
| arm-D | **CogniTino** | 3.73 | 3.07 | 4.00 | 2.60 | 2.80 | 3.00 | **3.20** |

Paired bootstrap over scenes:

| Comparison | Difference | 95% CI | p |
|---|---|---|---|
| CogniTino − V5 | **−0.556** | [−0.80, −0.29] | 0.0001 |
| CogniTino − V4 | **−0.444** | [−0.71, −0.20] | 0.0001 |
| CogniTino − V1 | **−0.367** | [−0.64, −0.11] | 0.0030 |

All three significant. CogniTino cleared the bar (mean ≥ 4.0, no dimension < 3.0) on
**0 of 15 scenes**; V5 on 2, V4 on 1, V1 on 1.

**The hypothesis specifically fails where it was aimed.** The whole argument for splitting the
layers was that emotional intelligence had never exceeded 3.67. CogniTino scores **2.80** on
it — below V5, and below what the V-series reached with a single pass.

---

## The other finding, which matters more

The same rubric, applied blind, scores the V-series roughly **0.4 lower** than the
non-blind evaluation did:

| Arm | Non-blind (docs/14) | **Blind (here)** | Δ |
|---|---|---|---|
| V5 | 4.06 | **3.76** | −0.30 |
| V4 | **4.16** | **3.64** | −0.52 |
| V1 | 4.02 | **3.57** | −0.45 |

The handshake records the claim that *"V4 and V5 are the first two arms to clear the bar"* of
mean ≥ 4.0. **Under blind evaluation with the same rubric and the same sample, neither does.
Nor does any arm.**

This is what the handshake's own caveat predicted — *"the evaluator is one Opus agent, not
blind to arm, who helped specify the designs it scores"* — and blinding was ranked next step
#1 for that reason. It was worth doing: the bar has not actually been cleared by anything,
and the scene layer is not the solved problem the previous reports implied.

---

## Why CogniTino lost

Three causes, in order of size. The first is a design error I had already measured the fix
for and failed to apply.

### 1. The abstraction windows are too wide

The V-series generates **one node per scene, one dedicated call**. CogniTino drafts
abstraction for **five scenes per call**, so each scene gets a fifth of the attention. The
output is correspondingly thin:

| | |
|---|---|
| Abstraction objects per scene | **2.6** |
| Mind-type objects per scene | **1.4** |
| Scenes with **no** mind object at all | **51 of 225 (23%)** |

A layer whose entire purpose is inner life left 23% of scenes without a single inference
about anyone's mind. That shows up directly as completeness 3.07 and emotional intelligence
2.80.

The uncomfortable part: **the Alexandria work in this same session already measured this
effect and found the fix.** Narrowing extraction windows from 12 scenes to 3 was worth +0.055
on the MCQ instrument, and *neither* narrowing nor prompt changes worked alone. I applied that
finding to the perception layer and then built the abstraction layer at five scenes per call
without carrying it across.

The drafting prompt also says *"Produce whatever mix the scenes actually support; do not
pad."* Written to prevent inflation, it appears to have licensed silence.

### 2. Confidence without warrant on scenes too small to carry it

Judges flagged, with specifics: a `probable` reading of anonymous police in a 30-word scene,
tagged as concerning a character not present in the sequence; a `near-certain` mind object
whose evidence points four scenes forward; an `uncertain` field holding a verbatim copy of
`dramatic_function`. Calibration scored **3.00**, the lowest of any arm.

This is the same skew the graph's own checks flagged and passed anyway: 189 `near-certain`
against 2 `speculative`. **The calibration check tests uniformity, not skew**, so a
distribution this lopsided clears it. That is a gap in the check, and it is now a known one.

### 3. Change reality is inherited, not abstraction's fault

CogniTino scores lowest on change reality (2.60) — but `what_changes` in this arm comes from
the **perception layer's** beat state changes, not the abstraction layer. Judges found
changes to states the scene never touches (windows `openable → bricked_up` where the bricks
predate the scene) and one pair that literally cancels (`grounded → airborne`,
`airborne → grounded`).

That is a Knowledge Unit defect surfacing through the composed node. Worth separating,
because fixing the abstraction layer will not fix it.

**And it is not only CogniTino's problem: no arm averages above 2.87 on change reality, and no
node scored above 3 on it anywhere in the sample.** Whatever is wrong is wrong with the node
contract, not with any variant of it.

---

## What is actually worth keeping

The layer is not worthless — it is under-supplied. Judges credited it, blind, with:

- **the most faithful beat-level transcription** of any arm;
- the only arm to record Neo's vitals `flatline → active` at sc-215 rather than describing the
  monitors;
- the only arm to get sc-129's four people on the street right, where the others list a
  character who is only a voice from the ship;
- `would_be_wrong_if` falsifiers that "do real work" where they are grounded in-scene.

So the machinery works; the volume and the calibration do not.

## Next, in order

1. **Rebuild the abstraction layer at 1–2 scenes per window.** Directly tests the diagnosis,
   and the effect size is already measured on the neighbouring layer.
2. **Make the calibration check test skew, not just uniformity.** It passed a distribution of
   189 `near-certain` to 2 `speculative`.
3. **Require a mind object per present character** on scenes above a size threshold, bound in
   the schema rather than requested in the prompt — the standing finding in this project is
   that structure repairs what instructions do not.
4. **Fix change reality at the perception layer**, where it originates.
5. **Re-score V0–V5 blind.** Their published scores are inflated by ~0.4 and the bar they were
   reported to clear has not been cleared.

## Method, and its limits

Three independent Opus judges, five scenes each, arms relabelled under a seeded shuffle with
the key withheld in a separate directory. Both systems mapped onto one common set of
presentation slots so field names do not identify the arm; content moved, never removed.

**Blinding is label-level, not structural.** The abstraction arm carries beat-reference
evidence and falsifiers on its mind entries, and a careful judge could infer from that which
arm is new. Removing them would hide the properties under evaluation. Disclosed rather than
claimed away.

**n = 15 scenes, one film, one judge model.** The differences are significant on a paired
bootstrap over scenes, but the sample is the same fifteen scenes used throughout this project,
and the judges are the same model family that produced three of the four arms.

Four errors were made building this harness before it produced a usable number; they are
listed in [README.md](README.md#evaluation-harness--errors-made-and-what-they-cost). Two would
have produced confident wrong figures.

## What is published here, and what is not

`blind_eval.json` (the aggregate) and `rubric6.txt` (the instrument) are in this folder.

**The three raw judge files are not.** The rubric requires every score to carry evidence
"naming a specific field or quoting text", so the judges quoted the screenplay — up to
seventeen consecutive words. Those files are exactly as useful for auditing as they are
unpublishable, and the same rule applies to them as to every other artifact in this project:
structure travels, source text does not. They stay on the machine that produced them.

This was caught by a pre-commit sweep, not by design. The instruction that made the judges
quote was written without noticing it would make their output unshippable.
