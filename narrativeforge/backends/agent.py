"""Agent backend — the same pipeline, executed by a spawned Claude Code agent.

There is no API call here. The backend writes the stage's prompt to a task
packet on disk and raises `AwaitingAgent`. The driver catches that, prints what
is pending, and exits with status 10. You then spawn an agent (Opus 5, via the
Agent tool) whose entire job is:

    read <packet>.task.md, do exactly what it says, write the result to <out>

and re-run the driver, which finds the answer file and continues from there.
Because every artifact is written to disk as it is completed, the pipeline is
fully resumable and the handshake can repeat as many times as there are stages.

The prompts are byte-identical to the ones the API backend sends. The agent is
not told it is an agent, is given no extra latitude, and its output is put
through exactly the same validator and repair loop. That is the whole point:
the two backends are comparable because only the executor differs.
"""

from __future__ import annotations

import json
from pathlib import Path

from .base import AwaitingAgent, Backend, BackendError, extract_json

PACKET_TEMPLATE = """\
# Task packet — `{tag}`

You are executing one stage of a structured narrative generation pipeline.
Follow the instructions below exactly. They are the same instructions the API
backend receives; you are the executor, not the author of the process.

**When you are done, write your output to this exact path and nothing else:**

```
{output_path}
```

{format_note}

Do not write any other file. Do not print the result to the transcript. Do not
ask for confirmation. Do not add commentary to the output file.

---

## System instructions

{system}

---

## Stage instructions

{user}
"""

JSON_NOTE = """\
The file must contain **one JSON document and nothing else** — no markdown
fence, no preamble, no trailing prose. It will be parsed mechanically and
validated against the schema below; a wrapper of any kind will fail the parse.
Write it with the Write tool in a single call.
"""

TEXT_NOTE = """\
The file must contain **the prose only** — no front matter, no title, no scene
heading, no markdown headers, no commentary. Write it with the Write tool in a
single call.
"""


class AgentBackend(Backend):
    name = "agent"

    def __init__(self, workdir: Path, *, model_hint: str = "opus") -> None:
        super().__init__()
        self.workdir = Path(workdir)
        self.workdir.mkdir(parents=True, exist_ok=True)
        self.model_hint = model_hint
        self.pending: list[AwaitingAgent] = []

    # ----------------------------------------------------------------------

    def _paths(self, tag: str, suffix: str) -> tuple[Path, Path]:
        safe = tag.replace("/", "_")
        return self.workdir / f"{safe}.task.md", self.workdir / f"{safe}.out{suffix}"

    def _dispatch(self, tag: str, system: str, user: str, suffix: str, note: str) -> Path:
        packet, output = self._paths(tag, suffix)
        if output.exists() and output.read_text().strip():
            return output
        packet.write_text(PACKET_TEMPLATE.format(
            tag=tag,
            output_path=output.resolve(),
            format_note=note,
            system=system,
            user=user,
        ))
        awaiting = AwaitingAgent(tag, str(packet.resolve()), str(output.resolve()),
                                 "json" if suffix == ".json" else "text")
        self.pending.append(awaiting)
        raise awaiting

    def complete_json(self, system: str, user: str, schema: dict, *, stage: str, tag: str) -> dict:
        output = self._dispatch(tag, system, user, ".json", JSON_NOTE)
        raw = output.read_text()
        try:
            return extract_json(raw)
        except BackendError as exc:
            raise BackendError(
                f"{tag}: the agent's output at {output} is not parseable JSON ({exc}). "
                f"Delete the file and re-run to reissue the packet."
            ) from None

    def complete_text(self, system: str, user: str, *, stage: str, tag: str) -> str:
        output = self._dispatch(tag, system, user, ".md", TEXT_NOTE)
        return output.read_text().strip()

    def cost_usd(self) -> float:
        return 0.0  # subscription credits, not metered here

    # ----------------------------------------------------------------------

    def manifest(self) -> dict:
        """What the orchestrator needs in order to spawn the right agents."""
        return {
            "backend": "agent",
            "model_hint": self.model_hint,
            "pending": [
                {"tag": item.tag, "packet": item.packet_path,
                 "output": item.output_path, "kind": item.kind}
                for item in self.pending
            ],
        }

    def write_manifest(self) -> Path:
        path = self.workdir / "PENDING.json"
        path.write_text(json.dumps(self.manifest(), indent=1))
        return path
