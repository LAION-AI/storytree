# EXP-001 · Failure-derived system-prompt addendum

**Status: mixed.** One clause improved its target metric on both items. One clause
showed no effect. One clause coincided with a regression on the single item where
improvement was possible. n=2.

---

## Question

Does a system-prompt addendum written against a model's *measured* failures reduce
those specific failures, when nothing else changes?

The broader question behind it: are the failure modes found by rubric evaluation
addressable by instruction, or are they capability limits? These have different
consequences — the first is a prompting problem, the second means the model is the
wrong tool for the layer.

## Prediction

*Recorded before running.*

Clauses A (confidence calibration) and B (concrete alternatives) were expected to
work, because both ask for a change in how an existing field is filled rather than
for new capability. Clause C (envelope discipline) was expected to work most
strongly of the three, since it is the most mechanical: restate the location, then
check the decision against it.

Expected direction on all three: improvement. Expected magnitude: largest on C.

## Design

Single variable. The addendum is appended to `BLIND_SYSTEM`; everything else —
prompts, schemas, scaffold structure, scene envelopes, dossier contents, decoding
parameters, thinking suppression — is byte-identical between arms.

| | Arm A (baseline) | Arm B (addendum) |
|---|---|---|
| System prompt | `BLIND_SYSTEM` | `BLIND_SYSTEM + addendum_for("qwen3.8-27b")` |
| Everything else | identical | identical |

Both arms ran on the *unfiltered* dossiers (`STRIP_DOSSIERS=0`), matching the
conditions under which the baseline nodes and the GLM comparison were produced.
The blind-channel fixes landed after these nodes were generated and deliberately
were not applied here, because changing the context and the prompt together would
measure neither.

## Materials

| | |
|---|---|
| Model | `orcarouter/Qwen3.8-27B-Uncensored-FP8`, vLLM, FP8/Marlin, one copy per GPU |
| Endpoints | `127.0.0.1:8104`, `:8105` (arms run on separate GPUs, concurrently) |
| Decoding | temperature 0.7, `enable_thinking: false` (verified: `reasoning_content` empty on every call) |
| Items | `sc-001`, `sc-002` of `reconstruct/runs/matrix` |
| Addendum | `narrativeforge/model_notes.py`, `addendum_for("qwen")` → 4,561 chars, 764 words |
| Baseline outputs | `reconstruct/runs/matrix/transitions_qwen/` |
| Treatment outputs | `reconstruct/runs/matrix/transitions_qwen_addendum/` |
| Measurement | `reconstruct/tools/measure_addendum.py` |

Reproduce:

```bash
export LOCAL_BASE_URL=http://127.0.0.1:8104/v1 LOCAL_MODEL=qwen3.8-27b
export MODEL_FAMILY=qwen STRIP_DOSSIERS=0 ADDENDUM=1
python3 tools/run_local_matrix.py runs/matrix sc-001 --think off \
        --out transitions_qwen_addendum
python3 tools/measure_addendum.py runs/matrix sc-001 sc-002
```

## Metrics

Each maps to one clause. Clauses without a metric were not tested, and are listed
as such.

| Metric | Computed how | Tests |
|---|---|---|
| Mean `decision.confidence` | field read directly | Clause A |
| Generic flip conditions | regex over alternatives for "if this were a different work" and variants | Clause B |
| In-envelope | keyword overlap between slug-line location and `decision.resolution` + `craft`, **confirmed by reading both arms of both items** | Clause C |
| State changes naming a declared variable | set membership against declared `state_variables` ∪ `state` | Shared 2 |
| Words | token count of the whole transition | the "spend more words on second-order material" note |

**Not tested by any metric:** Clause D (invention must not contradict what you were
handed), Shared 1 (roster closure — the counter resolves entity ids, not cues, and
was not trustworthy enough to report), Shared 3 and 4 (numeric sums, field naming —
these apply to the entity/event layers, not to transitions).

So this experiment tests three of the eight clauses.

## Results

| Scene | Arm | In envelope | Confidence | Generic flips | State ok | Words |
|---|---|---|---|---|---|---|
| sc-001 | baseline | no (0/2) | 95 | 2 | 2/2 | 6,837 |
| sc-001 | addendum | no (0/2) | **85** | 2 | 3/3 | 7,016 |
| sc-002 | baseline | **yes (2/2)** | 90 | 1 | 3/3 | 4,816 |
| sc-002 | addendum | no (0/2) | **65** | **0** | 1/1 | 4,954 |

| Arm | n | In envelope | Mean confidence | Generic flips | State ok | Words |
|---|---|---|---|---|---|---|
| baseline | 2 | 1/2 | 92 | 3 | 5/5 | 5,826 |
| addendum | 2 | **0/2** | **75** | **2** | 4/4 | 5,985 |

## Interpretation

**Clause A worked, on both items and in the same direction.** Confidence fell 95→85
and 90→65. This was the sharpest failure in the evaluation — the model asserted
90–95 on forecasts wrong in location, character and event simultaneously (rubric
dimension T2, −2.33 against GLM, its single worst result). Asking it to name the
established fact that would have to be false before writing a number moved it. That
is the clearest positive here.

**Clause B is one item's worth of signal.** Generic flips went 1→0 on sc-002 and
2→2 on sc-001. Consistent with a real effect, equally consistent with noise.

**Clause C did not work and may have hurt.** The one item where improvement was
possible got worse: sc-002 baseline named the correct hotel; the addendum arm named
no location and drifted to different characters than the roster gave. sc-001 failed
in both arms, so it carries no information about the clause.

**Words did not move** (5,826 → 5,985, +2.7%), so the instruction to spend more
length on second-order material had no measurable effect at this budget.

### What does not follow

- Not that the addendum is net positive. One clause up, one flat, one down, n=2.
- Not that clause C is wrong. It is one item; it may have been crowded out rather
  than mistaken.
- Nothing about rubric quality. These are mechanical counters. The rubric
  dimensions this was written against need the evaluator to re-score.

### A hypothesis worth its own experiment

The addendum adds 4,561 characters of instruction. If attention to instructions is
itself a limited budget, adding clauses may displace attention from constraints
already in the prompt — the envelope block among them.

That would make this **the same budget-dilution phenomenon measured on output
volume, appearing on instruction adherence.** If it holds, it has an uncomfortable
consequence: prompt fixes do not compose, and each added clause has a cost paid by
the clauses already there. Testing it requires arms with clause C alone, clauses
A+B alone, and all clauses, on enough items to separate them — EXP-002.

## Threats to validity

- **n=2.** Everything here is directional at best. The confidence result is the only
  one with the same sign on both items.
- **The in-envelope metric is keyword matching.** It was confirmed by reading all
  four outputs, so the reported values are right, but it would not generalise
  unchecked to other scenes.
- **sc-001 is uninformative for clause C** — both arms fail. Its roster is a generic
  cue (`BIG COP`), which the evaluation identified as the condition under which this
  model invents freely rather than grounding.
- **Three of eight clauses tested.** The addendum is not validated as a whole; the
  headline is about three clauses.
- **Single temperature, single sample per cell.** At temperature 0.7 the
  within-condition variance is unmeasured and could exceed the between-condition
  differences reported.
- **No correction for multiple comparisons.** Five metrics, one moved decisively.
