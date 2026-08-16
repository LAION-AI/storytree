"""Run storage. Every artifact, critique, revision and trace is kept.

Layout under a run directory:

    run/
      run.json                 config, model ids, timestamps
      artifacts/<node>.json    the passing (or final) artifact
      rounds/<node>/r1.draft.json
      rounds/<node>/r1.critique.json
      rounds/<node>/r2.draft.json ...
      traces/<node>.json       the hindsight trace and its own round history
      usage.json               per-call token accounting
      dataset/<node>.jsonl     the fine-tuning records emitted for this node

Nothing is overwritten. A re-run resumes from whatever is already on disk,
which is what makes the agent-backed judge workable at all: the driver stops,
an Opus agent answers one packet, the driver is re-run.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path


def _write(path: Path, doc) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(doc, str):
        path.write_text(doc)
    else:
        path.write_text(json.dumps(doc, indent=1, ensure_ascii=False))
    return path


@dataclass
class Store:
    root: Path
    meta: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.root = Path(self.root)
        self.root.mkdir(parents=True, exist_ok=True)
        if (self.root / "run.json").exists():
            self.meta = json.loads((self.root / "run.json").read_text())

    # -- config ------------------------------------------------------------

    def init_run(self, config: dict) -> None:
        self.meta = dict(config)
        self.meta.setdefault("created_at", time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                                         time.gmtime()))
        _write(self.root / "run.json", self.meta)

    # -- artifacts ---------------------------------------------------------

    def artifact_path(self, node_id: str) -> Path:
        return self.root / "artifacts" / f"{node_id}.json"

    def has_artifact(self, node_id: str) -> bool:
        return self.artifact_path(node_id).exists()

    def load_artifact(self, node_id: str) -> dict:
        return json.loads(self.artifact_path(node_id).read_text())

    def save_artifact(self, node_id: str, doc: dict, *, gate: dict,
                      rounds: int) -> Path:
        path = _write(self.artifact_path(node_id), doc)
        _write(self.root / "artifacts" / f"{node_id}.gate.json",
               {"node_id": node_id, "rounds": rounds, "gate": gate})
        return path

    # -- rounds ------------------------------------------------------------

    def round_dir(self, node_id: str) -> Path:
        return self.root / "rounds" / node_id

    def save_draft(self, node_id: str, round_no: int, doc: dict) -> Path:
        return _write(self.round_dir(node_id) / f"r{round_no}.draft.json", doc)

    def save_critique(self, node_id: str, round_no: int, doc: dict) -> Path:
        return _write(self.round_dir(node_id) / f"r{round_no}.critique.json", doc)

    def load_round(self, node_id: str, round_no: int, kind: str) -> dict | None:
        path = self.round_dir(node_id) / f"r{round_no}.{kind}.json"
        return json.loads(path.read_text()) if path.exists() else None

    def history(self, node_id: str) -> list[dict]:
        """Every round of this node, oldest first."""
        out = []
        d = self.round_dir(node_id)
        if not d.exists():
            return out
        rounds = sorted({int(p.name.split(".")[0][1:]) for p in d.glob("r*.json")})
        for n in rounds:
            out.append({
                "round": n,
                "draft": self.load_round(node_id, n, "draft"),
                "critique": self.load_round(node_id, n, "critique"),
            })
        return out

    def failed_dimensions(self, node_id: str) -> dict[str, list[int]]:
        """Dimension -> every score it ever received below the gate. This is the
        ground truth the hindsight trace's trap list is checked against."""
        out: dict[str, list[int]] = {}
        for entry in self.history(node_id):
            critique = entry.get("critique") or {}
            for row in critique.get("scores", []):
                if isinstance(row.get("score"), int) and row["score"] < 3:
                    out.setdefault(row["dimension"], []).append(row["score"])
        return out

    # -- traces ------------------------------------------------------------

    def save_trace(self, node_id: str, doc: dict, *, gate: dict,
                   rounds: int) -> Path:
        payload = {
            "node_id": node_id,
            "is_hindsight": True,
            "rounds": rounds,
            "gate": gate,
            "trace": doc,
        }
        return _write(self.root / "traces" / f"{node_id}.json", payload)

    def has_trace(self, node_id: str) -> bool:
        return (self.root / "traces" / f"{node_id}.json").exists()

    # -- usage -------------------------------------------------------------

    def record_usage(self, usage: dict) -> Path:
        path = self.root / "usage.json"
        existing = json.loads(path.read_text()) if path.exists() else {}
        return _write(path, _merge_counts(existing, usage))

    # -- dataset -----------------------------------------------------------

    def emit_dataset(self, node_id: str, records: list[dict]) -> Path:
        path = self.root / "dataset" / f"{node_id}.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(json.dumps(r, ensure_ascii=False)
                                  for r in records) + "\n")
        return path
