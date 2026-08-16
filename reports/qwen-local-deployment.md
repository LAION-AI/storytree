# Running Qwen3.8-27B-Uncensored-FP8 locally as 8 independent endpoints on 8× A100-80GB

Target repo: `orcarouter/Qwen3.8-27B-Uncensored-FP8`
Date: 2026-08-16
Status: **Deployed and measured.** Eight independent OpenAI-compatible endpoints serving on
`http://127.0.0.1:8100/v1` … `http://127.0.0.1:8107/v1`, one full model copy per GPU.
All measurements in this report come from runs performed on this box today.

**Headline:** 2,812.6 tok/s aggregate across the 8 endpoints on the real bookwriter payload
(deep JSON schema, 64 concurrent). GLM-5.2 on the same hardware delivered 27 tok/s aggregate.
That is a **104× improvement**, and it comes from three independent facts: the model is dense,
it fits on one card, and its attention is 75% linear.

---

## 1. What the repo actually publishes

Pulled from the HF API for `orcarouter/Qwen3.8-27B-Uncensored-FP8`.

| Property | Value |
|---|---|
| Architecture | `Qwen3_5ForConditionalGeneration` (`model_type: qwen3_5`) |
| Base model | `Qwen/Qwen3.8-27B`, abliterated/uncensored, Apache-2.0 |
| Shards | 7 safetensors, **30.87 GB** (10⁹) / 29 GiB on disk, 1,606 tensors |
| Layers | **64** — 48 `linear_attention` + 16 `full_attention`, strict 3:1 pattern (`full_attention_interval: 4`) |
| Hidden / intermediate | 5120 / 17408 |
| Full attention | 24 query heads, **4 KV heads**, `head_dim: 256`, `partial_rotary_factor: 0.25` |
| Linear attention | Gated DeltaNet — 16 key heads, 48 value heads, head dim 128, conv kernel 4, SSM state in fp32 |
| Vocab | 248,320 |
| Max context | **262,144** |
| Multimodal | Yes — vision tower (27 layers, hidden 1152, patch 16) + video, interleaved mRoPE |
| MTP | **`mtp_num_hidden_layers: 1`, and the weights are actually in the checkpoint** |
| Quantisation | FP8 `e4m3`, **block-wise** (`weight_scale_inv`), dynamic activation scheme; visual blocks 0–6 excluded |

### 1.1 Dense or MoE? — Dense. This single fact drives most of the report.

I checked the weight map directly rather than trusting the tag list: every one of the 1,606
tensors resolves to `model.language_model.layers.N.{linear_attn,self_attn,mlp}.*`,
`model.visual.*`, `mtp.*`, `lm_head` or `embed_tokens`. There is **no `experts`, no `gate`, no
router tensor anywhere.** The MLP is a plain `gate_proj`/`up_proj`/`down_proj` triple.

GLM-5.2 was a 256-expert top-8 MoE, and *every* negative result in the GLM report traced back to
that: n-gram speculation lost 25%, and concurrency was flat at 1.0× scaling, both because extra
tokens in a batch pull extra expert weights. **On a dense model neither mechanism exists.** The
same weights are read once and applied to every token in the batch, so widening the batch —
whether by speculative verification or by concurrent sequences — is close to free until the GPU
becomes compute-bound. Sections 7 and 8 confirm this held.

### 1.2 The hybrid attention matters almost as much

Only 16 of 64 layers keep a KV cache. Per token:

`16 layers × 4 KV heads × 256 head_dim × 2 (K,V) × 2 bytes = 64 KiB/token`

The other 48 layers carry a **fixed-size** recurrent state per *sequence* (not per token), so
their cost does not grow with context at all. The practical consequences show up twice in the
measurements: a **549,184-token KV cache** on a single 80 GB card (§4), and decode that falls
only 11% from 2.9k to 70k context where GLM lost 28% (§6).

---

## 2. The FP8-on-Ampere question, answered with evidence

A100 is SM80 and has no FP8 tensor cores. The brief correctly flagged this as the thing most
likely to bite. What actually happened:

vLLM selected the Marlin path and said so explicitly:

```
INFO  [__init__.py:634] Selected MarlinFP8ScaledMMLinearKernel for Fp8LinearMethod
WARN  [marlin_utils_fp8.py:112] Your GPU does not have native support for FP8 computation but
      FP8 quantization is being used. Weight-only FP8 compression will be used leveraging the
      Marlin kernel. This may degrade performance for compute-heavy workloads.
INFO  [gpu_model_runner.py:5405] Model loading took 28.9 GiB memory and 6.142374 seconds
```

