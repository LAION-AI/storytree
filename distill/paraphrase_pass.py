#!/usr/bin/env python3
"""Find copied source text in built nodes and rewrite it, with a small model.

Runs after the scene layer and after the event layer. Three things happen, in
this order, and the order matters:

  1. **check**      every string in every node is scanned for runs of eight or
                    more consecutive source words (distill/verbatim.py).
  2. **trim**       `evidence` and the scene anchors are *supposed* to be verbatim -- that
                    is what makes a claim checkable against the page -- so they
                    are cut to seven words rather than rewritten. Rewriting them
                    would destroy the only field whose job is to be exact.
  3. **paraphrase** everything else is rewritten by a small model: direct speech
                    into reported speech in the third person, stage directions
                    into a description of the observable fact.

Then it checks again. A rewrite that still carries a run, or that has dropped a
name or a number, is retried; after three attempts the span is elided instead.
**The pass can always fall back to a safe answer**, which is why it is allowed
to use a model at all.

Why a small model is the right tool: this is a local edit with a hard, machine-
checkable success condition. Nothing about it needs the model that built the
node -- and a 27B running beside the big one costs almost nothing.

Usage
  # gate a build, change nothing
  python3 distill/paraphrase_pass.py --nodes runs/scenes_x --source SCRIPT --check-only

  # rewrite in place
  python3 distill/paraphrase_pass.py --nodes runs/scenes_x --source SCRIPT \\
      --ports 8110,8111 --model qwen3.8-27b --out runs/scenes_x_clean
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, "/home/deployer/laion/project-alexandria/screenplay/src")

import verbatim as V  # noqa: E402

try:
    from screenplay_ku.client import EndpointPool  # noqa: E402
except Exception:                                   # pragma: no cover
    EndpointPool = None

# Fields whose whole point is to be exact. Cut, never reworded.
# `evidence` and the anchors exist to be exact. `basis` does not -- its schema
# asks what supports a reading, which is a paraphrase -- so it is rewritten like
# any other prose field rather than cut.
VERBATIM_FIELDS = {"evidence", "start_quote", "end_quote"}
VERBATIM_WORD_CAP = 7          # one below the bar

SYSTEM = """\
You rewrite short passages that accidentally copied a screenplay word for word.

You are given one field from a structured record, with the copied stretches
marked «like this», and the screenplay lines they came from.

Rewrite ONLY the marked stretches. Leave every other word of the field alone.

  * If the copied stretch is SPEECH, convert it to reported speech in the third
    person. Do not keep the speaker's words; say what they communicated.
      «I said, is everything in place?»
      -> she asks again whether everything is ready
  * If it is a STAGE DIRECTION or description, state the same observable fact in
    your own words.
      «The lamp swings above the table, throwing shadows that refuse to settle»
      -> the lamp keeps swinging and the shadows never come to rest
  * Keep every proper name, number, date, time and place name EXACTLY as given.
    These are facts and must not be reworded.
  * Do not add anything that is not already in the field. Do not remove
    information. Do not comment on the screenplay.
  * The rewrite must not reuse eight consecutive words from the screenplay.

