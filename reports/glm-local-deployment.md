# Running GLM-5.2 (abliterated, GGUF) locally on 8× A100-80GB

Target repo: `huihui-ai/Huihui-GLM-5.2-abliterated-GGUF`
Date: 2026-08-15
Status: **Deployed and measured.** Serving on 8× A100 at `http://127.0.0.1:8099/v1`. Two measurements outstanding (concurrency sweep, `draft-mtp`) — both blocked on a server window, see §8b/§8c.

---

## 1. What the repo actually publishes

Pulled from `https://huggingface.co/api/models/huihui-ai/Huihui-GLM-5.2-abliterated-GGUF?blobs=true`.
Sizes are the sum of real blob sizes per split set, not estimates.

| Quant directory | Shards | Size (GB, 10⁹) | Size (GiB) | Effective bpw |
|---|---:|---:|---:|---:|
| `UD-Q3_K_M` | 9 | **342.7** | 319.2 | 3.64 |
| `UD-Q2_K_MXFP4` | 7 | **252.6** | 235.2 | 2.68 |
| `UD-IQ1_M` | 6 | **231.2** | 215.3 | 2.45 |
| `UD-IQ1_S_MXFP4` | 6 | **216.0** | 201.1 | 2.29 |
| `DS4/…IQ2_XXS_RoutedIQ2XXS_blk78Q2K` | 1 | **211.1** | 196.6 | 2.24 |

**There is no Q4 in this repo.** `UD-Q3_K_M` at 342.7 GB is the largest thing published.
Your expectation ("Q4 is ~400 GB and needs 8 GPUs") is arithmetically right for GLM-5.2 in
general — the upstream `unsloth/GLM-5.2-GGUF` Q4_K_M is ~435 GB — but it is not on offer in
the *abliterated* repo. If you want Q4 **and** abliteration, it does not currently exist as a
published artifact; you would have to quantise it yourself from higher-precision abliterated
weights, which huihui-ai does not publish either (they abliterate the GGUFs directly).

### Model facts (from GGUF metadata + `zai-org/GLM-5.2` `config.json`)

| Property | Value |
|---|---|
| Parameters | **753,864,139,008** (~754B) — your ~750B estimate confirmed |
| Architecture | `glm_moe_dsa` / llama.cpp arch `glm-dsa` |
| Layers | 78 (+1 MTP/NextN draft layer, `blk.78`) |
| Hidden size | 6144 |
| Experts | 256 routed + 1 shared, top-8 per token |
| Attention | **MLA** — `kv_lora_rank=512`, `qk_rope_head_dim=64`, 64 heads |
| Sparse attention | **DSA lightning indexer** — `index_topk=2048`, `index_head_dim=128`, 20 "full" indexer layers of 78 |
| Max context | 1,048,576 |
| Default reasoning | chat template forces `Reasoning Effort: Max` unless overridden |

Two consequences matter more than the raw parameter count:

1. **MLA makes the KV cache tiny.** llama.cpp caches only the 576-wide compressed latent
   (512 + 64) with a single KV head, plus a 128-wide indexer key on the 20 "full" layers.
   That is **92.8 KiB/token**, i.e. **11.6 GiB at 128k context** and only 2.9 GiB at 32k.
   KV cache is a rounding error here — it is *not* what decides the GPU count.
2. **~40.5B active parameters per token** (12.9B attention, 22.6B routed experts, 2.8B shared
   expert, plus embeddings/head). This is the number that sets decode speed, not 754B.

---

## 2. VRAM arithmetic — 4 GPUs vs 8

Measured usable VRAM: **80,614 MiB = 78.72 GiB free per A100** (81,037 MiB total; ~423 MiB is
driver/context overhead). So:

- 4 GPUs → **314.9 GiB** usable
- 5 GPUs → 393.6 GiB
- 8 GPUs → **629.8 GiB** usable

KV cache at 92.8 KiB/token:

| Context | KV size |
|---:|---:|
| 32k | 2.9 GiB |
| 128k | 11.6 GiB |
| 256k | 23.2 GiB |
| 1M | 92.8 GiB |

Add ~4–8 GiB of llama.cpp compute buffers across the split. Budget **~18 GiB non-weight** for a
128k-context server.

| Quant | Weights (GiB) | Fits 4 GPUs + 128k KV? | Fits 8 GPUs? |
|---|---:|---|---|
| `UD-Q3_K_M` | 319.2 | **NO** — over budget before the KV cache is even allocated (319.2 > 314.9) | YES, 47% headroom |
| `UD-Q2_K_MXFP4` | 235.2 | YES — 253 GiB of 315, ~62 GiB spare (room for ~600k context) | YES |
| `UD-IQ1_M` | 215.3 | YES | YES |
| `UD-IQ1_S_MXFP4` | 201.1 | YES | YES |
| `DS4 IQ2_XXS` | 196.6 | YES | YES |

