#!/usr/bin/env python3
"""Phase 0 of the top-down plan (docs/16-topdown-generation-plan.md).

Reconstruct (tree + card + neighbour cards -> prose) training pairs for the
final leaf step T9, from already-built story trees. Deterministic and
offline: no model calls, stdlib only.

For every scene of every tree, one pair is emitted:

  input  = tree-above (root, expose, plot definitions + relevant chains,
           entity profiles, current + neighbouring events) with char budgets,
           plus the target scene's CARD, plus the cards of the 2 scenes
           before and the 2 scenes after it
  target = a REFERENCE (slug + scene_id), never prose -- unless
           --inline-prose is passed explicitly for local training. Published
           artifacts must be built without it (include_prose=False).

The blind rule (plan section 7.3): the input contains NO scene prose --
not the target's, not any neighbour's. Cards are loaded from `scenes/`
(which carries no full text), never from `scenes_with_text/`. A scene card
whose text fields match 8+ consecutive words of a co-located
`scenes_fulltext.json` entry is still structural metadata, but any pair
built with --inline-prose carries the raw prose and must not be committed.

Holdout is by FILM, never by scene: use --make-split to write slug lists;
a film's neighbourhood must never train while its target evaluates.

Usage:
  python3 topdown_pairs.py --trees /path/to/trees --out pairs.jsonl
  python3 topdown_pairs.py --hf-dir /path/to/hf-dataset --stats
  python3 topdown_pairs.py --trees /path/to/trees --out pairs.jsonl --inline-prose
  python3 topdown_pairs.py --make-split --trees /path/to/trees \\
      --ratio 0.05 --seed 7 --train train_slugs.txt --eval eval_slugs.txt
  python3 topdown_pairs.py --stats --trees /path/to/trees
"""

import argparse
import json
import os
import random
import sys
from pathlib import Path

# Char budgets from plan section 7.1. Truncation is marked, never silent.
BUDGETS = {
    "root": 8000,
    "expose": 12000,
    "plots": 8000,
    "entities": 8000,
    "events": 15000,
    "neighbour_card": 2000,
}

# Fields a neighbour card may carry. Deliberately small: who, what happens,
# what changes -- never prose, never evidence quotes.
NEIGHBOUR_KEYS = (
    "scene_id", "location", "time_of_day", "present",
    "summary", "what_changes", "dramatic_function",
)

TARGET_CARD_KEYS = NEIGHBOUR_KEYS + (
    "speaking", "objects_that_matter", "minds",
    "connects_back", "sets_up", "uncertain", "event_hint",
)


def _load(path, default=None):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return default


