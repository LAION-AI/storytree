#!/usr/bin/env python3
"""Follow the live tree pipeline and generate hindsight-CoT traces for each
tree as it completes.

Runs as a daemon beside tools/pool_worker.sh. BREADTH-FIRST across trees:
each cycle it rescans every ready tree, buckets all still-missing specs by
layer, and works exactly one layer -- the cheapest layer (by LAYER_ORDER)
that still has ANY pending work anywhere -- before rescanning again. This
guarantees root/expose/plot/meta/entity/event finish for essentially every
started tree before scene_facts (the bulk, ~55% of all specs) starts on
any of them. The old tree-major batching (finish tree 1 completely, incl.
its ~140 scene specs, before starting tree 2) produced exactly the uneven
"some trees 100%, most trees 0%" outcome this was rewritten to avoid.

A tree drops out of the rescan (marker file) only once EVERY layer's specs
for it are in `seen` -- that's the only point rebuilding its (expensive)
scene-file IO stops being worthwhile.

Deliberately uses its OWN shim ports, not pool/fresh_ports.txt, so it never
competes with the tree builders for the pool they claim from.

Traces append to traces_live.jsonl in the same record format as the
17k backfill, so the two files concatenate into one dataset.
"""
import json, os, sys, time, threading, argparse, glob
from collections import defaultdict
import concurrent.futures as cf

SCRATCH = str(config.TRACE_OUT)
sys.path.insert(0, SCRATCH)
import config
config.install_paths()
import trace_specs as ts  # noqa: E402
import trace_run as tr  # noqa: E402

TREES = str(config.TREES)
OUT = os.path.join(str(config.TRACE_OUT), "traces_live.jsonl")
MARKS = os.path.join(str(config.TRACE_OUT), "cot_done_trees")

# every artifact trace_specs needs before a tree is worth tracing
NEEDED = ["manifest.json", "meta/meta.json", "events/events.json",
          "events/events.partial.json", "entities/profiles.json",
          "root/story_root.json", "expose/expose.json", "plots/plots.json",
          "scenes_fulltext.json"]

_lock = threading.Lock()
_stats = {"done": 0, "fail": 0}


def ready_trees():
    out = []
    for d in sorted(glob.glob(os.path.join(TREES, "*"))):
        if not os.path.isdir(d):
            continue
        slug = os.path.basename(d)
        if os.path.exists(os.path.join(MARKS, slug)):
            continue
        if all(os.path.exists(os.path.join(d, n)) for n in NEEDED):
            if os.path.isdir(os.path.join(d, "scenes_with_text")):
                out.append(slug)
    return out


def run_one(spec, pool):
    tgt = ts._j(spec["target"])
    user = (f"THE TASK THE ANALYST WAS GIVEN:\n{spec['task']}\n\n"
            f"THE MATERIAL THEY WORKED FROM:\n{spec['context'][:60000]}\n\n"
            f"THE TARGET THEY PRODUCED (already correct -- reconstruct the "
            f"reasoning that would precede it):\n{tgt[:30000]}")
    t0 = time.time()
    try:
        r = pool.call(tr.COT_SYSTEM, user, schema=tr.COT_SCHEMA)
        cot = json.loads(r.text).get("reasoning", "").strip()
        if not cot:
            raise RuntimeError("empty reasoning")
        rec = {"tid": spec["tid"], "slug": spec["slug"], "layer": spec["layer"],
               "part": spec["part"], "cot": cot,
               "gen_s": round(time.time() - t0, 1)}
        ok = True
    except Exception as e:
        rec = {"tid": spec["tid"], "slug": spec["slug"], "layer": spec["layer"],
               "part": spec["part"], "error": str(e)[:200],
               "gen_s": round(time.time() - t0, 1)}
        ok = False
    with _lock:
        with open(OUT, "a") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        _stats["done"] += 1
        _stats["fail"] += 0 if ok else 1
    return ok


def load_seen():
    seen = set()
    if os.path.exists(OUT):
        with open(OUT) as f:
            for line in f:
                try:
                    seen.add(json.loads(line)["tid"])
                except Exception:
                    pass
    return seen


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ports", default=",".join(str(p) for p in range(19031, 19046)))
    ap.add_argument("--workers", type=int, default=15)
    ap.add_argument("--chunk", type=int, default=800,
                    help="max specs processed per layer-slice before rescanning "
                         "all ready trees -- keeps new trees' cheap layers from "
                         "waiting behind a long scene_facts run")
    ap.add_argument("--idle-sleep", type=int, default=180)
    ap.add_argument("--layers", default="", help="restrict to these layers")
    a = ap.parse_args()

    os.makedirs(MARKS, exist_ok=True)
    ports = [int(p) for p in a.ports.split(",")]
    pool = tr.make_pool(ports, 0.9, 6000)
    want = set(a.layers.split(",")) if a.layers else None
    seen = load_seen()
    print(f"follower up: {len(ports)} ports, {a.workers} workers, "
          f"{len(seen)} traces already on file, chunk={a.chunk}, "
          f"layer priority: {tr.LAYER_ORDER}", flush=True)

    while True:
        ready = ready_trees()
        if not ready:
            print(f"[{time.strftime('%H:%M')}] no ready trees; sleeping "
                  f"{a.idle_sleep}s (total {_stats['done']} traces, "
                  f"{_stats['fail']} failed)", flush=True)
            time.sleep(a.idle_sleep)
            continue

        t0 = time.time()
        try:
            specs = list(ts.all_specs(ready))
        except Exception as e:
            print(f"  all_specs build failed: {e}", flush=True)
            time.sleep(30)
            continue
        build_s = time.time() - t0

        by_layer = defaultdict(list)
        pending_by_slug = defaultdict(int)
        total_by_slug = defaultdict(int)
        for s in specs:
            total_by_slug[s["slug"]] += 1
            if want and s["layer"] not in want:
                continue
            if s["tid"] not in seen:
                by_layer[s["layer"]].append(s)
                pending_by_slug[s["slug"]] += 1

        newly_marked = 0
        for slug in ready:
            if total_by_slug.get(slug, 0) > 0 and pending_by_slug.get(slug, 0) == 0:
                open(os.path.join(MARKS, slug), "w").close()
                newly_marked += 1

        pending_layers = [l for l in tr.LAYER_ORDER if by_layer.get(l)]
        if not pending_layers:
            print(f"[{time.strftime('%H:%M')}] {len(ready)} ready trees all "
                  f"fully covered ({newly_marked} newly marked, "
                  f"{build_s:.0f}s to check); sleeping {a.idle_sleep}s",
                  flush=True)
            time.sleep(a.idle_sleep)
            continue

        layer = pending_layers[0]
        batch = by_layer[layer][:a.chunk]
        n_trees = len({s["slug"] for s in batch})
        pending_summary = ", ".join(f"{l}={len(by_layer[l])}" for l in pending_layers)
        print(f"[{time.strftime('%H:%M')}] {len(ready)} ready trees "
              f"(specs built in {build_s:.0f}s, {newly_marked} newly marked done) "
              f"| pending by layer: {pending_summary} "
              f"| working layer={layer} chunk={len(batch)}/{len(by_layer[layer])} "
              f"across {n_trees} trees", flush=True)

        with cf.ThreadPoolExecutor(max_workers=a.workers) as ex:
            list(ex.map(lambda s: run_one(s, pool), batch))
        for s in batch:
            seen.add(s["tid"])

        print(f"[{time.strftime('%H:%M')}] chunk done -- {_stats['done']} "
              f"traces total, {_stats['fail']} failed", flush=True)


if __name__ == "__main__":
    main()
