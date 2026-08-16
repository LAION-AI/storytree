"""Prompt assembly: load a prompt file, slice the cheat sheet, inject only the
blocks that node type uses.

The slicing is the point. EXP-001 found that appending 4,561 characters of
failure-derived instruction to a system prompt improved one target metric,
did nothing to a second, and coincided with a regression on the third — the
hypothesis being that instruction attention is a budget and added clauses
displace clauses already present. Until EXP-002 settles that, every call gets
the smallest instruction set its node type allows, and no call gets a block it
does not use.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROMPT_DIR = HERE / "prompts"
SHEET_DIR = HERE / "cheatsheets"

# A cheat-sheet section header looks like:  [ALL][SCENE] TITLE
_TAGGED = re.compile(r"^(\[[A-Z_]+\])+\s")


@dataclass
class Prompt:
    role: str
    node_type: str
    cheatsheet_tags: list[str]
    rubric: str
    inject: list[str]
    schema: str
    system: str
    user: str
    extra: dict = field(default_factory=dict)


def _parse_header(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        raise ValueError("prompt file must start with a --- header")
    _, header, body = text.split("---", 2)
    meta: dict = {}
    for line in header.strip().splitlines():
        if not line.strip() or ":" not in line:
            continue
        key, value = line.split(":", 1)
        meta[key.strip()] = value.strip()
    return meta, body


def _split_sections(body: str) -> tuple[str, str]:
    system, user = "", ""
    current = None
    for line in body.splitlines():
        if line.strip() == "# SYSTEM":
            current = "system"
            continue
        if line.strip() == "# USER":
            current = "user"
            continue
        if current == "system":
            system += line + "\n"
        elif current == "user":
            user += line + "\n"
    if not system or not user:
        raise ValueError("prompt file needs both a # SYSTEM and a # USER section")
    return system.strip(), user.strip()


def _listify(value: str | None) -> list[str]:
    if not value or value.strip() == "-":
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def load_prompt(role: str, node_type: str) -> Prompt:
    path = PROMPT_DIR / f"{role}_{node_type}.md"
    if not path.exists():
        raise FileNotFoundError(f"no prompt file at {path}")
    meta, body = _parse_header(path.read_text())
    system, user = _split_sections(body)
    known = {"role", "node_type", "cheatsheet_tags", "rubric", "inject", "schema"}
    return Prompt(
        role=meta.get("role", role),
        node_type=meta.get("node_type", node_type),
        cheatsheet_tags=_listify(meta.get("cheatsheet_tags")),
        rubric=meta.get("rubric", node_type),
        inject=_listify(meta.get("inject")),
        schema=meta.get("schema", "-"),
        system=system,
        user=user,
        extra={k: v for k, v in meta.items() if k not in known},
    )


def slice_cheatsheet(role: str, tags: list[str]) -> str:
    """Return only the sections of the role's cheat sheet carrying one of `tags`.

    Sections run from a tagged header to the next tagged header. Text before the
    first tagged header is preamble and is never included — it documents the file
    for humans, not for the model.
    """
    path = SHEET_DIR / f"{role}.txt"
    text = path.read_text()
    wanted = {t.upper() for t in tags}
    out: list[str] = []
    keeping = False
    for line in text.splitlines():
        if _TAGGED.match(line):
            section_tags = set(re.findall(r"\[([A-Z_]+)\]", line))
            keeping = bool(section_tags & wanted)
        if keeping:
            out.append(line)
    return "\n".join(out).strip()


# --------------------------------------------------------------------------
# Injected blocks. Imported lazily so `distill` stays importable without the
# whole forward pipeline on the path.
# --------------------------------------------------------------------------

def _block(name: str) -> str:
    if name == "craft_sheet":
        from narrativeforge.craft import sheet
        return sheet()
    if name == "craft_checks":
        from narrativeforge.craft import CRAFT_CHECKS
        return CRAFT_CHECKS
    if name == "plot_embedding":
        from narrativeforge.plotembedding import rubric_text
        return rubric_text()
    if name == "prose":
        return prose_block()
    if name == "model_notes":
        import os
        from narrativeforge.model_notes import addendum_for
        return addendum_for(os.environ.get("MODEL_FAMILY", "qwen"))
    raise KeyError(f"unknown injectable block: {name}")


def prose_block() -> str:
    """The prose constraints from docs/10-prose-system-prompt.md.

    Extracted from the doc rather than duplicated, so the provenance table in
    the doc stays the single source of truth for every clause.
    """
    doc = HERE.parent / "docs" / "10-prose-system-prompt.md"
    text = doc.read_text()
    start = text.find("```", text.find("## The prompt"))
    end = text.find("```", start + 3)
    if start == -1 or end == -1:
        return ""
    return text[start + 3:end].strip()


def injected(names: list[str]) -> dict:
    out = {}
    for name in ("craft_sheet", "craft_checks", "plot_embedding", "prose",
                 "model_notes"):
        out[name] = _block(name) if name in names else ""
    return out


# --------------------------------------------------------------------------

def render(prompt: Prompt, context: dict) -> tuple[str, str]:
    """Fill a prompt's USER body. Missing placeholders render empty, not KeyError:
    a node type that has no `previous_critiques` on round 1 is normal."""
    fields = dict(injected(prompt.inject))
    fields["cheatsheet"] = slice_cheatsheet(prompt.role, prompt.cheatsheet_tags)
    fields.setdefault("revision_block", "")
    fields.setdefault("previous_critiques", "")
    fields.update(context)

    class _Blank(dict):
        def __missing__(self, key):  # noqa: D105
            return ""

    body = prompt.user.format_map(_Blank(fields))
    # Collapse the runs of blank lines left by empty blocks. Prefix caching is a
    # byte-exact prefix match, so the collapse must be deterministic.
    body = re.sub(r"\n{3,}", "\n\n", body).strip()
    return prompt.system, body


def revision_block(critique: dict, round_no: int) -> str:
    """The instruction block appended to an author call from round 2 onward."""
    lines = [
        "REVISION",
        "",
        f"This is round {round_no}. Your previous draft was reviewed. Below are "
        "the scores and the instructions. Address every instruction. Where you "
        "disagree with one, do the thing anyway and say why in one line — the "
        "reviewer keeps its previous notes and will check.",
        "",
        "Do not rewrite what already passed. A revision that regresses a "
        "dimension that was already >= 4 is a failed revision.",
        "",
        json.dumps(critique, indent=1, ensure_ascii=False),
    ]
    return "\n".join(lines)
