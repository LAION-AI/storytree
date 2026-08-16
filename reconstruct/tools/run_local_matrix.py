"""Scaffolded reconstruction against the local GLM-5.2, measured on time and quality.

    python3 tools/run_local_matrix.py runs/matrix sc-001 sc-002 sc-003

What this is testing
--------------------
Three things at once, and they need to stay separable in the output:

1. **Does the local abliterated build hold the schema?** The hosted model needed
   repair passes; a 3.64-bpw abliterated copy of it has two extra sources of
   degradation stacked on top. This is the question the quality numbers answer.

2. **What does it actually cost in wall-clock?** Not the roofline, not a
   benchmark prompt — the real 15–40k-token structured calls the pipeline makes.

3. **Is the hidden reasoning earning its keep?** ~74% of everything this model
   generates is reasoning tokens, which on a local box is not a billing line but
   a 3x on wall-clock. And this pipeline is unusual: the scaffold already forces
   the reasoning to be written out explicitly into the schema — trajectories,
   theory of mind, rejected alternatives. So the hidden thinking may be doing
   duplicate work. `--no-think` tests that. If quality holds, the run gets ~3x
   faster for free; if it collapses, we have learned the reasoning was load-
   bearing and we pay for it knowingly.

The comparison is against transitions/ (hosted, single call) and
transitions_scaffolded/ (hosted, scaffolded) which are already on disk for these
scenes, so the same scenes are measured three ways.

Nothing here copies the source screenplay. Scene text is read to locate speaker
cues and is not written to any output.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import requests

from scriptforge import jsonschema_mini as js, reverse, scaffold, screenplay as sp

sys.path.insert(0, str(ROOT.parent))
from narrativeforge.model_notes import addendum_for

# The addendum is the single variable under test. When off, the system prompt is
# byte-identical to the one that produced the baseline nodes.
ADDENDUM = addendum_for(os.environ.get("LOCAL_MODEL", "")) if os.environ.get("ADDENDUM") == "1" else ""
SYSTEM = reverse.BLIND_SYSTEM + ADDENDUM
from scriptforge.nodegen import entity_digest
from scriptforge.pipeline import Project
from scriptforge.transitions import (
    CONTINUITY_SCHEMA, DYNAMICS_SCHEMA, PSYCH_SCHEMA, SPECIMEN_SCHEMA,
    TRANSITION_SCHEMA, grade, score_transition,
)

BASE = os.environ.get("LOCAL_BASE_URL", "http://127.0.0.1:8099/v1")
MODEL = os.environ.get("LOCAL_MODEL", "glm-5.2-abliterated-q3km")
RETRIES = 3

CALLS: list[dict] = []


def _reasoning_body(mode: str) -> dict:
    """How to suppress thinking — three of the obvious knobs are silent no-ops.

    Measured against /apply-template and against real generations, on this GGUF:

        reasoning_effort: "low"        HTTP 200, changes NOTHING  <- the trap
        reasoning_effort: "minimal"    HTTP 200, changes NOTHING
        reasoning: {"effort": "none"}  HTTP 200, changes NOTHING
        reasoning_effort: "none"       works
        chat_template_kwargs
          {"enable_thinking": false}   works

    The cause is in the model's own chat template, which reads

        effective_reasoning_effort = 'high' if reasoning_effort == 'high' else 'max'

    — everything that is not the literal string 'high' is mapped to *max*, the
    most expensive setting there is. So `"low"` is not a mild reduction, it is
    the maximum, and it is the parameter most people would reach for first. Only
    llama.cpp's special case for "none" escapes the template.

    'high' is therefore the only genuine reduction available short of off, and
    it only moves Max -> High. There is deliberately no 'low' option here: a
    condition that silently does nothing would produce a clean-looking A/B with
    two identical arms.
    """
    if os.environ.get("MODEL_FAMILY") == "qwen":
        # Qwen3.8 accepts only xhigh|medium|low for reasoning_effort — any other
        # value makes the chat template raise and the request 400s. There is no
        # "none". Thinking is switched off structurally instead.
        return ({"chat_template_kwargs": {"enable_thinking": False}} if mode == "off"
                else {"reasoning_effort": "xhigh"})
    if mode == "off":
        return {"reasoning_effort": "none",
                "chat_template_kwargs": {"enable_thinking": False}}
    return {"reasoning_effort": "high"}


def call(system: str, user: str, schema: dict, *, tag: str, think: str,
         max_tokens: int = 40000) -> dict:
    last = ""
    for attempt in range(1, RETRIES + 1):
        try:
            doc = _one(system, user, schema, tag=tag, think=think,
                       max_tokens=max_tokens, attempt=attempt)
            if isinstance(doc, dict) and len(json.dumps(doc)) < 200 and attempt < RETRIES:
                last = f"stub of {len(json.dumps(doc))} chars"
                print(f"      {tag}: {last} — retrying")
                continue
            return doc
        except (json.JSONDecodeError, ValueError) as exc:
            last = f"unparseable ({exc})"
            print(f"      {tag}: {last} — "
                  + ("retrying" if attempt < RETRIES else "giving up"))
    raise SystemExit(f"{tag}: {RETRIES} degenerate responses — {last}")


def _one(system, user, schema, *, tag, think, max_tokens, attempt) -> dict:
    body = {"model": MODEL,
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": user}],
            "response_format": {"type": "json_schema",
                                "json_schema": {"name": "part", "strict": False,
                                                "schema": schema}},
            "max_tokens": max_tokens, "temperature": 0.7,
            "cache_prompt": True,
            **_reasoning_body(think)}
    t0 = time.time()
    r = requests.post(f"{BASE}/chat/completions",
                      headers={"Authorization": "Bearer local"},
                      json=body, timeout=7200)
    dt = time.time() - t0
    if r.status_code != 200:
        raise SystemExit(f"{tag}: HTTP {r.status_code}: {r.text[:300]}")
    d = r.json()
    msg = d["choices"][0]["message"]
    content = msg.get("content") or ""
    reasoning = msg.get("reasoning_content") or ""
    u = d.get("usage", {})
    pt = u.get("prompt_tokens", 0)
    ct = u.get("completion_tokens", 0)
    CALLS.append({"tag": tag, "secs": dt, "in": pt, "out": ct,
                  "reasoning_chars": len(reasoning), "content_chars": len(content),
                  "finish": d["choices"][0].get("finish_reason"), "attempt": attempt})
    note = "" if attempt == 1 else f"  (attempt {attempt})"
    print(f"      {tag:<24} {dt:>6.0f}s  in={pt:>7,} out={ct:>6,} "
          f"{ct/dt if dt else 0:>5.1f} t/s  think={len(reasoning):>6,}c{note}")
    if not content.strip():
        raise ValueError("empty content")
    return json.loads(content)


def repair(part, doc, schema, node_id, think, rounds=2):
    for i in range(rounds):
        errs = js.validate(doc, schema)
        if not errs:
            return doc, []
        print(f"      repairing {part}: {len(errs)} violation(s)")
        doc = call(SYSTEM,
                   scaffold.repair_prompt(node_id, part, doc, errs, schema),
                   schema, tag=f"repair.{part}.{i+1}", think=think)
    return doc, js.validate(doc, schema)


def run_scene(project: Project, scene_id: str, think: str) -> dict:
    docs = project.load_all()
    ents = (docs["entities"] or {}).get("entities", {})
    scenes_all = (docs["scenes"] or {}).get("scenes", {})
    table = json.loads((project.root / "script_map.json").read_text())
    text = Path(table["source_file"]).read_text(errors="replace")
    _, parsed = sp.parse(text)
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
    position = scene.index / max(1, len(parsed))
    blind = reverse.blind_context(ctx, {}, position=position,
                                  strip_dossiers=os.environ.get('STRIP_DOSSIERS','0')=='1')
    env = reverse.envelope(scene, len(parsed) - scene.index, len(parsed))

    events = (docs["events"] or {}).get("events", {})
    on_screen, unresolved = scaffold.characters_in_scene(ents, scene, events)
    roster = scaffold.roster_text(ents, focus=on_screen)
    print(f"    characters: {on_screen}")
    if unresolved:
        print(f"    ! speakers with no entity: {unresolved}")

    craft_schema = {"type": "object", "additionalProperties": False,
                    "properties": {k: v for k, v in TRANSITION_SCHEMA["properties"].items()
                                   if k in ("target", "situation", "craft",
                                            "interaction", "decision")},
                    "required": ["target", "situation", "craft", "interaction", "decision"]}
    craft = call(SYSTEM,
                 scaffold.craft_prompt(scene_id, blind, env, roster),
                 craft_schema, tag="craft", think=think)
    craft, _ = repair("craft", craft, craft_schema, scene_id, think)

    psych = []
    for eid in on_screen:
        p = call(SYSTEM,
                 scaffold.psych_prompt(scene_id, eid, ents[eid], blind, craft, roster),
                 PSYCH_SCHEMA, tag=f"psych.{eid}", think=think)
        p, _ = repair(f"psych.{eid}", p, PSYCH_SCHEMA, scene_id, think)
        p["entity"] = eid
        psych.append(p)

    specimen = call(SYSTEM,
                    scaffold.specimen_prompt(scene_id, craft, psych, roster),
                    SPECIMEN_SCHEMA, tag="specimen", think=think)
    specimen, _ = repair("specimen", specimen, SPECIMEN_SCHEMA, scene_id, think)

    dyn_schema = {"type": "array", "items": DYNAMICS_SCHEMA}
    dynamics = call(SYSTEM,
                    scaffold.dynamics_prompt(scene_id, blind, craft, roster),
                    dyn_schema, tag="dynamics", think=think)
    if isinstance(dynamics, dict):
        dynamics = dynamics.get("dynamics") or list(dynamics.values())[0]

    continuity = call(SYSTEM,
                      scaffold.continuity_prompt(scene_id, blind, craft, psych),
                      CONTINUITY_SCHEMA, tag="continuity", think=think)
    continuity, _ = repair("continuity", continuity, CONTINUITY_SCHEMA, scene_id, think)

    return scaffold.assemble(scene_id, "scene", craft, psych, dynamics,
                             specimen, continuity)


def measure(tr: dict) -> dict:
    errs = js.validate(tr, TRANSITION_SCHEMA)
    sc = score_transition(tr)
    verdict, gaps = grade(sc)
    ps = tr.get("psychology") or []
    full = sum(1 for p in ps if all(p.get(k) for k in
               ("perception", "appraisal", "social_norms", "theory_of_mind", "urges",
                "impairments", "deliberation", "control", "trajectory", "intention", "action")))
    return {"violations": len(errs), "words": sc["words"], "psych": len(ps),
            "with_trajectory": sum(1 for p in ps if p.get("trajectory")),
            "complete_blocks": full, "tom_towers": sc["tom_towers"],
            "tom_depth3": sc["tom_depth3"], "specimen_lines": sc.get("specimen_lines", 0),
            "alternatives": sc["alternatives_rejected"],
            "nearly_chosen": sc.get("alternatives_nearly_chosen", 0),
            "dynamics": len(tr.get("dynamics") or []),
            "verdict": verdict, "gaps": gaps}


def show(label: str, m: dict):
    print(f"  {label}")
    print(f"    violations {m['violations']:<4} words {m['words']:>6,}   "
          f"psych {m['with_trajectory']}/{m['psych']} w/ trajectory, "
          f"{m['complete_blocks']}/{m['psych']} complete")
    print(f"    ToM {m['tom_towers']} towers ({m['tom_depth3']} at depth 3)   "
          f"specimen {m['specimen_lines']} lines   alts {m['alternatives']} "
          f"({m['nearly_chosen']} close)   dynamics {m['dynamics']}")
    print(f"    verdict: {m['verdict']}")
    for g in m["gaps"]:
        print(f"      gap: {g}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("scenes", nargs="+")
    ap.add_argument("--think", choices=["high", "off"], default="off")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    project = Project(Path(a.project))
    outdir = project.root / (a.out or f"transitions_local_{a.think}")
    outdir.mkdir(exist_ok=True)

    print(f"LOCAL RECONSTRUCTION · {BASE} · thinking={a.think}")
    print(f"  scenes: {', '.join(a.scenes)}\n")

    results = {}
    t_start = time.time()
    for sid in a.scenes:
        print(f"  === {sid} ===")
        t0 = time.time()
        n0 = len(CALLS)
        tr = run_scene(project, sid, a.think)
        dt = time.time() - t0
        (outdir / f"{sid}.json").write_text(json.dumps(tr, indent=1, ensure_ascii=False))
        m = measure(tr)
        m["secs"] = dt
        m["calls"] = len(CALLS) - n0
        results[sid] = m
        print()
        show(f"LOCAL scaffolded · {sid} · {dt/60:.1f} min · {m['calls']} calls", m)

        for other, tag in ((project.root / "transitions_scaffolded" / f"{sid}.json",
                            "hosted scaffolded"),
                           (project.root / "transitions" / f"{sid}.json",
                            "hosted single-call")):
            if other.exists():
                show(tag, measure(json.loads(other.read_text())))
        print()

    total = time.time() - t_start
    tin = sum(c["in"] for c in CALLS)
    tout = sum(c["out"] for c in CALLS)
    think_c = sum(c["reasoning_chars"] for c in CALLS)
    secs = sum(c["secs"] for c in CALLS)

    print("=" * 72)
    print(f"  {len(a.scenes)} scenes · {len(CALLS)} calls · {total/60:.1f} min wall")
    print(f"  tokens: {tin:,} in · {tout:,} out")
    print(f"  decode: {tout/secs if secs else 0:.1f} tok/s mean over all calls")
    print(f"  per scene: {total/60/len(a.scenes):.1f} min")
    print(f"  reasoning_content returned: {think_c:,} chars", end="")
    if a.think == "off" and think_c > 0:
        print("   <-- WARNING: --think off did NOT suppress thinking; timings are not a clean test")
    else:
        print()
    print(f"  extrapolated to all 224 scenes: {total/len(a.scenes)*224/3600:.1f} h")
    (outdir / "_run_stats.json").write_text(json.dumps(
        {"think": a.think, "base": BASE, "wall_secs": total, "calls": CALLS,
         "scenes": results}, indent=1))
    print(f"  -> {outdir}")
