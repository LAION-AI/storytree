"""RFC 6902 JSON Patch + RFC 6901 JSON Pointer.

Hand-rolled because the target machines have no `jsonpatch` package and the
pipeline must run from a bare Python 3.11+ with nothing but the stdlib.

Only the subset the narrative schema needs is implemented, but that subset is
implemented strictly: `add`, `remove`, `replace`, `move`, `copy`, `test`.

Design note for the narrative use-case
--------------------------------------
Patchable regions of a world state MUST NOT contain arrays. JSON Pointer
addresses array members by index, so inserting one element silently
re-targets every later pointer, and a story is nothing but a long sequence of
insertions. Everywhere the schema wants "a list of things that may later be
patched" it uses an object keyed by a stable id (``b01``, ``ch-04``) instead.
`assert_no_arrays` enforces that at validation time.
"""

from __future__ import annotations

import copy
import json
from typing import Any

__all__ = [
    "JsonPatchError",
    "escape_token",
    "unescape_token",
    "parse_pointer",
    "format_pointer",
    "resolve",
    "exists",
    "apply_patch",
    "apply_best_effort",
    "diff",
    "assert_no_arrays",
]


class JsonPatchError(Exception):
    """Raised when a pointer does not resolve or an op cannot be applied."""


# --------------------------------------------------------------------------
# RFC 6901 — JSON Pointer
# --------------------------------------------------------------------------

def escape_token(token: str) -> str:
    return token.replace("~", "~0").replace("/", "~1")


def unescape_token(token: str) -> str:
    # Order matters: ~01 must decode to ~1, not to /.
    return token.replace("~1", "/").replace("~0", "~")


def parse_pointer(pointer: str) -> list[str]:
    if pointer == "":
        return []
    if not pointer.startswith("/"):
        raise JsonPatchError(f"pointer must be empty or start with '/': {pointer!r}")
    return [unescape_token(t) for t in pointer.split("/")[1:]]


def format_pointer(tokens: list[str]) -> str:
    return "".join("/" + escape_token(str(t)) for t in tokens)


def _descend(doc: Any, token: str, pointer: str) -> Any:
    if isinstance(doc, dict):
        if token not in doc:
            raise JsonPatchError(f"missing key {token!r} while resolving {pointer!r}")
        return doc[token]
    if isinstance(doc, list):
        if token == "-":
            raise JsonPatchError(f"'-' is not resolvable for reads: {pointer!r}")
        try:
            idx = int(token)
        except ValueError:
            raise JsonPatchError(f"array index {token!r} is not an integer in {pointer!r}") from None
        if idx < 0 or idx >= len(doc):
            raise JsonPatchError(f"array index {idx} out of range in {pointer!r}")
        return doc[idx]
    raise JsonPatchError(f"cannot descend into {type(doc).__name__} at {token!r} in {pointer!r}")


def resolve(doc: Any, pointer: str) -> Any:
    """Return the value at `pointer`. Raises JsonPatchError if absent."""
    node = doc
    for token in parse_pointer(pointer):
        node = _descend(node, token, pointer)
    return node


def exists(doc: Any, pointer: str) -> bool:
    try:
        resolve(doc, pointer)
        return True
    except JsonPatchError:
        return False


def _split_parent(doc: Any, pointer: str, *, create_missing: bool = False) -> tuple[Any, str]:
    """Resolve everything but the last token; return (container, last_token).

    `create_missing` enables auto-vivification of intermediate *objects*, which
    is a deliberate extension to RFC 6902 and is off by default.

    The reason it exists: a model asked to add a sentence to a nested backstory
    emits a single op for the full path —

        add /entities/ch-02/profile/backstory/b04a/text

    — where `b04a` does not exist yet. Strict RFC 6902 rejects this, because
    `add` may only write into a container that already exists; creating `b04a`
    would need its own prior op. The model is thinking in paths and the standard
    wants steps. Since our patchable regions are objects all the way down (arrays
    are forbidden there precisely because index shifts break pointers), there is
    no ambiguity about what to create, so filling in the intermediate objects is
    safe and does exactly what the author meant.

    Only dicts are ever created. A missing *array* index is still an error: the
    intent there is genuinely ambiguous.
    """
    tokens = parse_pointer(pointer)
    if not tokens:
        raise JsonPatchError("cannot address the document root with this operation")
    node = doc
    for i, token in enumerate(tokens[:-1]):
        if create_missing and isinstance(node, dict) and token not in node:
            nxt = tokens[i + 1]
            if nxt == "-" or nxt.lstrip("-").isdigit():
                raise JsonPatchError(
                    f"refusing to auto-create a container for array index {nxt!r} "
                    f"in {pointer!r} — say explicitly what it should be"
                )
            node[token] = {}
        node = _descend(node, token, pointer)
    return node, tokens[-1]