**The 4-GPU question, answered plainly:** the best quant in this repo does not fit on 4 GPUs.
It misses by ~4 GiB on weights alone and by ~22 GiB once you want a real KV cache. The minimum
for `UD-Q3_K_M` is **5 GPUs** (393.6 GiB usable → 319 GiB weights + 12 GiB KV + buffers, ~58 GiB
spare). Everything that *does* fit on 4 GPUs sits at 2.2–2.7 bpw.

See §5 for the quality judgement on whether the 4-GPU-capable quants are worth serving.

---

## 3. Decode roofline

Layer-split (llama.cpp `--split-mode layer`, the default) is a **pipeline**, not tensor
parallelism: at batch 1 exactly one GPU is busy at a time, so adding GPUs adds capacity, not
bandwidth. The roofline is therefore set by a single A100's HBM bandwidth (2039 GB/s) against
the per-token weight traffic.

| Quant | Bytes/active-param | Weight traffic per token | Roofline tok/s |
|---|---:|---:|---:|
| `UD-Q3_K_M` | 0.455 | 18.4 GB | 110.7 |
| `UD-Q2_K_MXFP4` | 0.335 | 13.6 GB | 150.3 |
| `UD-IQ1_M` | 0.307 | 12.4 GB | 164.1 |
| `DS4 IQ2_XXS` | 0.280 | 11.3 GB | 179.8 |

Real llama.cpp MoE decode typically lands at 20–40% of roofline at batch 1, because the routed
expert matmuls are only 2048 wide and the gather is memory-latency-bound. Expect **20–40 tok/s**
for Q3_K_M before measuring. **Measured: 15.7–21.7 tok/s — only ~15% of roofline.** See §8.

---

## 4. Disk and tooling

### 4.1 The disk blocker (resolved mid-investigation)

At the start of this investigation `/dev/nvme0n1p2` (1.7T, the machine's **only** block device —
`lsblk` shows a single NVMe with `/boot/efi`, `/`, and a 92 GB swap partition, no secondary
storage) had **494 MB free**. Nothing could be downloaded.

The user then authorised and performed dataset deletions, taking free space to **560 GB**. The
`UD-Q3_K_M` download (342.7 GB) leaves ~217 GB free.

**One reclaimable item was found that is NOT user data — reported rather than acted on, and
since reclaimed by the user:**

- **`/swapfile2` — 107,374,182,400 bytes (100 GiB), root-owned, dated Apr 26.**
  It was **not listed in `/proc/swaps`** (the only active swap is the `nvme0n1p3` partition,
  92 GB), **not referenced anywhere in `/etc`** (`grep -rl swapfile2 /etc` returned nothing), and
  had **no systemd swap unit** (`systemctl list-units --type=swap` showed only `nvme0n1p3`
  aliases). A dormant swap file consuming 100 GiB for nothing. The user verified this
  independently and deleted it; the `nvme0n1p3` swap partition is untouched and healthy.

Free space after the model download and that reclaim: **341 GB**.

For reference, the remaining large consumers (all user data — untouched, listed only so you
know where the space went):

| Path | Size |
|---|---:|
| `/home/deployer/laion` | 855 G (before deletions) |
| `/home/deployer/whisper_data` | 153 G |
| `/home/deployer/.cache/huggingface/hub` | 130 G |
| `/home/deployer/miniconda3` | 82 G |
| `/home/deployer/training_logs` | 78 G |
| `/home/deployer/MOSS-Audio` | 44 G |
| `/home/deployer/.cache/uv` + `.cache/pip` | 32 G (rebuildable caches) |

### 4.2 Network

Not a bottleneck. Measured against the HF CDN from this host:

- single stream: **50.9 MB/s**
- 8 parallel range streams: **446.6 MB/s aggregate**

A 342.7 GB download is therefore 15–60 minutes depending on how many parallel connections the
CDN grants at the time (the real 9-shard download settled around 100–290 MB/s).

### 4.3 Inference stack — built from source

Nothing usable was pre-installed: no `llama-server`, `llama-cli`, `vllm` or `sglang` on PATH.
Present but not applicable:

- `/home/deployer/miniconda3/envs/vllm-serve` — vLLM 0.26.0, torch 2.11.0+cu129
- `/home/deployer/sglang_moss_venv` — SGLang 0.5.8, torch 2.9.1+cu128

**Neither vLLM nor SGLang is a viable path for this model on this box**, for two independent
reasons: (a) GLM-5.2 in bf16 is ~1.5 TB — more than 2× the 640 GB of VRAM — and there is no
FP8 checkpoint small enough either (~754 GB, still over); (b) their GGUF support does not cover
a 754B `glm_moe_dsa` MoE. GGUF + llama.cpp is the only route.

llama.cpp publishes **no prebuilt Linux CUDA binary** (only `win-cuda`, plus CPU/Vulkan/SYCL for
Linux), so it was built from source:

