#!/usr/bin/env bash
# Launch all 8 endpoints, GPU N -> port 810N
S=/tmp/claude-1001/-home-deployer-laion-bookwriter/70e4d41c-edcc-4f25-881c-f35243dc0da1/scratchpad
mkdir -p $S/logs
for i in 0 1 2 3 4 5 6 7; do
  if curl -s -m 2 http://127.0.0.1:810$i/health >/dev/null 2>&1; then
    echo "port 810$i already healthy, skipping"; continue
  fi
  nohup $S/launch_one.sh $i 810$i "$@" > $S/logs/gpu$i.log 2>&1 &
  echo "launched GPU$i -> 810$i (pid $!)"
done
