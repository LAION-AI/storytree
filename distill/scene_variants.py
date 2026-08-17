"""Scene-layer variants, measured against a fixed sample.

The optimisation target is not reproduction of the screenplay's sentences. It is
a structure a careful reader would call good, plausible, emotionally intelligent
and complete. Word overlap therefore survives only as a floor — a node with near
zero overlap is describing a different scene — and everything above that floor is
decided by rubric.

Each variant is one function returning a (system, user, schema) triple, so the
only thing that changes between arms is the prompt and schema. Same model, same
scenes, same decoding.

    python3 distill/scene_variants.py --variant v1 --out runs/v1
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "reconstruct"))

from distill.swarm import SCENE_SCHEMA, SCENE_SYSTEM, Swarm, _window  # noqa: E402
from scriptforge import screenplay as sp  # noqa: E402

SAMPLE = ["sc-003", "sc-008", "sc-015", "sc-024", "sc-039",
          "sc-056", "sc-075", "sc-097", "sc-113", "sc-129",
          "sc-148", "sc-164", "sc-182", "sc-200", "sc-215"]


# --------------------------------------------------------------------------
# V0 — the current production prompt, as the baseline to beat
# --------------------------------------------------------------------------

def v0(scene, text: str, script: str, neighbours: str):
    user = f"""\
Describe scene {scene.scene_id}.

THE SCENE
{text[:14000]}

FOR CONTEXT ONLY — the surrounding script. Use it to understand who people are
and what has already happened. Do not describe any scene but {scene.scene_id}.
{_window(script, scene)}

SCHEMA
{json.dumps(SCENE_SCHEMA, indent=1)}
"""
    return SCENE_SYSTEM, user, SCENE_SCHEMA


# --------------------------------------------------------------------------
# V1 — ranks 1-3 of the plan, together
#
#   A1  context cut from ~100,000 characters to the two neighbouring scenes
#   B1  the scene's word count stated, with a required proportion
#   B4  explicit permission to write little
#   B5  outside inference forbidden
#   D1  location, time and speakers bound into the schema
#
# A1 is the hypothesis under test. The median scene in this work is 45 words; at
# a 100,000-character window the scene is 0.2% of what the model reads. Every
# other change here is cheap enough to ride along, which does mean V1 cannot
# attribute its result to one cause — deliberately, since the first question is
# whether the ceiling moves at all.
# --------------------------------------------------------------------------

V1_SYSTEM = """\
You are reading one scene of a screenplay and recording exactly what is in it.

THE SCENE ON THE PAGE IS YOUR ONLY SOURCE. You may use the neighbouring scenes to
know who someone is or what a reference points back to. You may not use anything
else — not your knowledge of this film, not what you expect to happen, not what
would make a better story. If it is not on the page in front of you, it does not
go in your node.

WRITE IN PROPORTION. A twelve-word scene gets a short node: one or two changes,
no elaborate psychology, and that is a correct answer, not a lazy one. A
five-hundred-word scene gets a full one. Padding a small scene is a failure of
the same kind as skimping a large one.

Every piece of evidence you cite must be COPIED from the scene, word for word.
Do not paraphrase it. If you cannot find a span that shows a change, do not claim
the change.

Name people the way this scene names them. Consistency across scenes is handled
elsewhere.

Return JSON conforming to the schema. No prose outside it."""


def v1_schema(scene) -> dict:
    """Facts bound as const, cast bound as enum. Proven in EXP-002."""
    s = json.loads(json.dumps(SCENE_SCHEMA))
    p = s["properties"]
    p["scene_id"] = {"const": scene.scene_id}
    p["location"] = {"const": scene.location}
    p["time_of_day"] = {"const": scene.time_of_day or "UNSPECIFIED"}
    ev = p["what_changes"]["items"]["properties"]["evidence"]
    ev["minLength"] = 25
    ev["description"] = ("A span COPIED VERBATIM from this scene, at least 25 "
                         "characters. Not a paraphrase.")
    if scene.speakers:
        p["speaking"] = {"type": "array",
                         "items": {"type": "string", "enum": list(scene.speakers)}}
    return s


def v1(scene, text: str, script: str, neighbours: str):
    words = scene.word_count
    if words < 40:
        guide = ("This is a very short scene. One or two changes is right. "
                 "Psychology beyond a sentence would be invention.")
    elif words < 150:
        guide = "A short scene. Two or three changes, briefly reasoned."
    else:
        guide = "A full scene. Develop the changes and what drives them."

    user = f"""\
Describe scene {scene.scene_id}. It is {words} words long. {guide}

