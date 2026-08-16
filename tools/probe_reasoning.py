"""Probe what reasoning Grok 4.6 will actually give up through the Hyprlab API.

Three questions decide the architecture of the transition layer:

  A. Does `reasoning_content` come back on a real narrative task, how long is it,
     and does `reasoning_effort` move it?
  B. Is that native trace *usable* — does it reason about the things we need
     (theory of mind, appraisal, trajectory), or is it a terse planning scratch?
  C. Can the model instead emit a deliberate, written-out trace as structured
     JSON, and how does that compare in depth and cost?

Run:  python3 tools/probe_reasoning.py [--quick]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import requests

from narrativeforge.backends.hyprlab import load_env
import os

load_env(Path(__file__).resolve().parent.parent / ".env")
KEY = os.environ["HYPRLAB_API_KEY"]
BASE = os.environ.get("HYPRLAB_BASE_URL", "https://api.hyprlab.io/v1")
OUT = Path(__file__).resolve().parent.parent / "runs" / "probes"
OUT.mkdir(parents=True, exist_ok=True)

# A real transition task drawn from the finished run, so the probe measures the
# actual workload rather than a toy.
CONTEXT = """\
STORY ROOT (excerpt)
- Title: False Weight. Low fantasy, screenplay, plain register, dialogue 70%.
- Rule: magic exists only as binding — a named living person pays a concrete
  bodily cost; it never solves a problem without creating a worse one.
- Rule: a presentation-relic that is not the original holds the compact only
  while a living smith continues to pay a hidden levy bound into the piece.
- Keep in mind: do not redeem the master cheaply or damn him as simply selfish;
  the old reasons must still be audible. She thinks in work — moral confusion
  arrives as practical questions about what is owed.

ESTABLISHED ENTITIES
- ch-01 Willa, 24, blacksmith's apprentice. Taken into the forge-house as a
  child after her people died. Competent at craft, bad at deciding what she
  owes people. State: oath/debt_account = "unsettled", trust_in_orren = 70,
  hands_frosted = true, relic_knowledge = "read_as_forgery".
- ch-02 Orren, 71, the smith who raised her. Forged the false relic forty years
  ago after the original was lost in a slide, and bound the levy to himself so
  the compact would hold. Failing body. State: levy_paid = true,
  admission = "unspoken", body = "failing".
- ob-01 the village weight — the presentation relic. State: authenticity =
  "forgery_unread_by_village", custody = "with_willa".

PRIOR EVENT
ev-007: Before sleep Willa weighs the recovered piece, reads the false weight
and Orren's forty-year weld, and keeps that reading inside the house.

