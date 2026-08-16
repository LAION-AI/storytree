"""Rubric loading, the critique schema, and the gate.

The gate is deliberately hard and deliberately capped: every dimension >= 3 and
mean >= 4, with at most N rounds. The measured overall mean of this rubric
applied to real nodes was 3.21/5 (docs/07 §2), so a gate at 4.0 is above the
observed distribution. Two things follow and both are recorded rather than
hidden: some artifacts will not pass, and a judge under revision pressure may
drift upward. `gate_report` therefore keeps the full per-round score history so
drift is visible as a rising mean with unchanged evidence.
"""

from __future__ import annotations

import json
import statistics
from dataclasses import dataclass
from pathlib import Path

RUBRIC_DIR = Path(__file__).resolve().parent / "rubrics"

MIN_PER_DIMENSION = 3
MIN_MEAN = 4.0
MAX_ROUNDS = 5


def load(rubric_id: str) -> dict:
    return json.loads((RUBRIC_DIR / f"{rubric_id}.json").read_text())


def load_with_universal(rubric_id: str, *, reconstruction: bool = True) -> dict:
    """The full dimension set for a node type: universal + type + (R1, R2)."""
    doc = load(rubric_id)
    dims = list(load("universal")["dimensions"])
    dims += doc["dimensions"]
    if reconstruction and rubric_id != "reconstruction":
        recon = load("reconstruction")
        dims += [d for d in recon["dimensions"] if d["id"] in ("R1", "R2")]
    out = dict(doc)
    out["dimensions"] = dims
    out["scoring_rules"] = load("universal")["scoring_rules"]
    out["posture"] = load("universal")["posture"]
    return out


def dimension_ids(rubric_id: str, *, reconstruction: bool = True) -> list[str]:
    return [d["id"] for d in
            load_with_universal(rubric_id, reconstruction=reconstruction)["dimensions"]]


def as_prompt_text(rubric_id: str, *, reconstruction: bool = True) -> str:
    """The rubric as the judge sees it: ids, questions and the 1/3/5 anchors."""
    doc = load_with_universal(rubric_id, reconstruction=reconstruction)
    out = [f"POSTURE: {doc['posture']}", ""]
    out += [f"- {rule}" for rule in doc["scoring_rules"]]
    out += ["", f"GATE: every dimension >= {MIN_PER_DIMENSION} and mean >= {MIN_MEAN}.", ""]
    for dim in doc["dimensions"]:
        out.append(f"{dim['id']} · {dim['name']}")
        if dim.get("question"):
            out.append(f"  {dim['question']}")
        if dim.get("per_item"):
            out.append(f"  SCORED PER ITEM over {dim.get('item_key')}.")
        anchors = dim.get("anchors") or dim.get("anchors_sighted") or {}
        for score in ("1", "3", "5"):
            if score in anchors:
                out.append(f"  {score}: {anchors[score]}")
        if dim.get("checkable_items"):
            out.append("  checkable items: " + "; ".join(dim["checkable_items"]))
        out.append("")
    return "\n".join(out)


# --------------------------------------------------------------------------
# Critique schema — what a judge call must return.
# --------------------------------------------------------------------------

def critique_schema(rubric_id: str, *, reconstruction: bool = True) -> dict:
    ids = dimension_ids(rubric_id, reconstruction=reconstruction)
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["node_id", "scores", "mechanical", "gate", "verdict"],
        "properties": {
            "node_id": {"type": "string"},
            "round": {"type": "integer"},
            "scores": {
                "type": "array",
                "minItems": len(ids),
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["dimension", "score", "evidence", "instruction"],
                    "properties": {
                        "dimension": {"enum": ids},
                        "item": {"type": "string",
                                 "description": "for per-item dimensions, which item"},
                        "score": {"type": "integer", "minimum": 1, "maximum": 5},
                        "evidence": {"type": "string",
                                     "description": "one sentence naming a field or quoting text"},
                        "instruction": {"type": "string",
                                        "description": "what to change, concretely"},
                        "part": {"type": "string",
                                 "description": "scene nodes: which sub-call the instruction is for"},
                        "movement": {"enum": ["improved", "held", "regressed", "new"]},
                    },
                },
            },
            "mechanical": {
                "type": "object",
                "description": "computed checks; keys are node-type specific",
                "additionalProperties": True,
            },
            "gate": {
                "type": "object",
                "additionalProperties": False,
                "required": ["min_score", "mean", "passed"],
                "properties": {
                    "min_score": {"type": "integer"},
                    "mean": {"type": "number"},
                    "passed": {"type": "boolean"},
                },
            },
            "verdict": {
                "type": "object",
                "additionalProperties": False,
                "required": ["decision", "top_instructions"],
                "properties": {
                    "decision": {"enum": ["pass", "revise"]},
                    "top_instructions": {"type": "array", "items": {"type": "string"},
                                         "maxItems": 3},
                },
            },
        },
    }


# --------------------------------------------------------------------------
# The gate
# --------------------------------------------------------------------------

@dataclass
class Gate:
    passed: bool
    mean: float
    minimum: int
    missing: list[str]
    below: list[tuple[str, int]]

    def as_dict(self) -> dict:
        return {"passed": self.passed, "mean": round(self.mean, 3),
                "min_score": self.minimum, "missing_dimensions": self.missing,
                "below_threshold": [{"dimension": d, "score": s} for d, s in self.below]}


def evaluate_gate(critique: dict, rubric_id: str, *,
                  reconstruction: bool = True) -> Gate:
    """Recompute the gate in code. Never trust the judge's own `gate` block —
    a self-reported pass is the one thing an evaluator has an incentive to get
    wrong, and it is free to check."""
    expected = set(dimension_ids(rubric_id, reconstruction=reconstruction))
    scores: dict[str, list[int]] = {}
    for row in critique.get("scores", []):
        dim = row.get("dimension")
        if dim in expected and isinstance(row.get("score"), int):
            scores.setdefault(dim, []).append(row["score"])

    # A per-item dimension contributes the mean of its items, then is treated
    # as one dimension: ten badly described plots should not outvote everything.
    collapsed = {dim: statistics.fmean(vals) for dim, vals in scores.items()}
    missing = sorted(expected - set(collapsed))
    if not collapsed:
        return Gate(False, 0.0, 0, missing, [])

    minimum = min(collapsed.values())
    mean = statistics.fmean(collapsed.values())
    below = sorted([(d, int(v)) for d, v in collapsed.items() if v < MIN_PER_DIMENSION])
    passed = (not missing and minimum >= MIN_PER_DIMENSION and mean >= MIN_MEAN)
    return Gate(passed, mean, int(minimum), missing, below)


def evidence_ok(critique: dict, *, min_chars: int = 25) -> list[str]:
    """Scores whose evidence names nothing. `docs/07 §1.1`: a score without a
    field reference is not a score. Returned as findings, not raised — the loop
    decides whether to re-ask."""
    bad = []
    for row in critique.get("scores", []):
        ev = (row.get("evidence") or "").strip()
        if len(ev) < min_chars:
            bad.append(f"{row.get('dimension')}: evidence too short to name anything")
        elif not any(ch in ev for ch in "`\"'.") and "_" not in ev:
            bad.append(f"{row.get('dimension')}: evidence quotes and names nothing")
    return bad