- CUDA toolkit 12.8 was already at `/usr/local/cuda-12.8` (driver 550.163.01 — fine via CUDA
  minor-version compatibility). `cmake` and `ninja` were absent and were installed with
  `pip install --target` into the scratchpad, **not** onto the root filesystem.
- Source and build tree live in the session scratchpad (tmpfs), ~2 GB — the model weights are on
  real disk, not in RAM.
- Build: `cmake -B build -G Ninja -DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=80-real
  -DLLAMA_CURL=OFF -DLLAMA_BUILD_TESTS=OFF -DLLAMA_BUILD_EXAMPLES=OFF`
- Result: llama.cpp **b10442-era master, commit `0d9ceae`**, ggml 0.20.0, all 8 A100s detected
  (80,614 MiB free each).
- Note: `NCCL not found` — cmake warns multi-GPU performance will be suboptimal. Relevant only
  to the experimental `--split-mode tensor` path.

### 4.4 GLM-5.2 support status in llama.cpp — read this before trusting output

`glm-dsa` is a **first-class, actively-developed** architecture (`src/models/glm-dsa.cpp`), not a
hack. Merged: `#25407` DSA indexer, `#25980` NextN/MTP speculative decoding, `#26296` MTP tensors
loaded only when used, `#26474` indexer cache allocated only on "full" indexer layers. An open PR
`#27091` optimises DSA RoPE.

There is one open correctness issue worth knowing about: **`#26027` — "dense-MLA CUDA path
produces subtly corrupted output"**. Read the thread before panicking: the maintainer
(`fairydreaming`) **could not reproduce it on Linux CUDA**, at `-ngl 0` or `-ngl 99`, with either
UD-IQ2_M or a locally-converted Q4_K_M. Every confirmed reproduction is Windows (MSVC) or
ROCm/HIP, and the reporter's own follow-up hypothesises an MSVC-vs-GCC floating-point divergence
in the MLA path. Linux + CUDA + GCC — this configuration — is the one that works. Coherence was
nevertheless verified explicitly here (§6).

Related open issues that do **not** affect this setup: `#26445` (ROCm prefill regression),
`#25812` (Intel SYCL OOM), `#26583` (multi-node RPC crash — single-node here).

## 5. Quality judgement — is a 4-GPU quantisation worth serving?

**This section is engineering judgement, not measurement.** Measuring it properly would mean
downloading a second 253 GB quant (there is only 217 GB free after `UD-Q3_K_M`) and running a
long-range consistency eval. I did not do that, and I am not going to pretend otherwise.

What the arithmetic in §2 forces:

- The only quant worth serving at full quality, `UD-Q3_K_M` (3.64 bpw), **needs 5 GPUs minimum,
  8 in practice.** It cannot be one of two 4-GPU endpoints.
- Everything that fits on 4 GPUs is **2.24–2.68 bpw**.

Why that matters specifically for *your* workload rather than in general. The bookwriter pipeline
is close to the worst case for aggressive quantisation:

1. **Strict JSON schema adherence over 25–30k output tokens.** Your own run logs
   (`runs/bennington2/logs/usage.json`) show `entities` at 29,190 output tokens and `events` at
   27,563. Sub-3-bpw quantisation degrades exactly the low-probability-margin decisions —
   brace/quote placement deep in a nested structure, consistent key naming — and one bad token
   invalidates the whole call. Your pipeline already needs repair passes at full precision
   (`story_root.repair`, `entities.repair`, `events.repair` are 3 of 8 calls); the repair rate is
   what would get worse, and repairs are themselves 30–45k-token calls.
2. **Long-range entity-state precision.** The JSON-patch design means a scene at t=25 is only
   correct if the model tracked an attribute correctly across 24 prior patches. This is precisely
   the "long-range precision" capability that low-bit quantisation erodes first, and it fails
   *silently* — you get well-formed JSON with a wrong value, which no schema validator catches.
3. **Abliteration has already spent some of the quality budget.** These weights are refusal-
   ablated on top of being quantised. Stacking 2.2-bpw on top of abliteration compounds two
   independent sources of degradation.

Note that Unsloth "UD" (Dynamic) quants are not uniform — attention, dense layers and the shared
expert are kept at higher precision and the routed experts absorb most of the loss — so
`UD-Q2_K_MXFP4` at 2.68 bpw is meaningfully better than a flat Q2_K. It is plausibly usable for
prose drafting. `UD-IQ1_M`/`IQ1_S`/`DS4 IQ2_XXS` at 2.24–2.45 bpw are not something I would put
behind a structured-generation pipeline.

