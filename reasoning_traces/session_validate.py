#!/usr/bin/env python3
"""Strict schema gate for top-down traces (session AND api paths).

Checks required keys AND value types per step -- key presence alone let a
real defect through (expose.ending_first as {"ending": ...} instead of a
plain string; 3/10 T4 artifacts, 2026-09-06).

Usage:
  python3 session_validate.py --parts /path/to/parts [--merge --gen-dir ...]
  python3 session_validate.py --check-file /path/to/one.json

Exit 0 = all clean (or merge done), 1 = rejects found (listed with reasons).
"""

import argparse
import glob
import json
import os
import re
import sys

STR = str
INT = int
LIST = list
DICT = dict


def _str_min(n):
    return (STR, n)


def check(value, spec, path="root"):
    """Return list of error strings. spec is a nested structure:
    {key: subspec} for dicts, [subspec] (len 1) for lists, a type, or
    ("str", min_len) for strings with minimum length."""
    errs = []
    if isinstance(spec, dict):
        if not isinstance(value, dict):
            return ["%s: expected object, got %s" % (path, type(value).__name__)]
        for k, sub in spec.items():
            if k not in value:
                errs.append("%s: missing key '%s'" % (path, k))
            else:
                errs += check(value[k], sub, "%s.%s" % (path, k))
        return errs
    if isinstance(spec, list):
        if not isinstance(value, list):
            return ["%s: expected list, got %s" % (path, type(value).__name__)]
        lo, hi = spec[1] if len(spec) > 1 else (0, 999)
        if not lo <= len(value) <= hi:
            errs.append("%s: expected %d..%d items, got %d" % (path, lo, hi, len(value)))
        if spec and not isinstance(spec[0], int):
            for i, item in enumerate(value):
                errs += check(item, spec[0], "%s[%d]" % (path, i))
        return errs
    if isinstance(spec, tuple):
        t, n = spec
        if not isinstance(value, t):
            return ["%s: expected %s, got %s" % (path, t.__name__, type(value).__name__)]
        if len(value) < n:
            errs.append("%s: too short (%d < %d)" % (path, len(value), n))
        return errs
    if not isinstance(value, spec):
        return ["%s: expected %s, got %s" % (path, spec.__name__, type(value).__name__)]
    return errs


META_THEMES = {"big_questions": [STR, (3, 3)],
               "central_dilemma": {"statement": _str_min(20), "poles": [STR, (2, 2)]}}
META_EXTERNAL = {"conflicts": [{"parties": [STR, (2, 9)], "over": _str_min(10),
                                "stakes": _str_min(10)}, (3, 3)]}
META_INTERNAL = {"internal_conflicts": [{"whose": _str_min(1),
                                         "torn_between": [STR, (2, 2)],
                                         "anchored_in": _str_min(10)}, (2, 2)]}
META_REL = {"relationship_arcs": [{"between": [STR, (2, 2)], "start": _str_min(10),
                                   "turn": _str_min(10), "end": _str_min(10)}, (2, 2)]}
META_PERSP = {"perspectives": [{"holder": _str_min(1), "stance": _str_min(10)}, (3, 5)]}
PLOTS = {"plots": [{"plot_id": STR, "spine": _str_min(10), "agent": _str_min(1),
                    "goal": _str_min(5), "resistance": _str_min(5),
                    "stakes": _str_min(5), "outcome": _str_min(5)}, (3, 5)]}
# The planned dramatic structure (step t2b, docs/20-drama-structure-layer.md).
# Only the three fields t2b declares as required are gated here; exposition,
# hero_journey and ending are legitimately optional -- a minimal plan is a
# valid plan, and the layer's own rule is "smallest valid representation".
# Anchors carry NO event ids by design: no events exist at planning time.
DRAMA = {"analysis_scope": {"primary_lens": STR, "narration_mode": STR,
                            "why_this_lens": _str_min(30)},
         "anchors": [{"id": STR, "kind": STR,
                      "intended_change": _str_min(15),
                      "why_this_function": _str_min(15)}, (3, 14)],
         "acts": [{"label": _str_min(3), "start_boundary": STR,
                   "end_boundary": STR,
                   "dramatic_question": _str_min(10)}, (1, 6)]}
ENTITY = {"name": _str_min(1), "type": STR, "profile": _str_min(20),
          "state_variables": LIST, "arc_sketch": _str_min(10), "relationships": LIST}
EXPOSE = {"ending_first": _str_min(200),
          "synopsis": {"s01": _str_min(50), "s02": _str_min(50), "s03": _str_min(50),
                       "s04": _str_min(50), "s05": _str_min(50)},
          "jacket_copy": _str_min(200)}
SKELETON = {"event_id": STR, "question": _str_min(10), "owner_plot": STR,
            "n_scenes": INT}
