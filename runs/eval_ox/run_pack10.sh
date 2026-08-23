#!/bin/bash
# Build 10 = best of 8 and 9: keeps build 9's verified wins (boilerplate and
# pointer checks, locations enum, tidy_text fix) and reverts what regressed --
# the movement-contract fault no longer offers the unmoved escape hatch,
# accepted regenerations get predecessor exits re-applied so the entry chain
# cannot be severed, regeneration prompts are person/object aware, and a
# rewrite that nulls a reading is rejected. Judged against build 8, the best
# arm so far.
set -e
cd /home/deployer/laion/bookwriter

echo "$(date -Is) pack10: waiting for compose" >> runs/eval_ox/judging.log
while pgrep -f 'distill/event_layer.py' > /dev/null; do sleep 60; done

if [ ! -f runs/events_build10/events.json ]; then
    echo "$(date -Is) PACK10 ABORTED: compose finished without events.json" >> runs/eval_ox/judging.log
    exit 1
fi

# NOTE: the pass exits non-zero when residual runs remain. Under set -e that
# killed this script silently between compose and judging (build 10); zero
# residuals in builds 8-9 had hidden the behaviour. Keep going on residuals --
# they get elided before anything is published.
python3 distill/paraphrase_pass.py \
    --nodes runs/events_build10/events.json \
    --source distill/runs/matrix/script.normalized.txt \
    --ports 8120 --model qwen38-9b \
    --escalate-ports 8110,8111 --escalate-model ornith-1.5-397b \
    --workers 2 --report runs/events_build10/paraphrase_report.json \
    >> runs/events_build10.log 2>&1 || echo "$(date -Is) paraphrase had residuals; continuing" >> runs/eval_ox/judging.log

python3 distill/build_event_eval_pack.py \
    --a runs/events_build10/events.json \
    --b runs/events_build8/events.json \
    --out runs/eval_ox/pack10 \
    --key-out /home/deployer/eval_keys_ox/pack10_key \
    --seed 20260822 >> runs/eval_ox/judging.log 2>&1

python3 distill/judge_events.py --pack runs/eval_ox/pack10 \
    --out runs/eval_ox/pack10_scores --scenes-dir runs/scenes_ornith_v5 \
    --ports 8110,8111 --judges 4 >> runs/eval_ox/judging.log 2>&1

echo "$(date -Is) PACK10-DONE" >> runs/eval_ox/judging.log
