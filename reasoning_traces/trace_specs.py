#!/usr/bin/env python3
"""Task specs for hindsight-CoT generation across ALL tree layers.

Each spec is a dict:
  tid      unique task id  "<slug>::<layer>::<part>"
  slug     tree slug
  layer    scene_facts | scene_minds | event_compose | event_reconcile |
           meta_section | meta_perspectives | entity_profile | root |
           expose | plot_identify | plot_chain
  task     the instruction the *student* model will see (production wording)
  context  the input material the student model will see
  target   the JSON artifact the student model must produce

Context is reconstructed to match production inputs as closely as the
persisted artifacts allow. Where production fed an intermediate that was
never written to disk (entity phase-1 research, root spine facts), the
equivalent source material is substituted and that is noted per layer.

One deliberate divergence from production: the scene `minds` pass in
scene_variants.py L563-565 feeds The Matrix's events to every tree via a
hardcoded default path. Here the tree's OWN events are used.
"""
import json, os, sys
from pathlib import Path

import config
config.install_paths()
import meta_layer as ml  # noqa: E402
import entity_layer as el  # noqa: E402

TREES = config.TREES

FACT_KEYS = ["scene_id", "location", "time_of_day", "present", "speaking",
             "summary", "what_changes", "objects_that_matter", "event_hint",
             "uncertain"]
MIND_KEYS = ["minds", "connects_back", "sets_up", "dramatic_function"]

SECTION_KEY = {"themes": None, "external": "conflicts",
               "internal": "internal_conflicts",
               "relationships": "relationship_arcs"}


def _j(o, cap=None):
    s = json.dumps(o, ensure_ascii=False, indent=1)
    return s[:cap] if cap else s


def _load(p, default=None):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception:
        return default


# ---------------------------------------------------------------- scenes
def scene_specs(slug):
    """1 facts spec per scene; 1 minds spec per scene that ran the mind pass."""
    d = TREES / slug / "scenes_with_text"
    if not d.is_dir():
        return
    files = sorted(d.glob("sc-*.json"))
    nodes = []
    for f in files:
        n = _load(f)
        if n:
            nodes.append(n)
    # event lookup for the minds pass (the tree's OWN events, not Matrix's)
    events = (_load(TREES / slug / "events" / "events.json", {}) or {}).get("events", [])
    scene_to_ev = {}
    for i, ev in enumerate(events):
        for sid in ev.get("scene_ids", []):
            scene_to_ev[sid] = i

    for i, n in enumerate(nodes):
        sid = n.get("scene_id")
        text = n.get("_scene_fulltext", "") or ""
        wc = len(text.split())
        if wc < 40:
            guide = ("This is a very short scene. One or two changes is right. "
                     "Psychology beyond a sentence would be invention.")
        elif wc < 150:
            guide = "A short scene. Two or three changes, briefly reasoned."
        else:
            guide = "A full scene. Develop the changes and what drives them."
        prior = "\n\n".join(
            (nodes[k].get("_scene_fulltext", "") or "")[:2200]
            for k in range(max(0, i - 3), i))[-6000:]

        facts = {k: n[k] for k in FACT_KEYS if k in n}
        yield {
            "tid": f"{slug}::scene_facts::{sid}",
            "slug": slug, "layer": "scene_facts", "part": sid,
            "task": (f"Describe scene {sid}. It is {wc} words long. {guide} "
                     "The scene on the page is the only source. Record what "
                     "changes, who is present and speaking, what objects "
                     "matter, and what the scene sets up -- never reusing "
                     "eight or more consecutive words from the page except "
                     "in `evidence`, which is copied exactly and at most "
                     "seven words."),
            "context": (f"THE SCENE (your only source):\n{text[:14000]}\n\n"
                        f"THE PRECEDING SCENES, so you know who people are. "
                        f"Do not describe them:\n{prior}"),
            "target": facts,
        }

        if str(n.get("_mind_pass", "")).startswith("ran:") and n.get("minds"):
            ei = scene_to_ev.get(sid)
            own = later = "(none)"
            if ei is not None:
                e = events[ei]
                own = _j({"event_id": e.get("event_id"), "name": e.get("title"),
                          "what_happens": e.get("summary")})
                later = _j([{"event_id": x.get("event_id"), "name": x.get("title"),
                             "what_happens": (x.get("summary") or "")[:260]}
                            for x in events[ei + 1:ei + 7]])
            yield {
                "tid": f"{slug}::scene_minds::{sid}",
                "slug": slug, "layer": "scene_minds", "part": sid,
                "task": ("Now read the same scene for interiority. For each "
                         "person who carries the scene, record what they want, "
                         "what they feel, what they show, and what they "
                         "wrongly believe about another -- each grounded in "
                         "the page. Then state what this scene connects back "
                         "to, what it sets up, and its dramatic function. "
                         "Stated concealment is not subtext. Where a scene "
                         "carries no interiority, an empty list is correct."),
                "context": (f"THE SCENE:\n{text[:12000]}\n\n"
                            f"THE FACTS ALREADY RECORDED FOR IT:\n{_j(facts)}\n\n"
                            f"THE PRECEDING SCENES:\n{prior[:9000]}\n\n"
                            f"THE EVENT THIS SCENE BELONGS TO:\n{own}\n\n"
                            f"THE EVENTS THAT FOLLOW:\n{later}"),
                "target": {k: n[k] for k in MIND_KEYS if k in n},
            }


