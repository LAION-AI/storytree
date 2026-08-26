#!/usr/bin/env bash
# Best-of-N (muse one-pass samples) + two-pass v3 (both composers) + one
# final GLM panel over every new arm. Shims (8222-8224) are the shared
# bottleneck, so everything muse-side runs sequentially here; v3-ornith
# runs in parallel on 8110 (launched separately).
set -uo pipefail
cd "$(dirname "$0")/.."
MUSE="--ports 8222,8223,8224 --model muse-spark-1.2-contributor-free"
EV="--events runs/events_build10_full/events.json"
META="--meta runs/meta_layer_v2b/meta.json"

echo "== best-of-N: 4 fresh muse one-pass samples"
for i in 2 3 4 5; do
  echo "-- sample $i"
  python3 distill/plot_layer.py $META $EV \
    --out runs/plot_layer_muse_s$i $MUSE || echo "sample $i FAILED"
done

echo "== two-pass v3 with muse"
python3 distill/plot_layer_twopass.py $META $EV --seed throughline \
  --out runs/plot_layer_twopass_v3_muse $MUSE || echo "v3-muse FAILED"

echo "== waiting for v3-ornith (runs on 8110 in parallel)"
for _ in $(seq 1 120); do
  [ -f runs/plot_layer_twopass_v3_ornith/judgement.json ] && break
  sleep 30
done

echo "== final panel over all new arms"
ARMS='{'
for spec in \
  'v8_refined:runs/plot_layer_v8_refined/plots.json' \
  'muse_s2:runs/plot_layer_muse_s2/plots.json' \
  'muse_s3:runs/plot_layer_muse_s3/plots.json' \
  'muse_s4:runs/plot_layer_muse_s4/plots.json' \
  'muse_s5:runs/plot_layer_muse_s5/plots.json' \
  'v3_muse:runs/plot_layer_twopass_v3_muse/plots.json' \
  'v3_ornith:runs/plot_layer_twopass_v3_ornith/plots.json'; do
  name="${spec%%:*}"; path="${spec#*:}"
  [ -f "$path" ] && ARMS+="\"$name\": {\"plots\": \"$path\"},"
done
ARMS="${ARMS%,}}"
echo "panel arms: $ARMS"
python3 tools/glm_panel_judge.py --out runs/glm53_panel_experiments \
  --ports 8222,8223,8224 --model muse-spark-1.2-contributor-free \
  --layers plots --arms "$ARMS"
echo "== ALL DONE"
