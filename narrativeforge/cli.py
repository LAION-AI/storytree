"""Command line interface.

    python -m narrativeforge run      --project runs/x --brief briefs/x.md --backend hyprlab
    python -m narrativeforge run      --project runs/x --backend agent      # exits 10 when work is queued
    python -m narrativeforge validate --project runs/x
    python -m narrativeforge state    --project runs/x --at ev-007 --entity ch-01
    python -m narrativeforge timeline --project runs/x --entity ch-01
    python -m narrativeforge report   --project runs/x
    python -m narrativeforge book     --project runs/x
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import report as reporting, site_index, timeline, validate, webapp
from .backends import make_backend
from .nodegen import Forge
from .pipeline import ALL_STAGES, Pipeline, Project

EXIT_OK = 0
EXIT_INVALID = 1
EXIT_AWAITING_AGENT = 10


def _project(args) -> Project:
    return Project(Path(args.project))


def _pipeline(args, project: Project) -> Pipeline:
    if args.backend == "agent":
        backend = make_backend("agent", workdir=project.agent_dir, model_hint=args.agent_model)
    else:
        backend = make_backend(
            "hyprlab",
            model=args.model,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
            reasoning_effort=args.reasoning_effort,
            response_format=args.response_format,
            log_dir=project.logs / "calls",
        )
    brief = ""
    brief_path = Path(args.brief) if args.brief else project.root / "brief.md"
    if brief_path.exists():
        brief = brief_path.read_text()
        project.root.mkdir(parents=True, exist_ok=True)
        if brief_path.resolve() != (project.root / "brief.md").resolve():
            (project.root / "brief.md").write_text(brief)

    options = {}
    options_path = project.root / "options.json"
    if args.options:
        options = json.loads(Path(args.options).read_text())
        options_path.write_text(json.dumps(options, indent=1))
    elif options_path.exists():
        options = json.loads(options_path.read_text())

    return Pipeline(project, backend, brief=brief, options=options,
                    scene_batch=args.scene_batch,
                    prose_format=getattr(args, "prose_format", "auto"),
                    max_repairs=args.max_repairs)


# --------------------------------------------------------------------------

def cmd_run(args) -> int:
    project = _project(args)
    pipe = _pipeline(args, project)
    stages = args.stages.split(",") if args.stages else ALL_STAGES

    print(f"narrativeforge · {project.root} · backend={args.backend}")
    result = pipe.run(stages, force=args.force)

    if result.pending:
        print("\n" + "=" * 72)
        print("AWAITING AGENT — the pipeline has queued work and stopped.")
        for item in result.pending:
            print(f"\n  stage : {item['tag']}")
            print(f"  read  : {item['packet']}")
            print(f"  write : {item['output']}  ({item['kind']})")
        print("\nSpawn an agent to do exactly that, then re-run this command.")
        print("=" * 72)
        return EXIT_AWAITING_AGENT

    report = result.report
    print(f"\nvalidation: {report.summary()}")
    if not report.ok:
        print(report.as_text(limit=args.show))
    if hasattr(pipe.backend, "cost_usd"):
        usage = pipe.backend.usage
        if usage.calls:
            print(f"usage: {usage.calls} calls · {usage.input_tokens:,} in · "
                  f"{usage.output_tokens:,} out · {usage.reasoning_tokens:,} reasoning · "
                  f"${pipe.backend.cost_usd():.2f}")
            (project.logs / "usage.json").write_text(json.dumps(usage.as_dict(), indent=1))
    return EXIT_OK if report.ok else EXIT_INVALID


def cmd_forge(args) -> int:
    """Flattened, transition-driven generation: one node per call."""
    project = _project(args)
    pipe = _pipeline(args, project)
    forge = Forge(project, pipe.backend, brief=pipe.brief, options=pipe.options,
                  entity_passes=args.entity_passes)

    print(f"narrativeforge forge · {project.root} · backend={args.backend} · "
          f"entity_passes={args.entity_passes}")
    kinds = args.kinds.split(",") if args.kinds else None
    result = forge.run(kinds=kinds, limit=args.limit)

    if result.pending:
        print("\n" + "=" * 72)
        print("AWAITING AGENT")
        for item in result.pending:
            print(f"  stage : {item['tag']}\n  read  : {item['packet']}\n  write : {item['output']}")
        print("=" * 72)
        return EXIT_AWAITING_AGENT

    print(f"\nnodes: {len(result.nodes_written)}  transitions: {len(result.transitions_written)}")
    if result.scores:
        words = [v["score"]["words"] for v in result.scores.values()]
        verdicts = {}
        for v in result.scores.values():
            verdicts[v["verdict"]] = verdicts.get(v["verdict"], 0) + 1
        print(f"transition depth: {sum(words):,} words total, "
              f"{sum(words)//max(1,len(words)):,} avg · verdicts {verdicts}")
        (project.logs / "transition_scores.json").write_text(json.dumps(result.scores, indent=1))
    for e in result.errors[:args.show]:
        print(f"  ! {e}")
    if hasattr(pipe.backend, "cost_usd") and pipe.backend.usage.calls:
        u = pipe.backend.usage
        print(f"usage: {u.calls} calls · {u.input_tokens:,} in · {u.output_tokens:,} out · "
              f"{u.reasoning_tokens:,} reasoning · ${pipe.backend.cost_usd():.2f}")
        (project.logs / "usage_forge.json").write_text(json.dumps(u.as_dict(), indent=1))
    return EXIT_OK


def cmd_validate(args) -> int:
    project = _project(args)
    docs = project.load_all()
    present = [s for s, d in docs.items() if d is not None]
    print(f"layers present: {', '.join(present) or 'none'}")

    for stage, doc in docs.items():
        if doc is None:
            continue
        schema_errors = validate.validate_artifact(stage, doc)
        if schema_errors:
            print(f"\nschema violations in {stage}:")
            for err in schema_errors[:args.show]:
                print(f"  - {err}")

    report = validate.validate_story(
        root=docs["story_root"], expose=docs["expose"], plots_doc=docs["plots"],
        entities_doc=docs["entities"], events_doc=docs["events"],
        scenes_doc=docs["scenes"], prose=project.load_prose(),
    )
    print(f"\ngraph validation: {report.summary()}")
    print(report.as_text(limit=args.show))
    return EXIT_OK if report.ok else EXIT_INVALID


def cmd_state(args) -> int:
    project = _project(args)
    docs = project.load_all()
    fold = timeline.fold(docs["entities"], docs["events"], docs["scenes"])
    world = fold.state_at(args.at)

    if args.entity:
        entity = world.get(args.entity)
        if entity is None:
            print(f"no entity {args.entity!r} at {args.at}", file=sys.stderr)
            return EXIT_INVALID
        payload = entity if args.full else {
            "canonical_name": entity.get("canonical_name"),
            "state": entity.get("state"),
            "relationships": {k: {"kind": v.get("kind"), "valence": v.get("valence")}
                              for k, v in entity.get("relationships", {}).items()},
        }
    else:
        payload = {eid: e.get("state", {}) for eid, e in world.items()}

    print(json.dumps(payload, indent=1, ensure_ascii=False))
    return EXIT_OK


def cmd_timeline(args) -> int:
    project = _project(args)
    docs = project.load_all()
    fold = timeline.fold(docs["entities"], docs["events"], docs["scenes"])
    entities = docs["entities"]["entities"]
    targets = [args.entity] if args.entity else list(entities)

    for eid in targets:
        history = fold.entity_history(eid)
        name = entities.get(eid, {}).get("canonical_name", eid)
        print(f"\n{eid}  {name}   ({len(history)} change(s))")
        for row in history:
            print(f"  {row['scene']}#b{row['beat']:<2} {row['event']}  "
                  f"{row['variable']:<28} {row['before']!r} -> {row['after']!r}"
                  f"   [{row['dimension']}, mag {row['magnitude']}]")
    return EXIT_OK


def cmd_report(args) -> int:
    project = _project(args)
    text = reporting.build_report(project)
    path = project.root / "REPORT.md"
    path.write_text(text)
    print(text if args.stdout else f"wrote {path}")
    return EXIT_OK


def cmd_book(args) -> int:
    project = _project(args)
    text = reporting.build_book(project)
    path = project.root / "BOOK.md"
    path.write_text(text)
    print(f"wrote {path} ({len(text.split()):,} words)")
    return EXIT_OK


def cmd_site(args) -> int:
    project = _project(args)
    out = webapp.build(project, Path(args.out) if args.out else None)
    size = out.stat().st_size
    print(f"wrote {out} ({size/1024:.0f} KB)")
    return EXIT_OK


def cmd_shelf(args) -> int:
    """Build a landing page over several projects, each with its own viewer."""
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    cards = []
    for spec in args.projects:
        # slug=path[:kind[:model[:note]]]
        parts = spec.split(":")
        path = Path(parts[0])
        kind = parts[1] if len(parts) > 1 else "written"
        model = parts[2] if len(parts) > 2 else "grok-4.6"
        note = parts[3] if len(parts) > 3 else ""
        page = f"{path.name}.html"
        proj = Project(path)
        card = site_index.read_project(path, href=page, kind=kind, model=model, note=note)
        if card is None:
            print(f"  skipped {path} (no story_root)")
            continue
        # A reconstruction publishes structure only: never the source document.
        webapp.build(proj, out_dir / page, include_prose=(kind != "reconstructed"))
        cards.append(card)
        print(f"  {card.title:<24} {card.status:<15} {page}")

    index = site_index.build_index(cards, out_dir / "index.html",
                                   extra_links=[("Status report", "status.html"),
                                                ("Reasoning report", "report.html")])
    print(f"\nwrote {index}")
    return EXIT_OK


def cmd_pending(args) -> int:
    project = _project(args)
    manifest = project.agent_dir / "PENDING.json"
    if not manifest.exists():
        print("nothing pending")
        return EXIT_OK
    print(manifest.read_text())
    return EXIT_OK


# --------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="narrativeforge", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--project", default=".", help="project directory")
    parser.add_argument("--show", type=int, default=40, help="max findings to print")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="run the pipeline")
    run.add_argument("--backend", choices=["hyprlab", "agent"], default="hyprlab")
    run.add_argument("--brief", help="path to the brief (defaults to <project>/brief.md)")
    run.add_argument("--options", help="path to a JSON options file for the story root")
    run.add_argument("--stages", help=f"comma-separated subset of {','.join(ALL_STAGES)}")
    run.add_argument("--force", action="store_true", help="regenerate artifacts that already exist")
    run.add_argument("--scene-batch", type=int, default=0,
                     help="events per scene-layer call (0 = one call for all)")
    run.add_argument("--max-repairs", type=int, default=2)
    run.add_argument("--prose-format", default="auto", choices=["auto", "prose", "screenplay"],
                     help="auto follows story_root.form")
    run.add_argument("--model", default=None)
    run.add_argument("--agent-model", default="opus")
    run.add_argument("--temperature", type=float, default=0.85)
    run.add_argument("--max-tokens", type=int, default=32000)
    run.add_argument("--reasoning-effort", default=None,
                     choices=[None, "none", "low", "medium", "high"],
                     help="'none' is the only value that suppresses thinking on local GLM-5.2; "
                          "'low'/'medium' are silent no-ops there and select MAX effort")
    run.add_argument("--response-format", default="json_object", choices=["json_object", "json_schema"])
    run.set_defaults(func=cmd_run)

    forge = sub.add_parser("forge", help="flattened node-at-a-time generation with reasoning transitions")
    forge.add_argument("--backend", choices=["hyprlab", "agent"], default="hyprlab")
    forge.add_argument("--brief", help="path to the brief")
    forge.add_argument("--options", help="path to a JSON options file")
    forge.add_argument("--kinds", help="comma-separated subset of plot,entity,event")
    forge.add_argument("--limit", type=int, default=None, help="stop after N nodes")
    forge.add_argument("--entity-passes", type=int, default=1,
                       help="build each entity dossier in N reasoned passes")
    forge.add_argument("--force", action="store_true")
    forge.add_argument("--scene-batch", type=int, default=0)
    forge.add_argument("--max-repairs", type=int, default=1)
    forge.add_argument("--model", default=None)
    forge.add_argument("--agent-model", default="opus")
    forge.add_argument("--temperature", type=float, default=0.8)
    forge.add_argument("--max-tokens", type=int, default=60000)
    forge.add_argument("--reasoning-effort", default="high",
                       choices=["none", "low", "medium", "high"],
                       help="'none' suppresses hidden thinking (the explicit written-out "
                            "transition is the reasoning); on local GLM-5.2 'low'/'medium' "
                            "are silent no-ops that select MAX")
    forge.add_argument("--response-format", default="json_object", choices=["json_object", "json_schema"])
    forge.set_defaults(func=cmd_forge)

    val = sub.add_parser("validate", help="re-run every constraint over the artifacts on disk")
    val.set_defaults(func=cmd_validate)

    state = sub.add_parser("state", help="reconstruct the world state at a point in time")
    state.add_argument("--at", default="final", help="t0 | ev-NNN | sc-NNN | sc-NNN#bN | final")
    state.add_argument("--entity", default=None)
    state.add_argument("--full", action="store_true", help="whole dossier, not just state")
    state.set_defaults(func=cmd_state)

    tl = sub.add_parser("timeline", help="every change an entity undergoes, in order")
    tl.add_argument("--entity", default=None)
    tl.set_defaults(func=cmd_timeline)

    rep = sub.add_parser("report", help="write REPORT.md")
    rep.add_argument("--stdout", action="store_true")
    rep.set_defaults(func=cmd_report)

    book = sub.add_parser("book", help="assemble the prose leaves into BOOK.md")
    book.set_defaults(func=cmd_book)

    site = sub.add_parser("site", help="build the single-file explorer")
    site.add_argument("--out", default=None, help="output path (default <project>/site/index.html)")
    site.set_defaults(func=cmd_site)

    shelf = sub.add_parser("shelf", help="build a landing page over several projects")
    shelf.add_argument("--out", required=True, help="output directory")
    shelf.add_argument("projects", nargs="+",
                       help="path[:kind[:model[:note]]] — kind is written|reconstructed")
    shelf.set_defaults(func=cmd_shelf)

    pend = sub.add_parser("pending", help="show queued agent packets")
    pend.set_defaults(func=cmd_pending)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
