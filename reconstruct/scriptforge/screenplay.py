"""Parsing a finished screenplay into anchored scenes.

This is stage zero of the reconstruction pipeline and the only deterministic
one. Everything downstream — story root, exposé, plots, dossiers, events, scene
definitions — is inferred by a model, but the mapping from scene node to page
must not be. If the model were asked to quote scene boundaries back, it would
paraphrase, and paraphrase cannot be re-found in the source.

So the split happens here, in code, and the model is handed the result.

What comes out is an *anchor table*: for every scene, its slug line, its
character span, and a short verbatim head and tail quote that is guaranteed
unique in the document. Given the anchor table and the original file, anyone can
recover the exact text of any scene with a regex and no further intelligence —
which is the property the whole reconstruction depends on, because it is what
lets a scene node own exactly one passage of the real script.

Design notes
------------
* Offsets are computed against a *normalized* copy, and the normalization recipe
  is stored beside them, so the numbers stay meaningful when the file is
  reprocessed. This mirrors the whitepaper's treatment of source alignment.
* Anchors are grown until unique. A four-word head quote that appears twice in
  the script is not an anchor, it is a trap.
* Nothing here reproduces the script into the artifacts. The anchor table holds
  spans and short quotes; the text stays in the user's own file and is loaded on
  demand. That keeps the derived corpus a description rather than a copy.
"""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field, asdict

# --------------------------------------------------------------------------
# Normalization — deterministic, recorded, reversible enough to re-align
# --------------------------------------------------------------------------

NORMALIZATION_RECIPE = {
    "version": 1,
    "steps": [
        "unicode NFC",
        "CRLF and CR -> LF",
        "tabs -> 4 spaces",
        "strip trailing whitespace per line",
        "collapse runs of 3+ blank lines to 2",
        "strip a UTF-8 BOM",
        "ensure the text ends with exactly one newline",
    ],
}


def normalize(text: str) -> str:
    text = text.lstrip("﻿")
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\t", "    ")
    text = "\n".join(line.rstrip() for line in text.split("\n"))
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.rstrip("\n") + "\n"


# --------------------------------------------------------------------------
# Slug lines
# --------------------------------------------------------------------------

# INT. / EXT. / INT./EXT. / I/E, optionally preceded by a scene number, and the
# forms that turn up in real scripts once the formatting has been through a PDF.
SLUG_RE = re.compile(
    r"""^[ \t]*
        (?:(?P<number>[A-Z]{0,2}[0-9]{1,4}[A-Z]?)[ \t.)]*)?   # optional leading scene number
        (?P<kind>INT\.?/EXT\.?|EXT\.?/INT\.?|I/E\.?|INT\.?|EXT\.?)
        (?=[ \t]|$)
        (?P<rest>.*)$
    """,
    re.VERBOSE,
)

# Lines that terminate a scene without opening one.
TRANSITION_RE = re.compile(
    r"^[ \t]*(?:CUT TO|SMASH CUT TO|MATCH CUT TO|DISSOLVE TO|FADE (?:OUT|TO BLACK)"
    r"|FADE IN|WIPE TO|END OF (?:ACT|EPISODE)|THE END)[ \t]*[:.]?[ \t]*$",
    re.IGNORECASE,
)

TIME_OF_DAY = re.compile(
    r"\b(DAY|NIGHT|DAWN|DUSK|MORNING|AFTERNOON|EVENING|LATER|CONTINUOUS|"
    r"MOMENTS LATER|SAME|MAGIC HOUR|PRE-?DAWN|SUNSET|SUNRISE)\b", re.IGNORECASE)


def _looks_like_slug(line: str) -> bool:
    """A slug is a short line that starts with INT/EXT and reads as a heading."""
    m = SLUG_RE.match(line)
    if not m:
        return False
    rest = m.group("rest").strip()
    if not rest:
        return False
    if len(line.strip()) > 120:
        return False
    # A heading is overwhelmingly upper case. Sentence-case text beginning with
    # "Interior" style prose is not a heading.
    letters = [c for c in rest if c.isalpha()]
    if letters and sum(c.isupper() for c in letters) / len(letters) < 0.6:
        return False
    return True


