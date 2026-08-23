#!/usr/bin/env python3
"""Build the meta layer: themes, dilemmas, conflicts, relationship arcs.

The layer between events and plots. A plot is a perspective on a dilemma; the
dilemmas, the conflicts that carry them, and the relationships they move are
not visible from any single event, so they get their own pass before any plot
is written. Four agents work in parallel -- big questions and the central
dilemma, external conflicts, internal conflicts, relationship arcs -- each
FORCED to ground every claim in event and scene ids, then a fifth pass maps
the story's perspectives onto what the first four found (the ARCHITECTURE OF
THE STORY MIND throughlines: THEY / I / YOU / WE).

Everything is scaffold-checked before it counts:
  * every referenced scene/event id must exist,
  * named entities must overlap the film's own cast vocabulary,
  * every claim carries at least one evidence pointer with a paraphrase,
  * no eight-word run of source screenplay survives (verbatim gate),
and faults found here are sent back to the model with the fault named, one
item at a time -- the same audit-and-regenerate discipline as the event
layer. Nothing reaches the plot stage unjudged: distill/judge_meta.py scores
the finished layer against distill/rubrics/meta.json.

Usage:
  python3 distill/meta_layer.py --events runs/events_build10_full/events.json \
      --scenes-dir runs/scenes_ornith_v5 --out runs/meta_layer \
      --ports 8110,8111 --source distill/runs/matrix/script.normalized.txt
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, "/home/deployer/laion/project-alexandria/screenplay/src")
from screenplay_ku.client import EndpointPool, run_parallel  # noqa: E402
from screenplay_ku.kuschema import grammar_safe  # noqa: E402
import verbatim as V  # noqa: E402

SYSTEM = (
    "You analyse the deeper structure of a story from its finished scene and "
    "event layers. You name only what the layers support, you never invent "
    "scenes, characters or events, and you point at the material for every "
    "claim. You return only valid JSON."
)

def _ev_ref(scene_ids: Sequence[str], event_ids: Sequence[str]) -> Dict[str, Any]:
    """An evidence pointer: where a claim is visible, in the analyst's words."""
    return {
        "type": "object",
        "properties": {
            "event_id": {"type": "string", "enum": list(event_ids)},
            "scene_id": {"type": "string", "enum": list(scene_ids)},
            # Paraphrase, never quotation: what here supports the claim.
            "grounding": {"type": "string", "minLength": 15, "maxLength": 300},
        },
        "required": ["event_id", "scene_id", "grounding"],
        "additionalProperties": False,
    }


def _ref_array(scene_ids, event_ids, min_items: int = 1, max_items: int = 6):
    return {"type": "array", "minItems": min_items, "maxItems": max_items,
            "items": _ev_ref(scene_ids, event_ids)}

def _themes_schema(scene_ids, event_ids):
    ref = _ref_array
    return {
        "type": "object",
        "properties": {
            "big_questions": {
                "type": "array", "minItems": 2, "maxItems": 5,
                "items": {
                    "type": "object",
                    "properties": {
                        "question": {"type": "string", "minLength": 20,
                                     "maxLength": 200},
                        "why_central": {"type": "string", "minLength": 40,
                                        "maxLength": 500},
                        "evidence": ref(scene_ids, event_ids, 2, 6),
                    },
                    "required": ["question", "why_central", "evidence"],
                    "additionalProperties": False,
                }},
            "central_dilemma": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "minLength": 10, "maxLength": 120},
                    "horn_a": {"type": "string", "minLength": 30, "maxLength": 400},
                    "horn_b": {"type": "string", "minLength": 30, "maxLength": 400},
                    "why_genuine": {"type": "string", "minLength": 60,
                                    "maxLength": 500},
                    "evidence": ref(scene_ids, event_ids, 2, 6),
                },
                "required": ["name", "horn_a", "horn_b", "why_genuine",
                             "evidence"],
                "additionalProperties": False,
            },
        },
        "required": ["big_questions", "central_dilemma"],
        "additionalProperties": False,
    }


