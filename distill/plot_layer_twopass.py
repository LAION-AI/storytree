#!/usr/bin/env python3
"""Two-pass plot layer: membership first, chains second.

Why this exists (the project's core lesson applied): the failing plot
dimensions -- P1 within-chain causality, P3 membership, P5 redundancy -- are
GLOBAL properties, and the single-pass composer decides membership, causality
and framing simultaneously per plot with no cross-plot view. Structure fixes
what instructions could not:

  Pass 0  plot definitions are derived from the META LAYER's five
          perspectives (count and throughlines fixed procedurally, the model
          only words them).
  Pass A  MEMBERSHIP: per plot, select member events from the event digest
          plus scene-level evidence. v2: coverage is a REPORT, not a gate --
          forcing every event into some plot generated exactly the padding
          the v1 panel demolished (P3=2). Instead an ARC GATE checks each
          plot has setup/turn/resolution roles with the resolution in the
          final third, and repairs ONLY missing roles. Load-bearing events
          (>=3 plots) are marked for distinct per-plot context, never
          deleted (the muse-v2 lesson).
  Pass B  CHAINS: per plot, the schema's event_id AND enabled_by fields are
          enums over that plot's member ids -- a chain physically cannot cite
          an event outside its membership (the P1 defect all six judge passes
          named). Order/duplicate/backward-link faults are linted and
          repaired structurally, max 2 rounds. v2: the enum guarantees FORM,
          not causal truth (v1's and-then texture) -- so every link is then
          adversarially VERIFIED and chains with refuted links regenerate
          once with the faults named; the regeneration is accepted only if
          it refutes fewer links (repairs must not manufacture faults).

Output shape matches plot_layer.py (plots.json + judgement.json) so the
existing eval tooling and the GLM-5.3 panel apply unchanged;
caused_by_previous is rendered as "enabled by <id>: <link text>".
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import statistics
import sys
from collections import Counter
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


THROUGHLINES = ["objective_story", "main_character", "impact_character",
                "relationship", "society"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--meta", required=True)
    ap.add_argument("--events", required=True)
    ap.add_argument("--scenes", default="runs/scenes_ornith_v5_clean")
    ap.add_argument("--out", required=True)
    ap.add_argument("--ports", default="8110")
    ap.add_argument("--seed", choices=["throughline", "meta"],
                    default="throughline",
                    help="v3 'throughline': film-spanning identities worded "
                         "from the digest (the v2 'meta' seed anchored all "
                         "five plots on the central dilemma and was the "
                         "campaign's dominant failure cause)")
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
    by_id = {e["event_id"]: e for e in events}
    pool = EndpointPool([int(p) for p in a.ports.split(",")], a.model,
                        temperature=0.5, max_tokens=8000, timeout=1800)

    # Scene-level evidence: one compact line per event from its member scenes.
    scene_dir = Path(a.scenes)
    scene_evidence = {}
    for e in events:
        lines = []
        for sid in e.get("scene_ids", [])[:6]:
            p = scene_dir / (sid + ".json")
            if p.exists():
                s = json.loads(p.read_text(encoding="utf-8"))
                lines.append(f"{sid} {s.get('location','?')}: "
                             f"{str(s.get('summary',''))[:110]}")
        scene_evidence[e["event_id"]] = lines

    dilemma = json.dumps(meta.get("themes", {}).get("central_dilemma", {}),
                         ensure_ascii=False, indent=1)
    perspectives = meta.get("perspectives", {}).get("perspectives", [])
    assert len(perspectives) == 5, "expected the meta layer's 5 perspectives"

    # ---- Pass 0: word the five plots; count and throughlines are FIXED.
    def_schema = grammar_safe({
        "type": "object",
        "properties": {"plots": {
            "type": "array", "minItems": 5, "maxItems": 5, "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "minLength": 8,
                             "maxLength": 100},
                    "throughline": {"type": "string", "enum": THROUGHLINES},
                    "theme_or_dilemma": {"type": "string", "minLength": 10,
                                         "maxLength": 250},
                    "summary": {"type": "string", "minLength": 150,
                                "maxLength": 1200}},
                "required": ["name", "throughline", "theme_or_dilemma",
                             "summary"],
                "additionalProperties": False}}},
        "required": ["plots"], "additionalProperties": False})
    if a.seed == "meta":
        p0 = ("Word the five PLOTS of this story, one per given perspective, "
              "in the given order. A plot is ONE stance on the central "
              "dilemma told as a causal chain. Name each plot after its "
              "stance and carrier (who owns the perspective), not after the "
              "whole story. CENTRAL DILEMMA: " + dilemma +
              " THE FIVE PERSPECTIVES (one plot each, keep this order): " +
              json.dumps(perspectives, ensure_ascii=False)[:14000])
    else:
        # v3 seed: film-spanning throughlines. The v2 meta seed made all
        # five plots stances on ONE late-film decision; every judge then
        # saw the same sequence retold five times (P5 1.33). A plot must
        # be a throughline of the WHOLE story.
        p0 = ("Define the five PLOTS of this story, exactly one per "
              "classic throughline (objective_story, main_character, "
              "impact_character, relationship, society). A plot is ONE "
              "perspective on a theme or dilemma of human existence, told "
              "as a causal chain that SPANS THE WHOLE STORY: its stance is "
              "tested from the earliest events and resolved by the story's "
              "final events -- never a stance on a single mid-story "
              "decision. Name each plot after its stance and its carrier "
              "(the character, bond or system that owns the perspective). "
              "The central dilemma may inform themes but must not be the "
              "frame of every plot. CENTRAL DILEMMA (context only): "
              + dilemma + " THE EVENT LAYER: " + digest[:55000])
    plots = json.loads(pool.call(ml.SYSTEM, p0, schema=def_schema).text)["plots"]
    if a.seed == "meta":
        for plot, persp in zip(plots, perspectives):
            plot["throughline"] = persp.get("throughline", plot["throughline"])
    else:
        # one plot per throughline, procedurally enforced: keep the first
        # holder of each type, reassign surplus holders to the missing types
        first_holder = {}
        surplus = []
        for plot in plots:
            if plot["throughline"] in first_holder:
                surplus.append(plot)
            else:
                first_holder[plot["throughline"]] = plot
        missing = [tl for tl in THROUGHLINES if tl not in first_holder]
        for plot, tl in zip(surplus, missing):
            plot["throughline"] = tl
    print("defined 5 plots:", [p["name"] for p in plots], flush=True)

    # ---- Pass A: membership per plot (sees ALL definitions for discipline).
    mem_schema = grammar_safe({
        "type": "object",
        "properties": {"members": {
            "type": "array", "minItems": 6, "maxItems": 30, "items": {
                "type": "object",
                "properties": {
                    "event_id": {"type": "string", "enum": list(event_ids)},
                    "role": {"type": "string", "enum":
                             ["setup", "turn", "resolution", "connective"]},
                    "why": {"type": "string", "minLength": 25,
                            "maxLength": 220}},
                "required": ["event_id", "role", "why"],
                "additionalProperties": False}}},
        "required": ["members"], "additionalProperties": False})

    all_defs = json.dumps(plots, ensure_ascii=False, indent=1)

    def membership_for(plot):
        prompt = (
            "PASS A of a two-pass plot build: decide MEMBERSHIP ONLY (no "
            "chains yet). All five plots are listed; select the events that "
            "belong to THIS one: " + json.dumps(plot, ensure_ascii=False) +
            "\nALL FIVE PLOTS (for contrast -- an event may serve several "
            "plots, but only include it here if it tips THIS stance, and "
            "say WHY in this plot's own terms, never in another plot's "
            "terms): " + all_defs +
            "\nRules: this plot spans the WHOLE story -- its stance is "
            "tested from the earliest events on, so include the early-story "
            "events that seed it, every turn, and the resolution that "
            "closes it near the story's end. No padding (an event the "
            "protagonist merely appears in does not qualify); 'connective' "
            "entries are allowed when they carry causation between turns. "
            "EVENT LAYER: " + digest[:55000])
        r = pool.call(ml.SYSTEM, prompt, schema=mem_schema)
        return plot["name"], json.loads(r.text)["members"]

    membership = {}
    for res in run_parallel([(p,) for p in plots],
                            lambda t: membership_for(t[0]),
                            max_workers=min(2, len(plots))):
        if isinstance(res, Exception):
            print("membership FAILED:", str(res)[:120], flush=True)
            continue
        name, members = res
        # dedup, keep story order
        seen = set()
        members = [m for m in members
                   if not (m["event_id"] in seen or seen.add(m["event_id"]))]
        members.sort(key=lambda m: order[m["event_id"]])
        membership[name] = members
        print(f"membership {name}: {len(members)} events", flush=True)

    # Membership sanity for models without server-side grammar (Muse):
    # drop entries whose event_id is not a real event.
    for name in list(membership):
        membership[name] = [m for m in membership[name]
                            if m["event_id"] in order]

    # v2: coverage is a REPORT, not a gate. Plots do not tile the film;
    # forcing orphans into plots was v1's padding generator (panel P3=2).
    covered = {m["event_id"] for ms in membership.values() for m in ms}
    orphans = [eid for eid in event_ids if eid not in covered]
    print(f"uncovered events (allowed, reported): {len(orphans)}", flush=True)

    # v2 ARC GATE: each plot needs setup + turn(s) + a resolution that sits
    # in the final third of the story. Repair adds ONLY the missing roles.
    third = 2 * len(event_ids) // 3
    quarter = 3 * len(event_ids) // 4
    first_third = len(event_ids) // 3
    add_schema_tpl = {
        "type": "object",
        "properties": {"additions": {
            "type": "array", "minItems": 1, "maxItems": 6, "items": {
                "type": "object",
                "properties": {
                    "event_id": {"type": "string", "enum": list(event_ids)},
                    "role": {"type": "string", "enum":
                             ["setup", "turn", "resolution", "connective"]},
                    "why": {"type": "string", "minLength": 25,
                            "maxLength": 220}},
                "required": ["event_id", "role", "why"],
                "additionalProperties": False}}},
        "required": ["additions"], "additionalProperties": False}

    def arc_faults(members):
        roles = {m["role"] for m in members}
        faults = []
        setups = [m for m in members if m["role"] == "setup"]
        if not setups:
            faults.append("no setup")
        elif min(order[m["event_id"]] for m in setups) > first_third:
            faults.append("setup does not start in the first third -- the "
                          "stance must be seeded early")
        if "turn" not in roles:
            faults.append("no turn")
        res = [m for m in members if m["role"] == "resolution"]
        if not res:
            faults.append("no resolution")
        elif max(order[m["event_id"]] for m in res) < quarter:
            faults.append("resolution does not CLOSE the arc -- it must be "
                          "the late-story event where this stance is "
                          "decided or paid off")
        return faults

    for plot in plots:
        name = plot["name"]
        faults = arc_faults(membership.get(name, []))
        if not faults:
            continue
        pa = ("PASS A arc repair: this plot's membership is missing "
              + ", ".join(faults) + ". Add ONLY events that fill the "
              "missing roles for THIS plot's stance (why in this plot's own "
              "terms; a resolution must come from the story's final third). "
              "Do not restate existing members.\nPLOT: "
              + json.dumps(plot, ensure_ascii=False)
              + "\nEXISTING MEMBERS: "
              + json.dumps(membership.get(name, []), ensure_ascii=False)
              + "\nEVENT LAYER: " + digest[:50000])
        try:
            adds = json.loads(pool.call(ml.SYSTEM, pa,
                                        schema=grammar_safe(add_schema_tpl)
                                        ).text)["additions"]
            have = {m["event_id"] for m in membership[name]}
            for m in adds:
                if m["event_id"] in order and m["event_id"] not in have:
                    membership[name].append(m)
            membership[name].sort(key=lambda m: order[m["event_id"]])
            print(f"arc repair {name}: {faults} -> +{len(adds)}", flush=True)
        except Exception as e:
            print("arc repair failed " + name + ":", str(e)[:80], flush=True)

    # Load-bearing marking: claimed by >=3 plots -> distinct context per plot.
    claim_count = Counter(m["event_id"] for ms in membership.values()
                          for m in ms)
    load_bearing = sorted([e for e, c in claim_count.items() if c >= 3],
                          key=lambda e: order[e])
    print("load-bearing (>=3 plots):", load_bearing, flush=True)

    # ---- Pass B: chains, structurally confined to the membership.
    def chain_schema_for(member_ids):
        return grammar_safe({
            "type": "object",
            "properties": {"chain": {
                "type": "array", "minItems": min(4, len(member_ids)),
                "maxItems": len(member_ids), "items": {
                    "type": "object",
                    "properties": {
                        "event_id": {"type": "string", "enum": member_ids},
                        "why_in_plot": {"type": "string", "minLength": 30,
                                        "maxLength": 300},
                        "enabled_by": {"type": "string",
                                       "enum": member_ids + ["OPENING"]},
                        "causal_link": {"type": "string", "minLength": 20,
                                        "maxLength": 300}},
                    "required": ["event_id", "why_in_plot", "enabled_by",
                                 "causal_link"],
                    "additionalProperties": False}}},
            "required": ["chain"], "additionalProperties": False})

    def member_digest(member_ids):
        return ml.build_digest([by_id[eid] for eid in member_ids])

    def chain_prompt(plot, members, faults=()):
        member_ids = [m["event_id"] for m in members]
        shared_here = [e for e in load_bearing if e in member_ids]
        evid = []
        for eid in member_ids:
            for ln in scene_evidence.get(eid, [])[:2]:
                evid.append(ln)
        txt = (
            "PASS B of a two-pass plot build. The MEMBERSHIP of this plot "
            "is already decided (below) -- write the CHAIN over exactly "
            "these events, in story order. For each entry name the earlier "
            "member event that enables it (enabled_by; the first entry uses "
            "OPENING) and say HOW it enables it (causal_link), plus why the "
            "event belongs to this plot's stance (why_in_plot). You may "
            "DROP a member event that turns out to carry no causation, but "
            "you cannot add events.\nPLOT: "
            + json.dumps(plot, ensure_ascii=False)
            + "\nTHE OTHER PLOTS' STANCES (write THIS plot's why/link in "
            "its own vocabulary, not theirs): "
            + json.dumps([{ "name": p["name"],
                            "theme_or_dilemma": p["theme_or_dilemma"]}
                          for p in plots if p["name"] != plot["name"]],
                         ensure_ascii=False))
        if shared_here:
            txt += ("\nLOAD-BEARING SHARED EVENTS (also in other plots -- "
                    "keep them, but give each a context ONLY this plot can "
                    "give it): " + ", ".join(shared_here))
        if faults:
            txt += ("\nThe previous attempt had these structural faults; "
                    "fix them and nothing else: " + "; ".join(faults))
        txt += ("\nMEMBERSHIP (with pass-A reasons): "
                + json.dumps(members, ensure_ascii=False)
                + "\nMEMBER EVENTS: " + member_digest(member_ids)[:40000]
                + "\nSCENE EVIDENCE: " + "\n".join(evid)[:6000])
        return txt

    def lint_chain(chain, member_ids=None):
        faults, seen, last = [], set(), -1
        pos_in_chain = {}
        for i, m in enumerate(chain):
            eid = m["event_id"]
            if eid not in order:
                faults.append(eid + " is not a real event id")
                continue
            if member_ids is not None and eid not in member_ids:
                faults.append(eid + " is outside this plot's membership")
            if eid in seen:
                faults.append(eid + " cited twice")
            seen.add(eid)
            if order[eid] < last:
                faults.append(eid + " breaks story order")
            last = max(last, order[eid])
            pos_in_chain[eid] = i
        for i, m in enumerate(chain):
            en = m["enabled_by"]
            if i == 0:
                if en != "OPENING":
                    faults.append(m["event_id"] + " first entry must use "
                                  "OPENING")
                continue
            if en == "OPENING":
                faults.append(m["event_id"] + " only the first entry may "
                              "use OPENING")
            elif en not in pos_in_chain:
                faults.append(m["event_id"] + " enabled_by " + en +
                              " is not in the chain")
            elif pos_in_chain[en] >= i:
                faults.append(m["event_id"] + " enabled_by " + en +
                              " is not earlier in the chain")
        if len(chain) < 5:
            faults.append("chain thinner than 5 events")
        return faults

    def build_chain(plot, faults=()):
        members = membership[plot["name"]]
        member_ids = [m["event_id"] for m in members]
        r = pool.call(ml.SYSTEM, chain_prompt(plot, members, faults),
                      schema=chain_schema_for(member_ids))
        return plot["name"], json.loads(r.text)["chain"]

    chains, report = {}, {}
    for res in run_parallel([(p,) for p in plots],
                            lambda t: build_chain(t[0]),
                            max_workers=min(2, len(plots))):
        if isinstance(res, Exception):
            print("chain FAILED:", str(res)[:120], flush=True)
            continue
        name, chain = res
        member_ids = {m["event_id"] for m in membership[name]}
        faults = lint_chain(chain, member_ids)
        report[name] = {"events": len(chain), "faults": faults}
        chains[name] = chain
        print(f"chain {name}: {len(chain)} events, faults {faults[:2]}",
              flush=True)

    for _ in range(2):
        to_repair = [n for n in chains if report[n]["faults"]]
        if not to_repair:
            break
        for name in to_repair:
            plot = next(p for p in plots if p["name"] == name)
            try:
                _, chain = build_chain(plot, faults=report[name]["faults"])
                faults = lint_chain(
                    chain, {m["event_id"] for m in membership[name]})
                if len(faults) < len(report[name]["faults"]):
                    chains[name] = chain
                    report[name] = {"events": len(chain), "faults": faults}
                    print(f"repaired {name}: faults now {faults[:2]}",
                          flush=True)
            except Exception as e:
                print("repair failed " + name + ":", str(e)[:80], flush=True)

    # ---- v2: adversarial LINK VERIFY -> named-fault regeneration.
    # The enum guarantees form; whether A truly enables B is substance.
    def verify_links(plot, chain):
        links = [(i, m) for i, m in enumerate(chain)
                 if m.get("enabled_by") not in (None, "OPENING")]
        if not links:
            return []
        v_schema = grammar_safe({
            "type": "object",
            "properties": {"verdicts": {
                "type": "array", "minItems": len(links),
                "maxItems": len(links), "items": {
                    "type": "object",
                    "properties": {
                        "index": {"type": "integer"},
                        "ok": {"type": "boolean"},
                        "problem": {"type": "string", "maxLength": 200}},
                    "required": ["index", "ok", "problem"],
                    "additionalProperties": False}}},
            "required": ["verdicts"], "additionalProperties": False})
        listing = "\n".join(
            f"[{i}] {m['enabled_by']} -> {m['event_id']}: {m['causal_link']}"
            for i, m in links)
        member_ids = [m["event_id"] for m in membership[plot["name"]]]
        vp = ("Adversarially verify each claimed causal link of this plot "
              "chain. ok=true ONLY if the earlier event genuinely causes, "
              "enables or makes necessary the later one WITHIN this plot's "
              "stance -- mere adjacency, shared characters or 'and then' is "
              "ok=false with the problem named. Default to false when "
              "uncertain.\nPLOT: " + json.dumps(plot, ensure_ascii=False) +
              "\nLINKS:\n" + listing +
              "\nMEMBER EVENTS: " + member_digest(member_ids)[:35000])
        try:
            vs = json.loads(pool.call(ml.SYSTEM, vp,
                                      schema=v_schema).text)["verdicts"]
        except Exception as e:
            print("verify failed " + plot["name"] + ":", str(e)[:80],
                  flush=True)
            return []
        idx = {i for i, _ in links}
        return [v for v in vs if not v.get("ok") and v.get("index") in idx]

    for plot in plots:
        name = plot["name"]
        chain = chains.get(name)
        if not chain:
            continue
        bad = verify_links(plot, chain)
        print(f"verify {name}: {len(bad)} refuted links", flush=True)
        if not bad:
            continue
        named = ["link [{}] {}: {}".format(
            v["index"], chain[v["index"]]["event_id"] if v["index"] < len(chain)
            else "?", v.get("problem", ""))[:180] for v in bad]
        try:
            _, chain2 = build_chain(plot, faults=(
                ["these causal links were refuted -- rebuild so every "
                 "enabled_by names a genuine cause: "] + named))
            faults2 = lint_chain(chain2,
                                 {m["event_id"] for m in membership[name]})
            if faults2:
                print(f"regen {name}: structural faults, kept original",
                      flush=True)
                continue
            bad2 = verify_links(plot, chain2)
            if len(bad2) < len(bad):
                chains[name] = chain2
                report[name] = {"events": len(chain2), "faults": [],
                                "refuted_links": len(bad2)}
                print(f"regen {name}: refuted {len(bad)} -> {len(bad2)}, "
                      "accepted", flush=True)
            else:
                report[name]["refuted_links"] = len(bad)
                print(f"regen {name}: no improvement ({len(bad2)}), kept "
                      "original", flush=True)
        except Exception as e:
            print("regen failed " + name + ":", str(e)[:80], flush=True)

    # ---- Output in the plot_layer.py shape (+ _twopass annotations).
    out_plots = {}
    for plot in plots:
        name = plot["name"]
        chain = chains.get(name, [])
        out_plots[name] = {
            "definition": plot,
            "chain": [{
                "event_id": m["event_id"],
                "why_in_plot": m["why_in_plot"],
                "caused_by_previous": (
                    "Opens the chain: " + m["causal_link"]
                    if m["enabled_by"] == "OPENING" else
                    "enabled by " + m["enabled_by"] + ": " + m["causal_link"]),
            } for m in chain],
        }
    (out / "plots.json").write_text(json.dumps(
        {"plots": out_plots}, indent=1, ensure_ascii=False),
        encoding="utf-8")
    (out / "membership.json").write_text(json.dumps(
        {"membership": membership, "uncovered": orphans,
         "load_bearing": load_bearing, "report": report},
        indent=1, ensure_ascii=False), encoding="utf-8")

    # ---- Self-judge, same rubric text as plot_layer.py (parity only; the
    # decisive evaluation is the external GLM-5.3 panel).
    pl = _load("_pl", str(Path(__file__).resolve().parent / "plot_layer.py"))
    j_schema = grammar_safe({
        "type": "object",
        "properties": {
            **{d: {"type": "integer", "enum": [1, 2, 3, 4, 5]}
               for d in pl.DIMS},
            "evidence": {"type": "object",
                         "properties": {d: {"type": "string"}
                                        for d in pl.DIMS},
                         "required": pl.DIMS, "additionalProperties": False},
            "commentary": {"type": "string"}},
        "required": pl.DIMS + ["evidence", "commentary"],
        "additionalProperties": False})
    judge_view = {n: {"definition": v["definition"], "chain": v["chain"]}
                  for n, v in out_plots.items()}
    jprompt = (
        "Score this PLOT LAYER on five dimensions: " + ", ".join(pl.DIMS) +
        ". Integers 1-5 with one evidence clause each naming the plot or "
        "chain element it rests on. RUBRIC: " + pl.RUBRIC +
        " EVENT LAYER (ground truth): " + digest[:40000] +
        " PLOT LAYER: " + json.dumps(judge_view, ensure_ascii=False,
                                     indent=1)[:50000])
    jd = json.loads(pool.call(ml.SYSTEM, jprompt, schema=j_schema).text)
    scores = {d: jd[d] for d in pl.DIMS}
    judgement = {"scores": scores,
                 "mean": round(statistics.mean(scores.values()), 3),
                 "gate": ("PASS" if min(scores.values()) >= 3 and
                          statistics.mean(scores.values()) >= 4 else "FAIL"),
                 "evidence": jd.get("evidence", {}),
                 "commentary": jd.get("commentary", "")}
    (out / "judgement.json").write_text(json.dumps(judgement, indent=1,
                                                   ensure_ascii=False),
                                        encoding="utf-8")
    print("judgement: {} | mean {} | {}".format(
        judgement["gate"], judgement["mean"], scores), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
