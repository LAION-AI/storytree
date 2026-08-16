"""Command line for the reconstruction fork.

    python3 -m scriptforge.recon_cli parse    --script samples/tideline.fountain
    python3 -m scriptforge.recon_cli run      --project runs/x --script path/to/script.txt
    python3 -m scriptforge.recon_cli check    --project runs/x
    python3 -m scriptforge.recon_cli dryrun   --script samples/tideline.fountain

`dryrun` builds every prompt the pipeline would send and reports their sizes
without calling any model. It is how you confirm the wiring before spending
anything.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import reverse, screenplay as sp, validate
from .backends import make_backend
from .pipeline import Project
from .reconstruct import Reconstructor


def cmd_parse(args) -> int:
    raw = Path(args.script).read_text(encoding="utf-8", errors="replace")
    text, scenes = sp.parse(raw)
    table = sp.anchor_table(text, scenes)
    summary = sp.summarize(scenes)
    problems = sp.verify(text, scenes, table)

    print(f"{args.script}")
    print(f"  scenes            {summary['scenes']}")
    print(f"  words             {summary['words']:,}")
    print(f"  A4 pages          {summary['estimated_pages_a4']}")
    print(f"  runtime (min)     {summary['estimated_runtime_min']}")
    print(f"  dialogue ratio    {summary['mean_dialogue_ratio']}")
    print(f"  speakers          {', '.join(summary['distinct_speakers'][:12])}")
    print(f"  coverage          {table['coverage']:.1%}")
    print(f"  anchors unique    {sum(1 for v in table['scenes'].values() if v['anchors_unique'])}"
          f"/{len(table['scenes'])}")
    if problems:
        print(f"\n  {len(problems)} problem(s):")
        for p in problems[:args.show]:
            print(f"    - {p}")
    else:
        print("  round trip        exact for every scene")

    if args.out:
        Path(args.out).write_text(json.dumps(table, indent=1, ensure_ascii=False) + "\n")
        print(f"\n  anchor table -> {args.out}")
    if args.list:
        print()
        for s in scenes:
            print(f"  {s.scene_id}  {s.word_count:>5}w  {s.dialogue_ratio:.2f}  {s.heading}")
    return 0 if not problems else 1


def cmd_dryrun(args) -> int:
    """Build every prompt without sending any of them."""
    raw = Path(args.script).read_text(encoding="utf-8", errors="replace")
    text, scenes = sp.parse(raw)
    overview = reverse.script_overview(
        sp.summarize(scenes),
        [dict(sp.scene_digest([s])[0], heading=s.heading) for s in scenes])

    root_stub = {"title": "?", "form": "screenplay", "constraints": {},
                 "setting": {}, "style": {}, "keep_in_mind": []}
    expose_stub = {"ending_first": {}, "synopsis": {}}
    plots_stub = {"plots": []}
    ents_stub = {"entities": {}}

    prompts = {
        "story_root": reverse.story_root_prompt(text, overview, {}),
        "expose": reverse.expose_prompt(root_stub, text, overview),
        "plots": reverse.plots_prompt(root_stub, expose_stub, text, overview),
        "entities": reverse.entities_prompt(root_stub, expose_stub, plots_stub, text),
    }
    ctx = {"root": root_stub, "expose": expose_stub, "plots": [], "entities": {},
           "prior": None, "live_state": {}}
    env = reverse.envelope(scenes[0], len(scenes) - 1, len(scenes))
    prompts["blind_transition (sc-001)"] = reverse.blind_transition_prompt(
        "scene", "sc-001", ctx, env)
    table = sp.anchor_table(text, scenes)
    prompts["scene_node (sc-001)"] = reverse.scene_node_prompt(
        "sc-001", ctx, {}, dict(table["scenes"]["sc-001"], scene_id="sc-001"),
        scenes[0].text(text))

    total = 0
    print(f"dry run · {args.script} · {len(scenes)} scenes\n")
    for name, p in prompts.items():
        total += len(p)
        print(f"  {name:<28} {len(p):>9,} chars  ≈{len(p)//4:>7,} tok")
    per_scene = len(prompts["blind_transition (sc-001)"]) + len(prompts["scene_node (sc-001)"])
    print(f"\n  upper layers (4 calls)       ≈{sum(len(prompts[k]) for k in ('story_root','expose','plots','entities'))//4:,} tok in")
    print(f"  per scene (2 calls)          ≈{per_scene//4:,} tok in")
    print(f"  whole script ({len(scenes)} scenes)      ≈{(per_scene*len(scenes))//4:,} tok in")

    # the property that matters most, checked without a model
    print("\n  blind/sighted separation:")
    bt = prompts["blind_transition (sc-001)"]
    body = scenes[0].text(text)
    leaked = body[:200].strip() in bt
    print(f"    scene text absent from the blind prompt : {'yes' if not leaked else 'NO — LEAK'}")
    print(f"    envelope present                        : {'yes' if 'PRODUCTION ENVELOPE' in bt else 'no'}")
    print(f"    scene text present in the node prompt   : {'yes' if body[:120].strip() in prompts['scene_node (sc-001)'] else 'no'}")
    return 0


def cmd_run(args) -> int:
    project = Project(Path(args.project))
    backend = make_backend("hyprlab", model=args.model, temperature=args.temperature,
                           max_tokens=args.max_tokens, reasoning_effort=args.reasoning_effort,
                           log_dir=project.logs / "calls") if args.backend == "hyprlab" \
        else make_backend("agent", workdir=project.agent_dir)

    recon = Reconstructor(project, backend, Path(args.script),
                          options=json.loads(Path(args.options).read_text()) if args.options else {},
                          blind_transitions=not args.no_transitions,
                          inline_prose=args.inline_prose)

    print(f"scriptforge reconstruct · {project.root} · {args.script}")
    recon.parse_script()
    if args.stages in (None, "all", "upper"):
        recon.run_upper(force=args.force)
    if args.stages in (None, "all", "events"):
        recon.run_events(force=args.force)
    if args.stages in (None, "all", "scenes"):
        result = recon.run_scenes(limit=args.limit, force=args.force)
        if result.pending:
            print("\nAWAITING AGENT")
            for p in result.pending:
                print(f"  read  : {p['packet']}\n  write : {p['output']}")
            return 10
        print(f"\nscenes bound: {result.scenes_bound} · blind transitions: {result.transitions}")
        if result.divergence:
            qs = [d["quality"] for d in result.divergence if d["quality"] is not None]
            if qs:
                print(f"forecast quality: mean {sum(qs)/len(qs):.0f}, "
                      f"range {min(qs)}-{max(qs)}")
        for e in result.errors[:10]:
            print(f"  ! {e}")

    n = recon.bind_prose()
    print(f"prose bound: {n} scenes ({'inlined' if args.inline_prose else 'by reference'})")
    problems = recon.check_binding()
    print(f"binding: {'one to one, complete' if not problems else str(len(problems)) + ' problem(s)'}")
    for p in problems[:10]:
        print(f"  - {p}")
    return 0


def cmd_check(args) -> int:
    project = Project(Path(args.project))
    docs = project.load_all()
    report = validate.validate_story(
        root=docs["story_root"], expose=docs["expose"], plots_doc=docs["plots"],
        entities_doc=docs["entities"], events_doc=docs["events"], scenes_doc=docs["scenes"])
    print(f"graph validation: {report.summary()}")
    print(report.as_text(limit=args.show))

    map_path = project.root / "script_map.json"
    if map_path.exists():
        recon = Reconstructor(project, None, Path(json.loads(map_path.read_text())["source_file"]))
        problems = recon.check_binding()
        print(f"\nbinding: {'clean' if not problems else str(len(problems)) + ' problem(s)'}")
        for p in problems[:args.show]:
            print(f"  - {p}")
    return 0 if report.ok else 1


def build_parser():
    ap = argparse.ArgumentParser(prog="scriptforge.recon_cli", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--show", type=int, default=25)
    sub = ap.add_subparsers(dest="command", required=True)

    p = sub.add_parser("parse", help="parse a screenplay and report the anchor table")
    p.add_argument("--script", required=True)
    p.add_argument("--out", help="write the anchor table here")
    p.add_argument("--list", action="store_true", help="list every scene")
    p.set_defaults(func=cmd_parse)

    d = sub.add_parser("dryrun", help="build every prompt without calling a model")
    d.add_argument("--script", required=True)
    d.set_defaults(func=cmd_dryrun)

    r = sub.add_parser("run", help="reconstruct the layers above a screenplay")
    r.add_argument("--project", required=True)
    r.add_argument("--script", required=True)
    r.add_argument("--options")
    r.add_argument("--stages", choices=["all", "upper", "events", "scenes"], default="all")
    r.add_argument("--limit", type=int, default=None, help="stop after N scenes")
    r.add_argument("--force", action="store_true")
    r.add_argument("--no-transitions", action="store_true",
                   help="skip the blind forecast (halves the cost, loses the divergence record)")
    r.add_argument("--inline-prose", action="store_true",
                   help="copy each passage into the project instead of referencing it")
    r.add_argument("--backend", choices=["hyprlab", "agent"], default="hyprlab")
    r.add_argument("--model", default=None)
    r.add_argument("--temperature", type=float, default=0.7)
    r.add_argument("--max-tokens", type=int, default=60000)
    r.add_argument("--reasoning-effort", default="high", choices=["low", "medium", "high"])
    r.set_defaults(func=cmd_run)

    c = sub.add_parser("check", help="validate a reconstruction, including the binding")
    c.add_argument("--project", required=True)
    c.set_defaults(func=cmd_check)
    return ap


def main(argv=None):
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
