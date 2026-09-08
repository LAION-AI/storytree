#!/usr/bin/env python3
"""Build the DRAMA STRUCTURE layer: lens, anchors, acts, archetypes, ending.

A sibling of the meta layer, not a rewrite of it. The meta layer answers
"what is this story about" (dilemma, conflicts, relationships); this layer
answers "how is it BUILT" — which structural lens fits (three-act,
kishotenketsu, ensemble, nonlinear, ...), where the load-bearing turns sit
(inciting incident, midpoint, crisis, climax, ...), how the acts segment,
whether Hero's-Journey patterns genuinely apply, and what kind of ending it
is. Design doc: docs/20-drama-structure-layer.md; placement/schema history:
docs/18-dramatic-structure-extension.md; full analyst reference:
docs/19-dramaturgy-cheatsheet.md.

The analyst's context always contains the condensed dramaturgy cheat sheet
(distill/prompts/dramaturgy_condensed.md) so the vocabulary, the recognition
tests and the "frameworks are lenses, not facts" discipline ride along in
every call. Four passes, each grounded in event/scene ids:

  1. mode           — lens + narration mode + dramatic core + exposition
  2. anchors        — the turning points, controlled vocabulary, evidence
  3. acts           — act segmentation + optional sequences (needs 1+2)
  4. patterns_ending — Hero's-Journey statuses + ending axes + diagnostics

Screen positions are computed deterministically from event order — the model
is never asked to count pages. Everything is audited (references resolve,
acts contiguous for linear lenses, supported stages cite anchors, verbatim
gate) and faulty items are regenerated with the fault named, same discipline
as the meta layer.

Usage:
  python3 distill/drama_structure_layer.py --events runs/trees/X/events/events.json \
      --meta runs/trees/X/meta/meta.json --out runs/trees/X/drama \
      --ports 8899 --model muse-spark-1.2-contributor-free \
      --source runs/trees/X/script.normalized.txt
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, "/home/deployer/laion/project-alexandria/screenplay/src")
from screenplay_ku.client import EndpointPool  # noqa: E402
from screenplay_ku.kuschema import grammar_safe  # noqa: E402
import meta_layer as ml  # noqa: E402  (build_digest, shared conventions)
import verbatim as V  # noqa: E402

CHEATSHEET_PATH = Path(__file__).resolve().parent / "prompts" / "dramaturgy_condensed.md"

SYSTEM = (
    "You analyse the dramatic STRUCTURE of a story from its finished scene, "
    "event and meta layers, guided by the dramaturgy reference in your "
    "context. Frameworks are lenses, not facts: you describe before naming, "
    "you prefer 'ambiguous' or 'not_applicable' over a forced template, and "
    "you ground every material claim in event and scene ids. You never "
    "invent scenes, characters or events. You return only valid JSON."
)

ANCHOR_KINDS = [
    "opening_situation", "hook", "inciting_incident", "debate_or_refusal",
    "commitment_threshold", "act_break", "first_trial",
    "progressive_complication", "pinch_point", "midpoint", "reversal",
    "recognition", "reframing_reveal", "all_is_lost", "crisis", "climax",
    "false_ending", "denouement", "kiss_off", "cliffhanger",
]
LENSES = ["three_act", "five_act", "eight_sequence", "archplot", "miniplot",
          "antiplot", "kishotenketsu", "episodic", "parallel_ensemble",
          "framed", "nonlinear", "ambiguous"]
NARRATION = ["linear", "nonlinear", "parallel", "framed", "episodic",
             "ambiguous"]
VOGLER = ["ordinary_world", "call_to_adventure", "refusal",
          "meeting_with_mentor", "crossing_first_threshold",
          "tests_allies_enemies", "approach_to_inmost_cave", "ordeal",
          "reward", "road_back", "resurrection", "return_with_elixir"]
STATUS = ["observed", "supported_inference", "ambiguous"]
STAGE_STATUS = ["supported", "ambiguous", "absent", "not_applicable"]
CONF = ["low", "medium", "high"]
ESCALATION = ["obstacle_ladder", "narrowing_options", "expanding_scope",
              "deepening_cost", "information_reversal", "time_compression",
              "role_reversal", "convergence", "none"]
DIAG_CODES = ["unclear_dramatic_question", "low_escalation", "unearned_turn",
              "unresolved_thread", "orphaned_setup",
              "climax_question_mismatch", "exposition_overload_risk",
              "framework_overfit_risk"]


# ------------------------------------------------------------- schemas
def _ev_ref(scene_ids: Sequence[str], event_ids: Sequence[str]) -> Dict[str, Any]:
    """Evidence pointer, same shape as the meta layer's."""
    return {
        "type": "object",
        "properties": {
            "event_id": {"type": "string", "enum": list(event_ids)},
            "scene_id": {"type": "string", "enum": list(scene_ids)},
            "grounding": {"type": "string", "minLength": 15, "maxLength": 300},
        },
        "required": ["event_id", "scene_id", "grounding"],
        "additionalProperties": False,
    }


