# Experiment log

Every intervention tried on this system, whether it worked or not, in a format
that can be reconstructed later without access to the person who ran it.

**This log exists to be written up.** The target is a NeurIPS-quality paper, and
that constrains how entries are written: a result that cannot be reproduced from
its entry is not recorded, and a negative result is recorded with the same care
as a positive one. Most of what is here did not work, which is the point — the
interesting claims in this project came from predictions that measurement
destroyed, and those are only usable later if the prediction was written down
*before* the measurement.

## Format

One file per experiment, `EXP-NNN-short-slug.md`, containing:

| Section | Contents |
|---|---|
| **Question** | The single question, phrased so a result can contradict it |
| **Prediction** | What was expected, written before running. Non-negotiable — a prediction added afterwards is worthless |
| **Design** | Arms, what varies, what is held fixed, and how the confound was controlled |
| **Materials** | Exact commit, model ids, endpoints, prompts, seeds, node ids, file paths |
| **Metrics** | Each metric, how computed, and which clause or hypothesis it tests. Metrics with no hypothesis are exploratory and labelled so |
| **Results** | Raw numbers with n. No aggregation that hides n |
| **Interpretation** | What follows, and explicitly what does not |
| **Threats to validity** | Sample size, confounds, metric weaknesses, anything that would be raised in review |
| **Status** | `supported` / `refuted` / `mixed` / `inconclusive` / `running` |

## Rules that have already earned themselves

**Write the prediction first.** Three predictions in the inference work were
falsified within an hour each. They are only citable because they were recorded
before the measurement — otherwise the write-up is hindsight claiming foresight.

**Report n everywhere, including in the summary line.** Several results here rest
on one to three items. A mean over n=1 is a number, not evidence.

**Validate the metric before trusting the result.** Two metrics in this project
produced confident, wrong readings: a trajectory-flatness check that tested a
field the schema never had, and a leak detector that tokenised raw JSON so
punctuation prevented every match. Both reported clean results on broken data.
An entry should say how its metric was checked, not just what it returned.

**Read a sample by hand before believing a counter.** The envelope-discipline
counter in EXP-001 is keyword matching; it was confirmed by reading the outputs.
Where that check was not done, the entry must say so.

**A negative result is a result.** Do not delete a failed arm.

**Never grade against a roster the harness authored.** EXP-002 reported
"off-roster speakers 2 → 0" while the constraint that produced the output and the
check that scored it drew on the *same* wrong list. A check that shares its
source of truth with the thing it checks measures compliance, not correctness.
Corrections go in the entry, in place, not in a new one.

## Index

| ID | Question | Status |
|---|---|---|
| [EXP-001](EXP-001-model-notes-addendum.md) | Does a failure-derived system-prompt addendum reduce the failures it was written against? | mixed |
| [EXP-002](EXP-002-grounding-scaffold.md) | Do the failures a prompt clause could not fix yield to schema-level enforcement? | supported on quality (+11.7pts); violation count corrected downward |

## Earlier work, recorded outside this format

These predate the log and are written up in the docs rather than as protocol
entries. They should be converted if they are used as paper claims:

| Finding | Where | Status |
|---|---|---|
| Budget dilution: models divide a fixed output budget across requested structures rather than scaling to the task | [05](../05-model-behaviour.md) §1 | supported, n=3 conditions |
| Scaffolding (one deep structure per call) takes a scene from 0/4 to 4/4 passing | [05](../05-model-behaviour.md) §1 | supported, n=4 scenes |
| Hidden reasoning is 83.6% of generated tokens; suppressing it costs no measured quality | [05](../05-model-behaviour.md) §2 | supported on throughput, quality n=3 |
| `reasoning_effort: "low"` is a silent no-op selecting maximum effort | [05](../05-model-behaviour.md) §2 | supported, mechanism identified in chat template |
| Speculative decoding on a sparse MoE is a 25% regression at 21% acceptance | [06](../06-local-inference.md) | refuted the prediction, supported the mechanism |
| The same technique on a dense model is +138% at 77.5% acceptance | [06](../06-local-inference.md), [reports/qwen](../../reports/qwen-local-deployment.md) | supported |
| Concurrency gives zero aggregate throughput gain on a sparse MoE, 5.59× on a dense one | [06](../06-local-inference.md) | refuted the prediction, supported the mechanism |
| Blind-channel leakage via sighted dossiers, plot spines, and a backwards join | [03](../03-reconstruction.md), [07](../07-quality-evaluation.md) §12.1 | supported, three separate mechanisms found |
| GLM-5.2 vs Qwen3.8-27B: level forward, 15 points apart in reverse | [07](../07-quality-evaluation.md) | supported, n=6 nodes |
