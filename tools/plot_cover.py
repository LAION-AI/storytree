#!/usr/bin/env python3
"""Coverage repair: assign every event missing from a plot sample to at least
one existing plot (multi-assignment allowed), then rebuild ordered chains."""
import json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'distill'))
sys.path.insert(0, '/home/deployer/laion/project-alexandria/screenplay/src')
from screenplay_ku.client import EndpointPool
from screenplay_ku.kuschema import grammar_safe
import meta_layer as ml

R = Path('runs')
SRC = sys.argv[1] if len(sys.argv) > 1 else str(R/'plot_layer_v8/plots.json')
OUT = sys.argv[2] if len(sys.argv) > 2 else str(R/'plot_layer_v8/plots_covered.json')

events = json.load(open(R/'events_build10_full/events.json'))['events']
seg = json.load(open(R/'events_build10_full/segmentation.json'))['events']
ev_scenes = {e['event_id']: e.get('scene_ids', []) for e in seg}
plots = json.load(open(SRC))['plots']
covered = set()
for d in plots.values():
    covered.update(m['event_id'] for m in d['chain'])
missing = [e for e in events if e['event_id'] not in covered]
print(f'missing events: {len(missing)}')

pool = EndpointPool([8110, 8111], 'ornith-1.5-397b', temperature=0.4,
                    max_tokens=8000, timeout=1800)
schema = grammar_safe({'type': 'object', 'properties': {'assignments': {
    'type': 'array', 'minItems': len(missing), 'maxItems': len(missing),
    'items': {'type': 'object', 'properties': {
        'event_id': {'type': 'string'},
        'plots': {'type': 'array', 'minItems': 1, 'maxItems': 3,
                  'items': {'type': 'string'}},
        'why_in_plot': {'type': 'string', 'minLength': 30}},
        'required': ['event_id', 'plots', 'why_in_plot'],
        'additionalProperties': False}}},
    'required': ['assignments'], 'additionalProperties': False})

defs = json.dumps([{'name': n, 'theme': d['definition']['theme_or_dilemma'],
                    'summary': d['definition']['summary']} for n, d in plots.items()],
                  ensure_ascii=False)
miss_txt = '\n'.join(f"{e['event_id']} :: {e['title']} :: "
                     f"{e['summary'][:260]}" for e in missing)
resp = json.loads(pool.call(ml.SYSTEM, (
    'These plot throughlines exist:\n' + defs +
    '\n\nThe following events are NOT yet part of any plot. Assign EVERY one '
    'to at least one plot it genuinely serves (two or three if it carries '
    'several threads; never force a fit -- but every event here belongs '
    'somewhere, look closer). One line of why_in_plot each, naming what the '
    'event does FOR that plot.\n\n' + miss_txt), schema=schema).text)['assignments']

by_plot = {n: list(d['chain']) for n, d in plots.items()}
unmatched = []
for a in resp:
    eid = a['event_id']
    if eid not in {e['event_id'] for e in missing}:
        continue
    entry = {'event_id': eid, 'why_in_plot': a['why_in_plot'],
             'caused_by_previous': '(coverage repair: bridging link, see '
                                   'neighbouring chain links)',
             '_assigned_plots': a['plots']}
    names = list(by_plot)
    for name in a['plots']:
        target = next((n for n in names if n == name), None)
        if target is None:
            target = next((n for n in names if name in n or n in name), None)
        if target is None:
            continue
        by_plot[target].append(entry)
    if not any(a['plots'][0] in n or n in a['plots'][0] for n in names):
        unmatched.append(eid)

def evnum(m):
    return int(re.search(r'(\d+)', m['event_id']).group(1))
for name in by_plot:
    seen = set(); dedup = []
    for m in sorted(by_plot[name], key=evnum):
        if m['event_id'] in seen: continue
        seen.add(m['event_id']); dedup.append(m)
    by_plot[name] = dedup

json.dump({'plots': {n: {'definition': plots[n]['definition'], 'chain': c}
                     for n, c in by_plot.items()}},
          open(OUT, 'w'), indent=1, ensure_ascii=False)
print('wrote', OUT)
print('unmatched:', unmatched)
