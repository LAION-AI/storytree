# Serving and run operations

Everything needed to reproduce the runs, from a clean checkout, on 8 × A100-80GB.

## Serving

**Qwen3.8-27B — eight independent endpoints, one model copy per GPU.**
This is what the swarm and every scene variant were run against.

```bash
./ops/launch_all.sh              # ports 8100-8107, GPU N -> port 810N
./ops/launch_one.sh 3 8103       # a single endpoint on GPU 3
```

Three environment facts the launcher encodes, each of which cost time to find:

| | |
|---|---|
| `LD_LIBRARY_PATH` → NVIDIA forward-compat libs | the venv ships cu130 torch and the driver is CUDA 12.4 |
| venv `bin/` on `PATH` | vLLM JIT-compiles the FlashInfer sampler and needs `ninja` |
| `--speculative-config` with `qwen3_5_mtp` | the checkpoint ships real MTP weights; +138% at 77.5% acceptance |

**GLM-5.2 — one model across all GPUs**, used for the ensemble and the top-down
comparisons. `$SCRATCH` in `serve_glm.sh` is wherever the llama.cpp build lives.

```bash
SCRATCH=/path/to/build ./ops/serve_glm.sh    # port 8099
```

Note `-np 1`: the context window is divided between slots, and concurrency
measurably buys nothing on this architecture, so one slot with the full window
is strictly better. See `docs/06-local-inference.md`.

## Request-body quirks, both models

| | Qwen3.8 | GLM-5.2 |
|---|---|---|
| disable thinking | `chat_template_kwargs: {"enable_thinking": false}` | same, **or** `reasoning_effort: "none"` |
| `reasoning_effort` | only `xhigh\|medium\|low` — anything else makes the template **raise** and the request 400 | everything that is not literally `"high"` maps to *max*, so `"low"` is a silent no-op selecting the most expensive setting |
| output cap | `max_tokens` | `max_tokens`, **not** `max_completion_tokens` — llama.cpp's shim ignores the latter |
| deep JSON schema | enforced | enforced, but `propertyNames` makes vLLM return **HTTP 500 with an empty body** |

`grammar_safe()` in `distill/swarm.py` strips the unsupported keywords; the
schema is still validated in full after the call, so the guarantee moves from
the grammar to the validator rather than disappearing.

## Running the experiments

```bash
# the bottom-up swarm, all eight stages, 224 scenes
python3 distill/swarm.py reconstruct/runs/matrix --out <dir> --per-endpoint 8

# one scene-layer variant against the fixed fifteen-scene sample
python3 distill/scene_variants.py --variant v5 --out <dir>

# mechanical integrity of an event layer, no model involved
python3 tools/check_integrity.py runs/lattice-qwen runs/lattice
```

`--variant` takes `v0` … `v5`. The sample is hard-coded in
`distill/scene_variants.py` so arms stay comparable; changing it invalidates
every comparison in `docs/13`.

Each run writes `_tier1.json` with every mechanical measure, and the swarm writes
`protocol.json` with per-stage timings, token counts and check violations.

## Reproducibility notes

**The sample is fixed and must stay fixed.** Fifteen scenes chosen once, spread
across acts and lengths, never changed. Re-picking it would make new numbers
incomparable with `docs/13` and `docs/14`.

**Scene slicing.** `sp.parse()` returns `(cleaned_text, scenes)` and the offsets
index the **cleaned** text. Slicing the raw file with them misaligns every scene
— this happened, and 13 of 15 scenes were never shown to the model while the
correspondence metric reported success. `_assert_supply()` now verifies the slice
against the scene's own anchor before any call.

**Temperature 0.7, one sample per cell.** Within-condition variance is
unmeasured and may exceed several of the differences reported.

**Screenplay text is never committed.** The reconstruction reads a copyrighted
screenplay to derive structure and stores results by reference. `.gitignore`
matches `**/script.normalized.txt` anywhere in the tree, after a narrower pattern
failed to cover a newly created run directory.