THE SCENE — your only source
{text[:14000]}

THE TWO NEIGHBOURING SCENES, so you know who people are. Do not describe them.
{neighbours[:6000]}

SCHEMA
{json.dumps(v1_schema(scene), indent=1)}

Now describe scene {scene.scene_id}, and only that scene.
"""
    return V1_SYSTEM, user, v1_schema(scene)


# --------------------------------------------------------------------------
# V2 — two passes: structure from the scene alone, then mind from the context
#
# V1 established that cutting context anchors a node to its scene. But a scene
# read in isolation cannot say why a character conceals something, what they
# believe another believes, or what a silence costs — that information is not on
# the page, it accumulated across the scenes before it.
#
# So the two things are separated, because they want opposite context:
#
#   pass A   what is observably there   ->  the scene alone. Cheap, fast,
#                                           anchored, and V1 already measured it
#   pass B   what is going on in minds  ->  pass A's facts, plus the surrounding
#                                           scenes and what the characters have
#                                           been through
#
# Pass B is explicitly allowed to go beyond the observable — that is its job —
# but it must build on pass A's facts rather than replace them, and it must say
# which of its claims are inferences.
# --------------------------------------------------------------------------

MIND_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["scene_id", "minds", "connects_back", "sets_up"],
    "properties": {
        "scene_id": {"type": "string"},
        "minds": {"type": "array", "minItems": 1, "items": {
            "type": "object", "additionalProperties": False,
            "required": ["who", "wants", "feels", "shows", "basis"],
            "properties": {
                "who": {"type": "string"},
                "wants": {"type": "string",
                          "description": "What they are trying to get here."},
                "feels": {"type": "string",
                          "description": "What is actually going on in them."},
                "shows": {"type": "string",
                          "description": "What they let be seen. If it differs "
                                         "from `feels`, that gap is the scene."},
                "believes_about": {"type": "array", "items": {
                    "type": "object", "additionalProperties": False,
                    "required": ["other", "belief"],
                    "properties": {
                        "other": {"type": "string"},
                        "belief": {"type": "string"},
                        "wrong_because": {"type": "string",
                                          "description": "Where this belief is "
                                                         "mistaken, if it is."}}}},
                "basis": {"type": "string", "minLength": 30,
                          "description": "What in the scene or in what came "
                                         "before supports this reading."},
                "inferred": {"type": "boolean",
                             "description": "True if this goes beyond what is "
                                            "observable in the scene itself."}}}},
        "connects_back": {"type": "array", "items": {"type": "string"},
                          "description": "What earlier this depends on."},
        "sets_up": {"type": "array", "items": {"type": "string"},
                    "description": "What this makes possible or necessary later."},
        "dramatic_function": {"type": "string", "minLength": 40,
                              "description": "What this scene is doing in the "
                                             "story. Not what happens in it."},
    },
}

MIND_SYSTEM = """\
You are reading minds in a scene whose facts have already been established.

Someone else recorded what observably happens. You are not re-doing that and you
must not contradict it. Your job is the part that is not on the page: what each
person is trying to get, what is actually going on in them, what they let be
seen, and what they believe about each other — including where that belief is
wrong, because a mistaken belief is where drama comes from.

You have the scenes around this one. Use them. A character's guardedness here may
be the residue of something three scenes ago, and that is exactly the kind of
reading a scene taken alone cannot produce.

Two disciplines. First, every reading needs a basis: name what in this scene or
in what came before supports it. Second, mark as `inferred` anything that goes
beyond what is observable here — going beyond is your job, pretending you did not
is not.

If two people could swap their inner lives without the scene changing, you have
not read them, you have described a situation.

Return JSON conforming to the schema. No prose outside it."""


def v2_mind_prompt(scene, facts: dict, before: str, after: str) -> str:
    return f"""\
Read the minds in scene {scene.scene_id}.

THE FACTS, already established — do not contradict them
{json.dumps(facts, indent=1, ensure_ascii=False)}

THE SCENE ITSELF
{{scene_text}}

WHAT CAME IMMEDIATELY BEFORE
{before[:7000]}

WHAT COMES IMMEDIATELY AFTER — for what this scene sets up, not for hindsight
{after[:5000]}

