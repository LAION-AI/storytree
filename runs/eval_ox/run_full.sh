#!/bin/bash
# Full-film build 10: all 47 events of the reused segmentation, then two
# complete blind comparisons judged by the same four-judge panel --
#   A) build10_full vs build7_24 over the 23 reference anchors
#      (the historic baseline set; decision-grade n)
#   B) build10_full vs build 8 over their shared anchors (successor check)
# Keys go outside the tree. The paraphrase pass may exit non-zero on residual
# spans; that must not abort the run (build 10 lesson).
set -e
cd /home/deployer/laion/bookwriter

echo "$(date -Is) full: waiting for compose" >> runs/eval_ox/judging.log
while pgrep -f 'distill/event_layer.py' > /dev/null; do sleep 60; done

if [ ! -f runs/events_build10_full/events.json ]; then
    echo "$(date -Is) FULL ABORTED: compose finished without events.json" >> runs/eval_ox/judging.log
    exit 1
fi

python3 distill/paraphrase_pass.py \
    --nodes runs/events_build10_full/events.json \
    --source distill/runs/matrix/script.normalized.txt \
    --ports 8120 --model qwen38-9b \
    --escalate-ports 8110,8111 --escalate-model ornith-1.5-397b \
    --workers 2 --report runs/events_build10_full/paraphrase_report.json \
    >> runs/events_build10_full.log 2>&1 \
    || echo "$(date -Is) paraphrase had residuals; continuing" >> runs/eval_ox/judging.log

ANCHORS=$(python3 -c "
import json
rows = json.load(open('runs/events_build7_24/eval/scores_by_pairing.json'))
print(','.join(r['anchor_scene'] for r in rows))")

echo "$(date -Is) full: pack A vs build7_24 (23 anchors)" >> runs/eval_ox/judging.log
python3 distill/build_event_eval_pack.py \
    --a runs/events_build10_full/events.json \
    --b runs/events_build7_24/events.json \
    --out runs/eval_ox/packfull7 \
    --key-out /home/deployer/eval_keys_ox/packfull7_key \
    --anchors "$ANCHORS" --seed 20260822 >> runs/eval_ox/judging.log 2>&1

python3 distill/judge_events.py --pack runs/eval_ox/packfull7 \
    --out runs/eval_ox/packfull7_scores --scenes-dir runs/scenes_ornith_v5 \
    --ports 8110,8111 --judges 4 >> runs/eval_ox/judging.log 2>&1

echo "$(date -Is) full: pack B vs build8" >> runs/eval_ox/judging.log
python3 distill/build_event_eval_pack.py \
    --a runs/events_build10_full/events.json \
    --b runs/events_build8/events.json \
    --out runs/eval_ox/packfull8 \
    --key-out /home/deployer/eval_keys_ox/packfull8_key \
    --seed 20260822 >> runs/eval_ox/judging.log 2>&1

python3 distill/judge_events.py --pack runs/eval_ox/packfull8 \
    --out runs/eval_ox/packfull8_scores --scenes-dir runs/scenes_ornith_v5 \
    --ports 8110,8111 --judges 4 >> runs/eval_ox/judging.log 2>&1

echo "$(date -Is) FULL-DONE" >> runs/eval_ox/judging.log
