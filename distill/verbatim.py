#!/usr/bin/env python3
"""Detect source text that survived into a node.

The rule this enforces: **no run of eight or more consecutive source words in
any published artifact.** Nodes are supposed to record what happened, not the
words it happened in, and a summary that quotes dialogue at length has copied
rather than described.

This module only *finds*. Rewriting lives in paraphrase_pass.py and eliding in
tools/redact_source_spans.py, because a detector that also fixes things is a
detector nobody can test.

Two gates, because one is easy to slip past:

  exact       runs of >= BAR consecutive source tokens
  near        a window of NEAR_WINDOW content words of which at least
              NEAR_HITS also sit inside one window of the source. Ignores
              stopwords, word endings and *order*. Catches the rewrite that
              turns "the cursor continues to throb, relentlessly patient" into
              "the cursor kept throbbing, relentless and patient" -- which
              defeats the exact gate while copying the sentence whole.

              Consecutive-stem matching was tried first and did not work: a
              crude stemmer does not fold relentlessly/relentless or rang/ring,
              and one unfolded word in the middle breaks the run. Order was the
              wrong thing to depend on.

A run is not automatically a copy. A span that is only a name and a number
("HEART O' THE CITY HOTEL, Room 303") matches the source because the facts are
the facts, and the project requires those to stay exact. `Run.novelty` reports
how much of the run is ordinary prose, so a caller can adjudicate instead of
mechanically rewriting a location into something wrong.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

BAR = 8            # exact-token bar: eight consecutive words is a copy
NEAR_WINDOW = 10   # content words examined at a time
NEAR_HITS = 7      # how many must also appear together in the source

# Keeps apostrophes inside words. An earlier tokenizer split on them, so a
# quoted span read as different tokens than the same span unquoted and the gate
# was blind to exactly the text it existed to catch.
TOKEN = re.compile(r"[A-Za-z0-9]+(?:'[A-Za-z0-9]+)*")

STOPWORDS = {
    "a", "an", "and", "as", "at", "be", "been", "but", "by", "for", "from",
    "had", "has", "have", "he", "her", "him", "his", "i", "if", "in", "into",
    "is", "it", "its", "me", "my", "not", "of", "on", "or", "our", "out",
    "she", "so", "than", "that", "the", "their", "them", "then", "there",
    "they", "this", "to", "up", "was", "we", "were", "what", "when", "which",
    "who", "will", "with", "you", "your",
}


def tokens(text: str) -> List[str]:
    return [m.group(0).lower() for m in TOKEN.finditer(text or "")]


def spans(text: str) -> List[Tuple[int, int, str]]:
    return [(m.start(), m.end(), m.group(0).lower()) for m in TOKEN.finditer(text or "")]


def _stem(word: str) -> str:
    """Crude and deliberate. Enough to make tense and number stop mattering."""
    for suffix in ("ing", "ed", "es", "s"):
        if len(word) > len(suffix) + 2 and word.endswith(suffix):
            return word[: -len(suffix)]
    return word


def content_words(text: str) -> List[str]:
    return [_stem(w) for w in tokens(text) if w not in STOPWORDS and not w.isdigit()]


@dataclass
class Run:
    """One stretch of copied text inside a node value."""
    start: int          # char offset into the node value
    end: int
    words: int
    text: str
    kind: str = "exact"          # "exact" | "near"
    novelty: float = 1.0         # share of the run that is not a name or number
    source_char: Optional[int] = None
    role: str = "unknown"        # "dialogue" | "action" | "heading" | "unknown"
    role_confidence: str = "low"

    @property
    def is_probably_facts(self) -> bool:
        """A run made almost entirely of proper nouns and numbers.

        Rewriting one of these makes the node *wrong* -- the project requires
        names, dates and numbers to stay exact. Flag, do not paraphrase.
        """
        return self.novelty < 0.34


class SourceIndex:
    """The screenplay, indexed for both gates and for locating a hit."""

    def __init__(self, text: str) -> None:
        self.text = text
        self._spans = spans(text)
        toks = [w for _s, _e, w in self._spans]
        self.exact: Set[str] = {" ".join(toks[i:i + BAR])
                                for i in range(len(toks) - BAR + 1)}
        self._content_at: Dict[str, List[int]] = {}
        for pos, word in enumerate(content_words(text)):
            self._content_at.setdefault(word, []).append(pos)
        self._lines, self.dialogue_wrap = self._label_lines(text)
        self._exact_lookup: Dict[str, int] = {}
        for i in range(len(toks) - BAR + 1):
            self._exact_lookup.setdefault(" ".join(toks[i:i + BAR]), self._spans[i][0])

    # -- line roles -------------------------------------------------------

    @staticmethod
    def _label_lines(text: str) -> Tuple[List[Tuple[int, int, str]], int]:
        """(start_char, end_char, role) per line, plus the dialogue wrap width.

        Roles are a *hint*, not a claim. This screenplay came out of a PDF with
        most of its indentation destroyed, and indentation is what separates a
        dialogue block from an action paragraph. Two weak signals are combined:
        distance below a character cue, and line width.

        The width is measured from the file rather than fixed. Dialogue is
        wrapped narrower than action in every screenplay, but *how* narrow is a
        property of the document -- here dialogue runs to 33 characters at the
        90th percentile and action to 53. A constant tuned on one film is the
        definition of what does not transfer; the mind-pass gate learned this
        the expensive way.
        """
        try:
            sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "reconstruct"))
            from scriptforge.screenplay import _is_flat_cue, _looks_like_slug  # noqa
        except Exception:                                    # pragma: no cover
            _is_flat_cue = lambda line, nxt: False           # noqa: E731
            _looks_like_slug = lambda line: False            # noqa: E731

        lines = text.split("\n")
        widths = [len(l.strip()) for i, l in enumerate(lines)
                  if l.strip() and i and _is_flat_cue(lines[i - 1], l)]
        widths.sort()
        wrap = widths[int(len(widths) * 0.9)] if widths else 34

        out: List[Tuple[int, int, str]] = []
        pos = 0
        since_cue = 99
        for i, line in enumerate(lines):
            nxt = lines[i + 1] if i + 1 < len(lines) else ""
            start, end = pos, pos + len(line)
            pos = end + 1
            stripped = line.strip()
            if not stripped:
                since_cue = 99
                out.append((start, end, "blank"))
                continue
            if _looks_like_slug(line):
                since_cue = 99
                out.append((start, end, "heading"))
                continue
            if _is_flat_cue(line, nxt):
                since_cue = 0
                out.append((start, end, "cue"))
                continue
            since_cue += 1
            # A dialogue block sits just under its cue and is wrapped narrow.
            # Either signal alone is weak: action lines can be short, and a
            # long speech runs past any line budget.
            dialogue = since_cue <= 4 and len(stripped) <= wrap + 2
            if not dialogue:
                since_cue = 99          # the block has ended; do not resume it
            out.append((start, end, "dialogue" if dialogue else "action"))
        return out, wrap

    def role_at(self, char: int) -> Tuple[str, str]:
        """Where a hit came from, and how much to trust the answer."""
        for start, end, role in self._lines:
            if start <= char <= end:
                if role == "cue":
                    return "dialogue", "high"
                if role == "dialogue":
                    return "dialogue", "medium"
                if role == "heading":
                    return "heading", "high"
                return "action", "medium"
        return "unknown", "low"

    # -- gates ------------------------------------------------------------

    def _novelty(self, run_text: str) -> float:
        """Share of run tokens that are neither capitalised in the run nor digits."""
        raw = TOKEN.findall(run_text)
        if not raw:
            return 1.0
        plain = [w for w in raw if not w[0].isupper() and not w[0].isdigit()]
        return len(plain) / len(raw)

    def exact_runs(self, value: str) -> List[Run]:
        sp = spans(value)
        out: List[Run] = []
        i = 0
        while i <= len(sp) - BAR:
            key = " ".join(w for _s, _e, w in sp[i:i + BAR])
            if key in self.exact:
                j = i + BAR
                while j < len(sp) and " ".join(
                        w for _s, _e, w in sp[j - BAR + 1:j + 1]) in self.exact:
                    j += 1
                text = value[sp[i][0]:sp[j - 1][1]]
                run = Run(sp[i][0], sp[j - 1][1], j - i, text,
                          kind="exact", novelty=self._novelty(text),
                          source_char=self._exact_lookup.get(key))
                if run.source_char is not None:
                    run.role, run.role_confidence = self.role_at(run.source_char)
                out.append(run)
                i = j
            else:
                i += 1
        return out

    def near_runs(self, value: str) -> List[Run]:
        """Content-word overlap the exact gate misses.

        Reported separately and never auto-rewritten: a node that legitimately
        describes the same events will trip this sometimes, which is the price
        of catching the reworded copy. It is a review signal, not a gate.
        """
        keep = [(s, e, _stem(w)) for s, e, w in spans(value)
                if w not in STOPWORDS and not w.isdigit()]
        if len(keep) < NEAR_WINDOW:
            return []
        out: List[Run] = []
        i = 0
        while i <= len(keep) - NEAR_WINDOW:
            window = keep[i:i + NEAR_WINDOW]
            # Count how many distinct window words land in one source block.
            # Blocks are NEAR_WINDOW wide and counted with their right
            # neighbour, so a match straddling a block boundary still lands.
            per_block: Dict[int, Set[str]] = {}
            for _s, _e, stem in window:
                for pos in self._content_at.get(stem, ()):
                    per_block.setdefault(pos // NEAR_WINDOW, set()).add(stem)
            best = 0
            for block, words in per_block.items():
                joined = words | per_block.get(block + 1, set())
                best = max(best, len(joined))
            if best >= NEAR_HITS:
                j = i + NEAR_WINDOW
                out.append(Run(window[0][0], keep[j - 1][1], NEAR_WINDOW,
                               value[window[0][0]:keep[j - 1][1]],
                               kind="near",
                               novelty=self._novelty(value[window[0][0]:keep[j - 1][1]])))
                i = j
            else:
                i += 1
        return out

    def context(self, char: Optional[int], lines: int = 4) -> str:
        """Source lines around a hit, for a rewriter that needs to see the original."""
        if char is None:
            return ""
        idx = next((n for n, (s, e, _r) in enumerate(self._lines) if s <= char <= e), None)
        if idx is None:
            return ""
        lo, hi = max(0, idx - lines), min(len(self._lines), idx + lines + 1)
        return "\n".join(self.text[s:e] for s, e, _r in self._lines[lo:hi])


# ---------------------------------------------------------------------------
# walking a node


TEXT_FIELDS_SKIP = {"scene_id", "event_id", "evidence_scene", "from_scene"}


def walk(node, path: str = "") -> Iterable[Tuple[str, str]]:
    """Yield (json path, string) for every string in a node."""
    if isinstance(node, str):
        yield path, node
    elif isinstance(node, dict):
        for key, value in node.items():
            if key in TEXT_FIELDS_SKIP:
                continue
            yield from walk(value, "{}/{}".format(path, key))
    elif isinstance(node, list):
        for i, value in enumerate(node):
            yield from walk(value, "{}[{}]".format(path, i))


def scan_node(node, index: SourceIndex, *, near: bool = True) -> List[Tuple[str, Run]]:
    """Every offending run in a node, as (field path, run)."""
    found: List[Tuple[str, Run]] = []
    for path, value in walk(node):
        for run in index.exact_runs(value):
            found.append((path, run))
        if near:
            exact_ranges = [(r.start, r.end) for _p, r in found if r.kind == "exact"]
            for run in index.near_runs(value):
                if any(run.start >= s and run.end <= e for s, e in exact_ranges):
                    continue        # already reported by the stricter gate
                found.append((path, run))
    return found


def set_at(node, path: str, new: str) -> bool:
    """Write a value back at a path produced by walk()."""
    parts = [p for p in re.split(r"/", path) if p]
    cur = node
    for i, part in enumerate(parts):
        keys = re.findall(r"^([^\[]*)|\[(\d+)\]", part)
        name = part.split("[")[0]
        idxs = [int(x) for x in re.findall(r"\[(\d+)\]", part)]
        last = i == len(parts) - 1
        if name:
            if last and not idxs:
                if not isinstance(cur, dict):
                    return False
                cur[name] = new
                return True
            cur = cur.get(name) if isinstance(cur, dict) else None
        for k, idx in enumerate(idxs):
            if not isinstance(cur, list) or idx >= len(cur):
                return False
            if last and k == len(idxs) - 1:
                cur[idx] = new
                return True
            cur = cur[idx]
        if cur is None:
            return False
    return False
