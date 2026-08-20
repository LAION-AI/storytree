# Handshake — read this first

You are picking up a project you have no memory of. This file is the fastest
path back to working state. Written 18 August 2026.

---

## What this is

**storytree** generates screenplays as an explicit graph — story root, exposé,
plots, entity profiles, events, scenes, prose — and runs the same machinery
*backwards* to recover that graph from a finished screenplay. The reverse
direction produces training data for distilling narrative understanding into
smaller models.

Repo: `christophschuhmann/storytree`, private. Working dir
`/home/deployer/laion/bookwriter`. `GH_TOKEN` and `HYPRLAB_API_KEY` are in
`.env` (chmod 600, gitignored). **Never print them.**

## The one-paragraph state

The bottom-up swarm works and runs a 224-scene feature in ~20 minutes. The scene
layer has been optimised through six variants. **The scores below are superseded:
a blind A/B has since been run and no arm clears the bar** — see *Since then*.
V4 and V5 remain the best arms and remain indistinguishable from each other. The
remaining blocker for autonomy is **not quality** — it is that eight measurement
errors have occurred and the pipeline caught none of them, and the blind result
is a ninth of the same kind.

## Where things are

| | |
|---|---|
| **Start here** | `docs/14-rubric-scores-and-next-steps.md` — all scores, the ceiling analysis, 14 proposals |
| Raw data + method | `docs/13-scene-experiments-data.md` |
| Narrative of the swarm | `docs/12-swarm-results.md` |
| Evaluator's own reports | `docs/experiments/EXP-004-scene-variants.md` (1,424 lines, four passes) |
| Design | `distill/WHITEPAPER-SWARM.md` + `distill/swarm/*.md` (14 sections) |
| Model behaviour, measured | `docs/05-model-behaviour.md` — **read this before changing any prompt** |
| Serving and reproduction | `ops/README.md` |

**Code:** `distill/swarm.py` (eight-stage bottom-up pipeline),
`distill/scene_variants.py` (V0–V5 and the tier-1 harness),
`reconstruct/scriptforge/{presence,grounding,ensemble}.py`,
`tools/check_integrity.py`.

**Run outputs:** `reconstruct/runs/matrix/fix_v0` … `fix_v5` (the scored arms),
`swarm/` (full bottom-up run), `swarm_v1_empty_scenes/` (kept as evidence of a
bug, do not delete).

---

## What worked

**Inverting the direction.** The top-down pipeline wrote a story root first and
everything under it inherited its poverty — nine entities where thirty were
needed, then all 22 events at the one location that existed, then an ending
placing a character somewhere her own state model could not hold. Reading scenes
first and inducing upward fixed it: 23 locations against 1, 13 concepts against
0, 11 reversals against 0.

**Cutting context.** V0 gave the model ~100,000 characters of script per scene.
The median scene in this work is **45 words** — 0.01% of the window. V1 cuts to
the scene plus two neighbours: better on every measure, **4.5× faster and 15.7×
cheaper**.

**Splitting facts from minds.** They want opposite context. Pass A reads the
scene alone; pass B adds prior scenes and the event layer. Emotional intelligence
2.80 → 3.67.

**Gating the mind pass.** Running it everywhere broke calibration (2.13). Gating
on content — **≥2 speaker cues, or 1 cue above the work's own 75th percentile** —
keeps the gain and drops the cost. Prefer this over an absolute word count, which
does not transfer between screenplays.

**Schema-level enforcement over instructions.** Binding location and cast as
`const`/`enum` fixed what a prompt clause could not. General rule, measured
repeatedly: *instructions repair local fields, structure repairs global
consistency.*

**The canary.** One agent per run gets a deliberately blank scene. Anything it
writes is recall. It fired on its first execution and is the only check in the
system that detects failure by construction.

## What did not work

**Prompt clauses for global properties.** A failure-derived addendum fixed
confidence calibration and *regressed* location adherence. See EXP-001.

**Speculative decoding on a sparse MoE.** An n-gram drafter was a 25%
*regression* on GLM-5.2. The model's own trained MTP head won 45%. On a dense
model (Qwen) the same technique gives +138%.

**Concurrency on a sparse MoE.** Aggregate throughput is flat from 1 to 8
concurrent requests. Do not restructure a job from serial to parallel there.

