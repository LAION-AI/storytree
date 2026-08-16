"""Produce a reasoning transition for a node that already exists.

The forward pipeline writes the transition *before* the node. This tool runs the
inverse: given a finished node and everything established around it, reconstruct
the deliberate reasoning that arrives at it. That is the whitepaper's T7
direction, and it is how an existing corpus gets transitions without being
regenerated.

    python3 tools/make_transition.py runs/api-grok ev-008
    python3 tools/make_transition.py runs/api-grok sc-008
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import requests

from narrativeforge import timeline, transitions as T
from narrativeforge.backends.hyprlab import load_env
from narrativeforge.nodegen import entity_digest, event_digest
from narrativeforge.pipeline import Project

load_env(Path(__file__).resolve().parent.parent / ".env")
KEY = os.environ["HYPRLAB_API_KEY"]
BASE = os.environ.get("HYPRLAB_BASE_URL", "https://api.hyprlab.io/v1")


def _j(o):
    return json.dumps(o, indent=1, ensure_ascii=False)


SYSTEM = """\
You are a narrative architect, and your reasoning is the product.

You are given a node of a story graph that already exists, together with
everything established around it. Reconstruct the TRANSITION: the deliberate,
fully externalized reasoning that arrives at exactly this node.

This is not a review and not a justification written after the fact. Write it as
the reasoning itself — as though you were deciding, with the node as the
decision you reach. It will be read by other people and used as training data.

Every requirement in the schema is a requirement, not a suggestion. In
particular: theory of mind to three degrees per pair with the error named;
trajectories in phases with perceivable triggers, for minds and for objects
alike; felt versus expressed with the leakage; and a source pointer on every
established fact you lean on.

Be specific to THIS story. If a sentence could appear in a transition for a
different story, delete it and write the one that could not."""


def build(project: Project, node_id: str) -> tuple[str, dict]:
    docs = project.load_all()
    root = docs["story_root"]
    entities = (docs["entities"] or {}).get("entities", {})
    events = (docs["events"] or {}).get("events", {})
    scenes = (docs["scenes"] or {}).get("scenes", {})
    plots = (docs["plots"] or {}).get("plots", [])

    if node_id.startswith("ev-"):
        kind, node = "event", events[node_id]
        idx = (node.get("story_time") or {}).get("index", 0)
        prior = {k: v for k, v in event_digest(events).items()
                 if (events[k].get("story_time") or {}).get("index", 0) < idx}
        involved = set(node.get("participants") or []) | {node.get("location")}
        world = timeline.fold(docs["entities"], docs["events"], docs["scenes"]) if scenes else None
        state = ({e: world.state_before_event(node_id).get(e, {}).get("state", {}) for e in involved}
                 if world else {e: entities.get(e, {}).get("state", {}) for e in involved})
        realized = {sid: {"beats": s.get("beats"), "entry": s.get("entry_states"),
                          "exit": s.get("exit_states"), "function": s.get("dramatic_function")}
                    for sid, s in scenes.items() if node_id in (s.get("events") or [])}
        extra = f"\nHOW IT IS REALIZED IN SCENES\n{_j(realized)}"
    elif node_id.startswith("sc-"):
        kind, node = "scene", scenes[node_id]
        disc = node.get("discourse_index", 0)
        prior = {k: {"discourse": v.get("discourse_index"), "function": v.get("dramatic_function"),
                     "events": v.get("events")}
                 for k, v in scenes.items() if v.get("discourse_index", 0) < disc}
        involved = set(node.get("present") or []) | {node.get("location")}
        world = timeline.fold(docs["entities"], docs["events"], docs["scenes"])
        entering = world.state_entering_scene(node_id)
        state = {e: entering.get(e, {}).get("state", {}) for e in involved}
        extra = ("\nTHE EVENTS THIS SCENE REALIZES\n"
                 + _j({e: events[e] for e in (node.get("events") or []) if e in events}))
    else:
        raise SystemExit(f"unsupported node id {node_id!r} (expected ev-NNN or sc-NNN)")

    prompt = f"""\
RECONSTRUCT THE TRANSITION → {node_id}   ({kind})

STORY ROOT
{_j(root)}

PLOTS
{_j(plots)}

ENTITIES
{_j(entity_digest(entities))}

FULL DOSSIERS OF THE ENTITIES INVOLVED HERE
{_j({e: entities[e] for e in involved if e in entities})}

WHAT HAPPENED BEFORE THIS NODE
{_j(prior)}

LIVE STATE OF THE ENTITIES INVOLVED, AS THIS NODE OPENS
{_j(state)}
{extra}

═══════════════════════════════════════════════════════════════════════
THE NODE THAT WAS PRODUCED
═══════════════════════════════════════════════════════════════════════
{_j(node)}

═══════════════════════════════════════════════════════════════════════

Write the transition that arrives at this node. Fill every field the schema
requires; depth is the point.

SCHEMA
{_j(T.TRANSITION_SCHEMA)}
"""
    return prompt, {"kind": kind}


def main():
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    project = Project(Path(sys.argv[1]))
    node_id = sys.argv[2]
    prompt, meta = build(project, node_id)

    print(f"{node_id}: prompt {len(prompt):,} chars — calling grok-4.6 …", flush=True)
    t0 = time.time()
    r = requests.post(f"{BASE}/chat/completions",
                      headers={"Authorization": f"Bearer {KEY}"},
                      json={"model": "grok-4.6",
                            "messages": [{"role": "system", "content": SYSTEM},
                                         {"role": "user", "content": prompt}],
                            "response_format": {"type": "json_schema",
                                                "json_schema": {"name": "transition",
                                                                "strict": False,
                                                                "schema": T.TRANSITION_SCHEMA}},
                            "max_completion_tokens": 60000, "temperature": 0.7,
                            "reasoning_effort": "high"},
                      timeout=2400)
    dt = time.time() - t0
    if r.status_code != 200:
        raise SystemExit(f"HTTP {r.status_code}: {r.text[:600]}")
    d = r.json()
    content = d["choices"][0]["message"].get("content") or ""
    u = d.get("usage", {})
    doc = json.loads(content)

    out = project.root / "transitions"
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{node_id}.json").write_text(_j(doc) + "\n")

    sc = T.score_transition(doc)
    verdict, gaps = T.grade(sc)
    cost = (u.get("prompt_tokens", 0)/1e6)*1.8 + \
           ((u.get("completion_tokens", 0) +
             (u.get("completion_tokens_details") or {}).get("reasoning_tokens", 0))/1e6)*5.4
    print(f"  {sc['words']:,} words · {verdict} · {dt:.0f}s · ${cost:.3f}")
    for g in gaps:
        print(f"  gap: {g}")
    print(f"  -> {out / f'{node_id}.json'}")


if __name__ == "__main__":
    main()
