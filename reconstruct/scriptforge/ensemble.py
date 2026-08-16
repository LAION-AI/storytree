"""Two models, split by measured strength, with the bookkeeping done in code.

The split is not a guess. Across nine nodes on eighteen rubric dimensions plus
mechanical counters, the two models failed in opposite directions:

    GLM-5.2      depth, theory of mind, genuine self-revision in its analyses
                 -> 0 of 85 state values inside their own declared domain
                 -> objects written where the domain holds bare strings

    Qwen3.8-27B  11 of 13 values in domain, zero no-op changes, 8x faster
                 -> 2 of 3 scenes set in the wrong building
                 -> an event that could not happen to the character it happened to
                 -> one sentence per field where the layer needs a paragraph

Neither is good at both halves, and the halves are separable: one is a writing
problem, the other is data entry. So:

    GLM     writes the semantics — what happens, why, who feels what
    Qwen    converts that prose into state changes against a fixed vocabulary
    code    decides everything decidable, and neither model is asked

The third line matters most. The failures this pipeline has actually suffered
were nearly all decidable from files on disk: whether a speaker is in the scene,
whether a variable belongs to the entity named, whether a value is in the
declared domain, whether a causal reference resolves. A model asked those
questions will sometimes get them wrong; a function will not. Every check that
can be moved into code is one the judge's budget no longer has to cover.

The division of labour therefore has three tiers, not two:

    decidable from data      -> code, never a model
    needs reading            -> the weaker, faster model, tightly constrained
    needs judgement          -> the stronger model, given room
"""

from __future__ import annotations

import json
import re
import time

import requests

from . import grounding


# --------------------------------------------------------------------------
# Endpoints
# --------------------------------------------------------------------------

class Endpoint:
    """One OpenAI-compatible server, with the per-family quirks folded in."""

    def __init__(self, name: str, base: str, model: str, family: str,
                 max_tokens: int = 40000):
        self.name, self.base, self.model = name, base, model
        self.family, self.max_tokens = family, max_tokens
        self.calls: list[dict] = []

    def _thinking_off(self) -> dict:
        # Qwen's template raises on any reasoning_effort outside xhigh|medium|low
        # and the request 400s, so it gets the structural switch only. GLM's
        # template maps everything that is not the literal 'high' to *max*, so
        # only "none" escapes. Both understand chat_template_kwargs.
        body = {"chat_template_kwargs": {"enable_thinking": False}}
        if self.family == "glm":
            body["reasoning_effort"] = "none"
        return body

    def ask(self, system: str, user: str, schema: dict | None, *, tag: str,
            max_tokens: int | None = None, retries: int = 3) -> dict | str:
        body = {"model": self.model,
                "messages": [{"role": "system", "content": system},
                             {"role": "user", "content": user}],
                "max_tokens": max_tokens or self.max_tokens,
                "temperature": 0.7, "cache_prompt": True,
                **self._thinking_off()}
        if schema is not None:
            # vLLM's grammar compiler returns HTTP 500 with an empty body on
            # `propertyNames`; strip what a grammar may not implement. The schema
            # is still validated in full after the call.
            body["response_format"] = {
                "type": "json_schema",
                "json_schema": {"name": "a", "strict": False,
                                "schema": _grammar_safe(schema)}}

        last = ""
        for attempt in range(1, retries + 1):
            t0 = time.time()
            try:
                r = requests.post(f"{self.base}/chat/completions",
                                  headers={"Authorization": "Bearer local"},
                                  json=body, timeout=5400)
            except requests.RequestException as exc:
                last = f"transport: {exc}"
                continue
            dt = time.time() - t0
            if r.status_code != 200:
                last = f"HTTP {r.status_code}: {r.text[:160]}"
                print(f"      {tag}: {last}")
                continue
            d = r.json()
            msg = d["choices"][0]["message"]
            content = msg.get("content") or ""
            u = d.get("usage", {})
            self.calls.append({"tag": tag, "secs": dt, "in": u.get("prompt_tokens", 0),
                               "out": u.get("completion_tokens", 0),
                               "think": len(msg.get("reasoning_content") or "")})
            print(f"      {self.name:<5} {tag:<22} {dt:>6.0f}s  "
                  f"out={u.get('completion_tokens', 0):>6,}  "
                  f"{u.get('completion_tokens', 0) / dt if dt else 0:>5.1f} t/s")
            if not content.strip():
                last = "empty content"
                continue
            if schema is None:
                return content
            try:
                return json.loads(content)
            except json.JSONDecodeError as exc:
                last = f"unparseable: {exc}"
        raise RuntimeError(f"{tag}: {retries} attempts failed — {last}")


GRAMMAR_UNSUPPORTED = ("propertyNames", "dependentRequired", "dependentSchemas",
                       "unevaluatedProperties", "if", "then", "else")


def _grammar_safe(schema):
    if isinstance(schema, dict):
        return {k: _grammar_safe(v) for k, v in schema.items()
                if k not in GRAMMAR_UNSUPPORTED}
    if isinstance(schema, list):
        return [_grammar_safe(v) for v in schema]
    return schema


