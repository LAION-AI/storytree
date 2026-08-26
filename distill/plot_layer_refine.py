#!/usr/bin/env python3
"""One-pass plot layer + self-critique -> revision loop.

Takes an EXISTING one-pass plots.json as round 0 (so the loop's contribution
is isolated: same initial artifact, same composer, the only delta is
critique->revise). Each round:

  1. CRITIQUE: the composer scores its own layer against the P1-P5 rubric
     and writes concrete, actionable improvement instructions per plot
     (add/remove events, fix causal links, differentiate shared events).
  2. REVISE: each plot's chain is rewritten given its instructions plus a
     cross-plot view (the other chains' event ids and framings, so P5 can
     actually be addressed).
  3. GUARD: a revision is kept only if it does not add structural faults
     (order breaks, duplicates); the loop stops when the self-judged mean
     stops improving (max --rounds).

The self-judgement is only the LOOP SIGNAL; the decisive score is the
external GLM-5.3 panel, run separately on the final artifact.
"""
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--initial", required=True,
                    help="one-pass plots.json to refine")
    ap.add_argument("--events", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--ports", default="8222,8223,8224")
    ap.add_argument("--model", default="muse-spark-1.2-contributor-free")
    ap.add_argument("--rounds", type=int, default=2)
    a = ap.parse_args()

    here = Path(__file__).resolve().parent
    ml = _load("_ml", str(here / "meta_layer.py"))
    pl = _load("_pl", str(here / "plot_layer.py"))
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    events = json.loads(Path(a.events).read_text(encoding="utf-8"))["events"]
    event_ids = [e["event_id"] for e in events]
    order = {eid: i for i, eid in enumerate(event_ids)}
    digest = ml.build_digest(events)
    plots = json.loads(Path(a.initial).read_text(encoding="utf-8"))["plots"]
    names = list(plots.keys())
    pool = EndpointPool([int(p) for p in a.ports.split(",")], a.model,
                        temperature=0.5, max_tokens=8000, timeout=1800)

    def lint(chain):
        faults, seen, last = [], set(), -1
        for m in chain:
            eid = m.get("event_id")
            if eid not in order:
                faults.append(str(eid) + " unknown")
                continue
            if eid in seen:
                faults.append(eid + " duplicated")
            seen.add(eid)
            if order[eid] < last:
                faults.append(eid + " out of order")
            last = max(last, order[eid])
        return faults

    def layer_view(ps):
        return json.dumps(ps, ensure_ascii=False, indent=1)[:50000]

    def self_judge(ps):
        j_schema = grammar_safe({
            "type": "object",
            "properties": {
                **{d: {"type": "integer", "enum": [1, 2, 3, 4, 5]}
                   for d in pl.DIMS},
                "evidence": {"type": "object",
                             "properties": {d: {"type": "string"}
                                            for d in pl.DIMS},
                             "required": pl.DIMS,
                             "additionalProperties": False},
                "commentary": {"type": "string"}},
            "required": pl.DIMS + ["evidence", "commentary"],
            "additionalProperties": False})
        jp = ("Score this PLOT LAYER on five dimensions: "
              + ", ".join(pl.DIMS) +
              ". Integers 1-5 with one evidence clause each naming the plot "
              "or chain element it rests on. RUBRIC: " + pl.RUBRIC +
              " EVENT LAYER (ground truth): " + digest[:40000] +
              " PLOT LAYER: " + layer_view(ps))
        jd = json.loads(pool.call(ml.SYSTEM, jp, schema=j_schema).text)
        scores = {d: jd[d] for d in pl.DIMS}
        return scores, jd

    crit_schema = grammar_safe({
        "type": "object",
        "properties": {
            "suggestions": {
                "type": "array", "minItems": 3, "maxItems": 15, "items": {
                    "type": "object",
                    "properties": {
                        "plot": {"type": "string", "enum": names},
                        "dimension": {"type": "string", "enum": pl.DIMS},
                        "instruction": {"type": "string", "minLength": 40,
                                        "maxLength": 400}},
                    "required": ["plot", "dimension", "instruction"],
                    "additionalProperties": False}}},
        "required": ["suggestions"], "additionalProperties": False})

    def critique(ps):
        cp = ("You wrote this plot layer. Criticise it HARD against the "
              "rubric and produce concrete, executable improvement "
              "instructions -- name the plot, the dimension it fixes, and "
              "exactly what to change (which event to add or drop and why, "
              "which causal link is an and-then and what the real enabler "
              "is, which shared event needs a framing only that plot can "
              "give). No praise, no generalities. RUBRIC: " + pl.RUBRIC +
              " EVENT LAYER (ground truth): " + digest[:40000] +
              " PLOT LAYER: " + layer_view(ps))
        return json.loads(pool.call(ml.SYSTEM, cp,
                                    schema=crit_schema).text)["suggestions"]

    rev_schema = grammar_safe({
        "type": "object",
        "properties": {"chain": {
            "type": "array", "minItems": 3, "maxItems": 25, "items": {
                "type": "object",
                "properties": {
                    "event_id": {"type": "string", "enum": list(event_ids)},
                    "why_in_plot": {"type": "string", "minLength": 30,
                                    "maxLength": 300},
                    "caused_by_previous": {"type": "string",
                                           "minLength": 20,
                                           "maxLength": 300}},
                "required": ["event_id", "why_in_plot",
                             "caused_by_previous"],
                "additionalProperties": False}}},
        "required": ["chain"], "additionalProperties": False})

    def revise_plot(name, ps, suggestions):
        mine = [s for s in suggestions if s["plot"] == name]
        if not mine:
            return None
        others = {n: {"theme": ps[n]["definition"].get("theme_or_dilemma"),
                      "events": [m["event_id"] for m in ps[n]["chain"]]}
                  for n in names if n != name}
        rp = ("Revise ONE plot chain following your own critique. Apply "
              "every instruction; keep everything the critique did not "
              "touch. Story order, no duplicate events, each entry caused "
              "or enabled by an earlier entry of THIS chain.\nPLOT: "
              + json.dumps(ps[name]["definition"], ensure_ascii=False)
              + "\nCURRENT CHAIN: "
              + json.dumps(ps[name]["chain"], ensure_ascii=False)
              + "\nINSTRUCTIONS TO APPLY: "
              + json.dumps(mine, ensure_ascii=False)
              + "\nTHE OTHER PLOTS (for non-redundancy -- a shared event "
              "needs a framing only this plot can give): "
              + json.dumps(others, ensure_ascii=False)[:8000]
              + "\nEVENT LAYER: " + digest[:45000])
        r = pool.call(ml.SYSTEM, rp, schema=rev_schema)
        return json.loads(r.text)["chain"]

    log = []
    current = plots
    scores, jd = self_judge(current)
    mean = round(statistics.mean(scores.values()), 3)
    log.append({"round": 0, "scores": scores, "mean": mean})
    print(f"round 0 self-judge: mean {mean} {scores}", flush=True)

    for rnd in range(1, a.rounds + 1):
        suggestions = critique(current)
        print(f"round {rnd}: {len(suggestions)} suggestions "
              f"({[s['plot'][:18] + '/' + s['dimension'] for s in suggestions][:6]}...)",
              flush=True)
        candidate = json.loads(json.dumps(current))  # deep copy
        results = run_parallel(
            [(n,) for n in names],
            lambda t: (t[0], revise_plot(t[0], current, suggestions)),
            max_workers=min(3, len(names)))
        changed = 0
        for res in results:
            if isinstance(res, Exception):
                print("revision FAILED:", str(res)[:100], flush=True)
                continue
            name, chain = res
            if chain is None:
                continue
            old_faults = lint(current[name]["chain"])
            new_faults = lint(chain)
            if len(new_faults) > len(old_faults):
                print(f"  {name[:30]}: revision adds faults "
                      f"{new_faults[:2]}, kept", flush=True)
                continue
            candidate[name]["chain"] = chain
            changed += 1
        if not changed:
            print(f"round {rnd}: nothing changed, stopping", flush=True)
            break
        c_scores, c_jd = self_judge(candidate)
        c_mean = round(statistics.mean(c_scores.values()), 3)
        log.append({"round": rnd, "scores": c_scores, "mean": c_mean,
                    "suggestions": suggestions, "revised_plots": changed})
        print(f"round {rnd} self-judge: mean {c_mean} {c_scores} "
              f"(prev {mean})", flush=True)
        if c_mean < mean:
            print(f"round {rnd}: regressed, keeping previous", flush=True)
            break
        current, scores, jd, mean = candidate, c_scores, c_jd, c_mean

    (out / "plots.json").write_text(json.dumps(
        {"plots": current}, indent=1, ensure_ascii=False), encoding="utf-8")
    judgement = {"scores": scores, "mean": mean,
                 "gate": ("PASS" if min(scores.values()) >= 3 and
                          mean >= 4 else "FAIL"),
                 "evidence": jd.get("evidence", {}),
                 "commentary": jd.get("commentary", "")}
    (out / "judgement.json").write_text(json.dumps(
        judgement, indent=1, ensure_ascii=False), encoding="utf-8")
    (out / "refine_log.json").write_text(json.dumps(
        log, indent=1, ensure_ascii=False), encoding="utf-8")
    print("final: {} | mean {} | {}".format(judgement["gate"], mean, scores),
          flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