CHAIN = {"plot": STR, "chain": [{"event_id": STR, "why": _str_min(10)}, (1, 12)]}
EVENT = {"event_id": STR, "summary": _str_min(20), "state_triples": LIST}
CARD = {"scene_id": STR, "summary": _str_min(10), "what_changes": LIST}
PROSE = {"scene_id": STR, "scene_text": _str_min(100)}

SCHEMAS = {
    ("meta", "themes"): META_THEMES,
    ("meta", "external"): META_EXTERNAL,
    ("meta", "internal"): META_INTERNAL,
    ("meta", "relationships"): META_REL,
    ("meta", "perspectives"): META_PERSP,
    ("plots", "all"): PLOTS,
    ("drama", "all"): DRAMA,
    ("entity", None): ENTITY,
    ("expose", "all"): EXPOSE,
    ("skeleton", None): SKELETON,
    ("chain", None): CHAIN,
    ("event", None): EVENT,
    ("card", None): CARD,
    ("prose", None): PROSE,
}


def validate(record, filename=None):
    """Return list of error strings (empty = clean)."""
    errs = []
    for k in ("tid", "seed", "step", "part", "reasoning", "artifact"):
        if k not in record:
            errs.append("record: missing key '%s'" % k)
    if errs:
        return errs
    # tid contract: <seed>::topdown::<step>::<tidpart>, where tidpart is the
    # filename suffix. NOTE: for entity/chain records part carries the NAME
    # while the tid carries the stable index (p00 / pl-01) -- same as the
    # filename. A tid without the ::topdown:: infix (single underscores)
    # is a schema violation, not a variant.
    if filename:
        base = os.path.basename(filename)
        m = re.match(r"^(.+)__([a-z]+)__(.+)\.json$", base)
        if m:
            fseed, fstep, fpart = m.group(1), m.group(2), m.group(3)
            exp = "%s::topdown::%s::%s" % (fseed, fstep, fpart)
            if record.get("tid") != exp:
                errs.append("tid: expected '%s', got '%s'" % (exp, record.get("tid")))
            if record.get("seed") != fseed or record.get("step") != fstep:
                errs.append("record: seed/step disagree with filename '%s'" % base)
    if not isinstance(record.get("reasoning"), str) or len(record["reasoning"]) < 500:
        errs.append("reasoning: expected string >= 500 chars, got %d" %
                    len(str(record.get("reasoning") or "")))
    schema = SCHEMAS.get((record.get("step"), record.get("part")))
    if schema is None:
        schema = SCHEMAS.get((record.get("step"), None))
    if schema is None:
        return errs + ["record: no schema for step=%s part=%s" %
                       (record.get("step"), record.get("part"))]
    art = record.get("artifact")
    if not isinstance(art, dict):
        return errs + ["artifact: expected object, got %s" % type(art).__name__]
    # exact-sections rule for synopsis (no s06, no missing s03)
    if record.get("step") == "expose" and isinstance(art.get("synopsis"), dict):
        if set(art["synopsis"]) != {"s01", "s02", "s03", "s04", "s05"}:
            errs.append("artifact.synopsis: must be exactly s01..s05, got %s" %
                        sorted(art["synopsis"]))
    return errs + check(art, schema, "artifact")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--parts", default=None)
    ap.add_argument("--check-file", default=None)
    ap.add_argument("--merge", action="store_true")
    ap.add_argument("--gen-dir", default=None)
    args = ap.parse_args(argv)

    files = [args.check_file] if args.check_file else sorted(glob.glob(os.path.join(args.parts, "*.json")))
    clean, rejects = [], []
    for f in files:
        try:
            r = json.load(open(f))
        except Exception as e:
            rejects.append((f, ["unparsable JSON: %s" % str(e)[:120]]))
            continue
        errs = validate(r, filename=f)
        (clean if not errs else rejects).append((f, errs) if errs else r)

    if args.merge and args.gen_dir:
        os.makedirs(args.gen_dir, exist_ok=True)
        # Rebuild from parts (source of truth), dedup by tid. Parts hold one
        # record per trace; (seed,step,part) dedup is WRONG here because the
        # same entity name may legitimately cover several plots (p00-p03 all
        # "Barry Egan") -- those are distinct traces with distinct tids.
        by_seed = {}
        for r in clean:
            by_seed.setdefault(r["seed"], {})[r["tid"]] = r
        for seed, recs in by_seed.items():
            out = os.path.join(args.gen_dir, seed + ".jsonl")
            ordered = sorted(recs.values(), key=lambda r: r.get("tid", ""))
            open(out, "w").write("\n".join(json.dumps(x, ensure_ascii=False) for x in ordered) + "\n")

    print("clean: %d, rejects: %d" % (len(clean), len(rejects)))
    for f, errs in rejects:
        print("REJECT %s" % os.path.basename(f))
        for e in errs[:6]:
            print("   - %s" % e)
    return 1 if rejects else 0


if __name__ == "__main__":
    raise SystemExit(main())