# --------------------------------------------------------------------------
# Tier 1 — decided in code, no model asked
# --------------------------------------------------------------------------

def vocabulary(entities: dict, focus: list[str] | None = None) -> dict:
    """Every legal (entity, variable, value) triple, extracted from the dossiers.

    This is the whole trick. The bookkeeping model is never asked to *know* which
    variables exist or what values they may take — it is handed the closed list
    and asked only to choose from it. A vocabulary is data; remembering one is a
    capability, and it is the capability both models were measured failing at.
    """
    vocab = {}
    for eid, e in entities.items():
        if focus and eid not in focus:
            continue
        entry = {}
        for var, spec in (e.get("state_variables") or {}).items():
            dom = None
            if isinstance(spec, dict):
                dom = spec.get("domain") or spec.get("enum") or spec.get("values")
            cur = (e.get("state") or {}).get(var)
            if isinstance(cur, dict) and "value" in cur:
                cur = cur["value"]
            entry[var] = {"domain": dom, "current": cur,
                          "kind": spec.get("kind") if isinstance(spec, dict) else None}
        if entry:
            vocab[eid] = entry
    return vocab


def state_change_schema(vocab: dict) -> dict:
    """One schema branch per entity, so the grammar itself enforces ownership.

    `bind_schema` could not do this: it enumerated entity ids and left `variable`
    free, because JSON Schema cannot make one field's legal values depend on
    another's. A `oneOf` over per-entity branches can — each branch pins the
    entity with `const` and enumerates only that entity's variables and only that
    variable's domain.

    It is verbose, and it converts the last remaining ownership failure from
    something checked afterwards into something unwriteable.
    """
    branches = []
    for eid, vars_ in vocab.items():
        per_var = []
        for var, spec in vars_.items():
            val = ({"type": "string", "enum": list(spec["domain"])}
                   if spec.get("domain") else {"type": "string"})
            per_var.append({
                "type": "object", "additionalProperties": False,
                "required": ["entity", "variable", "before", "after", "because"],
                "properties": {
                    "entity": {"const": eid},
                    "variable": {"const": var},
                    "before": val, "after": val,
                    "because": {"type": "string", "minLength": 20},
                    "serves_plot": {"type": "string"},
                },
            })
        branches.extend(per_var)
    if not branches:
        return {"type": "array", "items": {"type": "object"}}
    return {"type": "array", "minItems": 1, "items": {"oneOf": branches}}


def check_changes(changes, vocab: dict) -> list[str]:
    """What the grammar still cannot catch: identity moves and absent causes."""
    out = []
    for i, c in enumerate(changes or []):
        if not isinstance(c, dict):
            out.append(f"change[{i}] is not an object")
            continue
        eid, var = c.get("entity"), c.get("variable")
        if eid not in vocab:
            out.append(f"change[{i}]: {eid!r} has no declared variables")
            continue
        if var not in vocab[eid]:
            out.append(f"change[{i}]: {var!r} is not a variable of {eid!r}")
            continue
        dom = vocab[eid][var].get("domain")
        for side in ("before", "after"):
            v = c.get(side)
            if dom and v not in dom:
                out.append(f"change[{i}].{side}: {json.dumps(v)[:40]} outside domain of {var!r}")
        if c.get("before") == c.get("after"):
            out.append(f"change[{i}]: no-op, {json.dumps(c.get('before'))[:30]} unchanged")
        if len((c.get("because") or "")) < 20:
            out.append(f"change[{i}]: no reason given")
    return out


# --------------------------------------------------------------------------
# Tier 2 — the bookkeeper. Reads prose, emits data. Never invents.
# --------------------------------------------------------------------------

BOOKKEEPER_SYSTEM = """\
You are a records clerk, not a writer. Somebody else has written what happens;
your only job is to record its consequences in a fixed vocabulary.

You will be given a passage of analysis and a closed list of entities, the
variables each one has, and the values each variable may take. You may not use
any entity, variable or value outside that list. If the analysis implies a change
you cannot express in the vocabulary, leave it out and say so — an approximation
recorded as fact is worse than a gap.

Record only changes the analysis actually asserts. Do not infer, do not
embellish, and do not record a change because it would be dramatically
satisfying. If the analysis says a character becomes suspicious, that is a
change; if it merely describes them as suspicious throughout, that is not.

Every change needs its `because` grounded in a specific sentence of the analysis."""


