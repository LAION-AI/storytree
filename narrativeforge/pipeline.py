"""The staged driver.

    story_root -> expose -> plots -> entities -> events -> scenes -> prose

Each stage writes one artifact to disk before the next begins, which buys three
things: resumability (re-running skips what exists), the agent handshake (the
driver can stop mid-pipeline and be restarted), and partial recovery (one
malformed field costs one stage, not the whole run).

Every artifact is validated the moment it lands, and a failing artifact goes
through a bounded repair loop — the violations are handed back verbatim and the
model returns an RFC 6902 patch that is applied mechanically and re-checked.
"""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path

from . import jsonpatch, plotembedding, prompts, timeline, validate
from .backends import AwaitingAgent, Backend, BackendError
from .schemas import SCHEMAS

ARTIFACT_STAGES = ["story_root", "expose", "plots", "entities", "events", "scenes"]
ALL_STAGES = ARTIFACT_STAGES + ["prose"]


@dataclass
class Project:
    root: Path

    def __post_init__(self) -> None:
        self.root = Path(self.root)

    @property
    def artifacts(self) -> Path:
        return self.root / "artifacts"

    @property
    def prose_dir(self) -> Path:
        return self.root / "prose"

    @property
    def derived(self) -> Path:
        return self.root / "derived"

    @property
    def agent_dir(self) -> Path:
        return self.root / "_agent"

    @property
    def logs(self) -> Path:
        return self.root / "logs"

    def ensure(self) -> None:
        for path in (self.artifacts, self.prose_dir, self.derived, self.logs):
            path.mkdir(parents=True, exist_ok=True)

    def artifact_path(self, stage: str) -> Path:
        return self.artifacts / f"{stage}.json"

    def load(self, stage: str) -> dict | None:
        path = self.artifact_path(stage)
        if not path.exists():
            return None
        return json.loads(path.read_text())

    def save(self, stage: str, doc: dict) -> Path:
        path = self.artifact_path(stage)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
        return path

    def load_prose(self) -> dict[str, str]:
        if not self.prose_dir.exists():
            return {}
        return {p.stem: p.read_text() for p in sorted(self.prose_dir.glob("sc-*.md"))}

    def load_all(self) -> dict:
        return {stage: self.load(stage) for stage in ARTIFACT_STAGES}


@dataclass
class RunResult:
    completed: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    pending: list[dict] = field(default_factory=list)
    report: validate.Report | None = None
    repairs: dict = field(default_factory=dict)

    @property
    def awaiting_agent(self) -> bool:
        return bool(self.pending)


# --------------------------------------------------------------------------


