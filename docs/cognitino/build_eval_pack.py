#!/usr/bin/env python3
"""Build a BLIND evaluation pack: CogniTino scene nodes vs V1 / V4 / V5.

The three consecutive evaluator reports in this project share one weakness, recorded in the
handshake: *"The evaluator is one Opus agent, not blind to arm, who helped specify the designs
it scores."* Ranked next step #1 was a blind A/B for exactly that reason.

So this pack is built blind by construction:

* Arms are relabelled `arm-A` … `arm-D` under a shuffle keyed by a seed, and the key is
  written to a **separate file** the judge is not given.
* Every field that names the arm is stripped, and both systems are mapped onto one common
  set of presentation slots, so the arm cannot be identified from the field names alone.
  Content is moved between slots, never removed; an empty slot means that arm genuinely has
  nothing for it, which is itself a finding.

**Blinding is label-level, not perfect, and pretending otherwise would be the same error this
file exists to correct.** The arms are different systems producing genuinely different
objects: the abstraction arm carries beat-reference evidence and falsifiers on its mind
entries, and a careful judge could infer from that which arm is new. Removing those fields
would hide the properties actually under evaluation, so they stay and the limitation is
disclosed instead.
* Scene order within each arm is preserved (the rubric is per-scene), but arm order in the
  file is shuffled per scene, so position carries no signal either.

Usage:
  python3 build_eval_pack.py --out eval_pack/
"""

from __future__ import annotations

import argparse
import json
import random
import re
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[2]
SAMPLE = ["sc-003", "sc-008", "sc-015", "sc-024", "sc-039",
          "sc-056", "sc-075", "sc-097", "sc-113", "sc-129",
          "sc-148", "sc-164", "sc-182", "sc-200", "sc-215"]


def _strip_arm_signals(node: Dict[str, Any]) -> Dict[str, Any]:
    """Remove keys that identify which system produced a node."""
    drop = {"_mind_pass", "_variant", "variant", "arm", "_arm", "provenance", "_window",
            "ao_id", "superseded_by", "absorbed", "schema_version"}

    def clean(value):
        if isinstance(value, dict):
            return {k: clean(v) for k, v in value.items() if k not in drop}
        if isinstance(value, list):
            return [clean(v) for v in value]
        return value
    return clean(node)


def load_variant(variant: str, scene_id: str) -> Dict[str, Any] | None:
    path = ROOT / "reconstruct" / "runs" / "matrix" / "fix_{}".format(variant) / "{}.json".format(scene_id)
    if not path.exists():
        return None
    return _strip_arm_signals(normalise_v(json.loads(path.read_text(encoding="utf-8"))))


def normalise_v(node: Dict[str, Any]) -> Dict[str, Any]:
    """Map a V-series node onto the common presentation slots.

    An enriched node carries extra keys added alongside the original; they are folded into
    the same slots so the arm is not identifiable by field names. Stripping them recovers
    plain V4 exactly, which is what makes the pair comparable.
    """
    minds = list(node.get("minds") or [])
    for m in node.get("deepened_minds") or []:
        minds.append({"who": m.get("who"), "wants": m.get("wants"),
                      "feels": "fears: {} | conceals: {} (from {})".format(
                          m.get("fears"), m.get("conceals"), m.get("from_whom")),
                      "shows": m.get("because"), "confidence": m.get("confidence"),
                      "would_be_wrong_if": m.get("would_be_wrong_if")})
    for t in node.get("theory_of_mind") or []:
        minds.append({"who": t.get("who"), "about": t.get("about"),
                      "feels": t.get("believes"), "shows": t.get("because"),
                      "confidence": t.get("confidence"),
                      "would_be_wrong_if": t.get("would_be_wrong_if")})
    changes = list(node.get("what_changes") or [])
    for c in node.get("internal_changes") or []:
        changes.append({"who": c.get("who"), "axis": c.get("axis"),
                        "before": c.get("before"), "after": c.get("after"),
                        "evidence": c.get("because")})
    sets_up = list(node.get("sets_up") or [])
    back = list(node.get("connects_back") or [])
    for l in node.get("causal_links") or []:
        line = "{} -> {}: {} ({})".format(
            (l.get("cause") or {}).get("scene_id"), (l.get("effect") or {}).get("scene_id"),
            l.get("because"), l.get("confidence"))
        (sets_up if l.get("kind") == "causes" else back).append(line)
    node = dict(node)
    node["minds"], node["what_changes"] = minds, changes
    node["sets_up"], node["connects_back"] = sets_up, back
    return {
        "scene_id": node.get("scene_id"),
        "location": node.get("location"),
        "time_of_day": node.get("time_of_day"),
        "present": node.get("present"),
        "speaking": node.get("speaking"),
        # The V-series has a single summary; presented as a one-element list so both arms
        # share a type and the difference in granularity remains visible rather than hidden.
        "what_happens": [node.get("summary")] if node.get("summary") else [],
        "what_changes": node.get("what_changes"),
        "minds": node.get("minds"),
        "dramatic_function": node.get("dramatic_function"),
        "sets_up": node.get("sets_up"),
        "connects_back": node.get("connects_back"),
        "objects_that_matter": node.get("objects_that_matter"),
        "uncertain": node.get("uncertain"),
    }


