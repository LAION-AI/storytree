# EXP-003 · The bottom-up swarm, first full run on a 224-scene feature

**Status: refuted, on a cause the design did not anticipate.** The run completed
in 18.4 minutes with 373/373 calls succeeding and produced a valid artifact at
every one of the eight stages. It is nonetheless not an evaluation of bottom-up
reconstruction, because **stage 1 never received a single line of scene text.**
`stage1_scenes` tests `hasattr(scene, "start")` on a dataclass whose fields are
`start_char`/`end_char`, so all 224 scene agents were handed an empty scene and
the first 120,000 characters of a 133,937-character script. The scene layer that
every higher layer was induced from is, by measurement, 7.1% correspondent with
the scenes it claims to describe. n=224 nodes, 33 events, 6 plots, 219 entities,
40 profiles, 1 root, 1 exposé.

The bug is one line. Its consequences are not, and the interesting part of this
entry is what the eight stages did *with* a fabricated substrate — which stages
noticed, which repaired, which laundered it into something that reads well.

---

## Question

The swarm design (`distill/WHITEPAPER-SWARM.md`) claims that inverting the
pipeline — reading scenes first, blind of any superstructure, and inducing the
higher layers from them — structurally prevents the two failures four rubric
passes found in the top-down arm: under-declaration strangling the layers below,
and attention drift across a whole feature.

Does the first full run support that, and is each stage's artifact fit for the
purpose that stage exists to serve?

## Prediction

*No prediction was registered for this evaluation.* The whitepaper's own
pre-registered claims are used instead, since they were written before the run:

| # | Claim, as written in the whitepaper | Outcome |
|---|---|---|
| P1 | ≈27 min wall for all ten stages on 8×A100 | **Supported, and beaten** — 18.4 min for stages 1–8 |
| P2 | ≈4.55M output tokens, of which ≈2.32M for stages 1–8 | **Refuted** — 242,988, 9.6× short |
| P3 | Under-declaration cannot strangle the lower layers, because the lower layers are written first | **Untestable this run** — see §Stage 1 |
| P4 | Divergent naming is safe to permit because stage 5 repairs it procedurally | **Refuted** — the repair splits the antagonist three ways |
| P5 | "Every stage boundary needs its own mechanical check, or the failures simply move" | **Supported, painfully** — every stage had a check; every check verified a property other than the one that failed |
| P6 | A 27B model writing one sentence where a paragraph is needed is a capability limit, mitigated by one narrow task per call | **Mixed** — stage 6 is genuinely deep; stage 7 produced 685 tokens for the whole story root |

P5 is the finding worth keeping. Eight stages ran, all eight checks passed or
reported only trivia, and the run's central defect — that no agent had read the
work — was invisible to all of them.

## Design

Observational, n=1 run. No arms, nothing varied. Five artifacts sampled by hand
per stage, spread across the work rather than taken from the front (stages 7 and
8 have one artifact each and were read whole), plus four whole-population
metrics computed against the script and the scene map, described under §Metrics.
Comparison against the top-down artifacts already on disk at
`reconstruct/runs/matrix/artifacts/`, which cover the same work at the same
layers.

## Materials

| | |
|---|---|
| Code | `distill/swarm.py` — **untracked at time of run**; repo HEAD `3f4e1f8` |
| Design | `distill/WHITEPAPER-SWARM.md` |
| Model | `qwen3.8-27b`, 8 endpoints `127.0.0.1:8100–8107`, 8 concurrent each = 64 |
| Decoding | temperature 0.7, thinking off, schema-constrained JSON |
| Work | The Matrix, 224 scenes, 133,937 chars, `reconstruct/runs/matrix/script.normalized.txt` |
| Outputs | `reconstruct/runs/matrix/swarm/artifacts/`, protocol at `../protocol.json` |
| Log | `reconstruct/runs/swarm_full.log` |
| Baseline | `reconstruct/runs/matrix/artifacts/` (top-down, complete superstructure, 4 of 224 scenes) |

Totals from `protocol.json`: 1,104.6 s, 373 calls, 373 ok, 0 failed,
11,373,846 tokens in, 242,988 out.

## Metrics

Four population metrics were computed over all 224 nodes. Each is decidable from
`script_map.json` and the normalised script, so none of them grades against a
list this apparatus authored.

1. **Evidence-in-own-scene.** Every quoted span of ≥25 characters inside a
   `what_changes[].evidence` field, whitespace-normalised, tested for occurrence
   in (a) the scene's own character range and (b) anywhere in the script. Tests
   whether the node read its scene. Validated by hand on sc-206: the check
   agreed with the reading.
2. **Best-match scene.** Content words of the node's summary and evidence, idf-
   weighted over the 224 scene texts, scored against every scene; the arg-max is
   compared to the node's own id. Exploratory and noisy — a paraphrase can score
   its neighbour higher than itself — so it is reported as a distribution of
   offsets, not as a pass rate.
