# 13 · How to tell whether this is actually better

The claim is falsifiable and the instruments to falsify it already exist. Four arms of
top-down reconstruction sit on disk, scored by the same evaluator against the same
rubric with the same anchors. The bottom-up swarm has to beat them on the same three
scenes, with the same model, before anything else is worth saying about it.

---

## 13.1 The rubric

Eighteen dimensions, defined in `docs/07-quality-evaluation.md` §1 and machine-readable
in `distill/rubrics/`. Integers 1–5, anchors written for 1, 3 and 5. **Hard marking: 3
is "acceptable, would survive review with notes", not "good".** A layer that fills
every schema slot correctly and adds no judgement scores 3 at best on the dimensions
that matter.

**Universal (7), applied to every node type:** internal consistency (A), referential
integrity (B), specificity — the transplant test (C), schema and instruction compliance
(D), dramatic competence (E), psychological plausibility (F), independent-writer band (G).

**Type-specific (9):** plot spine causality and resistance reality (P1, P2); entity t0
discipline and voice separability (E1, E2); event change reality and externalisation
(V1, V2); transition envelope discipline, deliberation honesty and specimen craft
(T1, T2, T3).

**Reconstruction-only (2):** fidelity of inference (R1) and leakage resistance (R2).
R1 splits by whether the node was written sighted or blind — for blind nodes it scores
coherence and dramatic competence of a decision made without the answer, explicitly
*not* agreement with the source.

Two procedural rules do more work than the anchors: **every score requires one sentence
of evidence naming a specific field or quoting text** — a score without a field
reference is not a score — and the node is scored **as delivered**, not as it could be
read charitably, because the reader downstream is a program.

Three dimensions carry most of the diagnostic load.

**G is the anti-fake dimension and it is the one this design is betting on.** It asks
two things: could a different competent writer, given exactly these inputs, have landed
here (in band), and could they have produced this *without* the inputs (load-bearing)?
A 3 means "in band, but the inputs did little work — essentially a restatement of the
layer above in the local vocabulary". G measured **2.33** for GLM across nine nodes,
the weakest dimension by a wide margin, and the commentary on one entity node is the
whole problem in a sentence: *a one-line prompt "write a character dossier for Neo from
The Matrix" produces this document, and the four reconstructed layers above it
contributed nothing detectable.* If the swarm's induced superstructure is real, G is
where it shows up. If G does not move, the tree is decorative.

**T1 is the dimension the mechanical checks are supposed to retire.** Envelope
discipline scored 1.67 for GLM and 1.00 for Qwen, with 0/3 roster compliance for both.
`distill/rubrics/scene.json` already records the conclusion: these are missing
assertions, not prompt problems — enforce them mechanically before scoring. Which means
**T1 near 5 in the swarm arm is not evidence the swarm is better.** It is evidence the
checks in §11 are wired up. Do not spend it as a quality result.

**C-versus-G is the shape to watch.** GLM measured C 4.67 and G 2.33 — excellent
texture, poor judgement about what belongs. It writes the sentence well and chooses the
wrong sentence to write. Reproducing that profile in the swarm arm means nothing
changed.

For stage-10 nodes the scene rubric adds five dimensions that the transition rubric had
no way to ask about, and they are the ones that test §10 directly: **S1** state-change
justification (does every change name the plot *and step* it discharges, or a category
word), **S2** beat-level mental simulation (is the full model present at every
important-change beat, or only at the two ends), **S3** whole-life — do characters have
lives outside the scene that measurably change a line or a timing, **S4** perception
across senses, **S5** prose discipline.

---

## 13.2 The comparisons already on disk — and a correction to how they are quoted

| Arm | Path | Model / configuration |
|---|---|---|
| GLM alone | `reconstruct/runs/matrix/transitions_local_off` | glm-5.2, scaffolded, thinking off |
| Qwen alone | `reconstruct/runs/matrix/transitions_qwen` | qwen3.8-27b, identical prompts and schemas |
| Qwen grounded | `reconstruct/runs/matrix/transitions_qwen_grounded` | + schema binding, post-check, one repair |
| Ensemble | `reconstruct/runs/matrix/transitions_ensemble` | GLM writes, Qwen keeps the books, code decides |

