#!/bin/bash
# The plot layer's prerequisite: once the full-film build 10 is composed AND
# judged (FULL-DONE from run_full.sh), identify the meta layer -- big
# questions, central dilemma, external and internal conflicts, relationship
# arcs, perspectives -- and judge it against distill/rubrics/meta.json.
# The plots themselves are written only after a human reads the judgement.
set -e
cd /home/deployer/laion/bookwriter

# Wait for the END of run_full.sh, signalled by its LAST score file.
# (The first version grepped this log for FULL-DONE -- and matched its own
# echo of that word, line 99, so it started before the film was composed.)
echo "$(date -Is) meta: waiting for packfull8 scores" >> runs/eval_ox/judging.log
while [ ! -f runs/eval_ox/packfull8_scores/scores_jox4.json ]; do sleep 120; done

echo "$(date -Is) meta: building meta layer" >> runs/eval_ox/judging.log
python3 distill/meta_layer.py \
    --events runs/events_build10_full/events.json \
    --scenes-dir runs/scenes_ornith_v5 \
    --out runs/meta_layer \
    --ports 8110,8111 >> runs/meta_layer.log 2>&1

echo "$(date -Is) meta: judging" >> runs/eval_ox/judging.log
python3 distill/judge_meta.py \
    --meta runs/meta_layer/meta.json \
    --events runs/events_build10_full/events.json \
    --out runs/meta_layer/judgement.json >> runs/meta_layer.log 2>&1

echo "$(date -Is) META-DONE" >> runs/eval_ox/judging.log