3. **Present-name grounding.** Each name in `present`, expanded through its
   alias set, tested for occurrence in the scene text. Over-counts: a character
   referred to only as "she" is really present and scores as a miss. Reported
   with that caveat and confirmed by hand on the five worst nodes.
4. **Verbatim leakage.** 8-gram overlap between generated prose and the script.

Stage-level artifacts were also re-checked against the pipeline's own checkers,
run at a different point in the sequence than the pipeline runs them.

---

## Stage 1 — scene nodes, blind of the tree

### Does it do its job?

No. It did not do a shallow version of its job; it did a different job.

`stage1_scenes` builds the scene text as

```python
text = script[scene.start:scene.end] if hasattr(scene, "start") else ""
```

`scriptforge.screenplay.Scene` declares `start_char` and `end_char`. There is no
`start`. `hasattr` returns False for all 224 scenes, the `THE SCENE` block of
every prompt was empty, and the guard that was meant to be defensive silently
selected the empty branch and reported nothing. Verified directly against the
parser.

The second half compounds it: the prompt appends `script[:120000]` of a
133,937-character file. **Scenes sc-183 to sc-224 — 42 scenes, the entire third
act — were not present anywhere in any stage-1 context window.** Nodes were
produced for all 42 anyway.

### What the measurements say

| Metric | Result |
|---|---|
| Quoted evidence spans ≥25 chars | 193 across 224 nodes |
| …found in the scene they are attributed to | **10 (5.2%)** |
| …found somewhere in the script | 126 (65.3%) |
| Nodes with ≥2 quoted spans and none in their own scene | 45 |
| Nodes whose text best matches their own scene (idf) | 16/224 (7.1%) |
| …restricted to sc-001–182 (script in context) | 8.8%, n=182 |
| …restricted to sc-183–224 (beyond the 120k cut) | **0.0%, n=42** |
| `present` names not findable in their own scene | 425/675 (63.0%), over-counted |

The offset distribution of metric 2 is not flat. Modes sit at +5 and +6 (60
nodes) with a strong positive bias — 129 nodes best-match a *later* scene, 79 an
earlier one. That is the signature of an agent trying to locate "scene 118" by
counting slug lines in a wall of script and landing a few headings past it.

### The failure, in three artifacts

- **sc-072.** Script, in full: the ship is quiet and dark, everyone is asleep —
  11 words. The node returns a 400-character summary of the mess-hall breakfast,
  seven characters present, and two state changes with quoted dialogue.
- **sc-197.** Script: Neo springs up the apartment stairs — 14 words. The node
  returns *the same breakfast scene*, near-verbatim to sc-072's.
- **sc-206.** Script: Neo kicks in a third-floor window and the door numbers
  count backwards, 310, 309 — 23 words, no speakers, and 6,800 characters past
  the truncation point. The node returns the film's opening hotel raid: Trinity
  at a computer, the BIG COP entering with armed officers, a gunfight, three
  state changes and quoted evidence. None of it is in the scene. **This is the
  famous-film confound, caught in the act**, and it is the cleanest instance
  because the model had no text at all and produced a confident, schema-valid,
  internally consistent node anyway.

### On the 22 recorded violations

Confirmed as real, and a symptom — but the important point is how badly they
undercount. `check_stage1` tests three things: that a node exists, that
`what_changes` is non-empty, and that each change's `who` appears in `present`.
All three are *internal* consistency. Nothing in the check compares a node to its
scene, so a node that describes a different scene entirely, coherently, passes.
Of the 22, one is a no-op change and 21 are `who`-not-in-`present`, most of them
collective nouns the schema permits (`Crew`, `Group`, `Narrative Flow`,
`LOBBY`). Meanwhile 45 nodes quote evidence that does not exist in the scene
they are attributed to, and not one of those is in the violation list.

The underlying node quality is genuinely decent *as prose about The Matrix* —
mean summary 413 characters, mean 1.72 changes, axes used sensibly, evidence
fields carrying real dialogue. It is worthless as a scene layer.

### What would fix it

1. `script[scene.start_char:scene.end_char]`, and delete the `hasattr` guard.
   A guard that silently substitutes empty input for missing input is worse than
   a crash; if the attribute may be absent, `getattr(scene, "start_char")` should
   raise.
2. Assert non-empty scene text before dispatch, and fail the run rather than the
   call.
3. Never truncate the script by character count. `script[:120000]` deleted act 3
   and left no trace in `protocol.json`. If the script exceeds the context
   budget, that is a fact the protocol must record.
4. **Add a correspondence check to the stage-1 boundary.** For each node,
   require that at least one quoted evidence span of ≥25 characters occurs in the
   scene's own character range, and that at least one `present` name occurs in
   the scene text or in `script_map`'s speaker cues for that scene. Both are
   arithmetic over data on disk. On this run the first clause alone rejects 45
   nodes and every one of the fabrications above.