**The four figures usually quoted — 64.2%, 57.1%, 61.7%, 72.2% — are not computed over
the same node set, and should not be put in one row.** 64.2% is GLM's overall across
all nine scored nodes (308/480). 57.1% is Qwen's total over the six nodes that could be
matched to GLM (180/315). 61.7% and 72.2% are the grounded and ensemble arms over the
three transition nodes only (111/180 and 130/180) — the upper layers were never
regenerated for those arms and are `not_regenerated` in the JSON.

The comparable ladder, all four arms on the same three blind transitions, same rubric,
same evaluator:

| Arm | Total | % |
|---|---:|---:|
| Qwen alone | 90 / 180 | **50.0** |
| Qwen grounded | 111 / 180 | **61.7** |
| GLM alone | 117 / 180 | **65.0** |
| Ensemble | 130 / 180 | **72.2** |

That is the baseline the swarm has to beat: **130/180 on `sc-001`–`sc-003` of the
Matrix reconstruction.** Not 64.2%.

One confound is recorded in the ensemble's own metadata and must travel with the
number: its writer is `glm-5.2-abliterated-q3km`, a 3-bit abliterated quant, while the
"GLM alone" arm at 117 used `glm-5.2`. They are not the same model. The direction is
unknown but a Q3_K_M abliterated quant would normally be the weaker one, which makes
the ensemble's gain a conservative estimate.

Two dimensions moved *down* in the ensemble and deserve attention rather than being
averaged away: schema and instruction compliance 4.0 → 2.0, and deliberation honesty
4.33 → 2.0. An arm can win on total while losing the two dimensions that say whether
the model was actually deciding anything.

---

## 13.3 The mechanical counters

Deterministic, outside the 1–5 scale, already computed for the existing arms in the
`_external_counters` blocks of `docs/eval/*.json`. These are cheap, they do not need a
judge, and several of them are the counters that motivated the inversion in the first
place.

**Structure and grounding** (from `tools/check_integrity.py` and `check_grounding`):

| Counter | GLM | Qwen | Why it matters |
|---|---|---|---|
| entities declared (lattice) | 17 | **9** | the founding failure |
| state-variable `init` contract violations | **62/62** | 0/30 | a state layer that cannot be type-checked |
| plot→entity refs resolving | 14/14 | 17/17 | referential integrity |
| screen-time shares sum | 1.0 | **1.2** | arithmetic |
| synopsis keys covered | 17/17 | 16/17 | coverage |
| event magnitudes on anchor | 127/127 | 34/34 | closed-enum compliance |
| state changes landing in-domain | **42/127** | 32/34 | the check that separates the models |
| `state_changes_implied` valid (transitions) | 4/12 | 1/7 | the layer's actual contribution |
| transition stays in envelope location | 3/3 | 1/3 | fixed to 3/3 by grounding |
| specimen honours envelope roster | **0/3** | **0/3** | fixed to 0 violations by §11 |

**Depth** (from `score_transition`): theory-of-mind towers, towers reaching the third
degree, towers with a named error, trajectory phases, sense channels filled, options
weighed, alternatives marked `nearly_chosen`, specimen lines, risks tested against the
dialogue.

**Leakage**: six-gram overlap against the source script. Measured 0.016% (GLM), 0.03%
(Qwen), 0.007% (grounded), 0.003% (ensemble), with 1/75 six-gram hits inside GLM's
specimen lines and 0 in every other arm.

**Two warnings about these counters, both earned.**

The depth counters **reward volume**, and `docs/05` §2 says so explicitly. GLM wrote
47,964 words across three transitions against Qwen's 16,518 and scored higher — but
`words_per_rubric_point` was 410 for GLM and 184 for Qwen. Report that ratio alongside
any total, or a longer arm wins by being longer.

And the counters must be computed against **the script**, not against the
reconstruction's own artifacts. This is §11.3 applied to evaluation: an arm graded
against a roster its own apparatus generated measures compliance, not correctness, and
that has already happened once here at the cost of a headline number.

---

## 13.4 What would falsify the claim

The claim is: *inverting the order — inducing the superstructure from the scenes rather
than imposing it on them — produces better nodes than the top-down pipeline.* Five
comparisons, in descending order of how decisive they are.

