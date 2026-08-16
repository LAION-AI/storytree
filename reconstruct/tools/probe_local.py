"""Does the local llama-server accept what this pipeline actually sends?

Four things can differ from a hosted OpenAI-compatible endpoint, and each of
them fails hours into a run rather than at the start:

  1. `response_format: json_schema` — llama.cpp converts the schema to a GBNF
     grammar. Our transition schemas are deep, use `additionalProperties:false`
     and enums, and the converter does not cover everything. If it silently
     ignores the schema we get prose instead of JSON; if it rejects it we get a
     400 at call one.
  2. `reasoning_effort` — GLM-5.2's template defaults to Max. Unconstrained,
     hidden reasoning ran at 1.5x visible output in our hosted logs and 11x on
     one call. Locally that is not a billing question, it is a wall-clock
     question: it multiplies an eight-hour job.
  3. The token accounting field names, which decide whether the run's own cost
     numbers mean anything.
  4. Real throughput on a real payload, as opposed to on a benchmark prompt.

Run it before committing to anything long.
"""

from __future__ import annotations

import json
import sys
import time

import requests

BASE = "http://127.0.0.1:8099/v1"
KEY = "local"

SMALL = {
    "type": "object", "additionalProperties": False,
    "required": ["verdict", "why"],
    "properties": {"verdict": {"type": "string", "enum": ["yes", "no"]},
                   "why": {"type": "string"}},
}

# the shape that matters: nested objects, arrays of objects, enums, required
DEEP = {
    "type": "object", "additionalProperties": False,
    "required": ["entity", "trajectory"],
    "properties": {
        "entity": {"type": "string"},
        "trajectory": {
            "type": "array", "minItems": 2,
            "items": {
                "type": "object", "additionalProperties": False,
                "required": ["phase", "trigger", "state"],
                "properties": {
                    "phase": {"type": "string"},
                    "trigger": {"type": "string"},
                    "state": {"type": "string",
                              "enum": ["guarded", "opening", "committed", "breaking"]},
                },
            },
        },
    },
}


def call(label, messages, schema=None, max_tokens=2000, **extra):
    body = {"model": "glm", "messages": messages,
            "max_tokens": max_tokens, "temperature": 0.7, **extra}
    if schema is not None:
        body["response_format"] = {"type": "json_schema",
                                   "json_schema": {"name": "p", "strict": False,
                                                   "schema": schema}}
    t0 = time.time()
    try:
        r = requests.post(f"{BASE}/chat/completions",
                          headers={"Authorization": f"Bearer {KEY}"},
                          json=body, timeout=1800)
    except Exception as exc:
        print(f"  {label:<22} TRANSPORT FAILED: {exc}")
        return None
    dt = time.time() - t0
    if r.status_code != 200:
        print(f"  {label:<22} HTTP {r.status_code}: {r.text[:220]}")
        return None
    d = r.json()
    msg = d["choices"][0]["message"]
    content = msg.get("content") or ""
    reasoning = msg.get("reasoning_content") or ""
    u = d.get("usage", {})
    pt, ct = u.get("prompt_tokens", 0), u.get("completion_tokens", 0)
    tps = ct / dt if dt else 0
    print(f"  {label:<22} {r.status_code}  {dt:>6.1f}s  in={pt:<7,} out={ct:<7,} "
          f"{tps:>5.1f} tok/s  reasoning={len(reasoning):,}c  content={len(content):,}c")
    parsed = None
    if content.strip():
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as exc:
            print(f"    {'':<20} NOT JSON: {exc}  first 160: {content[:160]!r}")
    return {"parsed": parsed, "content": content, "reasoning": reasoning,
            "usage": u, "secs": dt, "tps": tps, "finish": d["choices"][0].get("finish_reason")}


if __name__ == "__main__":
    print(f"probing {BASE}\n")

    print("1. plain call, no schema")
    call("no-schema", [{"role": "user", "content": "Reply with the single word: ready."}],
         max_tokens=200)

    print("\n2. json_schema support")
    r = call("small schema", [{"role": "user",
             "content": "Is a raven a bird? Answer in the given JSON schema."}], SMALL)
    if r and r["parsed"]:
        print(f"    -> conformed: {r['parsed']}")
    elif r:
        print("    -> SCHEMA NOT ENFORCED — grammar path unusable, need prompt-only JSON")

    print("\n3. deep nested schema (arrays of objects + enums, like our real ones)")
    r = call("deep schema", [{"role": "user", "content":
             "A guarded informant slowly decides to trust a stranger over one conversation. "
             "Give their trajectory with at least 3 phases, in the given schema. entity id is 'e-01'."}],
             DEEP, max_tokens=4000)
    if r and r["parsed"]:
        ph = r["parsed"].get("trajectory") or []
        print(f"    -> conformed, {len(ph)} phases, states={[p.get('state') for p in ph]}")
    elif r:
        print("    -> DEEP SCHEMA FAILED — this is the shape the pipeline needs")

    print("\n4. reasoning control (this decides the wall-clock of the whole run)")
    q = [{"role": "user", "content":
          "Two spies meet in a cafe. One is lying. Decide who and why, in 120 words."}]
    base = call("default effort", q, max_tokens=8000)
    for effort in ("low", "minimal", "none"):
        call(f"effort={effort}", q, max_tokens=8000, reasoning_effort=effort)
    call("chat_template_kwargs", q, max_tokens=8000,
         chat_template_kwargs={"enable_thinking": False})

    print("\n5. sustained throughput on a realistic payload")
    filler = ("The rain had not stopped for three days and the gutters ran black. "
              "Nobody in the building admitted to hearing the argument on the fourth floor. ") * 260
    r = call("~10k in / 3k out", [
        {"role": "system", "content": "You are a script analyst."},
        {"role": "user", "content": filler + "\n\nSummarise the mood in 900 words."}],
        max_tokens=3000)

    print("\ndone")
