#!/usr/bin/env bash
# Push only if both sweeps pass.
#
# Twice now a commit has gone out while the file sweep was reporting a leak,
# because the sweep ran as its own command and its exit code did not gate the
# push. Remembering to look at the output is not a control. This is.
#
# Usage: tools/publish.sh <message-file>
set -euo pipefail

MSG="${1:?usage: tools/publish.sh <message-file>}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "== staged files =="
git diff --cached --name-only | head -20
test -n "$(git diff --cached --name-only)" || { echo "nothing staged"; exit 1; }

echo "== sweeping tracked files =="
python3 tools/check_no_leak.py

echo "== sweeping the commit message =="
python3 tools/check_no_leak.py --message "$MSG"

echo "== committing =="
git commit -q -F "$MSG"

TOKEN="$(grep -E '^GH_TOKEN=' .env | cut -d= -f2-)"
[ -n "$TOKEN" ] || { echo "no GH_TOKEN in .env"; exit 1; }
git push "https://x-access-token:${TOKEN}@github.com/LAION-AI/storytree.git" main 2>&1 \
  | sed -E 's/gh[pousr]_[A-Za-z0-9]+/[REDACTED]/g' | tail -2
