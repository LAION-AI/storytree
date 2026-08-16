"""Build the single-file explorer from a project's artifacts.

The template carries the whole application; this only injects the data bundle,
so the page is self-contained and has no network dependency of any kind.
"""

from __future__ import annotations

import json
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parent.parent / "webapp" / "template.html"
PLACEHOLDER = "/*__DATA__*/{}"


def load_transitions(project) -> dict:
    """Reasoning transitions, keyed by the node id they produce."""
    tdir = project.root / "transitions"
    if not tdir.exists():
        return {}
    out = {}
    for path in sorted(tdir.glob("*.json")):
        # <node>.json, or <node>.pN.json for multi-pass entity dossiers
        node_id = path.stem.split(".p")[0]
        try:
            doc = json.loads(path.read_text())
        except json.JSONDecodeError:
            continue
        if ".p" in path.stem:
            out.setdefault(node_id, {}).setdefault("passes", []).append(doc)
        else:
            out[node_id] = doc
    return out


def bundle(project, *, include_prose: bool = True) -> dict:
    docs = project.load_all()
    return {
        "story_root": docs.get("story_root") or {},
        "expose": docs.get("expose") or {},
        "plots": docs.get("plots") or {"plots": []},
        "entities": docs.get("entities") or {"entities": {}},
        "events": docs.get("events") or {"events": {}},
        "scenes": docs.get("scenes") or {"scenes": {}},
        # A reconstruction describes a document it did not write. The structure
        # travels; the document does not.
        "prose": project.load_prose() if include_prose else {},
        "transitions": load_transitions(project),
    }


def build(project, out_path: Path | None = None, template: Path | None = None,
          *, include_prose: bool = True) -> Path:
    html = (template or TEMPLATE).read_text()
    if PLACEHOLDER not in html:
        raise RuntimeError(f"template has no {PLACEHOLDER} placeholder")

    data = bundle(project, include_prose=include_prose)
    # </script> inside string data would close the tag early; nothing else can escape.
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    html = html.replace(PLACEHOLDER, payload)

    out = Path(out_path) if out_path else project.root / "site" / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html)
    return out
