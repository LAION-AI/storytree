#!/usr/bin/env python3
"""3-judge GLM-5.3 panel over root / plots / expose, two arms.

Re-runs the EXACT judge prompts of root_layer / plot_layer / expose_layer
(same rubrics RT1-10, P1-P5, X1-X9, same context construction) with a panel
of three independent judges on the Muse/GLM endpoints, and averages.

Arms are anonymised: the judge sees only the artifact, never its origin.
Every call's wall time is recorded; the shim additionally logs upstream
timing to runs/muse_timing.jsonl.

Usage:
  python3 tools/glm_panel_judge.py --out runs/glm53_panel \
      --ports 8222,8223,8224 --model muse-spark-1.2-contributor-free
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "distill"))
sys.path.insert(0, "/home/deployer/laion/project-alexandria/screenplay/src")
from screenplay_ku.client import EndpointPool  # noqa: E402
from screenplay_ku.kuschema import grammar_safe  # noqa: E402


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ml = _load("_ml", str(ROOT / "distill" / "meta_layer.py"))
rl = _load("_rl", str(ROOT / "distill" / "root_layer.py"))
pl = _load("_pl", str(ROOT / "distill" / "plot_layer.py"))
xl = _load("_xl", str(ROOT / "distill" / "expose_layer.py"))

ARMS = {
    "explorer_default": {  # what storytree-explorer.html serves today
        "root": "runs/story_root_v3/story_root.json",
        "plots": "runs/plot_layer_v8/plots.json",
        "expose": "runs/expose_v1/expose.json",
    },
    "muse12": {
        "root": "runs/story_root_muse/story_root.json",
        "plots": "runs/plot_layer_muse/plots.json",
        "expose": "runs/expose_muse/expose.json",
    },
}

PLOT_JUDGE_SCHEMA = grammar_safe({
    "type": "object",
    "properties": {
        **{d: {"type": "integer", "enum": [1, 2, 3, 4, 5]} for d in pl.DIMS},
        "evidence": {"type": "object",
                     "properties": {d: {"type": "string"} for d in pl.DIMS},
                     "required": pl.DIMS, "additionalProperties": False},
        "commentary": {"type": "string"}},
    "required": pl.DIMS + ["evidence", "commentary"],
    "additionalProperties": False})


def judge_prompt(layer: str, artifact: dict, digest: str) -> tuple[str, dict, list]:
    """Return (prompt, schema, dims) — byte-identical rubric text to the
    layer code so panel scores stay comparable to pipeline gates."""
    if layer == "root":
        return ("Judge this story root against each dimension, score 1-5 "
                "with a one-line note. Dimensions: " + "; ".join(rl.DIMS) +
                "\nSTORY ROOT:\n" + json.dumps(artifact, ensure_ascii=False),
                rl.JUDGE_SCHEMA, rl.DIMS)
    if layer == "plots":
        chains = artifact["plots"] if "plots" in artifact else artifact
        return ("Score this PLOT LAYER on five dimensions: "
                + ", ".join(pl.DIMS) +
                ". Integers 1-5 with one evidence clause each naming the "
                "plot or chain element it rests on. RUBRIC: " + pl.RUBRIC +
                " EVENT LAYER (ground truth): " + digest[:40000] +
                " PLOT LAYER: " + json.dumps(chains, ensure_ascii=False,
                                             indent=1)[:50000],
                PLOT_JUDGE_SCHEMA, pl.DIMS)
    if layer == "expose":
        return ("Judge this expose against each dimension, score 1-5 with a "
                "one-line note. Dimensions: " + "; ".join(xl.DIMS) +
                "\nEXPOSE:\n" + json.dumps(artifact,
                                           ensure_ascii=False)[:40000],
                xl.JUDGE_SCHEMA, xl.DIMS)
    raise ValueError(layer)


def parse_scores(layer: str, jd: dict, dims: list) -> dict:
    if layer == "plots":
        return {d: jd[d] for d in dims}
    got = {s["dim"]: s["score"] for s in jd["scores"]}
    # judges sometimes echo a shortened dim label; match by prefix code
    out = {}
    for d in dims:
        code = d.split()[0]
        out[d] = next((v for k, v in got.items()
                       if k == d or k.split()[0] == code), None)
    missing = [d for d, v in out.items() if v is None]
    if missing:
        raise ValueError("judge omitted dims: " + ", ".join(missing))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--ports", default="8222,8223,8224")
    ap.add_argument("--model", default="muse-spark-1.2-contributor-free")
    ap.add_argument("--events", default="runs/events_build10_full/events.json")
    ap.add_argument("--judges", type=int, default=3)
    ap.add_argument("--arms", default=None,
                    help="JSON {arm: {layer: path}} overriding the default arms")
    ap.add_argument("--layers", default="root,plots,expose",
                    help="comma list of layers to judge")
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    ports = [int(p) for p in a.ports.split(",")]
    arms = json.loads(a.arms) if a.arms else ARMS
    layers = [l for l in a.layers.split(",") if l]

    events = json.loads((ROOT / a.events).read_text(encoding="utf-8"))["events"]
    digest = ml.build_digest(events)

    tasks = []  # (arm, layer, judge_idx)
    for arm in arms:
        for layer in layers:
            for j in range(a.judges):
                tasks.append((arm, layer, j))

    def run_one(t):
        arm, layer, j = t
        artifact = json.loads((ROOT / arms[arm][layer]).read_text(
            encoding="utf-8"))
        prompt, schema, dims = judge_prompt(layer, artifact, digest)
        pool = EndpointPool([ports[j % len(ports)]], a.model,
                            temperature=0.5, max_tokens=8000, timeout=1800)
        t0 = time.time()
        jd = json.loads(pool.call(ml.SYSTEM, prompt, schema=schema).text)
        dur = round(time.time() - t0, 1)
        scores = parse_scores(layer, jd, dims)
        rec = {"arm": arm, "layer": layer, "judge": j, "port": ports[j % len(ports)],
               "dur_s": dur, "scores": scores,
               "mean": round(statistics.mean(scores.values()), 3),
               "raw": jd}
        (out / f"{arm}_{layer}_judge{j}.json").write_text(
            json.dumps(rec, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"{arm:17s} {layer:7s} judge{j} port {rec['port']} "
              f"mean {rec['mean']} ({dur}s)", flush=True)
        return rec

    with ThreadPoolExecutor(max_workers=len(ports)) as ex:
        recs = []
        for r in ex.map(run_one, tasks):
            recs.append(r)

    # aggregate: per (arm, layer) average over judges, per dim and overall
    summary = {}
    for arm in arms:
        summary[arm] = {}
        for layer in layers:
            rs = [r for r in recs if r["arm"] == arm and r["layer"] == layer]
            dims = sorted(rs[0]["scores"].keys()) if rs else []
            per_dim = {d: round(statistics.mean(
                [r["scores"][d] for r in rs]), 2) for d in dims}
            means = [r["mean"] for r in rs]
            panel_mean = round(statistics.mean(means), 3)
            worst_dim = min(per_dim.values()) if per_dim else None
            summary[arm][layer] = {
                "panel_mean": panel_mean,
                "judge_means": means,
                "judge_spread": round(max(means) - min(means), 3),
                "per_dim": per_dim,
                "gate": ("PASS" if panel_mean >= 4.0 and worst_dim >= 3
                         else "FAIL"),
                "durs_s": [r["dur_s"] for r in rs],
            }
    (out / "summary.json").write_text(json.dumps(
        summary, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
