#!/bin/bash
# Full storytree pipeline with hard gates between stages.
# Any gate failure aborts the pipeline -- a dropped event or unplotted scene
# can never silently reach the next layer (see tools/pipeline_gate.py).
set -euo pipefail
cd "$(dirname "$0")/.."
PORTS="${PORTS:-8110,8111}"
EV=runs/events_build10_full/events.json
SEG=runs/events_build10_full/segmentation.json
META=${META:-runs/meta_layer_v2b/meta.json}
ENTS=${ENTS:-runs/entity_trial_v2/profiles.json}
PLOTDIR=${PLOTDIR:-runs/plot_layer_v8}
ROOTOUT=${ROOTOUT:-runs/story_root_v3}
EXPOUT=${EXPOUT:-runs/expose_v1}
GATE="python3 tools/pipeline_gate.py"

echo "== stage 0: event-layer integrity (segmentation vs events vs scenes) =="
$GATE --plots "$PLOTDIR/plots_covered.json" >/dev/null || { echo 'gate failed pre-run'; exit 1; }

if [ "${SKIP_PLOTS:-0}" != 1 ]; then
  echo "== stage 1: plot layer =="
  python3 distill/plot_layer.py --meta "$META" --events "$EV" \
      --out "$PLOTDIR" --ports "$PORTS"
  echo "== stage 1b: coverage repair (every event >=1 plot) =="
  python3 tools/plot_cover.py "$PLOTDIR/plots.json" "$PLOTDIR/plots_covered.json"
fi

echo "== stage 2: GATE on events + covered plots =="
$GATE --plots "$PLOTDIR/plots_covered.json"

if [ "${SKIP_ROOT:-0}" != 1 ]; then
  echo "== stage 3: story root =="
  python3 distill/root_layer.py --script distill/runs/matrix/script.normalized.txt \
      --events "$EV" --meta "$META" --entities "$ENTS" --out "$ROOTOUT" --ports "$PORTS"
fi
if [ "${SKIP_EXPOSE:-0}" != 1 ]; then
  echo "== stage 4: expose =="
  python3 distill/expose_layer.py --root "$ROOTOUT/story_root.json" --events "$EV" \
      --meta "$META" --entities "$ENTS" --out "$EXPOUT" --ports "$PORTS"
fi

echo "== stage 5: explorer data + final gate =="
python3 tools/build_explorer_data.py
$GATE --plots "$PLOTDIR/plots_covered.json" >/dev/null
echo "PIPELINE COMPLETE"