def normalise_cognitino(node: Dict[str, Any]) -> Dict[str, Any]:
    """Map a Scene Community onto the same slots.

    Content is moved, never removed. Where an arm genuinely has nothing for a slot the slot
    is empty, and that emptiness is a real finding rather than a blinding artefact.
    """
    unit = node["perception"]
    ao = node.get("abstraction") or []

    def of(*types):
        return [o for o in ao if o.get("type") in types]

    beats = unit.get("beats") or []
    changes = []
    for beat in beats:
        for change in beat.get("state_changes") or []:
            changes.append({
                "who": change.get("entity"), "axis": change.get("field"),
                "before": change.get("from"), "after": change.get("to"),
                "evidence": "{}#{}: {}".format(unit["scene_id"], beat.get("order"),
                                               beat.get("content")),
            })

    minds = []
    for o in of("mental_state", "theory_of_mind"):
        entry = {"who": o.get("subject"),
                 "feels": o.get("statement"),
                 "shows": o.get("reasoning"),
                 "evidence": ", ".join(o.get("grounded_in") or []),
                 "confidence": o.get("confidence")}
        if o.get("about"):
            entry["about"] = o["about"]
        if o.get("falsifier"):
            entry["would_be_wrong_if"] = o["falsifier"]
        minds.append(entry)

    return {
        "scene_id": node["scene_id"],
        "location": (node.get("heading") or {}).get("location"),
        "time_of_day": (node.get("heading") or {}).get("time_of_day"),
        "present": unit.get("present"),
        "speaking": sorted({b.get("actor") for b in beats if b.get("type") == "speech"}),
        # Beats stay ordered. The first version joined them into one string, which
        # destroyed exactly the structure the rubric asks about and would have scored the
        # arm down for a property the normaliser removed rather than the system lacked.
        "what_happens": [
            "{}. {}".format(b.get("order"), b.get("content")) for b in beats
        ],
        "what_changes": changes,
        "minds": minds,
        "dramatic_function": " ".join(o.get("statement") or "" for o in of("authorial_intent")),
        "sets_up": [o.get("statement") for o in of("consequence")] + [unit.get("context_after")],
        "connects_back": [unit.get("context_before")],
        "objects_that_matter": [e.get("name") for e in unit.get("entities") or []
                                if e.get("type") in ("object", "vehicle", "program")],
        "uncertain": [o.get("statement") for o in ao
                      if o.get("confidence") in ("speculative", "plausible")],
    }


def load_cognitino(graph: Dict[str, Any], scene_id: str) -> Dict[str, Any] | None:
    for node in graph.get("scene_nodes") or []:
        if node["scene_id"] != scene_id:
            continue
        return _strip_arm_signals(normalise_cognitino(node))
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--graph", default=str(ROOT / "runs" / "cognitino_matrix" / "scene_graph.json"))
    parser.add_argument("--graph2", default="", help="second cognitino graph, scored as its own arm")
    parser.add_argument("--enriched-dir", default="", help="enriched V4 nodes, scored as its own arm")
    parser.add_argument("--variants", default="v1,v4,v5")
    parser.add_argument("--out", required=True)
    parser.add_argument("--seed", type=int, default=20260819)
    args = parser.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    graph = json.loads(Path(args.graph).read_text(encoding="utf-8"))
    graph2 = json.loads(Path(args.graph2).read_text(encoding="utf-8")) if args.graph2 else None
    variants = args.variants.split(",")

    rng = random.Random(args.seed)
    arms = variants + (["cognitino"] if args.graph else []) \
        + (["cognitino_v2"] if graph2 else []) + (["v4_enriched"] if args.enriched_dir else [])
    labels = ["arm-{}".format(c) for c in "ABCDEFGH"[:len(arms)]]
    shuffled = arms[:]
    rng.shuffle(shuffled)
    key = dict(zip(labels, shuffled))

    pack, missing = [], []
    for scene_id in SAMPLE:
        entry = {"scene_id": scene_id, "arms": {}}
        for label in labels:
            source = key[label]
            if source == "cognitino":
                node = load_cognitino(graph, scene_id)
            elif source == "cognitino_v2":
                node = load_cognitino(graph2, scene_id)
            elif source == "v4_enriched":
                q = Path(args.enriched_dir) / "{}.json".format(scene_id)
                node = (_strip_arm_signals(normalise_v(json.loads(q.read_text(encoding="utf-8"))))
                        if q.exists() else None)
            else:
                node = load_variant(source, scene_id)
            if node is None:
                missing.append((scene_id, source))
                continue
            entry["arms"][label] = node
        order = labels[:]
        rng.shuffle(order)
        entry["arms"] = {label: entry["arms"][label] for label in order if label in entry["arms"]}
        pack.append(entry)

    (out / "pack.json").write_text(json.dumps({"scenes": pack}, indent=1), encoding="utf-8")
    (out / "KEY.json").write_text(json.dumps({"seed": args.seed, "key": key}, indent=1),
                                  encoding="utf-8")
    print("wrote {} scenes x {} arms -> {}".format(len(pack), len(labels), out / "pack.json"))
    print("key withheld in {} — do not give this to the judge".format(out / "KEY.json"))
    if missing:
        print("missing nodes: {}".format(missing[:10]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
