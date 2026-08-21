#!/usr/bin/env python3
"""Build a BLIND evaluation pack for two event-layer builds.

Blind by construction, for the reason recorded in the handshake: the first
evaluation in this project was not blind, and when it was repeated blind every
configuration dropped about 0.4 and the bar that had been reported as cleared
turned out never to have been cleared by anything.

  * Builds are relabelled `arm-A` / `arm-B` under a shuffle keyed by a seed. The
    key goes to a **separate directory** the judges are never pointed at -- an
    earlier run left KEY.json beside the batches and two of three judges saw it.
  * Every field that could name the build is stripped.
  * Arm order inside each pairing is shuffled per anchor, so position carries no
    signal either.
  * Events are paired by **scene anchor**, never by event id: segmentation moves
    between builds (57 vs 59 proposed), so an id names different material.

Blinding is label-level, not perfect. A build that has been through the
paraphrase pass reads slightly differently from one that has not, and a careful
judge could infer direction from that. Hiding it would mean hiding a property
under evaluation, so it stays and the limitation is disclosed.

Usage:
  python3 distill/build_event_eval_pack.py --a runs/events_build3/events.json \\
      --b runs/events_build4/events.json --out /tmp/pack --key-out /tmp/pack_key
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

# Bookkeeping the pipeline writes, and process traces that would identify a build.
DROP = {"_context_fit", "_roster", "prose_before_reconcile", "entry_source",
        "exit_source", "exit_asserted", "entry_asserted", "_variant", "variant",
        "arm", "_arm", "provenance", "schema_version", "event_hint",
        "working_title", "why_here"}


def strip(value):
    if isinstance(value, dict):
        return {k: strip(v) for k, v in value.items() if k not in DROP}
    if isinstance(value, list):
        return [strip(v) for v in value]
    return value


def load(path: str) -> List[Dict[str, Any]]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return data["events"] if isinstance(data, dict) else data


def by_anchor(events: Sequence[Dict[str, Any]], anchor: str) -> Optional[Dict[str, Any]]:
    for event in events:
        if anchor in (event.get("scene_ids") or []):
            return event
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", required=True)
    ap.add_argument("--b", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--key-out", required=True)
    ap.add_argument("--anchors", default="")
    ap.add_argument("--seed", type=int, default=20260821)
    ap.add_argument("--batches", type=int, default=3)
    ap.add_argument("--scenes-dir", default="runs/scenes_ornith_v5")
    a = ap.parse_args()

    left, right = load(a.a), load(a.b)
    anchors = [x.strip() for x in a.anchors.split(",") if x.strip()]
    if not anchors:
        shared = set()
        for events in (left, right):
            covered = {s for e in events for s in e.get("scene_ids") or []}
            shared = covered if not shared else (shared & covered)
        anchors = sorted(shared)[::max(1, len(shared) // 12)][:12]

    rng = random.Random(a.seed)
    out, key_out = Path(a.out), Path(a.key_out)
    out.mkdir(parents=True, exist_ok=True)
    key_out.mkdir(parents=True, exist_ok=True)

    pairings, key = [], []
    for anchor in anchors:
        one, two = by_anchor(left, anchor), by_anchor(right, anchor)
        if not one or not two:
            print("  {}: missing in {}".format(
                anchor, "A" if not one else "B"))
            continue
        # Which build gets which label is decided per pairing, so a judge who
        # guesses one cannot carry the guess to the next.
        flip = rng.random() < 0.5
        first, second = (two, one) if flip else (one, two)
        first_src, second_src = ("B", "A") if flip else ("A", "B")
        pairings.append({
            "pairing_id": "pair-{:02d}".format(len(pairings) + 1),
            "anchor_scene": anchor,
            "arm-A": strip(first),
            "arm-B": strip(second),
        })
        key.append({"pairing_id": pairings[-1]["pairing_id"], "anchor_scene": anchor,
                    "arm-A": {"A": a.a, "B": a.b}[first_src],
                    "arm-B": {"A": a.a, "B": a.b}[second_src]})

    per = max(1, -(-len(pairings) // a.batches))
    for i in range(a.batches):
        chunk = pairings[i * per:(i + 1) * per]
        if chunk:
            (out / "batch{}.json".format(i + 1)).write_text(
                json.dumps({"pairings": chunk}, indent=1, ensure_ascii=False),
                encoding="utf-8")
            print("  batch{}: {}".format(
                i + 1, ", ".join(p["pairing_id"] + "@" + p["anchor_scene"] for p in chunk)))

    (key_out / "KEY.json").write_text(json.dumps({"seed": a.seed, "key": key}, indent=1),
                                      encoding="utf-8")
    print("\n{} pairing(s) over {} anchors".format(len(pairings), len(anchors)))
    print("pack -> {}\nkey  -> {}  (never give this to a judge)".format(out, key_out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
