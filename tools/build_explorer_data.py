#!/usr/bin/env python3
"""Build webapp/explorer/storytree.json: one consolidated tree for the
storytree-explorer.html GitHub Pages viewer. Pulls every layer's artifacts
(root, expose, meta, plots, events, entities, scenes), trims the verbose
research fields, and writes a single self-contained JSON."""
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
R = ROOT / "runs"

def load(p):
    return json.loads(p.read_text(encoding="utf-8"))

def main() -> int:
    data = {"layers": {}, "source": {"story": "The Matrix", "form": "screenplay"}}

    # z1 story root
    data["layers"]["story_root"] = load(R / "story_root_v1/story_root.json")

    # z2 expose / treatment
    exp = load(R / "expose_v1/expose.json")
    data["layers"]["expose"] = {
        "jacket_copy": exp.get("jacket_copy", ""),
        "ending_first": exp.get("ending_first", {}).get("ending", ""),
        "synopsis_word_count": exp.get("synopsis_word_count"),
        "synopsis": exp.get("synopsis", {}),
    }

    # z3 meta layer
    meta = load(R / "meta_layer_v2b/meta.json")
    data["layers"]["meta"] = {
        "big_questions": meta["themes"].get("big_questions", []),
        "central_dilemma": meta["themes"].get("central_dilemma", {}),
        "external": meta.get("external", {}).get("conflicts", []),
        "internal": meta.get("internal", {}).get("internal_conflicts", []),
        "relationships": meta.get("relationships", {}).get("relationship_arcs", []),
        "perspectives": meta.get("perspectives", {}).get("perspectives", []),
    }

    # z4 plots (post-sample v8: 5 distinct throughlines)
    plots = load(R / "plot_layer_v8/plots.json")
    data["layers"]["plots"] = [
        {"name": name, "definition": p["definition"],
         "chain": [{"event_id": m.get("event_id"), "why_in_plot": m.get("why_in_plot"),
                    "caused_by_previous": m.get("caused_by_previous")} for m in p["chain"]]}
        for name, p in plots["plots"].items()
    ]

    # z5 events
    evs = load(R / "events_build10_full/events.json")["events"]
    data["layers"]["events"] = [
        {k: e.get(k) for k in ("event_id", "title", "summary", "participants",
                               "locations", "scene_ids", "carried_uncertainty",
                               "affects_outside", "turns_on")}
        for e in evs
    ]

    # z6 entities
    ents = load(R / "entity_trial_v2/profiles.json")
    if isinstance(ents, dict):
        ents = ents.get("entities", ents)
    skip = {"_research_facts", "_scenes_touched"}
    data["layers"]["entities"] = [
        {k: v for k, v in e.items() if k not in skip} for e in ents
    ]

    # z7 scenes (trimmed, includes minimal spine)
    scene_files = sorted((R / "scenes_ornith_v5_clean").glob("sc-*.json"))
    scenes = []
    for f in scene_files:
        s = load(f)
        scenes.append({k: s.get(k) for k in (
            "scene_id", "location", "time_of_day", "present", "summary",
            "what_changes", "sets_up", "dramatic_function")})
    scene_by_event = {}
    for e in evs:
        scene_by_event[e["event_id"]] = e.get("scene_ids", [])
    data["layers"]["scenes"] = {"by_event": scene_by_event, "list": scenes}

    out = ROOT / "webapp" / "explorer" / "storytree.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")),
                   encoding="utf-8")
    print(f"wrote {out} ({out.stat().st_size // 1024} kB)")
    return 0

def _trim(v, cap) -> str:
    s = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
    return s[:cap]

if __name__ == "__main__":
    raise SystemExit(main())