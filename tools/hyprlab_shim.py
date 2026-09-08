#!/usr/bin/env python3
"""OpenAI-chat-completions shim for the Hyprlab endpoint.

Why this exists: `EndpointPool` (screenplay_ku.client) hardcodes
`http://127.0.0.1:<port>/v1/chat/completions` and sends no Authorization
header, because it was written for local llama.cpp/vLLM servers. This shim
gives it a local port that forwards to a hosted OpenAI-compatible API with
the key injected, so every layer generator, the trace runner and
build_tree.sh work unchanged via `--ports <shimport>`.

It is the paid-route sibling of `tools/zen_shim.py`, which does the same job
for the OpenCode Zen free tier. Use this one when Zen is unavailable — as of
2026-09-08 Zen's free tier refuses non-OpenCode clients outright
(`MissingSessionID`), so this is the working route to GLM-5.3, which is the
same model Muse 1.2 serves.

Differences from zen_shim, all because the upstream is properly
OpenAI-compatible:
  * `response_format`/`json_schema` is passed through, not embedded in the
    prompt -- GLM-5.3 on this endpoint honours schemas natively.
  * The request body is forwarded near-verbatim; only the model name is
    mapped and unsupported keys are dropped.
  * Upstream failure => HTTP 502, so EndpointPool retries on its own.

Run:  PORT=8300 python3 tools/hyprlab_shim.py &
Env:  PORT (default 8300), HYPR_MODEL (default glm-5.3),
      SHIM_LOG (default <repo>/runs/hyprlab_timing.jsonl),
      HYPRLAB_API_KEY / HYPRLAB_BASE_URL (read from <repo>/.env if unset).
"""
import json
import os
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT = int(os.environ.get("PORT", "8300"))
LOG = os.environ.get("SHIM_LOG", os.path.join(REPO, "runs", "hyprlab_timing.jsonl"))
# Every model name the pipeline asks for is mapped to this one. The pipeline
# passes "muse-spark-1.2-contributor-free" everywhere; Muse 1.2 IS GLM-5.3,
# so the substitution keeps model identity while changing only the route.
MODEL = os.environ.get("HYPR_MODEL", "glm-5.3")
# Keys the upstream rejects or ignores; llama.cpp-specific knobs.
DROP_KEYS = {"chat_template_kwargs"}

_log_lock = threading.Lock()


def _load_env():
    """Read HYPRLAB_* from the environment, falling back to <repo>/.env."""
    key = os.environ.get("HYPRLAB_API_KEY")
    base = os.environ.get("HYPRLAB_BASE_URL")
    if key and base:
        return key, base.rstrip("/")
    path = os.path.join(REPO, ".env")
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            v = v.strip().strip('"').strip("'")
            if k.strip() == "HYPRLAB_API_KEY" and not key:
                key = v
            elif k.strip() == "HYPRLAB_BASE_URL" and not base:
                base = v
    if not key or not base:
        raise SystemExit("HYPRLAB_API_KEY / HYPRLAB_BASE_URL not found")
    return key, base.rstrip("/")


API_KEY, BASE_URL = _load_env()
UPSTREAM = BASE_URL + "/chat/completions"


def log_rec(rec):
    with _log_lock:
        with open(LOG, "a") as f:
            f.write(json.dumps(rec) + "\n")


# The upstream intermittently answers a perfectly valid request with
# 400 "Client-side error detected ... maybe just try again" -- measured:
# identical payloads that fail three times in a row then succeed. Retrying
# here rather than in EndpointPool keeps one flake from burning all three of
# the pool's attempts across all its ports at once.
RETRY_CODES = {400, 408, 429, 500, 502, 503, 504, 529}
RETRIES = int(os.environ.get("HYPR_RETRIES", "4"))


def forward(body):
    """Send one chat-completion upstream and return the parsed response."""
    out = {k: v for k, v in body.items() if k not in DROP_KEYS}
    out["model"] = MODEL
    payload = json.dumps(out).encode("utf-8")
    last = None
    for attempt in range(1, RETRIES + 1):
        req = urllib.request.Request(
            UPSTREAM, data=payload,
            headers={"Content-Type": "application/json",
                     "Authorization": "Bearer " + API_KEY},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=900) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as exc:
            if exc.code not in RETRY_CODES or attempt == RETRIES:
                raise
            last = exc
            log_rec({"t": time.time(), "port": PORT, "status": exc.code,
                     "retry": attempt, "note": "transient, retrying"})
            time.sleep(min(2 ** attempt, 30))
    raise last


class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *_a):  # keep the console quiet
        pass

    def _send(self, code, payload):
        out = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(out)))
        self.end_headers()
        self.wfile.write(out)

    def do_GET(self):
        # EndpointPool.health() probes /v1/models and only checks for 200.
        if self.path.rstrip("/").endswith("/v1/models"):
            self._send(200, {"object": "list",
                             "data": [{"id": MODEL, "object": "model"}]})
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(n) if n else b"{}"
        started = time.time()
        try:
            body = json.loads(raw)
        except Exception as exc:
            self._send(400, {"error": "unparsable request: %s" % exc})
            return
        try:
            parsed = forward(body)
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")[:400]
            log_rec({"t": time.time(), "port": PORT, "status": exc.code,
                     "seconds": round(time.time() - started, 2),
                     "error": detail})
            # 502 (not the upstream code) so EndpointPool treats it as a
            # transient endpoint fault and retries elsewhere in the pool.
            self._send(502, {"error": "upstream %s: %s" % (exc.code, detail)})
            return
        except Exception as exc:
            log_rec({"t": time.time(), "port": PORT, "status": "exc",
                     "seconds": round(time.time() - started, 2),
                     "error": str(exc)[:400]})
            self._send(502, {"error": str(exc)[:400]})
            return
        usage = parsed.get("usage") or {}
        # finish_reason matters more than it looks: EndpointPool rejects
        # "length" outright rather than accepting a truncated artifact, so a
        # 200 here can still cost the caller a full retry. Logging it is the
        # difference between "the model is slow" and "the budget is too low".
        try:
            finish = parsed["choices"][0].get("finish_reason")
        except (KeyError, IndexError, TypeError):
            finish = None
        log_rec({"t": time.time(), "port": PORT, "status": 200,
                 "seconds": round(time.time() - started, 2),
                 "model": parsed.get("model"),
                 "finish_reason": finish,
                 "prompt_tokens": usage.get("prompt_tokens"),
                 "completion_tokens": usage.get("completion_tokens")})
        self._send(200, parsed)


if __name__ == "__main__":
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    print("hyprlab shim on 127.0.0.1:%d -> %s (model %s)"
          % (PORT, UPSTREAM, MODEL), flush=True)
    ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()