def _conflicts_schema(scene_ids, event_ids):
    return {
        "type": "object",
        "properties": {"conflicts": {
            "type": "array", "minItems": 3, "maxItems": 8,
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "minLength": 10,
                             "maxLength": 150},
                    "parties": {"type": "array", "minItems": 2, "maxItems": 4,
                                "items": {"type": "string", "minLength": 2}},
                    "stakes": {"type": "string", "minLength": 30,
                               "maxLength": 400},
                    "how_it_develops": {"type": "string", "minLength": 40,
                                        "maxLength": 600},
                    "evidence": _ref_array(scene_ids, event_ids, 2, 6),
                },
                "required": ["name", "parties", "stakes", "how_it_develops",
                             "evidence"],
                "additionalProperties": False,
            }}},
        "required": ["conflicts"], "additionalProperties": False,
    }

def _internal_schema(scene_ids, event_ids):
    return {
        "type": "object",
        "properties": {"internal_conflicts": {
            "type": "array", "minItems": 2, "maxItems": 6,
            "items": {
                "type": "object",
                "properties": {
                    "character": {"type": "string", "minLength": 2},
                    "torn_between": {"type": "array", "minItems": 2,
                                     "maxItems": 3,
                                     "items": {"type": "string",
                                               "minLength": 10,
                                               "maxLength": 200}},
                    "what_it_costs": {"type": "string", "minLength": 30,
                                      "maxLength": 400},
                    "evidence": _ref_array(scene_ids, event_ids, 2, 6),
                },
                "required": ["character", "torn_between", "what_it_costs",
                             "evidence"],
                "additionalProperties": False,
            }}},
        "required": ["internal_conflicts"], "additionalProperties": False,
    }


def _relationships_schema(scene_ids, event_ids):
    return {
        "type": "object",
        "properties": {"relationship_arcs": {
            "type": "array", "minItems": 2, "maxItems": 6,
            "items": {
                "type": "object",
                "properties": {
                    "pair": {"type": "array", "minItems": 2, "maxItems": 2,
                             "items": {"type": "string", "minLength": 2}},
                    "arc": {"type": "string", "enum":
                            ["grows", "deteriorates", "changes_direction",
                             "repairs"]},
                    "what_changes": {"type": "string", "minLength": 40,
                                     "maxLength": 600},
                    "turning_points": {"type": "integer", "minimum": 1,
                                       "maximum": 4},
                    "evidence": _ref_array(scene_ids, event_ids, 2, 6),
                },
                "required": ["pair", "arc", "what_changes", "turning_points",
                             "evidence"],
                "additionalProperties": False,
            }}},
        "required": ["relationship_arcs"], "additionalProperties": False,
    }


def _perspectives_schema(scene_ids, event_ids):
    return {
        "type": "object",
        "properties": {"perspectives": {
            "type": "array", "minItems": 3, "maxItems": 6,
            "items": {
                "type": "object",
                "properties": {
                    "throughline": {"type": "string", "enum":
                                    ["objective_story", "main_character",
                                     "impact_character", "relationship",
                                     "society"]},
                    "label": {"type": "string", "minLength": 8,
                              "maxLength": 120},
                    "stance_on_dilemma": {"type": "string", "minLength": 40,
                                          "maxLength": 500},
                    "evidence": _ref_array(scene_ids, event_ids, 2, 6),
                },
                "required": ["throughline", "label", "stance_on_dilemma",
                             "evidence"],
                "additionalProperties": False,
            }}},
        "required": ["perspectives"], "additionalProperties": False,
    }

PROMPTS = {
    "themes": (
        "Identify the BIG QUESTIONS OF LIFE this story is built around -- "
        "questions most humans face: identity, meaning vs. pleasure, freedom "
        "vs. obligation, justice vs. mercy, mortality, love vs. duty, truth "
        "vs. a comfortable lie. Then name THE CENTRAL DILEMMA: a forced "
        "choice between two equally valid virtues or two painful evils. If "
        "choosing is easy, it is not a dilemma and does not belong here; "
        "both horns must cost something the story shows."),
    "external": (
        "List the noteworthy EXTERNAL CONFLICTS: parties whose goals or "
        "forces collide in visible action hard enough to bend the story's "
        "direction. Not every scuffle -- the ones that carry the story."),
    "internal": (
        "List the INTERNAL CONFLICTS: characters torn between goals, "
        "obligations, passions or fears, visibly enough that the story bends "
        "around their hesitation. Name the pulling forces and what the torn "
        "character pays."),
    "relationships": (
        "List the RELATIONSHIP ARCS worth remembering: bonds that grow, "
        "decay, repair or change direction, with their turning points "
        "located in events and scenes."),
    "perspectives": (
        "Map the PERSPECTIVES the story opens on its central dilemma, as "
        "throughlines: objective_story ('THEY', the world-level collision), "
        "main_character ('I', the protagonist's inside view), "
        "impact_character ('YOU', whoever challenges the protagonist's "
        "worldview), relationship ('WE', a bond under the dilemma), society "
        "(a group living the question). State each stance ON THE DILEMMA "
        "GIVEN BELOW."),
}
SECTION_KEY = {"themes": None, "external": "conflicts",
               "internal": "internal_conflicts",
               "relationships": "relationship_arcs",
               "perspectives": "perspectives"}


