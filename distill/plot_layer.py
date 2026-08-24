#!/usr/bin/env python3
"""Plot layer: perspectives on the dilemmas, as causal chains of events."""

from __future__ import annotations

import argparse
import importlib.util
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, "/home/deployer/laion/project-alexandria/screenplay/src")
from screenplay_ku.client import EndpointPool, run_parallel  # noqa: E402
from screenplay_ku.kuschema import grammar_safe  # noqa: E402


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


RUBRIC = (
    "P1 Causal integrity - within a plot each event must be caused, enabled "
    "or raised into necessity by earlier events of the SAME plot; and-then "
    "sequences without condition are the defect. "
    "P2 Perspective discipline - a plot is ONE stance on a theme or dilemma, "
    "not a retelling. "
    "P3 Membership accuracy - every cited event belongs and earns its place; "
    "nothing padded, nothing missing. "
    "P4 Arc completeness - setup, turns and resolution across the span; "
    "nothing dangling. "
    "P5 Non-redundancy - plots must not rehash one another. "
    "Integers 1-5, hard marking as usual.")
DIMS = ["P1", "P2", "P3", "P4", "P5"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--meta", required=True)
    ap.add_argument("--events", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--ports", default="8110,8111")
    ap.add_argument("--model", default="ornith-1.5-397b")
    a = ap.parse_args()

    ml = _load("_ml", str(Path(__file__).resolve().parent / "meta_layer.py"))
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    meta = json.loads(Path(a.meta).read_text(encoding="utf-8"))
    events = json.loads(Path(a.events).read_text(encoding="utf-8"))["events"]
    event_ids = [e["event_id"] for e in events]
    order = {eid: i for i, eid in enumerate(event_ids)}
    digest = ml.build_digest(events)
    pool = EndpointPool([int(p) for p in a.ports.split(",")], a.model,
                        temperature=0.5, max_tokens=8000, timeout=1800)

    dilemma = json.dumps(meta.get("themes", {}).get("central_dilemma", {}),
                         ensure_ascii=False, indent=1)
    questions = json.dumps(meta.get("themes", {}).get("big_questions", []),
                           ensure_ascii=False)[:4000]

    def_schema = grammar_safe({
        "type": "object",
        "properties": {"plots": {
            "type": "array", "minItems": 3, "maxItems": 6, "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "minLength": 8,
                             "maxLength": 100},
                    "throughline": {"type": "string", "enum":
                                    ["objective_story", "main_character",
                                     "impact_character", "relationship",
                                     "society"]},
                    "theme_or_dilemma": {"type": "string", "minLength": 10,
                                         "maxLength": 250},
                    "summary": {"type": "string", "minLength": 150,
                                "maxLength": 1200}},
                "required": ["name", "throughline", "theme_or_dilemma",
                             "summary"],
                "additionalProperties": False}}},
        "required": ["plots"], "additionalProperties": False})
    prompt_a = (
        "Define the PLOTS of this story. A plot is ONE perspective on a "
        "theme or dilemma of human existence, told as a causal chain of "
        "events: each event conditions the next INSIDE the plot. Cover the "
        "classic perspectives where the material supports them. Summarise "
        "each plot in about three sentences. CENTRAL DILEMMA: " + dilemma +
        " BIG QUESTIONS: " + questions +
        " THE EVENT LAYER: " + digest[:60000])
    plots = json.loads(pool.call(ml.SYSTEM, prompt_a,
                                 schema=def_schema).text)["plots"]
    print("defined {} plots".format(len(plots)), flush=True)

    mem_schema = grammar_safe({
        "type": "object",
        "properties": {"chain": {
            "type": "array", "minItems": 3, "maxItems": 25, "items": {
                "type": "object",
                "properties": {
                    "event_id": {"type": "string", "enum": list(event_ids)},
                    "why_in_plot": {"type": "string", "minLength": 30,
                                    "maxLength": 300},
                    "caused_by_previous": {"type": "string", "minLength": 20,
                                           "maxLength": 300}},
                "required": ["event_id", "why_in_plot",
                             "caused_by_previous"],
                "additionalProperties": False}}},
        "required": ["chain"], "additionalProperties": False})

    def work(plot):
        prompt = (
            "A plot has been defined as follows: "
            + json.dumps(plot, ensure_ascii=False, indent=1) +
            " Mark every event of the layer that BELONGS to this plot, in "
            "story order. For each: why it belongs to THIS plot's "
            "perspective, and how it is caused or enabled by the previous "
            "event IN THE CHAIN (the first entry names what sets the chain "
            "moving). Skip events that merely happen nearby without "
            "belonging. EVENT LAYER: " + digest[:60000])
        r = pool.call(ml.SYSTEM, prompt, schema=mem_schema)
        return plot["name"], json.loads(r.text)["chain"]

    chains = {}
    report = {}
    for res in run_parallel([(p,) for p in plots], lambda t: work(t[0]),
                            max_workers=2):
        if isinstance(res, Exception):
            print("research FAILED:", str(res)[:100], flush=True)
            continue
        name, chain = res
        bad, seen, last = [], set(), -1
        for m in chain:
            eid = m["event_id"]
            if eid not in order:
                bad.append("unknown " + eid)
            elif order[eid] < last:
                bad.append(eid + " breaks story order")
            elif eid in seen:
                bad.append(eid + " cited twice")
            seen.add(eid)
            last = max(last, order.get(eid, last))
        report[name] = {"events": len(chain), "faults": bad}
        chains[name] = {"definition": next(p for p in plots
                                           if p["name"] == name),
                        "chain": chain}
        print(name + ": {} events, faults {}".format(len(chain), bad[:2]),
              flush=True)

    # Repair round for broken or thin chains.
    for name in list(chains):
        rep = report.get(name) or {}
        if not rep.get("faults") and rep.get("events", 0) >= 5:
            continue
        try:
            _, chain = work(chains[name]["definition"])
            chains[name]["chain"] = chain
            print("repaired " + name, flush=True)
        except Exception as e:
            print("repair failed " + name + ":", str(e)[:80], flush=True)

    j_schema = grammar_safe({
        "type": "object",
        "properties": {
            **{d: {"type": "integer", "enum": [1, 2, 3, 4, 5]} for d in DIMS},
            "evidence": {"type": "object",
                         "properties": {d: {"type": "string"} for d in DIMS},
                         "required": DIMS,
                         "additionalProperties": False},
            "commentary": {"type": "string"}},
        "required": DIMS + ["evidence", "commentary"],
        "additionalProperties": False})
    jprompt = (
        "Score this PLOT LAYER on five dimensions: " + ", ".join(DIMS) +
        ". Integers 1-5 with one evidence clause each naming the plot or "
        "chain element it rests on. RUBRIC: " + RUBRIC +
        " EVENT LAYER (ground truth): " + digest[:40000] +
        " PLOT LAYER: " + json.dumps(chains, ensure_ascii=False,
                                     indent=1)[:50000])
    jd = json.loads(pool.call(ml.SYSTEM, jprompt, schema=j_schema).text)
    scores = {d: jd[d] for d in DIMS}
    judgement = {"scores": scores,
                 "mean": round(statistics.mean(scores.values()), 3),
                 "gate": ("PASS" if min(scores.values()) >= 3 and
                          statistics.mean(scores.values()) >= 4 else "FAIL"),
                 "evidence": jd["evidence"], "commentary": jd["commentary"]}

    (out / "plots.json").write_text(json.dumps(
        {"plots": chains}, indent=1, ensure_ascii=False), encoding="utf-8")
    (out / "judgement.json").write_text(json.dumps(judgement, indent=1,
                                                   ensure_ascii=False),
                                        encoding="utf-8")
    print("judgement: {} | mean {} | {}".format(
        judgement["gate"], judgement["mean"], scores), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


