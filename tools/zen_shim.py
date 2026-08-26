#!/usr/bin/env python3
"""OpenAI-chat-completions -> Zen /v1/responses shim for Muse models.

Fixes over v1 (see docs/handshake2.md):
- JSON mode: Muse ignores `response_format`/json_schema (no grammar layer).
  When a request carries a schema, the schema is embedded in the prompt with a
  strict "Respond with ONLY raw JSON" instruction.
- Tolerant parsing: markdown fences stripped, first '{' .. last '}' extracted;
  one in-shim retry with a harder reminder if the payload still is no JSON.
- ThreadingHTTPServer: parallel client requests actually run in parallel.
- Timing: every upstream call is appended to runs/muse_timing.jsonl.
- Upstream failure => HTTP 502 so EndpointPool retries on its own.

Run N instances:  PORT=8222 python3 tools/zen_shim.py &  (etc.)
Env: PORT (default 8222), SHIM_LOG (default <repo>/runs/muse_timing.jsonl).
"""
import json, os, re, threading, time, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ZEN = 'https://opencode.ai/zen/v1/responses'
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = os.environ.get('SHIM_LOG', os.path.join(REPO, 'runs', 'muse_timing.jsonl'))
PORT = int(os.environ.get('PORT', '8222'))
_log_lock = threading.Lock()


def log_rec(rec):
    with _log_lock:
        with open(LOG, 'a') as f:
            f.write(json.dumps(rec) + '\n')


def zen_call(inp, model, temperature=None, top_p=None, max_tokens=None):
    body = {'model': model, 'input': inp}
    if temperature is not None:
        body['temperature'] = temperature
    if top_p is not None:
        body['top_p'] = top_p
    # Headroom x3 so long schema outputs never hit finish=length (client would
    # hard-fail); free-tier muse-spark allows 131k output tokens.
    if max_tokens:
        body['max_output_tokens'] = min(int(max_tokens) * 3, 120000)
    r = urllib.request.Request(ZEN, data=json.dumps(body).encode(),
        headers={'Content-Type': 'application/json',
                 'User-Agent': 'curl/8.5.0'})
    resp = json.loads(urllib.request.urlopen(r, timeout=900).read())
    txt = ''
    for o in resp.get('output', []):
        if o.get('type') == 'message':
            for c in o.get('content', []):
                if isinstance(c, dict) and c.get('text'):
                    txt += c['text']
    return txt, resp.get('usage') or {}


def extract_json(txt):
    """Tolerant extraction: strip code fences, keep first '{' .. last '}'."""
    t = txt.strip()
    m = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', t, re.S)
    if m:
        t = m.group(1)
    i, j = t.find('{'), t.rfind('}')
    if i != -1 and j > i:
        return t[i:j + 1]
    return t

class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        out = json.dumps({'object': 'list', 'data': [{'id': 'zen-shim'}]}).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(out)))
        self.end_headers()
        self.wfile.write(out)

    def do_POST(self):
        n = int(self.headers.get('Content-Length', 0))
        req = json.loads(self.rfile.read(n))
        model = req.get('model', 'muse-spark-1.2-contributor-free')
        msgs = [m for m in req.get('messages', [])
                if isinstance(m.get('content'), str)]
        inp = '\n'.join(f"{m['role']}: {m['content']}" for m in msgs)

        schema = None
        rf = req.get('response_format') or {}
        if rf.get('type') == 'json_schema':
            schema = (rf.get('json_schema') or {}).get('schema')
        if schema is not None:
            inp += ("\n\nOUTPUT FORMAT -- STRICT: Respond with ONLY raw JSON "
                    "(no markdown fences, no prose before or after) matching "
                    "exactly this JSON schema:\n" + json.dumps(schema))

        started = time.time()
        attempts = 0
        err = None
        for attempt in range(2):          # one in-shim retry on unparsable JSON
            attempts += 1
            try:
                txt, usage = zen_call(
                    inp if attempt == 0 else
                    inp + "\n\nREMINDER: your previous reply was not valid "
                    "bare JSON. Output ONLY the JSON object, starting with { "
                    "and ending with }.",
                    model, req.get('temperature'), req.get('top_p'),
                    req.get('max_tokens'))
            except Exception as e:
                err = str(e)
                continue
            cand = extract_json(txt)
            try:
                json.loads(cand)          # must be bare parseable JSON
            except Exception:
                continue
            dur = time.time() - started
            log_rec({'ts': time.strftime('%FT%T'), 'port': PORT,
                     'model': model, 'dur_s': round(dur, 2),
                     'attempts': attempts, 'prompt_chars': len(inp),
                     'out_chars': len(txt),
                     'prompt_tokens': usage.get('input_tokens'),
                     'completion_tokens': usage.get('output_tokens'),
                     'ok': True})
            out = json.dumps({'id': 'shim', 'object': 'chat.completion',
                'model': model, 'choices': [{'index': 0, 'message':
                {'role': 'assistant', 'content': cand},
                'finish_reason': 'stop'}]}).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(out)))
            self.end_headers()
            self.wfile.write(out)
            return
        dur = time.time() - started
        log_rec({'ts': time.strftime('%FT%T'), 'port': PORT, 'model': model,
                 'dur_s': round(dur, 2), 'attempts': attempts,
                 'prompt_chars': len(inp), 'ok': False, 'error': err})
        body = json.dumps({'error': {'message':
                           f'zen shim failed after {attempts} tries: '
                           f'{err or "unparsable JSON"}'}}).encode()
        self.send_response(502)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)


ThreadingHTTPServer(('127.0.0.1', PORT), H).serve_forever()