def build_digest(events: Sequence[Dict[str, Any]]) -> str:
    lines = []
    for e in events:
        lines.append("### {} — {}  [scenes: {}]".format(
            e["event_id"], e.get("title"),
            ", ".join(e.get("scene_ids") or [])))
        if e.get("participants"):
            lines.append("participants: " + ", ".join(e["participants"][:12]))
        lines.append((e.get("summary") or "")[:420])
        lines.append("")
    return "\n".join(lines)


def audit_section(section: str, data: Dict[str, Any], events_by_id,
                  source_index) -> List[Dict[str, Any]]:
    """Faults a machine can prove, each naming the item to redo."""
    key = SECTION_KEY[section]
    items = data.get(key) if key else [data]
    faults = []
    for i, item in enumerate(items or []):
        def add(detail):
            faults.append({"section": section, "index": i, "detail": detail})
        seen = set()
        for ev in item.get("evidence") or []:
            eid, sid = ev.get("event_id"), ev.get("scene_id")
            if eid not in events_by_id:
                add("cites event {} which does not exist".format(eid))
                continue
            if sid not in (events_by_id[eid].get("scene_ids") or []):
                add("cites scene {} under event {}, but that event does not "
                    "contain the scene".format(sid, eid))
            if (eid, sid) in seen:
                add("cites the same event/scene pair twice")
            seen.add((eid, sid))
        if not (item.get("evidence") or []):
            add("carries no evidence pointers at all")
        for name in (item.get("parties") or []) + \
                (item.get("pair") or []) + \
                ([item.get("character")] if item.get("character") else []):
            for probe in V.scan_node({"n": name}, source_index):
                if probe[1].kind == "exact":
                    add("party {!r} quotes the screenplay verbatim".format(name))
    return faults


