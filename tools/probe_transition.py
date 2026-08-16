"""Can Grok 4.6 fill the real transition schema, and is what it produces any good?

Probe A/B established that the native `reasoning_content` is a compressed
summary with none of the content we need. This probe tests the alternative:
force the model to write the trace out on purpose, against the actual schema
from narrativeforge.transitions, and score what comes back.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import requests

from narrativeforge.backends.hyprlab import load_env
from narrativeforge.transitions import TRANSITION_SCHEMA, grade, score_transition

load_env(Path(__file__).resolve().parent.parent / ".env")
KEY = os.environ["HYPRLAB_API_KEY"]
BASE = os.environ.get("HYPRLAB_BASE_URL", "https://api.hyprlab.io/v1")
OUT = Path(__file__).resolve().parent.parent / "runs" / "probes"
OUT.mkdir(parents=True, exist_ok=True)

CONTEXT = Path(__file__).resolve().parent / "_probe_context.txt"
if not CONTEXT.exists():
    CONTEXT.write_text("""\
STORY ROOT (excerpt)
- Title: False Weight. Low fantasy, screenplay, plain register, dialogue 70%.
- Audience: adult, upper reading level. Reader promise: a moral problem that is
  not solved by anyone being revealed as a villain.
- Rule: magic exists only as binding — a named living person pays a concrete
  bodily cost; it never solves a problem without creating a worse one.
- Rule: a presentation-relic that is not the original holds the compact only
  while a living smith continues to pay a hidden levy bound into the piece.
- Rule: that levy cannot be transferred, paused, or discharged except by the
  bound smith's death or the relic's public breaking.
- Keep in mind: do not redeem the master cheaply or damn him as simply selfish;
  the old reasons must still be audible. She thinks in work — moral confusion
  arrives as practical questions about what is owed.
- Forbidden: interior monologue that names the theme; a redemptive confession
  that restores the household without cost.

ESTABLISHED ENTITIES
- ch-01 Willa, 24, blacksmith's apprentice. Taken into the forge-house as a
  child after her people died in a hard winter. Competent at craft, bad at
  deciding what she owes people. Values: true measure, work honestly done,
  debts settled. Fear: being owed something she cannot pay.
  State: debt_account="unsettled", trust_in_orren=70, hands_frosted=true,
  relic_knowledge="read_as_forgery", belonging="of_the_house".
- ch-02 Orren, 71, the smith who raised her. Forged the false relic forty years
  ago after the original was lost in a slide, and bound the levy to himself so
  the compact would hold. Failing body, hands going. Values: the village fed,
  the work continued, no debt passed to a child.
  State: levy_paid=true, admission="unspoken", body="failing",
  what_she_knows="believes_her_ignorant".
- ob-01 the village weight — the presentation relic, a forged bar with a
  forty-year weld and an inclusion where the levy sits.
  State: authenticity="forgery_unread_by_village", custody="with_willa",
  meaning="the village's protection".
- lo-01 the forge-house. Control: Orren's. The loft above the bellows is where
  Willa has slept since she was a child.
- gr-01 Highkettle folk — the village. State: believes_protected=true.

PRIOR EVENT
ev-007 (t14): Before sleep Willa weighs the recovered piece on the forge
balance, reads the false weight and Orren's forty-year weld, and keeps that
reading inside the house — she does not wake him and does not tell the village.

THE NODE TO GENERATE
ev-008 (t16): She takes the reading to Orren; he admits the forty-year weld and
the levy bound to himself. Discharges pl-02:st5 (admission_of_the_weld).
Duration about 40 minutes, at night, in the forge-house.
""")

INSTRUCTION = """\
Produce the TRANSITION for the node named above: a deliberate, written-out
reasoning trace that argues from everything already established to the node
that must come next.

This is not a summary of thinking you did elsewhere. It IS the thinking, put on
the page on purpose, to be read by other people and used as training data. Write
it as though the reader must be able to reconstruct your judgement without
access to you.

