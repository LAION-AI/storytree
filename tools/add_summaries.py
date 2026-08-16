"""Write the encyclopedia-style plot summaries into a finished project's exposé.

    python3 tools/add_summaries.py runs/bennington

New runs get these from the exposé stage directly. This backfills projects that
were generated before the fields existed, and it reads the finished scenes and
pages rather than the synopsis alone, so the summary describes the story that
actually got written rather than the one that was planned.
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
from narrativeforge.pipeline import Project
from narrativeforge.summaries import SUMMARY_SPEC

load_env(Path(__file__).resolve().parent.parent / ".env")
KEY = os.environ["HYPRLAB_API_KEY"]
BASE = os.environ.get("HYPRLAB_BASE_URL", "https://api.hyprlab.io/v1")

SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["plot_summary_short", "plot_summary_long"],
    "properties": {
        "plot_summary_short": {"type": "string"},
        "plot_summary_long": {"type": "string"},
    },
}

SYSTEM = (
    "You write plot summaries the way a good encyclopedia does: plainly, chronologically, "
    "completely, for a reader who knows nothing about the work and wants to understand it. "
    "You are informing, not selling. You never withhold an ending, never ask a rhetorical "
    "question, and never imitate the register of the work you are describing."
)


def build_prompt(project: Project) -> str:
    docs = project.load_all()
    root = docs["story_root"] or {}
    expose = docs["expose"] or {}
    plots = (docs["plots"] or {}).get("plots", [])
    ents = (docs["entities"] or {}).get("entities", {})
    events = (docs["events"] or {}).get("events", {})
    scenes = (docs["scenes"] or {}).get("scenes", {})

    cast = {k: {"name": v.get("canonical_name"), "type": v.get("type"),
                "salience": v.get("salience"), "arc": v.get("arc")}
            for k, v in ents.items() if v.get("salience") in ("major", "supporting")}
    chain = [{"id": k, "t": events[k]["story_time"].get("label"),
              "summary": events[k].get("summary")}
             for k in sorted(events, key=lambda x: events[x]["story_time"]["index"])]
    order = [{"scene": s, "fn": scenes[s].get("dramatic_function")}
             for s in sorted(scenes, key=lambda x: scenes[x].get("discourse_index", 0))]

    return f"""\
Write the two plot summaries for this finished work.

TITLE: {root.get('title')}   ({root.get('form')}, {root.get('genre_primary')})
LOGLINE: {root.get('logline')}
SETTING: {root.get('setting', {}).get('period')} — {', '.join(root.get('setting', {}).get('places', []))}

RULES OF THE WORLD (explain one in passing only where the plot needs it)
{json.dumps(root.get('setting', {}).get('rules_of_the_world', []), indent=1)}

CAST
{json.dumps(cast, indent=1, ensure_ascii=False)}

PLOTS
{json.dumps([{k: p.get(k) for k in ('plot_id','type','title','goal','outcome','thematic_function')} for p in plots], indent=1, ensure_ascii=False)}

THE EVENT CHAIN IN STORY ORDER — this is what happens
{json.dumps(chain, indent=1, ensure_ascii=False)}

THE SCENES IN READING ORDER
{json.dumps(order, indent=1, ensure_ascii=False)}

HOW IT ENDS
{json.dumps(expose.get('ending_first', {}), indent=1, ensure_ascii=False)}

═══════════════════════════════════════════════════════════════════════════

{SUMMARY_SPEC}

Return one JSON document with exactly the two fields.

SCHEMA
{json.dumps(SCHEMA, indent=1)}
"""


def main():
    project = Project(Path(sys.argv[1] if len(sys.argv) > 1 else "runs/bennington"))
    prompt = build_prompt(project)
    print(f"{project.root}: prompt {len(prompt):,} chars — writing summaries …", flush=True)

    t0 = time.time()
    r = requests.post(f"{BASE}/chat/completions",
                      headers={"Authorization": f"Bearer {KEY}"},
                      json={"model": "grok-4.6",
                            "messages": [{"role": "system", "content": SYSTEM},
                                         {"role": "user", "content": prompt}],
                            "response_format": {"type": "json_schema",
                                                "json_schema": {"name": "summaries",
                                                                "strict": False, "schema": SCHEMA}},
                            "max_completion_tokens": 30000, "temperature": 0.4,
                            "reasoning_effort": "medium"},
                      timeout=2400)
    if r.status_code != 200:
        raise SystemExit(f"HTTP {r.status_code}: {r.text[:500]}")
    d = r.json()
    out = json.loads(d["choices"][0]["message"]["content"])
    u = d.get("usage", {})
    cost = (u.get("prompt_tokens", 0)/1e6)*1.8 + \
           ((u.get("completion_tokens", 0) +
             (u.get("completion_tokens_details") or {}).get("reasoning_tokens", 0))/1e6)*5.4

    short_w = len(out["plot_summary_short"].split())
    long_w = len(out["plot_summary_long"].split())
    print(f"  short {short_w} words | long {long_w} words | {time.time()-t0:.0f}s | ${cost:.3f}")
    for name, w, lo, hi in (("short", short_w, 150, 300), ("long", long_w, 700, 1200)):
        if not lo <= w <= hi:
            print(f"  ! {name} is {w} words, outside {lo}-{hi}")
    if 250 < short_w <= 300:
        print(f"  short ran to {short_w} words — allowed only if the extra room went on "
              f"explaining world mechanics; check that it did")
    # the failure mode worth checking for automatically
    for name in ("plot_summary_short", "plot_summary_long"):
        if "?" in out[name]:
            print(f"  ! {name} contains a question mark — check for teaser phrasing")

    expose = project.load("expose")
    expose.update(out)
    project.save("expose", expose)
    print(f"  -> {project.artifact_path('expose')}")
    print("\n--- short ---\n" + out["plot_summary_short"])


if __name__ == "__main__":
    main()