# ---------------------------------------------------------------- events
def event_specs(slug):
    """1 compose spec per event; 1 reconcile spec per reconciled event."""
    partial = (_load(TREES / slug / "events" / "events.partial.json", {}) or {}).get("events", [])
    final = (_load(TREES / slug / "events" / "events.json", {}) or {}).get("events", [])
    fulltext = _load(TREES / slug / "scenes_fulltext.json", {}) or {}
    sdir = TREES / slug / "scenes"

    by_id = {e.get("event_id"): e for e in final}

    for e in partial:
        eid = e.get("event_id")
        sids = e.get("scene_ids", [])
        briefs = []
        for sid in sids:
            n = _load(sdir / f"{sid}.json")
            if n:
                briefs.append({k: n.get(k) for k in
                               ("scene_id", "location", "present", "summary",
                                "what_changes", "objects_that_matter",
                                "uncertain", "minds", "dramatic_function")})
        cap = 3000 if len(sids) <= 4 else 1200 if len(sids) <= 10 else 700
        text = "\n\n".join(f"--- {sid} ---\n{(fulltext.get(sid) or '')[:cap]}"
                           for sid in sids)
        roster = e.get("_roster") or []
        target = {k: e[k] for k in
                  ("title", "summary", "action", "participants", "locations",
                   "state_triples", "affects_outside", "turns_on",
                   "turns_on_entity", "carried_uncertainty") if k in e}
        yield {
            "tid": f"{slug}::event_compose::{eid}",
            "slug": slug, "layer": "event_compose", "part": eid,
            "task": ("Compose the EVENT that these consecutive scenes form. "
                     "Give it a title, a summary and an action line; name its "
                     "participants and locations; and for every entity record "
                     "its state triples -- for each register that moved, its "
                     "entry state, the change and its exit state with the "
                     "scene that evidences it, and for each that did not "
                     "move, why not. State what the event enables or blocks "
                     "outside itself, what it turns on, and what uncertainty "
                     "it carries forward."),
            "context": (f"THE ENTITY ROSTER FOR THIS EVENT:\n{_j(roster)[:6000]}\n\n"
                        f"THE SCENE NODES:\n{_j(briefs)[:40000]}\n\n"
                        f"THE SCREENPLAY TEXT OF THOSE SCENES:\n{text[:40000]}"),
            "target": target,
        }

        fin = by_id.get(eid)
        if fin and "prose_before_reconcile" in fin:
            moved = []
            for t in fin.get("state_triples", []):
                regs = {r: v for r, v in (t.get("registers") or {}).items()
                        if isinstance(v, dict) and v.get("moved")}
                if regs:
                    moved.append({"entity": t.get("entity"),
                                  "reading": t.get("reading"), "registers": regs})
            yield {
                "tid": f"{slug}::event_reconcile::{eid}",
                "slug": slug, "layer": "event_reconcile", "part": eid,
                "task": ("Rewrite this event's summary, action and turns_on so "
                         "they agree exactly with the state triples below. "
                         "Nothing may be asserted in the prose that the "
                         "triples do not carry, and nothing the triples "
                         "record may be missing from the prose."),
                "context": (f"TITLE: {fin.get('title')}\n\n"
                            f"THE STATE TRIPLES THAT MOVED:\n{_j(moved)[:30000]}\n\n"
                            f"THE PROSE AS IT STANDS:\n"
                            f"{_j(fin.get('prose_before_reconcile'))[:8000]}"),
                "target": {k: fin.get(k) for k in ("summary", "action", "turns_on")},
            }