**The FP8 is preserved as a storage format — it is not dequantised to bf16 at load.** 28.9 GiB
(29.36 GiB once the MTP head is also loaded), against the ~54 GiB a bf16 27B would need. The
weights stay 8-bit in HBM and Marlin dequantises per-tile inside the kernel to feed the bf16
tensor cores.

This is the good outcome and it is worth being precise about *why* it is good here. Marlin is a
weight-only scheme: it saves **memory and memory bandwidth**, not FLOPs. Decode is bandwidth-bound,
so FP8 storage is a genuine decode win on Ampere. Prefill is compute-bound, so the warning's
"may degrade performance for compute-heavy workloads" is real and applies to prefill — which is
why prefill lands at ~2,500 tok/s rather than higher. We keep the win where it matters and pay
for it where it matters less. Practically, 29 GiB of weights is what leaves ~44 GiB free for KV
cache on an 80 GB card, which is what makes eight independent copies viable at all.

**I never had to descend the fallback ladder.** Rung (a) — a sufficiently new vLLM — was enough.

---

## 3. Two environment blockers, and how they were cleared

Both are worth recording because they will recur on any fresh venv on this box.

### 3.1 vLLM 0.27.1 ships a cu130 torch; this driver is CUDA 12.4

`pip install vllm==0.27.1` pulls `torch 2.13.0+cu130`. The driver here is **550.163.01 = CUDA
12.4**, and cu130 binaries require an r580+ driver:

```
RuntimeError: The NVIDIA driver on your system is too old (found version 12040).
```

The fix is NVIDIA **forward compatibility**, which is supported precisely on datacenter GPUs like
the A100: a newer user-mode CUDA driver runs against the older kernel driver. I did this without
touching the system — downloaded `cuda-compat-13-1_590.48.01-1_amd64.deb` from the Debian 13 CUDA
repo, extracted it with `dpkg-deb -x`, and copied the libs to `/home/deployer/models/cuda-compat`
(410 MB). Every launcher then sets:

```bash
export LD_LIBRARY_PATH=/home/deployer/models/cuda-compat:$LD_LIBRARY_PATH
```

Verified before going further:

```
$ LD_LIBRARY_PATH=/home/deployer/models/cuda-compat python -c "import torch; ..."
avail True count 8
NVIDIA A100-SXM4-80GB (8, 0) bf16 55.1 TFLOPS
```

No `apt install`, no root, no change to the system CUDA or driver. Reversible by deleting one
directory. (There *is* passwordless sudo on this box; I deliberately did not use it.)

### 3.2 The engine crashed on a missing `ninja`

First launch died during memory profiling:

```
File "vllm/v1/worker/gpu_model_runner.py", line 6283, in _dummy_sampler_run
FileNotFoundError: [Errno 2] No such file or directory: 'ninja'
```

vLLM JIT-compiles the FlashInfer sampler at startup. `ninja` *was* installed in the venv, but I
was invoking `vllm` by absolute path, so the venv's `bin/` was never on `PATH`. Fixed in the
launcher:

```bash
export PATH=/home/deployer/models/vllm-venv/bin:/usr/local/cuda-12.8/bin:$PATH
```

Note this presents as a *startup crash long after load*, not an import error, because the sampler
is only exercised during the dummy profiling run.

### 3.3 Where things live

| Path | Size | Note |
|---|---:|---|
| `/home/deployer/models/Qwen3.8-27B-Unc-FP8` | 29 G | weights |
| `/home/deployer/models/vllm-venv` | 7.7 G | vLLM 0.27.1, torch 2.13.0+cu130, Python 3.12 |
| `/home/deployer/models/cuda-compat` | 410 M | forward-compat driver libs |

The venv is on `/home` rather than the scratchpad on purpose: the brief asked for scratchpad
temp files, but `/tmp` here is RAM-backed tmpfs and the venv needs to survive a reboot for the
launcher scripts to be genuinely restartable. Launcher scripts and benchmarks are in the
scratchpad as requested. Free space on `/home` after everything: **300 GB**.

---

## 4. What is deployed

Eight independent single-GPU servers, GPU *N* → port `810N`. This is the whole point of the
exercise and the deliberate contrast with GLM: the model fits on one card, so eight copies give
eight times the throughput instead of one copy limping across eight cards.

`<scratchpad>/launch_one.sh` (final, winning config):

