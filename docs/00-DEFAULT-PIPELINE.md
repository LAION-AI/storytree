# DEFAULT PIPELINE — the sanctioned path from screenplay to story tree

**This file is normative.** It names, per layer, the model, the process and
the exact command that produced the best measured result, with the evidence
for each choice. Deviate only with a new measured comparison (see
`docs/EXPERIMENT-LOG.md` for how we measure). Last updated 2026-08-27;
every score below is from the fixed judging instrument (§ Judging).

## The layer order

Reverse direction (screenplay → tree), which is what this repo runs:

```
screenplay text
  → scene layer → event layer → meta layer → entity layer
  → plot layer → exposé → story root
```

### Two extensions of this pipeline

- **[`reasoning_traces/`](../reasoning_traces/)** — after a tree is built,
  reconstructs the chain-of-thought that would justify each layer's output,
  and packages it as fine-tuning data. Runs either as a batch over existing
  trees or as a daemon that traces trees as this pipeline finishes them.
- **[series-season-storytree-pipeline](https://github.com/LAION-AI/series-season-storytree-pipeline)** (separate repo, currently
  private) — applies this same layer order to a whole TV season instead of
  one film, adding a "Stage 0" that reconstructs scene boundaries in
  transcripts that have no `INT./EXT.` headings.

## Per-layer defaults

| Layer | Model | Process | Best run | Score / gate |
|---|---|---|---|---|
| Scenes | **Ornith-1.5-397B** (local) | one pass per scene + verbatim cap + paraphrase pass | `runs/scenes_ornith_v5_clean` | model-swap gain +0.38 (p=0.002, replicated); 224 nodes, 0 copied runs |
| Events | **Ornith-1.5-397B** | build-10 recipe: segment → scaffold → compose (64k, wave=1) → repair → chain → audit→regenerate → verify → verbatim gate | `runs/events_build10_full` | first arm through the gate: mean 4.17, worst dim 3.56; blind b4→b7 +0.69 CI [+0.49,+0.88] |
| Meta | Ornith-1.5-397B | one pass | `runs/meta_layer_v2b` | pass (unchanged since) |
| Entities | Ornith-1.5-397B | one pass | `runs/entity_trial_v2` | 6.4 eval; known weakness: near-twin differentiation (Brown/Jones) |
| **Plots** | **Muse 1.2 (GLM-5.3)** via Zen | **one pass**, `distill/plot_layer.py` (perspective discipline / membership / self-contained causality prompt; structural-only repair) | `runs/plot_layer_muse` | **3.33 — best of 11 measured arms, ranking judge-invariant; still below the 4.0 gate** |
| Exposé | **Muse 1.2** | one pass, `distill/expose_layer.py` | `runs/expose_muse` | 4.44 PASS (and free of the jacket-copy truncation in `expose_v1`) |
| Story root | Ornith (v3) or Muse — tie | one pass, `distill/root_layer.py` | `runs/story_root_v3` (4.80) / `runs/story_root_muse` (4.73) | both PASS; difference within panel drift |

The public explorer (`webapp/explorer/storytree.json`, built by
`tools/build_explorer_data.py`) serves exactly these runs.

### Why one-pass for plots, when fancier things exist

Measured and documented in `docs/plots-twopass-campaign.md`:

- Two-pass (membership → chains) v1/v2/v3: best 3.00 (v3-muse). It fixed
  every FORM fault (first-ever zero structural chain errors) but never beat
  the one-pass ceiling.
- Self-critique → revise: falsified in both calibration regimes (Muse
  no-ops via its guard; Ornith degrades 2.73→2.53 while self-scoring 4.0).
- Best-of-5 sampling: 3.33 / 3.33 / 2.93 / 2.87 / 2.47 — 3.33 is the
  reproducible one-pass ceiling; selection only insures against bad draws.
- P1 (genuine causal enablement) never exceeded 3.0 on any arm: the wall
  is composer capability, not process.

## Judging — the one sanctioned instrument

**3-judge GLM-5.3 panel** (`tools/glm_panel_judge.py`, via the Zen shims),
rubric byte-identical to each layer's in-pipeline judge, artifacts
anonymised, scores averaged. Rules, each earned from a measured failure:

1. **Never composer-as-judge.** Ornith scored its own 2.73 layer at 4.6;
   its "self-improvement" loop degraded the artifact while self-scoring a
   flat 4.0. Anonymised, the bias disappears — but Ornith still scores P1
   at 4.33 where GLM sees 2.0–2.33: the judge shares the composer's
   blind spot, which is also why link-verification must be cross-model.
2. **Panel of 3, averaged, never a single call.** Single-draw drift is
   ±0.3; two independent same-instrument panels differed by 0.15–0.25
   (measured test-retest, `docs/plots-twopass-campaign.md`). Do not read
   between-arm gaps under ~0.3.
3. **One instrument, kept fixed.** Absolute scores do NOT transfer across
   judge models (Ornith-panel means run ~+0.8 above GLM's). Rankings did
   transfer in every case we measured — but compare numbers only within
   the same instrument, and give every eval batch a shared control arm.
4. In-pipeline self-judges remain as cheap smoke tests and loop signals
   only; they never decide anything.

## Serving (the environment these defaults assume)

- Ornith-1.5-397B: llama.cpp `llama-server`, port 8110 (+8111 when GPUs
  4–7 are free), 64k ctx — see `docs/00-HANDSHAKE.md`.
- Muse 1.2: Zen API through `tools/zen_shim.py` on ports 8222–8224
  (~27 tok/s/stream, ≤3 useful parallel streams; the shim renders
  `json_schema` into the prompt — always request JSON via schema).
- Qwen3.8-Flash-Next: local vLLM on port 8130 (`tools/serve_qwen38fn.sh`,
  54 tok/s single / 1305 tok/s @32 streams) — throughput roles only
  (drafts, mass checks); measured too weak as a plot composer (2.07).
- GLM-5.3(-Flash) cannot run on this machine (Hopper-only kernels):
  `docs/glm53-panel-report.md` §3.