THE NODE TO GENERATE
ev-008: She takes the reading to Orren; he admits the forty-year weld and the
levy bound to himself. This event discharges pl-02:st5 (admission_of_the_weld).
"""

TASK = "Generate event ev-008 as a JSON object with fields: summary, action (60-160 words, third person, no direct speech), and state_changes (a list of {entity, variable, before, after, dimension, magnitude})."


def call(payload, tag):
    t0 = time.time()
    r = requests.post(f"{BASE}/chat/completions",
                      headers={"Authorization": f"Bearer {KEY}"},
                      json=payload, timeout=1200)
    dt = time.time() - t0
    if r.status_code != 200:
        return {"tag": tag, "error": f"HTTP {r.status_code}: {r.text[:300]}", "secs": dt}
    d = r.json()
    msg = d["choices"][0]["message"]
    u = d.get("usage", {})
    return {
        "tag": tag, "secs": round(dt, 1),
        "content": msg.get("content") or "",
        "reasoning": msg.get("reasoning_content") or "",
        "finish": d["choices"][0].get("finish_reason"),
        "prompt_tokens": u.get("prompt_tokens"),
        "completion_tokens": u.get("completion_tokens"),
        "reasoning_tokens": (u.get("completion_tokens_details") or {}).get("reasoning_tokens"),
        "model": d.get("model"),
    }


# --------------------------------------------------------------- Probe A
def probe_a(quick=False):
    """Native reasoning_content vs reasoning_effort."""
    efforts = ["low", "high"] if quick else [None, "low", "medium", "high"]
    jobs = []
    for eff in efforts:
        p = {"model": "grok-4.6",
             "messages": [{"role": "system", "content": "You are a narrative architect."},
                          {"role": "user", "content": CONTEXT + "\n" + TASK}],
             "max_completion_tokens": 20000, "temperature": 0.8}
        if eff:
            p["reasoning_effort"] = eff
        jobs.append((p, f"A.effort={eff or 'default'}"))
    with ThreadPoolExecutor(max_workers=4) as ex:
        return list(ex.map(lambda j: call(*j), jobs))


# --------------------------------------------------------------- Probe B
TOM_MARKERS = {
    "perception": r"\b(sees?|hears?|smell|taste|touch|cold|sound|light|feel of)\b",
    "appraisal": r"\b(values?|shame|guilt|pride|betray|owe[sd]?|worth|dignity)\b",
    "theory_of_mind": r"\b(thinks that .* thinks|believes .* believes|assumes .* (thinks|knows)|what he thinks she|what she thinks he)\b",
    "inhibition": r"\b(conceal|withhold|does not say|suppress|hides?|masks?|refrains)\b",
    "trajectory": r"\b(by the end|over the (scene|event)|begins .* ends|shifts? from .* to|escalat|de-escalat)\b",
    "craft": r"\b(audience|genre|dramatic|reader|tension|midpoint|stakes|pacing)\b",
    "object_state": r"\b(the (weight|relic|piece) (is|becomes|moves|passes)|custody|possession)\b",
}


def score_trace(text):
    t = (text or "").lower()
    return {k: len(re.findall(p, t)) for k, p in TOM_MARKERS.items()}


# --------------------------------------------------------------- Probe C
EXPLICIT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["craft_rationale", "entity_psychology", "decision"],
    "properties": {
        "craft_rationale": {
            "type": "object", "additionalProperties": False,
            "required": ["audience_need", "genre_convention", "dramatic_function", "why_now", "alternatives_rejected"],
            "properties": {
                "audience_need": {"type": "string"},
                "genre_convention": {"type": "string"},
                "dramatic_function": {"type": "string"},
                "why_now": {"type": "string"},
                "alternatives_rejected": {"type": "array", "items": {"type": "string"}},
            },
        },
        "entity_psychology": {
            "type": "object",
            "additionalProperties": {
                "type": "object", "additionalProperties": False,
                "required": ["perception", "appraisal", "social_norms", "theory_of_mind",
                             "urges", "impairments", "deliberation", "control", "intention",
                             "action", "trajectory"],
                "properties": {
                    "perception": {
                        "type": "object", "additionalProperties": False,
                        "required": ["sight", "sound", "touch", "smell", "taste", "interoception"],
                        "properties": {k: {"type": "string"} for k in
                                       ["sight", "sound", "touch", "smell", "taste", "interoception"]},
                    },
                    "appraisal": {
                        "type": "object", "additionalProperties": False,
                        "required": ["value_at_stake", "valence", "self_conscious_emotion", "moral_reading"],
                        "properties": {"value_at_stake": {"type": "string"},
                                       "valence": {"type": "integer"},
                                       "self_conscious_emotion": {"type": "string"},
                                       "moral_reading": {"type": "string"}},
                    },
                    "social_norms": {
                        "type": "object", "additionalProperties": False,
                        "required": ["norms_in_force", "how_others_would_judge", "standing_at_risk"],
                        "properties": {"norms_in_force": {"type": "array", "items": {"type": "string"}},
                                       "how_others_would_judge": {"type": "string"},
                                       "standing_at_risk": {"type": "string"}},
                    },
                    "theory_of_mind": {
                        "type": "object", "additionalProperties": False,
                        "required": ["d1", "d2", "d3"],
                        "properties": {
                            "d1": {"type": "string", "description": "what this character believes about another"},
                            "d2": {"type": "string", "description": "what this character believes the other believes about them"},
                            "d3": {"type": "string", "description": "what this character believes the other believes they believe"},
                        },
                    },
                    "urges": {
                        "type": "object", "additionalProperties": False,
                        "required": ["cravings", "physical_needs", "psych_needs_conscious", "psych_needs_unconscious"],
                        "properties": {k: {"type": "string"} for k in
                                       ["cravings", "physical_needs", "psych_needs_conscious", "psych_needs_unconscious"]},
                    },
                    "impairments": {
                        "type": "object", "additionalProperties": False,
                        "required": ["physical", "medical", "magical", "chemical", "coercive"],
                        "properties": {k: {"type": "string"} for k in
                                       ["physical", "medical", "magical", "chemical", "coercive"]},
                    },
                    "deliberation": {
                        "type": "object", "additionalProperties": False,
                        "required": ["options_weighed", "reasoning", "chosen_because"],
                        "properties": {"options_weighed": {"type": "array", "items": {"type": "string"}},
                                       "reasoning": {"type": "string"},
                                       "chosen_because": {"type": "string"}},
                    },
                    "control": {
                        "type": "object", "additionalProperties": False,
                        "required": ["mode", "felt", "expressed", "divergence_reason"],
                        "properties": {"mode": {"enum": ["spontaneous", "inhibited", "mixed"]},
                                       "felt": {"type": "string"}, "expressed": {"type": "string"},
                                       "divergence_reason": {"type": "string"}},
                    },
                    "intention": {"type": "string"},
                    "action": {"type": "string"},
                    "trajectory": {
                        "type": "array",
                        "description": "how this character's state evolves ACROSS the unit, not one snapshot",
                        "items": {"type": "object", "additionalProperties": False,
                                  "required": ["phase", "shift", "trigger"],
                                  "properties": {"phase": {"type": "string"},
                                                 "shift": {"type": "string"},
                                                 "trigger": {"type": "string"}}},
                    },
                },
            },
        },
        "decision": {"type": "string"},
    },
}


def probe_c():
    instr = """\
