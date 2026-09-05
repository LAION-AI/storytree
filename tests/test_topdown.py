#!/usr/bin/env python3
"""Self-tests for the top-down pilot (generate + 3-judge panel).

Run with:  python3 tests/test_topdown.py

No network: all model calls go through a scripted FakeClient.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "reasoning_traces"))

import topdown_generate as G  # noqa: E402
import topdown_judge as J  # noqa: E402

PASS, FAIL = [], []


def check(name, condition, detail=""):
    (PASS if condition else FAIL).append(name)
    print("  {:<62} {}".format(name, "ok" if condition else "FAIL " + detail))


GOOD = ("<reasoning>considered A, rejected B because C</reasoning>\n"
        "<artifact>\n```json\n{\"a\": 1}\n```\n</artifact>")
BAD = "no tags here, just prose"


class FakeClient:
    model = "fake"

    def __init__(self, script=None):
        self.script = list(script or [GOOD])
        self.calls = []

    def generate(self, user, instructions=None, max_output_tokens=4096):
        self.calls.append(user)
        text = self.script.pop(0) if len(self.script) > 1 else self.script[0]
        return text, {"in": 1, "out": 1}


class FakeJudge:
    model = "fake-judge"

    def __init__(self, scores):
        self.scores = scores
        self.calls = 0

    def generate(self, user, instructions=None, max_output_tokens=2048):
        self.calls += 1
        return self.scores, {}


def main():
    r, a = G._parse(GOOD)
    check("parse: reasoning extracted", r == "considered A, rejected B because C", repr(r))
    check("parse: artifact extracted", a == {"a": 1}, repr(a))
    r2, a2 = G._parse(BAD)
    check("parse: malformed -> (None, None)", r2 is None and a2 is None)
    r3, a3 = G._parse("<reasoning>x</reasoning><artifact>```json\n{\"a\": 1}\n```\ntrailing chatter {oops")
    check("parse: trailing chatter repaired", a3 == {"a": 1}, repr(a3))
    check("balanced-json skips braces in strings",
          G._balanced_json('{\"t\": \"a{b}c\"} tail') == {"t": "a{b}c"})

    c = G.Chain("s", {"logline": "x"}, per_layer=2, client=FakeClient())
    check("t1 capped at per_layer", len(c.t1_meta()) == 2, str(len(c.t1_meta())))
    check("run_step t2 without meta: no jobs, no calls", c.run_step("t2") == [])
    check("no calls happened", len(c.client.calls) == 0, str(len(c.client.calls)))

    c2 = G.Chain("s", {"logline": "x"}, per_layer=2, client=FakeClient())
    recs = c2.run_step("t1")
    check("t1 runs 2 traces x 2 calls", len(recs) == 2 and len(c2.client.calls) == 4,
          str(len(c2.client.calls)))
    check("t1 artifacts ingested", len(c2.meta) == 2, str(len(c2.meta)))
    recs2 = c2.run_step("t1", skip={r["tid"] for r in recs})
    check("skip set avoids calls", recs2 == [] and len(c2.client.calls) == 4)

    c3 = G.Chain("s", {"logline": "x"}, per_layer=5, client=FakeClient())
    c3.skeletons = [{"event_id": "ev-001", "n_scenes": 4},
                    {"event_id": "ev-002", "n_scenes": 4}]
    c3.events = [{"event_id": "ev-001"}, {"event_id": "ev-002"}]
    plan = c3._scene_plan()
    check("scene plan capped at 5", len(plan) == 5, str(len(plan)))
    check("scene ids sequential", [s for s, _ in plan] ==
          ["sc-001", "sc-002", "sc-003", "sc-004", "sc-005"])

    blob = json.dumps([j[3] for j in c3.t8_cards()] + [j[3] for j in c3.t9_prose()])
    check("card/prose prompts carry no full script", "original_script" not in blob)
    check("t9 states the blind rule", "BLIND RULE" in blob)
    check("judge is blind (no model name)",
          "muse-spark" not in (J.JUDGE_SYS + J.JUDGE_USER).lower()
          and "muse-spark" not in
          (G.SYS + G.REASON_SYS + G.ARTIFACT_SYS).lower())

    fj = FakeJudge("```json\n{\"D1\": 5, \"D2\": 4, \"D3\": 4, \"D4\": 4, \"D5\": 5}\n```")
    rec = J.judge_trace(fj, "t", "meta", "task", "ctx", "rsn", {"a": 1})
    check("judge calls 3 times", fj.calls == 3, str(fj.calls))
    check("judge means averaged", rec["means"] == {"D1": 5.0, "D2": 4.0, "D3": 4.0,
                                                  "D4": 4.0, "D5": 5.0}, str(rec["means"]))
    check("judge pass at 4.4/4.0", rec["pass"] is True and rec["overall"] == 4.4)

    fj2 = FakeJudge("```json\n{\"D1\": 5, \"D2\": 5, \"D3\": 5, \"D4\": 2, \"D5\": 5}\n```")
    rec2 = J.judge_trace(fj2, "t", "meta", "task", "ctx", "rsn", {"a": 1})
    check("judge fails on weak dim (min<3)", rec2["pass"] is False, str(rec2["means"]))

    fj3 = FakeJudge("not json at all")
    rec3 = J.judge_trace(fj3, "t", "meta", "task", "ctx", "rsn", {"a": 1})
    check("judge error when all draw fail", "error" in rec3, str(rec3))

    print("\ntwo-call default")
    R1 = "<reasoning>candidate A vs B; B rejected; near-miss C</reasoning>"
    A2 = "<artifact>\n```json\n{\"plots\": []}\n```\n</artifact>"
    fc = FakeClient(script=[R1, A2])
    cc = G.Chain("s", {"logline": "x"}, per_layer=5, client=fc)
    # drive call() directly (run_step("t2") needs meta state)
    rec = cc.call("tid-1", "TASKCTX")
    check("two-call makes 2 calls", len(fc.calls) == 2, str(len(fc.calls)))
    check("reasoning comes from call 1",
          rec.get("reasoning") == "candidate A vs B; B rejected; near-miss C",
          repr(rec.get("reasoning")))
    check("artifact comes from call 2", rec.get("artifact") == {"plots": []},
          repr(rec.get("artifact")))
    check("call 2 carries call-1 reasoning", "candidate A vs B" in fc.calls[1])
    check("no error", "error" not in rec, str(rec))
    check("mode recorded", rec.get("usage", {}).get("mode") == "two-call")

    fc2 = FakeClient(script=["   "])
    cc2 = G.Chain("s", {"logline": "x"}, client=fc2)
    rec_e = cc2.call("tid-e", "TASKCTX")
    check("empty deliberation -> error, call2 skipped",
          "error" in rec_e and len(fc2.calls) == 1, str(rec_e))

    fc3 = FakeClient(script=[GOOD])
    cc3 = G.Chain("s", {"logline": "x"}, single_call=True, client=fc3)
    rec_s = cc3.call("tid-s", "TASKCTX")
    check("single-call makes 1 call", len(fc3.calls) == 1)
    check("single-call parses both", rec_s.get("artifact") == {"a": 1}
          and rec_s.get("reasoning") is not None)

    print("\nHF-shaped plots")
    PLOTS = {"plots": [
        {"definition": {"summary": "Find it."}, "name": "search"},
        {"definition": {"summary": "Hide it."}, "name": "hide"},
    ]}
    A_PLOTS = "<artifact>\n```json\n%s\n```\n</artifact>" % json.dumps(PLOTS)
    fc4 = FakeClient(script=["<reasoning>ok</reasoning>", A_PLOTS,
                             "<reasoning>ok</reasoning>",
                             "<artifact>\n```json\n{\"chain\": []}\n```\n</artifact>",
                             "<reasoning>ok</reasoning>",
                             "<artifact>\n```json\n{\"chain\": []}\n```\n</artifact>"])
    cc4 = G.Chain("s", {"logline": "x"}, per_layer=5, client=fc4)
    cc4.meta = {"themes": {}}
    cc4.run_step("t2")
    check("plots ingested", len(cc4.plots) == 2, str(len(cc4.plots)))
    cc4.skeletons = [{"event_id": "ev-001"}, {"event_id": "ev-002"}]
    recs4 = cc4.run_step("t6")
    tids = [r["tid"] for r in recs4]
    check("t6 makes 2 chain calls", len(recs4) == 2, str(len(recs4)))
    check("t6 tids unique (HF name key)", len(set(tids)) == 2, str(tids))

    print("\n%d passed, %d failed" % (len(PASS), len(FAIL)))
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