def _parse_slug(line: str) -> dict:
    m = SLUG_RE.match(line)
    rest = (m.group("rest") or "").strip(" .-–—")
    tod = None
    parts = re.split(r"\s+[-–—]+\s+", rest)
    if len(parts) > 1 and TIME_OF_DAY.search(parts[-1]):
        tod = parts[-1].strip()
        location = " - ".join(p.strip() for p in parts[:-1])
    else:
        location = rest
    return {
        "number": m.group("number"),
        "kind": m.group("kind").rstrip(".").upper().replace("/", "/"),
        "location": location.strip(),
        "time_of_day": tod,
        "heading": line.strip(),
    }


# --------------------------------------------------------------------------
# Anchors
# --------------------------------------------------------------------------

def _words(body: str, count: int, from_end: bool = False) -> str:
    """The first or last `count` words, sliced from the body VERBATIM.

    Rejoining split tokens with single spaces would produce a string that does
    not occur in the source the moment an anchor crosses a line break — and an
    anchor you cannot find is not an anchor. So we locate the words and slice
    between them, keeping the original whitespace intact.
    """
    spans = [m.span() for m in re.finditer(r"\S+", body)]
    if not spans:
        return ""
    if from_end:
        picked = spans[-count:]
        return body[picked[0][0]:picked[-1][1]]
    picked = spans[:count]
    return body[picked[0][0]:picked[-1][1]]


def anchor_pattern(quote: str) -> re.Pattern:
    """Match a quote tolerantly: any run of whitespace matches any other.

    This is what lets an anchor taken from one copy of a script still locate the
    same passage in a copy that has been re-wrapped, re-indented, or round
    tripped through a PDF.
    """
    parts = [re.escape(tok) for tok in quote.split()]
    return re.compile(r"\s+".join(parts))


def _count_matches(text: str, quote: str) -> int:
    if not quote:
        return 0
    return len(anchor_pattern(quote).findall(text))


# Anchors are stored in artifacts that get published, so they are bound by the
# same rule as everything else: fewer than eight consecutive source words. Three
# of 224 scenes needed eight or nine words to become unique and therefore shipped
# over the bar. The limit is now the bar, and a scene that cannot be uniquely
# anchored inside it is reported non-unique so the caller falls back to the
# character span -- which is exact anyway, and quotes nothing.
ANCHOR_TOKEN_BAR = 8

_ANCHOR_TOKEN = re.compile(r"[A-Za-z0-9]+(?:'[A-Za-z0-9]+)*")


def _anchor_token_count(quote: str) -> int:
    """Count the way the leak sweep counts.

    Whitespace words are not the unit: "9:15 A.M." is two whitespace words and
    four tokens. A limit expressed in whitespace words therefore let a nine-token
    anchor through while looking like a five-word one.
    """
    return len(_ANCHOR_TOKEN.findall(quote))


def _unique_anchor(text: str, body: str, *, from_end: bool, start_at: int = 5,
                   limit: int = 24) -> tuple[str, bool]:
    """Grow a quote until it matches exactly once in `text`.

    Returns (quote, is_unique). A non-unique anchor at the limit is reported
    rather than silently accepted — the caller decides whether to fall back to
    the character span.
    """
    last = ""
    for n in range(start_at, limit + 1):
        quote = _words(body, n, from_end=from_end)
        if not quote or quote == last:
            break
        if _anchor_token_count(quote) >= ANCHOR_TOKEN_BAR:
            # Growing further would publish a copyable run. Stop at the last
            # legal length and report non-unique; the caller falls back to the
            # character span, which is exact and quotes nothing.
            break
        last = quote
        if _count_matches(text, quote) == 1:
            return quote, True
    return last, False




# --------------------------------------------------------------------------
# PDF rescue
# --------------------------------------------------------------------------

# Real scripts arrive as PDFs, and PDF text extraction reliably destroys three
# things a naive parser depends on: it strips leading indentation, it glues
# margin scene numbers onto the slug line ("2INT. HOTEL - NIGHT 2"), and it
# leaves page furniture inline. None of that is exotic — it is what almost every
# extractor produces — so handling it is part of the job, not a special case.

