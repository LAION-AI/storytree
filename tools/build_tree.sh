#!/usr/bin/env bash
# Build a full story tree for one screenplay with Muse 1.2, fully resumable
# and dynamic-exit-pool aware. Every layer checkpoints; a re-run skips
# finished work and continues. Ports come from a LIVE pool file re-read
# before every stage, so exits can be added to the pool without stopping.
#
# Usage: OUT_BASE=... tools/build_tree.sh <slug>
# Ports: PORTS=8250,8251 (explicit) OR POOL_FILE=/path/fresh_ports.txt (live).
set -uo pipefail
cd "$(dirname "$0")/.."
SLUG="${1:?usage: tools/build_tree.sh <slug>}"
OUT_BASE="${OUT_BASE:-runs/trees}"
T="$OUT_BASE/$SLUG"
MODEL="muse-spark-1.2-contributor-free"
SRC="$T/script.normalized.txt"
MAP="$T/script_map.json"
POOL_FILE="${POOL_FILE:-/home/deployer/laion/screenplays/pool/fresh_ports.txt}"
[ -f "$SRC" ] && [ -f "$MAP" ] || { echo "GATE: $SLUG has no parsed project"; exit 1; }

# Live port set: explicit PORTS wins; else the current pool file (comma-joined,
# de-duplicated). Re-read before every stage so newly-added exits are used.
ports_now() {
  if [ -n "${PORTS:-}" ]; then echo "$PORTS"; return; fi
  [ -f "$POOL_FILE" ] && sort -u "$POOL_FILE" | grep -E '^[0-9]+$' | paste -sd, || echo ""
}
gate() { [ -e "$1" ] || { echo "GATE FAILED after $2: missing $1"; exit 1; }; echo "gate ok: $2"; }