# --------------------------------------------------------------------------
# RFC 6902 — JSON Patch
# --------------------------------------------------------------------------

def _op_add(doc: Any, path: str, value: Any, *, lenient: bool = False) -> None:
    parent, token = _split_parent(doc, path, create_missing=lenient)
    if isinstance(parent, dict):
        parent[token] = copy.deepcopy(value)
    elif isinstance(parent, list):
        if token == "-":
            parent.append(copy.deepcopy(value))
        else:
            try:
                idx = int(token)
            except ValueError:
                raise JsonPatchError(f"bad array index {token!r} in add {path!r}") from None
            if idx < 0 or idx > len(parent):
                raise JsonPatchError(f"add index {idx} out of range in {path!r}")
            parent.insert(idx, copy.deepcopy(value))
    else:
        raise JsonPatchError(f"cannot add into {type(parent).__name__} at {path!r}")


def _op_remove(doc: Any, path: str) -> Any:
    parent, token = _split_parent(doc, path)
    if isinstance(parent, dict):
        if token not in parent:
            raise JsonPatchError(f"remove: missing key {token!r} at {path!r}")
        return parent.pop(token)
    if isinstance(parent, list):
        try:
            idx = int(token)
        except ValueError:
            raise JsonPatchError(f"bad array index {token!r} in remove {path!r}") from None
        if idx < 0 or idx >= len(parent):
            raise JsonPatchError(f"remove index {idx} out of range in {path!r}")
        return parent.pop(idx)
    raise JsonPatchError(f"cannot remove from {type(parent).__name__} at {path!r}")


def _op_replace(doc: Any, path: str, value: Any, *, lenient: bool = False) -> None:
    parent, token = _split_parent(doc, path, create_missing=lenient)
    if isinstance(parent, dict):
        if token not in parent and not lenient:
            raise JsonPatchError(
                f"replace: {path!r} does not exist (use 'add' to create it)"
            )
        # Leniently, replace-on-absent means add. Models pick between the two by
        # whether the field *ought* to exist, not by whether it currently does —
        # and for a repair patch the intent is identical either way.
        parent[token] = copy.deepcopy(value)
    elif isinstance(parent, list):
        try:
            idx = int(token)
        except ValueError:
            raise JsonPatchError(f"bad array index {token!r} in replace {path!r}") from None
        if idx < 0 or idx >= len(parent):
            raise JsonPatchError(f"replace index {idx} out of range in {path!r}")
        parent[idx] = copy.deepcopy(value)
    else:
        raise JsonPatchError(f"cannot replace inside {type(parent).__name__} at {path!r}")


def apply_patch(doc: Any, ops: list[dict], *, in_place: bool = False,
                lenient: bool = False) -> Any:
    """Apply an RFC 6902 patch. Returns the patched document.

    Atomic by default: on failure the caller's document is untouched, because
    we work on a deep copy unless `in_place` is set.

    `lenient` enables the two extensions described in `_split_parent` and
    `_op_replace` — auto-vivified intermediate objects, and replace-on-absent
    behaving as add. Use it for model-authored repair patches, not for the
    timeline fold, where strictness is what makes the fold trustworthy.
    """
    target = doc if in_place else copy.deepcopy(doc)
    for i, op in enumerate(ops):
        try:
            _apply_one(target, op, lenient=lenient)
        except JsonPatchError as exc:
            raise JsonPatchError(f"op[{i}] ({op.get('op')} {op.get('path')}): {exc}") from None
    return target