PAGE_FURNITURE = [
    re.compile(r"^\s*\(?\s*CONTINUED\s*\)?\s*[:.]?\s*$", re.I),
    re.compile(r"^\s*\d*\s*CONTINUED\s*:?\s*(\(\d+\))?\s*\d*\s*$", re.I),
    re.compile(r"^\s*\(\s*MORE\s*\)\s*$", re.I),
    re.compile(r"^\s*\d{1,4}\s*[.)]?\s*$"),                       # a bare page number
    re.compile(r"^\s*(?:Rev\.|Revised|Draft)\b.*$", re.I),
    re.compile(r"^\s*.{0,60}?-\s*Rev\.\s*[\d/]+\s*\d{0,4}\.?\s*$", re.I),
    re.compile(r"^\s*Page\s+\d+\s*$", re.I),
]

# "2INT. HOTEL - NIGHT 2"  ->  "INT. HOTEL - NIGHT"
GLUED_SLUG = re.compile(
    r"^\s*(?P<num>[A-Z]{0,2}\d{1,4}[A-Z]?)?\s*"
    r"(?P<kind>INT\.?/EXT\.?|EXT\.?/INT\.?|I/E\.?|INT\.?|EXT\.?)"
    r"(?P<rest>[ \t].*?)"
    r"(?:\s+(?P=num))?\s*$"
)


def looks_like_pdf_extraction(text: str) -> bool:
    """True when indentation is gone — the signal that structure must be
    recovered from shape rather than from margins."""
    lines = [l for l in text.split("\n") if l.strip()]
    if not lines:
        return False
    indented = sum(1 for l in lines if len(l) - len(l.lstrip()) >= 6)
    return indented / len(lines) < 0.08


def preclean(text: str) -> tuple[str, dict]:
    """Strip page furniture and un-glue margin scene numbers.

    Returns the cleaned text and a report of what was removed, so the damage is
    visible rather than silent.
    """
    removed = {"furniture": 0, "slug_numbers": 0}
    out = []
    for raw in text.split("\n"):
        line = raw.replace("\x0c", "")
        if any(rx.match(line) for rx in PAGE_FURNITURE):
            removed["furniture"] += 1
            continue
        m = GLUED_SLUG.match(line)
        if m and m.group("kind") and m.group("rest") and m.group("rest").strip():
            if m.group("num"):
                removed["slug_numbers"] += 1
            line = f"{m.group('kind')}{m.group('rest').rstrip()}"
            # a trailing duplicate of the scene number, if it survived
            line = re.sub(r"\s+[A-Z]{0,2}\d{1,4}[A-Z]?$", "", line)
        out.append(line)
    return "\n".join(out), removed


# A cue when indentation is unavailable: a short all-caps line, followed by
# something, that is not a heading or a transition.
FLAT_CUE_RE = re.compile(r"^([A-Z][A-Z0-9 .'’#\-]{1,34})(\s*\([^)]*\))?\s*$")


def _is_flat_cue(line: str, nxt: str) -> bool:
    if not FLAT_CUE_RE.match(line):
        return False
    t = line.strip()
    if _looks_like_slug(line) or TRANSITION_RE.match(line):
        return False
    if t.rstrip(":") in ("CONTINUED", "MORE", "THE END", "FADE IN", "FADE OUT"):
        return False
    letters = [c for c in t if c.isalpha()]
    if len(letters) < 2:
        return False
    return bool(nxt.strip())


# --------------------------------------------------------------------------

@dataclass
class Scene:
    index: int
    scene_id: str
    heading: str
    kind: str
    location: str
    time_of_day: str | None
    number: str | None
    start_char: int
    end_char: int
    start_quote: str
    end_quote: str
    start_quote_unique: bool
    end_quote_unique: bool
    word_count: int
    line_count: int
    speakers: list[str] = field(default_factory=list)
    dialogue_ratio: float = 0.0

    def text(self, source: str) -> str:
        return source[self.start_char:self.end_char]


CUE_RE = re.compile(r"^[ \t]{6,}([A-Z][A-Z0-9 .'’\-]{1,38})(\s*\(.*\))?[ \t]*$")


