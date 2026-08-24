#!/bin/bash
# Repair chain after the evidence=null bug: re-judge build 1 so the
# judgement carries real evidence clauses, run the build-2 revision on them,
# judge the revision, push all three.
set -e
cd /home/deployer/laion/bookwriter

echo "$(date -Is) fix: re-judging meta v1 with evidence" >> runs/eval_ox/judging.log
python3 distill/judge_meta.py \
    --meta runs/meta_layer/meta.json \
    --events runs/events_build10_full/events.json \
    --out runs/meta_layer/judgement.json >> runs/meta_layer.log 2>&1

echo "$(date -Is) fix: revising to build 2" >> runs/eval_ox/judging.log
python3 distill/meta_revise.py \
    --meta runs/meta_layer/meta.json \
    --judgement runs/meta_layer/judgement.json \
    --events runs/events_build10_full/events.json \
    --out runs/meta_layer_v2 --ports 8110,8111 >> runs/meta_layer.log 2>&1

echo "$(date -Is) fix: judging meta v2" >> runs/eval_ox/judging.log
python3 distill/judge_meta.py \
    --meta runs/meta_layer_v2/meta.json \
    --events runs/events_build10_full/events.json \
    --out runs/meta_layer_v2/judgement.json >> runs/meta_layer.log 2>&1

elide () {
    python3 tools/redact_source_spans.py \
        --source distill/runs/matrix/script.normalized.txt --write "$@" \
        > /dev/null 2>&1 || true
}
elide runs/meta_layer/judgement.json runs/meta_layer_v2/meta.json \
      runs/meta_layer_v2/judgement.json
git add distill/judge_meta.py distill/meta_revise.py runs/meta_layer/judgement.json \
        runs/meta_layer_v2/meta.json runs/meta_layer_v2/judgement.json
cat > /tmp/msg_metafix.txt <<'EOF'
Meta layer build 2, and a judging-schema bug fixed

The judge's schema kept its evidence clauses outside the grammar's properties,
so the first judgement shipped with evidence=null and the revision pass that
consumes those clauses crashed. Schema nesting fixed; build 1 re-judged with
real per-dimension evidence; build 2 rewritten under every clause and the
commentary, scaffold-audited again, and judged in turn. Both judgements are
in the tree for a dimension-by-dimension comparison.
EOF
timeout 300 tools/publish.sh /tmp/msg_metafix.txt 2>&1 | tail -2 || \
    echo "$(date -Is) PUSH FAILED" >> runs/eval_ox/judging.log
echo "$(date -Is) METAFIX-DONE" >> runs/eval_ox/judging.log