def extract_changes(book: Endpoint, analysis: dict, vocab: dict, *, tag: str) -> dict:
    """Turn one model's prose into another's data, against a closed vocabulary."""
    schema = {"type": "object", "additionalProperties": False,
              "required": ["changes", "not_expressible"],
              "properties": {
                  "changes": state_change_schema(vocab),
                  "not_expressible": {"type": "array", "items": {"type": "string"}},
              }}
    lines = []
    for eid, vars_ in vocab.items():
        for var, spec in vars_.items():
            dom = ", ".join(spec["domain"]) if spec.get("domain") else "(free text)"
            lines.append(f"  {eid}.{var}: currently {spec.get('current')!r}; may be one of [{dom}]")

    user = f"""\
Record the state changes this analysis asserts.

THE VOCABULARY — the complete set of what you may write
{chr(10).join(lines)}

THE ANALYSIS
{json.dumps(analysis, indent=1, ensure_ascii=False)[:24000]}

Return the changes, and list separately anything the analysis asserts that the
vocabulary cannot express.

SCHEMA
{json.dumps(schema, indent=1)[:9000]}
"""
    return book.ask(BOOKKEEPER_SYSTEM, user, schema, tag=tag, max_tokens=12000)


# --------------------------------------------------------------------------
# Tier 3 — the writer. Given room, and relieved of the paperwork.
# --------------------------------------------------------------------------

WRITER_SYSTEM_SUFFIX = """\

--- YOU ARE NOT DOING THE PAPERWORK ---

State changes, variable names and value domains are recorded by someone else
from what you write. Do not produce them and do not try to be schema-correct
about them.

What that buys you is room. Spend it on the part only you can do: what each
person perceives, what they believe the other believes and where that belief is
wrong, how they move through the unit in phases, and what is felt against what is
shown. Write those at full length. Be concrete enough that the clerk can find the
specific sentence that justifies each change they record."""


def split_scene(writer: Endpoint, book: Endpoint, scene, entities: dict,
                blind_ctx: dict, env: dict, prompts, schemas,
                book_focus: list[str] | None = None) -> dict:
    """One scene, semantics from the writer, bookkeeping from the clerk.

    Returns the assembled transition plus a `_ensemble` block recording which
    model produced what and what the code-level checks found — so the split can
    be audited rather than taken on trust.
    """
    speakers = grounding.allowed_speakers(scene, entities)
    roster = "\n".join(f"  {eid:<10} {e.get('type','?'):<9} {e.get('canonical_name','?')}"
                       for eid, e in sorted(entities.items()))

    craft_schema = {"type": "object", "additionalProperties": False,
                    "properties": {k: v for k, v in schemas["transition"]["properties"].items()
                                   if k in ("target", "situation", "craft", "interaction")},
                    "required": ["target", "situation", "craft", "interaction"]}
    craft_schema = grounding.bind_schema(craft_schema, scene, entities,
                                         speakers, sorted(entities))

    craft = writer.ask(prompts["blind_system"] + WRITER_SYSTEM_SUFFIX,
                       prompts["craft"](scene.scene_id, blind_ctx, env, roster),
                       craft_schema, tag="craft")

    # Psychology covers who the scene is ABOUT, not who happens to have lines.
    # Iterating `speakers` looked right and silently produced nothing on a scene
    # whose only cue is unresolved: every id failed the `in entities` test, the
    # loop wrote zero blocks, and the structural scorer still returned `pass`
    # because it sums over an empty list. A hollow node that reports success is
    # the worst failure mode this pipeline has, and this is the second time an
    # id-resolution mismatch has produced one.
    analysed = [e for e in (book_focus or speakers) if e in entities]
    psych = []
    for eid in analysed:
        p = writer.ask(prompts["blind_system"] + WRITER_SYSTEM_SUFFIX,
                       prompts["psych"](scene.scene_id, eid, entities[eid],
                                        blind_ctx, craft, roster),
                       schemas["psych"], tag=f"psych.{eid}")
        p["entity"] = eid
        psych.append(p)

    spec_schema = grounding.bind_schema(schemas["specimen"], scene, entities,
                                        speakers, sorted(entities))
    specimen = writer.ask(prompts["blind_system"] + WRITER_SYSTEM_SUFFIX,
                          prompts["specimen"](scene.scene_id, craft, psych, roster),
                          spec_schema, tag="specimen")

    # --- the clerk, on a closed vocabulary built from the dossiers ---
    # Bookkeeping covers who the scene is *about*; speaking is a narrower set,
    # and on a scene whose only cue is unresolved it would be empty — collapsing
    # the closed vocabulary back to every entity in the work.
    focus = [e for e in (book_focus or speakers) if e in entities]
    vocab = vocabulary(entities, focus=focus or None)
    book_out = extract_changes(book, {"craft": craft, "psychology": psych},
                               vocab, tag="bookkeeping")
    changes = book_out.get("changes") or []
    problems = check_changes(changes, vocab)

    tr = dict(craft)
    tr["psychology"] = psych
    tr["specimen"] = specimen
    tr.setdefault("decision", {})["state_changes_implied"] = changes
    tr["_ensemble"] = {
        "writer": writer.model, "bookkeeper": book.model,
        "vocabulary_size": sum(len(v) for v in vocab.values()),
        "changes_recorded": len(changes),
        "not_expressible": book_out.get("not_expressible") or [],
        "code_problems": problems,
        "grounding": grounding.check_grounding(tr, scene, entities, speakers, None),
    }
    return tr
