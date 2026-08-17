# 12 · Throughput

Every number below is labelled **[M]** measured on this box, **[D]** derived
arithmetically from a measured number, or **[A]** assumed. Nothing is a measured
run of the swarm, because the swarm has not been run.

---

## 12.1 The measured inputs

All from `reports/qwen-local-deployment.md`, on 8× A100-80GB running one full copy of
`Qwen3.8-27B-Uncensored-FP8` per GPU, vLLM 0.27.1, FP8/Marlin, MTP k=4, thinking off.

| | Value | |
|---|---|---|
| Aggregate, 8 endpoints, 64 concurrent, deep-schema JSON | **2,812.6 tok/s** | [M] |
| Aggregate, 8 endpoints, 32 concurrent | 1,743.1 tok/s | [M] |
| Aggregate, 8 endpoints, 8 concurrent (1/endpoint) | 533.2 tok/s | [M] |
| Single stream, one endpoint, JSON + MTP k=4 | 99.6 tok/s | [M] |
| Single stream, no speculation, 2.9k / 28k / 70k context | 48.45 / 45.96 / 42.96 tok/s | [M] |
| Concurrency scaling 1→8 on one endpoint | 5.59× | [M] |
| Prefix cache, 48,969-token prefix, TTFT | 19.501 s → 0.399 s = **48.9×** | [M] |
| …same with MTP k=4 (`align` cache mode) | 0.642 s = 30.7× | [M] |
| Guided decoding cost | 45.11 vs 45.33 tok/s = **free** | [M] |
| Cold prefill | 2,333–2,690 tok/s per endpoint | [M] |
| KV cache | **549,184 tokens** per GPU | [M] |
| Engine-reported max concurrency at 131,072-token requests | **4.19×** | [M] |
| Mean TTFT at 64 concurrent | 6.72 s | [M] |

Two per-stream rates are used below and both are **[D]**, straight division of a
measured aggregate by the concurrency it was measured at: 66.7 tok/s per stream at 8
concurrent, 54.5 at 32, 43.9 at 64.

The one number the pipeline itself has produced, and the anchor for stage 10: a
**scaffolded scene transition, measured end to end** — 6 calls, 11,087 output tokens
against 40,708 prompt tokens, 153.3 s on one endpoint (`transitions_qwen`); and in
the grounded arm 6 calls, 14,785 output tokens, 257.0 s (`transitions_qwen_grounded`).
GLM's scaffolded path measured 5.3 calls and 22,679 output tokens per scene. **[M]**

---

## 12.2 The estimate, corrected

The draft table in `WHITEPAPER-SWARM.md` has two arithmetic problems and one modelling
problem, and all three push the same way.

**Problem 1: small stages are latency-bound, not throughput-bound.** Dividing a
stage's token count by 2,812.6 tok/s assumes 64 concurrent requests. Stage 4 has
seven calls. Seven calls cannot occupy 64 slots, so the wall clock is one call's
tokens divided by the *per-stream* rate, not the stage's tokens divided by the
aggregate. The draft gave stage 4 as 0.2 minutes; it is closer to 3.7.

**Problem 2: several stages are internally serial.** Stage 2 is three passes, each
consuming the previous. Stage 4 is draft → panel → consolidate. Stage 6 is author →
critic → revise. The wall is the sum of the rounds, not the whole stage in parallel.

**Problem 3: stage 10 is not one call per scene.** Budget dilution forbids it
(`docs/05` §1). A scene node is a scaffold of roughly six calls, and the measured
output is 11–15k tokens per scene, not the 9,000 the draft assumed.

Recomputed with the same rate model, rounds summed where serial:

| Stage | Calls | Output tokens | Wall | Bound by |
|---|---:|---:|---:|---|
| 1 · scene nodes, blind | 224 | 1,568,000 | **9.3 min** | throughput |
| 2 · event boundaries (3 passes) | 56 | 99,500 | **2.3 min** | 3 serial rounds |
| 3 · event drafts | 30 | 180,000 | **1.8 min** | per-stream @32 |
| 4 · plots (draft, 5 doctors, consolidate) | 7 | 36,000 | **3.7 min** | 3 serial rounds, N≤5 |
| 5 · entity unification *(concurrent with 4)* | 4 | 24,000 | *1.5 min* | per-stream @8 |
| 6 · profiles (author, critic, revise) | 105 | 437,500 | **4.7 min** | 3 serial rounds |
| 7 · root (write, critique, revise) *(conc. w/ 6)* | 3 | 12,000 | *2.0 min* | single stream |
| 8 · exposé (draft, 5 doctors, revise) *(conc. w/ 6)* | 7 | 21,000 | *2.3 min* | 3 serial rounds |
| 9 · event rewrite (2 calls each) | 60 | 300,000 | **3.1 min** | 2 serial rounds |
| 10 · scene rewrite (6 calls each) | 1,344 | 3,035,200 | **18.0 min** | throughput |
| **Total** | **1,840** | **5,713,200** | **≈ 43 min** | |

Bold rows are on the critical path; italic rows run inside another stage's window.
The two synchronisation barriers are `max(stage 4, stage 5) = 3.7 min` and
`max(stage 6, stage 7→8) = 4.7 min`.

**Against the draft: 690 calls → 1,840, 4.55M tokens → 5.71M, 27 min → 43 min.**
The call count is not a surprise — `docs/05` §7 already put a full story at ~1,800
calls.