def mode_schema(scene_ids, event_ids):
    alt = {"type": "object", "properties": {
        "lens": {"type": "string", "enum": LENSES},
        "confidence": {"type": "string", "enum": CONF},
        "why_not_primary": {"type": "string", "minLength": 20, "maxLength": 300},
    }, "required": ["lens", "confidence", "why_not_primary"],
        "additionalProperties": False}
    est = {"type": "object", "properties": {
        "function": {"type": "string", "enum":
                     ["want", "stakes", "world_rule", "relationship",
                      "threat", "tone"]},
        "claim": {"type": "string", "minLength": 20, "maxLength": 300},
        "evidence": {"type": "array", "minItems": 1, "maxItems": 3,
                     "items": _ev_ref(scene_ids, event_ids)},
    }, "required": ["function", "claim", "evidence"],
        "additionalProperties": False}
    return {
        "type": "object",
        "properties": {
            "analysis_scope": {"type": "object", "properties": {
                "narration_mode": {"type": "string", "enum": NARRATION},
                "primary_lens": {"type": "string", "enum": LENSES},
                "confidence": {"type": "string", "enum": CONF},
                "why_this_lens": {"type": "string", "minLength": 60,
                                  "maxLength": 700},
                "alternatives": {"type": "array", "minItems": 0,
                                 "maxItems": 3, "items": alt},
            }, "required": ["narration_mode", "primary_lens", "confidence",
                            "why_this_lens", "alternatives"],
                "additionalProperties": False},
            "dramatic_core": {"type": "object", "properties": {
                "central_dramatic_question": {"type": "string",
                                              "minLength": 20,
                                              "maxLength": 300},
                "values_at_stake": {"type": "array", "minItems": 1,
                                    "maxItems": 5,
                                    "items": {"type": "string",
                                              "minLength": 3,
                                              "maxLength": 60}},
                "clock_or_urgency": {"type": "string", "minLength": 5,
                                     "maxLength": 300},
            }, "required": ["central_dramatic_question", "values_at_stake",
                            "clock_or_urgency"],
                "additionalProperties": False},
            "exposition": {"type": "object", "properties": {
                "initial_world": {"type": "string", "minLength": 60,
                                  "maxLength": 700},
                "established": {"type": "array", "minItems": 2, "maxItems": 8,
                                "items": est},
                "closes_or_reframes_event_id": {"type": "string",
                                                "enum": list(event_ids)},
            }, "required": ["initial_world", "established",
                            "closes_or_reframes_event_id"],
                "additionalProperties": False},
        },
        "required": ["analysis_scope", "dramatic_core", "exposition"],
        "additionalProperties": False,
    }


def anchors_schema(scene_ids, event_ids):
    return {
        "type": "object",
        "properties": {"anchors": {
            "type": "array", "minItems": 4, "maxItems": 14,
            "items": {
                "type": "object",
                "properties": {
                    "kind": {"type": "string", "enum": ANCHOR_KINDS},
                    # An anchor may carry several functions (recognition that
                    # is also the midpoint); kind is the primary one.
                    "also_functions_as": {"type": "array", "minItems": 0,
                                          "maxItems": 3,
                                          "items": {"type": "string",
                                                    "enum": ANCHOR_KINDS}},
                    "event_ids": {"type": "array", "minItems": 1,
                                  "maxItems": 3,
                                  "items": {"type": "string",
                                            "enum": list(event_ids)}},
                    "change": {"type": "string", "minLength": 40,
                               "maxLength": 500},
                    "why_this_function": {"type": "string", "minLength": 40,
                                          "maxLength": 500},
                    "evidence": {"type": "array", "minItems": 1,
                                 "maxItems": 3,
                                 "items": _ev_ref(scene_ids, event_ids)},
                    "status": {"type": "string", "enum": STATUS},
                    "confidence": {"type": "string", "enum": CONF},
                },
                "required": ["kind", "also_functions_as", "event_ids",
                             "change", "why_this_function", "evidence",
                             "status", "confidence"],
                "additionalProperties": False,
            }}},
        "required": ["anchors"], "additionalProperties": False,
    }


