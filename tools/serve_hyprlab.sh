#!/usr/bin/env bash
# Start N Hyprlab shims (see tools/hyprlab_shim.py) on consecutive ports and
# wait until each answers its health probe.
#
#   tools/serve_hyprlab.sh [first_port] [count]   # default: 8300 3
#
# Stop them with:  pkill -f serve_hyprlab_worker
# (deliberately NOT "pkill -f hyprlab_shim": that pattern also matches the
# shell invoking it, which kills the caller and orphans nothing useful.)
set -uo pipefail
cd "$(dirname "$0")/.."
FIRST="${1:-8300}"
COUNT="${2:-3}"
mkdir -p runs

for i in $(seq 0 $((COUNT - 1))); do
  P=$((FIRST + i))
  if curl -s -m 3 -o /dev/null "http://127.0.0.1:$P/v1/models"; then
    echo "port $P: already serving"
    continue
  fi
  # exec -a renames the process so pkill can target the fleet precisely
  ( PORT=$P setsid bash -c 'exec -a serve_hyprlab_worker python3 tools/hyprlab_shim.py' \
      > "runs/hyprshim_$P.log" 2>&1 < /dev/null & )
done

for i in $(seq 0 $((COUNT - 1))); do
  P=$((FIRST + i))
  for _ in $(seq 1 20); do
    code=$(curl -s -m 3 -o /dev/null -w '%{http_code}' "http://127.0.0.1:$P/v1/models" || true)
    [ "$code" = 200 ] && break
    sleep 1
  done
  echo "port $P: ${code:-000}"
done
