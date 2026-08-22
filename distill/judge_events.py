#!/usr/bin/env python3
"""Agents as judges: blind A/B scoring of event-layer builds on local models.

The earlier rounds were judged through an external backend. This script runs the
SAME instrument locally — the docs/cognitino-era 14-dimension rubric (universal
A-G, event V1-V5, reconstruction R1/R2), POSTURE 3 = "acceptable", integers only,
one evidence clause per score — against the llama.cpp endpoints, so numbers from
different judging eras are never mixed: when the judge changes, EVERY arm is
re-judged under the new judge before any comparison is made.

Blinding is inherited from build_event_eval_pack.py: the pack holds arm-A/arm-B
under a per-pairing shuffle, and the KEY lives in a directory the judges are
never pointed at. This script reads only the pack.

Each judge is an independent pass over the whole pack (temperature sampling,
schema-forced integer scores); independence is statistical, and the judges share
one underlying model — the same limitation the scene layer documented, stated
rather than hidden.

Output files join directly into distill/aggregate_event_eval.py:
  {"judge": ..., "pairings": [{"pairing_id": ...,
                               "arm-A": {"scores": {...}}, ...}]}

Usage:
  python3 distill/judge_events.py --pack runs/eval_ox/baseline_pack \
      --out runs/eval_ox/baseline_scores --scenes-dir runs/scenes_ornith_v5 \
      --ports 8110,8111 --model ornith-1.5-397b --judges 4
"""

from __future__ import annotations

import argparse
import glob
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, "/home/deployer/laion/project-alexandria/screenplay/src")
from screenplay_ku.client import EndpointPool, run_parallel  # noqa: E402
from screenplay_ku.kuschema import grammar_safe  # noqa: E402

DIMENSIONS = ["A", "B", "C", "D", "E", "F", "G",
              "V1", "V2", "V3", "V4", "V5", "R1", "R2"]

# The corrected briefing. Every one of these lines earned its place: a briefing
# error is a systematic scoring shift (V3 was invalid for a whole round because
# the briefing described build 2's contract).
BRIEFING = """\
JUDGE BRIEFING — read before scoring anything

POSTURE. Hard marking. 3 means "acceptable, would survive review with notes",
not "good". A node that fills every slot correctly and adds no judgement
scores 3 at best on the dimensions that matter. Integers 1-5 only. Every score
carries one evidence clause naming a specific field or quoting the artifact.
Score what is delivered, not what could be read charitably.

CONTRACT NOTES (each corrects an error that once biased a round):
  * The register contract is NOT all seven registers. Objects carry only
    physical / positional / status. A person carrying knowledge, relational,
    emotional or safety registers is normal, not a violation.
  * A noun phrase is a state description, not truncation. "cuffed, face down"
    is a complete state; do not penalise brevity.
  * "[...]" marks a deliberate elision. It is neutral: neither a defect nor a
    virtue.
  * `off_screen_reactor` LEGITIMATELY names parties who do not appear in the
    event. That is its job. Only enables/blocks_or_costs naming absent parties
    who cannot act from outside is suspect.
  * Fields prefixed "_" are pipeline annotations, not content. Do not score
    them; do not treat them as admissions.
  * Never quote more than seven consecutive words from any source material.
"""


def load_rubric() -> str:
    """Assemble the 14-dimension rubric from distill/rubrics/RUBRICS.md."""
    text = Path(__file__).resolve().parent.joinpath("rubrics", "RUBRICS.md")\
        .read_text(encoding="utf-8")

    def between(start: str, end: str) -> str:
        i = text.index(start)
        j = text.index(end, i)
        return text[i:j].rstrip() + "\n"

    universal = between("## Universal dimensions", "## ROOT node")
    event = between("## EVENT node", "## SCENE node")
    recon = between("#### R1 ", "#### F1 ")
    return "\n\n".join([universal, event, recon])


def load_scenes(directory: str) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for path in glob.glob(str(Path(directory) / "sc-*.json")):
        node = json.loads(Path(path).read_text(encoding="utf-8"))
        out[node.get("scene_id") or Path(path).stem] = node
    return out


def scene_brief(scene: Dict[str, Any]) -> Dict[str, Any]:
    """The grounding a judge gets: what the scene layer recorded, compact."""
    keep: Dict[str, Any] = {}
    for k in ("location", "word_count"):
        if scene.get(k):
            keep[k] = scene[k]
    if scene.get("present"):
        keep["present"] = scene["present"][:20]
    if scene.get("objects_that_matter"):
        keep["objects"] = scene["objects_that_matter"]
    changes = []
    for c in scene.get("what_changes") or []:
        if isinstance(c, dict) and c.get("who"):
            changes.append({k: c.get(k) for k in ("who", "axis", "before", "after")
                            if c.get(k)})
    if changes:
        keep["what_changes"] = changes[:20]
    minds = []
    for m in scene.get("minds") or []:
        if isinstance(m, dict) and m.get("who"):
            mind = {"who": m["who"]}
            for k, v in m.items():
                if k != "who" and v:
                    mind[k] = str(v)[:160]
            minds.append(mind)
    if minds:
        keep["minds"] = minds[:10]
    return keep


_JUDGE_SYSTEM = (
    "You are one of several independent judges scoring structured story-graph "
    "event nodes against a fixed rubric. You work only from the artifacts and "
    "context you are given. You return only valid JSON."
)