def acts_schema(anchor_ids, event_ids):
    """Acts reference anchors by id; START/END mark the film's edges."""
    bound = {"type": "string", "enum": ["START", "END"] + list(anchor_ids)}
    return {
        "type": "object",
        "properties": {
            "acts": {"type": "array", "minItems": 1, "maxItems": 6, "items": {
                "type": "object",
                "properties": {
                    "label": {"type": "string", "minLength": 8,
                              "maxLength": 120},
                    "start_boundary": bound,
                    "end_boundary": bound,
                    "dramatic_question": {"type": "string", "minLength": 20,
                                          "maxLength": 300},
                    "state_delta": {"type": "string", "minLength": 40,
                                    "maxLength": 500},
                    "confidence": {"type": "string", "enum": CONF},
                },
                "required": ["label", "start_boundary", "end_boundary",
                             "dramatic_question", "state_delta",
                             "confidence"],
                "additionalProperties": False}},
            "sequences": {"type": "array", "minItems": 0, "maxItems": 10,
                          "items": {
                "type": "object",
                "properties": {
                    "label": {"type": "string", "minLength": 8,
                              "maxLength": 120},
                    "event_ids": {"type": "array", "minItems": 2,
                                  "maxItems": 8,
                                  "items": {"type": "string",
                                            "enum": list(event_ids)}},
                    "objective": {"type": "string", "minLength": 20,
                                  "maxLength": 300},
                    "escalation_pattern": {"type": "string",
                                           "enum": ESCALATION},
                    "outcome": {"type": "string", "minLength": 20,
                                "maxLength": 300},
                    "value_shift": {"type": "string", "minLength": 5,
                                    "maxLength": 120},
                },
                "required": ["label", "event_ids", "objective",
                             "escalation_pattern", "outcome", "value_shift"],
                "additionalProperties": False}},
        },
        "required": ["acts", "sequences"], "additionalProperties": False,
    }


def patterns_schema(anchor_ids):
    stage = {"type": "object", "properties": {
        "stage": {"type": "string", "enum": VOGLER},
        "status": {"type": "string", "enum": STAGE_STATUS},
        "anchor_ids": {"type": "array", "minItems": 0, "maxItems": 3,
                       "items": {"type": "string", "enum": list(anchor_ids)}},
        "note": {"type": "string", "minLength": 10, "maxLength": 300},
    }, "required": ["stage", "status", "anchor_ids", "note"],
        "additionalProperties": False}
    return {
        "type": "object",
        "properties": {
            "hero_journey": {"type": "object", "properties": {
                "applicability": {"type": "string", "enum":
                                  ["organising", "partial",
                                   "not_applicable"]},
                "why": {"type": "string", "minLength": 40, "maxLength": 500},
                "stages": {"type": "array", "minItems": 0, "maxItems": 12,
                           "items": stage},
            }, "required": ["applicability", "why", "stages"],
                "additionalProperties": False},
            "ending": {"type": "object", "properties": {
                "plot_closure": {"type": "string", "enum":
                                 ["closed", "partially_closed", "open",
                                  "deliberately_unresolved"]},
                "central_question_result": {"type": "string", "enum":
                                            ["affirmed", "answered_negative",
                                             "reframed", "refused",
                                             "ambiguous"]},
                "fortune_direction": {"type": "string", "enum":
                                      ["positive", "negative", "mixed",
                                       "ironic", "cyclical"]},
                "character_movement": {"type": "string", "enum":
                                       ["changed", "unchanged_by_choice",
                                        "changed_by_revelation", "corrupted",
                                        "unknown"]},
                "final_gesture": {"type": "string", "enum":
                                  ["denouement", "kiss_off", "cliffhanger",
                                   "callback", "reframing_reveal",
                                   "image_rhyme", "none"]},
                "resolution_denouement_relation": {
                    "type": "string", "minLength": 40, "maxLength": 500},
            }, "required": ["plot_closure", "central_question_result",
                            "fortune_direction", "character_movement",
                            "final_gesture",
                            "resolution_denouement_relation"],
                "additionalProperties": False},
            "diagnostics": {"type": "array", "minItems": 0, "maxItems": 5,
                            "items": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "enum": DIAG_CODES},
                    "severity": {"type": "string", "enum":
                                 ["note", "warning"]},
                    "evidence": {"type": "string", "minLength": 20,
                                 "maxLength": 300},
                },
                "required": ["code", "severity", "evidence"],
                "additionalProperties": False}},
        },
        "required": ["hero_journey", "ending", "diagnostics"],
        "additionalProperties": False,
    }