class Pipeline:
    def __init__(
        self,
        project: Project,
        backend: Backend,
        *,
        brief: str = "",
        options: dict | None = None,
        scene_batch: int = 0,
        prose_format: str = "auto",
        max_repairs: int = 2,
        verbose: bool = True,
    ) -> None:
        self.project = project
        self.backend = backend
        self.brief = brief
        self.options = options or {}
        self.scene_batch = scene_batch
        self.prose_format = prose_format
        self.max_repairs = max_repairs
        self.verbose = verbose
        self.project.ensure()

    def log(self, message: str) -> None:
        if self.verbose:
            print(message, flush=True)

    # -- stage execution -----------------------------------------------------

    def _build_prompt(self, stage: str, docs: dict) -> str:
        if stage == "story_root":
            return prompts.story_root_prompt(self.brief, self.options)
        if stage == "expose":
            return prompts.expose_prompt(docs["story_root"])
        if stage == "plots":
            return prompts.plots_prompt(docs["story_root"], docs["expose"])
        if stage == "entities":
            return prompts.entities_prompt(docs["story_root"], docs["expose"], docs["plots"])
        if stage == "events":
            return prompts.events_prompt(docs["story_root"], docs["expose"],
                                         docs["plots"], docs["entities"])
        raise ValueError(f"{stage} is not a single-call artifact stage")

    def run_stage(self, stage: str, *, force: bool = False) -> str:
        existing = self.project.load(stage)
        if existing is not None and not force:
            self.log(f"  · {stage:<11} present, skipping")
            return "skipped"

        docs = self.project.load_all()
        missing = [s for s in ARTIFACT_STAGES[:ARTIFACT_STAGES.index(stage)] if docs.get(s) is None]
        if missing:
            raise BackendError(f"cannot run {stage}: {', '.join(missing)} not yet produced")

        if stage == "scenes":
            doc = self._run_scenes(docs)
        else:
            user = self._build_prompt(stage, docs)
            self.log(f"  · {stage:<11} generating ({len(user):,} prompt chars)")
            doc = self.backend.complete_json(
                prompts.SYSTEM, user, SCHEMAS[stage], stage=stage, tag=stage
            )

        if stage == "story_root" and isinstance(doc.get("plot_embedding"), dict):
            # `dominant` is derivable from the genre scores; models get it wrong
            # often enough that trusting them just generates validation noise.
            for fix in plotembedding.normalize_embedding(doc["plot_embedding"]):
                self.log(f"    normalised {fix}")

        self.project.save(stage, doc)
        self._validate_and_repair(stage)
        return "completed"

    # -- L6, which is segmented ---------------------------------------------

    def _run_scenes(self, docs: dict) -> dict:
        events = docs["events"]["events"]
        ordered = sorted(events, key=lambda e: events[e].get("story_time", {}).get("index", 0))
        batch_size = self.scene_batch or len(ordered)
        batches = [ordered[i:i + batch_size] for i in range(0, len(ordered), batch_size)]

        scenes: dict = {}
        tail = ""
        for n, chunk in enumerate(batches, start=1):
            live = self._live_state(docs, scenes)
            user = prompts.scenes_prompt(
                docs["story_root"], docs["plots"], docs["entities"], docs["events"],
                chunk=chunk, live_state=live, previous_tail=tail,
                scene_start=len(scenes) + 1,
            )
            tag = "scenes" if len(batches) == 1 else f"scenes.b{n}"
            self.log(f"  · scenes      batch {n}/{len(batches)}: {len(chunk)} events "
                     f"({len(user):,} prompt chars)")
            part = self.backend.complete_json(
                prompts.SYSTEM, user, SCHEMAS["scenes"], stage="scenes", tag=tag
            )
            new = part.get("scenes", {})
            scenes.update(new)
            tail = json.dumps(
                [{"scene": sid, "dramatic_function": s.get("dramatic_function"),
                  "last_beat": (s.get("beats") or [{}])[-1].get("text", "")}
                 for sid, s in list(new.items())[-2:]],
                ensure_ascii=False,
            )
            # Checkpoint after every batch so a later failure never costs an earlier one.
            self.project.save("scenes", {"scenes": scenes})
        return {"scenes": scenes}

    def _live_state(self, docs: dict, scenes_so_far: dict) -> dict:
        """The carry-over state object: entity states as this batch begins."""
        if not scenes_so_far:
            world = timeline.world_state_t0(docs["entities"])
        else:
            fold = timeline.fold(docs["entities"], docs["events"], {"scenes": scenes_so_far})
            world = fold.final
        return {
            eid: {"name": entity.get("canonical_name"), "state": entity.get("state", {})}
            for eid, entity in world.items()
        }

    # -- validation and repair ----------------------------------------------

    def _current_report(self) -> validate.Report:
        docs = self.project.load_all()
        return validate.validate_story(
            root=docs["story_root"], expose=docs["expose"], plots_doc=docs["plots"],
            entities_doc=docs["entities"], events_doc=docs["events"],
            scenes_doc=docs["scenes"], prose=self.project.load_prose(),
        )

    def _validate_and_repair(self, stage: str) -> validate.Report:
        for attempt in range(self.max_repairs + 1):
            doc = self.project.load(stage)
            schema_errors = validate.validate_artifact(stage, doc)
            report = self._current_report()
            findings = schema_errors + [str(f) for f in report.errors]

            if not findings:
                self.log(f"    validation: clean ({report.summary()})")
                return report
            if attempt == self.max_repairs:
                self.log(f"    validation: {len(findings)} error(s) remain after "
                         f"{self.max_repairs} repair attempt(s) — quarantining for review")
                (self.project.logs / f"{stage}.violations.txt").write_text("\n".join(findings))
                return report

            self.log(f"    validation: {len(findings)} error(s), repair attempt {attempt + 1}")
            shutil.copy(self.project.artifact_path(stage),
                        self.project.artifacts / f"{stage}.pre-repair{attempt + 1}.json")
            self._apply_repair(stage, doc, findings, attempt + 1)
        return self._current_report()

    def _apply_repair(self, stage: str, doc: dict, findings: list[str], attempt: int) -> None:
        user = prompts.repair_prompt(stage, doc, findings[:60])
        try:
            answer = self.backend.complete_json(
                prompts.SYSTEM, user, SCHEMAS["repair"],
                stage=f"{stage}.repair", tag=f"{stage}.repair{attempt}",
            )
        except AwaitingAgent:
            raise
        except BackendError as exc:
            self.log(f"    repair call failed: {exc}")
            return

        ops = answer.get("patch", [])
        if not ops:
            self.log("    repair returned no ops")
            return

        # Best-effort, not all-or-nothing. One malformed op out of ninety used to
        # discard the other eighty-nine and send the model round again to redo
        # work it had already done correctly.
        patched, failures = jsonpatch.apply_best_effort(doc, ops)
        landed = len(ops) - len(failures)
        if failures:
            self.log(f"    {landed}/{len(ops)} op(s) applied, {len(failures)} rejected")
            for f in failures[:3]:
                self.log(f"      ! {f}")
            (self.project.logs / f"{stage}.rejected-ops{attempt}.json").write_text(
                json.dumps(failures, indent=1, ensure_ascii=False))
        if not landed:
            self.log("    no op applied — keeping the previous document")
            (self.project.logs / f"{stage}.failed-repair{attempt}.json").write_text(
                json.dumps(answer, indent=1, ensure_ascii=False))
            return

        # A repair that makes things worse is not a repair. Without this check a
        # patch could quietly trade five violations for fifteen and the loop
        # would carry the damage forward as its new baseline.
        before = len(validate.validate_artifact(stage, doc))
        after = len(validate.validate_artifact(stage, patched))
        if after > before:
            self.log(f"    repair rejected: {before} -> {after} schema error(s), reverting")
            (self.project.logs / f"{stage}.regressive-repair{attempt}.json").write_text(
                json.dumps(answer, indent=1, ensure_ascii=False))
            return

        self.project.save(stage, patched)
        (self.project.logs / f"{stage}.repair{attempt}.json").write_text(
            json.dumps(answer, indent=1, ensure_ascii=False))
        self.log(f"    applied {landed} repair op(s): {before} -> {after} schema error(s)")

    # -- T6, the leaves ------------------------------------------------------

    def run_prose(self, *, force: bool = False, only: list[str] | None = None) -> list[str]:
        docs = self.project.load_all()
        if docs["scenes"] is None:
            raise BackendError("cannot write prose before the scene layer exists")

        scenes = docs["scenes"]["scenes"]
        fold = timeline.fold(docs["entities"], docs["events"], docs["scenes"])
        order = sorted(scenes, key=lambda s: scenes[s].get("discourse_index", 0))
        written: list[str] = []
        tail = ""

        for scene_id in order:
            path = self.project.prose_dir / f"{scene_id}.md"
            if only and scene_id not in only:
                if path.exists():
                    tail = " ".join(path.read_text().split()[-120:])
                continue
            if path.exists() and not force:
                tail = " ".join(path.read_text().split()[-120:])
                continue

            user = prompts.prose_prompt(
                docs["story_root"], scenes[scene_id], docs["entities"], docs["events"],
                entry_world=fold.state_entering_scene(scene_id), previous_tail=tail,
                fmt=self.prose_format,
            )
            self.log(f"  · prose       {scene_id} "
                     f"(target {scenes[scene_id].get('target_words')} words)")
            text = self.backend.complete_text(
                prompts.SYSTEM, user, stage="prose", tag=f"prose.{scene_id}"
            )
            path.write_text(text.strip() + "\n")
            tail = " ".join(text.split()[-120:])
            written.append(scene_id)

        return written

    # -- derived artifacts ---------------------------------------------------

    def write_derived(self) -> None:
        docs = self.project.load_all()
        if not all(docs[s] for s in ("entities", "events", "scenes")):
            return
        fold = timeline.fold(docs["entities"], docs["events"], docs["scenes"])
        out = self.project.derived
        (out / "patches").mkdir(parents=True, exist_ok=True)

        (out / "world_state_t0.json").write_text(
            json.dumps(fold.world_t0, indent=1, ensure_ascii=False) + "\n")
        (out / "world_state_final.json").write_text(
            json.dumps(fold.final, indent=1, ensure_ascii=False) + "\n")

        events = docs["events"]["events"]
        scenes = docs["scenes"]["scenes"]
        plots = {p["plot_id"] for p in docs["plots"]["plots"]}

        (out / "patches" / "by_event.json").write_text(json.dumps(
            {eid: fold.event_patch(eid) for eid in
             sorted(events, key=lambda e: events[e].get("story_time", {}).get("index", 0))},
            indent=1, ensure_ascii=False) + "\n")
        (out / "patches" / "by_scene.json").write_text(json.dumps(
            {sid: fold.scene_patch(sid) for sid in
             sorted(scenes, key=lambda s: scenes[s].get("discourse_index", 0))},
            indent=1, ensure_ascii=False) + "\n")
        (out / "patches" / "by_plot.json").write_text(json.dumps(
            {pid: fold.plot_patch(pid, events) for pid in sorted(plots)},
            indent=1, ensure_ascii=False) + "\n")

        (out / "states_by_event.json").write_text(json.dumps(
            {eid: {e: v.get("state", {}) for e, v in fold.state_after_event(eid).items()}
             for eid in sorted(events, key=lambda e: events[e].get("story_time", {}).get("index", 0))},
            indent=1, ensure_ascii=False) + "\n")

        (out / "entity_timelines.json").write_text(json.dumps(
            {eid: fold.entity_history(eid) for eid in docs["entities"]["entities"]},
            indent=1, ensure_ascii=False) + "\n")

    # -- the whole thing -----------------------------------------------------

    def run(self, stages: list[str] | None = None, *, force: bool = False) -> RunResult:
        result = RunResult()
        wanted = stages or ALL_STAGES

        for stage in ARTIFACT_STAGES:
            if stage not in wanted:
                continue
            try:
                status = self.run_stage(stage, force=force)
            except AwaitingAgent as awaiting:
                result.pending.append({"tag": awaiting.tag, "packet": awaiting.packet_path,
                                       "output": awaiting.output_path, "kind": awaiting.kind})
                return self._finish(result)
            result.completed.append(stage) if status == "completed" else result.skipped.append(stage)

        if "prose" in wanted:
            try:
                written = self.run_prose(force=force)
            except AwaitingAgent as awaiting:
                result.pending.append({"tag": awaiting.tag, "packet": awaiting.packet_path,
                                       "output": awaiting.output_path, "kind": awaiting.kind})
                return self._finish(result)
            if written:
                result.completed.append(f"prose({len(written)})")

        return self._finish(result)

    def _finish(self, result: RunResult) -> RunResult:
        try:
            self.write_derived()
        except Exception as exc:  # derived artifacts must never break a run
            self.log(f"  (derived artifacts skipped: {exc})")
        result.report = self._current_report()
        if hasattr(self.backend, "write_manifest") and result.pending:
            self.backend.write_manifest()
        return result
