#!/usr/bin/env python3
"""Pre-publish leak sweep over everything git tracks.

The rule: no run of eight or more consecutive words from the source screenplay
survives into a published artifact.

This replaces a sweep that walked one directory. That scoping was the defect --
docs/nodes/ was written, checked with the old sweep, reported clean, and pushed
to GitHub carrying a twenty-four word run of dialogue. The sweep had answered
honestly about the folder it was given and said nothing about the folder that
mattered.

So the unit is no longer a folder chosen by hand. It is *what git tracks*, which
is by definition what leaves this machine. Adding a directory can no longer
quietly opt it out.

Allowances are encoded here with their reason. An exception a human has to
remember is an exception that gets forgotten by whoever runs this next.

Usage: python3 tools/check_no_leak.py
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

BAR = 8
ROOT = Path(__file__).resolve().parent.parent
SOURCES = ["reconstruct/runs/matrix/script.normalized.txt",
           "distill/runs/matrix/script.normalized.txt"]

# repo-relative path -> why it may carry source text.
ALLOWED = {
    "docs/cognitino/examples.md":
        "worked examples: 3 scenes of 225 (<2%), quoted for method illustration, disclosed "
        "in the file header and in project-alexandria/screenplay/docs/05-provenance-and-scope.md",
    "docs/cognitino/scene-communities.md":
        "one short dialogue fragment used to explain the two-kinds-of-question problem to a "
        "reader who has not seen the project",
}

TEXTUAL = {".md", ".json", ".txt", ".html", ".py", ".jsonl", ".csv"}
_WORD = re.compile(r"[a-z0-9]+(?:'[a-z0-9]+)*")


def tokens(text: str):
    return _WORD.findall((text or "").lower())


def strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from strings(item)


def longest_run(text: str, index) -> int:
    """Longest verbatim run in words, or 0. One linear pass, extending greedily.

    The first version tried eighteen n-gram sizes per file and took minutes over
    the repository -- the kind of cost that gets a check dropped from the loop.
    """
    toks = tokens(text)
    best, i = 0, 0
    while i <= len(toks) - BAR:
        if " ".join(toks[i:i + BAR]) in index:
            j = i + BAR
            while j < len(toks) and " ".join(toks[j - BAR + 1:j + 1]) in index:
                j += 1
            best = max(best, j - i)
            i = j
        else:
            i += 1
    return best


def tracked_files():
    out = subprocess.run(["git", "-C", str(ROOT), "ls-files"],
                         capture_output=True, text=True, check=True).stdout
    return [line for line in out.splitlines() if line]


def main() -> int:
    source = next((ROOT / s for s in SOURCES if (ROOT / s).exists()), None)
    if source is None:
        # Loud, and non-zero. The old sweep returned 0 here, so a machine without
        # the source would have reported "clear" for a file full of screenplay.
        print("BLOCKED: no source copy present; cannot sweep. Looked in:")
        for s in SOURCES:
            print("  " + s)
        return 1

    words = tokens(source.read_text(encoding="utf-8", errors="ignore"))
    index = {" ".join(words[i:i + BAR]) for i in range(len(words) - BAR + 1)}

    failures, allowed_hits, scanned = [], [], 0
    for rel in tracked_files():
        path = ROOT / rel
        if path.suffix.lower() not in TEXTUAL or not path.exists():
            continue
        if rel.endswith("check_no_leak.py") or rel.endswith("redact_source_spans.py"):
            continue
        scanned += 1
        try:
            if path.suffix == ".json":
                texts = list(strings(json.loads(path.read_text(encoding="utf-8"))))
            else:
                texts = [path.read_text(encoding="utf-8", errors="ignore")]
        except Exception as error:
            print("  {:<52} unreadable: {}".format(rel, error))
            continue

        worst = max((longest_run(text, index) for text in texts), default=0)
        if worst >= BAR:
            (allowed_hits if rel in ALLOWED else failures).append((rel, worst))

    print("swept {} tracked text files against {}".format(scanned, source.relative_to(ROOT)))
    for rel, worst in allowed_hits:
        print("  ALLOWED  {:<48} {:>2} words - {}".format(rel, worst, ALLOWED[rel]))
    for rel, worst in failures:
        print("  LEAK     {:<48} {:>2} words".format(rel, worst))
    for rel in ALLOWED:
        if not (ROOT / rel).exists():
            print("  stale allowance, file gone: {}".format(rel))

    if failures:
        print("\nBLOCKED: {} file(s). Elide with tools/redact_source_spans.py --write"
              .format(len(failures)))
        return 1
    print("\nclear")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