Return JSON: {"rewritten": "<the whole field, with only the marked stretches changed>"}
"""

SCHEMA = {
    "type": "object",
    "properties": {"rewritten": {"type": "string", "maxLength": 4000}},
    "required": ["rewritten"],
    "additionalProperties": False,
}

_NUM = re.compile(r"\d[\d,.:/-]*")
_ALLCAPS = re.compile(r"\b[A-Z][A-Z'\-]{2,}\b")
_CAPPED = re.compile(r"\b[A-Z][A-Za-z'\-]{2,}\b")

# Written-out quantities. The first version protected only digits, so a rewrite
# turning "a two-hundred-fifty pound sack" into "a heavy body" passed the fact
# check while deleting the number it was meant to protect.
_WORD_NUM = re.compile(
    r"\b(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
    r"twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred|thousand|"
    r"million|dozen|first|second|third|fourth|fifth)\b", re.I)

# Fields that name entities. A capitalised word is protected when the node
# itself treats it as a name -- which is grounded in the record rather than in
# orthography. Protecting every capitalised word instead forced an elision
# because a rewrite dropped the word "Savior" from inside a quotation.
ROSTER_FIELDS = {"participants", "present", "who", "entity", "canonical_name",
                 "speaking", "locations", "turns_on_entity", "aliases"}


def roster(node) -> set:
    out = set()

    def walk(value, key=""):
        if isinstance(value, str):
            if key in ROSTER_FIELDS:
                out.update(w.lower() for w in _CAPPED.findall(value))
        elif isinstance(value, dict):
            for k, v in value.items():
                walk(v, k)
                if k in ROSTER_FIELDS and isinstance(v, dict):
                    out.update(str(x).lower() for x in v)
        elif isinstance(value, list):
            for v in value:
                walk(v, key)

    walk(node)
    return out


def _tidy(text: str) -> str:
    """Clean the punctuation a substitution leaves behind.

    Replacing a stretch inside a sentence routinely produces ",," or " ." at the
    seam. Cosmetic, but it is the visible trace of a machine edit and cheap to
    remove.
    """
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    text = re.sub(r"([,;:])\1+", r"\1", text)
    text = re.sub(r",\s*\.", ".", text)
    return re.sub(r"\s{2,}", " ", text).strip()


def facts_preserved(before: str, after: str, protected: Optional[set] = None) -> Optional[str]:
    """Which fact the rewrite dropped, if any."""
    missing_num = set(_NUM.findall(before)) - set(_NUM.findall(after))
    if missing_num:
        return "dropped number(s): " + ", ".join(sorted(missing_num))

    words_b = {w.lower() for w in _WORD_NUM.findall(before)}
    words_a = {w.lower() for w in _WORD_NUM.findall(after)}
    if words_b - words_a:
        return "dropped quantity word(s): " + ", ".join(sorted(words_b - words_a))

    folded = {w.lower() for w in _CAPPED.findall(after)}
    names_b = {w for w in _ALLCAPS.findall(before)}
    names_b |= {w for w in _CAPPED.findall(before)
                if protected and w.lower() in protected}
    missing_name = {n for n in names_b if n.lower() not in folded}
    if missing_name:
        return "dropped name(s): " + ", ".join(sorted(missing_name))
    return None


def mark(value: str, runs: Sequence[V.Run]) -> str:
    out, last = [], 0
    for run in sorted(runs, key=lambda r: r.start):
        out.append(value[last:run.start])
        out.append("«" + value[run.start:run.end] + "»")
        last = run.end
    out.append(value[last:])
    return "".join(out)


def trim_verbatim(value: str, cap: int = VERBATIM_WORD_CAP) -> str:
    """Cut an exact-by-design field to below the bar, keeping it exact."""
    sp = V.spans(value)
    if len(sp) <= cap:
        return value
    return value[:sp[cap - 1][1]]


def field_name(path: str) -> str:
    return path.rstrip("]").split("/")[-1].split("[")[0]


def rewrite_one(pool, value: str, runs: Sequence[V.Run], index: V.SourceIndex,
                path: str, *, attempts: int = 3,
                protected: Optional[set] = None) -> Tuple[str, str]:
    """Returns (new_value, outcome). Falls back to elision, never to the original."""
    contexts = []
    for run in runs:
        ctx = index.context(run.source_char)
        if ctx:
            contexts.append("--- screenplay, around one copied stretch ---\n" + ctx)
    prompt = "\n\n".join([
        "FIELD: {}".format(field_name(path)),
        "ROLE OF THE COPIED TEXT: " + ", ".join(
            sorted({"{} ({} confidence)".format(r.role, r.role_confidence) for r in runs})),
        "\n".join(contexts) if contexts else "(source context unavailable)",
        "--- the field, with copied stretches marked ---\n" + mark(value, runs),
    ])

    last_reason = "no attempt"
    for attempt in range(attempts):
        try:
            result = pool.call(SYSTEM, prompt, schema=SCHEMA,
                               temperature=0.2 + 0.2 * attempt,
                               max_tokens=1200)
            new = (json.loads(result.text) or {}).get("rewritten", "").strip()
            # The model is shown the copied stretches wrapped in guillemets and
            # returns them still wrapped often enough to matter.
            new = new.replace("\u00ab", "").replace("\u00bb", "").strip()
            new = _tidy(new)
        except Exception as error:
            last_reason = "call failed: {}".format(error)
            continue
        if not new:
            last_reason = "empty rewrite"
            continue
        still = index.exact_runs(new)
        if still:
            last_reason = "still carries {} word(s) verbatim".format(
                max(r.words for r in still))
            continue
        dropped = facts_preserved(value, new, protected)
        if dropped:
            last_reason = dropped
            continue
        if not (0.5 * len(value) <= len(new) <= 1.8 * len(value)):
            last_reason = "length moved from {} to {}".format(len(value), len(new))
            continue
        return new, "rewritten (attempt {})".format(attempt + 1)

    # The floor. Eliding is always available and always safe, so a model that
    # cannot produce a clean rewrite costs quality, never correctness.
    elided, _n = _elide(value, runs)
    return elided, "elided after {} attempt(s): {}".format(attempts, last_reason)


def _elide(value: str, runs: Sequence[V.Run], keep: int = 5) -> Tuple[str, int]:
    pieces, last = [], 0
    for run in sorted(runs, key=lambda r: r.start):
        pieces.append(value[last:run.start])
        sp = V.spans(value[run.start:run.end])
        cut = run.start + (sp[keep - 1][1] if len(sp) >= keep else 0)
        pieces.append(value[run.start:cut] + " [...]")
        last = run.end
    pieces.append(value[last:])
    return "".join(pieces), len(runs)


def process_node(node, index: V.SourceIndex, pool) -> List[Dict[str, Any]]:
    """Rewrite in place. Returns one record per field touched."""
    log: List[Dict[str, Any]] = []
    protected = roster(node)
    hits = [(p, r) for p, r in V.scan_node(node, index, near=False)]
    by_field: Dict[str, List[V.Run]] = {}
    for path, run in hits:
        by_field.setdefault(path, []).append(run)

    for path, runs in by_field.items():
        value = dict(V.walk(node)).get(path)
        if value is None:
            continue
        name = field_name(path)

        if name in VERBATIM_FIELDS:
            new = trim_verbatim(value)
            outcome = "trimmed to {} words (exact by design)".format(VERBATIM_WORD_CAP)
        elif all(r.is_probably_facts for r in runs):
            # A run that is only names and numbers is not a copy of anyone's
            # prose, and rewriting it would make the node wrong.
            log.append({"path": path, "outcome": "kept: names and numbers only",
                        "words": max(r.words for r in runs)})
            continue
        elif pool is None:
            new, outcome = _elide(value, runs)[0], "elided (no model available)"
        else:
            new, outcome = rewrite_one(pool, value, runs, index, path,
                                       protected=protected)

        V.set_at(node, path, new)
        log.append({"path": path, "outcome": outcome,
                    "words": max(r.words for r in runs),
                    "role": runs[0].role, "before": value[:160], "after": new[:160]})
    return log


# ---------------------------------------------------------------------------


def load_nodes(target: Path) -> List[Tuple[Path, Any, str]]:
    """(path, data, kind) for a scene directory or an events.json."""
    if target.is_dir():
        return [(p, json.loads(p.read_text(encoding="utf-8")), "scene")
                for p in sorted(target.glob("sc-*.json"))]
    data = json.loads(target.read_text(encoding="utf-8"))
    return [(target, data, "events")]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--nodes", required=True, help="scene dir, or an events.json")
    ap.add_argument("--source", required=True)
    ap.add_argument("--out", default="", help="where to write; default is in place")
    ap.add_argument("--ports", default="8110")
    ap.add_argument("--model", default="qwen3.8-27b")
    ap.add_argument("--check-only", action="store_true",
                    help="report and exit non-zero; change nothing")
    ap.add_argument("--report", default="")
    a = ap.parse_args()

    index = V.SourceIndex(Path(a.source).read_text(encoding="utf-8", errors="ignore"))
    items = load_nodes(Path(a.nodes))

    # ---- check -----------------------------------------------------------
    total_exact = total_near = dirty = 0
    for _path, data, kind in items:
        nodes = data["events"] if kind == "events" and isinstance(data, dict) else (
            data if isinstance(data, list) else [data])
        for node in nodes:
            hits = V.scan_node(node, index)
            ex = [r for _p, r in hits if r.kind == "exact"]
            total_exact += len(ex)
            total_near += len([r for _p, r in hits if r.kind == "near"])
            dirty += 1 if ex else 0

    print("checked {} file(s) against {}".format(len(items), Path(a.source).name))
    print("  exact runs (>= {} words): {} in {} node(s)".format(V.BAR, total_exact, dirty))
    print("  near hits (review only):  {}".format(total_near))

    if a.check_only:
        print("\n" + ("BLOCKED" if total_exact else "clear"))
        return 1 if total_exact else 0
    if not total_exact:
        print("\nclear — nothing to rewrite")
        return 0

    # ---- rewrite ---------------------------------------------------------
    pool = None
    if EndpointPool is not None:
        pool = EndpointPool([int(p) for p in a.ports.split(",")], a.model,
                            temperature=0.2, max_tokens=1200)
        try:
            pool.health()
        except Exception as error:
            print("  no endpoint ({}): falling back to elision".format(error))
            pool = None
    else:
        print("  client unavailable: falling back to elision")

    report: List[Dict[str, Any]] = []
    out_root = Path(a.out) if a.out else None
    if out_root and Path(a.nodes).is_dir():
        out_root.mkdir(parents=True, exist_ok=True)

    for path, data, kind in items:
        nodes = data["events"] if kind == "events" and isinstance(data, dict) else (
            data if isinstance(data, list) else [data])
        for node in nodes:
            for entry in process_node(node, index, pool):
                entry["file"] = path.name
                entry["node"] = node.get("scene_id") or node.get("event_id")
                report.append(entry)
                print("  {:<10} {:<28} {}".format(
                    entry["node"] or "-", entry["path"][:28], entry["outcome"]))
        dest = (out_root / path.name) if out_root and path.is_file() and out_root.is_dir() \
            else (Path(a.out) if a.out and not Path(a.nodes).is_dir() else path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n",
                        encoding="utf-8")

    # ---- check again -----------------------------------------------------
    left = 0
    for path, data, kind in items:
        nodes = data["events"] if kind == "events" and isinstance(data, dict) else (
            data if isinstance(data, list) else [data])
        for node in nodes:
            left += len([r for _p, r in V.scan_node(node, index, near=False)])

    kinds: Dict[str, int] = {}
    for entry in report:
        key = entry["outcome"].split(" (")[0].split(":")[0]
        kinds[key] = kinds.get(key, 0) + 1
    print("\n{} field(s) touched: {}".format(len(report), kinds))
    print("runs remaining after the pass: {}".format(left))

    if a.report:
        Path(a.report).write_text(json.dumps(report, indent=1, ensure_ascii=False),
                                  encoding="utf-8")
        print("report -> {}".format(a.report))
    return 1 if left else 0


if __name__ == "__main__":
    raise SystemExit(main())
