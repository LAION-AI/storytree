"""Offline tests for the drama-structure layer's deterministic parts.

No model calls: screen positions, anchor annotation, the audit, and the
digest handed to upper layers. Run: python3 -m pytest tests/test_drama_structure.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "distill"))

import drama_structure_layer as dl  # noqa: E402

EVENTS = [
    {"event_id": "ev-001", "scene_ids": ["sc-001", "sc-002"]},
    {"event_id": "ev-002", "scene_ids": ["sc-003"]},
    {"event_id": "ev-003", "scene_ids": ["sc-004", "sc-005", "sc-006"]},
    {"event_id": "ev-004", "scene_ids": ["sc-007", "sc-008"]},
]
BY_ID = {e["event_id"]: e for e in EVENTS}


class FakeIndex:
    """Verbatim index that never matches anything."""


def _no_scan(node, index):
    return []


dl.V.SourceIndex = FakeIndex  # tests never touch a real screenplay
_real_scan = dl.V.scan_node


def setup_module(_m):
    dl.V.scan_node = _no_scan


def teardown_module(_m):
    dl.V.scan_node = _real_scan


def test_screen_positions_ordered_and_normalized():
    pos = dl.screen_positions(EVENTS)
    assert list(pos) == ["ev-001", "ev-002", "ev-003", "ev-004"]
    vals = list(pos.values())
    assert vals == sorted(vals)
    assert 0 < vals[0] < vals[-1] < 1
    # ev-001 covers scenes 1-2 of 8 -> middle at 1/8
    assert abs(pos["ev-001"] - 0.125) < 1e-9


def test_annotate_anchors_sorts_by_screen_order_and_ids_follow():
    anchors = [
        {"kind": "climax", "event_ids": ["ev-004"]},
        {"kind": "inciting_incident", "event_ids": ["ev-001"]},
    ]
    dl.annotate_anchors(anchors, dl.screen_positions(EVENTS))
    assert [a["kind"] for a in anchors] == ["inciting_incident", "climax"]
    assert [a["id"] for a in anchors] == ["ds-01", "ds-02"]
    assert anchors[0]["screen_position"] < anchors[1]["screen_position"]


def _drama(acts, narration="linear"):
    anchors = [
        {"kind": "inciting_incident", "event_ids": ["ev-001"],
         "evidence": [{"event_id": "ev-001", "scene_id": "sc-001",
                       "grounding": "the disturbance lands here"}]},
        {"kind": "climax", "event_ids": ["ev-004"],
         "evidence": [{"event_id": "ev-004", "scene_id": "sc-007",
                       "grounding": "the question is settled here"}]},
    ]
    dl.annotate_anchors(anchors, dl.screen_positions(EVENTS))
    return {
        "analysis_scope": {"narration_mode": narration},
        "anchors": anchors,
        "acts": acts,
        "hero_journey": {"stages": []},
    }


def test_audit_clean_tree_has_no_faults():
    d = _drama([
        {"start_boundary": "START", "end_boundary": "ds-01"},
        {"start_boundary": "ds-01", "end_boundary": "END"},
    ])
    assert dl.audit(d, BY_ID, FakeIndex()) == []


def test_audit_catches_gap_missing_end_and_bad_refs():
    d = _drama([
        {"start_boundary": "START", "end_boundary": "ds-01"},
        {"start_boundary": "ds-02", "end_boundary": "ds-02"},  # gap + no END
    ])
    d["anchors"][0]["event_ids"].append("ev-999")  # dangling event
    d["hero_journey"]["stages"] = [
        {"stage": "ordeal", "status": "supported", "anchor_ids": []}]
    details = " | ".join(f["detail"] for f in dl.audit(d, BY_ID, FakeIndex()))
    assert "not contiguous" in details
    assert "does not reach END" in details
    assert "ev-999" in details
    assert "'supported' but cites no anchors" in details


def test_audit_scene_must_belong_to_cited_event():
    d = _drama([])
    d["anchors"][0]["evidence"][0]["scene_id"] = "sc-007"  # lives in ev-004
    details = [f["detail"] for f in dl.audit(d, BY_ID, FakeIndex())]
    assert any("does not contain it" in x for x in details)


def test_drama_digest_is_compact_and_navigational():
    d = _drama([{"start_boundary": "START", "end_boundary": "END",
                 "label": "the whole film", "dramatic_question": "q?"}])
    d["analysis_scope"]["primary_lens"] = "three_act"
    d["dramatic_core"] = {"central_dramatic_question": "who pays?"}
    d["ending"] = {"plot_closure": "closed"}
    out = json.loads(dl.drama_digest(d))
    assert out["primary_lens"] == "three_act"
    assert out["anchors"][0]["id"] == "ds-01"
    assert "evidence" not in out["anchors"][0]  # rationales are dropped
    assert out["ending"]["plot_closure"] == "closed"


def test_plan_view_strips_everything_top_down_cannot_know():
    d = _drama([{"start_boundary": "START", "end_boundary": "ds-01",
                 "label": "setup", "dramatic_question": "q?",
                 "state_delta": "x", "confidence": "high"}])
    d["analysis_scope"]["primary_lens"] = "three_act"
    d["dramatic_core"] = {"central_dramatic_question": "who pays?"}
    d["exposition"] = {"initial_world": "w",
                       "established": [{"function": "want", "claim": "c",
                                        "evidence": [{"event_id": "ev-001",
                                                      "scene_id": "sc-001",
                                                      "grounding": "g"}]}],
                       "closes_or_reframes_event_id": "ev-002"}
    d["ending"] = {"plot_closure": "closed"}
    plan = dl.plan_view(d)
    blob = json.dumps(plan)
    # No pointer into material that does not exist at planning time.
    assert "ev-001" not in blob and "sc-001" not in blob
    assert "ev-002" not in blob
    assert "evidence" not in blob
    assert plan["version"] == "plan-1.0"
    # ...but the decisions themselves survive, including act boundaries,
    # which reference anchor ids and stay valid inside the plan.
    assert plan["anchors"][0]["kind"] == "inciting_incident"
    assert plan["anchors"][0]["intended_position"] is not None
    assert plan["acts"][0]["start_boundary"] == "START"
    assert plan["acts"][0]["end_boundary"] == "ds-01"
    assert plan["exposition"]["establishes"][0]["claim"] == "c"
    assert plan["ending"]["plot_closure"] == "closed"


def test_meta_condensed_keeps_only_the_needed_slice():
    meta = {"themes": {"central_dilemma": {"name": "duty vs love"},
                       "big_questions": [{"question": "what is owed?",
                                          "why_central": "...",
                                          "evidence": []}]},
            "external": {"conflicts": [{"name": "should not appear"}]}}
    out = json.loads(dl.meta_condensed(meta))
    assert out["central_dilemma"]["name"] == "duty vs love"
    assert out["big_questions"] == ["what is owed?"]
    assert "should not appear" not in json.dumps(out)
