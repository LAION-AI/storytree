#!/usr/bin/env python3
"""Deepen V4 scene nodes with a second agent pass, instead of replacing them.

CogniTino replaced the V-series node with a two-layer object and lost. This keeps the V4
node exactly as produced and adds a layer on top of it, so whatever V4 already does well —
fidelity, specificity, calibration — is untouched by construction, and only the dimensions
it does badly are targeted.

Two passes:

  1. `deepen`  — one agent per scene, sees the scene text and the V4 node, and writes what
                 the node leaves implicit: what people want and conceal, what each believes
                 about the others, and the internal state changes that are not physical.
  2. `connect` — the same scenes again, now each agent also sees every other scene's pass-1
                 output, and writes causal links: what this scene was caused by, what it
                 causes later. Each link names a cause pointer and an effect pointer.

Nothing may be asserted without a justification, and speculation must be labelled as such.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Sequence

sys.path.insert(0, "/home/deployer/laion/project-alexandria/screenplay/src")
from screenplay_ku.client import EndpointPool, run_parallel  # noqa: E402
from screenplay_ku.kuschema import grammar_safe  # noqa: E402
from screenplay_ku.scenes import load_scenes, load_source  # noqa: E402

SAMPLE = ["sc-003", "sc-008", "sc-015", "sc-024", "sc-039",
          "sc-056", "sc-075", "sc-097", "sc-113", "sc-129",
          "sc-148", "sc-164", "sc-182", "sc-200", "sc-215"]

SYSTEM = (
    "You deepen an existing scene analysis. You do not rewrite it and you do not repeat it. "
    "You add what it left implicit: what people want and hide, what they believe about each "
    "other, and what changes inside them. Every claim you make carries its justification and "
    "its evidence. You return only valid JSON."
)

_DEEPEN = """\
A scene and an existing analysis of it are below. The analysis is competent on what happens.
Your job is the part it left out.

Add three things, and nothing else:

**1. `minds` — what is going on inside people.**
For each person who is present and matters, record what they want, what they fear, and above
all **what they are concealing and from whom**. Naming an emotion is not enough; anyone can
write "she is tense". The bar is reading a concealed motive or an unspoken pressure *from
behaviour*, and reading it briefly.

  weak   — "Trinity is tense during the escape."
  strong — "Trinity keeps working the trace after the line is compromised, which means she
            has decided the information outweighs her own extraction, and she has told no one
            she made that decision."

**2. `theory_of_mind` — what A believes about B.**
Not what a character believes about the world; what they believe about *another mind*. Nest
it where the scene supports nesting: what A thinks B thinks about A. Set `who` to the
believer and `about` to whom the belief concerns.

**Be careful with knowledge.** Do not credit a character with knowing something the story has
not yet given them. Attributing knowledge a character does not have is the single most
damaging error available here, because everything downstream inherits it.

**3. `internal_changes` — state changes that are not physical.**
The V-series records that a door opened or a gun was drawn. Record what changed inside
someone: a belief revised, trust staked or withdrawn, a decision made silently, a fear
confirmed. `before` and `after` must genuinely differ, and the difference must matter later.

  not a change — `neo.location: hallway -> room` (physical; already recorded)
  a change     — `neo.trust_in_morpheus: provisional -> staked`

## Rules that make this worth having

- **Every entry carries `because`** — the behaviour in the scene that licenses it, quoted or
  described. An entry without a justification is an invention.
- **Say what would prove you wrong** in `would_be_wrong_if`. If you cannot name it, the
  claim is too vague to record.
- **Label your confidence honestly**: `speculative` / `plausible` / `probable` /
  `near-certain`. Second-order belief is rarely above `plausible`. If every entry carries the
  same label you are decorating, not calibrating.
- **Match the scene.** A twelve-word establishing shot with no people in it gets empty arrays.
  That is the correct answer, not a failure. A four-hundred-word confrontation deserves
  several entries per person. Do not pad a small scene and do not starve a large one.
- **Do not restate the analysis.** If it is already in the node below, it does not belong in
  your output.

SCENE {scene_id} ({words} words)
=== SCENE TEXT ===
{text}

=== EXISTING ANALYSIS ===
{node}
"""

_CONNECT = """\
You previously deepened one scene. You can now see every other scene's deepening.

Add causal links, and only causal links. Two kinds:

  `caused_by` — something earlier in the film that produced the state you recorded here
  `causes`    — something later that this scene makes possible, or forecloses