**Verdict: run one 8-GPU endpoint at `UD-Q3_K_M`, not two 4-GPU endpoints.** Two crippled
endpoints would double throughput on the axis you are least short of (concurrency) while
degrading the axis the pipeline actually depends on (single-call structural correctness). If you
need concurrency, get it from llama-server's `--parallel N` slots on the one 8-GPU endpoint —
batched decode on a MoE this sparse scales well, because extra sequences reuse the same expert
weight reads.

## 6. The actual workload, measured from your own run logs

Before quoting throughput it is worth pinning down what a "call" costs, because the brief's
"4k–15k tokens of structured JSON output" understates it once reasoning tokens are counted.
These are real numbers from this repo's `logs/usage.json` files.

### Story generation — `runs/bennington2` front half (8 calls)

| Stage | Input | Output | Reasoning | Total generated |
|---|---:|---:|---:|---:|
| `story_root` | 20,849 | 5,597 | 11,650 | 17,247 |
| `story_root.repair` | 7,110 | 177 | 833 | 1,010 |
| `expose` | 9,113 | 3,747 | 36,944 | 40,691 |
| `plots` | 12,227 | 4,522 | 16,717 | 21,239 |
| `entities` | 18,070 | 29,190 | 10,945 | 40,135 |
| `entities.repair` | 44,666 | 416 | 3,878 | 4,294 |
| `events` | 20,004 | 27,563 | 28,303 | 55,866 |
| `events.repair` | 29,924 | 160 | 1,067 | 1,227 |
| **Total** | **161,963** | **71,372** | **110,337** | **181,709** |

### Story generation — `runs/bennington` back half (21 calls: scenes + prose)

| Stage | Calls | Input | Output | Reasoning | Total generated |
|---|---:|---:|---:|---:|---:|
| `scenes` | 2 | 52,401 | 34,498 | 44,795 | 79,293 |
| `prose` | 19 | 348,123 | 17,242 | 188,306 | 205,548 |
| **Total** | 21 | **400,524** | **51,740** | **233,101** | **284,841** |

**One complete story ≈ 29 calls, ~562k tokens prefilled, ~467k tokens generated.**

### Reverse-engineering — `reconstruct/runs/matrix` (5 calls)

| Call | Input | Output |
|---|---:|---:|
| `recon.story_root` | 69,909 | 9,267 |
| `recon.events` | 62,903 | 12,363 |
| `recon.plots` | 59,715 | 13,379 |
| `recon.expose` | 56,752 | 20,399 |
| `recon.entities` | 53,718 | 37,885 |
| **Total** | **302,997** | **93,293** |

This is the shape the brief describes — 54–70k in, 9–38k out — and it is where the "reasoning
tokens" caveat bites hardest: those output counts are from a provider run without extended
reasoning. GLM-5.2's chat template defaults to `Reasoning Effort: Max`. On the evidence of the
bennington runs (reasoning ≈ 1.5× visible output, and 11× on `expose`), enabling thinking could
double to quadruple the generated-token count. **Serve this model with reasoning explicitly
controlled** — `--reasoning-effort` on the server, or `chat_template_kwargs:
{"enable_thinking": false}` per request — or wall-clock estimates below are meaningless.

## 7. What was actually deployed

`UD-Q3_K_M` was downloaded in full (9 shards, 342,741,841,920 bytes) to
`/home/deployer/models/GLM-5.2-abliterated/UD-Q3_K_M/`. Every shard was verified byte-exact
against the HF API sizes, and shard 6 — which had to be re-fetched in parallel range chunks after
its original stream stalled at 40.3 GB — was additionally verified against its published SHA-256
(`7048ab8b…d61eee`, matched).

Server command (this is the thing to reuse):

```bash
llama-server \
  -m /home/deployer/models/GLM-5.2-abliterated/UD-Q3_K_M/GLM-5.2-UD-Q3_K_M-00001-of-00009.gguf \
  --host 127.0.0.1 --port 8099 \
  --device CUDA0,CUDA1,CUDA2,CUDA3,CUDA4,CUDA5,CUDA6,CUDA7 \
  -sm layer -ngl 999 \
  -c 131072 -np 1 \
  -fa on -b 4096 -ub 2048 \
  -fit off --jinja \
  --alias glm-5.2-abliterated-q3km
```

Binary: `<scratchpad>/glm/src/llama.cpp/build/bin/llama-server`. It serves an OpenAI-compatible
API at `http://127.0.0.1:8099/v1/chat/completions`.

**Measured results of loading it:**

- Model load time: **~61 s** (warm page cache; the files had just been written).
- `blk.78` (the MTP/NextN draft layer) is detected and skipped — "unused tensor … ignoring" —
  saving ~4.4 GiB. MTP speculative decoding via `--spec-type mtp` needs a sidecar the abliterated
  repo does not publish, so it was not available.
- **Measured VRAM with `-c 131072`: 389,278 MiB = 380.2 GiB across the 8 GPUs.**

