"""Grok 4.6 via the Hyprlab OpenAI-compatible endpoint."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import requests

from .base import Backend, BackendError, extract_json

DEFAULT_BASE_URL = "https://api.hyprlab.io/v1"
DEFAULT_MODEL = "grok-4.6"

# Indicative published rates for grok-4.6 at <=200K context, in USD per 1M tokens.
PRICE_IN = 1.80
PRICE_OUT = 5.40


def load_env(path: str | Path = ".env") -> None:
    """Minimal .env loader — the target boxes have no python-dotenv."""
    env_path = Path(path)
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("'\""))



# Guided-decoding backends compile a JSON Schema into a grammar, and they do not
# all support the whole vocabulary. vLLM/xgrammar returns HTTP 500 with an EMPTY
# error message on `propertyNames` — no hint about which construct or where, and
# the request had already retried four times before failing the stage.
#
# Isolated by bisection: `propertyNames` alone reproduces it; removing it from
# the identical schema returns 200.
#
# Stripping it loosens what the *grammar* enforces, not what we accept:
# jsonschema_mini still checks the full schema after the call, so a key that
# violates the pattern is caught by validation instead of being made
# ungrammatical. That is a worse guarantee and an acceptable one.
GRAMMAR_UNSUPPORTED = ("propertyNames", "dependentRequired", "dependentSchemas",
                       "unevaluatedProperties", "unevaluatedItems", "if", "then", "else")


def strip_unsupported(schema):
    """Remove keywords a grammar compiler may not implement. Non-destructive."""
    if isinstance(schema, dict):
        return {k: strip_unsupported(v) for k, v in schema.items()
                if k not in GRAMMAR_UNSUPPORTED}
    if isinstance(schema, list):
        return [strip_unsupported(v) for v in schema]
    return schema


class HyprlabBackend(Backend):
    name = "hyprlab"

    def __init__(
        self,
        model: str | None = None,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        temperature: float = 0.85,
        max_tokens: int = 32000,
        reasoning_effort: str | None = None,
        response_format: str = "json_object",
        max_retries: int = 4,
        log_dir: Path | None = None,
        timeout: int = 1800,
    ) -> None:
        super().__init__()
        load_env()
        self.model = model or os.environ.get("NF_MODEL", DEFAULT_MODEL)
        self.api_key = api_key or os.environ.get("HYPRLAB_API_KEY", "")
        self.base_url = (base_url or os.environ.get("HYPRLAB_BASE_URL", DEFAULT_BASE_URL)).rstrip("/")
        self._is_local = ("127.0.0.1" in self.base_url or "localhost" in self.base_url)
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.reasoning_effort = reasoning_effort
        self.response_format = response_format
        self.max_retries = max_retries
        self.timeout = timeout
        self.log_dir = Path(log_dir) if log_dir else None
        if not self.api_key:
            raise BackendError("HYPRLAB_API_KEY is not set (put it in bookwriter/.env)")

    # ----------------------------------------------------------------------

    def _payload(self, system: str, user: str, schema: dict | None, *, json_mode: bool) -> dict:
        payload: dict = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": self.temperature,
            "max_completion_tokens": self.max_tokens,
        }
        if self.reasoning_effort and not (self._is_local and self.reasoning_effort == "none"):
            # "none" is GLM-specific. Qwen3.8's template accepts only
            # xhigh|medium|low and RAISES on anything else, turning the request
            # into a 400. The chat_template_kwargs form below switches thinking
            # off structurally and is understood by both, so for local endpoints
            # that is the only signal sent.
            payload["reasoning_effort"] = self.reasoning_effort
        if self._is_local:
            # llama.cpp's OpenAI shim reads `max_tokens`, not `max_completion_tokens`.
            # Sending only the latter leaves generation at the server default, which
            # truncates a 25k-token entities document without any error.
            payload["max_tokens"] = self.max_tokens
            # Reuse the KV cache for the shared prefix. Measured on this deployment:
            # a repeated 50k prefix costs 0.064 s instead of 193.7 s.
            payload["cache_prompt"] = True
            if self.reasoning_effort in ("none", "off", None):
                # Belt and braces. This GGUF's chat template maps every value that is
                # not the literal string 'high' to *max*, so "low"/"minimal" silently
                # select the most expensive setting. Only "none" (a llama.cpp special
                # case) and this kwarg actually suppress thinking.
                payload["chat_template_kwargs"] = {"enable_thinking": False}
        if json_mode:
            if self.response_format == "json_schema" and schema is not None:
                payload["response_format"] = {
                    "type": "json_schema",
                    "json_schema": {"name": "artifact", "strict": False,
                                    "schema": strip_unsupported(schema) if self._is_local
                                    else schema},
                }
            else:
                payload["response_format"] = {"type": "json_object"}
        return payload

    def _post(self, payload: dict, stage: str, tag: str) -> str:
        url = f"{self.base_url}/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        last_error: Exception | None = None

        for attempt in range(1, self.max_retries + 1):
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
            except requests.RequestException as exc:
                last_error = exc
                time.sleep(min(60, 4 * 2 ** attempt))
                continue

            if response.status_code == 200:
                data = response.json()
                choice = data["choices"][0]
                content = choice["message"].get("content") or ""
                self.usage.record(stage, data.get("usage", {}) or {})
                self._log(tag, payload, data)
                if choice.get("finish_reason") == "length":
                    raise BackendError(
                        f"{tag}: hit the {self.max_tokens}-token output cap. Raise --max-tokens "
                        f"or reduce the batch size for this stage."
                    )
                if not content.strip():
                    last_error = BackendError(f"{tag}: empty content, finish_reason="
                                              f"{choice.get('finish_reason')}")
                    continue
                return content

            if response.status_code in (400, 404, 422, 500) and "json_schema" in json.dumps(payload):
                # The endpoint rejected the schema; degrade to plain JSON mode.
                payload = dict(payload, response_format={"type": "json_object"})
                last_error = BackendError(f"schema rejected ({response.status_code}); retrying in json_object mode")
                continue

            if response.status_code in (408, 409, 429, 500, 502, 503, 504, 529):
                last_error = BackendError(f"HTTP {response.status_code}: {response.text[:400]}")
                time.sleep(min(90, 5 * 2 ** attempt))
                continue

            raise BackendError(f"{tag}: HTTP {response.status_code}: {response.text[:800]}")

        raise BackendError(f"{tag}: exhausted {self.max_retries} attempts — {last_error}")

    def _log(self, tag: str, payload: dict, data: dict) -> None:
        if not self.log_dir:
            return
        self.log_dir.mkdir(parents=True, exist_ok=True)
        record = {
            "tag": tag,
            "model": self.model,
            "usage": data.get("usage"),
            "finish_reason": data["choices"][0].get("finish_reason"),
            "prompt_chars": sum(len(m["content"]) for m in payload["messages"]),
            "response": data["choices"][0]["message"].get("content"),
            "reasoning": data["choices"][0]["message"].get("reasoning_content"),
        }
        (self.log_dir / f"{tag.replace('/', '_')}.json").write_text(
            json.dumps(record, indent=1, ensure_ascii=False)
        )

    # ----------------------------------------------------------------------

    def complete_json(self, system: str, user: str, schema: dict, *, stage: str, tag: str) -> dict:
        content = self._post(self._payload(system, user, schema, json_mode=True), stage, tag)
        return extract_json(content)

    def complete_text(self, system: str, user: str, *, stage: str, tag: str) -> str:
        content = self._post(self._payload(system, user, None, json_mode=False), stage, tag)
        return content.strip()

    def cost_usd(self) -> float:
        return self.usage.cost(PRICE_IN, PRICE_OUT)
