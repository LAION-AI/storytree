# GLM-5.3 panel report — Muse 1.2 vs. Explorer default, plus local-serving study

Date: 2026-08-26. Judge model: GLM-5.3-Flash (the model behind the Zen
`muse-spark-1.2` endpoint, per project usage; 321.3B total / 18B active
parameters, hybrid linear + DeepSeek-sparse attention, 288 routed experts).

Two questions answered here:

1. **Scores.** How does a *panel of three* GLM-5.3 judges (averaged) rate the
   Muse-1.2-generated layers against the Ornith-generated layers currently
   served by the public StoryTree Explorer?
2. **Serving.** Can GLM-5.3-Flash run locally on this machine under vLLM with
   efficient batching — and if not here, what hardware does it take?

---

## 1. Panel design

- Three independent judges per artifact, same prompt, temperature 0.5,
  scores averaged. Judge *i* is pinned to Zen shim port 822{2,3,4}, so the
  three judges run genuinely in parallel.
- The judge prompts and rubrics are **byte-identical** to the pipeline's
  layer judges (`distill/root_layer.py` RT1–RT10, `distill/plot_layer.py`
  P1–P5 with the event digest as ground truth, `distill/expose_layer.py`
  X1–X9), so panel means are comparable to the recorded pipeline gates.
- Arms are anonymised: a judge sees only the artifact, never its origin.
- Arms:
  - **explorer_default** — what https://projects.laion.ai/storytree/webapp/storytree-explorer.html
    serves today: `runs/story_root_v3`, `runs/plot_layer_v8`, `runs/expose_v1`
    (all composed by Ornith-1.5-397B).
  - **muse12** — the Muse-1.2 pipeline run: `runs/story_root_muse`,
    `runs/plot_layer_muse`, `runs/expose_muse`.
- Gate rule as everywhere in the project: mean ≥ 4.0 AND no dimension < 3.
- Harness: `tools/glm_panel_judge.py`; raw per-judge output in
  `runs/glm53_panel/`.

## 2. Results

### 2.1 Overview — panel means (average of 3 judges, scale 1–5)

| Layer | explorer_default (Ornith) | muse12 (GLM-5.3) | Δ (muse − default) | Gate |
|---|---|---|---|---|
| Story root | **4.80** (spread 0.0) | **4.73** (spread 0.1) | −0.07 | both PASS |
| Plots | **2.73** (spread 0.4) | **3.33** (spread 0.2) | **+0.60** | both FAIL |
| Exposé | **4.30** (spread 0.45) | **4.44** (spread 0.22) | +0.15 | both PASS |

Spread = max − min of the three judge means. Root and exposé differences sit
inside the judge spread — read them as ties. The plot difference (+0.60) is
larger than either arm's spread and points the same way for all three judges.

Events, entities and meta layer are identical in both arms (the Muse pipeline
consumed the existing `events_build10_full` / `entity_trial_v2` /
`meta_layer_v2b` artifacts), so they were not re-judged here.

### 2.2 The headline: the panel inverts the pipeline's plot ranking

The recorded pipeline judgements were **self-judgements** — each arm was
scored by the same model that composed it (v8 by Ornith: 4.6 PASS; Muse
plots by Muse: 2.6 FAIL). Under a *common* judge the ranking flips:

| Plot layer | Self-judge (pipeline) | GLM-5.3 panel |
|---|---|---|
| `plot_layer_v8` (online in the Explorer) | 4.6 PASS | **2.73 FAIL** |
| `plot_layer_muse` | 2.6 FAIL | **3.33 FAIL** |

This is the project's "checkers measure themselves" lesson in a new costume:
composer-as-judge inflated its own work by ~1.9 points. Absolute scores are
not comparable across judge models — but the within-panel comparison is
clean, and it says the Muse plot layer is the better of the two.

### 2.3 Plots per dimension

| Dim | explorer_default | muse12 | What the judges cite (paraphrased) |
|---|---|---|---|
| P1 causal integrity | 2.00 | 2.33 | Unanimous on both arms: chains contain and-then sequences without same-plot enablement, and several links cite causes from *other* plots' events (e.g. v8's "Hunter" chain leaning on trap/escape events it does not contain; Muse's "Matrix Itself" jumping ev-020→ev-045 without an enabling member) |
| P2 perspective discipline | 4.00 | 4.00 | Both arms hold one stance per plot |
| P3 membership accuracy | 2.33 | 3.00 | v8: events padded into the wrong plot (the Cypher bargain inside "Reluctant One", Betrayer claiming Rescue's events) and required turns missing (ev-033, ev-038, ev-044). Muse: fewer but real omissions (ev-011 rebirth) and one padded 19-event catch-all plot |
| P4 arc completeness | 3.33 | 4.00 | v8 arcs truncate; Muse arcs mostly resolve |
| P5 non-redundancy | 2.00 | 3.33 | v8: "Hunter and the Chosen" is effectively a subset-rehash of "Reluctant One" (four shared events, same framing); Rescue/Betrayer double-claim the sacrifice/capture pair. Muse: the climax events recur in 3–5 plots but *reframed* per stance — judges called it borderline instead of rehash |

Two conclusions the evidence supports directly:

* **P1 is the universal defect**, identical in kind on both arms and now
  flagged by six of six judge passes. It is checkable procedurally: every
  chain link's `caused_by_previous` must name an event *inside the same
  chain*; a link-lint over `plots.json` would have caught most citations.
* **The distinct-context strategy for shared climax events works.** Muse's
  P5 (3.33) with events recurring in up to five plots beat v8's P5 (2.00)
  with fewer shared events but verbatim-identical framing. This confirms
  handshake2's diagnosis (overlap is structure, not rehash — vary the
  `why_in_plot`/`caused_by_previous` context) and its Priority A
  (`load_bearing_event`).