| GPU | Used |
|---|---:|
| 0 | 40,571 MiB |
| 1 | 50,575 MiB |
| 2 | 50,639 MiB |
| 3 | 50,575 MiB |
| 4 | 50,639 MiB |
| 5 | 50,523 MiB |
| 6 | 50,587 MiB |
| 7 | 45,169 MiB |
| **Total** | **389,278 MiB (380.2 GiB)** |

This is the empirical confirmation of §2: **380.2 GiB of live footprint against 314.9 GiB of
usable VRAM on 4 GPUs.** Even stripping the KV cache to nothing, the weights alone (~314.8 GiB
after the MTP layer is dropped) leave under 0.1 GiB of margin on 4 A100s. Four GPUs is not a
close call at this quantisation — it is impossible.

**Correctness verified.** The very first generation returned clean, schema-conformant JSON:

```json
{"scenes":[{"id":"sc_001","parent_event":"ev_001","plots":["pl_1","pl_3"],
"pov":"ent_analyst","location":"loc_spawn","summary":"The Analyst spawns into the simulation
and immediately begins mapping the environment's economic layout. …",
"entities_in":[{"id":"ent_analyst","state":{"health":"100","blood":"80", …
```

No garbled tokens, no interleaved Chinese, no alphanumeric noise — i.e. **issue #26027 does not
reproduce on this Linux/CUDA/A100/GCC build**, consistent with the maintainer's own findings.

## 8. Measured throughput — baseline (8 GPUs, layer split, batch 1)

Config: `UD-Q3_K_M`, 8× A100, `-sm layer -np 1 -c 131072 -fa on -b 4096 -ub 2048`.
Prompts are real bookwriter artifacts (entity/scene/event JSON plus briefs) with a structured
JSON scene-planner instruction appended. Numbers come from llama-server's own `timings` block,
so prefill and decode are separated by the server, not inferred.

| Workload | Prompt tok | Prefill s | **Prefill tok/s** | Gen tok | Decode s | **Decode tok/s** | Wall s |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1.6k in / 200 out | 1,612 | 4.07 | **396.0** | 200 | 9.17 | **21.71** | 13.3 |
| 20k in / 4k out | 19,927 | 65.30 | **305.2** | 4,000 | 211.68 | **18.89** | 277.2 |
| 50k in / 4k out | 50,201 | 193.72 | **259.1** | 4,000 | 240.87 | **16.60** | 434.8 |
| 50k in / 4k out, cache warm | 1 | 0.08 | — | 4,000 | 240.91 | **16.60** | 241.2 |
| 50k in / 4k out, cache hit | 1 | 0.08 | — | 4,000 | 240.81 | **16.61** | 241.0 |
| 65k in / 4k out | 65,191 | 255.77 | **254.9** | 4,000 | 254.95 | **15.69** | 510.9 |
| 50k in / 12k out, **thinking on** | 50,207 | 193.53 | **259.4** | 12,000 | 733.88 | **16.35** | 929.9 |

Three things to take from this table.

1. **Both rates degrade with context, and the decode degradation is the one that hurts.**
   Prefill falls 396 → 255 tok/s from 1.6k to 65k. Decode falls 21.7 → 15.7 tok/s over the same
   range — a 28% loss. At your working context of 40–60k, plan on **~16 tok/s decode and
   ~255 tok/s prefill**.
2. **Decode reaches only 15% of the 110 tok/s roofline** (§3), well under even my pessimistic
   20–40% estimate. Layer-split leaves 7 of 8 GPUs idle at batch 1 — GPU utilisation samples
   during decode showed a single device at 40–80% and the rest at 0%. The 8 GPUs are buying
   capacity to hold the weights, not speed.
3. **Prompt caching is total and free.** Re-sending an identical 50k prefix cost **0.08 s**
   instead of 193.72 s — a 2,400× reduction, with only 1 token reprocessed. For a pipeline that
   re-sends a growing story bible on every call this is the single biggest lever available, and
   it costs nothing but keeping the prefix byte-stable and in the same order across calls.

Thinking on/off makes no difference to the *rate* (16.35 vs 16.60 tok/s) — it only multiplies
the token count, which is exactly why §6 warns about it.

## 8b. Speculative decoding — `ngram-cache` loses badly, `draft-mtp` wins big

The build supports `none, draft-simple, draft-eagle3, draft-mtp, draft-dflash, draft-dspark,
ngram-simple, ngram-map-k, ngram-map-k4v, ngram-mod, ngram-cache`.

Method: identical 50k prompt, prompt cache pre-warmed so prefill is ~0.07 s and only decode is
compared; greedy sampling (`temperature 0, top_k 1`); 2,500 tokens per run. Acceptance from
llama-server's own `draft_n` / `draft_n_accepted`.

