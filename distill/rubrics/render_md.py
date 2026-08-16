#!/usr/bin/env python3
"""Render the JSON rubrics into one human-readable markdown file.

The JSON is the source of truth; RUBRICS.md is generated. Run from anywhere:

    python3 distill/rubrics/render_md.py
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ORDER = ["universal", "root", "expose", "entity", "plot", "event", "scene",
         "trace", "reconstruction"]


def anchors_table(anchors: dict) -> list[str]:
    out = ["", "| | |", "|---|---|"]
    for score in ("1", "3", "5"):
        if score in anchors:
            out.append(f"| **{score}** | {anchors[score]} |")
    out.append("")
    return out


def render_dimension(dim: dict) -> list[str]:
    out = [f"#### {dim['id']} · {dim['name']}", ""]
    if dim.get("question"):
        out += [f"*{dim['question']}*", ""]
    for key, label in (("why", "Why it exists"), ("source", "Source"),
                       ("reading", "Reading"), ("scope", "Scope"),
                       ("computed", "Computed"), ("applies_to", "Applies to"),
                       ("applies_when", "Applies when"),
                       ("measured_context", "Measured context"),
                       ("note", "Note")):
        if dim.get(key):
            out.append(f"**{label}.** {dim[key]}")
            out.append("")
    if dim.get("per_item"):
        out += [f"**Scored per item** over `{dim.get('item_key', '?')}` — "
                "one score per element, reported individually and as a mean.", ""]
    if "anchors" in dim:
        out += anchors_table(dim["anchors"])
    for variant in ("anchors_sighted", "anchors_blind"):
        if variant in dim:
            out += [f"*{variant.replace('anchors_', '').capitalize()} reading:*"]
            out += anchors_table(dim[variant])
    if dim.get("checkable_items"):
        out += ["Checkable items — the judge counts how many are present *and consequential*:", ""]
        out += [f"- {item}" for item in dim["checkable_items"]]
        out.append("")
    return out


def render(doc: dict) -> list[str]:
    out = [f"## {doc['title']}", ""]
    for key, label in (("provenance", "Provenance"), ("posture", "Posture"),
                       ("what_it_is", "What it is"),
                       ("honesty_note", "Honesty note"),
                       ("notes", "Notes"), ("assembly", "Assembly"),
                       ("applies_to", "Applies to"),
                       ("measured_context", "Measured context")):
        if doc.get(key):
            out += [f"**{label}.** {doc[key]}", ""]
    if doc.get("inherits"):
        out += [f"Inherits the **{doc['inherits']}** dimensions (A–G).", ""]
    if doc.get("gate"):
        g = doc["gate"]
        out += [f"**Gate:** every dimension ≥ {g['min_per_dimension']} and mean ≥ "
                f"{g['min_mean']}; at most {g['max_rounds']} rounds, then "
                f"{g['on_gate_miss']}.", ""]
    if doc.get("length_budget"):
        lb = doc["length_budget"]
        out += [f"**Length budget:** {lb['rule']} Derived from `{lb['derived_from']}`, "
                f"tolerance ±{int(lb['tolerance'] * 100)}%. {lb['note']}", ""]
    if doc.get("scoring_rules"):
        out += ["**Scoring rules:**", ""]
        out += [f"- {r}" for r in doc["scoring_rules"]]
        out.append("")
    if doc.get("mechanical_prechecks"):
        out += ["**Mechanical prechecks** — run in code before a judge call is spent; "
                "a failure returns the artifact to the author with the failing "
                "assertion as the instruction:", ""]
        out += [f"- {c}" for c in doc["mechanical_prechecks"]]
        out.append("")
    if doc.get("applicability"):
        out += ["**Applicability by entity kind:**", "", "| kind | dimensions |", "|---|---|"]
        for kind, dims in doc["applicability"].items():
            out.append(f"| {kind} | {', '.join(dims)} |")
        out.append("")
    for dim in doc["dimensions"]:
        out += render_dimension(dim)
    return out


def main() -> None:
    lines = [
        "# Distillation rubrics",
        "",
        "**Generated from the JSON in this directory by `render_md.py`. Edit the JSON, not this file.**",
        "",
        "Every node type takes the seven universal dimensions (A–G) plus its own. "
        "Reconstruction runs additionally take R1 and R2. The gate for every node "
        "type is the same: **every dimension ≥ 3 and the mean ≥ 4**.",
        "",
        "The universal dimensions and R1/R2 are reproduced *verbatim* from "
        "`docs/07-quality-evaluation.md`. That is deliberate: scores from this "
        "pipeline are only comparable with the GLM-5.2 and Qwen3.8-27B passes "
        "already recorded there if a 3 means the same thing in all of them. "
        "Everything else here is new.",
        "",
        "---",
        "",
    ]
    for name in ORDER:
        doc = json.loads((HERE / f"{name}.json").read_text())
        lines += render(doc)
        lines += ["---", ""]
    (HERE / "RUBRICS.md").write_text("\n".join(lines).rstrip() + "\n")
    print(f"wrote {HERE / 'RUBRICS.md'}")


if __name__ == "__main__":
    main()
