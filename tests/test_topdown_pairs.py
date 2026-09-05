#!/usr/bin/env python3
"""Self-tests for Phase 0 pair reconstruction (top-down plan, T9 pairs).

Run with:  python3 tests/test_topdown_pairs.py

Builds a synthetic two-event / five-scene tree in a temp dir and asserts
the data contract from docs/16-topdown-generation-plan.md section 7:
one pair per scene, +-2 neighbour window, blind rule (no scene prose in
the input), by-reference targets by default, prose only with
--inline-prose, budgets respected, incomplete trees flagged unusable.
"""

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "reasoning_traces"))

import topdown_pairs as T  # noqa: E402

PASS, FAIL = [], []


def check(name, condition, detail=""):
    (PASS if condition else FAIL).append(name)
    print("  {:<62} {}".format(name, "ok" if condition else "FAIL " + detail))


def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")


def fixture_tree(base, slug="film__abc123", complete=True, prose=False):
    sdir = Path(base) / slug
    scenes = []
    for i in range(1, 6):
        sid = "sc-%03d" % i
        node = {
            "scene_id": sid,
            "location": "ROOM %d" % i,
            "present": ["ANA", "BEN"] if i % 2 else ["ANA"],
            "summary": "Scene %d happens: Ana confronts Ben about the missing key." % i,
            "what_changes": [{"who": "ANA", "axis": "knowledge",
                              "before": "unsure", "after": "certain"}],
            "dramatic_function": "raises the stakes",
        }
        scenes.append(node)
        write_json(sdir / "scenes" / (sid + ".json"), node)
    write_json(sdir / "events" / "events.json", {"events": [
        {"event_id": "ev-001", "scene_ids": ["sc-001", "sc-002", "sc-003"],
         "title": "The key goes missing", "summary": "The key vanishes.",
         "action": "The key vanishes from the room."},
        {"event_id": "ev-002", "scene_ids": ["sc-004", "sc-005"],
         "title": "The search", "summary": "They search the house.",
         "action": "They search the house room by room."},
    ]})
    if complete:
        write_json(sdir / "root" / "story_root.json",
                   {"logline": "A key goes missing.", "premise": "Two people search."})
        write_json(sdir / "expose" / "expose.json",
                   {"ending_first": "They find it.", "synopsis": {"s01": "It vanishes."}})
        write_json(sdir / "meta" / "meta.json",
                   {"themes": {"central_dilemma": {}, "big_questions": []}})
        write_json(sdir / "entities" / "profiles.json",
                   [{"name": "ANA", "type": "character", "profile": "Careful keeper.",
                     "evidence": [{"scene_id": "sc-001"}, {"scene_id": "sc-004"}]}])
        write_json(sdir / "plots" / "plots.json", {"plots": {
            "search": {"definition": {"spine": "Find the key.", "agent": "ANA",
                                      "goal": "the key", "outcome": "found"},
                       "chain": [{"event_id": "ev-001"}, {"event_id": "ev-002"}]}}})
    if prose:
        write_json(sdir / "scenes_fulltext.json",
                   {"sc-%03d" % i: "ANA\nWhere is the key tonight, Ben? (scene %d)" % i
                    for i in range(1, 6)})
    return str(base), slug


