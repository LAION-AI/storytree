#!/usr/bin/env python3
"""Generate hindsight-CoT traces for every layer of every PASS tree.

No judge panel: the pilot and the 68-tree plot run both hit >=4.0 on the
first candidate 100% of the time, so per-trace judging buys nothing here.

Resumable: results append to a JSONL keyed by tid; a restart skips every
tid already present. Only the CoT is stored -- task/context/target are
deterministically reconstructible from trace_specs.py, and storing the
contexts would cost ~1GB.
"""
import json, sys, os, time, threading, argparse
import concurrent.futures as cf

import config
config.install_paths()
import trace_specs as ts  # noqa: E402
import meta_layer as ml  # noqa: E402
from screenplay_ku.client import EndpointPool  # noqa: E402
from screenplay_ku.kuschema import grammar_safe  # noqa: E402

SCRATCH = str(config.TRACE_OUT)
OUT = os.path.join(str(config.TRACE_OUT), "traces_all_layers.jsonl")

# cheapest-and-highest-value first, so partial results are useful early
LAYER_ORDER = ["plot_identify", "plot_chain", "root", "expose",
               "meta_perspectives", "meta_section", "entity_profile",
               "event_reconcile", "event_compose", "scene_minds",
               "scene_facts"]

COT_SCHEMA = grammar_safe({
    "type": "object",
    "properties": {"reasoning": {"type": "string"}},
    "required": ["reasoning"], "additionalProperties": False})

COT_SYSTEM = (
    "You are reconstructing plausible reasoning. You will be given a task, "
    "the material it works from, and a TARGET output that a skilled analyst "
    "already produced. Your job is to write the step-by-step reasoning that "
    "analyst plausibly went through BEFORE writing the target down -- as if "
    "thinking out loud while still exploring the material, not already "
    "knowing the answer. Reference specific ids, names and details from the "
    "material. Where the task involved a real judgement call, consider what "
    "else could have been true and why it was ruled out. Do not simply "
    "restate or paraphrase the target as your reasoning -- show the "
    "inferential steps that would lead there. End your reasoning right at "
    "the point the target becomes the obvious conclusion, but do NOT write "
    "the target out yourself. Output plain prose reasoning only, no JSON, "
    "no headers. Scale your length to the task: a short scene node needs "
    "120-250 words, a full story root or expose needs 400-700. "
    "Return it as JSON: {\"reasoning\": \"<your prose>\"}.")

_lock = threading.Lock()
_done = 0
_fail = 0


def load_done():
    done = set()
    if os.path.exists(OUT):
        with open(OUT) as f:
            for line in f:
                try:
                    done.add(json.loads(line)["tid"])
                except Exception:
                    pass
    return done


def make_pool(ports, temp, max_tokens):
    return EndpointPool(ports, "muse-spark-1.2-contributor-free",
                        temperature=temp, max_tokens=max_tokens,
                        timeout=900, retries=4)


def run_one(spec, pool, total):
    global _done, _fail
    tgt = ts._j(spec["target"])
    # keep the whole prompt inside what the shim will accept
    user = (f"THE TASK THE ANALYST WAS GIVEN:\n{spec['task']}\n\n"
            f"THE MATERIAL THEY WORKED FROM:\n{spec['context'][:60000]}\n\n"
            f"THE TARGET THEY PRODUCED (already correct -- reconstruct the "
            f"reasoning that would precede it):\n{tgt[:30000]}")
    t0 = time.time()
    try:
        r = pool.call(COT_SYSTEM, user, schema=COT_SCHEMA)
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
        _done += 1
        if not ok:
            _fail += 1
        if _done % 25 == 0:
            print(f"  {_done}/{total} done ({_fail} failed)", flush=True)
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ports", default="19001,19002,19003,19004,19005,19006,"
                                       "19007,19008,19009,19010")
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--layers", default="", help="comma list; default all")
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()

    ports = [int(p) for p in a.ports.split(",")]
    slugs = json.load(open(os.path.join(str(config.TRACE_OUT), "relaxed_pass_slugs.json")))

    print("building specs...", flush=True)
    specs = list(ts.all_specs(slugs))
    want = set(a.layers.split(",")) if a.layers else None
    if want:
        specs = [s for s in specs if s["layer"] in want]
    order = {l: i for i, l in enumerate(LAYER_ORDER)}
    specs.sort(key=lambda s: (order.get(s["layer"], 99), s["slug"], s["part"]))

    done = load_done()
    todo = [s for s in specs if s["tid"] not in done]
    if a.limit:
        todo = todo[:a.limit]

    from collections import Counter
    c = Counter(s["layer"] for s in todo)
    print(f"specs total {len(specs)}, already done {len(done)}, todo {len(todo)}")
    for l in LAYER_ORDER:
        if c.get(l):
            print(f"  {l:22s} {c[l]}")
    if not todo:
        print("nothing to do")
        return

    pool = make_pool(ports, 0.9, 6000)
    total = len(todo)
    t0 = time.time()
    with cf.ThreadPoolExecutor(max_workers=a.workers) as ex:
        list(ex.map(lambda s: run_one(s, pool, total), todo))
    dt = time.time() - t0
    print(f"\nDONE {_done}/{total} in {dt/60:.1f} min ({_fail} failed)")
    print(f"rate: {_done/max(dt,1)*3600:.0f} traces/hour")


if __name__ == "__main__":
    main()
