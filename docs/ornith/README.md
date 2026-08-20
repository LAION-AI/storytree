# Ornith-1.5-397B on the V4 scene layer

*New to the scoring? [`docs/rubric-explained.md`](../rubric-explained.md) explains the six
dimensions and the 0–5 scale.*

The first change in this line of work that actually improves V4. Every earlier attempt —
the CogniTino abstraction layer, narrower windows, a separate deepening pass — lost to plain
V4. **The bottleneck was not the scaffold. It was the model.**

The comparison is the cleanest in the project: identical V4 code, identical fifteen-scene
sample, identical rubric, three blind judges. `--ports` and `--model` were already
parameters, so **not one line changed**. Only the model behind the endpoint.

---

## Result

| Dimension | Qwen3.8-27B | **Ornith-1.5-397B** | Δ |
|---|---|---|---|
| **emotional_intelligence** | 2.67 | **3.60** | **+0.93** |
| specificity | 3.60 | 4.27 | +0.67 |
| fidelity | 3.73 | 4.07 | +0.33 |
| completeness | 3.33 | 3.67 | +0.33 |
| change_reality | 3.00 | 3.33 | +0.33 |
| **calibration** | 3.93 | 3.67 | **−0.27** |
| **Mean** | **3.38** | **3.77** | **+0.39** |

**Paired bootstrap over scenes: +0.389, CI95 [+0.000, +0.778], p = 0.052.** The interval
touches zero exactly, so on this sample alone it was **called not significant** — and a
replication was run rather than the number being talked up. It held: see below.

Bar cleared (mean ≥ 4.0, no dimension < 3.0): **Ornith 6 of 15 scenes, Qwen 1 of 15.** Ornith
better on 9 scenes, worse on 3, tied on 3.

Five of six dimensions go to Ornith, but the difference lives mostly in **emotional
intelligence**. Blind, judges credit it with reading "Trinity's stillness as coiled readiness
rather than compliance" and "the cops still believing Brown is one of them"; the Qwen arm
names emotion at surface level and once attributes a vanity the text does not support.

**Calibration is the one dimension Ornith loses** — ~950 words on a 157-word scene. The same
pattern every extension in this project has shown: more text costs proportion. Here the gains
outweigh it instead of cancelling it.

## What it costs

| | Qwen3.8-27B | Ornith-1.5-397B |
|---|---|---|
| Model time, 15 scenes | 193 s | **916 s** (4.7×) |
| GPUs per instance | 1 | **4** |
| Words per node | 476 | 641 |
| tier-1 (mechanical) | 0.967 | 0.883 |
| Weights on disk | ~27 GB | **224 GB** (Q4_K_M) |

**Mechanically it is worse.** tier-1 drops from 0.967 to 0.883 and grounding contradictions
rise from 4 to 5 — while verbatim evidence improves, 15/15 against 13/15. Higher rubric
scores with lower mechanical scores is worth noting rather than smoothing over: the two
measures disagree, and the mechanical one is the cheaper of the two to run.

**The first run produced only 12 of 15 scenes** (parse failures, 16 of 28 calls succeeded).
The second produced 15/15. The setup is less robust than the 27B, and comparing on 12 scenes
would have been the handshake's measurement error #4 — averaging over different node counts,
then comparing.

## Serving

`ops/serve_ornith.sh`. Q4_K_M across 4×A100-80GB, ~58 GB per GPU, 43 s to load. Two instances
fit on eight GPUs (ports 8110/8111).

Four things cost time and are worth recording:

- **`curl -sI` reports 3032 bytes for every GGUF in the repo.** That is an HTML error page,
  not the file. The real sizes are only in the LFS metadata (`/api/models/.../tree/main`).
  Taken at face value it looks like an empty repository.
- **The Hub's Xet transfer runs at ~620 MB/s**; a single `curl` stream managed 47 MB/s. 224 GB
  in under seven minutes instead of eighty-five.
- **llama.cpp publishes no Linux CUDA binaries**, only Windows. It has to be built from source
  — CUDA 12.8, `-DCMAKE_CUDA_ARCHITECTURES=80`.