# --- scenes (resume: only build scene ids without a node yet)
ALLIDS=$(python3 -c "
import json;m=json.load(open('$MAP'))['scenes']
print(','.join(list(m) if isinstance(m,dict) else [x[0] for x in m]))")
mkdir -p "$T/scenes"
TODO=$(python3 -c "
import os
have={f[:-5] for f in os.listdir('$T/scenes') if f.endswith('.json') and f.startswith('sc-')}
ids='$ALLIDS'.split(',')
print(','.join(i for i in ids if i and i not in have))")
NALL=$(awk -F, '{print NF}' <<<"$ALLIDS"); NHAVE=$(ls "$T/scenes"/sc-*.json 2>/dev/null | wc -l)
if [ -z "$TODO" ]; then
  echo "== [$SLUG] scenes: all $NHAVE present, skipping"
else
  NTODO=$(awk -F, '{print NF}' <<<"$TODO")
  echo "== [$SLUG] scenes: $NHAVE/$NALL present, building $NTODO more"
  P=$(ports_now); [ -n "$P" ] || { echo "GATE: no ports in pool"; exit 2; }
  python3 distill/scene_variants.py --variant v5 --script-map "$MAP" \
    --scenes "$TODO" --ports "$P" --model "$MODEL" --per-endpoint 1 \
    --source "$SRC" --out "$T/scenes" 2>&1 | tail -8
fi
N=$(ls "$T/scenes"/sc-*.json 2>/dev/null | wc -l)
[ "$N" -ge $(( NALL * 6 / 10 )) ] || { echo "GATE FAILED after scenes: only $N/$NALL"; exit 1; }
echo "gate ok: scenes ($N/$NALL)"

# --- events (resume from events.partial.json if present)
NE=$(python3 -c "import json;print(len(json.load(open('$T/events/events.json'))['events']))" 2>/dev/null || echo 0)
NSEG=$(python3 -c "import json;print(len(json.load(open('$T/events/segmentation.json'))['events']))" 2>/dev/null || echo 0)
# "complete" = events.json holds >=90% of the segmented events. A burned run
# leaves a truncated events.json (e.g. 7 of 39); that must resume, not pass.
COMPLETE=$(python3 -c "print(1 if $NE>=5 and ($NSEG==0 or $NE>=0.9*$NSEG) else 0)")
if [ "$COMPLETE" = 1 ]; then
  echo "== [$SLUG] events: reusing $NE existing (of $NSEG segmented)"
else
  RESUME=""
  # resume from the richer of partial / a truncated events.json
  CKPT=""; NP=0
  for cand in "$T/events/events.partial.json" "$T/events/events.json"; do
    n=$(python3 -c "import json;print(len(json.load(open('$cand'))['events']))" 2>/dev/null||echo 0)
    [ "$n" -gt "$NP" ] && { NP=$n; CKPT="$cand"; }
  done
  if [ "$NP" -ge 1 ] && [ "$NSEG" -gt 0 ]; then
    RESUME="--resume-from $CKPT"; echo "== [$SLUG] events: resuming from $NP/$NSEG composed"
  else echo "== [$SLUG] events (fresh)"; fi
  P=$(ports_now); [ -n "$P" ] || { echo "GATE: no ports in pool"; exit 2; }
  python3 distill/event_layer.py --scenes-dir "$T/scenes" --out "$T/events" \
    --ports "$P" --model "$MODEL" --source "$SRC" --scene-map "$MAP" \
    --ctx 200000 --wave 1 $RESUME 2>&1 | tail -12
  NE=$(python3 -c "import json;print(len(json.load(open('$T/events/events.json'))['events']))" 2>/dev/null || echo 0)
  OK=$(python3 -c "print(1 if $NE>=5 and ($NSEG==0 or $NE>=0.9*$NSEG) else 0)")
  [ "$OK" = 1 ] || { echo "GATE FAILED after events: only $NE/$NSEG (incomplete, will resume next pass)"; exit 1; }
fi
echo "gate ok: events ($NE)"

# --- upper layers (stage-level resume: skip if output exists)
run_stage() { # name outfile cmd...
  local name="$1" outf="$2"; shift 2
  if [ -f "$outf" ]; then echo "== [$SLUG] $name: reusing existing"; return; fi
  echo "== [$SLUG] $name"; "$@" 2>&1 | tail -6; gate "$outf" "$name"
}
run_stage meta "$T/meta/meta.json" \
  python3 distill/meta_layer.py --events "$T/events/events.json" \
    --scenes-dir "$T/scenes" --out "$T/meta" --ports "$(ports_now)" --model "$MODEL" --source "$SRC"
# Drama-structure layer: sibling of meta (lens, anchors, acts, ending).
# Needs meta, feeds nothing downstream unless DRAMA_TO_UPPER=1 (see below).
run_stage drama "$T/drama/drama_structure.json" \
  python3 distill/drama_structure_layer.py --events "$T/events/events.json" \
    --meta "$T/meta/meta.json" --out "$T/drama" --ports "$(ports_now)" \
    --model "$MODEL" --source "$SRC"
# DRAMA_TO_UPPER=1 hands the drama layer to plots/root/expose as extra
# context. Default OFF: those layers have measured baselines
# (docs/00-DEFAULT-PIPELINE.md) and the addition must be panel-measured
# before it becomes the default — see docs/20-drama-structure-layer.md §6.
DRAMA_ARG=""
if [ "${DRAMA_TO_UPPER:-0}" = 1 ] && [ -f "$T/drama/drama_structure.json" ]; then
  DRAMA_ARG="--drama $T/drama/drama_structure.json"
fi
run_stage entities "$T/entities/profiles.json" \
  python3 distill/entity_layer.py --scenes-dir "$T/scenes" --out "$T/entities" \
    --ports "$(ports_now)" --model "$MODEL" --source "$SRC"
run_stage plots "$T/plots/plots.json" \
  python3 distill/plot_layer.py --meta "$T/meta/meta.json" \
    --events "$T/events/events.json" --out "$T/plots" --ports "$(ports_now)" --model "$MODEL" $DRAMA_ARG
run_stage root "$T/root/story_root.json" \
  python3 distill/root_layer.py --script "$SRC" --events "$T/events/events.json" \
    --meta "$T/meta/meta.json" --entities "$T/entities/profiles.json" \
    --out "$T/root" --ports "$(ports_now)" --model "$MODEL" $DRAMA_ARG
run_stage expose "$T/expose/expose.json" \
  python3 distill/expose_layer.py --root "$T/root/story_root.json" \
    --events "$T/events/events.json" --meta "$T/meta/meta.json" \
    --entities "$T/entities/profiles.json" --out "$T/expose" --ports "$(ports_now)" --model "$MODEL" $DRAMA_ARG

echo "== [$SLUG] TREE COMPLETE"
