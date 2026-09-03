#!/usr/bin/env python3
"""Pilot: hindsight/rationalized chain-of-thought synthesis for the plot
layer. For each of 5 known-good (PASS) plots, generate 3 candidate CoT
traces via Muse Spark that work BACKWARD from the target plot (given full
context: meta dilemma/questions, event digest, entity profiles) to produce
a plausible forward-looking derivation -- then judge each candidate with a
3-judge panel on 5 dimensions, reporting per-candidate panel mean/stdev."""
import json, sys, statistics, random
import config
config.install_paths()
import meta_layer as ml  # noqa: E402
from screenplay_ku.client import EndpointPool  # noqa: E402
from screenplay_ku.kuschema import grammar_safe  # noqa: E402

TREES = str(config.TREES)
OUT = str(config.TRACE_OUT / "hindsight_pilot_out.json")

PILOT_TREES = [
    "awesomefilm__04385ea70696", "awesomefilm__980ff763c8f1", "dailyscript__d4b401ce409d",
    "awesomefilm__cfa9c10e8197", "dailyscript__6dbccd42cee0",
]

ALL_PORTS = [19001, 19002, 19003, 19004, 19005, 19006]
gen_pool = EndpointPool(ALL_PORTS, "muse-spark-1.2-contributor-free",
                         temperature=0.9, max_tokens=6000, timeout=900, retries=5)
judge_pool = EndpointPool(ALL_PORTS, "muse-spark-1.2-contributor-free",
                           temperature=0.6, max_tokens=2000, timeout=900, retries=5)

COT_SCHEMA = grammar_safe({
    "type": "object",
    "properties": {"reasoning": {"type": "string"}},
    "required": ["reasoning"], "additionalProperties": False})

HDIMS = ["H1_forward_plausibility", "H2_groundedness", "H3_coherence",
         "H4_genuine_derivation", "H5_coverage"]
HRUBRIC = (
    "H1 Forward plausibility - reads as reasoning discovered in the moment, "
    "not as an announcement of the answer followed by justification. "
    "H2 Groundedness - cites specific event IDs, character names or dilemma "
    "language actually present in the supplied material, not generic prose. "
    "H3 Coherence - each step follows from the previous one; no jumps or "
    "contradictions. "
    "H4 Genuine derivation - shows real inferential work (weighing which "
    "events belong, considering and rejecting alternatives) rather than "
    "quoting or paraphrasing the target summary as if that were reasoning. "
    "H5 Coverage - addresses both why this throughline/definition fits AND "
    "why this specific causal event chain follows, not only one half. "
    "Integers 1-5, hard marking.")

j_schema = grammar_safe({
    "type": "object",
    "properties": {**{d: {"type": "integer", "enum": [1, 2, 3, 4, 5]} for d in HDIMS},
                   "commentary": {"type": "string"}},
    "required": HDIMS + ["commentary"], "additionalProperties": False})

COT_SYSTEM = (
    "You are reconstructing plausible reasoning. You will be given a piece "
    "of story material and a TARGET plot analysis that a skilled analyst "
    "already produced. Your job is to write the step-by-step reasoning "
    "that analyst plausibly went through BEFORE writing the target down -- "
    "as if thinking out loud while still exploring the material, not "
    "already knowing the answer. Reference specific events, characters and "
    "the central dilemma. Consider what else could have been true and why "
    "it was ruled out. Do not simply restate or paraphrase the target's "
    "summary as your reasoning -- show the inferential steps that would "
    "lead there. End your reasoning right at the point the target becomes "
    "the obvious conclusion, but do NOT write the target's JSON out "
    "yourself. Output plain prose reasoning only, 300-600 words, no JSON, "
    "no headers. Return it as JSON: {\"reasoning\": \"<your prose>\"}.")


def build_context(slug):
    T = f"{TREES}/{slug}"
    meta = json.loads(open(f"{T}/meta/meta.json").read())
    events = json.loads(open(f"{T}/events/events.json").read())["events"]
    digest = ml.build_digest(events)
    dilemma = json.dumps(meta.get("themes", {}).get("central_dilemma", {}), ensure_ascii=False, indent=1)
    questions = json.dumps(meta.get("themes", {}).get("big_questions", []), ensure_ascii=False)[:3000]
    try:
        profiles = json.loads(open(f"{T}/entities/profiles.json").read())
        entities = json.dumps(profiles, ensure_ascii=False, indent=1)[:6000]
    except Exception:
        entities = "(none available)"
    return dilemma, questions, digest, entities