```bash
#!/usr/bin/env bash
# usage: launch_one.sh <gpu> <port> [extra vllm args...]
GPU=$1; PORT=$2; shift 2
export CUDA_VISIBLE_DEVICES=$GPU
export LD_LIBRARY_PATH=/home/deployer/models/cuda-compat:$LD_LIBRARY_PATH
export PATH=/home/deployer/models/vllm-venv/bin:/usr/local/cuda-12.8/bin:$PATH
export HF_HUB_OFFLINE=1
exec /home/deployer/models/vllm-venv/bin/vllm serve /home/deployer/models/Qwen3.8-27B-Unc-FP8 \
  --served-model-name qwen3.8-27b \
  --port $PORT --host 127.0.0.1 \
  --tensor-parallel-size 1 \
  --max-model-len 131072 \
  --gpu-memory-utilization 0.92 \
  --enable-prefix-caching \
  --mamba-cache-mode align \
  --speculative-config '{"method":"qwen3_5_mtp","num_speculative_tokens":4}' \
  --trust-remote-code "$@"
```

`<scratchpad>/launch_all.sh` starts all eight (and skips any port already healthy, so it is safe
to re-run as a repair tool).

### Load time and VRAM — measured

```
$ ./launch_all.sh && (poll /health on 8100-8107)
ALL 8 UP in 113s
```

**113 seconds to bring all eight endpoints up in parallel**, with a warm `torch.compile` cache.
The first-ever cold start was ~5 minutes, of which 72 s was `torch.compile`; that cache lives in
`~/.cache/vllm/torch_compile_cache` and is shared by all eight processes, so only the very first
launch after a vLLM upgrade pays it.

Per-server startup accounting from the logs:

```
Model loading took 29.36 GiB memory and 7.623014 seconds
torch.compile took 4.96 s        (main model, warm cache)
torch.compile took 8.65 s        (MTP head, warm cache)
GPU KV cache size: 549,184 tokens
Maximum concurrency for 131,072 tokens per request: 4.19x
Graph capturing finished in 17 secs, took 1.24 GiB
Using FLASH_ATTN attention backend
```

`nvidia-smi` with all eight running:

| GPU | Used |
|---|---:|
| 0 | 74,695 MiB |
| 1 | 74,593 MiB |
| 2 | 74,593 MiB |
| 3 | 74,695 MiB |
| 4 | 74,695 MiB |
| 5 | 74,695 MiB |
| 6 | 74,695 MiB |
| 7 | 74,863 MiB |
| **Total** | **597,524 MiB (583.5 GiB)** |

The comparison that matters: GLM-5.2 spent **380.2 GiB across all 8 GPUs to hold one copy**.
Qwen3.8-27B spends **~73 GiB per GPU to hold a complete, independent copy — eight of them.**

`--max-model-len 131072` is a deliberate choice, not the model's limit (262,144). At 131k the
engine reports 4.19× max concurrency; at 262k it would be ~2.1×. Our prompts top out around 80k,
so halving the declared context buys twice the concurrent slots for free. Raise it only if a real
prompt exceeds 131k.

---

## 5. Required capabilities — each verified, not assumed

### 5.1 Deep JSON schema — works, and is enforced

Tested with a genuinely deep schema (`<scratchpad>/bench.py: DEEP_SCHEMA`): three levels of
nested objects, arrays of objects, five `enum`s, `minItems` on five arrays, and
`additionalProperties: false` at every object level — a miniature of the bookwriter entity/scene
structure. Output validated client-side with `jsonschema.validate`, not eyeballed.

```
wall 39.94s completion=1888 finish=stop
SCHEMA VALIDATES OK
entities: 4 kinds: ['location', 'faction', 'person', 'object']
scenes: 3 beats per scene: [3, 3, 3]
sample patch: {'op': 'replace', 'path': 'entities[2].attributes.physical.condition', 'value': 'wounded'}
```

Every constraint was honoured, including `minItems` and the enum on `kind`. It also held on a
much larger generation — **8,821 tokens** of schema-conformant JSON in the §9 realistic run, and
2,028 tokens on top of a 59k prompt in §5.2.

**Does it slow generation? No — the cost is within noise.** Same 28k prompt, same server, with
and without the schema:

| | Out tok | Decode tok/s |
|---|---:|---:|
| Deep schema (guided) | 8,821 | **45.11** |
| Free-form, no schema | 4,188 | **45.33** |

0.5% apart. vLLM compiles the schema to a grammar once and the per-token mask is negligible
against a 27B forward pass. **Use the schema everywhere; it is free.**

### 5.2 Long context — a real 60k prompt, end to end

Not just "it didn't crash". I buried a fact in the middle of a 58,847-token prompt and required
the model to retrieve it into a schema-constrained field:

```json
{"test": "60k prompt e2e", "prompt_tokens": 58847, "out": 2028, "ttft": 24.98,
 "wall": 63.8, "decode_toks": 52.23, "schema_valid": true,
 "entity_names": ["Corvath Ilmswen", "Elara Vane", "The Kraken of the Deep Fjord",
                  "The Arcane Grimoire"],
 "recalled_needle": true}
```

