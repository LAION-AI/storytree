#!/usr/bin/env python3
"""Where things live, resolved from the environment instead of hardcoded.

Every script in this directory needs three locations, and none of them can
be assumed:

  STORYTREE_TREES   the directory of built story trees, one subdirectory per
                    film (`<slug>/scenes/`, `<slug>/events/`, ...). This is
                    operational output, deliberately not inside this repo.
  SCREENPLAY_KU_SRC the `src/` of the sibling project that provides
                    `EndpointPool` (the LLM client) and `grammar_safe`
                    (JSON-schema sanitising).
  TRACE_OUT         where generated traces and datasets are written.

Set them as environment variables, or pass explicit paths on the command
line. The defaults below are relative guesses that work in a checkout next
to its sibling project; they are guesses, not requirements.
"""
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# The movie pipeline's layer generators (meta_layer, plot_layer, ...). These
# are imported for their prompts and their `build_digest()` helper, so that
# a trace is generated against exactly the text the real generator saw.
DISTILL_DIR = REPO_ROOT / "distill"

TREES = Path(os.environ.get("STORYTREE_TREES", REPO_ROOT.parent / "screenplays" / "trees"))

SCREENPLAY_KU_SRC = Path(os.environ.get(
    "SCREENPLAY_KU_SRC",
    REPO_ROOT.parent / "project-alexandria" / "screenplay" / "src"))

TRACE_OUT = Path(os.environ.get("TRACE_OUT", REPO_ROOT / "runs" / "reasoning_traces"))


def install_paths():
    """Put the two sibling source trees on `sys.path`.

    Called at import time by every script here. Kept as one function so the
    import order is identical everywhere and a missing sibling produces one
    clear error instead of a confusing `ModuleNotFoundError` deep in a call.
    """
    for p in (DISTILL_DIR, SCREENPLAY_KU_SRC):
        sp = str(p)
        if sp not in sys.path:
            sys.path.insert(0, sp)


def require(path: Path, what: str, env_var: str) -> Path:
    """Fail early and legibly when a required location is missing."""
    if not path.exists():
        raise SystemExit(
            f"{what} not found at {path}\n"
            f"Set {env_var} to the right location, e.g.:\n"
            f"    export {env_var}=/path/to/{path.name}")
    return path