def judge_schema() -> Dict[str, Any]:
    dim_props = {d: {"type": "integer", "enum": [1, 2, 3, 4, 5]}
                 for d in DIMENSIONS}
    ev_props = {d: {"type": "string"} for d in DIMENSIONS}

    def arm() -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "scores": {"type": "object", "properties": dict(dim_props),
                           "required": sorted(DIMENSIONS),
                           "additionalProperties": False},
                "evidence": {"type": "object", "properties": dict(ev_props),
                             "required": sorted(DIMENSIONS),
                             "additionalProperties": False},
            },
            "required": ["scores", "evidence"],
            "additionalProperties": False,
        }

    return {
        "type": "object",
        "properties": {
            "arm-A": arm(),
            "arm-B": arm(),
            "preferred": {"type": "string", "enum": ["arm-A", "arm-B", "tie"]},
            "reason": {"type": "string"},
        },
        "required": ["arm-A", "arm-B", "preferred", "reason"],
        "additionalProperties": False,
    }


_JUDGE_PROMPT = """\\
You are judging ONE pairing. Two arms each hold one event node covering the
same stretch of film. Score BOTH arms on all fourteen dimensions, then say
which arm you prefer.

SCORING RULES
  * Integers 1-5 only, per the rubric anchors. No half points, no averaging.
  * `evidence`: one short clause per dimension naming the field or quoted span
    it rests on. A score without a field reference is not a score.
  * `preferred`: which arm a rational producer would ship, weighing all
    fourteen dimensions — not the one with the higher mean by arithmetic.
  * Judge the nodes AS DELIVERED. Where both arms share an upstream fault, it
    depresses both equally; say so in `reason` rather than forgiving either.

=== RUBRIC AND BRIEFING ===
{rubric}

{briefing}
=== GROUNDING: WHAT THE SCENE LAYER RECORDED FOR THESE SCENES ===
{scenes}

=== PAIRING {pid} ===
{pairing_json}

Return the scores now.
"""

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pack", required=True,
                    help="dir with batch*.json from build_event_eval_pack.py")
    ap.add_argument("--out", required=True)
    ap.add_argument("--scenes-dir", default="runs/scenes_ornith_v5")
    ap.add_argument("--ports", default="8110,8111")
    ap.add_argument("--model", default="ornith-1.5-397b")
    ap.add_argument("--judges", type=int, default=4)
    ap.add_argument("--judge-id-prefix", default="jox")
    ap.add_argument("--temperature", type=float, default=0.7)
    ap.add_argument("--max-tokens", type=int, default=6000)
    ap.add_argument("--only-pairing", default="",
                    help="score a single pairing id; for smoke tests")
    a = ap.parse_args()

    pack = sorted(Path(a.pack).glob("batch*.json"))
    if not pack:
        print("no batch*.json in {}".format(a.pack))
        return 2
    pairings: List[Dict[str, Any]] = []
    for p in pack:
        pairings += json.loads(p.read_text(encoding="utf-8"))["pairings"]
    if a.only_pairing:
        pairings = [p for p in pairings if p["pairing_id"] == a.only_pairing]
    print("{} pairing(s)".format(len(pairings)), flush=True)

    rubric = load_rubric()
    scenes = load_scenes(a.scenes_dir)
    out_dir = Path(a.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    pool = EndpointPool([int(p) for p in a.ports.split(",")], a.model,
                        temperature=a.temperature, max_tokens=a.max_tokens,
                        timeout=3600)
    bad = [p for p, ok in pool.health() if not ok]
    if bad:
        print("unhealthy endpoints: {}".format(bad))
        return 2

    schema = grammar_safe(judge_schema())

    def work(job):
        pid, pairing = job
        ids = sorted({sid for arm_key in ("arm-A", "arm-B")
                      for sid in (pairing[arm_key].get("scene_ids") or [])})
        grounding = [scene_brief(scenes[sid]) for sid in ids if sid in scenes]
        prompt = _JUDGE_PROMPT.format(
            rubric=rubric, briefing=BRIEFING,
            scenes=json.dumps(grounding, ensure_ascii=False, indent=1),
            pid=pid,
            pairing_json=json.dumps(pairing, ensure_ascii=False, indent=1))
        r = pool.call(_JUDGE_SYSTEM, prompt, schema=schema)
        result = json.loads(r.text)
        result["pairing_id"] = pid
        result["anchor_scene"] = pairing.get("anchor_scene")
        return pid, result

    jobs = [(p["pairing_id"], p) for p in pairings]

    for j in range(1, a.judges + 1):
        judge_id = "{}{}".format(a.judge_id_prefix, j)
        out_path = out_dir / "scores_{}.json".format(judge_id)
        if out_path.exists():
            print("{}: already scored, skipping".format(judge_id), flush=True)
            continue
        started = time.time()

        def on_done(d, t, r):
            if d % 5 == 0 or d == t:
                print("  [{}/{}] {}".format(
                    d, t, "ok" if not isinstance(r, Exception) else "ERR"),
                    flush=True)

        results = run_parallel(jobs, work, max_workers=2, on_done=on_done)
        rows, failed = [], []
        for item in results:
            if isinstance(item, Exception) or not isinstance(item, tuple):
                failed.append(str(item)[:80])
                continue
            pid, res = item
            rows.append({
                "pairing_id": pid,
                "anchor_scene": res.get("anchor_scene"),
                "arm-A": res.get("arm-A"),
                "arm-B": res.get("arm-B"),
                "preferred": res.get("preferred"),
                # The holistic preference rationale. The first pack run lost
                # this field in the row writer and the judges' own reasons --
                # the part worth reading -- never reached the report.
                "reason": res.get("reason"),
            })
        out_path.write_text(json.dumps({"judge": judge_id, "pack": str(a.pack),
                                        "pairings": rows}, indent=1,
                                       ensure_ascii=False), encoding="utf-8")
        print("{}: {} scored, {} failed, {:.0f}s -> {}".format(
            judge_id, len(rows), len(failed), time.time() - started, out_path),
            flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


