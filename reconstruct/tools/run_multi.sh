#!/bin/bash
cd /home/deployer/laion/bookwriter/reconstruct
for s in sc-001 sc-003 sc-005; do
  echo "════════════════════════════════════════ $s"
  python3 -u tools/experiment_scaffold.py runs/matrix "$s" || echo "  FAILED $s"
done