def apply_best_effort(doc: Any, ops: list[dict], *,
                      lenient: bool = True) -> tuple[Any, list[str]]:
    """Apply what applies; report what did not. Never raises on a bad op.

    All-or-nothing is right for the fold, where a half-applied patch would leave
    the world state quietly wrong. It is the wrong policy for a *repair* patch:
    there, one malformed op out of ninety would discard eighty-nine good fixes
    and send the model round again to redo work it already did correctly. That
    turns a small error into a wasted call, and on a slow local model a wasted
    call is minutes.

    So: apply each op independently against the running document, collect the
    failures as strings, and let the caller decide whether what got through was
    enough. The failures are returned rather than logged so they can be fed back
    to the model verbatim on the next attempt.
    """
    target = copy.deepcopy(doc)
    failures: list[str] = []
    for i, op in enumerate(ops):
        try:
            _apply_one(target, op, lenient=lenient)
        except JsonPatchError as exc:
            failures.append(f"op[{i}] ({op.get('op')} {op.get('path')}): {exc}")
    return target, failures


def _apply_one(target: Any, op: dict, *, lenient: bool = False) -> None:
    kind = op.get("op")
    path = op.get("path")
    if kind is None or path is None:
        raise JsonPatchError("op requires 'op' and 'path'")

    if kind == "add":
        if "value" not in op:
            raise JsonPatchError("'add' requires 'value'")
        _op_add(target, path, op["value"], lenient=lenient)
    elif kind == "remove":
        _op_remove(target, path)
    elif kind == "replace":
        if "value" not in op:
            raise JsonPatchError("'replace' requires 'value'")
        _op_replace(target, path, op["value"], lenient=lenient)
    elif kind == "move":
        frm = op.get("from")
        if frm is None:
            raise JsonPatchError("'move' requires 'from'")
        if path == frm:
            return
        if path.startswith(frm.rstrip("/") + "/"):
            raise JsonPatchError("'move' cannot relocate a node into its own subtree")
        value = _op_remove(target, frm)
        _op_add(target, path, value, lenient=lenient)
    elif kind == "copy":
        frm = op.get("from")
        if frm is None:
            raise JsonPatchError("'copy' requires 'from'")
        _op_add(target, path, copy.deepcopy(resolve(target, frm)), lenient=lenient)
    elif kind == "test":
        if "value" not in op:
            raise JsonPatchError("'test' requires 'value'")
        actual = resolve(target, path)
        if actual != op["value"]:
            raise JsonPatchError(
                f"test failed: expected {json.dumps(op['value'])}, found {json.dumps(actual)}"
            )
    else:
        raise JsonPatchError(f"unknown op {kind!r}")


# --------------------------------------------------------------------------
# Diff — used to verify that declared exit states match the folded state
# --------------------------------------------------------------------------

def diff(a: Any, b: Any, path: str = "") -> list[dict]:
    """Minimal RFC 6902 patch turning `a` into `b`.

    Objects are diffed recursively. Arrays are replaced wholesale — index
    churn makes fine-grained array diffs unstable, and the narrative schema
    keeps arrays out of patchable regions for exactly that reason.
    """
    ops: list[dict] = []
    if isinstance(a, dict) and isinstance(b, dict):
        for key in a:
            child = f"{path}/{escape_token(key)}"
            if key not in b:
                ops.append({"op": "remove", "path": child})
            else:
                ops.extend(diff(a[key], b[key], child))
        for key in b:
            if key not in a:
                ops.append({"op": "add", "path": f"{path}/{escape_token(key)}", "value": b[key]})
        return ops
    if a != b:
        ops.append({"op": "replace", "path": path or "", "value": b})
    return ops


# --------------------------------------------------------------------------
# Schema hygiene for patchable regions
# --------------------------------------------------------------------------

# Arrays are tolerated at these pointers because they are declarative and are
# never the target of a patch (they describe the entity, they do not track it).
ARRAY_ALLOWLIST_SUFFIXES = ("/aliases", "/tags", "/domain", "/range", "/members_order")


def assert_no_arrays(doc: Any, path: str = "", *, allow: tuple[str, ...] = ARRAY_ALLOWLIST_SUFFIXES) -> list[str]:
    """Return pointers of every array found in a patchable region."""
    found: list[str] = []
    if isinstance(doc, list):
        if not path.endswith(allow):
            found.append(path or "/")
        return found
    if isinstance(doc, dict):
        for key, value in doc.items():
            found.extend(assert_no_arrays(value, f"{path}/{escape_token(key)}", allow=allow))
    return found