def _speakers_and_ratio(body: str, flat: bool = False) -> tuple[list[str], float]:
    speakers: list[str] = []
    dialogue_lines = 0
    total = 0
    lines = body.split("\n")
    for i, raw in enumerate(lines):
        if not raw.strip():
            continue
        total += 1
        if flat:
            nxt = lines[i + 1] if i + 1 < len(lines) else ""
            if _is_flat_cue(raw, nxt):
                name = FLAT_CUE_RE.match(raw.strip()).group(1).strip()
                if name not in speakers:
                    speakers.append(name)
                dialogue_lines += 2      # the cue and the line it introduces
            continue
        m = CUE_RE.match(raw)
        if m:
            name = m.group(1).strip()
            if name not in ("CONT'D", "MORE") and not TRANSITION_RE.match(raw):
                if name not in speakers:
                    speakers.append(name)
                dialogue_lines += 1
                continue
        indent = len(raw) - len(raw.lstrip())
        if indent >= 6:
            dialogue_lines += 1
    return speakers, (dialogue_lines / total if total else 0.0)


def parse(raw_text: str, *, id_prefix: str = "sc", clean: bool = True
          ) -> tuple[str, list[Scene]]:
    """Split a screenplay into scenes. Returns (normalized_text, scenes)."""
    if clean:
        raw_text, _ = preclean(raw_text)
    text = normalize(raw_text)
    flat = looks_like_pdf_extraction(text)
    lines = text.split("\n")

    # character offset of the start of each line
    offsets: list[int] = []
    pos = 0
    for line in lines:
        offsets.append(pos)
        pos += len(line) + 1

    starts = [i for i, line in enumerate(lines) if _looks_like_slug(line)]
    if not starts:
        return text, []

    scenes: list[Scene] = []
    for n, li in enumerate(starts):
        start = offsets[li]
        # the scene runs to the next slug, minus any trailing transition line
        if n + 1 < len(starts):
            end_line = starts[n + 1]
            while end_line - 1 > li and (
                not lines[end_line - 1].strip() or TRANSITION_RE.match(lines[end_line - 1])
            ):
                end_line -= 1
            end = offsets[end_line]
        else:
            end = len(text)
        body = text[start:end]
        meta = _parse_slug(lines[li])
        # anchors are taken from the body *after* the heading for the tail, and
        # from the heading forward for the head, so the head always includes the
        # slug and is therefore almost always unique on its own.
        head_q, head_u = _unique_anchor(text, body, from_end=False)
        tail_q, tail_u = _unique_anchor(text, body.rstrip(), from_end=True)
        speakers, ratio = _speakers_and_ratio(body, flat=flat)
        scenes.append(Scene(
            index=n + 1,
            scene_id=f"{id_prefix}-{n + 1:03d}",
            heading=meta["heading"],
            kind=meta["kind"],
            location=meta["location"],
            time_of_day=meta["time_of_day"],
            number=meta["number"],
            start_char=start,
            end_char=end,
            start_quote=head_q,
            end_quote=tail_q,
            start_quote_unique=head_u,
            end_quote_unique=tail_u,
            word_count=len(body.split()),
            line_count=len([x for x in body.split("\n") if x.strip()]),
            speakers=speakers,
            dialogue_ratio=round(ratio, 3),
        ))
    return text, scenes


# --------------------------------------------------------------------------
# The anchor table — the artifact everything downstream binds to
# --------------------------------------------------------------------------

def anchor_table(text: str, scenes: list[Scene]) -> dict:
    """The structured dictionary a later process can re-split the script with."""
    return {
        "normalization": NORMALIZATION_RECIPE,
        "source_chars": len(text),
        "scene_count": len(scenes),
        "coverage": round(sum(s.end_char - s.start_char for s in scenes) / max(len(text), 1), 4),
        "scenes": {
            s.scene_id: {
                "index": s.index,
                "heading": s.heading,
                "kind": s.kind,
                "location": s.location,
                "time_of_day": s.time_of_day,
                "start_char": s.start_char,
                "end_char": s.end_char,
                "start_quote": s.start_quote,
                "end_quote": s.end_quote,
                "anchors_unique": s.start_quote_unique and s.end_quote_unique,
                "word_count": s.word_count,
                "line_count": s.line_count,
                "speakers": s.speakers,
                "dialogue_ratio": s.dialogue_ratio,
            }
            for s in scenes
        },
    }


