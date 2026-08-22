#!/bin/bash
# Orchestrate the second half of the build-8 evaluation. Launched detached;
# waits for the compose to finish, then gives build 8 the SAME post-processing
# build 7 got (span-level paraphrase pass), builds the blind pack against
# build7_24 on shared anchors, and hands it to the same four-judge panel that
# re-judged the baseline. The KEY goes outside the repo, where judges never go.
set -e
cd /home/deployer/laion/bookwriter

echo "$(date -Is) waiting for compose to finish" >> runs/eval_ox/judging.log
while pgrep -f 'distill/event_layer.py' > /dev/null; do sleep 60; done

if [ ! -f runs/events_build8/events.json ]; then
    echo "$(date -Is) COMPOSE FINISHED WITHOUT events.json — aborting" >> runs/eval_ox/judging.log
    exit 1
fi
echo "$(date -Is) compose done; paraphrase pass" >> runs/eval_ox/judging.log

python3 distill/paraphrase_pass.py \
    --nodes runs/events_build8/events.json \
    --source distill/runs/matrix/script.normalized.txt \
    --ports 8120 --model qwen38-9b \
    --escalate-ports 8110,8111 --escalate-model ornith-1.5-397b \
    --workers 2 --report runs/events_build8/paraphrase_report.json \
    >> runs/events_build8.log 2>&1

echo "$(date -Is) building pack8" >> runs/eval_ox/judging.log
python3 distill/build_event_eval_pack.py \
    --a runs/events_build8/events.json \
    --b runs/events_build7_24/events.json \
    --out runs/eval_ox/pack8 \
    --key-out /home/deployer/eval_keys_ox/pack8_key \
    --seed 20260822 >> runs/eval_ox/judging.log 2>&1

echo "$(date -Is) judging pack8" >> runs/eval_ox/judging.log
python3 distill/judge_events.py --pack runs/eval_ox/pack8 \
    --out runs/eval_ox/pack8_scores --scenes-dir runs/scenes_ornith_v5 \
    --ports 8110,8111 --judges 4 >> runs/eval_ox/judging.log 2>&1

echo "$(date -Is) PACK8-DONE" >> runs/eval_ox/judging.log
