"""A/B the scaffolded transition against the single-call baseline.

    python3 tools/experiment_scaffold.py runs/matrix sc-002

Same model, same scene, same schema. The only variable is whether the deep
structures are asked for all at once or one per call. Everything is measured
against the schema rather than judged by eye.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import requests

from scriptforge import jsonschema_mini as js, reverse, scaffold, screenplay as sp
from scriptforge.backends.hyprlab import load_env
from scriptforge.nodegen import entity_digest
from scriptforge.pipeline import Project
from scriptforge.transitions import (
    CONTINUITY_SCHEMA, DYNAMICS_SCHEMA, PSYCH_SCHEMA, SPECIMEN_SCHEMA,
    TRANSITION_SCHEMA, grade, score_transition,
)

load_env(ROOT.parent / ".env")
KEY = os.environ["HYPRLAB_API_KEY"]
BASE = os.environ.get("HYPRLAB_BASE_URL", "https://api.hyprlab.io/v1")
MODEL = os.environ.get("EXP_MODEL", "glm-5.2")

STATS = {"calls": 0, "in": 0, "out": 0, "secs": 0.0}


DEGENERATE_RETRIES = 3


def call(system: str, user: str, schema: dict, *, tag: str, max_tokens: int = 40000) -> dict:
    """One call, with retries for the empty/stub responses glm-5.2 emits sporadically.

    Observed three times in this run: a bare {"ref": "sc-004"}, an empty content
    string, and — on the identical prompt that had just failed — a full 10.7k
    document. The failure is intermittent rather than a property of the prompt,
    so the only workable response is to detect it and ask again.
    """
    last = ""
    for attempt in range(1, DEGENERATE_RETRIES + 1):
        try:
            doc = _one_call(system, user, schema, tag=tag, max_tokens=max_tokens,
                            attempt=attempt)
            if isinstance(doc, dict) and len(json.dumps(doc)) < 200 and attempt < DEGENERATE_RETRIES:
                last = f"stub of {len(json.dumps(doc))} chars"
                print(f"    {tag}: {last} — retrying")
                continue
            return doc
        except (json.JSONDecodeError, ValueError) as exc:
            last = f"unparseable ({exc})"
            print(f"    {tag}: {last} — retrying" if attempt < DEGENERATE_RETRIES
                  else f"    {tag}: {last} — giving up")
    raise SystemExit(f"{tag}: {DEGENERATE_RETRIES} degenerate responses — {last}")


def _one_call(system: str, user: str, schema: dict, *, tag: str, max_tokens: int,
              attempt: int) -> dict:
    t0 = time.time()
    r = requests.post(f"{BASE}/chat/completions",
                      headers={"Authorization": f"Bearer {KEY}"},
                      json={"model": MODEL,
                            "messages": [{"role": "system", "content": system},
                                         {"role": "user", "content": user}],
                            "response_format": {"type": "json_schema",
                                                "json_schema": {"name": "part", "strict": False,
                                                                "schema": schema}},
                            "max_completion_tokens": max_tokens, "temperature": 0.7,
                            "reasoning_effort": "high"},
                      timeout=2400)
    dt = time.time() - t0
    if r.status_code != 200:
        raise SystemExit(f"{tag}: HTTP {r.status_code}: {r.text[:300]}")
    d = r.json()
    u = d.get("usage", {})
    STATS["calls"] += 1
    STATS["in"] += u.get("prompt_tokens", 0)
    STATS["out"] += u.get("completion_tokens", 0) + \
        (u.get("completion_tokens_details") or {}).get("reasoning_tokens", 0)
    STATS["secs"] += dt
    content = d["choices"][0]["message"].get("content") or ""
    suffix = "" if attempt == 1 else f"  (attempt {attempt})"
    print(f"    {tag:<26} {len(content):>7,} chars  {dt:>5.0f}s{suffix}")
    if not content.strip():
        raise ValueError("empty content")
    return json.loads(content)


def repair(part: str, doc, schema: dict, node_id: str, rounds: int = 2):
    """Feed the actual violations back. Asking again and hoping does not work."""
    for i in range(rounds):
        errs = js.validate(doc, schema)
        if not errs:
            return doc, []
        print(f"    repairing {part}: {len(errs)} violation(s)")
        doc = call(reverse.BLIND_SYSTEM,
                   scaffold.repair_prompt(node_id, part, doc, errs, schema),
                   schema, tag=f"repair.{part}.{i+1}")
    return doc, js.validate(doc, schema)


def run_scaffolded(project: Project, scene_id: str) -> dict:
    docs = project.load_all()
    ents = (docs["entities"] or {}).get("entities", {})
    scenes_all = (docs["scenes"] or {}).get("scenes", {})
    table = json.loads((project.root / "script_map.json").read_text())
    meta = table["scenes"][scene_id]

    text, parsed = sp.parse(Path(table["source_file"]).read_text(errors="replace"))
    scene = next(s for s in parsed if s.scene_id == scene_id)

    ctx = {
        "root": {k: (docs["story_root"] or {}).get(k) for k in
                 ("title", "form", "genre_primary", "setting", "style",
                  "state_dimensions", "keep_in_mind")},
        "plots": (docs["plots"] or {}).get("plots"),
        "entities": entity_digest(ents),
        "prior": {s: {"function": v.get("dramatic_function")}
                  for s, v in scenes_all.items() if s < scene_id},
        "live_state": {e: v.get("state", {}) for e, v in ents.items()},
    }
    blind = reverse.blind_context(ctx, {}, position=scene.index / max(1, len(parsed)))
    env = reverse.envelope(scene, len(parsed) - scene.index, len(parsed))

    events = (docs["events"] or {}).get("events", {})
    on_screen, unresolved = scaffold.characters_in_scene(ents, scene, events)
    roster = scaffold.roster_text(ents, focus=on_screen)
    print(f"  characters: {on_screen}   (cues: {scene.speakers})")
    if unresolved:
        print(f"  ! speakers with no entity: {unresolved}")

    print("  --- call 1: craft ---")
    craft_schema = {"type": "object", "additionalProperties": False,
                    "properties": {k: v for k, v in TRANSITION_SCHEMA["properties"].items()
                                   if k in ("target", "situation", "craft", "interaction", "decision")},
                    "required": ["target", "situation", "craft", "interaction", "decision"]}
    craft_part = call(reverse.BLIND_SYSTEM,
                      scaffold.craft_prompt(scene_id, blind, env, roster),
                      craft_schema, tag="craft")
    craft_part, _ = repair("craft", craft_part, craft_schema, scene_id)

    print("  --- one call per character ---")
    psych = []
    for eid in on_screen:
        p = call(reverse.BLIND_SYSTEM,
                 scaffold.psych_prompt(scene_id, eid, ents[eid], blind, craft_part, roster),
                 PSYCH_SCHEMA, tag=f"psych.{eid}")
        p, errs = repair(f"psych.{eid}", p, PSYCH_SCHEMA, scene_id)
        p["entity"] = eid                      # the id is ours, not the model's
        psych.append(p)

    print("  --- specimen, dynamics, continuity ---")
    specimen = call(reverse.BLIND_SYSTEM,
                    scaffold.specimen_prompt(scene_id, craft_part, psych, roster),
                    SPECIMEN_SCHEMA, tag="specimen")
    specimen, _ = repair("specimen", specimen, SPECIMEN_SCHEMA, scene_id)

    dyn_schema = {"type": "array", "items": DYNAMICS_SCHEMA}
    dynamics = call(reverse.BLIND_SYSTEM,
                    scaffold.dynamics_prompt(scene_id, blind, craft_part, roster),
                    dyn_schema, tag="dynamics")
    if isinstance(dynamics, dict):
        dynamics = dynamics.get("dynamics") or list(dynamics.values())[0]

    continuity = call(reverse.BLIND_SYSTEM,
                      scaffold.continuity_prompt(scene_id, blind, craft_part, psych),
                      CONTINUITY_SCHEMA, tag="continuity")
    continuity, _ = repair("continuity", continuity, CONTINUITY_SCHEMA, scene_id)

    return scaffold.assemble(scene_id, "scene", craft_part, psych, dynamics,
                             specimen, continuity)


def report(label: str, tr: dict) -> dict:
    errs = js.validate(tr, TRANSITION_SCHEMA)
    sc = score_transition(tr)
    verdict, gaps = grade(sc)
    ps = tr.get("psychology") or []
    print(f"\n  {label}")
    print(f"    schema violations      {len(errs)}")
    print(f"    words                  {sc['words']:,}")
    print(f"    psychology blocks      {len(ps)}")
    print(f"    ...with trajectory     {sum(1 for p in ps if p.get('trajectory'))}/{len(ps)}")
    print(f"    ...with all 11 fields  {sum(1 for p in ps if all(p.get(k) for k in ('perception','appraisal','social_norms','theory_of_mind','urges','impairments','deliberation','control','trajectory','intention','action')))}/{len(ps)}")
    print(f"    ToM towers / at depth3 {sc['tom_towers']} / {sc['tom_depth3']}")
    print(f"    specimen lines         {sc.get('specimen_lines', 0)}")
    print(f"    alternatives (close)   {sc['alternatives_rejected']} ({sc.get('alternatives_nearly_chosen',0)})")
    print(f"    verdict                {verdict}")
    for g in gaps:
        print(f"      gap: {g}")
    return {"violations": len(errs), "score": sc, "verdict": verdict}


if __name__ == "__main__":
    project = Project(Path(sys.argv[1]))
    scene_id = sys.argv[2]

    baseline_path = project.root / "transitions" / f"{scene_id}.json"
    print(f"EXPERIMENT · {MODEL} · {scene_id}\n")
    if baseline_path.exists():
        report("BASELINE (single call, already on disk)", json.loads(baseline_path.read_text()))

    print(f"\n  SCAFFOLDED — one deep structure per call")
    t0 = time.time()
    tr = run_scaffolded(project, scene_id)
    out = project.root / "transitions_scaffolded"
    out.mkdir(exist_ok=True)
    (out / f"{scene_id}.json").write_text(json.dumps(tr, indent=1, ensure_ascii=False))
    r = report("SCAFFOLDED", tr)
    print(f"\n  cost: {STATS['calls']} calls · {STATS['in']:,} in · {STATS['out']:,} out · "
          f"{STATS['secs']:.0f}s wall")
    cost = STATS["in"]/1e6*1.8 + STATS["out"]/1e6*5.4
    print(f"  approx ${cost:.2f}")
    print(f"  -> {out / f'{scene_id}.json'}")
