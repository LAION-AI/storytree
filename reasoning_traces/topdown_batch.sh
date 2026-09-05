#!/usr/bin/env bash
# Batch runner: top-down traces for every film with a complete tree,
# via the OpenCode Zen API (model muse-spark-1.3-contributor-free).
#
# Per film it runs the full T1..T9 chain (max 5 traces per step).
# Judging is OPT-IN (--judge): judge calls cost ~3x the generation and are
# for test runs only, not for the production batch.
#
# The key is NEVER stored here -- it must be in the environment:
#     export OPENCODE_API_KEY=sk-...
#
# Usage:
#   bash reasoning_traces/topdown_batch.sh \
#       --hf-dir /path/to/hf-dataset --out-dir /path/to/out
#   # ...with the 3-judge panel (test runs only):
#   bash reasoning_traces/topdown_batch.sh \
#       --hf-dir ... --out-dir ... --judge
#   # test with a single film first:
#   bash reasoning_traces/topdown_batch.sh \
#       --hf-dir ... --out-dir ... --films awesomefilm__04385ea70696
#   # or cap the number of films:
#   bash reasoning_traces/topdown_batch.sh --hf-dir ... --out-dir ... --max-films 3
#   # dry run: just list the films that would run:
#   bash reasoning_traces/topdown_batch.sh --hf-dir ... --out-dir ... --list-films
#
# Env overrides: PER_LAYER (default 5), ZEN_MODEL, MAX_TOKENS (default 8192).
set -u

HF_DIR=""; OUT_DIR=""; FILMS=""; MAX_FILMS=""; JUDGE=""; LIST_ONLY=""
while [ $# -gt 0 ]; do
  case "$1" in
    --hf-dir) HF_DIR="$2"; shift 2;;
    --out-dir) OUT_DIR="$2"; shift 2;;
    --films) FILMS="$2"; shift 2;;        # space-separated slugs
    --max-films) MAX_FILMS="$2"; shift 2;;
    --judge) JUDGE=1; shift;;
    --list-films) LIST_ONLY=1; shift;;
    *) echo "unknown arg: $1" >&2; exit 2;;
  esac
done

[ -n "$HF_DIR" ] || { echo "missing --hf-dir" >&2; exit 2; }
[ -n "$OUT_DIR" ] || { echo "missing --out-dir" >&2; exit 2; }

PER_LAYER="${PER_LAYER:-5}"
WORKERS="${WORKERS:-4}"
ZEN_MODEL="${ZEN_MODEL:-muse-spark-1.3-contributor-free}"
MAX_TOKENS="${MAX_TOKENS:-8192}"
HERE="$(cd "$(dirname "$0")/.." && pwd)"

mkdir -p "$OUT_DIR/gen" "$OUT_DIR/judge" "$OUT_DIR/logs"

if [ -n "$FILMS" ]; then
  # shellcheck disable=SC2206
  SLUGS=($FILMS)
else
  mapfile -t SLUGS < <(python3 -c "
import glob, os
print('\n'.join(sorted(os.path.basename(p)[:-5]
      for p in glob.glob('$HF_DIR/data/*.json'))))")
fi
if [ -n "$MAX_FILMS" ]; then
  SLUGS=("${SLUGS[@]:0:$MAX_FILMS}")
fi

echo "films: ${#SLUGS[@]}  per_layer: $PER_LAYER  workers: $WORKERS  model: $ZEN_MODEL  judge: ${JUDGE:-off}"
echo "out: $OUT_DIR"

if [ -n "$LIST_ONLY" ]; then
  printf '%s\n' "${SLUGS[@]}"
  exit 0
fi

[ -n "${OPENCODE_API_KEY:-}" ] || {
  echo "OPENCODE_API_KEY is not set. Export it first." >&2; exit 2; }

n_ok=0; n_fail=0
for slug in "${SLUGS[@]}"; do
  gen="$OUT_DIR/gen/$slug.jsonl"
  judge="$OUT_DIR/judge/$slug.jsonl"
  log="$OUT_DIR/logs/$slug.log"
  {
    echo "=== $slug $(date -u +%FT%TZ) ==="
    python3 "$HERE/reasoning_traces/topdown_generate.py" \
      --hf-dir "$HF_DIR" --film "$slug" \
      --out "$gen" --per-layer "$PER_LAYER" --workers "$WORKERS" \
      --model "$ZEN_MODEL" --max-tokens "$MAX_TOKENS" || {
        echo "GENERATE FAILED for $slug"; exit 1; }
    if [ -n "$JUDGE" ]; then
      python3 "$HERE/reasoning_traces/topdown_judge.py" \
        --in "$gen" --out "$judge" \
        --model "$ZEN_MODEL" --max-tokens "$MAX_TOKENS" || {
          echo "JUDGE FAILED for $slug"; exit 1; }
    fi
    echo "=== $slug DONE $(date -u +%FT%TZ) ==="
  } >>"$log" 2>&1
  if [ $? -eq 0 ]; then
    n_ok=$((n_ok+1)); echo "ok    $slug"
  else
    n_fail=$((n_fail+1)); echo "FAIL  $slug  (see $log)"
  fi
done

echo "done: $n_ok ok, $n_fail failed"