# ------------------------------------------------------------- prompts
PROMPTS = {
    "mode": (
        "Determine the STRUCTURAL MODE of this story. Choose the "
        "least-forcing primary lens and narration mode, defend the choice "
        "against the credible alternatives, name the central dramatic "
        "question and the values at stake, and analyse the EXPOSITION: what "
        "the initial world is, what the opening establishes (each claim with "
        "evidence), and the event at which the initial situation is closed "
        "off or reframed. If no clock or urgency mechanism exists, say so "
        "explicitly in that field."),
    "anchors": (
        "Locate the STRUCTURAL ANCHORS of this story using the controlled "
        "vocabulary from the reference. Apply the causality test to every "
        "candidate: what valued condition changed, whose strategy changes "
        "because of it, what later event would differ if it were removed. "
        "One event may carry several functions -- one anchor with "
        "also_functions_as, never duplicates. Only film-level turns: a "
        "local subplot beat is not an anchor. Do not manufacture an anchor "
        "kind the material does not support; a story without a midpoint or "
        "kiss-off is a valid result."),
    "acts": (
        "Segment the story into ACTS under the primary lens already chosen, "
        "using the anchors as boundaries (START and END mark the film's "
        "edges). Each act states the question that governs it and what has "
        "changed by its end. Acts must cover the story in screen order "
        "without gaps: each act starts at the boundary where the previous "
        "one ended. Then, ONLY where genuine intermediate units exist, name "
        "SEQUENCES (runs of events united by one objective) with their "
        "escalation pattern -- 'none' is a valid pattern. An episodic or "
        "meditative organisation with few acts is a valid answer."),
    "patterns_ending": (
        "Judge whether the HERO'S JOURNEY (Vogler's 12 stages) genuinely "
        "organises this story: 'organising', 'partial' or 'not_applicable', "
        "with the reason. Mind the false-positive traps in the reference "
        "(inciting incident is not automatically a call to adventure, a "
        "final fight is not a resurrection). Only if organising or partial, "
        "map the stages with statuses; a 'supported' stage must cite "
        "anchors. Then classify the ENDING on the independent axes and "
        "state how resolution, denouement and final gesture relate. "
        "Finally, list at most a few DIAGNOSTICS the evidence justifies -- "
        "they are pointers, not verdicts; an empty list is fine."),
}


# ------------------------------------------------- deterministic helpers
def screen_positions(events: Sequence[Dict[str, Any]]) -> Dict[str, float]:
    """Fraction of the story's scenes that lie before each event's middle.

    Computed from the ordered event list, never asked from the model. An
    event covering scenes 10-14 of 100 sits at (10 + 2.5) / 100 = 0.125.
    """
    counts = [max(1, len(e.get("scene_ids") or [])) for e in events]
    total = sum(counts)
    pos, before = {}, 0
    for e, c in zip(events, counts):
        pos[e["event_id"]] = round((before + c / 2) / total, 3)
        before += c
    return pos


def annotate_anchors(anchors: List[Dict], positions: Dict[str, float]) -> None:
    """Attach id + deterministic screen_position to each anchor, in place."""
    for i, a in enumerate(anchors):
        a["id"] = "ds-{:02d}".format(i + 1)
        cited = [positions[e] for e in a.get("event_ids") or []
                 if e in positions]
        a["screen_position"] = min(cited) if cited else None
    anchors.sort(key=lambda a: (a["screen_position"] is None,
                                a["screen_position"] or 0))
    for i, a in enumerate(anchors):  # ids follow screen order
        a["id"] = "ds-{:02d}".format(i + 1)


