#!/usr/bin/env python3
"""Scaled hindsight/rationalized CoT generation for the plot layer, across
all PASS trees under the relaxed threshold (mean>=3.5, min_dim>=2.75).
Best-of-1 per plot; only if the 3-judge panel mean is <4 does it retry
generation (fresh candidate) up to 5 attempts total, keeping the
best-scoring attempt seen."""
import json, sys, statistics, concurrent.futures as cf
import config
config.install_paths()
import meta_layer as ml  # noqa: E402
from screenplay_ku.client import EndpointPool  # noqa: E402
from screenplay_ku.kuschema import grammar_safe  # noqa: E402

TREES = str(config.TREES)
OUT = str(config.TRACE_OUT / "hindsight_scale_out.json")
SLUGS_FILE = str(config.TRACE_OUT / "relaxed_pass_slugs.json")
MAX_ATTEMPTS = 5
TARGET = 4.0
WORKERS = 10

ALL_PORTS = [19001, 19002, 19003, 19004, 19005, 19006, 19007, 19008, 19009, 19010]
gen_pool = EndpointPool(ALL_PORTS, "muse-spark-1.2-contributor-free",
                         temperature=0.9, max_tokens=6000, timeout=900, retries=6)
judge_pool = EndpointPool(ALL_PORTS, "muse-spark-1.2-contributor-free",
                           temperature=0.6, max_tokens=2000, timeout=900, retries=6)

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


def judge_candidate(cot, dilemma, digest, target):
    jprompt = ("Score this RECONSTRUCTED REASONING TRACE on: " + ", ".join(HDIMS) +
               ". RUBRIC: " + HRUBRIC +
               " CENTRAL DILEMMA: " + dilemma +
               " EVENT LAYER (for checking groundedness): " + digest[:10000] +
               " TARGET IT SHOULD LEAD TO: " + target[:4000] +
               " REASONING TRACE TO SCORE: " + cot[:6000])
    panel = []
    for _ in range(3):
        try:
            jd = json.loads(judge_pool.call(ml.SYSTEM, jprompt, schema=j_schema).text)
            scores = {d: jd[d] for d in HDIMS}
            panel.append(statistics.mean(scores.values()))
        except Exception:
            pass
    if not panel:
        return None, None
    return round(statistics.mean(panel), 3), round(statistics.stdev(panel) if len(panel) > 1 else 0.0, 3)


def process_one(slug):
    try:
        name, plot = pick_plot(slug)
        dilemma, questions, digest, entities = build_context(slug)
        target = json.dumps(plot, ensure_ascii=False, indent=1)
        cot_user = (
            "CENTRAL DILEMMA: " + dilemma + " BIG QUESTIONS: " + questions +
            " ENTITY PROFILES: " + entities + " EVENT LAYER: " + digest[:16000] +
            " TARGET PLOT ANALYSIS (already correct, produced by the analyst "
            "-- reconstruct the reasoning that would precede it): " + target[:8000])

        attempts_log = []
        best = None
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                r = gen_pool.call(COT_SYSTEM, cot_user, schema=COT_SCHEMA)
                cot = json.loads(r.text).get("reasoning", "").strip()
            except Exception as e:
                attempts_log.append({"attempt": attempt, "gen_error": str(e)})
                continue
            pm, psd = judge_candidate(cot, dilemma, digest, target)
            attempts_log.append({"attempt": attempt, "panel_mean": pm, "panel_stdev": psd})
            if pm is not None and (best is None or pm > best["panel_mean"]):
                best = {"panel_mean": pm, "panel_stdev": psd, "cot": cot, "attempt": attempt}
            if pm is not None and pm >= TARGET:
                break
        status = "ok" if best is not None else "no_valid_candidate"
        result = {"slug": slug, "plot_name": name, "status": status,
                  "n_attempts": len(attempts_log), "attempts_log": attempts_log,
                  "best": best}
        tag = "REACHED>=4" if best and best["panel_mean"] >= TARGET else "CAPPED<4" if best else "FAILED"
        print(f"[{slug}] {tag} best_mean={best['panel_mean'] if best else None} "
              f"in {len(attempts_log)} attempt(s)", flush=True)
        return result
    except Exception as e:
        print(f"[{slug}] FATAL: {e}", flush=True)
        return {"slug": slug, "status": "fatal_error", "error": str(e)}


def main():
    slugs = json.load(open(SLUGS_FILE))
    print(f"Processing {len(slugs)} PASS trees (relaxed threshold), best-of-1, retry<4 up to {MAX_ATTEMPTS}x, {WORKERS} workers", flush=True)
    results = []
    with cf.ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = {ex.submit(process_one, s): s for s in slugs}
        for fut in cf.as_completed(futs):
            results.append(fut.result())
            json.dump(results, open(OUT, "w"), ensure_ascii=False, indent=1)
            print(f"  progress: {len(results)}/{len(slugs)}", flush=True)

    print("\n=== SCALE SUMMARY ===")
    ok = [r for r in results if r.get("status") == "ok"]
    reached = [r for r in ok if r["best"]["panel_mean"] >= TARGET]
    capped = [r for r in ok if r["best"]["panel_mean"] < TARGET]
    failed = [r for r in results if r.get("status") != "ok"]
    means = [r["best"]["panel_mean"] for r in ok]
    attempt_counts = [r["n_attempts"] for r in ok]
    print(f"total trees: {len(slugs)}")
    print(f"ok (got >=1 valid candidate): {len(ok)}")
    print(f"reached target (>=4.0): {len(reached)}  ({len(reached)/len(slugs)*100:.1f}%)")
    print(f"capped below 4.0 after {MAX_ATTEMPTS} attempts: {len(capped)}")
    print(f"failed (no valid candidate / fatal): {len(failed)}")
    if means:
        print(f"mean of best panel-means: {statistics.mean(means):.3f}")
        print(f"stdev of best panel-means: {statistics.stdev(means):.3f}" if len(means) > 1 else "")
    if attempt_counts:
        print(f"avg attempts used: {statistics.mean(attempt_counts):.2f}")
        from collections import Counter
        print("attempts distribution:", dict(Counter(attempt_counts)))
    if capped:
        print("\ntrees still <4.0 after retries:")
        for r in sorted(capped, key=lambda r: r["best"]["panel_mean"]):
            print(f"  {r['slug']:35s} mean={r['best']['panel_mean']} attempts={r['n_attempts']}")
    if failed:
        print("\nfailed trees:")
        for r in failed:
            print(f"  {r['slug']:35s} status={r.get('status')} err={r.get('error')}")


if __name__ == "__main__":
    main()
