#!/usr/bin/env python3
"""Cross-layer consistency check: root.dramatic_structure vs. the drama layer.

Both layers describe the same thing. The story root has always carried a
coarse `dramatic_structure` (act count + a handful of turning points, each
with a free-text `where` that usually names event and scene ids). The drama
structure layer (docs/20-drama-structure-layer.md) produces a controlled,
audited version of the same analysis.

When the two are built independently -- which is the default, since feeding
the drama layer to root is opt-in behind DRAMA_TO_UPPER=1 -- they can
disagree. This script measures that disagreement, which is rubric dimension
6 ("cross-layer consistency") from docs/18-dramatic-structure-extension.md.

It reports, without judging:
  * act count on each side;
  * for every root turning point, the event ids its `where` text names, and
    whether a drama anchor covers any of them;
  * drama anchors the root does not mention at all;
  * how far apart the two are in screen position where both locate a beat.

A high overlap is evidence the drama layer is describing the same film the
rest of the tree describes. A low overlap is a flag to inspect, not proof
that either side is wrong -- the root names ~5 beats, the drama layer names
up to 14, so the root being a subset is the expected healthy case.

Usage:
  python3 tools/compare_root_vs_drama.py \
      --root runs/story_root_v3/story_root.json \
      --drama runs/drama_matrix/drama_structure.json
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Set

EV_RE = re.compile(r"\bev-\d{3,}\b")
SC_RE = re.compile(r"\bsc-\d{3,}\b")


def root_turning_points(root: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Pull the root's turning points, with the ids their text names."""
    ds = root.get("dramatic_structure") or {}
    out = []
    for tp in ds.get("turning_points") or []:
        blob = "{} {}".format(tp.get("name", ""), tp.get("where", ""))
        out.append({
            "name": tp.get("name", ""),
            "where": tp.get("where", ""),
            "events": set(EV_RE.findall(blob)),
            "scenes": set(SC_RE.findall(blob)),
        })
    return out


def compare(root: Dict[str, Any], drama: Dict[str, Any]) -> Dict[str, Any]:
    tps = root_turning_points(root)
    anchors = drama.get("anchors") or []
    anchor_events: List[Set[str]] = [set(a.get("event_ids") or [])
                                     for a in anchors]

    matched_anchor_idx: Set[int] = set()
    rows = []
    for tp in tps:
        hit = None
        for i, evs in enumerate(anchor_events):
            if tp["events"] & evs:
                hit = i
                matched_anchor_idx.add(i)
                break
        rows.append({
            "root_point": tp["name"],
            "root_events": sorted(tp["events"]),
            "drama_anchor": (anchors[hit]["id"] + " " + anchors[hit]["kind"])
                            if hit is not None else None,
            "drama_position": anchors[hit].get("screen_position")
                              if hit is not None else None,
        })

    unmatched = [{"id": a.get("id"), "kind": a.get("kind"),
                  "events": a.get("event_ids"),
                  "position": a.get("screen_position")}
                 for i, a in enumerate(anchors) if i not in matched_anchor_idx]

    # A raw act count misleads: a three-act analysis routinely carries a
    # closing denouement/coda band, so `len(acts)` reads 4 while the lens
    # says three_act. Report the labels too, and count coda bands apart, so
    # a difference of one is visibly explained rather than looking like a
    # contradiction between the layers.
    CODA = ("denouement", "coda", "epilogue", "aftermath")
    acts_list = drama.get("acts") or []
    coda = [x for x in acts_list
            if any(w in (x.get("label") or "").lower() for w in CODA)]
    root_acts = (root.get("dramatic_structure") or {}).get("act_count")
    return {
        "act_count": {"root": root_acts, "drama": len(acts_list),
                      "drama_excluding_coda": len(acts_list) - len(coda)},
        "act_labels": [x.get("label") for x in acts_list],
        "primary_lens": (drama.get("analysis_scope") or {}).get("primary_lens"),
        "root_points": len(tps),
        "drama_anchors": len(anchors),
        "matched": sum(1 for r in rows if r["drama_anchor"]),
        "rows": rows,
        "anchors_root_does_not_name": unmatched,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--drama", required=True)
    ap.add_argument("--json", action="store_true", help="machine-readable")
    a = ap.parse_args()

    root = json.loads(Path(a.root).read_text(encoding="utf-8"))
    drama = json.loads(Path(a.drama).read_text(encoding="utf-8"))
    rep = compare(root, drama)

    if a.json:
        print(json.dumps(rep, indent=1, ensure_ascii=False))
        return 0

    ac = rep["act_count"]
    extra = ("" if ac["drama"] == ac["drama_excluding_coda"]
             else " ({} + {} coda band(s))".format(
                 ac["drama_excluding_coda"],
                 ac["drama"] - ac["drama_excluding_coda"]))
    print("lens: {} | acts: root says {}, drama says {}{}".format(
        rep["primary_lens"], ac["root"], ac["drama"], extra))
    print("      drama acts: {}".format(" / ".join(
        str(l) for l in rep["act_labels"])))
    print("root turning points: {} | drama anchors: {} | matched: {}\n".format(
        rep["root_points"], rep["drama_anchors"], rep["matched"]))
    for r in rep["rows"]:
        mark = "OK " if r["drama_anchor"] else "-- "
        pos = ("  @{:.0%}".format(r["drama_position"])
               if r["drama_position"] is not None else "")
        print("{}{}".format(mark, r["root_point"][:70]))
        print("     root cites {} -> {}{}".format(
            ", ".join(r["root_events"]) or "no event id",
            r["drama_anchor"] or "NO MATCHING ANCHOR", pos))
    if rep["anchors_root_does_not_name"]:
        print("\nanchors the root does not name ({}):".format(
            len(rep["anchors_root_does_not_name"])))
        for u in rep["anchors_root_does_not_name"]:
            print("   {} {:26s} {}  @{}".format(
                u["id"], u["kind"], ",".join(u["events"] or []),
                "{:.0%}".format(u["position"]) if u["position"] is not None
                else "?"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