Non-negotiables:

1. EVERY character materially involved gets a full psychology block. Both of
   them here. Perception across all seven channels as THAT character has it —
   two people in one room do not perceive the same room. Appraisal against that
   character's own declared values. The social norms actually in force.

2. THEORY OF MIND TO THREE DEGREES, per pair, in both directions. d1: what A
   believes about B. d2: what A believes B believes about A. d3: what A believes
   B believes A believes. Then state where that model is WRONG and what the
   error will cost — a theory of mind that is always accurate produces no drama.

3. TRAJECTORY, not snapshot. This event runs forty minutes. Nobody is the same
   at minute forty as at minute one. Give the phases, each with the perceivable
   trigger that causes the shift, for characters AND for objects, locations and
   groups. The relic's meaning changes during this conversation; say how.

4. What is FELT versus what is EXPRESSED, and what leaks through the control
   anyway. In a 70%-dialogue screenplay this gap is the entire craft.

5. Cite your sources. Every established fact you rely on names the node or
   pointer it came from.

Be specific to THIS story. Generic psychology is the failure mode — if a
sentence could appear in a transition for any other story, delete it."""


def run(effort="high", max_tokens=48000):
    payload = {
        "model": "grok-4.6",
        "messages": [
            {"role": "system", "content":
             "You are a narrative architect. You externalize your reasoning on purpose, "
             "in full, because the reasoning is the product."},
            {"role": "user", "content": CONTEXT.read_text() + "\n" + INSTRUCTION},
        ],
        "response_format": {"type": "json_schema",
                            "json_schema": {"name": "transition", "strict": False,
                                            "schema": TRANSITION_SCHEMA}},
        "max_completion_tokens": max_tokens,
        "temperature": 0.7,
        "reasoning_effort": effort,
    }
    t0 = time.time()
    r = requests.post(f"{BASE}/chat/completions",
                      headers={"Authorization": f"Bearer {KEY}"}, json=payload, timeout=2400)
    dt = time.time() - t0
    print(f"HTTP {r.status_code} in {dt:.0f}s")
    if r.status_code != 200:
        print(r.text[:1500])
        return None
    d = r.json()
    ch = d["choices"][0]
    msg = ch["message"]
    u = d.get("usage", {})
    content = msg.get("content") or ""
    print(f"finish_reason={ch.get('finish_reason')}  content={len(content):,} chars")
    print(f"prompt={u.get('prompt_tokens'):,}  completion={u.get('completion_tokens'):,}  "
          f"reasoning={(u.get('completion_tokens_details') or {}).get('reasoning_tokens'):,}")
    cost = (u.get("prompt_tokens", 0)/1e6)*1.8 + \
           ((u.get("completion_tokens", 0) + (u.get("completion_tokens_details") or {}).get("reasoning_tokens", 0))/1e6)*5.4
    print(f"cost for this one transition: ${cost:.3f}")

    try:
        doc = json.loads(content)
    except json.JSONDecodeError as e:
        print("JSON parse failed:", e)
        (OUT / "transition_raw.txt").write_text(content)
        return None

    (OUT / "transition_full.json").write_text(json.dumps(doc, indent=1, ensure_ascii=False))
    sc = score_transition(doc)
    verdict, gaps = grade(sc)
    print("\n--- structural depth ---")
    for k, v in sc.items():
        print(f"  {k:<28} {v}")
    print(f"\n  verdict: {verdict}")
    for g in gaps:
        print(f"    gap: {g}")

    json.dump({"usage": u, "cost_usd": round(cost, 4), "score": sc,
               "verdict": verdict, "gaps": gaps, "secs": round(dt)},
              open(OUT / "transition_meta.json", "w"), indent=1)
    return doc


if __name__ == "__main__":
    eff = sys.argv[1] if len(sys.argv) > 1 else "high"
    run(eff)
