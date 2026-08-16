"""Compute estimator for one full reconstruction run.

Every constant is tagged `measured` or `assumption`. Measured constants come
from this repository's own logs and reports and are cited to the file that holds
them. Assumptions are labelled and are the things to attack first if the numbers
look wrong.

    python3 -m distill estimate
    python3 -m distill estimate --json

The two levers that dominate everything: whether hidden reasoning is on (a ~6x
swing on generated tokens) and whether the judge is Opus or Qwen (roughly half
the input tokens in the run).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

# --------------------------------------------------------------------------
# MEASURED — the work
# --------------------------------------------------------------------------

M = {
    "script_chars": (133_937, "reconstruct/runs/matrix/script_map.json"),
    "script_tokens": (39_596, "measured with the Qwen3.8-27B tokenizer on "
                              "127.0.0.1:8100 /tokenize, 2026-08-16"),
    "scenes": (224, "reconstruct/runs/matrix/script_map.json"),
    "entities": (36, "reconstruct/runs/matrix/artifacts/entities.json "
                     "(16 characters, 10 locations, 4 objects, 3 groups, 3 concepts)"),
    "plots": (5, "reconstruct/runs/matrix/artifacts/plots.json"),
    "events": (18, "reconstruct/runs/matrix/artifacts/events.json"),
    "beats_per_scene": (3.25, "mean over the 4 reconstructed scene nodes — n=4, weak"),
    "one_deep_structure_out": (4_280, "22,679 output tokens / 5.3 calls per "
                                      "scaffolded scene transition, docs/03 and docs/05 §1"),
    "scene_out_total": (22_679, "docs/05 §1: scaffolded scene transition"),
    "scene_calls": (5.3, "docs/05 §1"),
    "scene_in_per_call": (27_000, "mean of the measured blind (27,795-28,191) and "
                                  "sighted node (19,044-26,318) prompt token counts "
                                  "in reconstruct/runs/matrix/logs/calls/"),
    "reasoning_share": (0.836, "docs/05 §2: 520,211 reasoning vs 102,108 visible "
                               "output on a complete forward feature run"),
}

# Measured per-call input/output for the five upper-layer stages, from
# reconstruct/runs/matrix/logs/calls/recon.*.json. Sum: 302,997 in / 93,293 out.
UPPER_MEASURED = {
    "root":   {"in": 69_909, "out": 9_267},
    "expose": {"in": 56_752, "out": 20_399},
    "plots":  {"in": 59_715, "out": 13_379},
    "entity": {"in": 53_718, "out": 37_885},
    "event":  {"in": 62_903, "out": 12_363},
}

# --------------------------------------------------------------------------
# MEASURED — the hardware (reports/qwen-local-deployment.md, docs/06)
# --------------------------------------------------------------------------

HW = {
    "a100_agg_tok_s": (2_812.6, "8 endpoints x 8 concurrent, deep-schema JSON, "
                                "MTP k=4; 93% of linear vs single-endpoint x8"),
    "a100_single_endpoint_n8": (377.6, "one endpoint, 8 concurrent, JSON, MTP k=4"),
    "a100_single_stream_json_mtp": (99.6, "one endpoint, N=1, JSON, MTP k=4"),
    "a100_single_stream_plain": (46.6, "one endpoint, N=1, plain text"),
    "a100_prefill_tok_s": (2_500.0, "prefill at 20-50k context, per endpoint"),
    "prefix_cache_speedup": (48.9, "19.50 s -> 0.399 s TTFT on a repeated 48,969-token prefix"),
    "gib_per_copy": (29.36, "FP8 weights + MTP head, one copy per A100"),
}

# --------------------------------------------------------------------------
# MEASURED — Opus 5 pricing (Anthropic API, current at 2026-08-16)
# --------------------------------------------------------------------------

OPUS = {
    "in_per_mtok": 5.00,
    "out_per_mtok": 25.00,
    "cache_write_multiplier": 1.25,   # 5-minute TTL
    "cache_read_multiplier": 0.10,
}

# --------------------------------------------------------------------------
# ASSUMPTIONS — every one of these is a guess and is labelled as such
# --------------------------------------------------------------------------

A = {
    "author_rounds": (3, "the brief's 'assume 3 feedback rounds per artifact on "
                         "average'. Read as three author-judge exchanges: 3 author "
                         "calls and 3 judge calls, the third judge call being the "
                         "passing verdict."),
    "judge_rounds": (3, "as above"),
    "revision_scale": (1.0, "a revision costs a full redraft. Conservative: a "
                            "targeted revision that only rewrites the failing "
                            "sub-structure would cost ~0.6x. Reported as a "
                            "sensitivity."),
    "entity_out": (3_000, "the spec's entity profile is far richer than the "
                          "existing pipeline's 618-token-per-entity artifact "
                          "(relationships to every character, a few-hundred-word "
                          "backstory, Big Five, off-cliche interests). Set above "
                          "the one-deep-structure rate of 4,280? No: below it, "
                          "because much of the profile is enumerated fields."),
    "entity_nonchar_out": (1_800, "locations, objects, groups, concepts"),
    "plot_out": (4_280, "one deep structure per call, at the measured rate"),
    "event_out": (4_280, "same"),
    "trace_out": (2_500, "a few hundred words of derivation plus the trap list"),
    "trace_in_scale": (0.6, "a trace sees the artifact, the round history and the "
                            "source material it was derived from, but not the "
                            "whole script for the lower layers"),
    "judge_out": ({"root": 3_000, "expose": 2_500, "entity": 2_000, "plot": 1_800,
                   "event": 1_800, "scene": 4_000, "trace": 1_500},
                  "one score + evidence + instruction per dimension, plus the "
                  "mechanical block. Scene is largest: 17 dimensions over a "
                  "22.7k-token artifact."),
    "judge_overhead_in": (7_000, "judge cheat sheet (~4k) + the rendered rubric "
                                 "(~3k), on top of the author's context"),
    "cacheable_upper": (46_596, "script (39,596) + rubric and sheets (~7,000) — "
                                "byte-identical across rounds and across nodes of "
                                "the same layer, so cacheable"),
    "cacheable_scene": (15_000, "root + plots + dossiers, stable across a scene's "
                                "sub-calls and rounds; the scene text is not"),
    "b200_per_gpu_speedup": (3.5, "ASSUMPTION, not measured here. A100-80GB HBM2e "
                                  "is ~2.0 TB/s; B200 is ~8 TB/s. Small-batch "
                                  "decode is bandwidth-bound, so ~4x is the naive "
                                  "ceiling; 3.5x allows for the fact that our A100 "
                                  "number already includes MTP speculation and "
                                  "high concurrency. It may be conservative: FP8 on "
                                  "A100 is emulated through Marlin (no native FP8 "
                                  "hardware), while B200 has native FP8, so the "
                                  "compute-bound part of the curve could improve "
                                  "more than bandwidth alone predicts. Unmeasured."),
    "b200_scaling": (0.93, "the measured cross-GPU scaling efficiency on 8 A100s "
                           "with fully independent per-GPU copies, reused. No "
                           "interconnect is involved in this workload."),
}


def val(table, key):
    v = table[key]
    return v[0] if isinstance(v, tuple) else v


# --------------------------------------------------------------------------

@dataclass
class Layer:
    name: str
    count: int
    calls_per_round: float
    author_in: int
    author_out: int
    judge_out: int
    cacheable_in: int
    traces: bool = True
    detail: str = ""
    totals: dict = field(default_factory=dict)


def layers() -> list[Layer]:
    ce = val(A, "cacheable_upper")
    cs = val(A, "cacheable_scene")
    jo = val(A, "judge_out")
    ent = val(M, "entities")
    chars = 16                      # measured split of the 36 entities
    others = ent - chars
    ent_out = int((chars * val(A, "entity_out") +
                   others * val(A, "entity_nonchar_out")) / ent)
    return [
        Layer("root", 1, 1, UPPER_MEASURED["root"]["in"],
              UPPER_MEASURED["root"]["out"], jo["root"], ce,
              detail="measured in/out for the single sighted root call"),
        Layer("expose", 1, 1, UPPER_MEASURED["expose"]["in"],
              UPPER_MEASURED["expose"]["out"], jo["expose"], ce,
              detail="measured in/out for the single exposé call"),
        Layer("entity", ent, 1, UPPER_MEASURED["entity"]["in"], ent_out,
              jo["entity"], ce,
              detail=f"{chars} characters + {others} non-character entities, "
                     "one per call (the spec's one-at-a-time rule)"),
        Layer("plot", val(M, "plots"), 1, UPPER_MEASURED["plots"]["in"],
              val(A, "plot_out"), jo["plot"], ce,
              detail="one plot per call at the measured one-deep-structure rate"),
        Layer("event", val(M, "events"), 1, UPPER_MEASURED["event"]["in"],
              val(A, "event_out"), jo["event"], ce,
              detail="18 measured events; sensitivity below for a finer event layer"),
        Layer("scene", val(M, "scenes"), val(M, "scene_calls"),
              val(M, "scene_in_per_call"),
              int(val(M, "scene_out_total") / val(M, "scene_calls")),
              jo["scene"], cs,
              detail="scaffolded: 5.3 calls, 22,679 output tokens per scene, both "
                     "measured"),
    ]


def cost_node(layer: Layer, rounds_a: int, rounds_j: int,
              revision_scale: float) -> dict:
    """Token cost for ONE artifact of this layer, across the whole loop."""
    a_calls = a_in = a_out = 0.0
    j_calls = j_in = j_out = 0.0
    artifact_out = layer.author_out * layer.calls_per_round
    prior_critiques = 0.0

    for r in range(1, rounds_a + 1):
        scale = 1.0 if r == 1 else revision_scale
        a_calls += layer.calls_per_round
        a_in += (layer.author_in + prior_critiques) * layer.calls_per_round
        a_out += artifact_out * scale
        if r <= rounds_j:
            j_calls += 1
            j_in += (layer.author_in + artifact_out
                     + val(A, "judge_overhead_in") + prior_critiques)
            j_out += layer.judge_out
            prior_critiques += layer.judge_out

    return {"author_calls": a_calls, "author_in": a_in, "author_out": a_out,
            "judge_calls": j_calls, "judge_in": j_in, "judge_out": j_out,
            "artifact_out": artifact_out}


def trace_cost(layer: Layer, rounds_a: int, rounds_j: int,
               revision_scale: float) -> dict:
    """A hindsight trace is itself an artifact with its own loop."""
    t_in = int(layer.author_in * val(A, "trace_in_scale"))
    pseudo = Layer(f"{layer.name}:trace", layer.count, 1, t_in,
                   val(A, "trace_out"), val(A, "judge_out")["trace"],
                   int(layer.cacheable_in * val(A, "trace_in_scale")))
    return cost_node(pseudo, rounds_a, rounds_j, revision_scale)


def build(*, revision_scale: float | None = None,
          rounds_a: int | None = None, rounds_j: int | None = None,
          thinking: bool = False) -> dict:
    revision_scale = revision_scale if revision_scale is not None else val(A, "revision_scale")
    rounds_a = rounds_a or val(A, "author_rounds")
    rounds_j = rounds_j or val(A, "judge_rounds")

    rows = []
    total = {"author_calls": 0.0, "author_in": 0.0, "author_out": 0.0,
             "judge_calls": 0.0, "judge_in": 0.0, "judge_out": 0.0}
    for layer in layers():
        per = cost_node(layer, rounds_a, rounds_j, revision_scale)
        per_trace = trace_cost(layer, rounds_a, rounds_j, revision_scale)
        row = {"layer": layer.name, "count": layer.count, "detail": layer.detail,
               "per_artifact": per, "per_trace": per_trace,
               "cacheable_in_per_call": layer.cacheable_in}
        for key in total:
            row.setdefault("layer_total", {})[key] = (per[key] + per_trace[key]) * layer.count
            total[key] += row["layer_total"][key]
        rows.append(row)

    artifacts = sum(layer.count for layer in layers())
    traces = artifacts
    calls = total["author_calls"] + total["judge_calls"]
    gen = total["author_out"] + total["judge_out"]
    gen_with_thinking = gen / (1 - val(M, "reasoning_share"))

    report = {
        "work": {
            "title": "The Matrix",
            "scenes": val(M, "scenes"),
            "source_chars": val(M, "script_chars"),
            "source_tokens": val(M, "script_tokens"),
            "artifacts": artifacts,
            "hindsight_traces": traces,
            "nodes_total": artifacts + traces,
        },
        "parameters": {
            "author_rounds": rounds_a, "judge_rounds": rounds_j,
            "revision_scale": revision_scale,
            "thinking": "on" if thinking else "off",
        },
        "layers": rows,
        "totals": {
            "calls": round(calls),
            "input_tokens": round(total["author_in"] + total["judge_in"]),
            "output_tokens": round(gen),
            "author_input_tokens": round(total["author_in"]),
            "author_output_tokens": round(total["author_out"]),
            "judge_input_tokens": round(total["judge_in"]),
            "judge_output_tokens": round(total["judge_out"]),
            "generated_tokens_thinking_off": round(gen),
            "generated_tokens_thinking_on": round(gen_with_thinking),
        },
    }
    report["opus_judge"] = opus_cost(total, rows)
    report["wallclock"] = wallclock(total, thinking=thinking)
    report["hardware"] = hardware_scenarios(total)
    report["sensitivity"] = sensitivity(rounds_a, rounds_j)
    return report


def opus_cost(total: dict, rows: list[dict]) -> dict:
    """Opus 5 as judge: it sees the judge input and produces the judge output."""
    j_in = total["judge_in"]
    j_out = total["judge_out"]
    naive = (j_in / 1e6) * OPUS["in_per_mtok"] + (j_out / 1e6) * OPUS["out_per_mtok"]

    # With prompt caching: the stable prefix is written once per (layer, node)
    # and read on every later call for that node.
    cached_reads = 0.0
    cache_writes = 0.0
    for row in rows:
        calls = row["per_artifact"]["judge_calls"] + row["per_trace"]["judge_calls"]
        writes = 1  # one write per node; the prefix survives the node's rounds
        cacheable = row["cacheable_in_per_call"]
        cache_writes += writes * cacheable * row["count"]
        cached_reads += (calls - writes) * cacheable * row["count"]
    uncached = max(0.0, j_in - cache_writes - cached_reads)
    cached_cost = (
        (uncached / 1e6) * OPUS["in_per_mtok"]
        + (cache_writes / 1e6) * OPUS["in_per_mtok"] * OPUS["cache_write_multiplier"]
        + (cached_reads / 1e6) * OPUS["in_per_mtok"] * OPUS["cache_read_multiplier"]
        + (j_out / 1e6) * OPUS["out_per_mtok"]
    )
    return {
        "input_tokens": round(j_in),
        "output_tokens": round(j_out),
        "usd_uncached": round(naive, 2),
        "usd_with_prompt_caching": round(cached_cost, 2),
        "cache_write_tokens": round(cache_writes),
        "cache_read_tokens": round(cached_reads),
        "note": "Opus 5 at $5/Mtok in, $25/Mtok out; cache write 1.25x, cache "
                "read 0.10x. Opus is not asked to think in this accounting — its "
                "thinking would be billed as output and is not included.",
    }


def wallclock(total: dict, *, thinking: bool) -> dict:
    """Local wall-clock for the author's share, and for author+judge if both are
    local. Decode dominates; prefill is largely erased by prefix caching."""
    mult = 1 / (1 - val(M, "reasoning_share")) if thinking else 1.0
    author_out = total["author_out"] * mult
    both_out = (total["author_out"] + total["judge_out"]) * mult

    def hours(tokens, rate):
        return tokens / rate / 3600

    agg = val(HW, "a100_agg_tok_s")
    single = val(HW, "a100_single_stream_json_mtp")
    one_ep = val(HW, "a100_single_endpoint_n8")
    return {
        "assumption": "decode-bound; prefill is ~2,500 tok/s per endpoint and the "
                      "stable prefix is cached at 48.9x, so prefill contributes "
                      "single-digit minutes and is not modelled separately.",
        "author_only": {
            "single_stream_hours": round(hours(author_out, single), 2),
            "one_endpoint_8_concurrent_hours": round(hours(author_out, one_ep), 2),
            "full_box_8xA100_hours": round(hours(author_out, agg), 2),
        },
        "author_and_judge_both_qwen": {
            "single_stream_hours": round(hours(both_out, single), 2),
            "full_box_8xA100_hours": round(hours(both_out, agg), 2),
        },
        "thinking": "on" if thinking else "off",
        "swing_if_thinking_on": round(1 / (1 - val(M, "reasoning_share")), 2),
    }


def hardware_scenarios(total: dict) -> dict:
    agg = val(HW, "a100_agg_tok_s")
    speed = val(A, "b200_per_gpu_speedup")
    scaling = val(A, "b200_scaling")
    per_a100 = agg / 8

    author = total["author_out"]
    both = total["author_out"] + total["judge_out"]

    def gpu_hours(tokens, rate_per_gpu, n, *, measured_at_8=False):
        # The 2,812.6 tok/s aggregate is already the measured 8-GPU number, so
        # the 93%-of-linear factor must not be applied again at n=8.
        eff = 1.0 if (measured_at_8 and n == 8) else scaling
        wall = tokens / (rate_per_gpu * n * eff) / 3600
        return wall, wall * n

    out = {"a100": {}, "b200": {}}
    for label, tokens in (("opus_judge_qwen_author", author),
                          ("qwen_author_and_judge", both)):
        wall, gh = gpu_hours(tokens, per_a100, 8, measured_at_8=True)
        out["a100"][label] = {"gpus": 8, "wall_hours": round(wall, 2),
                              "gpu_hours": round(gh, 2)}
    for n in (8, 64, 512):
        wall, gh = gpu_hours(both, per_a100 * speed, n)
        out["b200"][f"n={n}"] = {"wall_hours": round(wall, 3),
                                 "gpu_hours": round(gh, 2),
                                 "scripts_in_parallel": n // 8}
    out["b200"]["assumptions"] = A["b200_per_gpu_speedup"][1]
    widest = val(M, "scenes") * val(M, "scene_calls")
    out["parallelism_ceiling"] = (
        f"Layers are sequential (entities need the exposé, scenes need the "
        f"events), so within ONE script the concurrency ceiling is the widest "
        f"layer: {widest:.0f} independent scene sub-calls. Past roughly that "
        f"many concurrent streams, extra GPUs do nothing for a single script and "
        f"the only remaining axis is more scripts. The GPU-hour figure is "
        f"invariant under N by construction; only wall-clock moves."
    )
    out["note"] = ("The workload is embarrassingly parallel across nodes within a "
                   "layer and across scripts: one model copy per GPU, no NCCL, no "
                   "shared KV. Cross-GPU scaling was measured at 93% of linear on "
                   "8 A100s, and that figure is reused for B200 counts.")
    return out


def sensitivity(rounds_a: int, rounds_j: int) -> dict:
    base = build_light(rounds_a, rounds_j, 1.0)
    out = {"base": base}
    out["targeted_revisions_0.6"] = build_light(rounds_a, rounds_j, 0.6)
    out["one_round"] = build_light(1, 1, 1.0)
    out["five_rounds"] = build_light(5, 5, 1.0)
    out["no_traces"] = build_light(rounds_a, rounds_j, 1.0, traces=False)
    out["finer_event_layer_60"] = build_light(rounds_a, rounds_j, 1.0, events=60)
    return out


def build_light(rounds_a: int, rounds_j: int, revision_scale: float, *,
                traces: bool = True, events: int | None = None) -> dict:
    tin = tout = 0.0
    for layer in layers():
        count = events if (events and layer.name == "event") else layer.count
        per = cost_node(layer, rounds_a, rounds_j, revision_scale)
        tin += (per["author_in"] + per["judge_in"]) * count
        tout += (per["author_out"] + per["judge_out"]) * count
        if traces:
            tr = trace_cost(layer, rounds_a, rounds_j, revision_scale)
            tin += (tr["author_in"] + tr["judge_in"]) * count
            tout += (tr["author_out"] + tr["judge_out"]) * count
    return {"input_tokens": round(tin), "output_tokens": round(tout)}


# --------------------------------------------------------------------------

def render_markdown(r: dict) -> str:
    w, t = r["work"], r["totals"]
    L = [
        f"# Compute estimate — {w['title']}",
        "",
        f"{w['scenes']} scenes, {w['source_chars']:,} source characters "
        f"= {w['source_tokens']:,} tokens (measured).",
        f"{w['artifacts']} artifacts + {w['hindsight_traces']} hindsight traces "
        f"= {w['nodes_total']} nodes.",
        f"Parameters: {r['parameters']['author_rounds']} author rounds, "
        f"{r['parameters']['judge_rounds']} judge rounds, "
        f"revision scale {r['parameters']['revision_scale']}, "
        f"thinking {r['parameters']['thinking']}.",
        "",
        "## Totals",
        "",
        "| | calls | input tokens | output tokens |",
        "|---|---:|---:|---:|",
        f"| author | {r['totals']['calls']:,} total | "
        f"{t['author_input_tokens']:,} | {t['author_output_tokens']:,} |",
        f"| judge | | {t['judge_input_tokens']:,} | {t['judge_output_tokens']:,} |",
        f"| **all** | **{t['calls']:,}** | **{t['input_tokens']:,}** | "
        f"**{t['output_tokens']:,}** |",
        "",
        f"Generated tokens with hidden reasoning ON: "
        f"**{t['generated_tokens_thinking_on']:,}** "
        f"({1/(1-val(M,'reasoning_share')):.2f}x).",
        "",
        "## Per layer",
        "",
        "| layer | n | author calls | author in | author out | judge in | judge out |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in r["layers"]:
        lt = row["layer_total"]
        L.append(f"| {row['layer']} | {row['count']} | {lt['author_calls']:,.0f} | "
                 f"{lt['author_in']:,.0f} | {lt['author_out']:,.0f} | "
                 f"{lt['judge_in']:,.0f} | {lt['judge_out']:,.0f} |")
    o = r["opus_judge"]
    L += [
        "",
        "## Opus 5 as judge",
        "",
        f"- input {o['input_tokens']:,}, output {o['output_tokens']:,}",
        f"- **${o['usd_uncached']:,.2f}** without prompt caching",
        f"- **${o['usd_with_prompt_caching']:,.2f}** with prompt caching "
        f"({o['cache_read_tokens']:,} tokens served from cache)",
        "",
        "## Wall clock",
        "",
    ]
    wc = r["wallclock"]
    for scope, block in (("Qwen author only", wc["author_only"]),
                         ("Qwen author + Qwen judge", wc["author_and_judge_both_qwen"])):
        L.append(f"**{scope}** (thinking {wc['thinking']})")
        for k, v in block.items():
            L.append(f"  - {k.replace('_', ' ')}: {v} h")
    L += ["", "## GPU hours", ""]
    for k, v in r["hardware"]["a100"].items():
        L.append(f"- A100 x8, {k}: {v['wall_hours']} h wall, {v['gpu_hours']} GPU-hours")
    for k, v in r["hardware"]["b200"].items():
        if isinstance(v, dict):
            L.append(f"- B200 {k}: {v['wall_hours']} h wall, {v['gpu_hours']} GPU-hours "
                     f"({v['scripts_in_parallel']} scripts in parallel)")
    L += ["", "## Sensitivity", "",
          "| variant | input | output |", "|---|---:|---:|"]
    for k, v in r["sensitivity"].items():
        L.append(f"| {k} | {v['input_tokens']:,} | {v['output_tokens']:,} |")
    return "\n".join(L)


if __name__ == "__main__":
    print(render_markdown(build()))
