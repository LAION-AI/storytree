#!/usr/bin/env python3
"""Entity profiles: research -> profile -> leak/quality gate.

Trial build over the first --max-scenes scenes. Per prominent entity three
phases: a researcher walks every scene the entity touches collecting facts
with pointers; a writer compiles the standard profile from that research
ALONE; an audit counts verbatim source runs and the profiles are judged on
groundedness, concreteness, completeness, voice and leak-freedom.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, "/home/deployer/laion/project-alexandria/screenplay/src")
from screenplay_ku.client import EndpointPool, run_parallel  # noqa: E402
from screenplay_ku.kuschema import grammar_safe  # noqa: E402


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

PERSON_FIELDS = ["name", "kind", "age_and_gender", "appearance", "clothing",
                 "life_situation", "key_relationships",
                 "personality_big_five", "coping_with_problems",
                 "dreams_and_goals_short", "goals_long_term", "fears",
                 "wanted_image_and_roles", "comfortable_feelings_vs_shadow",
                 "intellect_and_skills", "interests_hobbies",
                 "background_story", "typical_sentences_style",
                 "secrets_never_said"]
THING_FIELDS = ["name", "kind", "appearance", "ownership_and_history",
                "role_in_story", "current_state_physical_social",
                "what_is_known_about_it"]

SYSTEM = ("You build character and world profiles for a screenwriting system "
          "from finished scene analyses and screenplay excerpts. Third person "
          "only; never quote the source -- paraphrase or invent in-style; "
          "every factual claim cites the scene it rests on. Valid JSON only.")

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenes-dir", default="runs/scenes_ornith_v5")
    ap.add_argument("--out", required=True)
    ap.add_argument("--source",
                    default="distill/runs/matrix/script.normalized.txt")
    ap.add_argument("--max-scenes", type=int, default=30,
                    help="0 = all scenes")
    ap.add_argument("--top", type=int, default=8)
    ap.add_argument("--ports", default="8110,8111")
    ap.add_argument("--model", default="ornith-1.5-397b")
    a = ap.parse_args()

    ml = _load("_ml", str(Path(__file__).resolve().parent / "meta_layer.py"))
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    files = sorted(Path(a.scenes_dir).glob("sc-*.json"))
    if a.max_scenes:
        files = files[:a.max_scenes]
    nodes = [json.loads(p.read_text(encoding="utf-8")) for p in files]
    print("trial scope: {} scenes".format(len(nodes)), flush=True)

    counts = Counter()
    canon_all: dict = {}
    for n in nodes:
        names = ([str(x) for x in (n.get("present") or [])]
                 + [str(c.get("who")) for c in (n.get("what_changes") or [])
                    if isinstance(c, dict)]
                 + [str(m.get("who")) for m in (n.get("minds") or [])
                    if isinstance(m, dict)])
        # Fold case variants ACROSS nodes: NEO and Neo are one entity.
        for x in names:
            key = re.sub(r"[^a-z0-9 ]", "", x.casefold()).strip()
            if len(key) > 2:
                disp = canon_all.setdefault(key, x)
                counts[disp] += 1
    loc_counts = Counter(str(n.get("location")) for n in nodes
                         if n.get("location"))
    targets = [t for t, _ in counts.most_common(a.top)]
    targets += [t for t, _ in loc_counts.most_common(2)][
        :max(0, a.top - len(targets))]
    print("entities:", targets, flush=True)

    pool = EndpointPool([int(p) for p in a.ports.split(",")], a.model,
                        temperature=0.4, max_tokens=8000, timeout=1800)

    def material_for(target):
        mats = []
        words = {w for w in re.findall(r"[a-z0-9']+", target.casefold())
                 if len(w) > 2}
        for n in nodes:
            hay = json.dumps(n, ensure_ascii=False).casefold()
            if words and any(w in hay for w in words):
                mats.append({
                    "scene_id": n.get("scene_id"),
                    "location": n.get("location"),
                    "present": (n.get("present") or [])[:12],
                    "changes": [{k: c.get(k) for k in
                                 ("who", "axis", "before", "after")}
                                for c in (n.get("what_changes") or [])
                                if isinstance(c, dict) and c.get("who")][:12],
                    "minds": [{"who": m.get("who"),
                               **{k: str(v)[:140] for k, v in m.items()
                                  if k != "who"}}
                              for m in (n.get("minds") or [])[:8]]})
        return mats

    def research(target):
        mats = material_for(target)
        r = pool.call(SYSTEM, (
            "PHASE 1 - RESEARCH. Walk these scenes and collect everything "
            "actually recorded about '{}': traits shown, appearance, "
            "relationships, goals, fears, habits, history hints. Only what "
            "the scenes support; each fact carries its scene_id.\n\n{}"
        ).format(target, json.dumps(mats, ensure_ascii=False,
                                    indent=1)[:50000]),
            schema=grammar_safe({
                "type": "object",
                "properties": {"facts": {"type": "array", "minItems": 5,
                                         "items": {"type": "object",
                                                   "properties": {
                                                       "scene_id": {
                                                           "type": "string"},
                                                       "fact": {
                                                           "type": "string",
                                                           "minLength": 15}},
                                                   "required": ["scene_id",
                                                                "fact"],
                                                   "additionalProperties":
                                                       False}}},
                "required": ["facts"], "additionalProperties": False}))
        return target, json.loads(r.text)["facts"], mats

    profiles = []
    for res in run_parallel([(t,) for t in targets],
                            lambda t: research(t[0]), max_workers=2):
        if isinstance(res, Exception):
            print("  research FAILED:", str(res)[:100], flush=True)
            continue
        target, facts, mats = res
        is_loc = target in {str(n.get("location")) for n in nodes}
        fields = THING_FIELDS if is_loc else PERSON_FIELDS
        prof_schema = grammar_safe({
            "type": "object",
            "properties": {f: {"type": "string", "minLength": 20}
                           for f in fields},
            "evidence": {"type": "array", "minItems": 5, "items": {
                "type": "object",
                "properties": {"scene_id": {"type": "string"},
                               "note": {"type": "string", "minLength": 15}},
                "required": ["scene_id", "note"],
                "additionalProperties": False}},
            "required": fields + ["evidence"],
            "additionalProperties": False})
        prompt = "\n\n".join([
            "PHASE 2 - PROFILE. Compile the standard profile of '{}' "
            "({}). Use ONLY the phase-1 research; invent nothing factual. "
            "Third person; concrete; no category words; typical sentences "
            "are paraphrased or invented in the voice's style, never "
            "quoted. Every evidence entry cites a real scene id from the "
            "research.".format(target,
                               "location" if is_loc else "entity"),
            "FIELDS:\n" + ", ".join(fields),
            "PHASE-1 RESEARCH:\n" + json.dumps(facts, ensure_ascii=False,
                                               indent=1)[:40000]])
        try:
            prof = json.loads(pool.call(SYSTEM, prompt,
                                        schema=prof_schema).text)
        except Exception as e:
            print("  profile FAILED {}:".format(target), str(e)[:90])
            continue
        prof["_research_facts"] = len(facts)
        prof["_scenes_touched"] = len(mats)
        profiles.append(prof)
        print("  {}: ok ({} facts)".format(target, len(facts)), flush=True)

    import verbatim as V
    index = V.SourceIndex(Path(a.source).read_text(encoding="utf-8",
                                                   errors="ignore"))
    leaks = sum(1 for p in profiles for _p, rr in V.scan_node(p, index)
                if rr.kind == "exact")

    scores = {}
    if profiles:
        E = ("E1_grounded", "E2_concrete", "E3_complete", "E4_voice",
             "E5_leakfree")
        jprompt = "\n\n".join([
            "Score these ENTITY PROFILES: E1 grounded (claims traceable to "
            "cited scenes), E2 concrete/specific (no generic filler), E3 "
            "complete against recorded material, E4 voice authentic, E5 "
            "leak-free. Integers 1-5 with brief justification.",
            json.dumps(profiles, ensure_ascii=False, indent=1)[:60000]])
        jd = json.loads(pool.call(SYSTEM, jprompt, schema=grammar_safe({
            "type": "object",
            "properties": {**{d: {"type": "integer", "enum": [1, 2, 3, 4, 5]}
                              for d in E},
                           "commentary": {"type": "string"}},
            "required": list(E) + ["commentary"],
            "additionalProperties": False})).text)
        scores = {d: jd[d] for d in E}

    (out / "profiles.json").write_text(json.dumps(
        profiles, indent=1, ensure_ascii=False), encoding="utf-8")
    (out / "protocol.json").write_text(json.dumps({
        "trial_scenes": len(nodes), "entities": len(profiles),
        "verbatim_exact_runs": leaks, "judge_scores": scores,
        "gate": ("PASS" if scores and min(scores.values()) >= 3
                 else "FAIL" if scores else "NOT-JUDGED"),
    }, indent=1), encoding="utf-8")
    print("done: {} profiles | leaks {} | judge {}".format(
        len(profiles), leaks, scores), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