def main():
    with tempfile.TemporaryDirectory() as tmp:
        trees, slug = fixture_tree(tmp)

        pairs = list(T.build_pairs_for_slug(trees, slug))
        check("one pair per scene", len(pairs) == 5, str(len(pairs)))
        check("tids unique", len({p["tid"] for p in pairs}) == 5)
        check("all usable when tree complete", all(p["usable"] for p in pairs))

        first, mid, last = (p["input"] for p in (pairs[0], pairs[2], pairs[4]))
        check("first scene: 0 before, 2 after",
              first["neighbours"]["before"] == [] and len(first["neighbours"]["after"]) == 2)
        check("middle scene: 2 before, 2 after",
              len(mid["neighbours"]["before"]) == 2 and len(mid["neighbours"]["after"]) == 2)
        check("last scene: 2 before, 0 after",
              len(last["neighbours"]["before"]) == 2 and len(last["neighbours"]["after"]) == 0)
        check("neighbour order preserved",
              [n["scene_id"] for n in mid["neighbours"]["before"]] == ["sc-001", "sc-002"])

        blob = json.dumps(pairs)
        check("blind rule: no full-text key in input", "_scene_fulltext" not in blob)
        check("targets are by reference by default",
              all(set(p["target"]) == {"slug", "scene_id"} for p in pairs))

        inline = list(T.build_pairs_for_slug(trees, slug, inline_prose=True))
        check("inline prose requested but absent -> unusable",
              all(not p["usable"] for p in inline))

        trees2, slug2 = fixture_tree(tmp, slug="other__def456", prose=True)
        inline2 = {p["scene_id"]: p for p in T.build_pairs_for_slug(trees2, slug2, inline_prose=True)}
        check("inline prose present -> usable + carried",
              inline2["sc-001"]["usable"] and "key tonight" in inline2["sc-001"]["target"]["prose"])
        blob2 = json.dumps([p["input"] for p in inline2.values()])
        check("blind rule holds for inputs even with --inline-prose",
              "key tonight" not in blob2)

        # budgets: oversized root must be cut and marked
        big = "x" * (T.BUDGETS["root"] + 500)
        write_json(Path(trees) / slug / "root" / "story_root.json", {"logline": big})
        cut = list(T.build_pairs_for_slug(trees, slug))[0]["input"]["tree_above"]["root"]
        check("root budget enforced + marked",
              len(cut) <= T.BUDGETS["root"] + 60 and "truncated" in cut, str(len(cut)))

        # incomplete tree: pairs still emitted, flagged unusable
        trees3, slug3 = fixture_tree(tmp, slug="bare__ghi789", complete=False)
        bare = list(T.build_pairs_for_slug(trees3, slug3))
        check("incomplete tree still yields pairs", len(bare) == 5)
        check("incomplete tree flagged unusable with reason",
              all(not p["usable"] and p["skip_reason"] for p in bare))

        # split is by film and deterministic
        train, eval_ = T.make_split(["a", "b", "c", "d"], 0.25, seed=7)
        check("split covers all films once",
              sorted(train + eval_) == ["a", "b", "c", "d"] and len(eval_) == 1)
        check("split deterministic",
              T.make_split(["a", "b", "c", "d"], 0.25, seed=7) == (train, eval_))

    # HF layout: one dict per film, scenes WITH _scene_fulltext + full script
    film = {
        "slug": "hf__test",
        "original_script": "ANA\nWhere is the key tonight, Ben? This is the full prose.",
        "layers": {
            "scenes": [
                    {"scene_id": "sc-001", "location": "HALL",
                     "present": ["ANA"], "summary": "Ana enters.",
                     "what_changes": [], "_scene_fulltext": "ANA\nWhere is the key tonight?"},
                    {"scene_id": "sc-002", "location": "ROOM",
                     "present": ["ANA", "BEN"], "summary": "Ben answers.",
                     "what_changes": [{"who": "BEN", "axis": "knowledge",
                                       "before": "silent", "after": "speaking"}]},
            ],
            "events": [{"event_id": "ev-001", "scene_ids": ["sc-001", "sc-002"],
                        "title": "Ask", "summary": "She asks, he answers.",
                        "action": "She asks. He answers."}],
            "root": {"logline": "A key."},
            "expose": {"ending_first": "Found."},
            "entities": [{"name": "ANA", "evidence": [{"scene_id": "sc-001"}]}],
            "plots": {"search": {"definition": {"summary": "Find it."},
                                 "chain": [{"event_id": "ev-001"}]}},
        },
    }
    hf_pairs = list(T.build_pairs_from_hf(film))
    check("hf: one pair per scene", len(hf_pairs) == 2, str(len(hf_pairs)))
    check("hf: usable", all(p["usable"] for p in hf_pairs))
    check("hf: original_script never in input",
          "Where is the key tonight, Ben? This is the full prose." not in json.dumps(hf_pairs))
    check("hf: _scene_fulltext stripped from input",
          "_scene_fulltext" not in json.dumps([p["input"] for p in hf_pairs]))
    try:
        list(T.build_pairs_from_hf(film, inline_prose=True))
        check("hf: --inline-prose refused", False, "no SystemExit")
    except SystemExit:
        check("hf: --inline-prose refused", True)

    print("\n%d passed, %d failed" % (len(PASS), len(FAIL)))
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