Before you generate the node, produce a TRANSITION: an explicit, written-out
reasoning trace. This is not a summary of your thinking — it IS the thinking,
externalized, and it will be read by other people and used as training data.

It must cover, for EVERY entity materially involved:
 - perception across all five senses plus interoception, as that entity has it now
 - appraisal against that entity's own values, with the self-conscious emotion named
 - the social norms in force and how others present would judge the act
 - theory of mind to three degrees: what A believes about B (d1), what A believes
   B believes about A (d2), what A believes B believes A believes (d3)
 - urges: cravings, physical needs, conscious and unconscious psychological needs
 - impairments: physical, medical, magical, chemical, coercive
 - deliberate analysis: the options weighed and why one was chosen
 - whether the act is spontaneous or inhibited, what is FELT versus what is
   EXPRESSED, and why they diverge if they do
 - intention, then the action actually taken
 - a TRAJECTORY: how the state evolves across the unit in phases, with triggers.
   Not one snapshot — a character enters an event in one state and leaves in
   another, and the phases between are what the writer needs.

Plus craft rationale: what the audience needs here, what the genre expects,
what dramatic function this serves, why it happens now and not earlier, and
which alternatives you rejected.

Be concrete and specific to THIS story. Generic psychology is a failure."""
    p = {"model": "grok-4.6",
         "messages": [{"role": "system", "content": "You are a narrative architect."},
                      {"role": "user", "content": CONTEXT + "\n" + instr}],
         "response_format": {"type": "json_schema",
                             "json_schema": {"name": "transition", "strict": False,
                                             "schema": EXPLICIT_SCHEMA}},
         "max_completion_tokens": 32000, "temperature": 0.7, "reasoning_effort": "high"}
    return call(p, "C.explicit_structured")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    args = ap.parse_args()

    print("=" * 74)
    print("PROBE A — native reasoning_content vs reasoning_effort")
    print("=" * 74)
    res_a = probe_a(args.quick)
    for r in res_a:
        if r.get("error"):
            print(f"  {r['tag']:<22} ERROR {r['error'][:90]}")
            continue
        rl, cl = len(r["reasoning"]), len(r["content"])
        print(f"  {r['tag']:<22} reasoning={rl:>7,} chars  content={cl:>6,} chars  "
              f"rtok={r['reasoning_tokens']:>6}  otok={r['completion_tokens']:>5}  {r['secs']:>5}s")

    print()
    print("=" * 74)
    print("PROBE B — is the native trace about the things we need?")
    print("=" * 74)
    best = max((r for r in res_a if not r.get("error")), key=lambda r: len(r["reasoning"]), default=None)
    if best:
        sc = score_trace(best["reasoning"])
        print(f"  scoring the longest native trace ({best['tag']}, {len(best['reasoning']):,} chars)")
        for k, v in sc.items():
            print(f"    {k:<16} {v:>3} hits  {'yes' if v else 'NO'}")
        (OUT / "native_trace.txt").write_text(best["reasoning"])
        print(f"  -> saved {OUT/'native_trace.txt'}")

    print()
    print("=" * 74)
    print("PROBE C — deliberate written-out structured transition")
    print("=" * 74)
    r = probe_c()
    if r.get("error"):
        print(f"  ERROR {r['error'][:200]}")
    else:
        print(f"  content={len(r['content']):,} chars  native_reasoning={len(r['reasoning']):,} chars")
        print(f"  reasoning_tokens={r['reasoning_tokens']}  completion_tokens={r['completion_tokens']}  {r['secs']}s")
        try:
            doc = json.loads(r["content"])
            (OUT / "explicit_transition.json").write_text(json.dumps(doc, indent=1, ensure_ascii=False))
            ents = list((doc.get("entity_psychology") or {}).keys())
            print(f"  parsed OK. entities covered: {ents}")
            for e in ents:
                p = doc["entity_psychology"][e]
                traj = len(p.get("trajectory") or [])
                tom = p.get("theory_of_mind", {})
                print(f"    {e}: trajectory phases={traj}  tom d1/d2/d3 = "
                      f"{bool(tom.get('d1'))}/{bool(tom.get('d2'))}/{bool(tom.get('d3'))}")
            sc = score_trace(json.dumps(doc))
            print("  marker scores on the explicit trace:")
            for k, v in sc.items():
                print(f"    {k:<16} {v:>3}")
            print(f"  -> saved {OUT/'explicit_transition.json'}")
        except Exception as exc:
            print(f"  parse failed: {exc}")
            (OUT / "explicit_raw.txt").write_text(r["content"])

    json.dump({"probe_a": res_a, "probe_c": r}, open(OUT / "probe_results.json", "w"),
              indent=1, ensure_ascii=False)
    print(f"\nfull results -> {OUT/'probe_results.json'}")


if __name__ == "__main__":
    main()