The needle (`Corvath Ilmswen`) was placed at the halfway point and came back verbatim in the
generated JSON. Long context is functional, not merely accepted.

### 5.3 Prompt caching — 48.9×, with server-side proof

Repeated ~49k prefix on one endpoint, reading vLLM's own
`vllm:prefix_cache_{queries,hits}_total` counters around each request:

| Run | Prompt tok | TTFT s | Effective prefill tok/s | Blocks queried | Blocks hit |
|---|---:|---:|---:|---:|---:|
| cold (first send) | 48,969 | **19.501** | 2,511 | 48,969 | 0 |
| warm (same prefix, new suffix) | 48,969 | **0.399** | 122,703 | 48,969 | **48,608** |
| warm again | 48,969 | **0.394** | 124,170 | 48,969 | 48,608 |

**19.50 s → 0.399 s, a 48.9× reduction in time-to-first-token**, with 99.26% of blocks served
from cache. The residual 361 tokens are the tail partial block: vLLM set the attention block size
to **784 tokens** to make it match the mamba page size, so the cache granularity here is coarser
than the usual 16.

A note on comparing this to GLM's 2,400×: GLM's ratio was larger only because its cold prefill was
catastrophically slow (193.7 s). In absolute terms both land in the same place — a re-sent prefix
costs a fraction of a second. Qwen's cold prefill is already ~10× faster, so there is simply less
to save. The operational advice is identical and still the highest-leverage thing you control:
**keep the prefix byte-stable and in the same order across calls.**

I also tested `--mamba-cache-mode all` (which additionally caches the recurrent state of the 48
linear-attention layers) on a separate GPU. It made **no difference**: 0.406 s warm TTFT vs
0.399 s for the default. Not worth enabling, which is convenient because MTP forbids it (§7).

### 5.4 Thinking control — the off switch is real, and I verified it by token count

The chat template is unambiguous. Reading `chat_template.jinja` directly:

```jinja
{%- if enable_thinking is undefined or enable_thinking is true %}
    {%- set resolved_reasoning_effort = reasoning_effort|default('xhigh') %}
    {%- if resolved_reasoning_effort not in ('xhigh', 'medium', 'low') %}
        {{- raise_exception('Unexpected reasoning effort ...') }}
...
{%- if add_generation_prompt %}
    {{- '<|im_start|>assistant\n' }}
    {%- if enable_thinking is defined and enable_thinking is false %}
        {{- '<think>\n\n</think>\n\n' }}     ← hard off switch
    {%- else %}
        {{- '<think>\n' }}
```

So: **thinking is ON by default at `reasoning_effort: 'xhigh'`** — the same trap GLM had. Setting
`enable_thinking: false` pre-fills an already-closed `<think></think>` block, which structurally
prevents the model from thinking rather than merely asking it not to.

Measured on a realistic multi-step counting task (`max_tokens: 8000`, temperature 0):

| Setting | Prompt tok | **Completion tok** | Wall s |
|---|---:|---:|---:|
| `enable_thinking: false` | 81 | **725** | 5.6 |
| `reasoning_effort: low` | 109 | **346** | 3.0 |
| `reasoning_effort: medium` | 79 | **650** | 4.9 |
| `reasoning_effort: xhigh` (**default**) | 121 | **1,283** | 12.2 |

And on a trivial arithmetic prompt, `enable_thinking: false` took completions from 43 tokens to
**4**, and the prompt from 67 to 27 (the xhigh instruction paragraph disappears from the system
message).

Three things follow that you need to know before sending traffic:

1. **The default costs 1.8× the output tokens of thinking-off on a realistic task**, and 10× on a
   short one. Leaving it at the default silently multiplies your bill and your wall-clock.
2. **Unlike GLM, `reasoning_effort: "low"` is a real branch, not a silent no-op** — it genuinely
   produced the fewest tokens of any thinking-on mode. But there is **no `"none"`**, and any value
   outside `xhigh|medium|low` makes the template `raise_exception`, i.e. the request 400s.
3. **No reasoning parser is configured**, so with thinking ON the chain-of-thought comes back
   inside `content` with a trailing `</think>`, *not* in a separate `reasoning_content` field.
   vLLM ships a `qwen3` parser (`--reasoning-parser qwen3`) if you ever want thinking-on with
   clean separation. We deploy with thinking off, so this is moot for the pipeline — but it would
   silently corrupt any JSON parse if someone enabled thinking without the parser.

