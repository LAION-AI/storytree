#!/usr/bin/env bash
# Quota watcher: polls the free tier every 30 min and starts the resume
# batch (--clean-errors) the moment quota is back.
# Usage: OPENCODE_API_KEY=sk-... bash reasoning_traces/quota_watch.sh \
#            --hf-dir ... --out-dir ...
# Runs forever until quota returns and the batch is launched.
set -u
HF_DIR=""; OUT_DIR=""
while [ $# -gt 0 ]; do
  case "$1" in
    --hf-dir) HF_DIR="$2"; shift 2;;
    --out-dir) OUT_DIR="$2"; shift 2;;
    *) echo "unknown arg: $1" >&2; exit 2;;
  esac
done
[ -n "$HF_DIR" ] && [ -n "$OUT_DIR" ] || { echo "missing --hf-dir/--out-dir" >&2; exit 2; }
[ -n "${OPENCODE_API_KEY:-}" ] || { echo "OPENCODE_API_KEY not set" >&2; exit 2; }
HERE="$(cd "$(dirname "$0")/.." && pwd)"

while true; do
  if python3 -c "
import sys; sys.path.insert(0, '$HERE/reasoning_traces')
from zen_client import ZenClient
try:
    t, u = ZenClient().generate('Reply with exactly: PONG', max_output_tokens=64)
    print('quota back:', repr(t[:60]))
except Exception as e:
    print('waiting:', str(e)[:120])
    sys.exit(1)
"; then
    echo "quota is back -- launching resume batch"
    export WORKERS=4
    bash "$HERE/reasoning_traces/topdown_batch.sh" \
      --hf-dir "$HF_DIR" --out-dir "$OUT_DIR" --clean-errors
    echo "batch exited: $?"
    exit 0
  fi
  echo "next probe in 30 min ($(date -u +%FT%TZ))"
  sleep 1800
done