Each link needs:
  - `cause` — a pointer: the scene id, and what in it
  - `effect` — a pointer: the scene id, and what in it
  - `because` — why one produces the other
  - `confidence` — speculative / plausible / probable / near-certain

**Speculation is allowed and useful, but it must be argued.** "This scene probably matters
later" is worthless. "Neo's silent decision here is what lets him refuse the same offer in
sc-182, where he has no time to deliberate" is a claim someone can check and disagree with.

Link only across scenes you can actually see below. Do not invent scene ids. Return an empty
array if this scene genuinely connects to nothing — a transitional scene often does not.

YOUR SCENE: {scene_id}
=== YOUR DEEPENING ===
{mine}

=== EVERY OTHER SCENE'S DEEPENING ===
{others}
"""

CONF = ["speculative", "plausible", "probable", "near-certain"]


def deepen_schema() -> Dict[str, Any]:
    entry = lambda extra: {  # noqa: E731
        "type": "object",
        "properties": dict({
            "who": {"type": "string", "minLength": 1},
            "because": {"type": "string", "minLength": 20},
            "would_be_wrong_if": {"type": "string", "minLength": 10},
            "confidence": {"type": "string", "enum": CONF},
        }, **extra),
        "required": ["who", "because", "would_be_wrong_if", "confidence"] + list(extra),
        "additionalProperties": False,
    }
    return {
        "type": "object",
        "properties": {
            "minds": {"type": "array", "maxItems": 8, "items": entry({
                "wants": {"type": "string", "minLength": 10},
                "fears": {"type": "string", "minLength": 5},
                "conceals": {"type": "string", "minLength": 5},
                "from_whom": {"type": ["string", "null"]},
            })},
            "theory_of_mind": {"type": "array", "maxItems": 8, "items": entry({
                "about": {"type": "string", "minLength": 1},
                "believes": {"type": "string", "minLength": 20},
            })},
            "internal_changes": {"type": "array", "maxItems": 10, "items": entry({
                "axis": {"type": "string", "minLength": 3},
                "before": {"type": "string", "minLength": 2},
                "after": {"type": "string", "minLength": 2},
            })},
        },
        "required": ["minds", "theory_of_mind", "internal_changes"],
        "additionalProperties": False,
    }


def connect_schema(scene_ids: Sequence[str]) -> Dict[str, Any]:
    ref = {"type": "string", "enum": list(scene_ids)}
    return {
        "type": "object",
        "properties": {"causal_links": {"type": "array", "maxItems": 10, "items": {
            "type": "object",
            "properties": {
                "kind": {"type": "string", "enum": ["caused_by", "causes"]},
                "cause": {"type": "object", "properties": {
                    "scene_id": ref, "what": {"type": "string", "minLength": 10}},
                    "required": ["scene_id", "what"], "additionalProperties": False},
                "effect": {"type": "object", "properties": {
                    "scene_id": ref, "what": {"type": "string", "minLength": 10}},
                    "required": ["scene_id", "what"], "additionalProperties": False},
                "because": {"type": "string", "minLength": 25},
                "confidence": {"type": "string", "enum": CONF},
            },
            "required": ["kind", "cause", "effect", "because", "confidence"],
            "additionalProperties": False,
        }}},
        "required": ["causal_links"],
        "additionalProperties": False,
    }


def _parse(text: str) -> Dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.S)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        a, b = text.find("{"), text.rfind("}")
        if a >= 0 and b > a:
            return json.loads(text[a:b + 1])
        raise


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--v4-dir", default="reconstruct/runs/matrix/fix_v4")
    ap.add_argument("--source", default="reconstruct/runs/matrix/script.normalized.txt")
    ap.add_argument("--scene-map", default="reconstruct/runs/matrix/script_map.json")
    ap.add_argument("--out", required=True)
    ap.add_argument("--ports", default="8100-8106")
    ap.add_argument("--model", default="qwen3.8-27b")
    ap.add_argument("--workers", type=int, default=14)
    args = ap.parse_args()

    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    started = time.time()
    source = load_source(Path(args.source))
    scenes = {s.scene_id: s for s in load_scenes(Path(args.scene_map), source)}

    nodes = {}
    for sid in SAMPLE:
        p = Path(args.v4_dir) / "{}.json".format(sid)
        if p.exists():
            nodes[sid] = json.loads(p.read_text(encoding="utf-8"))
    print("V4 nodes loaded: {}".format(len(nodes)), flush=True)

    lo, hi = (args.ports.split("-") + [None])[:2]
    ports = list(range(int(lo), int(hi) + 1)) if hi else [int(lo)]
    pool = EndpointPool(ports, args.model, temperature=0.6, max_tokens=8192)

    ids = sorted(nodes)
    prog = lambda d, t, r: print("    [{}/{}]{}".format(  # noqa: E731
        d, t, " !" if isinstance(r, Exception) else ""), flush=True) if d % 5 == 0 or d == t else None

    print("\npass 1 — deepen ({} scenes)".format(len(ids)), flush=True)
    def deepen(sid):
        scene = scenes[sid]
        prompt = _DEEPEN.format(scene_id=sid, words=scene.word_count,
                                text=scene.text(source),
                                node=json.dumps(nodes[sid], ensure_ascii=False, indent=1))
        r = pool.call(SYSTEM, prompt, schema=grammar_safe(deepen_schema()), max_tokens=8192)
        return _parse(r.text), r.prompt_tokens, r.completion_tokens

    res = run_parallel(ids, deepen, max_workers=args.workers, on_done=prog)
    deep, calls, tin, tout = {}, 0, 0, 0
    for sid, r in zip(ids, res):
        if isinstance(r, Exception):
            print("  fail {}: {}".format(sid, r)); continue
        payload, a, b = r
        deep[sid] = payload; calls += 1; tin += a; tout += b
    print("  {} deepened | minds {} | tom {} | internal {}".format(
        len(deep), sum(len(v['minds']) for v in deep.values()),
        sum(len(v['theory_of_mind']) for v in deep.values()),
        sum(len(v['internal_changes']) for v in deep.values())), flush=True)

    print("\npass 2 — connect (each sees all others)", flush=True)
    def brief(sid):
        v = deep.get(sid) or {}
        return {"scene_id": sid,
                "minds": [{"who": m["who"], "wants": m.get("wants"), "conceals": m.get("conceals")}
                          for m in v.get("minds") or []],
                "internal_changes": [{"who": c["who"], "axis": c.get("axis"),
                                      "before": c.get("before"), "after": c.get("after")}
                                     for c in v.get("internal_changes") or []]}

    def connect(sid):
        others = [brief(o) for o in ids if o != sid and o in deep]
        prompt = _CONNECT.format(scene_id=sid,
                                 mine=json.dumps(deep.get(sid), ensure_ascii=False, indent=1),
                                 others=json.dumps(others, ensure_ascii=False, indent=1))
        r = pool.call(SYSTEM, prompt, schema=grammar_safe(connect_schema(ids)), max_tokens=6144)
        return _parse(r.text), r.prompt_tokens, r.completion_tokens

    res2 = run_parallel([s for s in ids if s in deep], connect,
                        max_workers=args.workers, on_done=prog)
    links = {}
    for sid, r in zip([s for s in ids if s in deep], res2):
        if isinstance(r, Exception):
            print("  fail {}: {}".format(sid, r)); continue
        payload, a, b = r
        links[sid] = payload.get("causal_links") or []; calls += 1; tin += a; tout += b
    print("  {} causal links".format(sum(len(v) for v in links.values())), flush=True)

    enriched = {}
    for sid in ids:
        node = dict(nodes[sid])
        d = deep.get(sid) or {}
        # Added alongside, never overwriting: whatever V4 does well is untouched by
        # construction, and an evaluator can strip these keys to recover V4 exactly.
        node["deepened_minds"] = d.get("minds") or []
        node["theory_of_mind"] = d.get("theory_of_mind") or []
        node["internal_changes"] = d.get("internal_changes") or []
        node["causal_links"] = links.get(sid) or []
        enriched[sid] = node
        (out / "{}.json".format(sid)).write_text(json.dumps(node, indent=1), encoding="utf-8")

    protocol = {"scenes": len(enriched), "calls": calls,
                "tokens_in": tin, "tokens_out": tout,
                "seconds": round(time.time() - started, 1),
                "minds": sum(len(v.get("minds") or []) for v in deep.values()),
                "theory_of_mind": sum(len(v.get("theory_of_mind") or []) for v in deep.values()),
                "internal_changes": sum(len(v.get("internal_changes") or []) for v in deep.values()),
                "causal_links": sum(len(v) for v in links.values())}
    (out / "protocol.json").write_text(json.dumps(protocol, indent=1), encoding="utf-8")
    print("\n{}".format(json.dumps(protocol, indent=1)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
