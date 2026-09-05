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

    def __init__(self, script=None, artifacts=None):
        self.script = list(script or [GOOD])
        self.artifacts = list(artifacts or [])
        self.calls = []
        self.budgets = []

    def generate(self, user, instructions=None, max_output_tokens=4096):
        self.calls.append(user)
        self.budgets.append(max_output_tokens)
        if self.artifacts and ("NOW BUILD" in user or "Resend the COMPLETE" in user):
            items = self.artifacts
            text = items.pop(0) if len(items) > 1 else items[0]
        else:
            text = self.script.pop(0) if len(self.script) > 1 else self.script[0]
        return text, {"in": 1, "out": 1}


class FlakyClient(FakeClient):
    """Raises incomplete once, then behaves like FakeClient."""

    def generate(self, user, instructions=None, max_output_tokens=4096):
        from zen_client import ZenError
        if not getattr(self, "_flaked", False):
            self._flaked = True
            self.calls.append(user)
            self.budgets.append(max_output_tokens)
            raise ZenError("incomplete response, status=incomplete")
        return super().generate(user, instructions, max_output_tokens)


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

    c2 = G.Chain("s", {"logline": "x"}, per_layer=2, client=FakeClient(script=[
        "<reasoning>r1</reasoning>",
        "<artifact>\n```json\n{\"big_questions\": [], \"central_dilemma\": {}}\n```\n</artifact>",
        "<reasoning>r2</reasoning>",
        "<artifact>\n```json\n{\"conflicts\": []}\n```\n</artifact>",
    ]))
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

    print("\nrepair retry + grounding rules")
    R_OK = "<reasoning>deliberation done</reasoning>"
    A_BAD = "<artifact>\n```json\n{\"nope\": 1}\n```\n</artifact>"
    A_GOOD = "<artifact>\n```json\n{\"event_id\": \"ev-001\", \"summary\": \"s\", \"state_triples\": []}\n```\n</artifact>"
    fc5 = FakeClient(script=[R_OK, A_BAD, A_GOOD])
    cc5 = G.Chain("s", {"logline": "x"}, client=fc5)
    rec5 = cc5.call("tid-r", "CTX", required_keys=("event_id", "summary"))
    check("repair: 3 calls total", len(fc5.calls) == 3, str(len(fc5.calls)))
    check("repair: artifact recovered", rec5.get("artifact", {}).get("event_id") == "ev-001")
    check("repair: no error recorded", "error" not in rec5, str(rec5.get("error")))
    check("repair: usage notes repair", "repair" in rec5.get("usage", {}))
    check("repair call names missing keys", "summary" in fc5.calls[2], fc5.calls[2][:120])

    fc6 = FakeClient(script=[R_OK, A_BAD, A_BAD])
    cc6 = G.Chain("s", {"logline": "x"}, client=fc6)
    rec6 = cc6.call("tid-r2", "CTX", required_keys=("event_id",))
    check("repair failed twice -> error kept, reasoning kept",
          "error" in rec6 and rec6.get("reasoning") == "deliberation done",
          str(rec6))

    cc7 = G.Chain("s", {"logline": "x"}, per_layer=2,
                  client=FakeClient(script=[GOOD]))
    cc7.expose = {"ending_first": "x"}
    t5jobs = cc7.t5_skeletons()
    check("t5 has required keys", t5jobs[0][4] == ("event_id", "question", "owner_plot", "n_scenes"))
    check("t5 grounding rule present", "NO proper noun" in t5jobs[0][3])
    cc7.events = [{"event_id": "ev-001"}]
    cc7.skeletons = [{"event_id": "ev-001", "n_scenes": 2}]
    t9jobs = cc7.t9_prose()
    check("t9 card adherence present", "CARD ADHERENCE" in t9jobs[0][3])
    check("t9 has required keys", t9jobs[0][4] == ("scene_id", "scene_text"))

    print("\nparallel + budget escalation + retry-errors")
    arts = {
        "themes": {"big_questions": [], "central_dilemma": {}},
        "external": {"conflicts": []},
        "internal": {"internal_conflicts": []},
        "relationships": {"relationship_arcs": []},
        "perspectives": {"perspectives": []},
    }
    art_blocks = ["<artifact>\n```json\n%s\n```\n</artifact>" % json.dumps(a)
                  for a in arts.values()]
    fc7 = FakeClient(script=["<reasoning>r</reasoning>"], artifacts=art_blocks)
    cc7p = G.Chain("s", {"logline": "x"}, per_layer=5, workers=3, client=fc7)
    recs7 = cc7p.run_step("t1")
    check("parallel t1: 5 traces", len(recs7) == 5, str(len(recs7)))
    check("parallel t1: 10 calls, no repairs", len(fc7.calls) == 10,
          str(len(fc7.calls)))
    check("parallel t1: tids unique",
          len({r["tid"] for r in recs7}) == 5)
    check("parallel t1: all ingested", len(cc7p.meta) == 5)
    keymap = {"themes": "big_questions", "external": "conflicts",
              "internal": "internal_conflicts",
              "relationships": "relationship_arcs",
              "perspectives": "perspectives"}
    check("parallel t1: every artifact fits its section",
          all(keymap[r["part"]] in (r.get("artifact") or {}) for r in recs7))

    fc8 = FlakyClient(script=[GOOD])
    cc8 = G.Chain("s", {"logline": "x"}, client=fc8)
    rec8 = cc8.call("tid-b", "CTX")
    check("escalation: recovered after incomplete",
          rec8.get("artifact") == {"a": 1} and "error" not in rec8)
    check("escalation: retry used bigger budget",
          fc8.budgets[1] > fc8.budgets[0], str(fc8.budgets))
    check("escalation: flagged in usage",
          rec8.get("usage", {}).get("budget_retry") is True)

    import tempfile, os
    with tempfile.TemporaryDirectory() as tmp:
        p = os.path.join(tmp, "g.jsonl")
        with open(p, "w") as f:
            f.write('{"tid": "a", "artifact": {"x": 1}}\n')
            f.write('{"tid": "b", "error": "boom", "reasoning": "r"}\n')
        kept, dropped = G.drop_error_records(p)
        check("retry-errors: counts", (kept, dropped) == (1, 1),
              str((kept, dropped)))
        rest = [json.loads(l) for l in open(p)]
        check("retry-errors: only good kept",
              [r["tid"] for r in rest] == ["a"])

    print("\n%d passed, %d failed" % (len(PASS), len(FAIL)))
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
