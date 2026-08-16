"""Referential and state integrity of an event layer, checked against data.

    python3 tools/check_integrity.py runs/lattice-qwen runs/lattice

Everything here is decidable from files already on disk. No model, no judge, no
opinion — either a participant id exists in the entity layer or it does not.

Why this is a separate tool from `narrativeforge/validate.py`
------------------------------------------------------------
The validator answers "does this conform to the schema". Both models' event
layers pass it with zero errors, and they are nonetheless very far apart on
whether the events are internally coherent. Schema conformance is a syntax
guarantee: it checks that `variable` is a string, not that the string names a
variable the entity actually has.

The gap between those two is where this project's most expensive failures live.
A state change naming a variable that belongs to a *different character* is
well-formed JSON, passes every schema check, and quietly corrupts the fold. It
was found once by reading and once by a rubric evaluation; neither scales.

So these checks exist to make that class mechanical. They are cheap enough to run
in the write path.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def load(base: Path, name: str):
    p = base / "artifacts" / f"{name}.json"
    if not p.exists():
        return None
    d = json.loads(p.read_text())
    body = d.get(name, d)
    return list(body.values()) if isinstance(body, dict) and name != "entities" else body


def check(base: Path) -> dict:
    events = load(base, "events") or []
    entities = load(base, "entities") or {}
    plots = load(base, "plots") or []

    plot_ids = {p["plot_id"] for p in plots if isinstance(p, dict)}
    event_ids = {e["event_id"] for e in events if isinstance(e, dict) and e.get("event_id")}
    # a variable is legal on an entity only if that entity declares it
    declared = {eid: set(e.get("state_variables") or {}) | set(e.get("state") or {})
                for eid, e in entities.items()}

    r = {"events": len(events), "entities": len(entities), "plots": len(plot_ids),
         "problems": []}

    def bad(msg):
        r["problems"].append(msg)

    parts = parts_ok = 0
    links = links_ok = 0
    sc = sc_entity_ok = sc_var_ok = sc_moves = 0
    dom_ok = dom_tot = 0

    for e in events:
        if not isinstance(e, dict):
            continue
        eid = e.get("event_id", "?")

        for p in e.get("participants") or []:
            parts += 1
            if p in entities:
                parts_ok += 1
            else:
                bad(f"{eid}: participant {p!r} is not a declared entity")

        for p in list(e.get("plots") or []) + ([e["primary_plot"]] if e.get("primary_plot") else []):
            if p not in plot_ids:
                bad(f"{eid}: plot {p!r} does not exist")

        for key in ("caused_by", "causes"):
            for ref in e.get(key) or []:
                links += 1
                if ref in event_ids:
                    links_ok += 1
                else:
                    bad(f"{eid}: {key} points at {ref!r}, which is not an event")

        if not (e.get("caused_by") or e.get("is_root")):
            bad(f"{eid}: has no cause and is not marked as a root")

        for i, c in enumerate(e.get("state_changes") or []):
            if not isinstance(c, dict):
                continue
            sc += 1
            ent = c.get("entity")
            var = c.get("variable") or c.get("state_variable")
            if ent in entities:
                sc_entity_ok += 1
                if var and declared.get(ent):
                    if var in declared[ent]:
                        sc_var_ok += 1
                    else:
                        owner = next((o for o, v in declared.items() if var in v), None)
                        bad(f"{eid}.change[{i}]: {var!r} is not a variable of {ent!r}"
                            + (f" — it belongs to {owner}" if owner else ""))
                elif var:
                    sc_var_ok += 1          # entity declares nothing; nothing to contradict
            else:
                bad(f"{eid}.change[{i}]: entity {ent!r} is not declared")
            before, after = c.get("before"), c.get("after")
            if before is None or before != after:
                sc_moves += 1
            else:
                bad(f"{eid}.change[{i}]: no-op, {before!r} unchanged")

            # Does the value land inside the domain the variable itself declares?
            #
            # This is a different question from the one above and it took a
            # discrepancy to notice. The ownership check passes 127/127 on a run
            # where an evaluator independently measured 42/127 "landing on a
            # declared, in-domain value". Both numbers are right: the variable
            # names are correct and the *values* are not.
            #
            # The cause is visible in the data. One model writes
            #     "after": {"status": "severed"}
            # against a domain of bare strings ["intact", "severed", ...], so the
            # object can never equal a member and every single change misses.
            # The other writes "after": "severed" and lands. A wrapper one level
            # deep, propagated from the declared init, invalidates the whole
            # state layer while leaving every schema check green.
            #
            # This is the check that separates the two models, so it belongs in
            # the tool rather than in someone's terminal.
            spec = ((entities.get(ent) or {}).get("state_variables") or {}).get(var)
            if isinstance(spec, dict):
                domain = spec.get("domain") or spec.get("enum") or spec.get("values")
                if domain:
                    dom_tot += 1
                    val = after.get("value") if isinstance(after, dict) and "value" in after \
                        else after
                    if val in domain:
                        dom_ok += 1
                    else:
                        shown = json.dumps(val)[:60]
                        bad(f"{eid}.change[{i}]: {shown} is not in the declared "
                            f"domain of {var!r}"
                            + (" (value is object-wrapped; domain holds bare values)"
                               if isinstance(val, dict) else ""))

    r["participants"] = f"{parts_ok}/{parts}"
    r["causal_links"] = f"{links_ok}/{links}"
    r["state_entity"] = f"{sc_entity_ok}/{sc}"
    r["state_variable"] = f"{sc_var_ok}/{sc}"
    r["state_moves"] = f"{sc_moves}/{sc}"
    r["state_domain"] = f"{dom_ok}/{dom_tot}"
    r["plot_coverage"] = {p: sum(1 for e in events if isinstance(e, dict)
                                 and p in (e.get("plots") or [])) for p in sorted(plot_ids)}
    r["uncovered_plots"] = [p for p, n in r["plot_coverage"].items() if n == 0]
    return r


if __name__ == "__main__":
    rows = {}
    for arg in sys.argv[1:]:
        base = Path(arg)
        rows[base.name] = check(base)

    keys = ["events", "entities", "participants", "causal_links",
            "state_entity", "state_variable", "state_moves", "state_domain"]
    labels = {"events": "events", "entities": "entities declared",
              "participants": "participants resolve",
              "causal_links": "causal links resolve",
              "state_entity": "state change names a declared entity",
              "state_variable": "...and a variable that entity owns",
              "state_moves": "...and actually changes it",
              "state_domain": "...to a value inside the declared domain"}

    w = max(len(v) for v in labels.values()) + 2
    print(f"{'check':<{w}}" + "".join(f"{n:>18}" for n in rows))
    print("-" * (w + 18 * len(rows)))
    for k in keys:
        print(f"{labels[k]:<{w}}" + "".join(f"{str(r[k]):>18}" for r in rows.values()))

    for name, r in rows.items():
        print(f"\n{name}: {len(r['problems'])} problem(s)"
              + (f", plots with no events: {r['uncovered_plots']}" if r["uncovered_plots"] else ""))
        print(f"  plot coverage: {json.dumps(r['plot_coverage'])}")
        for p in r["problems"][:10]:
            print(f"  ! {p}")
        if len(r["problems"]) > 10:
            print(f"  ... and {len(r['problems']) - 10} more")