def _fit(obj, budget, text_keys=(), drop_keys=()):
    """Shrink a projected dict until its JSON fits `budget` chars.

    Shrinks long text fields first, then drops optional keys. Always
    returns a valid object -- never a cut-off JSON string.
    """
    s = json.dumps(obj, ensure_ascii=False)
    if len(s) <= budget:
        return obj
    for k in text_keys:
        v = obj.get(k)
        if isinstance(v, str) and len(s) > budget:
            obj[k] = v[:max(0, budget // 4)] + "…[truncated]"
            s = json.dumps(obj, ensure_ascii=False)
    if isinstance(obj.get("what_changes"), list) and len(s) > budget:
        obj["what_changes"] = obj["what_changes"][:4]
        s = json.dumps(obj, ensure_ascii=False)
    for k in drop_keys:
        if len(s) <= budget:
            break
        if k in obj:
            del obj[k]
            s = json.dumps(obj, ensure_ascii=False)
    if len(s) > budget:
        keep = {}
        for k in ("scene_id", "event_id"):
            if k in obj:
                keep[k] = obj[k]
        keep["_truncated"] = True
        obj.clear()
        obj.update(keep)
    return obj


def _cut(text, budget):
    """Truncate a tree-above section to budget chars, marking the cut.

    Returns a string (used as-is, never re-parsed as JSON), so cutting
    mid-structure is safe here -- unlike for projected cards.
    """
    if text is None:
        return None
    s = text if isinstance(text, str) else json.dumps(text, ensure_ascii=False)
    if len(s) <= budget:
        return s
    return s[:budget] + "\n…[truncated to %d chars]" % budget


def _scene_files(slug_dir):
    d = Path(slug_dir) / "scenes"
    if not d.is_dir():
        return []
    return sorted(d.glob("sc-*.json"))


def _project(node, keys, per_card_budget):
    proj = {k: node.get(k) for k in keys if k in node and node.get(k) not in (None, "", [], {})}
    if "what_changes" in proj and isinstance(proj["what_changes"], list):
        proj["what_changes"] = proj["what_changes"][:12]
    if "minds" in proj and isinstance(proj["minds"], list):
        proj["minds"] = proj["minds"][:8]
    if "present" in proj and isinstance(proj["present"], list):
        proj["present"] = proj["present"][:12]
    return _fit(proj, per_card_budget,
                text_keys=("summary", "dramatic_function"),
                drop_keys=("minds", "connects_back", "sets_up", "uncertain",
                           "objects_that_matter", "speaking", "event_hint",
                           "what_changes"))


def _event_of(scene_id, events):
    for e in events:
        if scene_id in (e.get("scene_ids") or []):
            return e
    return None


def _project_event(event, budget_each=3000):
    keys = ("event_id", "title", "summary", "action", "participants",
            "locations", "boundary_reason", "turns_on", "affects_outside")
    proj = {k: event.get(k) for k in keys
            if k in event and event.get(k) not in (None, "", [], {})}
    return _fit(proj, budget_each,
                text_keys=("summary", "action", "boundary_reason", "turns_on"),
                drop_keys=("affects_outside", "boundary_reason", "turns_on",
                           "locations", "participants"))


def build_pairs_from_parts(slug, nodes, events, root, expose, profiles, plots,
                           fulltext=None, inline_prose=False):
    """Yield one pair dict per scene. Pure function of the passed artifacts.

    Blind rule: `nodes` must carry no scene prose. Any `_scene_fulltext`
    key is dropped here again, so no caller can smuggle it in.
    """
    nodes = [n for n in (nodes or []) if n and n.get("scene_id")]
    for n in nodes:
        n.pop("_scene_fulltext", None)
    nodes.sort(key=lambda n: n["scene_id"])
    if not nodes:
        return
    events = events or []
    profiles = profiles or []
    plots = plots or {}
    fulltext = fulltext or {}

    # Entity lookup: prefer profiles whose evidence cites scenes in this
    # film; at pair time filter to the target + neighbour window.
    ev_scenes = {}
    for p in profiles:
        sids = set()
        for ev in (p.get("evidence") or []):
            if isinstance(ev, dict):
                sid = ev.get("scene_id")
            elif isinstance(ev, str):
                sid = ev
            else:
                continue
            if sid:
                sids.add(sid)
        ev_scenes[p.get("name", "?")] = sids

    for i, node in enumerate(nodes):
        sid = node["scene_id"]
        window = nodes[max(0, i - 2):i + 3]
        window_ids = {w["scene_id"] for w in window}

        neighbours = {
            "before": [_project(w, NEIGHBOUR_KEYS, BUDGETS["neighbour_card"])
                       for w in window if w["scene_id"] < sid],
            "after": [_project(w, NEIGHBOUR_KEYS, BUDGETS["neighbour_card"])
                      for w in window if w["scene_id"] > sid],
        }

        window_events, seen_ev = [], set()
        for w in window:
            e = _event_of(w["scene_id"], events)
            if e and e.get("event_id") not in seen_ev:
                seen_ev.add(e.get("event_id"))
                window_events.append(_project_event(e))

        # Entities: those whose evidence touches the window; cap by budget.
        ent_picks = [p for p in profiles if ev_scenes.get(p.get("name", "?"), set()) & window_ids]
        if not ent_picks:
            ent_picks = profiles[:4]
        entities_txt = _cut(
            [{"name": p.get("name"), "type": p.get("type"),
              "profile": p.get("profile"), "relationships": (p.get("relationships") or [])[:6]}
             for p in ent_picks[:8]], BUDGETS["entities"])

        # Plots: all definitions (small) + chains overlapping the window.
        defs = []
        chains = {}
        for pname, p in plots.items():
            d = p.get("definition", {}) or {}
            defs.append({k: d.get(k) for k in
                         ("spine", "agent", "goal", "resistance", "stakes", "outcome",
                          "name", "throughline", "theme_or_dilemma", "summary")
                         if d.get(k)})
            defs[-1]["plot"] = pname
            chain = p.get("chain") or []
            overlap = [c for c in chain
                       if isinstance(c, dict) and c.get("event_id") in seen_ev]
            if overlap:
                chains[pname] = overlap[:12]
        plots_txt = _cut({"definitions": defs, "relevant_chains": chains}, BUDGETS["plots"])

        tree_above = {
            "root": _cut(root, BUDGETS["root"]) if root else None,
            "expose": _cut(expose, BUDGETS["expose"]) if expose else None,
            "plots": plots_txt,
            "entities": entities_txt,
            "events": _cut(window_events, BUDGETS["events"]),
        }

        card = _project(node, TARGET_CARD_KEYS, BUDGETS["neighbour_card"] * 2)
        cur_event = _event_of(sid, events)

        usable, reason = True, None
        if not node.get("summary"):
            usable, reason = False, "target card has no summary"
        if cur_event is None:
            usable, reason = False, "scene maps to no event"
        if root is None or not events:
            usable, reason = False, "tree above incomplete (root/events missing)"

        pair = {
            "tid": "%s::scene_prose::%s" % (slug, sid),
            "slug": slug,
            "scene_id": sid,
            "usable": usable,
            "skip_reason": reason,
            "input": {
                "tree_above": tree_above,
                "card": card,
                "neighbours": neighbours,
            },
            "target": {"slug": slug, "scene_id": sid},
        }
        if inline_prose:
            pair["target"]["prose"] = fulltext.get(sid)
            if not pair["target"].get("prose"):
                pair["usable"] = False
                pair["skip_reason"] = "inline prose requested but missing for scene"
        yield pair


def build_pairs_for_slug(trees_dir, slug, inline_prose=False):
    """On-disk tree layout: trees/<slug>/{scenes,events,entities,...}."""
    sdir = Path(trees_dir) / slug
    files = _scene_files(sdir)
    if not files:
        return
    nodes = [_load(f) for f in files]
    events = (_load(sdir / "events" / "events.json", {}) or {}).get("events", []) or []
    root = _load(sdir / "root" / "story_root.json")
    expose = _load(sdir / "expose" / "expose.json")
    profiles = _load(sdir / "entities" / "profiles.json", []) or []
    plots_doc = _load(sdir / "plots" / "plots.json", {}) or {}
    plots = plots_doc.get("plots", {}) or {}
    fulltext = _load(sdir / "scenes_fulltext.json", {}) or {} if inline_prose else {}
    yield from build_pairs_from_parts(slug, nodes, events, root, expose,
                                      profiles, plots, fulltext, inline_prose)


def build_pairs_from_hf(film, inline_prose=False):
    """Hugging Face layout: one dict per film with `slug` + `layers.*`.

    `original_script` is NEVER admitted to the input (blind rule) -- it is
    the prose the model must learn to write. --inline-prose is unsupported
    here because the dataset ships the full script without per-scene spans,
    so prose cannot be attributed to a scene card.
    """
    if inline_prose:
        raise SystemExit("--inline-prose is not supported with --hf-dir: the dataset "
                         "ships the full script without per-scene spans, so prose cannot "
                         "be attributed to a scene card.")
    layers = film.get("layers", {}) or {}
    slug = film.get("slug", "?")
    nodes = [dict(n) for n in (layers.get("scenes") or []) if isinstance(n, dict)]
    events = layers.get("events") or []
    root = layers.get("root")
    expose = layers.get("expose")
    profiles = layers.get("entities") or []
    plots = layers.get("plots") or {}
    return build_pairs_from_parts(slug, nodes, events, root, expose,
                                  profiles, plots, {}, False)


def iter_hf_slugs(hf_dir):
    d = Path(hf_dir) / "data"
    if not d.is_dir():
        return []
    return sorted(p.stem for p in d.glob("*.json"))


def iter_slugs(trees_dir):
    p = Path(trees_dir)
    if not p.is_dir():
        return []
    return sorted(d.name for d in p.iterdir() if d.is_dir() and _scene_files(d))


def make_split(slugs, ratio, seed):
    rng = random.Random(seed)
    order = list(slugs)
    rng.shuffle(order)
    n_eval = max(1, int(len(order) * ratio)) if order else 0
    return order[n_eval:], order[:n_eval]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--trees", default=os.environ.get("STORYTREE_TREES", "trees"))
    ap.add_argument("--hf-dir", default=None,
                    help="Hugging Face dataset root (data/<slug>.json + index.jsonl); "
                         "alternative to --trees")
    ap.add_argument("--out", default=None)
    ap.add_argument("--slugs", default=None,
                    help="file with one slug per line; default: all slugs under --trees")
    ap.add_argument("--inline-prose", action="store_true",
                    help="include scene prose in target (local training only; never commit output)")
    ap.add_argument("--make-split", action="store_true")
    ap.add_argument("--ratio", type=float, default=0.05)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--train", default="train_slugs.txt")
    ap.add_argument("--eval", default="eval_slugs.txt")
    ap.add_argument("--stats", action="store_true")
    args = ap.parse_args(argv)

    if args.make_split:
        if args.hf_dir:
            slugs = iter_hf_slugs(args.hf_dir)
        else:
            slugs = iter_slugs(args.trees)
        train, eval_ = make_split(slugs, args.ratio, args.seed)
        Path(args.train).write_text("\n".join(train) + ("\n" if train else ""), encoding="utf-8")
        Path(args.eval).write_text("\n".join(eval_) + ("\n" if eval_ else ""), encoding="utf-8")
        print("slugs=%d train=%d eval=%d (by film)" % (len(slugs), len(train), len(eval_)))
        return 0

    if args.slugs:
        slugs = [l.strip() for l in Path(args.slugs).read_text(encoding="utf-8").splitlines()
                 if l.strip()]
    elif args.hf_dir:
        slugs = iter_hf_slugs(args.hf_dir)
    else:
        slugs = iter_slugs(args.trees)

    def pairs_for(slug):
        if args.hf_dir:
            film = _load(Path(args.hf_dir) / "data" / (slug + ".json"))
            if not film:
                return
            yield from build_pairs_from_hf(film, inline_prose=args.inline_prose)
        else:
            yield from build_pairs_for_slug(args.trees, slug, inline_prose=args.inline_prose)

    if args.stats and args.out is None:
        total = usable = 0
        reasons = {}
        for slug in slugs:
            for pair in pairs_for(slug):
                total += 1
                if pair["usable"]:
                    usable += 1
                else:
                    reasons[pair["skip_reason"]] = reasons.get(pair["skip_reason"], 0) + 1
        print("slugs=%d pairs=%d usable=%d unusable=%d" % (len(slugs), total, usable, total - usable))
        for r, c in sorted(reasons.items(), key=lambda x: -x[1]):
            print("  %-55s %d" % (r, c))
        return 0

    out = open(args.out, "w", encoding="utf-8") if args.out else sys.stdout
    n = u = 0
    with out:
        for slug in slugs:
            for pair in pairs_for(slug):
                out.write(json.dumps(pair, ensure_ascii=False) + "\n")
                n += 1
                u += bool(pair["usable"])
    print("wrote %d pairs (%d usable) for %d films" % (n, u, len(slugs)), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
