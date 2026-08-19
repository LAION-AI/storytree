#!/usr/bin/env python3
"""Render Scene Communities as a readable document: source text, perception, abstraction.

Reproduces the same three-scene exhibit pattern as the Alexandria worked examples, extended
with the abstraction layer.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, "/home/deployer/laion/project-alexandria/screenplay/src")

from screenplay_ku.scenes import load_scenes, load_source  # noqa: E402

TYPE_LABEL = {
    "mental_state": "Mental state",
    "theory_of_mind": "Theory of mind",
    "hypothesis": "Hypothesis",
    "relationship": "Relationship",
    "entity_trait": "Entity trait",
    "concept": "Concept",
    "process": "Process",
    "authorial_intent": "Authorial intent",
    "consequence": "Consequence",
}

CONF_MARK = {"speculative": "○○○", "plausible": "●○○",
             "probable": "●●○", "near-certain": "●●●"}


def render_community(node, scene, source, index):
    unit = node["perception"]
    abstraction = node.get("abstraction") or []
    heading = (node.get("heading") or {}).get("raw") or scene.heading_raw
    out = []
    out.append("## {}. {} — `{}`\n".format(index, heading, node["scene_id"]))
    out.append("*{} words of source · {} beats · {} abstraction objects*\n".format(
        scene.word_count, len(unit.get("beats") or []), len(abstraction)))

    out.append("### Layer 0 — the scene as written\n")
    out.append("```text\n{}\n```\n".format(scene.text(source).rstrip()))

    out.append("### Layer 1 — Perception: what the script *states*\n")
    out.append("Every line here is checkable against the text above. Nothing is inferred.\n")
    if unit.get("present"):
        out.append("**Present:** {}\n".format(", ".join("`{}`".format(x) for x in unit["present"])))
    for beat in unit.get("beats") or []:
        ref = "{}#{}".format(node["scene_id"], beat.get("order"))
        addressee = beat.get("addressee")
        arrow = " → `{}`".format(addressee) if addressee else ""
        out.append("**`{}`** `[{}]` `{}`{}  \n{}".format(
            ref, beat.get("type"), beat.get("actor"), arrow, beat.get("content")))
        for change in beat.get("state_changes") or []:
            out.append("  \n&nbsp;&nbsp;&nbsp;&nbsp;*state:* `{}.{}`: {} → **{}**".format(
                change.get("entity"), change.get("field"),
                change.get("from"), change.get("to")))
        out.append("")

    out.append("### Layer 2 — Abstraction: what the script *implies*\n")
    out.append("Nothing here is stated by the scene. Every object points back to the beats "
               "that license it, and names what would prove it wrong.\n")
    if not abstraction:
        out.append("*(none produced for this scene)*\n")
    for obj in sorted(abstraction, key=lambda o: o.get("type") or ""):
        subject = obj.get("subject") or "?"
        about = obj.get("about")
        who = "`{}` → `{}`".format(subject, about) if about else "`{}`".format(subject)
        out.append("**{}** · {} · {} {}  ".format(
            TYPE_LABEL.get(obj.get("type"), obj.get("type")), who,
            CONF_MARK.get(obj.get("confidence"), ""), obj.get("confidence")))
        out.append("> {}\n".format(obj.get("statement")))
        out.append("*Because:* {}  ".format(obj.get("reasoning")))
        out.append("*Grounded in:* {}  ".format(
            ", ".join("`{}`".format(g) for g in obj.get("grounded_in") or [])))
        if obj.get("falsifier"):
            out.append("*Would be wrong if:* {}  ".format(obj["falsifier"]))
        for item in obj.get("contradicting_evidence") or []:
            out.append("*Counter-evidence* `{}`: {}  ".format(
                item.get("beat_ref"), item.get("why")))
        if obj.get("confidence_history"):
            last = obj["confidence_history"][-1]
            out.append("*Confidence revised* {} → {} after research: {}  ".format(
                last.get("from"), last.get("to"), last.get("why")))
        links = obj.get("links") or []
        if links:
            out.append("*Links:* {}  ".format(", ".join(
                "{} `{}`".format(l.get("link"), l.get("to")) for l in links[:4])))
        out.append("")
    out.append("---\n")
    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--graph", required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--scene-map", required=True)
    parser.add_argument("--scenes", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--header", default="")
    args = parser.parse_args()

    graph = json.loads(Path(args.graph).read_text(encoding="utf-8"))
    source = load_source(Path(args.source))
    scenes = {s.scene_id: s for s in load_scenes(Path(args.scene_map), source)}
    nodes = {n["scene_id"]: n for n in graph["scene_nodes"]}

    parts = []
    if args.header and Path(args.header).exists():
        parts.append(Path(args.header).read_text(encoding="utf-8"))
    for index, scene_id in enumerate(args.scenes.split(","), start=1):
        node, scene = nodes.get(scene_id), scenes.get(scene_id)
        if not node or not scene:
            print("skip {}".format(scene_id))
            continue
        parts.append(render_community(node, scene, source, index))
    Path(args.out).write_text("\n".join(parts), encoding="utf-8")
    print("wrote {}".format(args.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