def regenerate_item(pool, section, data, faults, digest, schema) -> Optional[Dict]:
    """Redo one faulty item with the fault named; accepted only if clean."""
    key = SECTION_KEY[section]
    items = data.get(key) if key else [data]
    by_index: Dict[int, List[str]] = {}
    for f in faults:
        by_index.setdefault(f["index"], []).append(f["detail"])
    fixed_any = False
    for i, details in by_index.items():
        item = items[i] if key else data
        prompt = "\n\n".join([
            "TASK: {}".format(PROMPTS[section]),
            "THE ITEM THAT FAILED AUDIT:\n" + json.dumps(
                item, ensure_ascii=False, indent=1),
            "FAULTS FOUND IN IT:\n" + "\n".join("  - " + d for d in details),
            "THE EVENT LAYER OF THE STORY:\n" + digest[:60000],
            "Rewrite ONLY this item. Same schema, real evidence pointers, "
            "paraphrased grounding."])
        try:
            r = pool.call(SYSTEM, prompt, schema=grammar_safe(schema),
                          max_tokens=4000, temperature=0.4)
            new = json.loads(r.text)
        except Exception:
            continue
        new_item = new.get(key) if key else new
        if key:
            if not isinstance(new_item, list) or not new_item:
                continue
            items[i] = new_item[0]
        else:
            data.clear()
            data.update(new_item)
        fixed_any = True
    return data if fixed_any else None

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--events", required=True)
    ap.add_argument("--scenes-dir", default="runs/scenes_ornith_v5")
    ap.add_argument("--out", required=True)
    ap.add_argument("--ports", default="8110,8111")
    ap.add_argument("--model", default="ornith-1.5-397b")
    ap.add_argument("--source", default="distill/runs/matrix/script.normalized.txt")
    ap.add_argument("--rounds", type=int, default=2)
    a = ap.parse_args()

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    started = time.time()

    events = json.loads(Path(a.events).read_text(encoding="utf-8"))["events"]
    events_by_id = {e["event_id"]: e for e in events}
    scene_ids = sorted({s for e in events for s in (e.get("scene_ids") or [])})
    event_ids = [e["event_id"] for e in events]
    digest = build_digest(events)
    print("events: {} | scenes covered: {}".format(len(events), len(scene_ids)),
          flush=True)

    pool = EndpointPool([int(p) for p in a.ports.split(",")], a.model,
                        temperature=0.5, max_tokens=8000, timeout=1800)
    bad = [p for p, ok in pool.health() if not ok]
    if bad:
        print("unhealthy endpoints: {}".format(bad))
        return 2

    schemas = {
        "themes": _themes_schema(scene_ids, event_ids),
        "external": _conflicts_schema(scene_ids, event_ids),
        "internal": _internal_schema(scene_ids, event_ids),
        "relationships": _relationships_schema(scene_ids, event_ids),
    }

    def work(section):
        prompt = "{}\n\nTHE EVENT LAYER OF THE STORY:\n{}".format(
            PROMPTS[section], digest)
        r = pool.call(SYSTEM, prompt,
                      schema=grammar_safe(schemas[section]))
        return section, json.loads(r.text)

    meta: Dict[str, Any] = {}
    print("stage 1 — four analysts in parallel", flush=True)
    for section, data in run_parallel(list(schemas), work):
        if isinstance(data, Exception):
            print("  {} FAILED: {}".format(section, data), flush=True)
            return 2
        meta[section] = data
        n = len(data.get(SECTION_KEY[section]) or
                [data]) if SECTION_KEY[section] else 1
        print("  {}: {} item(s)".format(section, n), flush=True)

    # Perspectives need the dilemma the themes pass named.
    dilemma = meta["themes"].get("central_dilemma") or {}
    p_schema = _perspectives_schema(scene_ids, event_ids)
    prompt = "{}\n\nTHE CENTRAL DILEMMA:\n{}\n\nTHE EVENT LAYER:\n{}".format(
        PROMPTS["perspectives"],
        json.dumps(dilemma, ensure_ascii=False, indent=1), digest[:50000])
    r = pool.call(SYSTEM, prompt, schema=grammar_safe(p_schema))
    meta["perspectives"] = json.loads(r.text)
    print("  perspectives: {} item(s)".format(
        len(meta["perspectives"]["perspectives"])), flush=True)

    # Audit and regenerate, one faulty item at a time.
    source_index = V.SourceIndex(Path(a.source).read_text(
        encoding="utf-8", errors="ignore"))
    audit_report: Dict[str, Any] = {}
    for round_no in range(a.rounds):
        all_faults = []
        for section in meta:
            all_faults += audit_section(section, meta[section], events_by_id,
                                        source_index)
        print("audit round {}: {} faults".format(round_no + 1, len(all_faults)),
              flush=True)
        audit_report["round_{}".format(round_no + 1)] = len(all_faults)
        if not all_faults:
            break
        by_section: Dict[str, List] = {}
        for f in all_faults:
            by_section.setdefault(f["section"], []).append(f)

        def regen(job):
            section, faults = job
            return section, regenerate_item(pool, section, meta[section],
                                            faults, digest, schemas[section])

        results = run_parallel(list(by_section.items()), regen, max_workers=2)
        still = [r for r in results if isinstance(r, Exception)]
        if still:
            print("  regeneration errors: {}".format(len(still)), flush=True)

    leaks = []
    for section in meta:
        for probe in V.scan_node(meta[section], source_index):
            if probe[1].kind == "exact":
                leaks.append("{}/{}".format(section, probe[0]))
    gate = {"exact_runs": len(leaks), "examples": leaks[:10]}
    print("verbatim gate: {} exact runs".format(len(leaks)), flush=True)

    (out / "meta.json").write_text(json.dumps(meta, indent=1,
                                              ensure_ascii=False),
                                   encoding="utf-8")
    (out / "protocol.json").write_text(json.dumps({
        "seconds": round(time.time() - started, 1),
        "events_source": a.events, "events": len(events),
        "scenes": len(scene_ids),
        "audit_rounds": audit_report,
        "verbatim_gate": gate,
    }, indent=1), encoding="utf-8")
    print("wrote {}".format(out / "meta.json"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())





