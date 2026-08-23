#!/usr/bin/env python3
"""Meta layer build 2: revise build 1 under the judge's own evidence.

Reads the judgement of the first meta layer, hands EVERY evidence clause and
the commentary to a rewrite pass per section -- keep what passed, fix what
was named -- audits the revision with the same scaffold checks as build 1,
and writes a v2 artifact for re-judging. The judge is not asked whether v2 is
better; that comparison is made by running judge_meta.py on both.

Usage:
  python3 distill/meta_revise.py --meta runs/meta_layer/meta.json \
      --judgement runs/meta_layer/judgement.json \
      --events runs/events_build10_full/events.json \
      --out runs/meta_layer_v2 --ports 8110,8111
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Dict

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, "/home/deployer/laion/project-alexandria/screenplay/src")
from screenplay_ku.client import EndpointPool  # noqa: E402
from screenplay_ku.kuschema import grammar_safe  # noqa: E402


def _load(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--meta", required=True)
    ap.add_argument("--judgement", required=True)
    ap.add_argument("--events", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--ports", default="8110,8111")
    ap.add_argument("--model", default="ornith-1.5-397b")
    a = ap.parse_args()

    ml = _load("_ml", str(Path(__file__).resolve().parent / "meta_layer.py"))
    meta = json.loads(Path(a.meta).read_text(encoding="utf-8"))
    judgement = json.loads(Path(a.judgement).read_text(encoding="utf-8"))
    events = json.loads(Path(a.events).read_text(encoding="utf-8"))["events"]
    scene_ids = sorted({s for e in events for s in (e.get("scene_ids") or [])})
    event_ids = [e["event_id"] for e in events]
    digest = ml.build_digest(events)

    # The critique, verbatim and complete: scores, every evidence clause,
    # the commentary. Sections get all of it -- a weakness named under M1
    # usually shows in several sections.
    evidence = judgement.get("evidence") or {}
    critique = "\n".join(
        "{} = {} -- {}".format(d, judgement["scores"][d],
                               evidence.get(d) or "(no clause recorded)")
        for d in judgement["scores"])
    critique += "\n\nOVERALL: " + str(judgement.get("commentary") or
                                      "(none recorded)")

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    pool = EndpointPool([int(p) for p in a.ports.split(",")], a.model,
                        temperature=0.4, max_tokens=8000, timeout=1800)

    schemas = {
        "themes": ml._themes_schema(scene_ids, event_ids),
        "external": ml._conflicts_schema(scene_ids, event_ids),
        "internal": ml._internal_schema(scene_ids, event_ids),
        "relationships": ml._relationships_schema(scene_ids, event_ids),
        "perspectives": ml._perspectives_schema(scene_ids, event_ids),
    }

    revised: Dict[str, Any] = {}
    for section in ("themes", "external", "internal", "relationships",
                    "perspectives"):
        prompt = "\n\n".join([
            "TASK: {}".format(ml.PROMPTS[section]),
            "THE SECTION AS IT STANDS:\n" + json.dumps(
                meta[section], ensure_ascii=False, indent=1),
            "THE JUDGE'S CRITIQUE OF THE FULL ARTIFACT:\n" + critique,
            "Rewrite this section so every named weakness is fixed WITHOUT "
            "losing what the judge did not criticise: same schema, real "
            "evidence pointers into the events below, paraphrased grounding, "
            "no inventions.",
            "THE EVENT LAYER:\n" + digest[:60000]])
        r = pool.call(ml.SYSTEM, prompt,
                      schema=grammar_safe(schemas[section]))
        revised[section] = json.loads(r.text)
        print("  {} rewritten".format(section), flush=True)

    events_by_id = {e["event_id"]: e for e in events}
    source_index = ml.V.SourceIndex(Path("distill/runs/matrix/script.normalized.txt")
                                    .read_text(encoding="utf-8", errors="ignore"))
    for round_no in range(2):
        faults = []
        for section in revised:
            faults += ml.audit_section(section, revised[section],
                                       events_by_id, source_index)
        print("audit round {}: {} faults".format(round_no + 1, len(faults)))
        if not faults:
            break
        by_sec: Dict[str, list] = {}
        for f in faults:
            by_sec.setdefault(f["section"], []).append(f)
        for section, fs in by_section_safe(by_sec):
            ml.regenerate_item(pool, section, revised[section], fs, digest,
                               schemas[section])

    (out / "meta.json").write_text(json.dumps(revised, indent=1,
                                              ensure_ascii=False),
                                   encoding="utf-8")
    print("wrote {}".format(out / "meta.json"))
    return 0


def by_section_safe(by_sec):
    return list(by_sec.items())


if __name__ == "__main__":
    raise SystemExit(main())