# ------------------------------------------------------------------ meta
def meta_specs(slug):
    meta = _load(TREES / slug / "meta" / "meta.json")
    events = (_load(TREES / slug / "events" / "events.json", {}) or {}).get("events", [])
    if not meta or not events:
        return
    digest = ml.build_digest(events)
    for section, key in SECTION_KEY.items():
        if key is None:
            tgt = {k: meta.get("themes", {}).get(k)
                   for k in ("big_questions", "central_dilemma")}
            if not tgt.get("big_questions"):
                continue
        else:
            # meta.json nests each section: meta["external"]["conflicts"]
            val = (meta.get(section) or {}).get(key)
            if not val:
                continue
            tgt = {key: val}
        yield {
            "tid": f"{slug}::meta_section::{section}",
            "slug": slug, "layer": "meta_section", "part": section,
            "task": ml.PROMPTS[section] + " Every item must cite evidence: "
                    "the event id, the scene id under it, and what in that "
                    "scene grounds the claim.",
            "context": f"THE EVENT LAYER:\n{digest[:55000]}",
            "target": tgt,
        }
    if meta.get("perspectives"):
        dilemma = _j(meta.get("themes", {}).get("central_dilemma", {}))
        yield {
            "tid": f"{slug}::meta_perspectives::all",
            "slug": slug, "layer": "meta_perspectives", "part": "all",
            "task": ml.PROMPTS["perspectives"] + " Every item must cite "
                    "evidence grounding it in an event and scene.",
            "context": (f"THE CENTRAL DILEMMA:\n{dilemma}\n\n"
                        f"THE EVENT LAYER:\n{digest[:50000]}"),
            "target": {"perspectives": meta["perspectives"]},
        }


