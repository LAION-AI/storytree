"""Mechanical A/B counters for the model-notes addendum.

The rubric evaluation needs a strong reader and takes an hour. These counters
take a second and check exactly the failures the addendum was written against,
so an experiment can be rejected quickly before spending an evaluator on it.

Every counter here corresponds to one clause of the addendum. If a clause has no
counter it is not being tested, and the write-up should say so rather than
implying the whole prompt was validated.

    python3 tools/measure_addendum.py runs/matrix sc-001 sc-002
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scriptforge import screenplay as sp

# Flip conditions that restate the genre instead of naming a fact that could
# have been otherwise. Measured as Qwen's characteristic failure: every
# alternative's flip condition was a variant of "if this were a different work".
GENERIC_FLIP = re.compile(
    r"if (this|the (story|work|film|script|scene)) (were|was|had been)"
    r"|different (kind of |type of )?(work|story|film|genre|tone)"
    r"|in (a|another) (different|other) (work|story|film|genre)"
    r"|were (this|it) a ",
    re.I)


def _txt(o) -> str:
    return json.dumps(o, ensure_ascii=False) if not isinstance(o, str) else o


def measure(path: Path, scene, declared: set[str]) -> dict:
    tr = json.loads(path.read_text())
    dec = tr.get("decision") or {}
    craft = tr.get("craft") or {}
    spec = tr.get("specimen") or {}

    # --- C: envelope discipline. Does the decision stay in the given room? ---
    loc = (scene.location or "").lower()
    key = [w for w in re.findall(r"[a-z']{4,}", loc) if w not in
           ("the", "and", "int", "ext", "city")]
    body = (_txt(dec.get("resolution")) + " " + _txt(craft)).lower()
    loc_hits = sum(1 for w in key if w in body)
    in_envelope = bool(key) and loc_hits >= max(1, len(key) // 2)

    # --- roster: every specimen speaker must be on the given cast list ---
    lines = spec.get("lines") or []
    speakers = {l.get("speaker") for l in lines if isinstance(l, dict)}
    roster = {s.lower() for s in (scene.speakers or [])}
    # speakers are entity ids; a cue matches if any roster cue shares a stem
    unlisted = len(speakers)  # resolved by the caller against the id map

    # --- A: confidence calibration ---
    conf = dec.get("confidence")
    conf = conf if isinstance(conf, (int, float)) else None

    # --- B: alternatives are things you nearly chose ---
    alts = craft.get("why_not_otherwise") or craft.get("alternatives_rejected") or []
    if isinstance(alts, dict):
        alts = list(alts.values())
    alt_n = len(alts) if isinstance(alts, list) else 0
    generic = sum(1 for a in (alts if isinstance(alts, list) else [])
                  if GENERIC_FLIP.search(_txt(a)))

    # --- 2 (shared): state changes must name a declared variable ---
    sci = dec.get("state_changes_implied") or []
    if isinstance(sci, dict):
        sci = list(sci.values())
    named = 0
    for c in sci if isinstance(sci, list) else []:
        v = (c.get("variable") or c.get("state_variable") or "") if isinstance(c, dict) else ""
        if v and v in declared:
            named += 1

    return {"in_envelope": in_envelope, "loc_hits": f"{loc_hits}/{len(key)}",
            "confidence": conf, "alts": alt_n, "generic_flips": generic,
            "specimen_lines": len(lines), "speakers": len(speakers),
            "state_changes": len(sci) if isinstance(sci, list) else 0,
            "state_declared": named,
            "words": len(_txt(tr).split())}


if __name__ == "__main__":
    project = Path(sys.argv[1])
    scene_ids = sys.argv[2:]

    table = json.loads((project / "script_map.json").read_text())
    _raw = Path(table["source_file"]).read_text(errors="replace")
    # offsets index the CLEANED text; slice that, not the raw file
    script, parsed = sp.parse(_raw)
    scenes = {s.scene_id: s for s in parsed}

    ents = (json.loads((project / "artifacts" / "entities.json").read_text())
            .get("entities", {}))
    declared = {v for e in ents.values() for v in (e.get("state_variables") or {})}
    declared |= {v for e in ents.values() for v in (e.get("state") or {})}

    arms = [("baseline", "transitions_qwen"),
            ("addendum", "transitions_qwen_addendum")]

    print(f"{'scene':<8} {'arm':<9} {'envelope':>9} {'conf':>5} {'alts':>5} "
          f"{'generic':>8} {'spec':>5} {'state ok':>9} {'words':>7}")
    print("-" * 74)
    agg: dict = {}
    for sid in scene_ids:
        for label, folder in arms:
            p = project / folder / f"{sid}.json"
            if not p.exists():
                continue
            m = measure(p, scenes[sid], declared)
            agg.setdefault(label, []).append(m)
            print(f"{sid:<8} {label:<9} "
                  f"{('YES ' + m['loc_hits']) if m['in_envelope'] else ('no  ' + m['loc_hits']):>9} "
                  f"{str(m['confidence'] or '-'):>5} {m['alts']:>5} {m['generic_flips']:>8} "
                  f"{m['specimen_lines']:>5} "
                  f"{str(m['state_declared']) + '/' + str(m['state_changes']):>9} "
                  f"{m['words']:>7,}")
    print()
    for label, rows in agg.items():
        n = len(rows)
        cf = [r["confidence"] for r in rows if r["confidence"] is not None]
        print(f"{label:<9} n={n}  in-envelope {sum(1 for r in rows if r['in_envelope'])}/{n}  "
              f"mean confidence {sum(cf)/len(cf) if cf else float('nan'):.0f}  "
              f"alts {sum(r['alts'] for r in rows)}  "
              f"generic flips {sum(r['generic_flips'] for r in rows)}  "
              f"state ok {sum(r['state_declared'] for r in rows)}/{sum(r['state_changes'] for r in rows)}  "
              f"words {sum(r['words'] for r in rows)//n:,}")