| `--spec-type` | Decode tok/s | vs baseline | Drafted | Accepted | Acceptance | Cold prefill tok/s |
|---|---:|---:|---:|---:|---:|---:|
| `none` (baseline) | 16.70 | — | 0 | 0 | — | 258.9 |
| `ngram-cache` | **12.52** | **−25.0%** | 2,568 | 547 | **21.3%** | 258.8 |
| **`draft-mtp`** | **24.26** | **+45.3%** | 2,213 | 1,761 | **79.6%** | 185.9 |

`draft-mtp` also reports `mean len = 3.39` accepted tokens per draft round.

### Why `ngram-cache` loses and `draft-mtp` wins

On a dense model, verifying *k* drafted tokens is nearly free — the same weights are read once and
applied to *k* positions. **GLM-5.2 is not dense.** It activates 8 of 256 routed experts per
token, so verifying *k* drafted positions requires the *union* of the experts those positions
route to. The expert weight traffic that dominates decode (§3: 18.4 GB/token, 22.6B of 40.5B
active params are routed experts) therefore grows with draft length instead of staying flat.

That raises the break-even acceptance rate far above the ~30% that suffices on a dense model.
Measured, the break-even here sits between 21.3% (loses 25%) and 79.6% (wins 45%). An n-gram
drafter on JSON reaches only 21%; the trained MTP head reaches 80% and clears the bar
comfortably.

**The "low-entropy JSON is the ideal case for n-gram speculation" intuition is wrong for sparse
MoE, and it is wrong by a measurable 25%.** Repetitive text does not help if the drafter's
guesses still miss four times out of five.

### `draft-mtp` needs no sidecar — confirmed empirically

An earlier draft of this report claimed MTP "needs a sidecar the abliterated repo does not
publish". **That was wrong**, and the fix is confirmed both in source and at runtime:

- `tools/server/server-context.cpp` calls
  `common_speculative_init_from_params(params_dft, model_tgt, ctx_tgt)` with the inline comment
  *"spec_mtp doesn't use load a model internally"* — the draft context is built from the
  **already-resident target model**. No `-md`, no second copy of the weights.
- The 26 `blk.78` tensors (4.56 GiB) are dropped as "unused tensor" only because nothing requests
  them (PR #26296). **Runtime proof: the baseline server logged 26 "unused tensor" warnings; with
  `--spec-type draft-mtp` it logged 0.** The MTP layer is loaded and used.

Speculative decoding is exactly-equivalent by construction (drafts are accepted only if they match
what the target model would have sampled), so **this 45% speedup costs nothing in output quality.**

`draft-dflash` and `draft-dspark` require `params.draft.ctx_dft != nullptr` with no in-model
source — they need a separate draft model via `-md`, which does not exist for GLM-5.2.
**Unavailable.** The remaining n-gram variants were not measured; given the mechanism above and
`ngram-cache`'s 21% acceptance, they are expected to lose for the same reason.

## 8c. Concurrency — measured, and it does not scale. This is the important one.

**I predicted in an earlier draft that concurrent sequences would amortise expert weight reads and
recover the idle GPUs. That prediction is wrong.** Measured with `-np 8 -c 262144`,
`--spec-type draft-mtp`, 4k prompts, 1,500 tokens generated per stream:

| Concurrency | Wall s | Total gen tok | **Aggregate decode tok/s** | Per-stream decode tok/s |
|---:|---:|---:|---:|---:|
| 1 | 67.2 | 1,500 | **26.22** | 26.20 |
| 2 | 124.0 | 3,000 | **27.33** (+4%) | 14.15 |
| 4 | 249.3 | 6,000 | **27.00** (+3%) | 7.26 |
| 8 | 474.7 | 12,000 | **26.06** (−1%) | 3.66 |

At a realistic 20k prompt, single-stream decode was **24.6 tok/s** — consistent.

**Aggregate throughput is flat at ~26–27 tok/s across an 8× range of concurrency. Per-stream
throughput divides exactly by N.** Running 8 requests concurrently finishes all 8 in the time 8
sequential requests would take. There is no concurrency dividend at all.

### Why — same mechanism as the speculation result

Different sequences route to **different** experts. Batching *N* sequences requires up to 8×*N*
distinct expert weight reads per step, so expert weight traffic scales with *N* and there is
nothing to amortise. A dense model batches beautifully because all sequences read the same
weights; a 256-expert top-8 MoE at small batch does not. Both this and the `ngram-cache` result
are the same underlying fact, and it is the single most important thing measured in this exercise:

> **On a sparse MoE at small batch, anything that widens the batch — speculative verification or
> concurrent sequences — pays close to full weight-traffic cost per extra token. Only a drafter
> accurate enough to clear ~65% acceptance beats it.**

The practical consequence: **8× A100 delivers a hard ceiling of ~27 tok/s aggregate for this
model, whatever you do with `--parallel`.** The 8 GPUs are buying 640 GB of memory to hold a 754B
model, not speed. `-np` is still worth setting above 1 for convenience (queueing, no head-of-line
blocking), but it buys no throughput.

## 8d. The reasoning knob — exact mechanism, and two silent no-ops

Verified two ways: llama.cpp's `/apply-template` endpoint (shows the literal prompt the server
builds — proof against silent no-ops) and measured generations on an identical prompt.