SCHEMA
{json.dumps(MIND_SCHEMA, indent=1)}
"""


VARIANTS = {"v0": v0, "v1": v1}


# --------------------------------------------------------------------------
# Tier 1 — mechanical, gates the expensive tier
# --------------------------------------------------------------------------

STOP = set("the a an and or of to in is was on at it he she they her his with "
           "for that this but as from by up out into".split())


def _toks(s: str) -> set:
    return {w for w in re.findall(r"[a-z']{3,}", (s or "").lower()) if w not in STOP}


def _loose(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").lower()).strip()


def tier1(node: dict, scene, text: str) -> dict:
    """Cheap checks. Not a quality judgement — a floor."""
    if not node:
        return {"produced": False, "score": 0.0, "problems": ["no node"]}
    p = []
    own = text.lower()
    cues = {c.lower() for c in (scene.speakers or [])}

    names = [n for n in node.get("present") or [] if n]
    named_ok = sum(1 for n in names
                   if n.lower() in own or any(n.lower() in c or c in n.lower()
                                              for c in cues))
    if names and not named_ok:
        p.append(f"none of {names[:3]} appears in the scene or its cues")

    spans = [c.get("evidence", "") for c in node.get("what_changes") or []]
    long = [e for e in spans if len(e) >= 25]
    verbatim = sum(1 for e in long if _loose(e) in _loose(own))
    if long and not verbatim:
        p.append("no evidence span appears verbatim in the scene")

    noops = sum(1 for c in node.get("what_changes") or []
                if c.get("before") == c.get("after"))
    if noops:
        p.append(f"{noops} no-op change(s)")

    ev = _toks(" ".join(spans) + " " +
               " ".join((c.get("after") or "") for c in node.get("what_changes") or []))
    overlap = len(ev & _toks(text)) / len(ev) if ev else 0.0
    if overlap < 0.10:
        p.append(f"word overlap {overlap:.0%} — probably a different scene")

    return {"produced": True,
            "named_ok": f"{named_ok}/{len(names)}" if names else "0/0",
            "verbatim": f"{verbatim}/{len(long)}" if long else "0/0",
            "noops": noops, "overlap": round(overlap, 3),
            "words": len(json.dumps(node).split()),
            "scene_words": scene.word_count,
            "problems": p,
            "score": round(1.0 - 0.25 * len(p), 2)}


def run_v2(out: Path, ports: list[int], model: str, per_endpoint: int = 4) -> dict:
    """Two passes per scene: facts from the scene alone, then minds with context."""
    out.mkdir(parents=True, exist_ok=True)
    sw = Swarm(ports, model, per_endpoint)
    table = json.loads((ROOT / "reconstruct/runs/matrix/script_map.json").read_text())
    script = Path(table["source_file"]).read_text(errors="replace")
    _, scenes = sp.parse(script)
    by = {s.scene_id: s for s in scenes}
    order = [s.scene_id for s in scenes]

    def one(sid):
        sc = by[sid]
        text = script[sc.start_char:sc.end_char]
        i = order.index(sid)

        def span(j0, j1):
            out_ = ""
            for j in range(max(0, j0), min(len(scenes), j1)):
                n = scenes[j]
                out_ += (f"\n--- {n.scene_id} ({n.heading}) ---\n"
                         + script[n.start_char:n.end_char][:2200])
            return out_

        # pass A — V1 exactly: the scene, its two neighbours, nothing else
        system, user, schema = v1(sc, text, script, span(i - 1, i) + span(i + 1, i + 2))
        facts = sw.ask(system, user, schema, stage="v2-facts", tag=sid, max_tokens=9000)
        if not facts:
            return None
        facts["scene_id"] = sid

        # pass B — minds, given the facts and a wider run of scenes
        mind = sw.ask(MIND_SYSTEM,
                      v2_mind_prompt(sc, facts, span(i - 3, i), span(i + 1, i + 2))
                      .replace("{scene_text}", text[:12000]),
                      MIND_SCHEMA, stage="v2-minds", tag=sid, max_tokens=9000)
        if mind:
            mind["scene_id"] = sid
            facts["minds"] = mind.get("minds")
            facts["connects_back"] = mind.get("connects_back")
            facts["sets_up"] = mind.get("sets_up")
            facts["dramatic_function"] = mind.get("dramatic_function")
        return facts

    nodes = sw.map(one, SAMPLE, stage="v2", label=lambda s: s)
    results = {}
    for sid, nd in zip(SAMPLE, nodes):
        sc = by[sid]
        r = tier1(nd, sc, script[sc.start_char:sc.end_char])
        r["minds"] = len((nd or {}).get("minds") or [])
        r["inferred"] = sum(1 for m in (nd or {}).get("minds") or []
                            if m.get("inferred"))
        results[sid] = r
        if nd:
            (out / f"{sid}.json").write_text(json.dumps(nd, indent=1, ensure_ascii=False))

    ok = [r for r in results.values() if r.get("produced")]
    summary = {"variant": "v2", "n": len(SAMPLE), "produced": len(ok),
               "mean_tier1": round(sum(r["score"] for r in ok) / len(ok), 3) if ok else 0,
               "mean_overlap": round(sum(r["overlap"] for r in ok) / len(ok), 3) if ok else 0,
               "clean": sum(1 for r in ok if not r["problems"]),
               "verbatim_ok": sum(1 for r in ok if r["verbatim"] != "0/0"
                                  and not r["verbatim"].startswith("0/")),
               "mean_words": round(sum(r["words"] for r in ok) / len(ok)) if ok else 0,
               "mean_minds": round(sum(r["minds"] for r in ok) / len(ok), 1) if ok else 0,
               "usage": {k: sw.summary("v2-facts")[k] + sw.summary("v2-minds")[k]
                         for k in ("calls", "ok", "tok_in", "tok_out", "model_secs")},
               "per_scene": results}
    (out / "_tier1.json").write_text(json.dumps(summary, indent=1))
    return summary


def run_variant(name: str, out: Path, ports: list[int], model: str,
                per_endpoint: int = 4) -> dict:
    fn = VARIANTS[name]
    out.mkdir(parents=True, exist_ok=True)
    sw = Swarm(ports, model, per_endpoint)

    table = json.loads((ROOT / "reconstruct/runs/matrix/script_map.json").read_text())
    script = Path(table["source_file"]).read_text(errors="replace")
    _, scenes = sp.parse(script)
    by = {s.scene_id: s for s in scenes}
    order = [s.scene_id for s in scenes]

    def one(sid):
        sc = by[sid]
        text = script[sc.start_char:sc.end_char]
        if not text.strip():
            raise ValueError(f"{sid}: empty scene text")
        i = order.index(sid)
        nb = ""
        for j in (i - 1, i + 1):
            if 0 <= j < len(scenes):
                n = scenes[j]
                nb += (f"\n--- {n.scene_id} ({n.heading}) ---\n"
                       + script[n.start_char:n.end_char][:2500])
        system, user, schema = fn(sc, text, script, nb)
        d = sw.ask(system, user, schema, stage=name, tag=sid, max_tokens=9000)
        if d:
            d["scene_id"] = sid
        return d

    nodes = sw.map(one, SAMPLE, stage=name, label=lambda s: s)
    results = {}
    for sid, nd in zip(SAMPLE, nodes):
        sc = by[sid]
        results[sid] = tier1(nd, sc, script[sc.start_char:sc.end_char])
        if nd:
            (out / f"{sid}.json").write_text(json.dumps(nd, indent=1, ensure_ascii=False))

    ok = [r for r in results.values() if r.get("produced")]
    summary = {
        "variant": name, "n": len(SAMPLE), "produced": len(ok),
        "mean_tier1": round(sum(r["score"] for r in ok) / len(ok), 3) if ok else 0,
        "mean_overlap": round(sum(r["overlap"] for r in ok) / len(ok), 3) if ok else 0,
        "clean": sum(1 for r in ok if not r["problems"]),
        "verbatim_ok": sum(1 for r in ok
                           if r["verbatim"] != "0/0" and not r["verbatim"].startswith("0/")),
        "mean_words": round(sum(r["words"] for r in ok) / len(ok)) if ok else 0,
        "usage": sw.summary(name),
        "per_scene": results,
    }
    (out / "_tier1.json").write_text(json.dumps(summary, indent=1))
    return summary


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", required=True, choices=list(VARIANTS) + ["v2"])
    ap.add_argument("--out", required=True)
    ap.add_argument("--ports", default="8100,8101,8102,8103,8104,8105,8106,8107")
    ap.add_argument("--model", default="qwen3.8-27b")
    ap.add_argument("--per-endpoint", type=int, default=4)
    a = ap.parse_args()

    ports = [int(p) for p in a.ports.split(",")]
    s = (run_v2(Path(a.out), ports, a.model, a.per_endpoint) if a.variant == "v2"
         else run_variant(a.variant, Path(a.out), ports, a.model, a.per_endpoint))
    print(f"\n  {s['variant']}: {s['produced']}/{s['n']} produced · "
          f"tier1 {s['mean_tier1']} · clean {s['clean']}/{s['produced']} · "
          f"overlap {s['mean_overlap']:.0%} · "
          f"verbatim ok {s['verbatim_ok']}/{s['produced']} · "
          f"{s['mean_words']} words/node")
    for sid, r in s["per_scene"].items():
        if r.get("problems"):
            print(f"    {sid} ({r.get('scene_words')}w): {'; '.join(r['problems'])}")
