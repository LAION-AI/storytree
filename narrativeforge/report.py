"""Human-readable views over a finished story graph."""

from __future__ import annotations

from . import timeline, validate


def build_report(project) -> str:
    docs = project.load_all()
    prose = project.load_prose()
    lines: list[str] = []
    add = lines.append

    root = docs.get("story_root") or {}
    add(f"# {root.get('title', project.root.name)}")
    add("")
    if root.get("logline"):
        add(f"*{root['logline']}*")
        add("")
    add(f"`{root.get('genre_primary', '?')}` · {root.get('form', '?')} · "
        f"{root.get('audience', {}).get('age_band', '?')} · "
        f"pov {root.get('pov', {}).get('person', '?')}, {root.get('pov', {}).get('tense', '?')}")
    add("")

    # -- shape ---------------------------------------------------------------
    plots = {p["plot_id"]: p for p in (docs.get("plots") or {}).get("plots", [])}
    entities = (docs.get("entities") or {}).get("entities", {})
    events = (docs.get("events") or {}).get("events", {})
    scenes = (docs.get("scenes") or {}).get("scenes", {})

    add("## Shape")
    add("")
    add("| layer | count |")
    add("|---|---|")
    add(f"| L4 plots | {len(plots)} |")
    add(f"| L3 entities | {len(entities)} |")
    add(f"| L5 events | {len(events)} |")
    add(f"| L6 scenes | {len(scenes)} |")
    add(f"| beats | {sum(len(s.get('beats', [])) for s in scenes.values())} |")
    add(f"| patch ops | {sum(len(b.get('changes', [])) for s in scenes.values() for b in s.get('beats', []))} |")
    add(f"| prose leaves | {len(prose)} |")
    add(f"| prose words | {sum(len(t.split()) for t in prose.values()):,} |")
    add("")

    by_type: dict[str, int] = {}
    for entity in entities.values():
        by_type[entity.get("type", "?")] = by_type.get(entity.get("type", "?"), 0) + 1
    if by_type:
        add("Entities by type: " + ", ".join(f"{k} {v}" for k, v in sorted(by_type.items())))
        add("")

    # -- plots ---------------------------------------------------------------
    if plots:
        add("## Plots")
        add("")
        for pid, plot in sorted(plots.items()):
            owned = [e for e in events.values() if e.get("primary_plot") == pid]
            served = [e for e in events.values() if pid in e.get("plots", [])]
            add(f"### {pid} — {plot.get('title')}")
            add("")
            add(f"- **type** `{plot.get('type')}` · **outcome** `{plot.get('outcome')}` · "
                f"share {plot.get('screen_time_share')}")
            add(f"- **goal** {plot.get('goal')}")
            add(f"- **stakes** {plot.get('stakes')}")
            add(f"- **agent** {plot.get('agent')} vs **resistance** {plot.get('resistance')}")
            add(f"- **events** {len(owned)} owned, {len(served)} served")
            add("")
            add("| step | function | events | because |")
            add("|---|---|---|---|")
            for key, step in sorted(plot.get("spine", {}).items(), key=lambda kv: kv[1].get("step", 0)):
                bound = [eid for eid, e in events.items()
                         if any(b.get("plot") == pid and b.get("step") == key
                                for b in e.get("plot_bindings", []))]
                add(f"| {key} | {step.get('function')} | {', '.join(sorted(bound)) or '—'} "
                    f"| {', '.join(step.get('because', [])) or '—'} |")
            add("")

    # -- the tree ------------------------------------------------------------
    if events and scenes:
        add("## Story tree (primary edges)")
        add("")
        add("Each scene has exactly one parent event; each event exactly one parent plot.")
        add("Secondary memberships are shown in brackets.")
        add("")
        for pid in sorted(plots):
            add(f"- **{pid}** {plots[pid].get('title')}")
            owned = sorted((e for e in events.values() if e.get("primary_plot") == pid),
                           key=lambda e: e.get("story_time", {}).get("index", 0))
            for event in owned:
                extra = [p for p in event.get("plots", []) if p != pid]
                mark = f"  _[also {', '.join(extra)}]_" if extra else ""
                add(f"  - `{event['event_id']}` t{event.get('story_time', {}).get('index')} "
                    f"— {event.get('summary')}{mark}")
                kids = sorted((s for s in scenes.values() if s.get("primary_event") == event["event_id"]),
                              key=lambda s: s.get("discourse_index", 0))
                for scene in kids:
                    also = [e for e in scene.get("events", []) if e != event["event_id"]]
                    mark = f"  _[also {', '.join(also)}]_" if also else ""
                    add(f"    - `{scene['scene_id']}` d{scene.get('discourse_index')} "
                        f"{scene.get('dramatic_function')}{mark}")
        add("")

    # -- state ---------------------------------------------------------------
    if entities and events and scenes:
        fold = timeline.fold(docs["entities"], docs["events"], docs["scenes"])
        add("## State trajectories")
        add("")
        for eid in sorted(entities):
            history = fold.entity_history(eid)
            if not history:
                continue
            add(f"### {eid} — {entities[eid].get('canonical_name')}")
            add("")
            add("| where | event | variable | before | after | dim | mag |")
            add("|---|---|---|---|---|---|---|")
            for row in history:
                add(f"| {row['scene']}#b{row['beat']} | {row['event']} | `{row['variable']}` "
                    f"| `{row['before']}` | `{row['after']}` | {row['dimension']} | {row['magnitude']} |")
            add("")

        add("### Final state")
        add("")
        add("```json")
        import json as _json
        add(_json.dumps({eid: e.get("state", {}) for eid, e in fold.final.items()},
                        indent=1, ensure_ascii=False))
        add("```")
        add("")

    # -- validation ----------------------------------------------------------
    report = validate.validate_story(
        root=docs.get("story_root"), expose=docs.get("expose"), plots_doc=docs.get("plots"),
        entities_doc=docs.get("entities"), events_doc=docs.get("events"),
        scenes_doc=docs.get("scenes"), prose=prose,
    )
    add("## Validation")
    add("")
    add(f"**{report.summary()}**")
    add("")
    if report.findings:
        add("```")
        add(report.as_text())
        add("```")
    else:
        add("Every constraint holds.")
    add("")

    return "\n".join(lines) + "\n"


def build_book(project) -> str:
    docs = project.load_all()
    root = docs.get("story_root") or {}
    scenes = (docs.get("scenes") or {}).get("scenes", {})
    prose = project.load_prose()

    lines = [f"# {root.get('title', 'Untitled')}", ""]
    if root.get("logline"):
        lines += [f"*{root['logline']}*", ""]

    chapter = None
    for sid in sorted(scenes, key=lambda s: scenes[s].get("discourse_index", 0)):
        if sid not in prose:
            continue
        scene = scenes[sid]
        if scene.get("chapter") != chapter:
            chapter = scene.get("chapter")
            lines += ["", f"## {chapter}", ""]
        else:
            lines += ["", "* * *", ""]
        lines.append(prose[sid].strip())

    return "\n".join(lines) + "\n"