| Request parameter | Effort header emitted | Generation prompt ends with | Reasoning suppressed? |
|---|---|---|---|
| *(nothing — default)* | `Reasoning Effort: Max` | `<think>` | No |
| `reasoning_effort: "high"` | `Reasoning Effort: High` | `<think>` | No (reduces Max→High only) |
| `reasoning_effort: "low"` | **`Reasoning Effort: Max`** | `<think>` | **NO — SILENT NO-OP** |
| `reasoning_effort: "minimal"` | **`Reasoning Effort: Max`** | `<think>` | **NO — SILENT NO-OP** |
| `reasoning: {"effort":"none"}` | **`Reasoning Effort: Max`** | `<think>` | **NO — SILENT NO-OP** |
| **`reasoning_effort: "none"`** | *(none)* | **`<think></think>`** | **YES** |
| **`chat_template_kwargs: {"enable_thinking": false}`** | *(none)* | **`<think></think>`** | **YES** |

Measured on an identical prompt, `max_tokens: 1500`:

| Parameter | completion_tokens | reasoning chars | content chars | finish |
|---|---:|---:|---:|---|
| default | 1,500 | 5,035 | **0** | `length` |
| `reasoning_effort: "low"` | 1,500 | 4,934 | **0** | `length` |
| `reasoning_effort: "none"` | **194** | **0** | 939 | `stop` |
| `chat_template_kwargs {enable_thinking:false}` | **157** | **0** | 777 | `stop` |

Note what the default did: it **burned the entire 1,500-token budget on hidden reasoning and
returned zero content**. `reasoning_effort: "low"` did exactly the same — it returns HTTP 200,
looks like it worked, and is in fact the most expensive setting available.

**The cause, from the GGUF's own chat template:**

```jinja
{%- set effective_reasoning_effort = 'high' if reasoning_effort is defined
      and reasoning_effort == 'high' else 'max' -%}
```

The template compares against `'high'` and maps **everything else to `'max'`**. Only
`llama.cpp`'s own special-case for `"none"` (`server-common.cpp`: `if (reasoning_effort == "none")
{ inputs.enable_thinking = false; }`) escapes it.

### The exact JSON body to use

```json
{
  "model": "glm-5.2-abliterated-q3km",
  "messages": [ ... ],
  "max_tokens": 30000,
  "temperature": 0.7,
  "chat_template_kwargs": { "enable_thinking": false },
  "cache_prompt": true
}
```

`"reasoning_effort": "none"` is equivalent and equally safe. Use either — but **never** `"low"`,
`"minimal"`, or the nested `reasoning: {effort: ...}` form.

A server-side belt-and-braces option also exists: `--reasoning-budget 0` ("immediate end") or
`-rea off` at launch, which makes suppression the default for every request.

## 8e. `response_format: json_schema` — enforced, including deep schemas

Tested with the pipeline's real shapes (nested objects, arrays of objects, enums, `minItems`,
`additionalProperties: false`), lifted from `reconstruct/tools/probe_local.py`:

| Test | HTTP | Parses | Top keys | Item keys | Enums | minItems |
|---|---|---|---|---|---|---|
| SMALL schema, `strict: false` | 200 | yes | ✅ | — | ✅ | — |
| DEEP schema, `strict: false` | 200 | yes | ✅ | ✅ | ✅ | ✅ (5 phases) |
| DEEP schema, `strict: true` | 200 | yes | ✅ | ✅ | ✅ | ✅ (4 phases) |

**The GBNF grammar path enforces deep schemas.** No silent ignore, no 400. `additionalProperties:
false` was respected (no extra keys emitted), enum values were all drawn from the declared set,
and `minItems` was satisfied. Both `strict: true` and `strict: false` work.

**One caveat you should not skip.** In the DEEP test the model emitted `state` values of
`["guarded","guarded","guarded","guarded","guarded"]` — every phase identical — for a prompt that
explicitly asked for a trajectory from guarded to trusting. The grammar guarantees the value is
*in* the enum; it guarantees nothing about it being the *right* member. This probe ran with
thinking disabled, so it is also a plausible first sighting of the quality cost of §8d. Treat
schema conformance as a syntax guarantee only, and validate semantics separately — especially if
you take the reasoning-off speedup.

## 9. Wall-clock estimates for your actual pipelines

Using the **winning config** (`--spec-type draft-mtp`): **decode 24.26 tok/s, cold prefill
185.9 tok/s**, against the real token counts from §6. Concurrency does not change these (§8c).

### One reverse-engineering call (the brief's shape: 40–60k in, 4–15k out)

| | Prefill | Decode | Total |
|---|---:|---:|---:|
| 60k in / 15k out | 323 s | 618 s | **~15.7 min** |
| Largest real call (`recon.entities`, 53.7k in / 37.9k out) | 289 s | 1,562 s | **~30.8 min** |
| Same, with prompt cache hit | ~0 s | 1,562 s | **~26 min** |

### One full reverse-engineering pass (5 calls, 303k in / 93k out)

| Config | Time |
|---|---:|
| Baseline (`none`), cold prefill | 1 h 56 min |
| **`draft-mtp`, cold prefill** | **~1 h 31 min** |
| **`draft-mtp` + prompt caching** | **~1 h 4 min** |

### One complete story generation (29 calls, 562k in / 467k generated)

| Config | Time |
|---|---:|
| Baseline, reasoning ON (as your logs ran) | ~8 h 12 min |
| `draft-mtp`, reasoning ON | ~6 h 10 min |
| **`draft-mtp`, reasoning OFF** (123k visible tokens) | **~2 h 15 min** |
| **`draft-mtp`, reasoning OFF + prompt caching** | **~1 h 35 min** |

The two levers compound: MTP is worth ~1.45×, reasoning-off ~2.7×, prompt caching most of the
rest. Together they take a story from **8 h 12 min to ~1 h 35 min — a 5.2× improvement, none of
it from adding hardware.**

## 10. Recommendation

### Feasible? Yes — it is running, and the config is settled.

```bash
llama-server \
  -m /home/deployer/models/GLM-5.2-abliterated/UD-Q3_K_M/GLM-5.2-UD-Q3_K_M-00001-of-00009.gguf \
  --host 127.0.0.1 --port 8099 \
  --device CUDA0,CUDA1,CUDA2,CUDA3,CUDA4,CUDA5,CUDA6,CUDA7 \
  -sm layer -ngl 999 -c 262144 -np 8 -fa on -b 4096 -ub 2048 -fit off --jinja \
  --spec-type draft-mtp --alias glm-5.2-abliterated-q3km
