#!/usr/bin/env python3
"""Emit the next N top-down session jobs, dependencies respected.

One sequential job per film per wave for chained steps (T2/T4/T7-single);
parallel-safe steps fan out (T1/T3/T5/T6/T8/T9, T5 mapped to s01..s05,
T8/T9 to sc-001..sc-005). Films closest to complete come first.

Usage: python3 session_plan.py --parts DIR --hf-dir DIR --n 50
Output: JSON list [{film, step, part, kind}] on stdout.
"""
import argparse
import glob
import json
import os

T1 = ["themes", "external", "internal", "relationships", "perspectives"]


def load(path):
    try:
        return json.load(open(path))
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--parts", required=True)
    ap.add_argument("--hf-dir", required=True)
    ap.add_argument("--n", type=int, default=50)
    args = ap.parse_args()

    slugs = sorted(os.path.basename(p)[:-5]
                   for p in glob.glob(os.path.join(args.hf_dir, "data", "*.json")))
    have = {}
    for f in glob.glob(os.path.join(args.parts, "*.json")):
        r = load(f)
        if r and r.get("tid"):
            # NOTE: keyed by tid, not (step, part): entity parts carry the
            # entity NAME, and the same agent may legitimately cover several
            # plots (e.g. 4 Punch-Drunk plots all driven by Barry Egan).
            have.setdefault(r["seed"], set()).add(r["tid"])

    def has(seed, step, part):
        # trailing whitespace is stripped: filenames cannot reliably hold it
        # (see Miller chain repairs), so "x " and "x" are the same job.
        want = ("%s::topdown::%s::%s" % (seed, step, part)).strip()
        return any(t.strip().startswith(want)
                   for t in have.get(seed, set()))

    def plots_of(slug):
        r = load(os.path.join(args.parts, "%s__plots__all.json" % slug))
        try:
            return r["artifact"]["plots"]
        except Exception:
            return []

    jobs = []

    def add(film, step, part, kind):
        jobs.append({"film": film, "step": step, "part": part, "kind": kind})

    # priority 1: advance started films (most complete first)
    started = [s for s in slugs if s in have]
    started.sort(key=lambda s: -len(have[s]))
    for slug in started:
        meta = [p for p in T1 if has(slug, "meta", p)]
        for p in T1:
            if not has(slug, "meta", p):
                add(slug, "meta", p, "t1")
        plots = plots_of(slug)
        if len(meta) == 5 and not has(slug, "plots", "all"):
            add(slug, "plots", "all", "t2")
        # The dramatic-structure plan (t2b) needs root + meta + plots and is
        # the exposé's structural input, so it is scheduled as soon as plots
        # exist and before the exposé gate below.
        # docs/20-drama-structure-layer.md §8.
        if len(meta) == 5 and plots and not has(slug, "drama", "all"):
            add(slug, "drama", "all", "t2b")
        if plots:
            # NOTE: entity records carry the entity NAME in part (tid holds
            # the p-index), so completion is counted, not matched.
            n_ent_done = len([1 for t in have.get(slug, set()) if "::entity::" in t])
            for i in range(n_ent_done, min(len(plots), 5)):
                add(slug, "entity", "p%02d" % i, "t3")
            n_ent = min(len(plots), 5)
            ent_done = n_ent_done >= n_ent
            if len(meta) == 5 and plots and ent_done and not has(slug, "expose", "all"):
                add(slug, "expose", "all", "t4")
            sk_done = all(has(slug, "skeleton", "ev-%03d" % i) for i in range(1, 6))
            if has(slug, "expose", "all"):
                for i in range(1, 6):
                    if not has(slug, "skeleton", "ev-%03d" % i):
                        add(slug, "skeleton", "ev-%03d" % i, "t5")
            if plots and sk_done:
                for p in plots[:5]:
                    pid = p.get("plot_id") or p.get("name") or "plot"
                    if not has(slug, "chain", str(pid)[:24]):
                        add(slug, "chain", str(pid)[:24], "t6")
            n_ch = min(len(plots), 5) if plots else 0
            ch_done = plots and sk_done and all(
                has(slug, "chain", str((p.get("plot_id") or p.get("name")))[:24])
                for p in plots[:5])
            ev_done = [has(slug, "event", "ev-%03d" % i) for i in range(1, 6)]
            if sk_done and not all(ev_done):
                nxt = ev_done.index(False) + 1
                add(slug, "event", "ev-%03d" % nxt, "t7")
            if all(ev_done):
                for i in range(1, 6):
                    if not has(slug, "card", "sc-%03d" % i):
                        add(slug, "card", "sc-%03d" % i, "t8")
                cards_done = all(has(slug, "card", "sc-%03d" % i) for i in range(1, 6))
                if cards_done:
                    for i in range(1, 6):
                        if not has(slug, "prose", "sc-%03d" % i):
                            add(slug, "prose", "sc-%03d" % i, "t9")

    # priority 2: seed untouched films (T1 themes only; rest follows later)
    if len(jobs) < args.n:
        for slug in slugs:
            if slug not in have:
                if not has(slug, "meta", "themes"):
                    add(slug, "meta", "themes", "t1")
            if len(jobs) >= args.n:
                break

    print(json.dumps(jobs[:args.n], indent=0))


if __name__ == "__main__":
    raise SystemExit(main())
