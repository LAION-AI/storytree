"""Tests for the screenplay parser and the anchor round trip.

Run:  python3 tests/test_screenplay.py

The round trip is the one that matters: if the anchor table cannot recover each
scene's exact text from the file alone, every scene node downstream is bound to
a passage nobody can locate again, and the whole reconstruction is worthless.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scriptforge import screenplay as sp  # noqa: E402

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(f"  {'ok  ' if cond else 'FAIL'}  {name}{'' if cond else '  <- ' + str(detail)}")


SAMPLE = (ROOT / "samples" / "tideline.fountain").read_text()


def test_normalization():
    print("\nnormalization")
    messy = "﻿A\r\nB\r\n\n\n\n\tC   \n\n\n"
    n = sp.normalize(messy)
    check("strips BOM", not n.startswith("﻿"))
    check("CRLF becomes LF", "\r" not in n)
    check("tabs become spaces", "\t" not in n)
    check("collapses 3+ blank lines", "\n\n\n" not in n, repr(n))
    check("ends with exactly one newline", n.endswith("\n") and not n.endswith("\n\n"))
    check("is idempotent", sp.normalize(n) == n)


def test_parse():
    print("\nparsing")
    text, scenes = sp.parse(SAMPLE)
    check("found every scene", len(scenes) == 5, f"{len(scenes)} scenes")
    ids = [s.scene_id for s in scenes]
    check("ids are sequential", ids == [f"sc-{i:03d}" for i in range(1, len(scenes) + 1)], ids)

    kinds = [s.kind for s in scenes]
    check("recognises EXT", kinds[0] == "EXT", kinds)
    check("recognises INT", kinds[1] == "INT", kinds)
    check("recognises INT/EXT", any("/" in k for k in kinds), kinds)

    first = scenes[0]
    check("parses the location", first.location == "HARBOUR WALL", first.location)
    check("parses time of day", first.time_of_day == "PRE-DAWN", first.time_of_day)

    check("finds the speakers", "MAREN" in first.speakers, first.speakers)
    check("ignores CONT'D as a speaker",
          all("CONT'D" not in sp_ for s in scenes for sp_ in s.speakers),
          [s.speakers for s in scenes])
    check("measures a dialogue ratio", 0.1 < first.dialogue_ratio < 0.95, first.dialogue_ratio)

    # a transition line must not be swallowed into the next scene's body
    body2 = scenes[1].text(text)
    check("transition lines end a scene, not start one", not body2.lstrip().startswith("CUT TO"),
          body2[:40])
    # nor should the front matter become a scene
    check("front matter is not a scene", "Written by" not in scenes[0].text(text))


def test_anchors_and_roundtrip():
    print("\nanchors and round trip")
    text, scenes = sp.parse(SAMPLE)
    table = sp.anchor_table(text, scenes)

    check("every anchor is unique in the document",
          all(v["anchors_unique"] for v in table["scenes"].values()),
          [k for k, v in table["scenes"].items() if not v["anchors_unique"]])
    for sid, meta in table["scenes"].items():
        check(f"{sid}: head quote occurs exactly once", text.count(meta["start_quote"]) == 1)

    recovered = sp.split_by_anchors(text, table)
    check("recovers every scene", set(recovered) == {s.scene_id for s in scenes})
    exact = [s.scene_id for s in scenes
             if recovered[s.scene_id].strip() == s.text(text).strip()]
    check("round trip is exact for every scene", len(exact) == len(scenes),
          f"{len(exact)}/{len(scenes)} exact")

    check("coverage is high", table["coverage"] > 0.85, table["coverage"])
    problems = sp.verify(text, scenes, table)
    check("verify reports no problems", not problems, problems)

    # the anchors must survive re-normalization of a differently formatted file
    remangled = SAMPLE.replace("\n", "\r\n").replace("    ", "\t")
    text2, _ = sp.parse(remangled)
    rec2 = sp.split_by_anchors(text2, table)
    same = sum(1 for s in scenes if rec2[s.scene_id].strip() == recovered[s.scene_id].strip())
    check("anchors survive CRLF + tab remangling", same == len(scenes), f"{same}/{len(scenes)}")


def test_injected_faults():
    print("\ninjected faults (verify must catch these)")
    text, scenes = sp.parse(SAMPLE)

    table = sp.anchor_table(text, scenes)
    table["scenes"]["sc-002"]["start_quote"] = "a phrase that is nowhere in this file"
    rec = sp.split_by_anchors(text, table)
    check("a broken anchor falls back to the span rather than exploding",
          rec["sc-002"].strip().startswith("INT. HARBOUR STATION"), rec["sc-002"][:50])

    overlapping = [s for s in scenes]
    overlapping[1].start_char = overlapping[0].start_char  # force an overlap
    problems = sp.verify(text, overlapping, sp.anchor_table(text, overlapping))
    check("overlapping spans are reported", any("overlap" in p for p in problems), problems[:2])

    empty_text, empty_scenes = sp.parse("Just some prose with no slug lines at all.\n")
    check("a non-screenplay is reported, not silently accepted",
          any("no scenes found" in p for p in sp.verify(empty_text, empty_scenes, {"scenes": {}, "coverage": 0})),
          "")


def test_summary():
    print("\nsummary")
    text, scenes = sp.parse(SAMPLE)
    s = sp.summarize(scenes)
    check("counts scenes", s["scenes"] == 5, s["scenes"])
    check("estimates pages", s["estimated_pages_a4"] > 0, s)
    check("collects speakers", "MAREN" in s["distinct_speakers"] and "DEREK" in s["distinct_speakers"],
          s["distinct_speakers"])
    check("collects locations", any("HARBOUR" in loc for loc in s["locations"]), s["locations"])
    digest = sp.scene_digest(scenes)
    check("digest carries no script text",
          all("text" not in row for row in digest) and len(digest) == 5)


# ---------------------------------------------------------------- reverse ---

def test_blind_sighted_separation():
    """The one property the whole reconstruction rests on.

    If the finished passage reaches the blind transition call, the reasoning it
    produces is hindsight wearing the costume of deliberation, and the resulting
    corpus teaches a model to sound like it is deciding while copying.
    """
    print("\nblind / sighted separation")
    from scriptforge import reverse

    text, scenes = sp.parse(SAMPLE)
    table = sp.anchor_table(text, scenes)
    scene = scenes[1]                       # a dialogue-heavy scene
    body = scene.text(text)
    ctx = {"root": {"title": "x"}, "expose": {}, "plots": [], "entities": {},
           "prior": None, "live_state": {}}
    env = reverse.envelope(scene, len(scenes) - scene.index, len(scenes))

    blind = reverse.blind_transition_prompt("scene", scene.scene_id, ctx, env)
    sighted = reverse.scene_node_prompt(
        scene.scene_id, ctx, {"situation": "x"},
        dict(table["scenes"][scene.scene_id], scene_id=scene.scene_id), body)

    # no substantial run of the passage may appear in the blind prompt
    chunks = [body[i:i + 60] for i in range(0, max(len(body) - 60, 1), 40)]
    leaked = [c for c in chunks if c.strip() and c.strip() in blind]
    check("passage does not leak into the blind prompt", not leaked, leaked[:1])

    # nor may any line of dialogue
    dialogue = [ln.strip() for ln in body.split("\n")
                if ln.startswith("          ") and len(ln.strip()) > 12]
    check("no dialogue line leaks into the blind prompt",
          not [d for d in dialogue if d in blind], dialogue[:1])

    check("blind prompt carries the production envelope", "PRODUCTION ENVELOPE" in blind)
    check("envelope is shape only, never content",
          set(env) == {"position", "scenes_remaining_after_this", "setting",
                       "on_screen", "approximate_length_words", "dialogue_ratio", "note"},
          sorted(env))
    check("blind system prompt forbids hindsight",
          "you have not read the finished work" in reverse.BLIND_SYSTEM.lower())
    check("sighted prompt does carry the passage", body[:120].strip() in sighted)
    check("sighted prompt demands a divergence record", "divergence" in sighted)
    check("scene node schema requires the binding",
          "bound_scene_id" in reverse.SCENE_NODE_SCHEMA["properties"]["scene"]["required"])


def test_leakage_detector():
    print("\nhindsight leakage detector")
    from scriptforge.reconstruct import _leakage
    clean = {"situation": "She has not spoken to him since the crossing.",
             "decision": {"resolution": "He asks the question he has been avoiding."}}
    check("clean trace passes", not _leakage(clean), _leakage(clean))
    for phrase in ("the script has her refuse", "as it turns out he lied",
                   "we later learn the boat was empty"):
        check(f"catches {phrase!r}", bool(_leakage({"x": phrase})))



if __name__ == "__main__":
    test_normalization()
    test_parse()
    test_anchors_and_roundtrip()
    test_injected_faults()
    test_summary()
    test_blind_sighted_separation()
    test_leakage_detector()
    print(f"\n{'=' * 60}\n{len(PASS)} passed, {len(FAIL)} failed")
    if FAIL:
        print("failed: " + ", ".join(FAIL))
    raise SystemExit(1 if FAIL else 0)