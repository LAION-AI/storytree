#!/usr/bin/env python3
"""Join blind judge scores to the key and report the paired comparison.

Paired by construction: each pairing holds one node from each build covering the
same stretch of film, so the difference is taken within a pairing and the
film's own variation cancels. An unpaired comparison over nine nodes would be
dominated by which events happened to land in the sample.

Bootstrap over pairings, not over scores: the pairing is the unit that was
sampled. Resampling individual dimension scores would treat fourteen views of
one node as fourteen independent observations and produce an interval several
times too narrow.
"""

from __future__ import annotations

import argparse
import json
import random
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

DIMENSIONS = ["A", "B", "C", "D", "E", "F", "G",
              "V1", "V2", "V3", "V4", "V5", "R1", "R2"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--judges", nargs="+", required=True)
    ap.add_argument("--key", required=True)
    ap.add_argument("--label-a", default="")
    ap.add_argument("--label-b", default="")
    ap.add_argument("--out", default="")
    a = ap.parse_args()

    key = {k["pairing_id"]: k for k in json.loads(
        Path(a.key).read_text(encoding="utf-8"))["key"]}

    # build path -> per-pairing means, and per-dimension scores
    per_build_pairing: Dict[str, Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))
    per_build_dim: Dict[str, Dict[str, List[int]]] = defaultdict(lambda: defaultdict(list))
    judges_seen = []

    for path in a.judges:
        p = Path(path)
        if not p.exists():
            print("  missing: {}".format(path))
            continue
        data = json.loads(p.read_text(encoding="utf-8"))
        judges_seen.append(data.get("judge", p.parent.name))
        for pairing in data.get("pairings", []):
            pid = pairing.get("pairing_id")
            if pid not in key:
                print("  unknown pairing {}".format(pid))
                continue
            for arm in ("arm-A", "arm-B"):
                build = key[pid][arm]
                scores = (pairing.get(arm) or {}).get("scores") or {}
                values = [scores[d] for d in DIMENSIONS if isinstance(scores.get(d), (int, float))]
                if not values:
                    continue
                per_build_pairing[build][pid].append(statistics.mean(values))
                for d in DIMENSIONS:
                    if isinstance(scores.get(d), (int, float)):
                        per_build_dim[build][d].append(scores[d])

    builds = sorted(per_build_pairing)
    if len(builds) != 2:
        print("expected two builds, got {}".format(builds))
        return 2
    left, right = builds
    label = {left: a.label_a or Path(left).parent.name,
             right: a.label_b or Path(right).parent.name}

    shared = sorted(set(per_build_pairing[left]) & set(per_build_pairing[right]))
    print("judges: {} | pairings scored by both arms: {}".format(
        ", ".join(judges_seen), len(shared)))

    def mean_of(build, pid):
        return statistics.mean(per_build_pairing[build][pid])

    diffs = [mean_of(right, pid) - mean_of(left, pid) for pid in shared]

    print("\n{:<10} {:>10} {:>10} {:>10}".format("pairing", label[left], label[right], "diff"))
    for pid, d in zip(shared, diffs):
        print("{:<10} {:>10.2f} {:>10.2f} {:>+10.2f}".format(
            pid, mean_of(left, pid), mean_of(right, pid), d))

    m_left = statistics.mean([mean_of(left, p) for p in shared])
    m_right = statistics.mean([mean_of(right, p) for p in shared])
    print("{:<10} {:>10.2f} {:>10.2f} {:>+10.2f}".format(
        "MEAN", m_left, m_right, m_right - m_left))

    rng = random.Random(11)
    boots = []
    for _ in range(10000):
        sample = [diffs[rng.randrange(len(diffs))] for _ in diffs]
        boots.append(statistics.mean(sample))
    boots.sort()
    lo, hi = boots[int(0.025 * len(boots))], boots[int(0.975 * len(boots))]
    share = sum(1 for b in boots if b > 0) / len(boots)
    print("\npaired bootstrap over {} pairings, 10000 resamples".format(len(shared)))
    print("  difference {:+.2f}  95% CI [{:+.2f}, {:+.2f}]".format(
        m_right - m_left, lo, hi))
    print("  P(difference > 0) = {:.3f}".format(share))
    if lo <= 0 <= hi:
        print("  the interval contains zero: no separation at this sample size")

    print("\nper dimension (mean over all scored nodes)")
    print("  {:<6} {:>10} {:>10} {:>8}".format("dim", label[left], label[right], "diff"))
    for d in DIMENSIONS:
        l = per_build_dim[left].get(d) or []
        r = per_build_dim[right].get(d) or []
        if l and r:
            print("  {:<6} {:>10.2f} {:>10.2f} {:>+8.2f}".format(
                d, statistics.mean(l), statistics.mean(r),
                statistics.mean(r) - statistics.mean(l)))

    print("\ngate: mean >= 4.0 and no dimension < 3.0")
    for b in (left, right):
        allv = [v for d in DIMENSIONS for v in (per_build_dim[b].get(d) or [])]
        worst = min((statistics.mean(per_build_dim[b][d])
                     for d in DIMENSIONS if per_build_dim[b].get(d)), default=0)
        print("  {:<28} mean {:.2f}, weakest dimension {:.2f} -> {}".format(
            label[b], statistics.mean(allv), worst,
            "PASS" if statistics.mean(allv) >= 4.0 and worst >= 3.0 else "FAIL"))

    if a.out:
        Path(a.out).write_text(json.dumps({
            "judges": judges_seen, "pairings": shared,
            "means": {label[left]: m_left, label[right]: m_right},
            "difference": m_right - m_left, "ci95": [lo, hi],
            "p_gt_0": share,
            "per_dimension": {label[b]: {d: statistics.mean(per_build_dim[b][d])
                                         for d in DIMENSIONS if per_build_dim[b].get(d)}
                              for b in (left, right)},
        }, indent=1), encoding="utf-8")
        print("\nwrote {}".format(a.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