**Recommendation: send `"chat_template_kwargs": {"enable_thinking": false}` on every pipeline
call.** It is also required for clean schema output, since guided decoding would otherwise force
JSON from the first token and destroy the thinking block.

---

## 6. Single-stream throughput

One request at a time on port 8100, streaming, `min_tokens == max_tokens` and `ignore_eos` so the
decode rate is measured over a known token count. Prefill rate is `prompt_tokens / TTFT`
(client-side, so it includes tokenisation and scheduling — slightly pessimistic). Unique prompts
per row so prefix caching cannot flatter the result.

Command: `python b1_single.py`

| Prompt tok | TTFT s | **Prefill tok/s** | Gen tok | Decode s | **Decode tok/s** | Wall s |
|---:|---:|---:|---:|---:|---:|---:|
| 2,879 | 1.12 | **2,568.2** | 400 | 8.24 | **48.45** | 9.4 |
| 28,161 | 10.47 | **2,690.8** | 400 | 8.68 | **45.96** | 19.1 |
| 70,484 | 30.21 | **2,333.2** | 400 | 9.29 | **42.96** | 39.5 |

Two observations.

1. **Prefill is essentially flat across a 24× context range** (2,568 → 2,333 tok/s, −9%). This is
   the hybrid attention earning its keep: only 16 layers do quadratic work, the other 48 are
   linear in sequence length.
2. **Decode degrades only 11% from 2.9k to 70k.** GLM lost 28% over a comparable range. Same
   reason — the KV cache that has to be re-read every decode step covers a quarter of the layers.

These are without speculative decoding. §7 roughly doubles the decode column.

---

## 7. Speculative decoding — the MTP head is a large win, exactly inverting the GLM result

The checkpoint ships real MTP weights (`mtp.fc`, `mtp.layers.0.*`, `mtp.norm`,
`mtp.pre_fc_norm_{embedding,hidden}`), and vLLM 0.27.1 registers `Qwen3_5MTP` with method name
`qwen3_5_mtp`. No sidecar, no second model — the draft head is part of the checkpoint.

One constraint: `Qwen3_5MTP` refuses `--mamba-cache-mode all` and requires `align`. Since §5.3
showed `all` buys nothing, this costs us nothing.

Method: identical prompts, greedy (`temperature 0`), acceptance read from vLLM's
`vllm:spec_decode_num_{draft,accepted}_tokens_total` counters around each request.
Baseline is port 8100 (no spec), MTP on port 8107.

| Workload | Config | Out tok | **Decode tok/s** | Drafted | Accepted | **Acceptance** |
|---|---|---:|---:|---:|---:|---:|
| plain text, 3k out | baseline | 2,579 | 48.09 | 0 | 0 | — |
| plain text, 3k out | MTP k=2 | 2,562 | **78.47** (+63%) | 2,220 | 1,452 | **65.4%** |
| plain text, 3k out | MTP k=3 | 2,562 | **82.16** (+71%) | 2,958 | 1,578 | 53.3% |
| plain text, 3k out | MTP k=4 | 2,565 | **79.37** (+65%) | 3,824 | 1,609 | 42.1% |
| **deep-schema JSON, 3k out** | baseline | 3,000 | 48.02 | 0 | 0 | — |
| **deep-schema JSON, 3k out** | MTP k=2 | 3,000 | **89.69** (+87%) | 2,147 | 1,873 | **87.2%** |
| **deep-schema JSON, 3k out** | MTP k=3 | 3,000 | **103.72** (+116%) | 2,563 | 2,090 | 81.5% |
| **deep-schema JSON, 3k out** | MTP k=4 | 3,000 | **114.09** (+138%) | 2,871 | 2,226 | **77.5%** |

**Structured JSON accepts far better than prose** — 77–87% vs 42–65% — which is the intuition the
GLM report had to abandon. Low-entropy output *is* the ideal case for speculation; it just could
never pay off on a 256-expert MoE. On a dense model it pays off exactly as theory predicts.

`k` trades acceptance *rate* against accepted tokens *per step*. Prose peaks at k=3; JSON is still
climbing at k=4. **We deploy k=4** because the pipeline's token volume is dominated by structured
output — the repo's own `usage.json` logs show ~91k structured output tokens against ~17k of prose
per story. The cost is a 3.4% regression on prose leaves, against +10% on JSON.

**Prefill is unaffected.** vLLM warns that spec decoding clamps `max_num_scheduled_tokens` to
2048; I checked whether that hurts, and it does not:

| Port | Config | Prompt tok | TTFT s | Prefill tok/s |
|---|---|---:|---:|---:|
| 8100 | baseline | 48,993 | 19.49 | 2,513.9 |
| 8107 | MTP | 48,993 | 19.59 | 2,501.4 |

