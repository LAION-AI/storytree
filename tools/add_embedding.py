"""Score an existing story on the plot-embedding coordinate system.

    python3 tools/add_embedding.py runs/api-grok

Reads the finished artifacts, scores all 52 genres and 24 dimensions, validates
the result, and patches it into the story root as `plot_embedding`.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import requests

from narrativeforge import plotembedding as pe
from narrativeforge.backends.hyprlab import load_env
from narrativeforge.pipeline import Project

load_env(Path(__file__).resolve().parent.parent / ".env")
KEY = os.environ["HYPRLAB_API_KEY"]
BASE = os.environ.get("HYPRLAB_BASE_URL", "https://api.hyprlab.io/v1")

SYSTEM = ("You score finished works on a fixed coordinate system. You are an analyst, not "
          "an advocate: the work is what it is, and inflating a score to flatter it "
          "destroys the only thing the coordinate system is good for.")


def build_prompt(project: Project) -> str:
    docs = project.load_all()
    root = docs["story_root"] or {}
    expose = docs["expose"] or {}
    plots = (docs["plots"] or {}).get("plots", [])
    scenes = (docs["scenes"] or {}).get("scenes", {})
    prose = project.load_prose()

    # One representative page so the scorer sees the actual register.
    sample_id = sorted(prose)[len(prose) // 2] if prose else None
    sample = prose.get(sample_id, "")[:2600] if sample_id else "(no pages)"

    synopsis = " ".join(v.get("text", "") for v in expose.get("synopsis", {}).values())

    return f"""\
Score this finished work on the plot-embedding coordinate system.

TITLE: {root.get('title')}
FORM: {root.get('form')} · {root.get('genre_primary')} · audience {root.get('audience', {}).get('age_band')}
LOGLINE: {root.get('logline')}

RULES OF THE WORLD
{json.dumps(root.get('setting', {}).get('rules_of_the_world', []), indent=1)}

STYLE
{json.dumps(root.get('style', {}), indent=1)}

FULL-SPOILER SYNOPSIS
{synopsis}

PLOTS
{json.dumps([{k: p.get(k) for k in ('plot_id', 'type', 'title', 'goal', 'stakes', 'outcome', 'thematic_function')} for p in plots], indent=1)}

SCENE FUNCTIONS AND TENSION CURVE
{json.dumps([{'scene': s, 'fn': v.get('dramatic_function'), 'tension': [v.get('tension_in'), v.get('tension_out')]} for s, v in sorted(scenes.items())], indent=1)}

A REPRESENTATIVE PAGE ({sample_id})
{sample}

═══════════════════════════════════════════════════════════════════════════

{pe.rubric_text()}

Score every key. Most keys in most works are 0 — a work is not "a little bit
cyberpunk" because it contains a machine. Reserve 4 and 5 for what actually
drives acts. `dominant` lists exactly those genres scoring 4 or 5, strongest
first. Any score of 1 or more needs `evidence`: at most 25 words naming the
concrete thing in THIS work that earns it.

Return one JSON document conforming to the schema.

SCHEMA
{json.dumps(pe.PLOT_EMBEDDING_SCHEMA, indent=1)}
"""


def main():
    project = Project(Path(sys.argv[1] if len(sys.argv) > 1 else "runs/api-grok"))
    prompt = build_prompt(project)
    print(f"prompt {len(prompt):,} chars — scoring …", flush=True)

    t0 = time.time()
    r = requests.post(f"{BASE}/chat/completions",
                      headers={"Authorization": f"Bearer {KEY}"},
                      json={"model": "grok-4.6",
                            "messages": [{"role": "system", "content": SYSTEM},
                                         {"role": "user", "content": prompt}],
                            "response_format": {"type": "json_schema",
                                                "json_schema": {"name": "plot_embedding",
                                                                "strict": False,
                                                                "schema": pe.PLOT_EMBEDDING_SCHEMA}},
                            "max_completion_tokens": 40000, "temperature": 0.3,
                            "reasoning_effort": "high"},
                      timeout=2400)
    if r.status_code != 200:
        raise SystemExit(f"HTTP {r.status_code}: {r.text[:600]}")
    d = r.json()
    emb = json.loads(d["choices"][0]["message"]["content"])
    u = d.get("usage", {})
    cost = (u.get("prompt_tokens", 0)/1e6)*1.8 + \
           ((u.get("completion_tokens", 0) +
             (u.get("completion_tokens_details") or {}).get("reasoning_tokens", 0))/1e6)*5.4
    print(f"scored in {time.time()-t0:.0f}s · ${cost:.3f}")

    for fix in pe.normalize_embedding(emb):
        print(f"  normalised {fix}")
    errors = pe.validate_embedding(emb)
    if errors:
        print(f"\n{len(errors)} validation issue(s):")
        for e in errors[:12]:
            print("  -", e)
    else:
        print("validation: clean")

    prof = pe.profile(emb)
    print(f"\nage rating   : {prof['age_rating']}")
    print(f"genre mass   : {prof['genre_mass']} across {prof['nonzero_genres']} non-zero genres")
    print("dominant     :")
    for k, v in prof["dominant_genres"]:
        ev = emb["genres"][k].get("evidence", "")
        print(f"  {v}  {k:<24} {ev}")
    print("salient dimensions:")
    for k, v in prof["salient_dimensions"]:
        print(f"  {v}  {k:<26} {emb['dimensions'][k].get('evidence','')[:70]}")

    root = project.load("story_root")
    root["plot_embedding"] = emb
    project.save("story_root", root)
    print(f"\npatched into {project.artifact_path('story_root')}")
    print(f"vector: {pe.vector(emb)}")


if __name__ == "__main__":
    main()
