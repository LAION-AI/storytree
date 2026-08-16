"""Backend contract.

A backend turns (system prompt, user prompt) into either a JSON document or a
block of text. That is the entire interface — everything that decides *what* a
stage says lives in `prompts.py`, so the API path and the agent path are held
to identical instructions.

Two implementations:

* `HyprlabBackend` — an HTTP call to Grok 4.6 on Hyprlab.
* `AgentBackend`   — writes the prompt to disk for a Claude Code agent to
                     execute, and raises `AwaitingAgent` until the answer file
                     appears. The pipeline is resumable, so the driver simply
                     stops, the agent writes, and the driver is re-run.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field


class BackendError(RuntimeError):
    pass


class AwaitingAgent(Exception):
    """Raised by AgentBackend when a prompt is queued but not yet answered."""

    def __init__(self, tag: str, packet_path: str, output_path: str, kind: str):
        super().__init__(f"awaiting agent for {tag}")
        self.tag = tag
        self.packet_path = packet_path
        self.output_path = output_path
        self.kind = kind


@dataclass
class Usage:
    calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    reasoning_tokens: int = 0
    cached_tokens: int = 0
    by_stage: dict = field(default_factory=dict)

    def record(self, stage: str, usage: dict) -> None:
        details = usage.get("completion_tokens_details") or {}
        prompt_details = usage.get("prompt_tokens_details") or {}
        self.calls += 1
        self.input_tokens += usage.get("prompt_tokens", 0)
        self.output_tokens += usage.get("completion_tokens", 0)
        self.reasoning_tokens += details.get("reasoning_tokens", 0)
        self.cached_tokens += prompt_details.get("cached_tokens", 0)
        row = self.by_stage.setdefault(stage, {"calls": 0, "in": 0, "out": 0, "reasoning": 0})
        row["calls"] += 1
        row["in"] += usage.get("prompt_tokens", 0)
        row["out"] += usage.get("completion_tokens", 0)
        row["reasoning"] += details.get("reasoning_tokens", 0)

    def cost(self, per_m_in: float, per_m_out: float) -> float:
        # Reasoning tokens are billed as output even though they are discarded.
        billed_out = self.output_tokens + self.reasoning_tokens
        return (self.input_tokens / 1e6) * per_m_in + (billed_out / 1e6) * per_m_out

    def as_dict(self) -> dict:
        return {
            "calls": self.calls,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "reasoning_tokens": self.reasoning_tokens,
            "cached_tokens": self.cached_tokens,
            "by_stage": self.by_stage,
        }


class Backend:
    name = "base"

    def __init__(self) -> None:
        self.usage = Usage()

    def complete_json(self, system: str, user: str, schema: dict, *, stage: str, tag: str) -> dict:
        raise NotImplementedError

    def complete_text(self, system: str, user: str, *, stage: str, tag: str) -> str:
        raise NotImplementedError


# --------------------------------------------------------------------------

_FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.S)


def extract_json(text: str) -> dict:
    """Recover a JSON document from a model response.

    Models fenced, prefaced and trailing-commented output long before they were
    told not to, and one malformed wrapper should not cost a whole stage.
    """
    text = (text or "").strip()
    if not text:
        raise BackendError("empty response")

    candidates = [text]
    fenced = _FENCE.search(text)
    if fenced:
        candidates.insert(0, fenced.group(1).strip())
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        candidates.append(text[start:end + 1])

    errors = []
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError as exc:
            errors.append(str(exc))
            continue
        if isinstance(parsed, dict):
            return parsed
        errors.append(f"top level is {type(parsed).__name__}, expected object")
    raise BackendError(f"could not parse JSON from response: {errors[0]}")