**Prefix caching still works with MTP**, slightly degraded by the `align` cache mode: warm TTFT
0.642 s vs 0.399 s baseline (30.7× vs 48.9×), 48,000 blocks cached vs 48,608. Paying 0.24 s per
call to gain 55–138% on decode is trivially worth it.

Speculative decoding is exactly-equivalent by construction — drafts are only accepted if they
match what the target model would have sampled — so **this speedup costs nothing in quality.**

---

## 8. Concurrency — this is where it decisively beats GLM

### 8.1 One endpoint, plain text (mirrors the GLM protocol exactly: ~4k prompt, 1,500 tok/stream)

Command: `python b2_conc.py <port> 1500 1,2,4,8,16,32`. Unique prompt per request, so no prefix
sharing.

| Concurrency | Wall s | Total gen tok | **Aggregate tok/s** | Per-stream decode tok/s | Mean TTFT s |
|---:|---:|---:|---:|---:|---:|
| 1 | 32.5 | 1,500 | **46.1** (1.00×) | 48.14 | 1.39 |
| 2 | 34.8 | 3,000 | **86.3** (1.87×) | 46.44 | 2.47 |
| 4 | 38.9 | 6,000 | **154.3** (3.35×) | 43.27 | 4.11 |
| 8 | 46.6 | 12,000 | **257.8** (5.59×) | 38.15 | 6.87 |
| 16 | 62.4 | 24,000 | **384.7** (8.34×) | 30.58 | 12.22 |
| 32 | 94.8 | 48,000 | **506.3** (10.98×) | 21.85 | 23.09 |

**11× aggregate scaling on a single GPU.** GLM was flat at 1.0× across the same 8× range on all
eight GPUs. Per-stream decode falls gracefully (48 → 22 tok/s over a 32× concurrency increase)
rather than dividing exactly by N. This is dense-model batching working the way it should: one
weight read serves the whole batch.

### 8.2 One endpoint, the real workload shape (deep-schema JSON), baseline vs MTP k=4

The decision-relevant sweep — this is what picked the deployed config.

| Concurrency | baseline agg tok/s | **MTP k=4 agg tok/s** | MTP gain |
|---:|---:|---:|---:|
| 1 | 45.6 | **99.6** | +118% |
| 4 | 148.7 | **250.4** | +68% |
| 8 | 243.5 | **377.6** | +55% |
| 16 | 353.5 | **402.4** | +14% |

MTP wins across the entire realistic operating range and is still ahead at 16. The gain narrows
as concurrency rises because the GPU shifts from bandwidth-bound to compute-bound, at which point
verifying extra draft tokens stops being free. On plain text at k=2 I measured the crossover
directly: MTP led at every level up to 16 (+15%) and finally **lost at 32** (456.5 vs 506.3,
−10%). If you ever push a single endpoint past ~24 concurrent, turn speculation off.

### 8.3 All eight endpoints at once — the number that matters for fan-out

Deep-schema JSON, production config (MTP k=4), unique prompts, all 8 servers driven simultaneously.

| Per endpoint | Total concurrent | Wall s | Gen tok | **Aggregate tok/s (8 GPUs)** | Mean TTFT s |
|---:|---:|---:|---:|---:|---:|
| 1 | 8 | 18.0 | 9,600 | **533.2** | 2.63 |
| 4 | 32 | 22.0 | 38,400 | **1,743.1** | 4.34 |
| 8 | 64 | 27.3 | 76,800 | **2,812.6** | 6.72 |

**2,812.6 tok/s aggregate.** Scaling across GPUs is essentially perfect: single-endpoint JSON at
N=8 was 377.6 tok/s, ×8 = 3,021 predicted, 2,812.6 measured = **93% of linear**. The processes are
fully independent — no NCCL, no shared KV, no interconnect traffic — so the only contention is
host CPU and PCIe during prefill.

For comparison, the earlier plain-text fan-out on the pre-MTP config reached 2,053.5 tok/s at 64
concurrent (99.6% of linear).

---

## 9. The realistic payload