Per-unit output-token counts for stages 2 through 9 are **[A]**, as are the counts of
224 scenes, ~30 events and ~35 entities. Stages 1 and 10 are anchored on measurement:
stage 10 on the two scaffolded runs above, stage 1 on the assumption that a blind
scene node without the full mental simulation costs about half a finished one.

### The serial comparison, stated honestly

At 45 tok/s — the single-stream rate without speculation, which is the configuration
the earlier pipeline actually ran — 5.71M output tokens is **35.3 hours**, so the
speedup is **49×**.

That is the flattering framing and it is not the fair one. Speculative decoding is a
configuration choice available to a serial run too. Against a serial run of the *same*
optimised configuration at 99.6 tok/s, the same work is **15.9 hours** and the speedup
is **22×**.

**22× is the number the architecture earns.** The rest is the MTP head, which the
top-down design could have had as well.

For 100 screenplays: ~72 hours of 8-GPU wall time, **≈570 GPU-hours** [D]. The
comparison against the ~15,000 GPU-hours estimated for the top-down design with a
three-round feedback loop still holds by a wide margin, and for the stated reason —
that design is serial by construction and this one is not.

---

## 12.3 The dependency that dominates, and is unverified

**Every stage-1 and stage-10 agent needs the full script in context.** For a feature
that is roughly 40,000 tokens [A]. Stage-10 agents additionally need the finished
superstructure — root, exposé, plots, entity profiles, the parent event — call it
another 25,000 [A], so ~65,000 tokens of context per call.

Stage 10 issues 1,344 calls. **If nothing is cached, that is 87.4 million prefill
tokens** [D]. At the measured cold-prefill rate of 2,333 tok/s per endpoint across 8
endpoints, that is **78 minutes** [D] — on a stage whose decode work is 18 minutes.
Stage 1 adds a further 8.96M prefill tokens, 8 minutes [D].

Prefix caching is what makes this go away, and the deployment measured it at **48.9×**
on a 48,969-token prefix, with 99.26% of blocks served from cache. The script and the
superstructure are byte-identical across all 1,344 calls, so if the prefix is kept
byte-stable and *first* in the message list, it should be prefilled once per endpoint —
8 cold prefills, ~20 seconds total — and every subsequent call pays the measured warm
TTFT of 0.642 s.

**But there is a second thing prefix caching is doing here, and it is the one nobody
has verified.** With 8 concurrent sequences per endpoint at 65,000 tokens each, the
naïve KV requirement is 520,000 tokens against a measured cache of 549,184. That is
95% full before a single token is generated, and the engine's own log agrees: it
reports a maximum concurrency of **4.19×** for 131,072-token requests. Block-level
prefix sharing is what changes 8 × 65k into 65k + 8 × (suffix + output) ≈ 185k, which
is comfortable. So prefix caching is not an optimisation on this stage. **It is the
thing that makes 8-concurrent-per-endpoint possible at all.**

The measurement that exists — `b3_prefix.py` — drove **one endpoint sequentially**
with a repeated prefix. That the same sharing holds across eight *concurrent* slots on
the same GPU is **[A]**, and it is assumed, not measured.

### What happens if it does not hold

Say it plainly, because the answer is not "a bit slower":

- Every call pays a cold prefill. Stage 10 goes from 18 minutes to roughly **96
  minutes**; stage 1 from 9 to 17. And prefill contends with decode on the same GPU,
  so treating them as additive is the optimistic case.
- Concurrency has to drop. Without block sharing, 8 × 65k does not fit in 549k, so the
  operating point falls to ~4 concurrent per endpoint (32 total), where the measured
  aggregate is 1,743.1 tok/s rather than 2,812.6 — a further 1.6× on every
  throughput-bound stage.
- Together, the pipeline goes from **~43 minutes to somewhere between 2 and 3.5
  hours**, and the 22× advantage over a serial run collapses to roughly 5×.

**This is the first thing to measure, it is cheap, and it is one timing.** Run stage 1
alone on one script and read vLLM's own `vllm:prefix_cache_{queries,hits}_total`
counters around the batch. If the hit rate at 8 concurrent matches the 99.26% measured
at 1 concurrent, the table above stands. If it does not, the fix is known and
unpleasant: reduce concurrency per endpoint, or stop sending the whole script and send
a retrieved window instead — which reintroduces exactly the attention-scoping decision
the design was trying to avoid making by hand.

---

## 12.4 Three smaller caveats, all in the same direction

**The 2,812.6 figure was measured on short prompts.** The fan-out benchmark used
prompts of a few thousand tokens, not 65,000. Measured single-stream decode falls 11%
from 2.9k to 70k context, and the same hybrid-attention mechanism should apply under
batching — so expect the real aggregate at long context to be roughly 10% below the
headline. The table does not include that haircut.

**Guided decoding is free, but only for decode.** Measured at 0.5% against free-form
output, which is the basis for schema-constraining every call in the pipeline. It has
no bearing on the prefill problem above.

**MTP gains shrink under load.** Measured on JSON: +118% at 1 concurrent, +55% at 8,
+14% at 16, and on prose it *lost* 10% at 32. The 2,812.6 figure already includes MTP
at k=4 at 64 total concurrent, so this is priced in — but if concurrency per endpoint
is raised past ~24 to compensate for anything, speculation must be turned off, and
that changes the numbers again.

---

*None of this has been measured on the swarm. The 43 minutes is an estimate built on
measured rates and an unmeasured caching assumption, and the assumption is worth more
than the estimate. Treat 43 minutes as the optimistic end of a range whose pessimistic
end is 3.5 hours, until stage 1 has actually run once.*