### 2.4 Root and exposé — weakest dimensions

Root (both PASS): the only dim below 4 on either arm is **RT4 entity roster
coverage** — default 4.00, muse 3.33. That matches the known Muse weakness
in entity differentiation (Brown/Jones) already on the handshake's list.

Exposé (both PASS): weakest dims are **X4 causal chain honours every plot**
on the default arm (3.33 — consistent with its weak plot layer) and
**X7 processing fluency** on both arms (default 3.67, muse 3.33).

Two concrete, fixable findings from the notes: the **jacket-copy truncation
("…save one he") sits in the default arm** (`expose_v1`, i.e. what the
Explorer serves) and was cited by all three judges — it costs points on X1,
X5 *and* X7 there; the Muse exposé has no truncation, its X7 loss comes from
2253-word density and long hypotactic sentences in the synopsis.

---

## 3. Local serving study: GLM-5.3-Flash on this machine

**Verdict: not runnable on this box — not in vLLM, not in llama.cpp, not in
SGLang, in any precision.** The blocker is the GPU architecture, not the
quantisation. This machine has 8× **A100-SXM4-80GB (Ampere, SM80)**, not
H100s.

The evidence, item by item (all checked 2026-08-26):

1. **vLLM has no GLM-5.3-Flash support in any release.** The architecture
   (`Glm5NextForConditionalGeneration`, model_type `glm5_next`) is absent
   from the model registry of vLLM 0.27.1 (installed here), 0.28.0 (latest
   PyPI release) and current `main`. Support exists only as PR
   [vllm-project/vllm#53906](https://github.com/vllm-project/vllm/pull/53906)
   — opened **today**, unmerged, and it ships new CUDA kernels
   (FlashMLA cmake, sparse-MLA tests, mHC tilelang kernels).
2. **The sparse-attention kernels are Hopper-only.** GLM-5.3-Flash inherits
   GLM-5's DeepSeek-style sparse attention (DSA: MLA with `kv_lora_rank`
   512 + a top-k indexer, `index_topk` 2048). Every sparse-MLA backend in
   vLLM is gated on compute capability 9.x or newer —
   `flashattn_mla_sparse.py` literally returns
   `capability.major == 9`; the FlashMLA and FlashInfer sparse backends are
   SM90/SM100/SM120. **There is no SM80 sparse-MLA backend at all**, so no
   choice of dtype, quant, or offload makes this model run on an A100.
3. **The native checkpoint is FP8** (e4m3, dynamic activation scales).
   Ampere has no FP8 tensor cores; vLLM's weight-only fallback would not
   help because of (2).
4. **BF16 does not fit anywhere.** `zai-org/GLM-5.3-Flash-BF16` is
   321.3B × 2 bytes ≈ **599 GiB** — larger than this machine's free disk
   (352 GB) and effectively the whole 640 GB of combined VRAM, before KV
   cache. The FP8 checkpoint is ≈ 299 GiB and fits neither in the free
   disk comfortably nor in the 4 GPUs one Ornith instance could vacate
   (320 GB minus runtime overhead), and (2) makes the attempt moot anyway.
5. **llama.cpp does not know the architecture.** `master` has `glm4moe` and
   `glm-dsa` (GLM-5.x dense-DSA lineage) but no `glm5_next`; no open PR.
   All three GGUF repos on the Hub (unsloth, AtomicChat, aj9o9) are
   **empty placeholders** — README only, no weights, because there is
   nothing to run them with yet.
