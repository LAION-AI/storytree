#!/bin/bash
# Build 9 = build 8's pipeline plus the fault classes its judges' evidence named
# (object boilerplate in person registers, moved-but-identical registers,
# evidence-scene pointers outside the entity's scenes, open location list).
# Same discipline as run_pack8.sh: wait for compose, identical paraphrase pass,
# blind pack against build 8, same four-judge panel, key outside the repo.
set -e
cd /home/deployer/laion/bookwriter

echo "$(date -Is) pack9: waiting for compose" >> runs/eval_ox/judging.log
while pgrep -f 'distill/event_layer.py' > /dev/null; do sleep 60; done

if [ ! -f runs/events_build9/events.json ]; then
    echo "$(date -Is) PACK9 ABORTED: compose finished without events.json" >> runs/eval_ox/judging.log
    exit 1
fi

python3 distill/paraphrase_pass.py \
    --nodes runs/events_build9/events.json \
    --source distill/runs/matrix/script.normalized.txt \
    --ports 8120 --model qwen38-9b \
    --escalate-ports 8110,8111 --escalate-model ornith-1.5-397b \
    --workers 2 --report runs/events_build9/paraphrase_report.json \
    >> runs/events_build9.log 2>&1

python3 distill/build_event_eval_pack.py \
    --a runs/events_build9/events.json \
    --b runs/events_build8/events.json \
    --out runs/eval_ox/pack9 \
    --key-out /home/deployer/eval_keys_ox/pack9_key \
    --seed 20260822 >> runs/eval_ox/judging.log 2>&1

python3 distill/judge_events.py --pack runs/eval_ox/pack9 \
    --out runs/eval_ox/pack9_scores --scenes-dir runs/scenes_ornith_v5 \
    --ports 8110,8111 --judges 4 >> runs/eval_ox/judging.log 2>&1

echo "$(date -Is) PACK9-DONE" >> runs/eval_ox/judging.log