def pick_plot(slug):
    plots = json.loads(open(f"{TREES}/{slug}/plots/plots.json").read())["plots"]
    name = next(iter(plots))
    return name, plots[name]


def main():
    random.seed(11)
    pilot = []
    for slug in PILOT_TREES:
        name, plot = pick_plot(slug)
        dilemma, questions, digest, entities = build_context(slug)
        target = json.dumps(plot, ensure_ascii=False, indent=1)

        cot_user = (
            "CENTRAL DILEMMA: " + dilemma + " BIG QUESTIONS: " + questions +
            " ENTITY PROFILES: " + entities + " EVENT LAYER: " + digest[:16000] +
            " TARGET PLOT ANALYSIS (already correct, produced by the analyst "
            "-- reconstruct the reasoning that would precede it): " + target[:8000])

        print(f"[{slug}] plot='{name[:60]}' generating 3 hindsight-CoT candidates...", flush=True)
        candidates = []
        for i in range(3):
            try:
                r = gen_pool.call(COT_SYSTEM, cot_user, schema=COT_SCHEMA)
                cot_text = json.loads(r.text).get("reasoning", "").strip()
                candidates.append(cot_text)
                print(f"  candidate {i}: {len(cot_text)} chars", flush=True)
            except Exception as e:
                print(f"  candidate {i}: GEN FAILED: {e}", flush=True)
                candidates.append(None)

        cand_results = []
        for i, cot in enumerate(candidates):
            if cot is None:
                cand_results.append({"i": i, "ok": False})
                continue
            jprompt = ("Score this RECONSTRUCTED REASONING TRACE on: " + ", ".join(HDIMS) +
                       ". RUBRIC: " + HRUBRIC +
                       " CENTRAL DILEMMA: " + dilemma +
                       " EVENT LAYER (for checking groundedness): " + digest[:10000] +
                       " TARGET IT SHOULD LEAD TO: " + target[:4000] +
                       " REASONING TRACE TO SCORE: " + cot[:6000])
            panel = []
            for run in range(3):
                try:
                    jd = json.loads(judge_pool.call(ml.SYSTEM, jprompt, schema=j_schema).text)
                    scores = {d: jd[d] for d in HDIMS}
                    m = statistics.mean(scores.values())
                    panel.append(m)
                except Exception as e:
                    print(f"    judge run {run} failed: {e}", flush=True)
            if panel:
                pm = statistics.mean(panel)
                psd = statistics.stdev(panel) if len(panel) > 1 else 0.0
                cand_results.append({"i": i, "ok": True, "panel_scores": panel,
                                      "panel_mean": round(pm, 3), "panel_stdev": round(psd, 3),
                                      "cot": cot})
                print(f"  candidate {i}: panel={[round(p,2) for p in panel]} mean={pm:.2f} stdev={psd:.2f}", flush=True)
            else:
                cand_results.append({"i": i, "ok": True, "judge_failed": True, "cot": cot})

        pilot.append({"slug": slug, "plot_name": name, "candidates": cand_results})
        json.dump(pilot, open(OUT, "w"), ensure_ascii=False, indent=1)

    # summary
    print("\n=== PILOT SUMMARY ===")
    all_means, all_stdevs = [], []
    for p in pilot:
        for c in p["candidates"]:
            if c.get("ok") and "panel_mean" in c:
                all_means.append(c["panel_mean"])
                all_stdevs.append(c["panel_stdev"])
        best = max((c for c in p["candidates"] if "panel_mean" in c),
                   key=lambda c: c["panel_mean"], default=None)
        if best:
            print(f"{p['slug']:35s} best-of-3 candidate {best['i']}: mean={best['panel_mean']} stdev={best['panel_stdev']}")
    if all_means:
        print(f"\nAcross all {len(all_means)} candidates:")
        print(f"  mean of panel-means:  {statistics.mean(all_means):.3f}")
        print(f"  stdev of panel-means (candidate-to-candidate spread): {statistics.stdev(all_means):.3f}")
        print(f"  mean of panel-stdevs (typical within-panel judge disagreement): {statistics.mean(all_stdevs):.3f}")


if __name__ == "__main__":
    main()