**FP8 for GLM-5.2.** It reads 2.2× more bytes per token than the current
quantisation, so it makes decoding *slower*, and it fits on no reasonable
configuration.

**Letting the mind pass decline.** `minItems: 1` was dropped so an empty `minds`
list would be legal — the model never once used it in fifteen opportunities,
because the gate had already removed every scene where declining was right.
Untested, not disproven.

---

## The eight measurement errors

This is the most transferable thing here. **Every one produced a confident number
computed over the wrong thing, and not one failed loudly.**

| # | Check | What it actually did |
|---|---|---|
| 1 | trajectory flatness | tested a field the schema never had |
| 2 | leak detector | tokenised raw JSON; punctuation blocked every match |
| 3 | grounding | read another schema's field names |
| 4 | arm comparison | averaged over different node counts, then compared |
| 5 | correspondence | tested for a quote where the schema asked for a paraphrase |
| 6 | scene slicing | sliced the raw file with cleaned-text offsets — 13 of 15 scenes never reached the model, and the metric could not see it because it compared against the same corrupted slice |
| 7 | clean count | a new check written into the list an older count derives from |
| 8 | grounding gate | appended after the score was fixed, so contradictions could not lower it |

**Six of eight were found by an outside reader; two by recomputing. Zero by any
check in the system.**

### Rules earned from them

1. **Never grade against a list your own apparatus generated.** That measures
   compliance, not correctness. It once produced a schema that *mandated* the
   error it was meant to prevent.
2. **Validate the metric before trusting the result.** Read the check next to the
   schema it checks.
3. **Presence is not integrity.** A guard that accepts any non-empty input passes
   a misaligned one unchanged.
4. **A guard that substitutes empty input for missing input is worse than no
   guard** — it converts a crash into a confident wrong answer.
5. **A check that has never been shown to fail is not a check.** Every one of the
   eight passed silently on data it should have rejected.
6. **Dry-run before spending GPU time.** Two bugs were caught by ten-second
   checks; several were not, and cost full runs.

---

## Since then: the blind A/B was run, and it changed the picture

Step #1 below was done. Three blind rounds, fifteen scenes, three independent Opus judges,
same six-dimension rubric, arms relabelled with the key withheld. Everything in
[`docs/cognitino/results.md`](cognitino/results.md).

**The bar has not been cleared by anything.** Blind scoring puts every arm ~0.4 below its
published figure:

| Arm | Published (docs/14) | **Blind** |
|---|---|---|
| V4 | 4.16 | **3.63 – 3.88** |
| V5 | 4.06 | **3.66 – 3.74** |
| V1 | 4.02 | **3.51 – 3.57** |

The claim in this document that *"V4 and V5 are the first two arms to clear the bar"* does not
survive blinding. **Neither does. Nor does any arm.** That is what the non-blind caveat below
predicted, and it is the single most important correction to make to this file.

**V4 and V5 remain indistinguishable from each other** across all three rounds. Judge variance
between rounds moved V4 by 0.24 and swapped its rank with V5 — larger than several differences
previously reported as findings.

**Three extensions were tried and all three lost to plain V4:**

| Extension | Mean | Effort vs V4 |
|---|---|---|
| CogniTino abstraction layer, 2-scene windows | 3.37 | 1.9× calls, ~17× input tokens |
| CogniTino abstraction layer, 5-scene windows | 3.29 | same |
| V4 + a separate deepening pass | **2.57** | 2.4× calls, 3.3× input |

The pattern is consistent and is the transferable lesson: **every attempt to append more
analysis cost more in proportion and fidelity than it gained in insight.** Twice the same
mistake was made — forcing content onto scenes that cannot carry it. The abstraction layer does
win emotional intelligence (+0.37 against V4), so the mechanism works; it is not worth its cost.

**Practical consequence:** return to V4, and treat its published score as ~3.7, not 4.16.

**Then the model was swapped, and that is what moved the number.** Same V4 code, same sample,
same rubric, blind: **Ornith-1.5-397B scores 3.77 against Qwen3.8-27B's 3.38** (+0.39,
CI95 [0.00, 0.78], p = 0.052 — not significant, but it clears the bar on 6 of 15 scenes
against 1). Emotional intelligence, the dimension nothing else could move, goes 2.67 → 3.60.
Costs 4.7× the model time, 4 GPUs per instance and 224 GB on disk, and is mechanically
*worse* (tier-1 0.883 vs 0.967). See [`docs/ornith/`](ornith/).