# --------------------------------------------------------------- entities
def entity_specs(slug):
    """Production fed phase-1 research (never persisted). Substitute the
    scene material that research was itself drawn from."""
    profiles = _load(TREES / slug / "entities" / "profiles.json", []) or []
    sdir = TREES / slug / "scenes"
    for prof in profiles:
        name = prof.get("name")
        if not name:
            continue
        # the profile's own evidence names the scenes it rests on -- a far
        # better context source than substring-matching the long descriptive
        # name ("WILL -- the Stratford-born hired player and ...") against
        # scene JSON, which never contains it verbatim.
        sids, seen = [], set()
        for ev in (prof.get("evidence") or []):
            sid = ev.get("scene_id")
            if sid and sid not in seen:
                seen.add(sid)
                sids.append(sid)
        mat = []
        for sid in sids:
            n = _load(sdir / f"{sid}.json")
            if n:
                mat.append({"scene_id": n.get("scene_id"),
                            "location": n.get("location"),
                            "present": (n.get("present") or [])[:12],
                            "summary": n.get("summary"),
                            "what_changes": (n.get("what_changes") or [])[:12],
                            "minds": (n.get("minds") or [])[:8]})
        if not mat:
            continue
        fields = [k for k in prof.keys()
                  if k not in ("evidence", "_research_facts", "_scenes_touched")]
        prof = {k: v for k, v in prof.items()
                if k not in ("_research_facts", "_scenes_touched")}
        yield {
            "tid": f"{slug}::entity_profile::{name}",
            "slug": slug, "layer": "entity_profile", "part": name,
            "task": (f"Compile the standard profile of '{name}'. Third "
                     "person; concrete; no category words; typical sentences "
                     "are paraphrased or invented in the voice's style, never "
                     "quoted. Invent nothing factual -- everything must come "
                     "from the scene material. Every evidence entry cites a "
                     "real scene id.\nFIELDS: " + ", ".join(fields)),
            "context": f"THE SCENE MATERIAL FOR THIS ENTITY:\n{_j(mat)[:50000]}",
            "target": prof,
        }


# ------------------------------------------------------------------ root
def root_specs(slug):
    root = _load(TREES / slug / "root" / "story_root.json")
    meta = _load(TREES / slug / "meta" / "meta.json")
    events = (_load(TREES / slug / "events" / "events.json", {}) or {}).get("events", [])
    ents = _load(TREES / slug / "entities" / "profiles.json", []) or []
    if not root or not events:
        return
    digest = ml.build_digest(events)
    names = [e.get("name", "?") for e in ents]
    yield {
        "tid": f"{slug}::root::all",
        "slug": slug, "layer": "root", "part": "all",
        "task": ("Fill the STORY ROOT for this screenplay. Every field must "
                 "agree with the layers below; do not invent beyond them. "
                 "ANTI-FLOSKEL RULE, applies to EVERY field: an abstract "
                 "claim without a concrete anchor is worthless -- every "
                 "strength, weakness, dilemma or theme must cite a specific "
                 "moment (a scene or event id, a named concrete situation). "
                 "If a sentence could survive with the proper nouns swapped "
                 "out, it is not finished. identification_value needs both "
                 "halves mechanically connected: an admirable strength shown "
                 "to cost something in named scenes, an opening vulnerability "
                 "the audience recognises from their own life, and the exact "
                 "mechanism linking them. rules_of_the_world are constraints "
                 "the script actually obeys. entity_roster covers every "
                 "entity whose removal would change the plot."),
        "context": (f"THE EVENT LAYER:\n{digest[:55000]}\n\n"
                    f"THE META LAYER:\n{_j(meta)[:30000]}\n\n"
                    f"THE ENTITY ROSTER:\n{json.dumps(names)}"),
        "target": root,
    }


# ---------------------------------------------------------------- expose
def expose_specs(slug):
    exp = _load(TREES / slug / "expose" / "expose.json")
    root = _load(TREES / slug / "root" / "story_root.json")
    meta = _load(TREES / slug / "meta" / "meta.json")
    events = (_load(TREES / slug / "events" / "events.json", {}) or {}).get("events", [])
    ents = _load(TREES / slug / "entities" / "profiles.json", []) or []
    if not exp or not events:
        return
    digest = ml.build_digest(events)
    ectx = [{k: e.get(k) for k in ("name", "appearance")} for e in ents]
    yield {
        "tid": f"{slug}::expose::all",
        "slug": slug, "layer": "expose", "part": "all",
        "task": ("Write the EXPOSE of this story in three parts. (1) "
                 "ending_first: tell how it ends, plainly. (2) synopsis: five "
                 "to ten numbered sections (keys s01, s02, ...) that retell "
                 "the story causally from beginning to end -- introduce every "
                 "named entity in context, keep every plot thread "
                 "recognisable, and let the human-experience questions "
                 "surface through what happens rather than as statements. "
                 "(3) jacket_copy: back-cover text that sells the book "
                 "without spoiling the ending. Everything must agree with the "
                 "layers below; invent nothing. Vary sentence length "
                 "naturally, mostly 10-25 words -- avoid both long "
                 "comma-stacked sentences and monotonous staccato."),
        "context": (f"THE STORY ROOT:\n{_j(root)[:8000]}\n\n"
                    f"THE EVENT LAYER:\n{digest[:50000]}\n\n"
                    f"THE META LAYER:\n{_j(meta)[:25000]}\n\n"
                    f"THE ENTITIES:\n{_j(ectx)[:12000]}"),
        "target": exp,
    }


