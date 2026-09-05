#!/usr/bin/env python3
"""Minimal client for the OpenCode Zen responses API (stdlib only).

The key is NEVER stored here. It is read from the environment
(`OPENCODE_API_KEY`) at call time. Do not paste keys into scripts that
might be committed -- export the variable in your shell instead:

    export OPENCODE_API_KEY=sk-...
    python3 topdown_generate.py --hf-dir ... --film ...

Verified 2026-09-05 against https://opencode.ai/zen/v1:
  GET  /models                       -> {"object": "list", "data": [{"id": ...}]}
  POST /responses {model, instructions, input, max_output_tokens}
    -> {"status": "completed", "output": [{"type": "reasoning", ...},
        {"type": "message", "content": [{"type": "output_text", "text": ...}]}]}
"""

import json
import os
import time
import urllib.error
import urllib.request

BASE = "https://opencode.ai/zen/v1"
DEFAULT_MODEL = "muse-spark-1.3-contributor-free"


class ZenError(Exception):
    pass


class ZenClient:
    def __init__(self, model=DEFAULT_MODEL, api_key=None, base=BASE,
                 timeout=600, retries=3):
        self.model = model
        self.api_key = api_key or os.environ.get("OPENCODE_API_KEY")
        if not self.api_key:
            raise SystemExit("OPENCODE_API_KEY is not set. Export it first:\n"
                             "    export OPENCODE_API_KEY=sk-...")
        self.base = base.rstrip("/")
        self.timeout = timeout
        self.retries = retries

    def generate(self, user, instructions=None, max_output_tokens=4096):
        """One reasoning+answer call. Returns (text, usage dict)."""
        body = {"model": self.model, "input": user,
                "max_output_tokens": max_output_tokens}
        if instructions:
            body["instructions"] = instructions
        last = None
        for attempt in range(self.retries + 1):
            try:
                req = urllib.request.Request(
                    self.base + "/responses",
                    data=json.dumps(body).encode("utf-8"),
                    headers={"Authorization": "Bearer " + self.api_key,
                             "Content-Type": "application/json",
                             # Cloudflare in front of the API answers 1010
                             # to non-browser UAs (incl. Python-urllib).
                             "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) "
                                           "AppleWebKit/537.36 (KHTML, like Gecko) "
                                           "Chrome/126.0 Safari/537.36"})
                with urllib.request.urlopen(req, timeout=self.timeout) as r:
                    doc = json.loads(r.read().decode("utf-8"))
                return _extract(doc)
            except urllib.error.HTTPError as e:
                try:
                    detail = e.read().decode("utf-8")[:300]
                except Exception:
                    detail = ""
                last = ZenError("HTTP %s %s" % (e.code, detail))
                if e.code not in (429, 500, 502, 503, 529):
                    raise last
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
                last = ZenError("transport: %r" % (e,))
            time.sleep(2 * (attempt + 1))
        raise last


def _extract(doc):
    if doc.get("type") == "error" or doc.get("error"):
        raise ZenError("api error: %s" % json.dumps(doc)[:300])
    texts = []
    for item in doc.get("output", []) or []:
        if item.get("type") != "message":
            continue
        for c in item.get("content", []) or []:
            if c.get("type") == "output_text" and c.get("text"):
                texts.append(c["text"])
    if not texts and doc.get("status") != "completed":
        raise ZenError("incomplete response, status=%s" % doc.get("status"))
    return "\n".join(texts), doc.get("usage", {}) or {}
