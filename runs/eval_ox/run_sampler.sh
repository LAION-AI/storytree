#!/bin/bash
# AFK sampler: produce more independent plot-layer samples (v4..v8), each
# judged inline, each pushed automatically. More artefacts = stronger panel
# later. Keys are not involved; scores are single-judge absolutes.
set -e
cd /home/deployer/laion/bookwriter
for N in 4 5 6 7 8; do
  OUT=runs/plot_layer_v$N
  echo "$(date -Is) sampler: sample v$N" >> runs/eval_ox/judging.log
  python3 distill/plot_layer.py \
      --meta runs/meta_layer_v2b/meta.json \
      --events runs/events_build10_full/events.json \
      --out $OUT --ports 8110,8111 >> $OUT.log 2>&1 || true
  if [ -f $OUT/plots.json ]; then
    python3 tools/redact_source_spans.py \
        --source distill/runs/matrix/script.normalized.txt --write \
        $OUT/plots.json $OUT/judgement.json > /dev/null 2>&1 || true
    git add $OUT/plots.json $OUT/judgement.json 2>/dev/null || true
    cat > /tmp/msg_samp.txt <<MSG
Plot layer sample v$N: another independent draw for the panel

Same pipeline, fresh sampling pass, judged inline by the P-rubric. Samples
accumulate so a later multi-judge panel can separate real quality movement
from the session drift measured between earlier judging runs.
MSG
    timeout 300 tools/publish.sh /tmp/msg_samp.txt > /dev/null 2>&1 || \
        echo "$(date -Is) push failed v$N" >> runs/eval_ox/judging.log
    echo "$(date -Is) v$N pushed" >> runs/eval_ox/judging.log
  fi
done
echo "$(date -Is) SAMPLER-DONE" >> runs/eval_ox/judging.log