def meta_condensed(meta: Dict[str, Any]) -> str:
    """The slice of the meta layer the structural analyst needs."""
    themes = meta.get("themes", {})
    keep = {
        "central_dilemma": themes.get("central_dilemma"),
        "big_questions": [q.get("question") for q in
                          themes.get("big_questions") or []],
        "perspectives": [{k: p.get(k) for k in
                          ("throughline", "label", "stance_on_dilemma")}
                         for p in (meta.get("perspectives") or {})
                         .get("perspectives") or []],
    }
    return json.dumps(keep, ensure_ascii=False, indent=1)


def drama_digest(drama: Dict[str, Any], cap: int = 12000) -> str:
    """Compact rendering for consumption by upper layers (plots/root/expose).

    Keeps the navigational core -- lens, question, anchors, acts, ending --
    and drops the long free-text rationales.
    """
    scope = drama.get("analysis_scope") or {}
    core = drama.get("dramatic_core") or {}
    keep = {
        "primary_lens": scope.get("primary_lens"),
        "narration_mode": scope.get("narration_mode"),
        "central_dramatic_question": core.get("central_dramatic_question"),
        "anchors": [{k: a.get(k) for k in
                     ("id", "kind", "event_ids", "screen_position", "change")}
                    for a in drama.get("anchors") or []],
        "acts": [{k: x.get(k) for k in
                  ("label", "start_boundary", "end_boundary",
                   "dramatic_question")}
                 for x in drama.get("acts") or []],
        "ending": drama.get("ending"),
    }
    return json.dumps(keep, ensure_ascii=False, indent=1)[:cap]


# ---------------------------------------------------------------- audit
def audit(drama: Dict[str, Any], events_by_id: Dict[str, Dict],
          source_index) -> List[Dict[str, Any]]:
    """Machine-provable faults, each naming the section and item to redo."""
    faults: List[Dict[str, Any]] = []

    def add(section, index, detail):
        faults.append({"section": section, "index": index, "detail": detail})

    def check_refs(section, i, item):
        for eid in item.get("event_ids") or []:
            if eid not in events_by_id:
                add(section, i, "cites event {} which does not exist".format(eid))
        for ev in item.get("evidence") or []:
            eid, sid = ev.get("event_id"), ev.get("scene_id")
            if eid not in events_by_id:
                add(section, i, "evidence cites event {} which does not "
                                "exist".format(eid))
            elif sid not in (events_by_id[eid].get("scene_ids") or []):
                add(section, i, "evidence cites scene {} under event {}, but "
                                "that event does not contain it".format(sid, eid))

    for i, item in enumerate((drama.get("exposition") or {})
                             .get("established") or []):
        check_refs("mode", i, item)

    anchors = drama.get("anchors") or []
    seen_kind_events = set()
    for i, a in enumerate(anchors):
        check_refs("anchors", i, a)
        key = (a.get("kind"), tuple(sorted(a.get("event_ids") or [])))
        if key in seen_kind_events:
            add("anchors", i, "duplicates anchor kind {} on the same "
                              "events".format(a.get("kind")))
        seen_kind_events.add(key)

    anchor_ids = {a.get("id") for a in anchors}
    acts = drama.get("acts") or []
    linear = ((drama.get("analysis_scope") or {})
              .get("narration_mode")) == "linear"
    prev_end = "START"
    pos_of = {a.get("id"): a.get("screen_position") for a in anchors}
    for i, act in enumerate(acts):
        for b in (act.get("start_boundary"), act.get("end_boundary")):
            if b not in ("START", "END") and b not in anchor_ids:
                add("acts", i, "references anchor {} which does not "
                               "exist".format(b))
        if act.get("start_boundary") != prev_end:
            add("acts", i, "acts are not contiguous: act starts at {} but the "
                           "previous one ended at {}".format(
                               act.get("start_boundary"), prev_end))
        prev_end = act.get("end_boundary")
        if linear:
            s = pos_of.get(act.get("start_boundary"))
            e = pos_of.get(act.get("end_boundary"))
            if s is not None and e is not None and e <= s:
                add("acts", i, "act ends at screen position {} before it "
                               "starts at {} although narration is "
                               "linear".format(e, s))
    if acts and prev_end != "END":
        add("acts", len(acts) - 1, "the final act does not reach END")

    hj = (drama.get("hero_journey") or {})
    for i, st in enumerate(hj.get("stages") or []):
        if st.get("status") == "supported" and not st.get("anchor_ids"):
            add("patterns_ending", i, "stage {} is 'supported' but cites no "
                                      "anchors".format(st.get("stage")))
        for aid in st.get("anchor_ids") or []:
            if aid not in anchor_ids:
                add("patterns_ending", i, "stage cites anchor {} which does "
                                          "not exist".format(aid))

    for section in ("analysis_scope", "dramatic_core", "exposition",
                    "anchors", "acts", "sequences", "hero_journey",
                    "ending", "diagnostics"):
        node = drama.get(section)
        if node is None:
            continue
        for probe in V.scan_node(node, source_index):
            if probe[1].kind == "exact":
                add(section if section in ("anchors", "acts") else "verbatim",
                    -1, "{} quotes the screenplay verbatim at {}".format(
                        section, probe[0]))
    return faults


