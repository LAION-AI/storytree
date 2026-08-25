#!/usr/bin/env python3
"""Pipeline gate: hard assertions over all layer artefacts. Exit 1 on any
failure -- wire this after every generation stage so a dropped event or an
unplotted scene can never reach the next layer silently.

Checks:
  A. events.json <-> segmentation.json agree (would have caught ev-033)
  B. every scene file maps to EXACTLY ONE event
  C. every event belongs to >=1 plot chain; every scene therefore reached
  D. plot chains reference real event ids, strictly ascending (story order)
  E. downstream artefacts exist and passed their gates
Usage: python3 tools/pipeline_gate.py [--plots plots_covered.json]"""
import json, sys
from pathlib import Path
R = Path('runs')
fail = []
def check(name, ok, detail=''):
    print(('PASS ' if ok else 'FAIL ') + name + (f' -- {detail}' if detail else ''))
    if not ok: fail.append(name)

# --- load ---
ev = json.load(open(R/'events_build10_full/events.json'))['events']
seg = json.load(open(R/'events_build10_full/segmentation.json'))['events']
sc_files = {json.load(open(p))['scene_id'] for p in (R/'scenes_ornith_v5_clean').glob('sc-*.json')}
plots_file = sys.argv[sys.argv.index('--plots')+1] if '--plots' in sys.argv else str(R/'plot_layer_v8/plots_covered.json')
plots = json.load(open(plots_file))['plots']

ids_ev = [e['event_id'] for e in ev]
ids_seg = [e['event_id'] for e in seg]

# A. segmentation <-> events agreement (ev-033 bug class)
check('A1 event counts match segmentation', len(ev) == len(seg), f'{len(ev)} vs {len(seg)}')
check('A2 same event id set', set(ids_ev) == set(ids_seg),
      f'only-in-seg={sorted(set(ids_seg)-set(ids_ev))[:4]} only-in-events={sorted(set(ids_ev)-set(ids_seg))[:4]}')
ev_sc = {e['event_id']: e.get('scene_ids', []) for e in ev}
seg_sc = {e['event_id']: e.get('scene_ids', []) for e in seg}
drift = [i for i in ids_ev if i in seg_sc and set(ev_sc[i]) != set(seg_sc[i])]
check('A3 scene_ids match segmentation per event', not drift, str(drift[:4]))

# B. every scene -> exactly one event
scene_owner = {}
for eid, scs in ev_sc.items():
    for sc in scs:
        scene_owner.setdefault(sc, []).append(eid)
no_event = sc_files - set(scene_owner)
multi = {k: v for k, v in scene_owner.items() if len(v) > 1}
ghost = set(scene_owner) - sc_files
check('B1 every scene has an event', not no_event, str(sorted(no_event)[:6]))
check('B2 no scene in 2+ events', not multi, str(list(multi)[:6]))
check('B3 no event references unknown scenes', not ghost, str(sorted(ghost)[:6]))

# C/D. plot coverage + integrity
cov = {}
for name, d in plots.items():
    prev = 0
    ordered = True
    for m in d['chain']:
        eid = m['event_id']
        cov.setdefault(eid, []).append(name)
        n = int(eid.split('-')[1]) if eid.split('-')[1].isdigit() else -1
        if n < prev: ordered = False
        prev = max(prev, n)
    check(f'D chain story-ordered: {name[:40]}', ordered)
bad_ref = [eid for eid in cov if eid not in set(ids_ev)]
check('C1 chains reference real events', not bad_ref, str(bad_ref[:6]))
missing = [e for e in ids_ev if e not in cov]
check('C2 every event in >=1 plot', not missing,
      f'missing {len(missing)}: {sorted(missing)[:6]}')
unreached = sc_files - {sc for eid in cov for sc in ev_sc.get(eid, [])}
check('C3 every scene reached by a plotted event', not unreached,
      f'{len(unreached)}: {sorted(unreached)[:6]}')

# E. downstream artefacts
for label, p in [('root', R/'story_root_v3/judgement.json'),
                 ('expose', R/'expose_v1/judgement.json')]:
    try:
        j = json.load(open(p))
        check(f'E gate {label}: {p.parent.name}', j.get('gate') == 'PASS',
              f"mean={j.get('mean')}")
    except Exception as ex:
        check(f'E gate {label}', False, repr(ex))
iv = json.load(open(R/'story_root_v3/story_root.json')).get('identification_value', {})
need = {'admirable_strength', 'opening_vulnerability', 'connection'}
check('E identification_value complete (RT10)', need <= set(iv) and
      all(len(iv[k]) >= 150 for k in need),
      {k: len(iv.get(k, '')) for k in need}.__str__())

print()
if fail:
    print(f'GATE: FAIL ({len(fail)})'); [print(' -', f) for f in fail]; sys.exit(1)
print('GATE: ALL PASS')