6. **SGLang is in the same state**: GLM-5.3-Flash support is an open
   same-day PR (sgl-project/sglang#36507), and the merged cookbook targets
   Hopper/Blackwell (TRT-LLM DSA kernels, FP8 KV).

### The "one GPU per endpoint, experts in RAM" idea

Tempting — 18B active parameters would indeed fit into a single 80 GB GPU —
but no engine can do it for this architecture today:

- vLLM's only CPU-offload mechanism (`--cpu-offload-gb`) is *layer*-granular,
  not *expert*-granular: it would stream **all 288 experts of a layer** over
  PCIe on every forward pass regardless of which 8 the router picked.
  That is hundreds of GB per token step — well under 1 tok/s.
  Expert-granular offload (keep the router + attention on GPU, page experts
  from RAM on demand) exists in llama.cpp (`--n-cpu-moe`) and KTransformers,
  but both require architecture support that does not exist (point 5), and
  Ampere-compatible attention kernels, which also do not exist (point 2).
- Even when llama.cpp support lands: with a Q4 GGUF (~170–190 GB), 1 GPU +
  experts in the 1 TB RAM, realistic decode is of the order of 10–20 tok/s
  per stream, CPU-memory-bandwidth-bound — around Zen-API speed, without
  the batching headroom vLLM was wanted for.

### What it actually takes (H100 sizing)

Per the official vLLM recipe the model targets "NVIDIA Hopper and newer";
FP8 weights ≈ 299 GiB + KV + runtime. Tensor parallel must divide the 64
attention heads (TP4/TP8 fine).

| Setup | Weights/GPU | Verdict |
|---|---|---|
| 4× H100 80GB, TP4 | 74.8 GiB | **Does not fit** — <4 GiB left for KV/runtime; the official TP4 recipe presumes H200/B200-class memory |
| **8× H100 80GB, TP8** | 37.4 GiB | **The minimum H100 config.** ~35 GiB/GPU free for KV; with MLA's tiny KV (≈ 576 B/token/DSA-layer, and the ~2/3 linear-attention layers hold O(1) state) that is effectively unlimited batch capacity — the deployment is compute-bound, ideal for batching |
| 4× H200 141GB, TP4 | 74.8 GiB | The official single-node recipe; ~55 GiB/GPU for KV |
| 2 endpoints à 8× H100 | — | Only if two nodes exist; on one 8-GPU node run ONE TP8 endpoint and batch — vLLM continuous batching replaces the "many endpoints" pattern we use with llama.cpp |

Recommended launch (from the vLLM recipe, once PR #53906 is merged):

```bash
vllm serve zai-org/GLM-5.3-Flash --tensor-parallel-size 8 \
  --kv-cache-dtype fp8 \
  --speculative-config '{"method":"mtp","num_speculative_tokens":5}'
```

With 18B active parameters in FP8, MTP speculative decoding and sparse
attention, published Hopper numbers for this class of model suggest
~100+ tok/s single-stream and thousands of tok/s aggregate under batch —
i.e. one 8×H100 node would replace the Zen API at roughly 5–10× the
per-stream speed and far higher parallel throughput. (Estimates, not
measurements — we have no Hopper hardware to verify.)

---

## 4. Measured Zen/Muse throughput (what we actually get today)

From `runs/muse_timing.jsonl` (pipeline + this panel; all calls through the
`tools/zen_shim.py` instances on ports 8222–8224):

| Metric | Value |
|---|---|
| Calls logged | 73 (71 ok, 2× HTTP 503, both recovered by retry) |
| Wall time per call | mean 161 s, median 155 s, p90 265 s, max 375 s |
| Decode speed | **median 27 tok/s**, mean 34 tok/s per stream |
| Prompt size | mean 8.3k tokens, max 19.8k |
| Completion size | mean 4.4k tokens, max 10.7k |
| Retries needed | 8 of 73 calls |
| This panel | 18 judge calls, 3-way parallel, **~15 min wall clock** |

For comparison, local Ornith-1.5-397B under llama.cpp does ~44 tok/s per
stream and doubles across its two instances — i.e. today the *local* big
model is faster per stream than GLM-5.3 over Zen, and the Zen path caps at
~3 useful parallel streams.

Operational notes: three shims give real 3-way parallelism; beyond ~4
concurrent calls Zen itself throttles (sublinear speedup, sporadic
HTTP 503 — two observed in the pipeline run, retried successfully).

---

## 5. Consequences

1. **The Explorer's plot layer is not the better one.** Under a common
   judge panel, `plot_layer_muse` (3.33) beats the online `plot_layer_v8`
   (2.73); v8's recorded 4.6 was its composer judging itself. Consider
   swapping the Explorer's plot layer once a Muse v3 run (with
   `load_bearing_event`, handshake2 Priority A) passes the panel — and from
   now on, gate layers with a judge that did not compose them.
2. **P1 (within-plot causal enablement) is the defect to attack next**, on
   both arms, per six of six judge passes. It is procedurally checkable:
   lint that every `caused_by_previous` names an event of the same chain,
   and feed violations back as named faults (the event-layer
   audit→regenerate pattern, applied to plots).
3. **Distinct contexts beat deletion for shared climax events** — now
   confirmed by an independent judge model, not just our post-mortem of the
   v2 regression.
4. Root and exposé are effectively tied and both PASS; the two cheap wins
   are fixing `expose_v1`'s truncated jacket copy (all three judges caught
   it, it drags three dimensions) and Muse's synopsis sentence density.
5. **Serving GLM-5.3 stays remote for now.** This box (8× A100/SM80)
   cannot run it in any engine or precision — the sparse-attention kernels
   exist only for Hopper+. Re-check after vLLM PR #53906 merges *and* a
   Hopper-class node is available: the efficient shape is one 8× H100 TP8
   endpoint (or 4× H200 TP4) with continuous batching, not many small
   endpoints. Until then: 3 Zen shims ≈ 3 × 27 tok/s, and local Ornith
   remains the throughput workhorse.