# ----------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--events", required=True)
    ap.add_argument("--meta", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--ports", default="8899")
    ap.add_argument("--model", default="muse-spark-1.2-contributor-free")
    ap.add_argument("--source", required=True,
                    help="normalized screenplay, for the verbatim gate")
    ap.add_argument("--rounds", type=int, default=2)
    a = ap.parse_args()

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    started = time.time()

    events = json.loads(Path(a.events).read_text(encoding="utf-8"))["events"]
    meta = json.loads(Path(a.meta).read_text(encoding="utf-8"))
    events_by_id = {e["event_id"]: e for e in events}
    scene_ids = sorted({s for e in events for s in (e.get("scene_ids") or [])})
    event_ids = [e["event_id"] for e in events]
    digest = ml.build_digest(events)
    positions = screen_positions(events)
    cheat = CHEATSHEET_PATH.read_text(encoding="utf-8")
    mcond = meta_condensed(meta)
    print("events: {} | scenes: {} | cheatsheet: {} chars".format(
        len(events), len(scene_ids), len(cheat)), flush=True)

    pool = EndpointPool([int(p) for p in a.ports.split(",")], a.model,
                        temperature=0.4, max_tokens=8000, timeout=1800)
    bad = [p for p, ok in pool.health() if not ok]
    if bad:
        print("unhealthy endpoints: {}".format(bad))
        return 2

    def call(task_key, extra_ctx, schema):
        prompt = "\n\n".join([
            "TASK: " + PROMPTS[task_key],
            "DRAMATURGY REFERENCE (your working rules and vocabulary):\n"
            + cheat,
            extra_ctx,
            "THE EVENT LAYER OF THE STORY (in screen order):\n"
            + digest[:55000]])
        r = pool.call(SYSTEM, prompt, schema=grammar_safe(schema))
        return json.loads(r.text)

    drama: Dict[str, Any] = {"version": "1.0"}

    print("pass 1 — mode / exposition", flush=True)
    p1 = call("mode", "THE META LAYER (condensed):\n" + mcond,
              mode_schema(scene_ids, event_ids))
    drama.update(p1)

    print("pass 2 — anchors", flush=True)
    p2 = call("anchors",
              "THE STRUCTURAL MODE ALREADY DETERMINED:\n"
              + json.dumps(p1["analysis_scope"], ensure_ascii=False, indent=1),
              anchors_schema(scene_ids, event_ids))
    drama["anchors"] = p2["anchors"]
    annotate_anchors(drama["anchors"], positions)
    anchor_ids = [x["id"] for x in drama["anchors"]]
    anchors_view = json.dumps(
        [{k: x.get(k) for k in ("id", "kind", "event_ids",
                                "screen_position", "change")}
         for x in drama["anchors"]], ensure_ascii=False, indent=1)

    print("pass 3 — acts / sequences", flush=True)
    p3 = call("acts",
              "THE STRUCTURAL MODE:\n"
              + json.dumps(p1["analysis_scope"], ensure_ascii=False)
              + "\n\nTHE ANCHORS (in screen order):\n" + anchors_view,
              acts_schema(anchor_ids, event_ids))
    drama["acts"], drama["sequences"] = p3["acts"], p3["sequences"]

    print("pass 4 — hero's journey / ending / diagnostics", flush=True)
    p4 = call("patterns_ending",
              "THE ANCHORS (in screen order):\n" + anchors_view,
              patterns_schema(anchor_ids))
    drama.update(p4)

    # Audit and targeted regeneration, same discipline as the meta layer:
    # the fault is named, the whole pass is redone only for faulty sections.
    source_index = V.SourceIndex(Path(a.source).read_text(
        encoding="utf-8", errors="ignore"))
    audit_report: Dict[str, int] = {}
    for round_no in range(a.rounds):
        faults = audit(drama, events_by_id, source_index)
        audit_report["round_{}".format(round_no + 1)] = len(faults)
        print("audit round {}: {} faults".format(round_no + 1, len(faults)),
              flush=True)
        if not faults:
            break
        by_section: Dict[str, List[str]] = {}
        for f in faults:
            by_section.setdefault(f["section"], []).append(f["detail"])
        try:
            if "mode" in by_section or "verbatim" in by_section:
                p1 = call("mode",
                          "THE META LAYER (condensed):\n" + mcond
                          + "\n\nYOUR PREVIOUS ANSWER FAILED AUDIT:\n"
                          + "\n".join("  - " + d for d in
                                      by_section.get("mode", [])
                                      + by_section.get("verbatim", []))
                          + "\nRedo the pass without these faults.",
                          mode_schema(scene_ids, event_ids))
                drama.update(p1)
            if "anchors" in by_section:
                p2 = call("anchors",
                          "THE STRUCTURAL MODE:\n"
                          + json.dumps(p1["analysis_scope"],
                                       ensure_ascii=False)
                          + "\n\nYOUR PREVIOUS ANCHORS FAILED AUDIT:\n"
                          + "\n".join("  - " + d for d in
                                      by_section["anchors"])
                          + "\nRedo the pass without these faults.",
                          anchors_schema(scene_ids, event_ids))
                drama["anchors"] = p2["anchors"]
                annotate_anchors(drama["anchors"], positions)
                anchor_ids = [x["id"] for x in drama["anchors"]]
                anchors_view = json.dumps(
                    [{k: x.get(k) for k in ("id", "kind", "event_ids",
                                            "screen_position", "change")}
                     for x in drama["anchors"]], ensure_ascii=False, indent=1)
                # anchors changed -> acts and patterns must re-bind
                by_section.setdefault("acts", []).append(
                    "anchors were regenerated; re-bind boundaries")
                by_section.setdefault("patterns_ending", []).append(
                    "anchors were regenerated; re-bind stage citations")
            if "acts" in by_section:
                p3 = call("acts",
                          "THE STRUCTURAL MODE:\n"
                          + json.dumps(p1["analysis_scope"],
                                       ensure_ascii=False)
                          + "\n\nTHE ANCHORS (in screen order):\n"
                          + anchors_view
                          + "\n\nYOUR PREVIOUS ACTS FAILED AUDIT:\n"
                          + "\n".join("  - " + d for d in by_section["acts"])
                          + "\nRedo the pass without these faults.",
                          acts_schema(anchor_ids, event_ids))
                drama["acts"], drama["sequences"] = p3["acts"], p3["sequences"]
            if "patterns_ending" in by_section:
                p4 = call("patterns_ending",
                          "THE ANCHORS (in screen order):\n" + anchors_view
                          + "\n\nYOUR PREVIOUS ANSWER FAILED AUDIT:\n"
                          + "\n".join("  - " + d for d in
                                      by_section["patterns_ending"])
                          + "\nRedo the pass without these faults.",
                          patterns_schema(anchor_ids))
                drama.update(p4)
        except Exception as exc:  # keep the best tree we have; report it
            print("  regeneration error: {}".format(exc), flush=True)
            break

    leaks = sum(1 for _ in V.scan_node(
        {k: v for k, v in drama.items() if k != "version"}, source_index))
    (out / "drama_structure.json").write_text(
        json.dumps(drama, indent=1, ensure_ascii=False), encoding="utf-8")
    (out / "protocol.json").write_text(json.dumps({
        "seconds": round(time.time() - started, 1),
        "events_source": a.events, "events": len(events),
        "scenes": len(scene_ids),
        "anchors": len(drama.get("anchors") or []),
        "acts": len(drama.get("acts") or []),
        "audit_rounds": audit_report,
        "verbatim_probes": leaks,
    }, indent=1), encoding="utf-8")
    print("wrote {}".format(out / "drama_structure.json"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
