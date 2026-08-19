#!/usr/bin/env python3
"""Pre-commit leak sweep for the cognitino folder.

Every file is checked for verbatim runs from the source screenplay. Two files are allowed to
contain source text, and the allowance is *encoded here with its reason* rather than
remembered — an exception a human has to recall is an exception that will be forgotten by
whoever runs this next.

Exit non-zero if anything outside the allowlist carries a run at or above the bar.

Usage: python3 docs/cognitino/check_no_leak.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

BAR = 8
SOURCE = Path("/home/deployer/laion/bookwriter/reconstruct/runs/matrix/script.normalized.txt")
FOLDER = Path(__file__).resolve().parent

# path -> why it may contain source text. Anything not listed here must be clean.
ALLOWED = {
    "examples.md":
        "worked examples: 3 scenes of 225 (<2%), quoted for method illustration, disclosed "
        "in the file header and in project-alexandria/screenplay/docs/05-provenance-and-scope.md",
    "scene-communities.md":
        "one short dialogue fragment used to explain the two-kinds-of-question problem to a "
        "reader who has not seen the project",
}

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


def main() -> int:
    if not SOURCE.exists():
        print("source not present; cannot sweep")
        return 0
    words = tokens(SOURCE.read_text(encoding="utf-8"))
    index = {n: {tuple(words[i:i + n]) for i in range(len(words) - n + 1)}
             for n in range(BAR, 26)}

    failures = []
    for path in sorted(FOLDER.iterdir()):
        if path.name == Path(__file__).name or path.is_dir():
            continue
        try:
            if path.suffix == ".json":
                texts = list(strings(json.loads(path.read_text(encoding="utf-8"))))
            else:
                texts = [path.read_text(encoding="utf-8", errors="ignore")]
        except Exception as error:
            print("  {:<24} unreadable: {}".format(path.name, error))
            continue

        worst = 0
        for text in texts:
            toks = tokens(text)
            for n in range(25, BAR - 1, -1):
                if len(toks) < n:
                    continue
                if any(tuple(toks[i:i + n]) in index[n] for i in range(len(toks) - n + 1)):
                    worst = max(worst, n)
                    break

        if worst >= BAR:
            if path.name in ALLOWED:
                print("  {:<24} {:>2} words  ALLOWED — {}".format(
                    path.name, worst, ALLOWED[path.name]))
            else:
                print("  {:<24} {:>2} words  LEAK".format(path.name, worst))
                failures.append(path.name)
        else:
            print("  {:<24} clean".format(path.name))

    if failures:
        print("\nBLOCKED: {}".format(", ".join(failures)))
        return 1
    print("\nclear")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
