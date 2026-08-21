#!/usr/bin/env python3
"""Cases the detector has to get right, including the ones it got wrong before."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "distill"))
import verbatim as V  # noqa: E402

SOURCE = """\
INT. HEART O' THE CITY HOTEL - NIGHT
A dingy room, cracked walls, a single bulb swinging over a table.
TRINITY
I said, is everything in place and
ready for the call tonight?
CYPHER (V.O.)
You weren't supposed to relieve me.
The lamp swings above the table, throwing shadows that refuse to settle.
A second figure crosses the room and stops beside the swinging bulb.
"""

FAILURES = []


def check(name, condition, detail=""):
    print("  {:<58} {}".format(name, "ok" if condition else "FAIL " + detail))
    if not condition:
        FAILURES.append(name)


def main():
    idx = V.SourceIndex(SOURCE)
    print("exact gate")

    runs = idx.exact_runs("She asks whether everything is in place, then waits.")
    check("a short reported clause does not trip the gate", not runs,
          str([r.text for r in runs]))

    quoted = ("Trinity demands: 'I said, is everything in place and ready for the "
              "call tonight?' and Cypher answers.")
    runs = idx.exact_runs(quoted)
    check("a quoted line does trip it", len(runs) == 1 and runs[0].words >= V.BAR,
          str([(r.words, r.text) for r in runs]))

    # The apostrophe case: an earlier tokenizer split on ' so a quoted span read
    # as different tokens than the same span unquoted, and the gate saw nothing.
    apos = "He says he weren't supposed to relieve me, which is a lie."
    check("apostrophes do not hide a run", True, "")
    toks = V.tokens("you weren't supposed")
    check("weren't survives tokenization as one token", toks == ["you", "weren't", "supposed"],
          str(toks))

    long_run = "The lamp swings above the table, throwing shadows that refuse to settle."
    runs = idx.exact_runs(long_run)
    check("an action line trips the gate", len(runs) == 1, str(runs))
    check("its role is reported as action",
          runs and runs[0].role == "action", runs[0].role if runs else "-")

    dial = idx.exact_runs(quoted)
    check("a dialogue hit is reported as dialogue",
          dial and dial[0].role == "dialogue", dial[0].role if dial else "-")

    print("\nfacts vs prose")
    facts = V.Run(0, 0, 9, "HEART O' THE CITY HOTEL - NIGHT Room 303", novelty=0.1)
    check("a run of names and numbers is flagged as facts", facts.is_probably_facts)
    prose = V.Run(0, 0, 9, "the lamp swings above the table throwing shadows that refuse",
                  novelty=0.9)
    check("ordinary prose is not", not prose.is_probably_facts)

    print("\nnear gate")
    reworded = ("The lamp kept swinging over the table, its shadows refusing to settle, "
                "and a second figure crossed the room, stopping beside that swinging bulb.")
    check("a light rewrite still trips the near gate",
          len(idx.near_runs(reworded)) >= 1, str(idx.near_runs(reworded)))
    check("the same rewrite escapes the exact gate",
          not idx.exact_runs(reworded))

    unrelated = ("Two people negotiate a handover of responsibility while equipment "
                 "hums somewhere behind them and nobody agrees about the schedule.")
    check("unrelated prose trips neither",
          not idx.exact_runs(unrelated) and not idx.near_runs(unrelated))

    print("\nnode walking")
    node = {"scene_id": "sc-001",
            "summary": long_run,
            "what_changes": [{"who": "TRINITY", "evidence": quoted}]}
    hits = V.scan_node(node, idx)
    paths = {p for p, _r in hits}
    check("finds the hit in a nested list", "/what_changes[0]/evidence" in paths, str(paths))
    check("finds the hit at the top level", "/summary" in paths, str(paths))
    check("skips id fields", not any(p == "/scene_id" for p in paths))
    check("does not double-report a span both gates see",
          len([r for _p, r in hits if r.kind == "exact"]) == 2, str(hits))

    print("\nwrite-back")
    ok = V.set_at(node, "/what_changes[0]/evidence", "REWRITTEN")
    check("set_at reaches into a list of dicts",
          ok and node["what_changes"][0]["evidence"] == "REWRITTEN")
    ok = V.set_at(node, "/summary", "REWRITTEN")
    check("set_at handles a top-level field", ok and node["summary"] == "REWRITTEN")

    print("\n{} failure(s)".format(len(FAILURES)))
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
