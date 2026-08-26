#!/bin/bash
# Full storytree pipeline against Muse 1.2 via the Zen shim (tools/zen_shim.py),
# with per-stage wall-time tracking -> runs/muse_pipeline_timing.md
# Shims must be running: PORT=8222..8224 python3 tools/zen_shim.py &
set -euo pipefail
cd "$(dirname "$0")/.."
PORTS="${PORTS:-8222,8223,8224}"
MODEL="${MODEL:-muse-spark-1.2-contributor-free}"
EV=runs/events_build10_full/events.json
META=runs/meta_layer_v2b/meta.json
ENTS=runs/entity_trial_v2/profiles.json
ROOTOUT=runs/story_root_muse
PLOTDIR=runs/plot_layer_muse
EXPOUT=runs/expose_muse
GATE="python3 tools/pipeline_gate.py"
TIMING=runs/muse_pipeline_timing.md

: > "$TIMING"
echo "# Storytree x Muse pipeline — $(date -Is)" >> "$TIMING"
echo "| stage | wall time |" >> "$TIMING"
echo "|---|---|" >> "$TIMING"

stage() {
  local name="$1"; shift
  local t0=$(date +%s)
  echo "== [$name] start $(date -Is) =="
  "$@" 2>&1 | tee "runs/muse_${name}.log" | grep -v '^$' || true
  local rc=${PIPESTATUS[0]}
  local t1=$(date +%s)
  echo "| $name | $((t1 - t0))s |" >> "$TIMING"
  echo "== [$name] done in $((t1 - t0))s (rc=$rc) =="
  [ "$rc" -eq 0 ] || { echo "STAGE FAILED: $name"; exit "$rc"; }
}

T0=$(date +%s)

echo "== stage 0: pre-run gate on ornith baseline =="
$GATE --plots runs/plot_layer_v8/plots_covered.json >/dev/null \
  || { echo 'gate failed pre-run'; exit 1; }

stage root python3 distill/root_layer.py \
  --script distill/runs/matrix/script.normalized.txt \
  --events "$EV" --meta "$META" --entities "$ENTS" \
  --out "$ROOTOUT" --ports "$PORTS" --model "$MODEL"

stage plots python3 distill/plot_layer.py \
  --meta "$META" --events "$EV" \
  --out "$PLOTDIR" --ports "$PORTS" --model "$MODEL"

MUSE_PORTS="$PORTS" MUSE_MODEL="$MODEL" \
  stage cover python3 tools/plot_cover.py \
    "$PLOTDIR/plots.json" "$PLOTDIR/plots_covered.json"

echo "== gate on muse plots_covered =="
$GATE --plots "$PLOTDIR/plots_covered.json"

stage expose python3 distill/expose_layer.py \
  --root "$ROOTOUT/story_root.json" --events "$EV" \
  --meta "$META" --entities "$ENTS" \
  --out "$EXPOUT" --ports "$PORTS" --model "$MODEL"

stage explorer_data python3 tools/build_explorer_data.py
$GATE --plots "$PLOTDIR/plots_covered.json" >/dev/null

T1=$(date +%s)
echo "| TOTAL | $((T1 - T0))s |" >> "$TIMING"
echo "PIPELINE COMPLETE — total $((T1 - T0))s (see $TIMING, runs/muse_timing.jsonl)"
