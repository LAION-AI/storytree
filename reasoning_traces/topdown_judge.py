#!/usr/bin/env python3
"""3-judge panel for top-down pilot traces (see topdown_generate.py).

Each trace (reasoning + artifact + the context it was built from) is scored
independently by 3 judges on 5 dimensions (0-5 integers, from the hindsight
quality rubric):

  D1 forward plausibility -- could this reasoning lead to this artifact?
  D2 groundedness          -- everything claimed comes from the layers above?
  D3 coherence             -- internally consistent, no contradictions?
  D4 genuine derivation    -- weighs alternatives, rules things out
                             (not a restatement of the artifact)?
  D5 coverage              -- everything the task demanded is addressed?

Judges are blind: the prompt never names the composer model. Scores are
averaged; PASS = mean >= 4.0 AND worst dimension mean >= 3.0 (the project
bar). Gaps under ~0.3 are noise -- never read them.

Usage:
  python3 topdown_judge.py --in gen.jsonl --out judge.jsonl
  python3 topdown_judge.py --in gen.jsonl --out judge.jsonl --tids tid1,tid2

Output JSONL: {tid, step, scores: [j1..j3], means: {D1..D5}, overall, pass}
or {tid, step, error}. Resumable like topdown_generate.py.
Key via OPENCODE_API_KEY (see zen_client.py).
"""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from zen_client import ZenClient, ZenError  # noqa: E402

DIMS = ["D1", "D2", "D3", "D4", "D5"]

JUDGE_SYS = ("You are a blind judge of story-generation reasoning. You do "
             "not know which system produced the trace. Score ONLY what is in "
             "front of you. Answer with EXACTLY one ```json fenced block and "
             "nothing else: {\"D1\": 0-5, \"D2\": 0-5, \"D3\": 0-5, "
             "\"D4\": 0-5, \"D5\": 0-5, \"notes\": \"one line per dim\"}. "
             "3 = acceptable with notes, not good. Be harsh about invented "
             "facts and about reasoning that merely restates the artifact.")

JUDGE_USER = """TASK: {task}

CONTEXT THE COMPOSER HAD:
{context}

REASONING TO JUDGE:
{reasoning}

ARTIFACT IT PRODUCED:
{artifact}

Score D1 forward plausibility (could this reasoning lead here?),
D2 groundedness (all claims from the context above?),
D3 coherence (no contradictions?),
D4 genuine derivation (alternatives weighed and ruled out, not restated?),
D5 coverage (task fully addressed?)."""


def _parse_scores(text):
    m = re.search(r"```json(.*?)```", text, re.S)
    blob = m.group(1).strip() if m else text.strip()
    try:
        doc = json.loads(blob)
    except Exception:
        return None
    scores = {}
    for d in DIMS:
        try:
            v = int(doc[d])
        except Exception:
            return None
        if not 0 <= v <= 5:
            return None
        scores[d] = v
    return scores


def judge_trace(client, tid, step, task, context, reasoning, artifact,
                max_tokens=8192):
    user = JUDGE_USER.format(
        task=task, context=(context or "")[:8000],
        reasoning=(reasoning or "")[:12000],
        artifact=json.dumps(artifact, ensure_ascii=False)[:8000])
    draws = []
    for _ in range(3):
        try:
            raw, _ = client.generate(user, instructions=JUDGE_SYS,
                                     max_output_tokens=max_tokens)
            s = _parse_scores(raw)
            draws.append(s or {"error": "unparsable judge output"})
        except ZenError as e:
            draws.append({"error": str(e)[:200]})
    good = [d for d in draws if "error" not in d]
    if not good:
        return {"tid": tid, "step": step, "error": "all 3 judges failed"}
    means = {d: round(sum(g[d] for g in good) / len(good), 2) for d in DIMS}
    overall = round(sum(means.values()) / len(means), 2)
    rec = {"tid": tid, "step": step, "n_judges": len(good),
           "scores": draws, "means": means, "overall": overall,
           "pass": bool(overall >= 4.0 and min(means.values()) >= 3)}
    return rec


TASK_OF = {
    "meta": "derive one META section from the story root",
    "plots": "define the plots (one perspective per thread) from root+meta",
    "entity": "write one entity profile from meta+plots",
    "expose": "tell the story once (ending-first, synopsis, jacket) from all above",
    "skeleton": "define one event skeleton (question, owner plot, scenes)",
    "chain": "assign events to one plot as a causal chain",
    "event": "fill one event with state triples and reconciled prose",
    "card": "write one scene card (changes, minds, function)",
    "prose": "write one scene's dialogue+action from its card (blind)",
}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--tids", default=None)
    ap.add_argument("--model", default=os.environ.get("ZEN_MODEL", "muse-spark-1.3-contributor-free"))
    ap.add_argument("--max-tokens", type=int, default=8192)
    args = ap.parse_args(argv)

    recs = []
    with open(args.inp, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                recs.append(json.loads(line))
    if args.tids:
        want = set(args.tids.split(","))
        recs = [r for r in recs if r.get("tid") in want]
    recs = [r for r in recs if r.get("artifact") and not r.get("error")]

    done = set()
    out_path = Path(args.out)
    if out_path.exists():
        with open(out_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    done.add(json.loads(line).get("tid"))

    client = ZenClient(model=args.model)
    n_new = n_pass = 0
    with out_path.open("a", encoding="utf-8") as out:
        for r in recs:
            if r["tid"] in done:
                continue
            step = r.get("step", "?")
            rec = judge_trace(client, r["tid"], step,
                              TASK_OF.get(step, step), r.get("prompt", ""),
                              r.get("reasoning"),
                              r.get("artifact"), max_tokens=args.max_tokens)
            out.write(json.dumps(rec, ensure_ascii=False) + "\n")
            out.flush()
            done.add(r["tid"])
            n_new += 1
            n_pass += bool(rec.get("pass"))
            print("%s %-8s %s overall=%s" % (
                "PASS" if rec.get("pass") else ("ERROR" if rec.get("error") else "fail"),
                step, r["tid"], rec.get("overall")), flush=True)
    print("judged %d new, %d pass" % (n_new, n_pass))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