- **Check the architecture before loading 224 GB.** The GGUF declares `qwen35moe` (512 experts
  × 11B, 60 blocks), which build b10509 supports. Reading that from the file header took
  seconds; discovering it after a failed load would have cost minutes and a wasted download.

`-np 1` follows the GLM finding in `ops/README.md`: aggregate throughput on a sparse MoE is
flat across concurrent slots, and slots divide the context window, so one slot with the whole
window is strictly better.

---

## Replication on a fresh sample: it holds

The first result sat at p = 0.052 with an interval touching zero, which is a reason to repeat
it rather than a conclusion. It was repeated on **fifteen new scenes with zero overlap** with
the frozen set (`replication_sample.txt`), drawn with the same stratification and a new seed,
both models run on the same day, blind-scored by three fresh judges.

| Dimension | Qwen3.8-27B | **Ornith-1.5-397B** | Δ |
|---|---|---|---|
| **emotional_intelligence** | 2.93 | **3.80** | **+0.87** |
| specificity | 3.80 | 4.47 | +0.67 |
| fidelity | 3.67 | 4.20 | +0.53 |
| change_reality | 3.40 | 3.60 | +0.20 |
| completeness | 3.73 | 3.73 | 0.00 |
| calibration | 3.53 | 3.53 | 0.00 |
| **Mean** | **3.51** | **3.89** | **+0.38** |

**+0.378, CI95 [+0.067, +0.678], p = 0.017 — significant.** Bar cleared: **Ornith 8 of 15,
Qwen 2 of 15.** Better on 10 scenes, worse on 3.

**Pooled across both samples (n = 30): +0.383, CI95 [+0.133, +0.628], p = 0.0019.**

The effect is near-identical across two disjoint samples — +0.389 and +0.378. That is the
strongest evidence produced in this line of work, and the only result here that has
reproduced.

### Two things this settles

**The pre-registered worry was wrong, in Qwen's favour.** Before running, the concern was that
the fresh sample would flatter Ornith: its smallest scene is 32 words against the frozen set's
12, and calibration — the one dimension Ornith lost — was the dimension that discriminated on
tiny scenes. In the event **calibration came out exactly level at 3.53**. The advantage does
not come from a sampling artefact; it comes from emotional intelligence, specificity and
fidelity.

**The mechanical tier-1 score is not a usable proxy for quality.** It reversed between samples
— Ornith 0.883 → 0.917, Qwen 0.967 → 0.900 — while the rubric gap stayed constant. tier-1
varies more between samples than between models, so it cannot stand in for the rubric.

### Where the 27B is still better

Recorded because the aggregate hides it. Judges found consistently that Ornith **leaves
`speaking` and `objects_that_matter` null** while quoting the very dialogue those fields
should list, and that its **length barely tracks scene size** — a 172-word scene receives an
analysis comparable to a 593-word one. One node contained **corrupted non-English tokens
mid-sentence**, which is a character-encoding artefact worth watching.

Qwen took the only fidelity 5 in one batch and imports less foreign material on short scenes.

---

## Limits

- **Two samples, 30 scenes, one film, one judge model.** The result reproduced, which is more
  than anything else here can claim, but it is still one screenplay.
- **Judge variance has moved arm means by up to 0.24 between rounds** in this project. The
  pooled effect (+0.383) is larger than that, and it held across two independent judge panels
  on disjoint scenes — which is the specific reason to trust it over the single-sample number.
- **Only the scene layer was tested.** Events, plots, profiles, exposé and root have never
  been rubric-scored against either model.
- Ornith leaves `speaking` and `objects_that_matter` null on most nodes while quoting the
  dialogue itself, and on one 12-word scene filled a deliberate blank with neighbouring-scene
  content. The 27B fills schema slots more reliably and flags the genuine unknowns. One Ornith
  node carried corrupted non-English tokens mid-sentence.
- Both arms made the same knowledge-attribution error on sc-148, recording Neo's prior state
  as "believes he is the One" when the Oracle has already told him otherwise. That is a
  recurring failure across every arm in this project and is not a model difference.