28k-token prompt, deep JSON schema, large structured output, `temperature 0.7` (i.e. sampling, not
greedy — this is why acceptance and therefore speedup are lower here than in §7's greedy runs).

| Config | Prompt tok | Out tok | TTFT s | **Decode tok/s** | Wall s | Schema valid |
|---|---:|---:|---:|---:|---:|---|
| baseline | 26,656 | 8,821 | 9.80 | **45.11** | 205.3 | ✅ |
| MTP k=4 | 26,656 | 6,719 | 9.94 | **55.90** (+24%) | 130.1 | ✅ |
| baseline, no schema | 26,656 | 4,188 | 0.77 | 45.33 | 93.1 | n/a |

Both structured runs produced valid deep-schema JSON at 6.7–8.8k output tokens. The +24% from MTP
here is smaller than the +138% in §7 for two reasons worth understanding: temperature 0.7 lowers
draft acceptance, and at 28k context each verification step carries more attention work.

**Translating to a full story run.** The GLM report established one story ≈ 29 calls, ~562k tokens
prefilled and ~467k generated (with thinking on; far less with it off). At the measured rates for
a *single* endpoint on this workload — ~2,500 tok/s prefill, ~56 tok/s decode:

- prefill 562k → ~225 s
- decode 467k → ~8,300 s

≈ **2.4 hours per story on one endpoint**, and eight stories in parallel across the eight
endpoints for roughly the same wall-clock. Turning thinking off (§5.4) cuts the generated-token
count substantially, and prefix caching (§5.3) largely erases the prefill term for the repeated
story-bible prefix. The equivalent GLM figure at 16 tok/s decode was ~8 hours for one story with
no parallelism available at all.

---

## 10. Direct comparison against GLM-5.2

GLM figures are the measured numbers from `reports/glm-local-deployment.md`.

| Metric | GLM-5.2 (754B MoE, Q3_K_M, llama.cpp, **8 GPUs for 1 copy**) | Qwen3.8-27B (27B dense, FP8, vLLM, **1 GPU per copy**) | Ratio |
|---|---:|---:|---:|
| Prefill @ ~2k | 396.0 tok/s | **2,568.2** tok/s | **6.5×** |
| Prefill @ ~20–28k | 305.2 tok/s | **2,690.8** tok/s | **8.8×** |
| Prefill @ ~50–70k | 254.9–259.1 tok/s | **2,333.2** tok/s | **9.0–9.2×** |
| Decode, single stream @ 2k | 21.71 tok/s | **48.45** (99.6 w/ MTP on JSON) | **2.2× / 4.6×** |
| Decode, single stream @ 50–70k | 15.69–16.60 tok/s | **42.96** tok/s | **2.6–2.7×** |
| Best single-stream decode | 24.26 (draft-mtp) | **114.09** (MTP k=4, JSON) | **4.7×** |
| Aggregate @ 8 concurrent, one endpoint | 26.06 tok/s *(all 8 GPUs)* | **377.6** tok/s *(one GPU)* | **14.5× on ⅛ the hardware** |
| **Aggregate, whole box** | **~27 tok/s** | **2,812.6 tok/s** | **104×** |
| Concurrency scaling 1→8 | **1.00×** (flat) | **5.59×** | — |
| Speculative decoding | draft-mtp +45%, 79.6% acc; ngram **−25%** | MTP k=4 **+138%** on JSON, 77.5% acc | — |
| Prefix cache benefit | 2,400× (193.7 s → 0.08 s) | 48.9× (19.50 s → 0.399 s) | GLM higher *ratio*, similar absolute |
| Footprint | **380.2 GiB for ONE copy** across 8 GPUs | **~73 GiB per copy**, 583.5 GiB for **EIGHT** | — |
| Max context served | 131,072 | 131,072 (model supports 262,144) | — |
| Thinking default | `Reasoning Effort: Max` | `enable_thinking=true`, `xhigh` | both need explicit disabling |

### What actually explains the gap

It is not that vLLM beats llama.cpp, though it helps. Three structural facts do the work:

1. **Dense beats sparse at small batch.** Every GLM pathology — flat concurrency, n-gram
   speculation losing 25% — was the same mechanism: extra tokens in a batch pull extra expert
   weights, so nothing amortises. Dense weights are read once for the whole batch. This is why
   Qwen scales 5.6× where GLM scaled 1.0×, and why speculation gains 138% where n-gram lost 25%.
2. **Fitting on one card converts 8 GPUs from a memory pool into 8 independent workers.** GLM's
   eight A100s were buying capacity to *hold* 754B parameters, with seven idle at any instant
   under layer-split. Qwen's eight A100s are eight real workers.
3. **Hybrid linear attention makes long context cheap.** 16 of 64 layers keep a KV cache, giving
   a 549k-token cache on one card and near-flat prefill across a 24× context range.

The one place GLM's numbers look better is the prefix-cache *ratio*, and that is an artefact of its
cold prefill being 10× slower — there was simply more to save.

---

## 11. Recommended client usage

```python
import openai
c = openai.OpenAI(base_url="http://127.0.0.1:8100/v1", api_key="none")   # 8100..8107
r = c.chat.completions.create(
    model="qwen3.8-27b",
    messages=[...],
    max_tokens=20000,
    extra_body={
        "chat_template_kwargs": {"enable_thinking": False},   # REQUIRED, see §5.4
    },
    response_format={"type": "json_schema",
                     "json_schema": {"name": "scenes", "schema": SCHEMA, "strict": True}},
)
```

- **Always** pass `enable_thinking: False`. The default is `xhigh` and costs ~1.8× the tokens.
- Never pass a `reasoning_effort` outside `xhigh|medium|low` — the template raises and you get a 400.
- Keep the long story-bible prefix **byte-stable and first** in the message list, so prefix caching
  hits (§5.3). This is the single highest-leverage thing the client controls.
- Fan out across all 8 ports; they are fully independent. Round-robin is fine. ~8 concurrent per
  endpoint is the sweet spot (377.6 tok/s/GPU); beyond ~24 per endpoint, speculation starts to hurt.
- Guided decoding is free — use the schema on every structured call.

---

## 12. What I would change with another hour

1. **Measure quality, not just speed.** Everything here is throughput. Marlin FP8 is weight-only
   and mathematically mild, but the checkpoint is also *abliterated*, and the GLM report's §5
   argument applies with equal force: long-range JSON-patch consistency fails silently. I would
   run the repo's own `reconstruct/runs/matrix` prompts through this endpoint and diff the
   entity-state timelines against the provider run. That is the measurement that decides whether
   this model can replace the API, and I did not make it.
2. **Sweep `--max-num-seqs` and `--max-num-batched-tokens`.** Both are at defaults. The concurrency
   curve was still climbing at 32, and TTFT at 64 concurrent (6.7 s) suggests prefill scheduling is
   the limiter, not decode. A larger batched-token budget would likely push the fan-out number
   past 3,000 tok/s.
3. **Test MTP k=5 and k=6 on JSON.** Acceptance was still 77.5% at k=4 and the tok/s curve had not
   turned over. There is probably another 10–15% there for structured output.
4. **Try `--kv-cache-dtype fp8`.** The KV cache is already 549k tokens, so this is not needed for
   capacity — but halving KV traffic should speed decode at high concurrency, where we are
   bandwidth-bound on the 16 full-attention layers.
5. **Drop the vision tower.** The model is multimodal and we will never send an image; the ViT and
   its 16,384-token encoder budget are pure overhead. Worth a small amount of VRAM and startup time.
6. **Pin a cu128 vLLM build** to remove the forward-compat dependency. The current setup works and
   is verified, but it relies on `LD_LIBRARY_PATH` ordering that a future caller could easily omit —
   and the failure mode (driver too old) is at least loud rather than silent.
7. **Put a load balancer in front of 8100–8107.** Right now the client must round-robin. A trivial
   nginx or a `vllm serve --api-server-count` front end would make the fan-out a single URL, which
   is less error-prone than eight ports in the pipeline config.

---

## 13. Reproducing everything here

All scripts are in the session scratchpad
(`/tmp/claude-1001/-home-deployer-laion-bookwriter/70e4d41c-edcc-4f25-881c-f35243dc0da1/scratchpad`),
which is tmpfs and will not survive a reboot — copy them somewhere durable if you want to keep them.

| File | Produces |
|---|---|
| `launch_one.sh <gpu> <port> [args]` | one endpoint on the winning config |
| `launch_all.sh` | all eight; skips already-healthy ports |
| `bench.py` | shared harness + the deep JSON schema |
| `b1_single.py` | §6 single-stream prefill/decode table |
| `b2_conc.py <port> <gen> <levels>` | §8.1 concurrency sweep |
| `b3_prefix.py <port>` | §5.3 prefix-cache table |
| `b4_fanout.py` | §8.3 8-endpoint fan-out (plain text) |
| `b5_real.py <port>` | §9 realistic payload |
| `b6_spec.py` | §7 speculative decoding + acceptance |
| `b7_conc_json.py` | §8.2 JSON concurrency, baseline vs MTP |
| `logs/gpu*.log` | server logs quoted throughout |

Health check for all eight:

```bash
for p in 810{0..7}; do printf "%s: " $p; curl -s -m2 http://127.0.0.1:$p/health -o /dev/null -w "%{http_code}\n"; done
```

### Housekeeping

- The eight servers are the only processes I started on these GPUs, and all eight are running.
- Nothing was deleted or moved. No user data touched; `runs/` and `reconstruct/runs/` untouched.
- No system-level changes: no `apt`, no root, no driver or CUDA modification. The forward-compat
  libs are a self-contained directory under `/home/deployer/models`.
- The GPUs were verified free (1 MiB each) before I started, and nothing else was found running
  on them at any point.