def split_by_anchors(text: str, table: dict) -> dict[str, str]:
    """Recover each scene's text from the anchor table alone.

    Uses the quotes, not the offsets, so it still works if the file was
    re-normalized or lightly edited. Falls back to the recorded span when an
    anchor cannot be located.
    """
    out: dict[str, str] = {}
    cursor = 0
    for scene_id, meta in sorted(table["scenes"].items(), key=lambda kv: kv[1]["index"]):
        start = -1
        if meta.get("start_quote"):
            m = anchor_pattern(meta["start_quote"]).search(text, cursor)
            start = m.start() if m else -1
        if start < 0:
            start = meta["start_char"]

        end = -1
        if meta.get("end_quote"):
            m = anchor_pattern(meta["end_quote"]).search(text, start)
            end = m.end() if m else -1
        if end < 0:
            end = meta["end_char"]

        out[scene_id] = text[start:end]
        cursor = max(cursor, end)
    return out


def verify(text: str, scenes: list[Scene], table: dict) -> list[str]:
    """Checks that must pass before any model is asked to reason about this."""
    problems: list[str] = []
    if not scenes:
        problems.append("no scenes found — is this a screenplay with INT./EXT. slug lines?")
        return problems

    for s in scenes:
        if not s.start_quote_unique:
            problems.append(f"{s.scene_id}: head anchor is not unique in the document")
        if not s.end_quote_unique:
            problems.append(f"{s.scene_id}: tail anchor is not unique in the document")
        if s.word_count < 8:
            problems.append(f"{s.scene_id}: only {s.word_count} words — probably a stray heading")

    # spans must be ordered and non-overlapping
    for a, b in zip(scenes, scenes[1:]):
        if b.start_char < a.end_char:
            problems.append(f"{a.scene_id}/{b.scene_id}: spans overlap")

    if table["coverage"] < 0.90:
        problems.append(f"scenes cover only {table['coverage']:.0%} of the file; "
                        f"material before the first slug line is normal, but 10%+ is not")

    # the round trip is the real test
    recovered = split_by_anchors(text, table)
    for s in scenes:
        got = recovered.get(s.scene_id, "")
        want = s.text(text)
        if got.strip() != want.strip():
            problems.append(f"{s.scene_id}: anchor round-trip does not reproduce the span "
                            f"({len(got)} chars recovered vs {len(want)})")
    return problems


def summarize(scenes: list[Scene]) -> dict:
    total_w = sum(s.word_count for s in scenes)
    total_l = sum(s.line_count for s in scenes)
    return {
        "scenes": len(scenes),
        "words": total_w,
        "lines": total_l,
        "estimated_pages_a4": round(total_l / 58, 1),
        "estimated_runtime_min": round(total_l / 58),
        "mean_scene_words": round(total_w / max(len(scenes), 1)),
        "mean_dialogue_ratio": round(sum(s.dialogue_ratio for s in scenes) / max(len(scenes), 1), 3),
        "distinct_speakers": sorted({sp for s in scenes for sp in s.speakers}),
        "locations": sorted({s.location for s in scenes if s.location}),
    }


def scene_digest(scenes: list[Scene], limit: int | None = None) -> list[dict]:
    """A compact index handed to the model, without the script text itself."""
    rows = []
    for s in scenes[:limit] if limit else scenes:
        rows.append({
            "scene_id": s.scene_id, "index": s.index, "heading": s.heading,
            "words": s.word_count, "speakers": s.speakers,
            "dialogue_ratio": s.dialogue_ratio,
        })
    return rows


__all__ = ["Scene", "normalize", "parse", "anchor_table", "split_by_anchors",
           "verify", "summarize", "scene_digest", "anchor_pattern", "preclean",
           "looks_like_pdf_extraction", "NORMALIZATION_RECIPE"]
