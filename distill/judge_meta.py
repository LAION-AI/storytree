#!/usr/bin/env python3
"""Judge the meta layer against distill/rubrics/meta.json.

One judge pass per run (the panel lives in judge_events.py if a full A/B is
needed later; here the artifact is absolute, not comparative). The judge gets
the meta layer, the event digest it claims to describe, and the rubric --
nothing else. Scores are integers 1-5 with one evidence clause each.

Usage:
  python3 distill/judge_meta.py --meta runs/meta_layer/meta.json \
      --events runs/events_build10_full/events.json \
      --out runs/meta_layer/judgement.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, "/home/deployer/laion/project-alexandria/screenplay/src")
from screenplay_ku.client import EndpointPool  # noqa: E402
from screenplay_ku.kuschema import grammar_safe  # noqa: E402

DIMENSIONS = ["M1", "M2", "M3", "M4", "M5", "M6"]

SYSTEM = (
    "You are an independent judge of a story-analysis artifact. You work "
    "only from the artifact and the event layer you are given; general "
    "knowledge of the work must not leak into your scoring. You return only "
    "valid JSON.")


def load_rubric() -> str:
    p = Path(__file__).resolve().parent / "rubrics" / "meta.json"
    r = json.loads(p.read_text(encoding="utf-8"))
    lines = ["POSTURE: " + r["posture"], ""]
    for d in r["dimensions"]:
        lines.append("{} — {}".format(d["id"], d["name"]))
        for anchor in ("1", "3", "5"):
            lines.append("  {}: {}".format(anchor, d["anchors"][anchor]))
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--meta", required=True)
    ap.add_argument("--events", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--ports", default="8110,8111")
    ap.add_argument("--model", default="ornith-1.5-397b")
    a = ap.parse_args()

    meta = json.loads(Path(a.meta).read_text(encoding="utf-8"))
    events = json.loads(Path(a.events).read_text(encoding="utf-8"))["events"]
    digest = "\n".join(
        "### {} — {} [{}]\nparticipants: {}\n{}".format(
            e["event_id"], e.get("title"),
            ", ".join(e.get("scene_ids") or []),
            ", ".join((e.get("participants") or [])[:10]),
            (e.get("summary") or "")[:380])
        for e in events)

    rubric = load_rubric()
    pool = EndpointPool([int(p) for p in a.ports.split(",")], a.model,
                        temperature=0.3, max_tokens=6000, timeout=1800)

    schema = grammar_safe({
        "type": "object",
        "properties": {d: {"type": "integer", "enum": [1, 2, 3, 4, 5]}
                       for d in DIMENSIONS},
        "evidence": {"type": "object",
                     "properties": {d: {"type": "string"} for d in DIMENSIONS},
                     "required": sorted(DIMENSIONS),
                     "additionalProperties": False},
        "commentary": {"type": "string"},
        "required": sorted(DIMENSIONS) + ["evidence", "commentary"],
        "additionalProperties": False,
    })

    prompt = "\n\n".join([
        "Score this META LAYER on all six dimensions.\n\n"
        "SCORING: integers 1-5 per the anchors; one evidence clause per "
        "dimension naming the exact claim or pointer it rests on. Where both "
        "arms... there are no arms: score AS DELIVERED.",
        "=== RUBRIC ===\n" + rubric,
        "=== GROUND TRUTH: THE EVENT LAYER ===\n" + digest[:80000],
        "=== ARTIFACT UNDER JUDGEMENT ===\n" +
        json.dumps(meta, ensure_ascii=False, indent=1)[:60000],
        "Return the scores now.",
    ])

    r = pool.call(SYSTEM, prompt, schema=schema)
    result = json.loads(r.text)
    scores = {d: result[d] for d in DIMENSIONS}
    import statistics
    mean = statistics.mean(scores.values())
    worst = min(scores.values())
    out = {
        "judge": "meta_judge_ornith",
        "scores": scores,
        "mean": round(mean, 3),
        "weakest_dimension": min(scores, key=scores.get),
        "gate": "PASS" if mean >= 4.0 and worst >= 3 else "FAIL",
        "evidence": result.get("evidence"),
        "commentary": result.get("commentary"),
    }
    Path(a.out).write_text(json.dumps(out, indent=1, ensure_ascii=False),
                           encoding="utf-8")
    print("{} | mean {} | weakest {} ({}) -> {}".format(
        out["gate"], out["mean"], out["weakest_dimension"],
        scores[out["weakest_dimension"]], a.out))
    print(json.dumps(scores, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
