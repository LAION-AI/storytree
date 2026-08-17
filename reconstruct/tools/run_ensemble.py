"""Run the two-model ensemble on scenes, and measure what the split bought.

    python3 tools/run_ensemble.py runs/matrix sc-001 sc-002 sc-003

GLM-5.2 (7 GPUs, :8099) writes the semantics. Qwen3.8-27B (1 GPU, :8107) converts
that prose into state changes against a closed vocabulary extracted from the
dossiers. Code decides everything decidable and neither model is consulted.

The comparison arms already on disk, same three scenes, same conditions:

    transitions_local_off      GLM alone
    transitions_qwen           Qwen alone
    transitions_qwen_grounded  Qwen alone + schema binding
    transitions_ensemble       this
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scriptforge import ensemble, grounding, reverse, scaffold, screenplay as sp
from scriptforge import jsonschema_mini as js
from scriptforge.nodegen import entity_digest
from scriptforge.pipeline import Project
from scriptforge.transitions import (
    CONTINUITY_SCHEMA, DYNAMICS_SCHEMA, PSYCH_SCHEMA, SPECIMEN_SCHEMA,
    TRANSITION_SCHEMA, grade, score_transition,
)


def build(project: Project, scene_id: str, writer, book, think_ctx: bool) -> dict:
    docs = project.load_all()
    ents = (docs["entities"] or {}).get("entities", {})
    scenes_all = (docs["scenes"] or {}).get("scenes", {})
    table = json.loads((project.root / "script_map.json").read_text())
    _, parsed = sp.parse(Path(table["source_file"]).read_text(errors="replace"))
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
    # Historical conditions, matching the arms this is compared against.
    blind = reverse.blind_context(ctx, {}, position=scene.index / max(1, len(parsed)),
                                  strip_dossiers=False)
    env = reverse.envelope(scene, len(parsed) - scene.index, len(parsed))

    prompts = {
        "blind_system": reverse.BLIND_SYSTEM,
        "craft": scaffold.craft_prompt,
        "psych": scaffold.psych_prompt,
        "specimen": scaffold.specimen_prompt,
        "dynamics": scaffold.dynamics_prompt,
        "continuity": scaffold.continuity_prompt,
    }
    schemas = {"transition": TRANSITION_SCHEMA, "psych": PSYCH_SCHEMA,
               "specimen": SPECIMEN_SCHEMA, "dynamics": DYNAMICS_SCHEMA,
               "continuity": CONTINUITY_SCHEMA}
    # Who the vocabulary should cover. Speaker cues alone are too narrow — an
    # unresolved cue like BIG COP resolves to nobody, and the vocabulary then
    # falls back to all 36 entities, which is the wide-open list the closed
    # vocabulary exists to avoid. The event layer already records who each scene
    # is *about*, which is the right set for bookkeeping even though it is the
    # wrong set for who may speak.
    evs = (docs["events"] or {}).get("events", {})
    involved, _ = scaffold.characters_in_scene(ents, scene, evs)
    return ensemble.split_scene(writer, book, scene, ents, blind, env, prompts,
                                schemas, book_focus=involved, events=evs)


def report(tr: dict, scene, ents) -> dict:
    speakers = grounding.allowed_speakers(scene, ents)
    sc = score_transition(tr)
    verdict, _ = grade(sc)
    ps = tr.get("psychology") or []
    full = sum(1 for p in ps if all(p.get(k) for k in
               ("perception", "appraisal", "social_norms", "theory_of_mind", "urges",
                "impairments", "deliberation", "control", "trajectory", "intention", "action")))
    e = tr.get("_ensemble") or {}
    return {"words": sc["words"], "d3": sc["tom_depth3"],
            "spec": sc.get("specimen_lines", 0), "psych": f"{full}/{len(ps)}",
            "changes": e.get("changes_recorded", 0),
            "code_problems": len(e.get("code_problems") or []),
            "grounding": len(e.get("grounding") or []),
            "presence": len(e.get("presence") or []),
            "not_expressible": len(e.get("not_expressible") or []),
            "verdict": verdict}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("scenes", nargs="+")
    ap.add_argument("--writer", default="http://127.0.0.1:8099/v1")
    ap.add_argument("--writer-model", default="glm-5.2-abliterated-q3km")
    ap.add_argument("--book", default="http://127.0.0.1:8107/v1")
    ap.add_argument("--book-model", default="qwen3.8-27b")
    ap.add_argument("--out", default="transitions_ensemble")
    a = ap.parse_args()

    writer = ensemble.Endpoint("GLM", a.writer, a.writer_model, "glm")
    book = ensemble.Endpoint("Qwen", a.book, a.book_model, "qwen")

    project = Project(Path(a.project))
    outdir = project.root / a.out
    outdir.mkdir(exist_ok=True)

    table = json.loads((project.root / "script_map.json").read_text())
    _, parsed = sp.parse(Path(table["source_file"]).read_text(errors="replace"))
    scenes = {s.scene_id: s for s in parsed}
    ents = (project.load("entities") or {}).get("entities", {})

    print(f"ENSEMBLE · writer={a.writer_model} @ {a.writer}")
    print(f"           clerk ={a.book_model} @ {a.book}\n")

    t_all = time.time()
    results = {}
    for sid in a.scenes:
        print(f"  === {sid} ===")
        t0 = time.time()
        tr = build(project, sid, writer, book, True)
        dt = time.time() - t0
        (outdir / f"{sid}.json").write_text(json.dumps(tr, indent=1, ensure_ascii=False))
        m = report(tr, scenes[sid], ents)
        m["secs"] = dt
        results[sid] = m
        e = tr.get("_ensemble") or {}
        print(f"    {dt/60:.1f} min · {m['words']:,} words · {m['changes']} changes "
              f"from a {e.get('vocabulary_size', 0)}-term vocabulary")
        print(f"    code {m['code_problems']} · grounding {m['grounding']} "
              f"· presence {m['presence']} · inexpressible {m['not_expressible']} "
              f"· dyn {len(tr.get('dynamics') or [])} · {m['verdict']}")
        for v in (e.get("presence") or [])[:3]:
            print(f"      P! {v['violation']}")
        for p in (e.get("code_problems") or [])[:3]:
            print(f"      ! {p}")
        for p in (e.get("not_expressible") or [])[:2]:
            print(f"      ~ could not express: {p[:90]}")
        print()

    wall = time.time() - t_all
    wt = sum(c["secs"] for c in writer.calls)
    bt = sum(c["secs"] for c in book.calls)
    print("=" * 70)
    print(f"  {len(a.scenes)} scene(s) · {wall/60:.1f} min wall")
    print(f"  writer: {len(writer.calls)} calls, {sum(c['out'] for c in writer.calls):,} out, "
          f"{wt/60:.1f} min")
    print(f"  clerk : {len(book.calls)} calls, {sum(c['out'] for c in book.calls):,} out, "
          f"{bt/60:.1f} min ({bt/(wt+bt)*100 if wt+bt else 0:.0f}% of model time)")
    print(f"  thinking suppressed: "
          f"{'yes' if not any(c['think'] for c in writer.calls + book.calls) else 'NO — check'}")
    (outdir / "_run_stats.json").write_text(json.dumps(
        {"wall": wall, "writer": writer.calls, "book": book.calls,
         "scenes": results}, indent=1))
    print(f"  -> {outdir}")
