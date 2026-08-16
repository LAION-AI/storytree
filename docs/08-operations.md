# Operations

## Requirements

Python 3.11+. The core needs only the standard library — JSON Patch, JSON Pointer and a
JSON Schema subset are hand-rolled so the pipeline runs on a bare interpreter. `requests`
for HTTP backends.

## Configuration

Secrets live in `.env` at the repo root, `chmod 600`, gitignored. Never commit them,
never bake them into a published page. The web app's chat co-writer stores its key in
browser localStorage only.

```
HYPRLAB_API_KEY=...
HYPRLAB_BASE_URL=https://api.hyprlab.io/v1     # or http://127.0.0.1:8099/v1
NF_MODEL=grok-4.6
```

Any OpenAI-compatible endpoint works. The backend detects `127.0.0.1`/`localhost` and
adjusts the request body accordingly — see below.

## Local-endpoint quirks that cost real time

**`max_completion_tokens` is ignored by llama.cpp.** It reads `max_tokens`. Sending only
the former leaves generation at the server default, which truncates a 25k-token document
with no error. The backend sends both when talking to a local endpoint.

**`reasoning_effort: "low"` is a silent no-op on GLM-5.2** and actually selects *maximum*
effort. Only `"none"` or `chat_template_kwargs: {"enable_thinking": false}` work. The CLI
accepts `--reasoning-effort none` for this reason; there is deliberately no `low` option
in the A/B harness, because a condition that silently does nothing produces a
clean-looking experiment with two identical arms.

**`-np N` divides the context window.** `-c 262144 -np 8` gives each call 32,768 tokens.
A 23k prompt then leaves 9.5k for the answer and generation stops mid-sentence. Since
concurrency measurably buys nothing on a sparse MoE, use `-np 1`.

**Put stable content first in the prompt.** The KV cache matches on a byte-identical
prefix. A large schema block placed *after* the varying material is re-processed on every
call.

## Running

```bash
# forward
python3 -m narrativeforge --project runs/x run --brief briefs/x.md \
    --backend hyprlab --model MODEL --response-format json_schema \
    --max-tokens 60000 --reasoning-effort none
python3 -m narrativeforge --project runs/x forge --max-tokens 60000 --reasoning-effort none

# inspect
python3 -m narrativeforge --project runs/x validate
python3 -m narrativeforge --project runs/x state --entity ch-01 --at sc-012
python3 -m narrativeforge --project runs/x timeline
python3 -m narrativeforge --project runs/x report

# publish
python3 -m narrativeforge --project runs/x site --out runs/x/site
python3 -m narrativeforge shelf --out site runs/x:written:MODEL
```

Completed stages are skipped on re-run, so an interrupted run resumes. To redo a stage,
move its artifact out of `artifacts/` — do not delete it; the broken version is often the
most informative thing you have.

## Tests

```bash
python3 tests/test_engine.py
```

52 tests. The number to watch is not "52 passed" but the **injected-error detection
rate**: 23 of 23. A validator that never fires is indistinguishable from a broken one.

## Long runs

Launch through a script with `nohup`, never with an inline `pkill`-able command line —
`pkill -f <pattern>` matches the shell running it and kills the launcher. Use the bracket
trick (`pgrep -f 'run_[l]ocal'`) or kill by PID.

Python buffers stdout when redirected. Use `python3 -u` or the log will look frozen while
the job is fine.

Expect repair loops on the entity layer. If violations *rise* across attempts, that used
to be silently saved; it is now rejected and the previous document kept
(`05-model-behaviour.md` §5).

## Estimating a run

Measured unit costs, local GLM-5.2 at 24.26 tok/s decode / 185.9 prefill, thinking off:

```
hours ≈ 1.3                             (upper layers, length-independent)
      + N × 22,679 / 24.26 / 3600       (scenes, scaffolded)
      + N × 148,400 × c / 185.9 / 3600  (prefill; c = 0.15 warm, 1.0 cold)

      × 6.1  if hidden reasoning is left on
```

A 224-scene feature is ~66 h scaffolded with a warm cache, ~108 h cold. Do not plan to
recover that with parallelism — aggregate throughput is flat from 1 to 8 concurrent
requests on this architecture.

## Publishing

`serve.py` serves a directory on localhost with no-cache headers; a Cloudflare quick
tunnel exposes it. The tunnel's subdomain does not survive a `cloudflared` restart.

Always set `<meta charset="utf-8">`. `http.server` sends `text/html` with no charset and
the page will mangle.

For reconstructions, build viewers with `include_prose=False`.