**Replicated on fifteen fresh scenes with zero overlap: +0.378, p = 0.017.** Pooled over both
samples, n = 30: **+0.383, CI95 [0.133, 0.628], p = 0.0019.** The effect is near-identical
across two disjoint samples, and calibration — the dimension the fresh sample was expected to
flatter — came out exactly level, so the advantage is not a sampling artefact.

**The bottleneck was the model, not the scaffold.** Three scaffold changes lost; one model
change won, and it is the only result in this line of work that has reproduced.

New readers, in order:
[`docs/scene-layer-explained.md`](scene-layer-explained.md) — what the six scene conditions
were, what differed, what worked and what did not ·
[`docs/rubric-explained.md`](rubric-explained.md) — the dimensions and what 0–5 mean ·
[`docs/events/`](events/) — the layer above scenes, and the first measurement of it.

**Naming warning:** `V0–V5` are *scene conditions*; `V1–V5` in the event rubric are *scoring
dimensions*. Unrelated, same letters.

## What was about to happen next

Ranked, from `docs/14`:

1. **Blind A/B at n=40, three samples per cell, V1 vs V4 vs V5.** Nothing in
   three evaluator reports separates statistically. Strip `_mind_pass` first — it
   labels the arm on every node. *This is the only step that turns any of the
   quality work into evidence.*
2. **Negative test cases for every check.** Would have caught most of the eight.
3. **Test the short-scene ceiling hypothesis.** All five worst-ceiling scenes are
   12–27 words with 0–1 cues. Either the rubric asks them for what they cannot
   have, or a twelve-word scene is the wrong unit and belongs to its event as a
   beat. One cheap test distinguishes these and it has not been run.
4. **Gate on ≥2 cues AND an actual exchange.** V5's single false positive cost 9
   rubric points on one scene.
5. Then: the other layers. Events, plots, profiles, exposé and root have never
   been rubric-scored. The bar was to finish the scene layer first, and it is
   now cleared.

## Things that will bite you

- **The evaluator is one Opus agent, not blind to arm, who helped specify the
  designs it scores.** Three consecutive reports share this. Discount accordingly
  and prefer the blind A/B.
- **Opus subscription limits.** A weekly cap has already killed three agents
  mid-task. Tell every spawned agent to write incrementally; a partial file is
  worth more than none.
- **Commit messages with backticks or quotes break the shell.** Always
  `git commit -F <file>`.
- **History was force-pushed** (to purge a screenplay). `git fetch` before
  committing.
- **`pkill -f <pattern>` matches the shell running it** and kills the launcher.
  Use the bracket trick or kill by PID.
- **Copyright.** The reconstruction reads a copyrighted screenplay. Structure is
  derived and committed; prose is stored by reference and never copied. Check
  `.gitignore` before adding anything under a `runs/` tree — a narrower pattern
  once failed to cover a newly created directory and a full screenplay was
  committed and had to be purged from history.

## How to get back to the good results

```bash
./ops/launch_all.sh                                    # 8 endpoints, ~2 min to load
python3 distill/scene_variants.py --variant v5 --out /tmp/check
```

Expect tier-1 ≈ 0.88 corrected, 15/15 verbatim evidence, ~600 words per node,
~16.6k output tokens for fifteen scenes. If those numbers are far off, something
in serving changed — check the request body against `ops/README.md` before
suspecting the model.

For the full pipeline:

```bash
python3 distill/swarm.py reconstruct/runs/matrix --out /tmp/swarm --per-endpoint 8
```

~20 minutes, 373 calls, `protocol.json` with per-stage timings and violations.

---

## The honest summary

The architecture is sound and the scene layer clears its bar. But the strongest
claim the data supports is narrow: **on fifteen scenes, read once, by one
non-blind evaluator, two configurations scored above 4.0 and did not
distinguish themselves from a simpler one.**

The interesting work left is not more variants. It is making the system able to
detect its own failures — because the record is eight for eight in the wrong
direction, and that, not quality, is what stands between here and a hundred books
unattended.