**1 · Same scenes, same model, head to head.** Run the swarm on the Matrix
reconstruction and score `sc-001`–`sc-003` with the same rubric, anchors and evaluator.
The claim fails if the swarm arm does not exceed **130/180**. n=3 is far too small to
settle it — every existing result in this project is n=3 or n=2 and directional at best
— so the real version of this test is n ≥ 20 scenes across ≥ 3 scripts, with the
evaluator blind to arm and order.

**2 · The founding counters.** The inversion was motivated by a specific mechanical
failure: nine entities where thirty to forty were asked for, one location, all 22 events
placed at it, and a character ejected into a place her own state model could not hold.
If the bottom-up entity layer does not raise the entity count, does not produce a
location entity per place the script visits, and does not spread events across them,
then the founding diagnosis was wrong — under-declaration was not caused by top-down
ordering — and the architecture is answering a question that was not asked.

**3 · The rewrite control.** The swarm does two descents. A top-down run does one. So a
straight win might be "rewriting beats not rewriting" rather than "bottom-up beats
top-down". **The control is a top-down arm given a second pass over its own scenes with
the full tree in context.** If that control lands within noise of the swarm, the
inversion is not what produced the gain, and the cheap version of the improvement is a
rewrite pass on the existing pipeline.

**4 · The dramaturgical-function ablation.** §10's specific claim is that an agent that
knows what a scene is *for* writes a better scene. Isolate it: stage 10 with the
per-beat function field required, versus stage 10 with it removed and everything else
identical. Score S1, S2, E and G. If G does not move, the field is bookkeeping.

**5 · Cost-adjusted.** The swarm is ~1,840 calls and ~5.7M output tokens per script
(§12). Give the top-down arm the same budget — more scenes, more repair rounds, a
larger model on the upper layers — and compare. `docs/05` §7 already establishes that
putting the strongest model on the ~8 upper-layer calls is nearly free and determines
everything downstream, which is a much cheaper hypothesis than ten stages. If a top-down
run with Opus on the upper eight calls matches the swarm, the swarm is the wrong
solution to a real problem.

---

## 13.5 What a negative result looks like, concretely

Not "it didn't work". These are the specific shapes, and three of them are partial
results worth keeping rather than failures.

- **The flat result.** Swarm scores 125–135/180 on the three matched scenes. Within
  noise of the ensemble at 130, at roughly 6× the calls. Verdict: the ten stages bought
  nothing a two-model ensemble with a bookkeeper does not already buy, and the ensemble
  is the design to develop.

- **The compliance result.** Mechanical counters go clean — T1 to 4–5, roster
  violations to 0, in-domain landing to 100% — while C, E, F and G stay where they were.
  This is the honest partial: the swarm bought **admissibility, not quality**. It is
  exactly what EXP-002 predicted for grounding and then found to be wrong in the other
  direction, so it is a live possibility either way. Worth shipping, worth not
  overclaiming.

- **The texture result.** C rises, G stays at 2–3. More particular detail, same
  judgement about what belongs. This reproduces the measured GLM profile exactly and
  means the pipeline is producing better sentences about the wrong things.

- **The volume result.** Total rises but `words_per_rubric_point` rises with it. The arm
  won by writing more. Ties to the S2 requirement in §10 — mental simulation at every
  important beat multiplies word count by construction, so this failure mode is
  *designed into* the swarm and must be controlled for explicitly, not hoped away.

- **The propagation result.** One stage boundary is wrong on one script and every node
  below it is wrong in the same direction, so the arm's scores are bimodal across
  scripts rather than uniformly mediocre. Diagnostic rather than fatal — it says the
  check at that boundary is missing (§11) — but it will look like high variance if
  nobody plots per-script distributions.

- **The regression.** Swarm scores below 111/180, i.e. below the grounded single-model
  arm. Given that stage 10 has more context, more constraints and more calls than any
  existing arm, this would most likely mean context dilution: the agent is handed the
  whole tree and attends to none of it. The test is to strip the superstructure back to
  the parent event alone and see if the score recovers.

One methodological note that applies to all of them. Every score in this project was
produced by a single evaluator (Opus 5) applying anchors it has now applied four times.
That is good for comparability across arms and bad for independence. A result that
matters should be re-scored blind, with arm labels stripped and node order shuffled,
and preferably by a second evaluator — and the disagreement rate reported, because a
rubric two evaluators cannot agree on is not measuring what it says it measures.
