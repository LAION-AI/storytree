#!/usr/bin/env python3
"""Join the generated hindsight CoTs with their specs into an SFT dataset
in thinking-mode format, ready to ship to the GH200 box.

Each example:
  system    the production SYSTEM prompt the layer actually runs under
  user      task instruction + the material (exactly what the student sees
            at inference time)
  assistant <think>{hindsight cot}</think>{target json}

Writes one JSONL plus a per-layer split so layers can be trained/ablated
independently, and a stats report.
"""
import json, os, sys, argparse, random, statistics
from collections import Counter, defaultdict

import config
config.install_paths()
import trace_specs as ts  # noqa: E402
import meta_layer as ml  # noqa: E402

SCRATCH = str(config.TRACE_OUT)
TRACES = os.path.join(str(config.TRACE_OUT), "traces_all_layers.jsonl")
OUTDIR = os.path.join(str(config.TRACE_OUT), "sft_dataset")

# The scene layer runs under its own system prompt, not meta_layer's.
try:
    import scene_variants as sv
    SCENE_SYSTEM = sv.V1_SYSTEM
    MIND_SYSTEM = getattr(sv, "MIND_SYSTEM_V5", sv.V1_SYSTEM)
except Exception:
    SCENE_SYSTEM = MIND_SYSTEM = ml.SYSTEM

SYSTEM_FOR = defaultdict(lambda: ml.SYSTEM, {
    "scene_facts": SCENE_SYSTEM,
    "scene_minds": MIND_SYSTEM,
})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--holdout", type=float, default=0.05,
                    help="fraction of TREES (not examples) held out for eval")
    ap.add_argument("--seed", type=int, default=13)
    a = ap.parse_args()

    cots = {}
    n_err = 0
    with open(TRACES) as f:
        for line in f:
            try:
                r = json.loads(line)
            except Exception:
                continue
            if "cot" in r:
                cots[r["tid"]] = r["cot"]
            else:
                n_err += 1
    print(f"loaded {len(cots)} usable CoTs ({n_err} error records skipped)")

    slugs = json.load(open(os.path.join(str(config.TRACE_OUT), "relaxed_pass_slugs.json")))
    rnd = random.Random(a.seed)
    shuffled = slugs[:]
    rnd.shuffle(shuffled)
    n_hold = max(1, int(len(shuffled) * a.holdout))
    holdout = set(shuffled[:n_hold])
    print(f"holdout trees ({n_hold}): {sorted(holdout)}")

    os.makedirs(OUTDIR, exist_ok=True)
    train_p = os.path.join(OUTDIR, "train.jsonl")
    eval_p = os.path.join(OUTDIR, "eval.jsonl")
    per_layer = defaultdict(list)
    stats = defaultdict(lambda: {"n": 0, "cot_chars": [], "tgt_chars": [],
                                 "ctx_chars": []})
    n_train = n_eval = n_missing = 0

    with open(train_p, "w") as ftr, open(eval_p, "w") as fev:
        for spec in ts.all_specs(slugs):
            cot = cots.get(spec["tid"])
            if not cot:
                n_missing += 1
                continue
            tgt = ts._j(spec["target"])
            ex = {
                "tid": spec["tid"],
                "slug": spec["slug"],
                "layer": spec["layer"],
                "messages": [
                    {"role": "system", "content": SYSTEM_FOR[spec["layer"]]},
                    {"role": "user", "content":
                        f"{spec['task']}\n\n{spec['context']}"},
                    {"role": "assistant", "content":
                        f"<think>{cot}</think>{tgt}"},
                ],
            }
            line = json.dumps(ex, ensure_ascii=False) + "\n"
            if spec["slug"] in holdout:
                fev.write(line)
                n_eval += 1
            else:
                ftr.write(line)
                n_train += 1
                per_layer[spec["layer"]].append(line)
            s = stats[spec["layer"]]
            s["n"] += 1
            s["cot_chars"].append(len(cot))
            s["tgt_chars"].append(len(tgt))
            s["ctx_chars"].append(len(spec["context"]))

    for layer, lines in per_layer.items():
        with open(os.path.join(OUTDIR, f"train.{layer}.jsonl"), "w") as f:
            f.writelines(lines)

    print(f"\nwrote {n_train} train / {n_eval} eval examples "
          f"({n_missing} specs had no CoT yet)")
    print(f"  {train_p}\n  {eval_p}\n  + per-layer train.<layer>.jsonl")

    print("\n=== PER-LAYER ===")
    hdr = f"{'layer':22s} {'n':>6s} {'cot~':>7s} {'target~':>8s} {'ctx~':>8s}"
    print(hdr)
    print("-" * len(hdr))
    for layer in sorted(stats, key=lambda k: -stats[k]["n"]):
        s = stats[layer]
        print(f"{layer:22s} {s['n']:6d} "
              f"{statistics.median(s['cot_chars']):7.0f} "
              f"{statistics.median(s['tgt_chars']):8.0f} "
              f"{statistics.median(s['ctx_chars']):8.0f}")
    tot_tok = sum(sum(s["ctx_chars"]) + sum(s["cot_chars"]) + sum(s["tgt_chars"])
                  for s in stats.values()) / 3.6
    print(f"\napprox total training tokens: {tot_tok/1e6:.1f}M "
          "(chars/3.6, English prose+JSON)")

    json.dump({"holdout_trees": sorted(holdout),
               "n_train": n_train, "n_eval": n_eval,
               "per_layer": {k: v["n"] for k, v in stats.items()}},
              open(os.path.join(OUTDIR, "manifest.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
