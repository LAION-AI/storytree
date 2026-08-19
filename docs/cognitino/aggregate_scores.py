#!/usr/bin/env python3
"""Aggregate blind rubric scores and un-blind them against the withheld key.

Reports per-arm means on the six dimensions used for V0-V5, so the numbers are comparable
with `docs/14-rubric-scores-and-next-steps.md`. Also runs a paired bootstrap over scenes,
because the previous scene-layer comparisons had no significance test at all and their
standing caveat is that within-condition variance was never measured.
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from statistics import mean

DIMS = ["fidelity", "completeness", "specificity", "change_reality",
        "emotional_intelligence", "calibration"]


def load_scores(paths):
    rows = []
    for path in paths:
        p = Path(path)
        if not p.exists():
            print("missing: {}".format(path))
            continue
        try:
            payload = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            print("unparsed {}: {}".format(path, error))
            continue
        for entry in payload.get("scores") or []:
            for arm, body in (entry.get("arms") or {}).items():
                dims = body.get("dims") or {}
                rows.append({"scene_id": entry.get("scene_id"), "arm": arm,
                             "dims": {d: dims.get(d) for d in DIMS},
                             "words": entry.get("scene_words")})
    return rows


def paired_bootstrap(rows, arm_a, arm_b, iterations=20000, seed=11):
    by_scene = {}
    for row in rows:
        by_scene.setdefault(row["scene_id"], {})[row["arm"]] = row
    scenes = [s for s, arms in by_scene.items() if arm_a in arms and arm_b in arms]
    diffs = []
    for scene in scenes:
        a = [v for v in by_scene[scene][arm_a]["dims"].values() if v is not None]
        b = [v for v in by_scene[scene][arm_b]["dims"].values() if v is not None]
        if a and b:
            diffs.append(mean(a) - mean(b))
    if not diffs:
        return None
    rng = random.Random(seed)
    boots = []
    for _ in range(iterations):
        sample = [diffs[rng.randrange(len(diffs))] for _ in range(len(diffs))]
        boots.append(mean(sample))
    boots.sort()
    low, high = boots[int(0.025 * iterations)], boots[int(0.975 * iterations)]
    p = 2 * min(sum(1 for x in boots if x <= 0), sum(1 for x in boots if x >= 0)) / iterations
    return {"n_scenes": len(diffs), "diff": round(mean(diffs), 3),
            "ci95": [round(low, 3), round(high, 3)], "p": round(p, 4)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scores", nargs="+", required=True)
    parser.add_argument("--key", required=True, help="withheld arm->system mapping")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    rows = load_scores(args.scores)
    key = json.loads(Path(args.key).read_text(encoding="utf-8"))["key"]

    arms = sorted({r["arm"] for r in rows})
    table = {}
    for arm in arms:
        subset = [r for r in rows if r["arm"] == arm]
        per_dim = {}
        for dim in DIMS:
            values = [r["dims"][dim] for r in subset if r["dims"].get(dim) is not None]
            per_dim[dim] = round(mean(values), 2) if values else None
        overall = [v for r in subset for v in r["dims"].values() if v is not None]
        scene_means = [mean([v for v in r["dims"].values() if v is not None])
                       for r in subset if any(v is not None for v in r["dims"].values())]
        cleared = sum(1 for r in subset
                      if all(v is not None and v >= 3 for v in r["dims"].values())
                      and mean([v for v in r["dims"].values()]) >= 4.0)
        table[arm] = {"system": key.get(arm, "?"), "n_scenes": len(subset),
                      "per_dimension": per_dim,
                      "overall": round(mean(overall), 2) if overall else None,
                      "worst_dimension": min((d for d in DIMS if per_dim[d] is not None),
                                             key=lambda d: per_dim[d], default=None),
                      "scenes_clearing_bar": cleared,
                      "scene_means": [round(x, 2) for x in scene_means]}

    cognitino_arm = next((a for a, v in key.items() if v == "cognitino"), None)
    comparisons = {}
    if cognitino_arm:
        for arm in arms:
            if arm == cognitino_arm:
                continue
            result = paired_bootstrap(rows, cognitino_arm, arm)
            if result:
                comparisons["cognitino vs {}".format(key.get(arm))] = result

    report = {"dimensions": DIMS, "arms": table, "comparisons": comparisons,
              "bar": "mean >= 4.0 and no dimension below 3.0"}
    Path(args.out).write_text(json.dumps(report, indent=1), encoding="utf-8")

    print("\n{:<12} {:<11} {:>6} {:>7} {:>7} {:>7} {:>7} {:>7} {:>7} {:>6}".format(
        "arm", "system", "n", "fid", "compl", "spec", "chg", "emo", "calib", "MEAN"))
    for arm in arms:
        t = table[arm]
        d = t["per_dimension"]
        print("{:<12} {:<11} {:>6} {:>7} {:>7} {:>7} {:>7} {:>7} {:>7} {:>6}".format(
            arm, t["system"], t["n_scenes"],
            *[("-" if d[k] is None else d[k]) for k in DIMS], t["overall"]))
    print("\nbar (mean>=4.0, no dim<3.0) cleared on:")
    for arm in arms:
        print("  {:<12} {:<11} {} of {} scenes".format(
            arm, table[arm]["system"], table[arm]["scenes_clearing_bar"], table[arm]["n_scenes"]))
    if comparisons:
        print("\npaired bootstrap over scenes:")
        for name, c in comparisons.items():
            verdict = "significant" if (c["ci95"][0] > 0 or c["ci95"][1] < 0) else "n.s."
            print("  {:<28} diff={:+.3f} CI95[{:+.3f},{:+.3f}] p={:.4f}  {}".format(
                name, c["diff"], c["ci95"][0], c["ci95"][1], c["p"], verdict))
    print("\nwrote {}".format(args.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
