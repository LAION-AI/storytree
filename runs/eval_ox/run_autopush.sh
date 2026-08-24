#!/bin/bash
# Auto-publish watcher: as each stage of the full-film campaign lands, its
# results are elided, committed via tools/publish.sh and pushed -- no manual
# step between a finished run and the repository. Then the meta layer's build
# 2 is revised under the judge's feedback and pushed the same way.
set -e
cd /home/deployer/laion/bookwriter

push_stage () {
    local MSGFILE="$1"
    timeout 300 tools/publish.sh "$MSGFILE" 2>&1 | tail -2 || \
        echo "$(date -Is) PUSH FAILED for $MSGFILE" >> runs/eval_ox/judging.log
}

elide () {
    python3 tools/redact_source_spans.py \
        --source distill/runs/matrix/script.normalized.txt --write "$@" \
        > /dev/null 2>&1 || true
}

echo "$(date -Is) autopush: waiting for full results" >> runs/eval_ox/judging.log
while [ ! -f runs/eval_ox/packfull8_scores/scores_jox4.json ]; do sleep 120; done

elide runs/events_build10_full/protocol.json \
      runs/events_build10_full/paraphrase_report.json \
      runs/events_build10_full/events.json \
      runs/eval_ox/packfull7_scores/scores_jox*.json \
      runs/eval_ox/packfull8_scores/scores_jox*.json
cat > /tmp/msg_full.txt <<'EOF'
Full-film build 10 and both full-scale blind comparisons

All 47 events of the reused segmentation composed with the build-10 pipeline,
then judged against build 7_24 over the 23 reference anchors (the historic
baseline set) and against build 8 over their shared anchors -- four local
judge passes each. Result tables in runs/eval_ox/packfull7_result.json and
packfull8_result.json.
EOF
python3 distill/aggregate_event_eval.py \
    --judges runs/eval_ox/packfull7_scores/scores_jox*.json \
    --key /home/deployer/eval_keys_ox/packfull7_key/KEY.json \
    --label-a "Build 7_24" --label-b "Build 10 full" \
    --out runs/eval_ox/packfull7_result.json > /dev/null 2>&1 || true
python3 distill/aggregate_event_eval.py \
    --judges runs/eval_ox/packfull8_scores/scores_jox*.json \
    --key /home/deployer/eval_keys_ox/packfull8_key/KEY.json \
    --label-a "Build 8" --label-b "Build 10 full" \
    --out runs/eval_ox/packfull8_result.json > /dev/null 2>&1 || true
git add runs/events_build10_full/events.json runs/events_build10_full/protocol.json \
        runs/events_build10_full/paraphrase_report.json runs/events_build10_full/segmentation.json \
        runs/eval_ox/packfull7_scores runs/eval_ox/packfull8_scores \
        runs/eval_ox/packfull7 runs/eval_ox/packfull8 \
        runs/eval_ox/packfull7_result.json runs/eval_ox/packfull8_result.json \
        2>/dev/null || true
push_stage /tmp/msg_full.txt
echo "$(date -Is) autopush: full results pushed" >> runs/eval_ox/judging.log

echo "$(date -Is) autopush: waiting for meta judgement" >> runs/eval_ox/judging.log
while [ ! -f runs/meta_layer/judgement.json ]; do sleep 120; done

elide runs/meta_layer/meta.json runs/meta_layer/protocol.json
git add runs/meta_layer/meta.json runs/meta_layer/protocol.json \
        runs/meta_layer/judgement.json 2>/dev/null || true
cat > /tmp/msg_meta1.txt <<'EOF'
Meta layer build 1 with its judgement

Themes, central dilemma, external and internal conflicts, relationship arcs
and perspectives for the full film, grounded in the event layer, audited by
the scaffold checks and scored by distill/judge_meta.py against the six
meta dimensions.
EOF
push_stage /tmp/msg_meta1.txt

echo "$(date -Is) autopush: revising meta layer under the judge's feedback" >> runs/eval_ox/judging.log
python3 distill/meta_revise.py \
    --meta runs/meta_layer/meta.json \
    --judgement runs/meta_layer/judgement.json \
    --events runs/events_build10_full/events.json \
    --out runs/meta_layer_v2 --ports 8110,8111 >> runs/meta_layer.log 2>&1
python3 distill/judge_meta.py \
    --meta runs/meta_layer_v2/meta.json \
    --events runs/events_build10_full/events.json \
    --out runs/meta_layer_v2/judgement.json >> runs/meta_layer.log 2>&1

elide runs/meta_layer_v2/meta.json
git add runs/meta_layer_v2/meta.json runs/meta_layer_v2/judgement.json \
        distill/meta_revise.py 2>/dev/null || true
cat > /tmp/msg_meta2.txt <<'EOF'
Meta layer build 2: revised under the judge's own evidence

Every evidence clause and the commentary of the build-1 judgement went into a
per-section rewrite; the scaffold audit ran again on the revision. Both
judgements are in the tree so the two builds can be compared dimension by
dimension.
EOF
push_stage /tmp/msg_meta2.txt
echo "$(date -Is) AUTOPUSH-DONE" >> runs/eval_ox/judging.log
