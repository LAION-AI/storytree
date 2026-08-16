"""distill CLI.

    python3 -m distill --project distill/runs/matrix parse  --script <path>
    python3 -m distill --project distill/runs/matrix root   [--judge qwen|agent]
    python3 -m distill --project distill/runs/matrix trace  --node root
    python3 -m distill --project distill/runs/matrix status
    python3 -m distill estimate [--json]

The judge is pluggable. `--judge qwen` puts it on a second local endpoint;
`--judge agent` writes a task packet and stops, so an Opus agent can answer it
over subscription credits and the driver can be re-run. Both write the same
critique format into the same place, so a run can mix them and the dataset
records which judged what.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
for extra in (str(REPO), str(REPO / "reconstruct")):
    if extra not in sys.path:
        sys.path.insert(0, extra)

from distill import loop, nodes  # noqa: E402
from distill import rubric as rubric_mod  # noqa: E402
from distill.store import Store  # noqa: E402


@dataclass
class Run:
    root: Path
    script_text: str = ""
    overview: dict = field(default_factory=dict)
    current_envelope: dict | None = None

    @classmethod
    def load(cls, project: Path) -> "Run":
        run = cls(root=Path(project))
        script_map = run.root / "script_map.json"
        if not script_map.exists():
            raise SystemExit(f"no script_map.json in {project} — run `parse` first")
        data = json.loads(script_map.read_text())
        source = run.root / "script.normalized.txt"
        if not source.exists():
            raise SystemExit(
                f"{source} is missing. It is gitignored on purpose (third-party "
                f"screenplay text) — re-run `parse` with --script."
            )
        run.script_text = source.read_text()
        run.overview = data["overview"]
        return run


# --------------------------------------------------------------------------

def cmd_parse(args) -> int:
    from scriptforge import screenplay as sp
    from scriptforge.reverse import script_overview

    project = Path(args.project)
    project.mkdir(parents=True, exist_ok=True)
    raw = Path(args.script).read_text()
    text, scenes = sp.parse(raw)
    (project / "script.normalized.txt").write_text(text)

    summary = sp.summarize(scenes)
    headings = sp.scene_digest(scenes)
    overview = script_overview(summary, headings)
    (project / "script_map.json").write_text(json.dumps({
        "source_file": str(Path(args.script).resolve()),
        "source_chars": len(text),
        "scene_count": len(scenes),
        "overview": overview,
    }, indent=1, ensure_ascii=False))
    print(f"parsed {len(scenes)} scenes, {len(text):,} chars -> {project}")
    return 0


def _backend(kind: str, *, workdir: Path, port: int, label: str):
    if kind == "agent":
        from narrativeforge.backends.agent import AgentBackend
        return AgentBackend(workdir / f"agent-{label}", model_hint="opus")
    from narrativeforge.backends.hyprlab import HyprlabBackend
    os.environ.setdefault("HYPRLAB_API_KEY", "local")
    return HyprlabBackend(
        model=os.environ.get("LOCAL_MODEL", "qwen3.8-27b"),
        base_url=os.environ.get(f"{label.upper()}_BASE_URL",
                                f"http://127.0.0.1:{port}/v1"),
        temperature=float(os.environ.get("TEMPERATURE", "0.7")),
        max_tokens=int(os.environ.get("MAX_TOKENS", "24000")),
        reasoning_effort=None,
        response_format="json_schema",
        log_dir=workdir / "logs" / "calls",
    )


def cmd_node(args) -> int:
    from narrativeforge.backends.base import AwaitingAgent

    project = Path(args.project)
    run = Run.load(project)
    store = Store(project)
    if not store.meta:
        store.init_run({
            "script": str(project / "script.normalized.txt"),
            "scenes": run.overview.get("scene_count"),
            "author": args.author,
            "judge": args.judge,
        })

    author = _backend(args.author, workdir=project, port=args.author_port,
                      label="author")
    judge = _backend(args.judge, workdir=project, port=args.judge_port,
                     label="judge")

    node_type = args.node_type
    node_id = args.node_id or node_type
    print(f"== {node_type} :: {node_id}")
    try:
        result = loop.run_node(node_type=node_type, node_id=node_id, run=run,
                               store=store, author_backend=author,
                               judge_backend=judge, max_rounds=args.max_rounds)
    except AwaitingAgent as pending:
        for backend in (author, judge):
            if getattr(backend, "pending", None):
                path = backend.write_manifest()
                print(f"\nAWAITING AGENT: {pending.tag}")
                print(f"  packet: {pending.packet_path}")
                print(f"  write the answer to: {pending.output_path}")
                print(f"  manifest: {path}")
        return 10

    store.record_usage({"author": author.usage.as_dict(),
                        "judge": judge.usage.as_dict()})
    records = loop.dataset_records(result, store, run_id=project.name)
    store.emit_dataset(node_id, records)
    print(f"\n{node_id}: {'PASSED' if result.passed else 'did not pass'} "
          f"after {result.rounds} round(s); "
          f"{len(records)} dataset record(s) written")
    return 0 if result.passed else 1


def cmd_status(args) -> int:
    project = Path(args.project)
    store = Store(project)
    print(f"run: {project}")
    if store.meta:
        print(json.dumps(store.meta, indent=1))
    art = sorted((project / "artifacts").glob("*.json")) if (project / "artifacts").exists() else []
    for path in art:
        if path.name.endswith(".gate.json"):
            continue
        gate_path = path.with_suffix(".gate.json")
        gate = json.loads(gate_path.read_text())["gate"] if gate_path.exists() else {}
        print(f"  {path.stem:12s} rounds={gate.get('rounds', '?')} "
              f"mean={gate.get('mean', '?')} passed={gate.get('passed')}")
    for node in sorted((project / "rounds").glob("*")) if (project / "rounds").exists() else []:
        failed = store.failed_dimensions(node.name)
        if failed:
            print(f"  {node.name}: dimensions that ever failed -> "
                  f"{ {k: v for k, v in failed.items()} }")
    return 0


def cmd_rubric(args) -> int:
    print(rubric_mod.as_prompt_text(args.rubric))
    return 0


def cmd_estimate(args) -> int:
    from distill import estimate
    report = estimate.build()
    if args.json:
        print(json.dumps(report, indent=1))
    else:
        print(estimate.render_markdown(report))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="distill")
    ap.add_argument("--project", default="distill/runs/default")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("parse")
    p.add_argument("--script", required=True)
    p.set_defaults(func=cmd_parse)

    for node_type in nodes.ORDER:
        p = sub.add_parser(node_type)
        p.add_argument("--node-id", default=None)
        p.add_argument("--author", default="qwen", choices=["qwen", "agent"])
        p.add_argument("--judge", default="agent", choices=["qwen", "agent"])
        p.add_argument("--author-port", type=int, default=8100)
        p.add_argument("--judge-port", type=int, default=8101)
        p.add_argument("--max-rounds", type=int, default=rubric_mod.MAX_ROUNDS)
        p.set_defaults(func=cmd_node, node_type=node_type)

    p = sub.add_parser("status")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("rubric")
    p.add_argument("rubric")
    p.set_defaults(func=cmd_rubric)

    p = sub.add_parser("estimate")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_estimate)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
