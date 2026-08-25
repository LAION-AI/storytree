#!/usr/bin/env python3
"""Story-root layer: fills the top-level story root from the screenplay
and ALL downstream layers (events, meta, entities). Three phases:
map (per-chunk spine facts) -> fill (root schema) -> judge (RT rubric)."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, "/home/deployer/laion/project-alexandria/screenplay/src")
from screenplay_ku.client import EndpointPool, run_parallel  # noqa: E402
from screenplay_ku.kuschema import grammar_safe  # noqa: E402
import meta_layer as ml  # noqa: E402

SPINE_SCHEMA = grammar_safe({"type": "object", "properties": {"facts": {
    "type": "array", "minItems": 3, "maxItems": 15, "items": {
    "type": "object", "properties": {
        "aspect": {"type": "string", "enum": ["protagonist_goal",
            "opposition", "turning_point", "climax", "resolution",
            "world_rule", "theme_signal"]},
        "fact": {"type": "string", "minLength": 30, "maxLength": 400},
        "evidence": {"type": "string", "maxLength": 200}},
    "required": ["aspect", "fact", "evidence"],
    "additionalProperties": False}}},
    "required": ["facts"], "additionalProperties": False})

ROOT_SCHEMA = grammar_safe({"type": "object", "properties": {
    "title": {"type": "string", "minLength": 2},
    "logline": {"type": "string", "minLength": 60, "maxLength": 400},
    "premise": {"type": "string", "minLength": 100, "maxLength": 1200},
    "genre_primary": {"type": "string"},
    "genre_secondary": {"type": "string"},
    "audience": {"type": "string"},
    "setting": {"type": "string", "minLength": 40},
    "pov": {"type": "string"},
    "style": {"type": "string", "minLength": 40},
    "narrative_vector": {"type": "object", "properties": {
        "goal": {"type": "string"}, "motivation": {"type": "string"},
        "conflict": {"type": "string"},
        "generative_question": {"type": "string"}},
        "required": ["goal", "motivation", "conflict",
                     "generative_question"], "additionalProperties": False},
    "state_dimensions": {"type": "array", "minItems": 3, "maxItems": 8,
                         "items": {"type": "string"}},
    "constraints": {"type": "array", "minItems": 2, "items": {
                    "type": "string"}},
    "keep_in_mind": {"type": "array", "minItems": 2, "items": {
                     "type": "string"}}},
    "required": ["title", "logline", "premise", "genre_primary",
                 "genre_secondary", "audience", "setting", "pov", "style",
                 "narrative_vector", "state_dimensions", "constraints",
                 "keep_in_mind"], "additionalProperties": False})

JUDGE_SCHEMA = grammar_safe({"type": "object", "properties": {"scores": {
    "type": "array", "minItems": 10, "maxItems": 10, "items": {
    "type": "object", "properties": {
        "dim": {"type": "string"},
        "score": {"type": "integer", "minimum": 1, "maximum": 5},
        "note": {"type": "string", "maxLength": 200}},
    "required": ["dim", "score", "note"],
    "additionalProperties": False}}},
    "required": ["scores"], "additionalProperties": False})

DIMS = ["RT1 Genre precision", "RT2 Audience identification",
        "RT3 Elevator pitch dual test", "RT4 Entity roster coverage",
        "RT5 Plot identification", "RT6 Per-plot description",
        "RT7 Writing style unnamed-author test", "RT8 Dramatic structure",
        "RT9 Human-experience topics and dilemmas",
        "RT10 Protagonist identification value"]

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--script", default="distill/runs/matrix/script.normalized.txt")
    ap.add_argument("--events", default="runs/events_build10_full/events.json")
    ap.add_argument("--meta", default="runs/meta_layer_v2b/meta.json")
    ap.add_argument("--entities", default="runs/entity_trial_v2/profiles.json")
    ap.add_argument("--out", required=True)
    ap.add_argument("--ports", default="8110,8111")
    ap.add_argument("--model", default="ornith-1.5-397b")
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    script = Path(a.script).read_text(encoding="utf-8")
    events = json.loads(Path(a.events).read_text(encoding="utf-8"))["events"]
    meta = json.loads(Path(a.meta).read_text(encoding="utf-8"))
    ents = json.loads(Path(a.entities).read_text(encoding="utf-8"))
    pool = EndpointPool([int(p) for p in a.ports.split(",")], a.model,
                        temperature=0.5, max_tokens=8000, timeout=1800)
    digest = ml.build_digest(events)
    ent_names = [e.get("name", "?") for e in (ents if isinstance(ents, list)
                                              else ents.get("entities", []))]
    layers_ctx = ("META LAYER:\n" + json.dumps(meta, ensure_ascii=False)[:30000]
                  + "\nENTITY ROSTER:\n" + json.dumps(ent_names))

    # Phase 1: map spine facts per script chunk.
    chunks = [script[i:i + 45000] for i in range(0, len(script), 45000)]
    print("chunks:", len(chunks), flush=True)
    def work(idx_chunk):
        idx, ch = idx_chunk
        r = pool.call(ml.SYSTEM, (
            "Extract the STORY SPINE facts visible in this part of a "
            "screenplay (part {} of {}). For each: what happens at story "
            "level and short verbatim-ish evidence.").format(idx + 1,
                                                              len(chunks))
                      + ch, schema=SPINE_SCHEMA)
        return json.loads(r.text)["facts"]
    facts = []
    for res in run_parallel(list(enumerate(chunks)), work, max_workers=2):
        if isinstance(res, Exception):
            print("chunk fail:", res, flush=True); continue
        facts.extend(res)
    print("spine facts:", len(facts), flush=True)

    # Phase 2: fill the root schema from everything.
    prompt = ("Fill the STORY ROOT for this screenplay. You see the whole "
              "screenplay compressed three ways: an event layer (causal "
              "chains), extracted spine facts with evidence, and the meta "
              "plus entity layers built earlier. Every field must agree "
              "with them; do not invent beyond them.\nEVENT LAYER:\n"
              + digest[:55000] + "\nSPINE FACTS:\n"
              + json.dumps(facts, ensure_ascii=False)[:30000] + "\n"
              + layers_ctx)
    root = json.loads(pool.call(ml.SYSTEM, prompt,
                                schema=ROOT_SCHEMA).text)

    # Phase 3: judge against the RT rubric dimensions.
    jd = json.loads(pool.call(ml.SYSTEM, (
        "Judge this story root against each dimension, score 1-5 with a "
        "one-line note. Dimensions: " + "; ".join(DIMS) +
        "\nSTORY ROOT:\n" + json.dumps(root, ensure_ascii=False)),
        schema=JUDGE_SCHEMA).text)["scores"]
    mean = round(sum(s["score"] for s in jd) / len(jd), 2)
    gate = "PASS" if mean >= 4.0 and min(s["score"] for s in jd) >= 3 \
           else "FAIL"
    (out / "story_root.json").write_text(json.dumps(root, indent=1,
                                        ensure_ascii=False), encoding="utf-8")
    (out / "judgement.json").write_text(json.dumps(
        {"gate": gate, "mean": mean,
         "scores": {s["dim"]: s["score"] for s in jd},
         "notes": {s["dim"]: s["note"] for s in jd}}, indent=1),
        encoding="utf-8")
    (out / "protocol.json").write_text(json.dumps(
        {"chunks": len(chunks), "spine_facts": len(facts)}, indent=1),
        encoding="utf-8")
    print("ROOT", gate, "mean", mean, flush=True)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
