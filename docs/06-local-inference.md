# Running large models locally

Measured on 8 × A100-SXM4-80GB with GLM-5.2 (754B total, 40.5B active per token,
256 experts, top-8 routing) quantised to `UD-Q3_K_M` — 3.64 bits per weight, 342.7 GB
on disk — served by a from-source CUDA build of llama.cpp.

Full deployment report with commands: [`../reports/glm-local-deployment.md`](../reports/glm-local-deployment.md).

## Headline numbers

| | |
|---|---|
| Live footprint | **380.2 GiB** across 8 GPUs |
| Load time | 61 s from 9 GGUF shards |
| Prefill | 255–396 tok/s depending on context length |
| Decode, no speculation | 15.7–21.7 tok/s |
| Decode, with the model's own draft head | **24.26 tok/s** |
| Aggregate at 8 concurrent requests | **~26 tok/s — the same as at 1** |
| Repeated 50k prefix, cached | 193.7 s → **0.064 s** |

## Four GPUs cannot run it

380.2 GiB measured against 314.9 GiB usable on four A100s. Even with the KV cache
stripped to nothing, the weights leave under 0.1 GiB of margin. **Five is the minimum,
eight is comfortable.** The repository publishes no Q4; `UD-Q3_K_M` is the largest of
five quantisations and everything else is ≤2.68 bpw, which is not a sensible base for
25–30k-token strict-JSON emissions with long-range state dependencies.

One pleasant surprise: GLM-5.2 uses multi-head latent attention, so llama.cpp caches
only a 576-wide compressed latent with a single KV head — **92.8 KiB per token**, or
11.6 GiB at the full 128k context. On most large models the KV cache decides your GPU
count. Here it is a rounding error and the weights decide.

## The rule that cost three wrong predictions

> **On a sparse MoE at small batch, anything that widens the batch — speculative
> verification or concurrent sequences — pays close to full weight-traffic cost per extra
> token. Only a drafter accurate enough to clear roughly 65% acceptance beats it.**

Three predictions were made from dense-model intuition. All three were wrong, and the
rule above is what survived.

### Prediction 1: low-entropy JSON would make speculative decoding shine

Our output is schema-bound JSON with the same keys repeating. Acceptance rates rise as
entropy falls, so this should have been the ideal case.

| Config | Decode | Acceptance |
|---|---|---|
| `none` | 16.70 tok/s | — |
| `ngram-cache` | **12.52 tok/s** | 21.3% |

A **25% regression.** The "verification is nearly free" argument holds on a dense model,
where the same weights are read whatever tokens you check. Here, each drafted position
pulls its own set of 8 routed experts, so the union of weights to stream grows roughly
linearly with draft length. At 21% acceptance you pay for ~4.7 drafted tokens to keep
one, and the extra expert gathers cost more than the tokens saved.

### Prediction 2: the MTP head needs a draft model the repo does not publish

Wrong, and the loader said so. GLM-5.2 ships a multi-token-prediction head as layer
`blk.78` — 26 tensors, 4.56 GiB — which the loader was discarding as *"unused tensor"*
purely because nothing requested it. The server builds the draft context from the
**resident** model; no `-md`, no second copy.

| Config | Decode | Acceptance |
|---|---|---|
| `none` | 16.70 tok/s | — |
| `draft-mtp` | **24.26 tok/s** | **79.6%** |

**+45%, and free of quality cost** — speculative decoding is exactly-equivalent by
construction. Runtime proof: 26 "unused tensor" warnings on baseline, zero with MTP.
Cold prefill drops 258.9 → 185.9 tok/s, which prompt caching makes irrelevant.

`draft-eagle3`, `draft-dspark` and `draft-dflash` need a separately trained draft model
matched to the base. None exists for an abliterated GLM-5.2. Present in the build,
unusable in practice.

### Prediction 3: a sparse MoE batches well, so concurrency recovers the idle cards

Layer-split across 8 GPUs is a *pipeline*: at batch 1 exactly one card computes and seven
wait. The entire 8-GPU throughput case rested on concurrency recovering that.

| Concurrent requests | Aggregate | Per stream |
|---|---|---|
| 1 | 26.22 tok/s | 26.20 |
| 2 | 27.33 tok/s | 14.15 |
| 4 | 27.00 tok/s | 7.26 |
| 8 | 26.06 tok/s | 3.66 |

**Flat across an eightfold range.** Per-stream divides exactly by N. Eight concurrent
calls finish in the time eight sequential calls would take. Same mechanism: different
sequences route to different experts, so batching N sequences needs up to 8N distinct
expert reads and there is nothing to amortise.

**Practical consequence: do not restructure a long job from serial to parallel.** Issue
calls sequentially and spend the effort on prompt-cache prefix stability.

## The biggest lever is not a decode question

Re-sending an identical 50k prefix: **193.7 s → 0.064 s**, a factor of 2,400, with one
token reprocessed. Nothing else on this page competes.

The condition is that the shared prefix must be **byte-identical and in the same
position**. This has a direct implication for prompt construction that we got wrong at
first: our prompts put the large, stable schema block *after* the scene-specific
material, so it was re-prefilled on every one of ~1,800 calls. Stable content first,
varying content last.

Also: `-np N` divides the context window between slots. With `-c 262144 -np 8` each call
gets 32,768 tokens — and a 23k prompt then leaves 9.5k for the answer, truncating
mid-sentence with no error. Since concurrency buys nothing here, `-np 1` with the full
window is strictly better.

## Combined effect

| Configuration | One complete story |
|---|---|
| baseline, reasoning on | 8 h 12 min |
| + `draft-mtp` | 6 h 10 min |
| + reasoning off | 2 h 15 min |
| + prompt caching | **1 h 35 min** |

**5.2× on unchanged hardware.** MTP ~1.45×, reasoning-off ~2.7×, caching most of the
rest.

## Serving config that won

```
llama-server -m GLM-5.2-UD-Q3_K_M-00001-of-00009.gguf \
  --host 127.0.0.1 --port 8099 \
  --device CUDA0,...,CUDA7 -sm layer -ngl 999 \
  -c 262144 -np 1 -fa on -b 4096 -ub 2048 -fit off \
  --jinja --spec-type draft-mtp --alias glm-5.2-abliterated-q3km
```

Request body:

```json
{
  "max_tokens": 60000,
  "cache_prompt": true,
  "chat_template_kwargs": { "enable_thinking": false },
  "response_format": {"type": "json_schema", "json_schema": {...}}
}
```

`max_completion_tokens` is ignored by llama.cpp's shim — it reads `max_tokens`. Sending
only the former silently leaves generation at the server default.

## Schema enforcement

Deep schemas — nested objects, arrays of objects, enums, `minItems`,
`additionalProperties: false` — are genuinely enforced through the GBNF grammar path, in
both strict modes. No silent ignore, no 400.

One caveat that matters more than it looks: asked for a trajectory moving from guarded to
trusting, the model returned five phases all valued `"guarded"`. **The grammar guarantees
the value is in the enum; it guarantees nothing about it being the right member.** Schema
conformance is a syntax check. A pipeline that counts only violations would score that
as perfect.

## Hosted versus local

Local wins on data governance, on a pinned reproducible checkpoint, on cost at volume,
and on having no router between you and the weights. Hosted wins on single-call latency
and on peak quality.

The sensible split follows from the cost structure rather than from preference: upper
layers are ~0.4% of call volume and determine everything downstream, so run them on the
strongest model available. Run the bulk locally, where volume is what matters and the
marginal cost is zero.
