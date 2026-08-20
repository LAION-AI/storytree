#!/usr/bin/env python3
"""Lint an event-layer build and prepare its blind evaluation pack.

One script for every build, so comparisons are not confounded by the measurement changing
between them. It does two things and refuses to do more:

  * **lint** — every defect class a machine can decide, counted, and normalised per register
    entry so builds with different node counts stay comparable. A raw count of placeholders
    falls simply by writing fewer registers.
  * **pack** — the same twelve events (matched across builds by scene overlap, since
    segmentation shifts between builds), batched for three judges, with the answer key
    written somewhere the judges are never pointed at.

Usage:
  python3 distill/eval_events.py --events runs/events_build3/events.json \\
      --scenes-dir runs/scenes_ornith_v5 --out /tmp/pack3 --compare runs/events_ornith/events.json
"""

from __future__ import annotations

import argparse
import glob
import importlib.util
import json
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

_spec = importlib.util.spec_from_file_location(
    "_el", str(Path(__file__).resolve().parent / "event_layer.py"))
_el = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_el)

# The reference sample, defined by the scenes each event covers rather than by event id.
# Segmentation shifts between builds, so an id is not stable across them but a scene span is.
REFERENCE_SPANS = [
    "sc-014", "sc-035", "sc-075", "sc-080", "sc-090",
    "sc-102", "sc-116", "sc-121", "sc-130", "sc-173", "sc-208", "sc-223",
]


def load_scenes(directory: str) -> Dict[str, Dict[str, Any]]:
    out = {}
    for path in glob.glob(str(Path(directory) / "sc-*.json")):
        node = json.loads(Path(path).read_text(encoding="utf-8"))
        out[node.get("scene_id") or Path(path).stem] = node
    return out


def normalised_lint(events: Sequence[Dict[str, Any]],
                    scenes: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    report = _el.lint(list(events), scenes)
    slots = sum(1 for e in events for t in e.get("state_triples") or []
                for _n, _s in _el._iter_registers(t))
    triples = sum(len(e.get("state_triples") or []) for e in events)
    out = {k: v for k, v in report.items() if k != "examples"}
    out["register_slots"] = slots
    out["state_triples"] = triples
    out["events"] = len(events)
    # Per-100-slot rates. Raw counts reward a build that simply writes less, which is the
    # opposite of what any of these checks is asking about.
    for key in ("placeholder_entries", "conceding_unchanged", "unmoved_with_exit",
                "moved_but_identical", "entity_absent_from_evidence_scene"):
        out["{}_per100".format(key)] = round(100 * report.get(key, 0) / slots, 2) if slots else None
    out["examples"] = report.get("examples", [])[:8]
    return out


def pick_reference_events(events: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """One event per reference span: whichever covers that scene."""
    picked, seen = [], set()
    for anchor in REFERENCE_SPANS:
        for event in events:
            if anchor in (event.get("scene_ids") or []) and event["event_id"] not in seen:
                picked.append(event)
                seen.add(event["event_id"])
                break
    return picked


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--events", required=True)
    ap.add_argument("--scenes-dir", default="runs/scenes_ornith_v5")
    ap.add_argument("--out", default="")
    ap.add_argument("--compare", default="", help="an earlier build's events.json")
    ap.add_argument("--rubric", default="/tmp/claude-1001/-home-deployer-laion-bookwriter/149ab362-811a-4ce9-b02f-2ebe0a244656/scratchpad/rubric_event.txt")
    ap.add_argument("--batches", type=int, default=3)
    a = ap.parse_args()

    scenes = load_scenes(a.scenes_dir)
    events = json.loads(Path(a.events).read_text(encoding="utf-8"))["events"]
    here = normalised_lint(events, scenes)

    print("LINT — {} ({} events, {} triples, {} register slots)".format(
        a.events, here["events"], here["state_triples"], here["register_slots"]))
    rows = ["placeholder_entries", "missing_registers", "conceding_unchanged",
            "unmoved_with_exit", "moved_but_identical",
            "entity_absent_from_evidence_scene", "quotes_outside_reading",
            "participants_mismatch"]
    if a.compare:
        other = normalised_lint(
            json.loads(Path(a.compare).read_text(encoding="utf-8"))["events"], scenes)
        print("\n  {:<38} {:>10} {:>10}".format("", Path(a.compare).parent.name,
                                                Path(a.events).parent.name))
        for key in rows:
            print("  {:<38} {:>10} {:>10}".format(key, other.get(key, "-"), here.get(key, "-")))
        print("\n  per 100 register slots:")
        for key in rows[:1] + rows[2:6]:
            k = key + "_per100"
            if k in here:
                print("  {:<38} {:>10} {:>10}".format(key, other.get(k, "-"), here.get(k, "-")))
    else:
        for key in rows:
            print("  {:<38} {:>10}".format(key, here.get(key, "-")))

    if a.out:
        out = Path(a.out)
        out.mkdir(parents=True, exist_ok=True)
        picked = pick_reference_events(events)
        print("\nreference events matched: {} of {}".format(len(picked), len(REFERENCE_SPANS)))
        per = max(1, -(-len(picked) // a.batches))
        for i in range(a.batches):
            chunk = picked[i * per:(i + 1) * per]
            if chunk:
                (out / "batch{}.json".format(i + 1)).write_text(
                    json.dumps({"events": chunk}, indent=1), encoding="utf-8")
                print("  batch{}: {}".format(i + 1, ", ".join(e["event_id"] for e in chunk)))
        if Path(a.rubric).exists():
            shutil.copy(a.rubric, out / "rubric.txt")
        (out / "lint.json").write_text(json.dumps(here, indent=1), encoding="utf-8")
        print("wrote {}".format(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
