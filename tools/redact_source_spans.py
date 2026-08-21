#!/usr/bin/env python3
"""Elide verbatim runs of source text from anything about to be published.

The project's rule is that no run of eight or more consecutive words from the
screenplay survives into a published artifact. Node contents are derived, not
copied, but a summary that quotes dialogue at length copies anyway -- and the
first version of docs/nodes/ went to GitHub carrying a twenty-four word run
because the existing sweep only looked at one directory.

This does not paraphrase. It replaces the offending run with [...] and leaves
everything else exactly as the pipeline produced it, so an example stays a real
example and the elision is visible rather than silent.

  python3 distill/redact_source_spans.py --source X --check  docs/nodes/*
  python3 distill/redact_source_spans.py --source X --write  docs/nodes/*
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import List, Set, Tuple

N = 8  # the project's threshold: eight consecutive words is a copy

# Keeps apostrophes inside words. An earlier tokenizer split on them, so any
# quoted span read as different tokens than the same span unquoted and the gate
# was blind to exactly the text it existed to catch.
_TOK = re.compile(r"[A-Za-z0-9]+(?:'[A-Za-z0-9]+)*")


def shingles(text: str, n: int = N) -> Set[str]:
    words = [m.group(0).lower() for m in _TOK.finditer(text)]
    return {" ".join(words[i:i + n]) for i in range(len(words) - n + 1)}


def find_runs(text: str, source: Set[str], n: int = N) -> List[Tuple[int, int, int]]:
    """Maximal runs of >= n source words. Returns (char_start, char_end, words)."""
    spans = [(m.start(), m.end(), m.group(0).lower()) for m in _TOK.finditer(text)]
    out, i = [], 0
    while i <= len(spans) - n:
        if " ".join(w for _s, _e, w in spans[i:i + n]) in source:
            j = i + n
            while j < len(spans) and " ".join(
                    w for _s, _e, w in spans[j - n + 1:j + 1]) in source:
                j += 1
            out.append((spans[i][0], spans[j - 1][1], j - i))
            i = j
        else:
            i += 1
    return out


def redact(text: str, source: Set[str], keep: int = 5) -> Tuple[str, int]:
    """Elide each run, keeping its first `keep` words so the sentence still reads."""
    runs = find_runs(text, source)
    if not runs:
        return text, 0
    pieces, last = [], 0
    for start, end, _words in runs:
        pieces.append(text[last:start])
        head = _TOK.finditer(text[start:end])
        cut = start
        for idx, m in enumerate(head):
            if idx == keep:
                break
            cut = start + m.end()
        pieces.append(text[start:cut] + " [...]")
        last = end
    pieces.append(text[last:])
    return "".join(pieces), len(runs)


def redact_json(value, source, keep: int = 5):
    """Redact inside string values only.

    A run of source words is found by tokenizing, which ignores punctuation --
    including the quote-comma-quote between two list entries. Eliding on the raw
    file text would therefore happily delete a run that started in one string and
    ended in the next, taking the JSON structure with it. So the unit of
    redaction is one string value.
    """
    if isinstance(value, str):
        new, n = redact(value, source, keep)
        return new, n
    if isinstance(value, dict):
        total, out = 0, {}
        for k, v in value.items():
            out[k], n = redact_json(v, source, keep)
            total += n
        return out, total
    if isinstance(value, list):
        total, out = 0, []
        for v in value:
            nv, n = redact_json(v, source, keep)
            out.append(nv)
            total += n
        return out, total
    return value, 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True, help="the screenplay text")
    ap.add_argument("--write", action="store_true", help="rewrite in place")
    ap.add_argument("paths", nargs="+")
    a = ap.parse_args()

    src = shingles(Path(a.source).read_text(encoding="utf-8", errors="ignore"))
    total = 0
    for path in a.paths:
        p = Path(path)
        if not p.is_file():
            continue
        text = p.read_text(encoding="utf-8")
        runs = find_runs(text, src)
        if not runs:
            print("  {:<44} clean".format(p.name))
            continue
        total += len(runs)
        worst = max(w for _s, _e, w in runs)
        print("  {:<44} {} run(s), longest {} words".format(p.name, len(runs), worst))
        for start, end, words in runs[:4]:
            print("      {:2d}w  {}".format(words, text[start:end][:110].replace("\n", " ")))
        if a.write:
            if p.suffix == ".json":
                data, n = redact_json(json.loads(text), src)
                p.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n",
                             encoding="utf-8")
            else:
                out, n = redact(text, src)
                p.write_text(out, encoding="utf-8")
            print("      -> elided {} run(s)".format(n))
    if total and not a.write:
        print("\nFAIL: {} verbatim run(s). Re-run with --write to elide.".format(total))
        return 1
    print("\nclear" if not total else "\nrewritten")
    return 0


if __name__ == "__main__":
    sys.exit(main())