# ----------------------------------------------------------------- plots
def plot_specs(slug):
    plots = (_load(TREES / slug / "plots" / "plots.json", {}) or {}).get("plots", {})
    meta = _load(TREES / slug / "meta" / "meta.json")
    events = (_load(TREES / slug / "events" / "events.json", {}) or {}).get("events", [])
    if not plots or not events:
        return
    digest = ml.build_digest(events)
    dilemma = _j(meta.get("themes", {}).get("central_dilemma", {}))
    questions = json.dumps(meta.get("themes", {}).get("big_questions", []),
                           ensure_ascii=False)[:4000]

    defs = [p.get("definition", {}) for p in plots.values()]
    yield {
        "tid": f"{slug}::plot_identify::all",
        "slug": slug, "layer": "plot_identify", "part": "all",
        "task": ("Define the PLOTS of this story. A plot is ONE perspective "
                 "on a theme or dilemma of human existence, told as a causal "
                 "chain of events: each event conditions the next INSIDE the "
                 "plot. Cover the classic perspectives where the material "
                 "supports them. Summarise each plot in about three "
                 "sentences."),
        "context": (f"THE CENTRAL DILEMMA:\n{dilemma}\n\n"
                    f"THE BIG QUESTIONS:\n{questions}\n\n"
                    f"THE EVENT LAYER:\n{digest[:60000]}"),
        "target": {"plots": defs},
    }

    for name, p in plots.items():
        chain = p.get("chain")
        if not chain:
            continue
        yield {
            "tid": f"{slug}::plot_chain::{name}",
            "slug": slug, "layer": "plot_chain", "part": name,
            "task": ("Mark every event of the layer that BELONGS to this "
                     "plot, in story order. PERSPECTIVE DISCIPLINE: include "
                     "only events that advance THIS plot's stance and its "
                     "stated carrier. Do NOT include an event just because "
                     "the protagonist acts in it; it must tip THIS outlook "
                     "specifically. MEMBERSHIP: no padding -- if an event "
                     "merely happens nearby and does not move this plot's "
                     "causal spine, skip it. SELF-CONTAINED CAUSALITY: each "
                     "event must be caused or enabled by the PREVIOUS event "
                     "in THIS chain."),
            "context": (f"THE PLOT:\n{_j(p.get('definition', {}))}\n\n"
                        f"THE CENTRAL DILEMMA:\n{dilemma}\n\n"
                        f"THE EVENT LAYER:\n{digest[:60000]}"),
            "target": {"chain": chain},
        }


BUILDERS = [scene_specs, event_specs, meta_specs, entity_specs,
            root_specs, expose_specs, plot_specs]


def all_specs(slugs):
    for slug in slugs:
        for b in BUILDERS:
            try:
                for spec in b(slug):
                    yield spec
            except Exception as e:
                print(f"[{slug}] {b.__name__} FAILED: {e}", file=sys.stderr)


if __name__ == "__main__":
    slugs = json.load(open(sys.argv[1]))
    from collections import Counter
    c = Counter()
    n = 0
    for s in all_specs(slugs):
        c[s["layer"]] += 1
        n += 1
    print(f"TOTAL SPECS: {n}")
    for k, v in sorted(c.items(), key=lambda x: -x[1]):
        print(f"  {k:22s} {v}")
