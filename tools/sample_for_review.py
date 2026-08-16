"""Pull a reviewable sample out of a run: N reasoning traces and N outputs.

    python3 tools/sample_for_review.py reconstruct/runs/matrix --n 5 --out /tmp/sample.json

Sampling is deterministic given a seed so the same review can be repeated, and
it spreads across the run rather than taking the first N — the opening of a
story is not representative of its middle.

Only derived material is emitted. Where a project references a source script,
the script's own text is never included; the scene nodes describe it in the
pipeline's own words, which is what is being judged anyway.
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path


def _load(p: Path):
    return json.loads(p.read_text()) if p.exists() else None


def sample(project: Path, n: int = 5, seed: int = 7) -> dict:
    rng = random.Random(seed)
    art = project / "artifacts"
    tdir = project / "transitions"

    # ---- reasoning traces ----
    traces = []
    files = sorted(tdir.glob("*.json")) if tdir.exists() else []
    picked = files if len(files) <= n else [files[round(i * (len(files) - 1) / (n - 1))]
                                            for i in range(n)]
    for f in picked:
        doc = json.loads(f.read_text())
        traces.append({"node": f.stem, "transition": doc})

    # ---- outputs, spread across layers ----
    outputs = []
    root = _load(art / "story_root.json")
    if root:
        outputs.append({"kind": "story_root", "id": "story_root", "doc": {
            k: root.get(k) for k in
            ("title", "logline", "premise", "genre_primary", "audience", "setting",
             "pov", "style", "state_dimensions", "constraints", "keep_in_mind")}})
    exp = _load(art / "expose.json")
    if exp:
        outputs.append({"kind": "expose", "id": "expose", "doc": exp})
    plots = (_load(art / "plots.json") or {}).get("plots", [])
    if plots:
        outputs.append({"kind": "plot", "id": plots[0].get("plot_id"), "doc": plots[0]})
        if len(plots) > 1:
            outputs.append({"kind": "plot", "id": plots[-1].get("plot_id"), "doc": plots[-1]})
    ents = (_load(art / "entities.json") or {}).get("entities", {})
    majors = [e for e in ents.values() if e.get("salience") == "major"] or list(ents.values())
    if majors:
        outputs.append({"kind": "entity", "id": majors[0].get("entity_id"), "doc": majors[0]})
    events = (_load(art / "events.json") or {}).get("events", {})
    if events:
        key = sorted(events)[len(events) // 2]
        outputs.append({"kind": "event", "id": key, "doc": events[key]})
    scenes = (_load(art / "scenes.json") or {}).get("scenes", {})
    if scenes:
        key = sorted(scenes)[len(scenes) // 2]
        outputs.append({"kind": "scene", "id": key, "doc": scenes[key]})

    if len(outputs) > n:
        keep = [outputs[0]] + rng.sample(outputs[1:], n - 1)
        outputs = sorted(keep, key=lambda o: outputs.index(o))

    return {
        "project": str(project),
        "counts": {"plots": len(plots), "entities": len(ents),
                   "events": len(events), "scenes": len(scenes),
                   "transitions_available": len(files)},
        "traces": traces,
        "outputs": outputs,
    }


REVIEW_RUBRIC = """\
You are reviewing machine-generated narrative artifacts. Two kinds:

  TRACES  — reasoning transitions: the deliberate argument a model wrote to get
            from everything established so far to the next node of a story graph.
  OUTPUTS — the nodes themselves: story roots, exposés, plots, entity dossiers,
            events, scene definitions.

Judge each on these dimensions, 0-100, and say what the score is FOR:

  factuality        Internal accuracy. Does it contradict the material it claims
                    to build on? Are cited facts real facts of this story? For a
                    reconstruction, does it describe the source correctly?
  emotional_intel   Is the psychology specific, plausible and non-generic? Do
                    characters want incompatible things? Is the felt/expressed
                    gap real? Is the theory of mind actually second and third
                    order, or first order wearing a costume?
  dramatic_quality  Does this create or sustain pressure? Is conflict rising
                    rather than static? Would a scene built from this be worth
                    watching, or is it competent and inert?
  plausibility      Coherence against everything else knowable — the world's own
                    rules, the characters as established, ordinary human
                    behaviour, and the genre's logic.
  specificity       Could any sentence of this appear in a different story? The
                    more portable the prose, the lower the score.
  craft_awareness   Does it show real understanding of dramatic construction, or
                    does it recite craft vocabulary without applying it?

Then, overall:
  - `verdict`: one of "excellent", "good", "serviceable", "thin", "bad"
  - `strongest`: the single most impressive thing, quoted briefly
  - `weakest`: the single worst problem, quoted briefly
  - `tell`: if you can see a specific machine-generation tell — a habit no human
            writer would have — name it. If you cannot, say so plainly.
  - `would_a_human_writer_accept_this`: true/false, and one sentence of why

Be a hard marker. These are not being graded on effort. Score 90+ only for work
you would be pleased to have written yourself; score below 40 for work that
would need to be thrown away. Inflated scores make the whole exercise useless.
"""
