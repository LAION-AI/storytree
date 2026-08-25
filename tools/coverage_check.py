#!/usr/bin/env python3
"""Coverage audit: does every EVENT belong to >=1 plot chain, and does every
SCENE belong to exactly one event (flag: zero events, or 2+ events)?
Usage: python tools/coverage_check.py [plots.json ...]"""
import json, sys
from pathlib import Path
R = Path('runs')
events = json.load(open(R/'events_build10_full/events.json'))['events']
seg = json.load(open(R/'events_build10_full/segmentation.json'))['events']
ev_scenes = {e['event_id']: e.get('scene_ids', []) for e in seg}
scene_count = 224
all_scenes = set()
for s in (R/'scenes_ornith_v5_clean').glob('sc-*.json'):
    all_scenes.add(json.load(open(s))['scene_id'])

def audit(pfile):
    p = json.load(open(pfile))['plots']
    covered_events = {}
    for name, d in p.items():
        for m in d['chain']:
            covered_events.setdefault(m['event_id'], []).append(name)
    ev_all = {e['event_id'] for e in events}
    miss_ev = sorted(ev_all - set(covered_events))
    # scene -> events mapping (via segmentation scene_ids)
    scene_events = {}
    for eid, scs in ev_scenes.items():
        for sc in scs:
            scene_events.setdefault(sc, []).append(eid)
    scenes_in_plots = set()
    for eid in covered_events:
        scenes_in_plots.update(ev_scenes.get(eid, []))
    miss_sc = sorted(all_scenes - scenes_in_plots)
    multi_event = {sc: v for sc, v in scene_events.items() if len(v) > 1}
    no_event = sorted(all_scenes - set(scene_events))
    multi_plot_ev = {e: v for e, v in covered_events.items() if len(v) > 1}
    return {
        'plots_file': str(pfile), 'plots': len(p),
        'events_total': len(ev_all),
        'events_in_plots': len(covered_events),
        'events_missing': miss_ev,
        'events_in_multiple_plots': multi_plot_ev,
        'scenes_total': len(all_scenes),
        'scenes_reached_via_plotted_events': len(scenes_in_plots),
        'scenes_missing_from_plots': miss_sc,
        'scenes_with_no_event': no_event,
        'scenes_in_multiple_events': {k: len(v) for k, v in multi_event.items()},
    }

if __name__ == '__main__':
    files = sys.argv[1:] or [str(R/f'plot_layer_v{i}/plots.json') for i in range(1, 9)]
    out = []
    for f in files:
        if not Path(f).exists():
            print('skip', f); continue
        r = audit(f)
        out.append(r)
        print(f"{f}: plots={r['plots']} events {r['events_in_plots']}/{r['events_total']} "
              f"(missing {len(r['events_missing'])}) | scenes reached "
              f"{r['scenes_reached_via_plotted_events']}/{r['scenes_total']} "
              f"(missing {len(r['scenes_missing_from_plots'])}) | "
              f"scenes w/o event: {len(r['scenes_with_no_event'])} | "
              f"scenes in 2+ events: {len(r['scenes_in_multiple_events'])} | "
              f"events in 2+ plots: {len(r['events_in_multiple_plots'])}")
    Path(R/'coverage_report.json').write_text(json.dumps(out, indent=1))
    print('wrote runs/coverage_report.json')