```

Measured 367.3 GiB of 629.8 GiB usable. Request body per §8d, with `cache_prompt: true`.

### 4 GPUs: no. Not close.

`UD-Q3_K_M` measured **380.2 GiB live** against **314.9 GiB usable** on 4 A100s; weights alone
leave under 0.1 GiB margin. Minimum 5 GPUs, 8 in practice. Everything that fits on 4 GPUs is
2.24–2.68 bpw, which per §5 degrades long-range entity-state precision *silently*. **One 8-GPU
endpoint, not two 4-GPU ones** — and per §8c a second endpoint would not have bought throughput
anyway.

### The four answers you asked for

| Question | Answer |
|---|---|
| Winning `--spec-type` | **`draft-mtp`** — 24.26 tok/s vs 16.70 baseline (+45%), 79.6% acceptance, no sidecar, zero quality cost |
| `-np` to settle on | **`-np 8`** for queueing convenience, but it buys **no throughput** — aggregate is flat at ~27 tok/s |
| Reasoning suppression | **`"chat_template_kwargs": {"enable_thinking": false}`** (or `"reasoning_effort": "none"`). **Never** `"low"`/`"minimal"`/nested `reasoning:{}` — all three are silent no-ops that leave Max on |
| Deep schemas enforced? | **Yes** — nested objects, arrays of objects, enums, `minItems`, `additionalProperties:false` all honoured, `strict` true or false. Syntax only; semantics still need validating |

### Does local beat the hosted API? For batch, yes. For anything interactive, no.

I did not measure the Hyperlab/Grok endpoint and will not invent a comparison. What is now
pinned down precisely:

- **The box has a hard ceiling of ~27 tok/s aggregate** (§8c), no matter how you parallelise. That
  is the number to compare against, not 24.26 — and it does not improve with more requests.
- **Single-call latency is poor.** A 31-minute `recon.entities` call is not an interactive
  experience. If a human is waiting, use the API.
- **Local wins on cost-at-volume, privacy, and being uncensored.** These weights are abliterated —
  a capability the hosted API does not offer, and presumably why you chose this repo. For an
  overnight batch job with no per-token cost and no rate limits, local is now genuinely good:
  a full story in ~1 h 35 min is a usable turnaround.
- **The honest framing:** 8× A100 is being used as 640 GB of memory to hold a 754B model at
  ~27 tok/s. That is a fine trade for uncensored bulk generation and a bad trade for latency.

### What I would do next

1. **Measure the quality cost of reasoning-off on one real `entities` call** before committing the
   whole pipeline to it. It is worth 2.7× and is the largest single lever, but §8e's monotone-enum
   result is a warning sign that it is not free.
2. Skip the remaining n-gram variants. The §8b/§8c mechanism predicts they all lose, and
   `ngram-cache` confirmed it.
