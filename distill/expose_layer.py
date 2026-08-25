#!/usr/bin/env python3
"""Expose layer: readable treatment of the story, repo format:
ending_first + sectioned synopsis + jacket_copy. Grounded in the story
root and all downstream layers; judged against the X rubric."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, "/home/deployer/laion/project-alexandria/screenplay/src")
from screenplay_ku.client import EndpointPool  # noqa: E402
from screenplay_ku.kuschema import grammar_safe  # noqa: E402
import meta_layer as ml  # noqa: E402

EXPOSE_SCHEMA = grammar_safe({"type": "object", "properties": {
    "ending_first": {"type": "object", "properties": {
        "ending": {"type": "string", "minLength": 150,
                   "maxLength": 1200}},
        "required": ["ending"], "additionalProperties": False},
    "synopsis": {"type": "object", "minProperties": 5, "maxProperties": 12,
                 "additionalProperties": {"type": "object", "properties": {
                     "text": {"type": "string", "minLength": 200,
                              "maxLength": 1800}},
                     "required": ["text"],
                     "additionalProperties": False}},
    "jacket_copy": {"type": "string", "minLength": 200,
                    "maxLength": 900}},
    "required": ["ending_first", "synopsis", "jacket_copy"],
    "additionalProperties": False})

JUDGE_SCHEMA = grammar_safe({"type": "object", "properties": {"scores": {
    "type": "array", "minItems": 9, "maxItems": 9, "items": {
    "type": "object", "properties": {
        "dim": {"type": "string"},
        "score": {"type": "integer", "minimum": 1, "maximum": 5},
        "note": {"type": "string", "maxLength": 200}},
    "required": ["dim", "score", "note"],
    "additionalProperties": False}}},
    "required": ["scores"], "additionalProperties": False})

DIMS = ["X1 Cold comprehensibility", "X2 World explained only where it matters",
        "X3 Entity introduction in context", "X4 Causal chain honours every plot",
        "X5 Structural conformity", "X6 In-world jargon glossed",
        "X7 Processing fluency / readability",
        "X8 Protagonist likeability and the open heart",
        "X9 Human-experience topics woven in"]

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="runs/story_root_v1/story_root.json")
    ap.add_argument("--events", default="runs/events_build10_full/events.json")
    ap.add_argument("--meta", default="runs/meta_layer_v2b/meta.json")
    ap.add_argument("--entities", default="runs/entity_trial_v2/profiles.json")
    ap.add_argument("--out", required=True)
    ap.add_argument("--ports", default="8110,8111")
    ap.add_argument("--model", default="ornith-1.5-397b")
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    root = json.loads(Path(a.root).read_text(encoding="utf-8"))
    events = json.loads(Path(a.events).read_text(encoding="utf-8"))["events"]
    meta = json.loads(Path(a.meta).read_text(encoding="utf-8"))
    ents = json.loads(Path(a.entities).read_text(encoding="utf-8"))
    if not isinstance(ents, list):
        ents = ents.get("entities", [])
    pool = EndpointPool([int(p) for p in a.ports.split(",")], a.model,
                        temperature=0.5, max_tokens=8000, timeout=1800)
    digest = ml.build_digest(events)
    ctx = ("STORY ROOT:\n" + json.dumps(root, ensure_ascii=False)[:8000]
           + "\nEVENT LAYER:\n" + digest[:50000]
           + "\nMETA LAYER:\n" + json.dumps(meta, ensure_ascii=False)[:25000]
           + "\nENTITIES:\n" + json.dumps(
               [{k: e.get(k) for k in ("name", "role", "appearance",
                  "skills", "background")} for e in ents],
               ensure_ascii=False)[:12000])
    prompt = ("Write the EXPOSE of this story in three parts. (1) "
              "ending_first: tell how it ends, plainly. (2) synopsis: five "
              "to ten numbered sections (keys s01, s02, ...) that retell "
              "the story causally from beginning to end -- introduce every "
              "named entity in context, explain world terms only where a "
              "cold reader needs them and gloss jargon inline, keep every "
              "plot thread recognisable without naming plot mechanics, make "
              "the protagonist someone a reader can open their heart to, "
              "and let the human-experience questions surface through what "
              "happens rather than as statements. (3) jacket_copy: back-"
              "cover text that sells the book without spoiling the ending. "
              "Everything must agree with the layers below; invent nothing."
              + ctx)
    expose = json.loads(pool.call(ml.SYSTEM, prompt,
                                  schema=EXPOSE_SCHEMA).text)
    wc = sum(len(s["text"].split()) for s in expose["synopsis"].values())
    print("sections:", len(expose["synopsis"]), "| synopsis words:", wc,
          flush=True)

    jd = json.loads(pool.call(ml.SYSTEM, (
        "Judge this expose against each dimension, score 1-5 with a "
        "one-line note. Dimensions: " + "; ".join(DIMS) +
        "\nEXPOSE:\n" + json.dumps(expose, ensure_ascii=False)[:40000]),
        schema=JUDGE_SCHEMA).text)["scores"]
    mean = round(sum(s["score"] for s in jd) / len(jd), 2)
    gate = "PASS" if mean >= 4.0 and min(s["score"] for s in jd) >= 3 \
           else "FAIL"
    (out / "expose.json").write_text(json.dumps(dict(
        expose, synopsis_word_count=wc), indent=1, ensure_ascii=False),
        encoding="utf-8")
    md = ["# Expose", "", "## Jacket copy", expose["jacket_copy"], "",
          "## Synopsis"]
    for k in sorted(expose["synopsis"]):
        md += ["### " + k, expose["synopsis"][k]["text"], ""]
    md += ["## Ending first", expose["ending_first"]["ending"]]
    (out / "expose.md").write_text("\n".join(md), encoding="utf-8")
    (out / "judgement.json").write_text(json.dumps(
        {"gate": gate, "mean": mean,
         "scores": {s["dim"]: s["score"] for s in jd},
         "notes": {s["dim"]: s["note"] for s in jd}}, indent=1),
        encoding="utf-8")
    print("EXPOSE", gate, "mean", mean, flush=True)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
