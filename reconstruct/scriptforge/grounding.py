"""Grounding enforcement: make the wrong answer unwriteable, then check the rest.

Why this module exists rather than another prompt clause
--------------------------------------------------------
EXP-001 asked whether the failures a rubric evaluation found in Qwen3.8-27B are
instruction problems or capability limits. It got a split answer, and the split
is what this module is built on.

The **confidence** clause worked: 95 -> 85 and 90 -> 65, same direction on both
items. The **envelope-location** clause did not, and on the one item where
improvement was possible it regressed.

That difference is not noise, it is structural. Confidence is a *local* field:
the model fills it at one point in the generation and an instruction reaches
that point. Staying in the room the slug line names is a *global* consistency
requirement holding across the whole generation — and it was already in the
prompt. Restating it added tokens and moved nothing.

So the rule this repo has now found three times applies again: asking harder
does not fix structural failures, only structure does. Concretely, four moves,
in descending order of how much they can be trusted:

1. **Make it unwriteable.** The location and the cast are facts, not decisions.
   They are bound into the schema as `const` and `enum`, so the grammar refuses
   the wrong answer. A model cannot set a scene in the wrong building if the
   building is not a field it writes.
2. **Condition on it.** The binding block is the *first* thing in the document,
   so by the time the model writes anything else it has already emitted the
   ground truth into its own context. This is the part that reaches free-text
   fields the grammar cannot constrain.
3. **Check mechanically.** The fabricated event that prompted this work
   contradicted three things that were all available as data — the dossier, the
   model's own preceding node, and the state model. Detecting that needs no
   judge, only a comparison.
4. **Separate writing from checking.** Confidence 95 on a forecast wrong in
   location, character and event is a self-assessment failure. A call that only
   verifies has no answer of its own to defend.

Nothing here touches the *depth* of what the model writes. Grounding is about
whether claims are admissible, not whether they are good.
"""

from __future__ import annotations

import copy
import json
import re


def _norm(s: str) -> str:
    return "".join(c for c in (s or "").lower() if c.isalnum())


def allowed_speakers(scene, entities: dict, resolved: list[str] | None = None) -> list[str]:
    """Exactly who speaks in this scene, per the script. Nothing else.

    The first version of this took `characters_in_scene()` — cues *plus event
    participants* — as its base and appended unresolved cues. That was wrong in a
    way worth recording, because it made the constraint actively harmful rather
    than merely loose.

    On a scene whose only script cue is one police officer, it produced an enum
    of three, and `binding.on_screen` carried `minItems = maxItems = 3`. The
    schema therefore *mandated* that two characters who are not in the scene be
    listed as present, and the model dutifully gave them lines. An evaluation
    scored that as the arm's worst failure — and the harness had required it.

    Worse, the error was invisible to the post-check, because the check compared
    the output against the same wrong roster that produced it. "Off-roster
    speakers: 0" meant only that the model complied with a roster the harness had
    invented.

    Ground truth for who speaks is the script's speaker cues and nothing else.
    Event participants describe who a scene is *about*, which is a different and
    larger set. `resolved` is accepted and ignored, kept only so existing callers
    do not break.
    """
    by_key = {}
    for eid, e in entities.items():
        for label in [e.get("canonical_name", "")] + list(e.get("aliases") or []):
            if _norm(label):
                by_key[_norm(label)] = eid

    out: list[str] = []
    for cue in getattr(scene, "speakers", []) or []:
        hit = by_key.get(_norm(cue))
        if hit is None:
            hit = next((eid for k, eid in by_key.items()
                        if k and (k in _norm(cue) or _norm(cue) in k) and len(k) > 3), None)
        # An unresolved cue is kept as its raw name. It marks a hole in the
        # entity layer, and dropping it would leave the model no legal way to
        # write the scene it was handed.
        pick = hit or cue
        if pick not in out:
            out.append(pick)
    return out


def binding_block(scene, speakers: list[str]) -> dict:
    """The facts, as a schema fragment the model must reproduce exactly."""
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["scene_id", "location", "time_of_day", "on_screen"],
        "properties": {
            "scene_id": {"const": scene.scene_id},
            "location": {"const": scene.location},
            "time_of_day": {"const": scene.time_of_day or "UNSPECIFIED"},
            # No minItems/maxItems. A fixed length does not verify presence, it
            # *mandates* it — and when the roster was wrong that is exactly how a
            # constraint manufactured the failure it was meant to prevent. The
            # enum bounds who may appear; how many appear is the model's to get
            # right, and is checked afterwards instead.
            "on_screen": {
                "type": "array", "minItems": 1,
                "items": {"type": "string", "enum": speakers},
            },
        },
    }


def bind_schema(schema: dict, scene, entities: dict, speakers: list[str],
                entity_ids: list[str]) -> dict:
    """Return a copy of `schema` with the facts bound and the free ids enumerated.

    Three edits, each aimed at one measured failure:

      binding            first property, all const  -> location drift
      specimen speaker   free string -> enum        -> roster violation
      state change entity free string -> enum       -> invented entity ids

    `state_changes_implied.variable` is deliberately NOT enumerated. Which
    variables are legal depends on which entity was named, and a JSON-Schema
    grammar cannot express that dependency. Enumerating the union of all
    variables would permit exactly the failure worth catching — a variable
    belonging to a different character — while looking like enforcement. It is
    checked afterwards instead, in `check_grounding`.
    """
    s = copy.deepcopy(schema)
    props = s.setdefault("properties", {})

    # 1. the facts, first in the document so everything later is conditioned on them
    props["binding"] = binding_block(scene, speakers)
    req = s.setdefault("required", [])
    if "binding" not in req:
        req.insert(0, "binding")
    s["properties"] = {"binding": props.pop("binding"), **props}

    # 2 and 3. Constrain the free-string id fields wherever they occur.
    #
    # Walk rather than index. The first version indexed a fixed path
    # (`properties.specimen.properties.lines`) and silently did nothing when the
    # specimen schema was passed on its own, because then `lines` sits at the
    # top level and there is no `specimen` key to descend into. It bound the
    # location correctly and left every speaker unconstrained — a half-applied
    # constraint that reports success. Caught by a dry run before it cost a
    # generation; it would have looked like the enum simply not working.
    _enumerate(s, "speaker", speakers)
    if entity_ids:
        _enumerate(s, "entity", entity_ids)

    return s


def _enumerate(node, field: str, values: list[str]) -> None:
    """Replace every `{field: {type: string}}` leaf in the schema with an enum."""
    if isinstance(node, dict):
        p = node.get("properties")
        if isinstance(p, dict) and isinstance(p.get(field), dict) \
                and p[field].get("type") == "string" and "const" not in p[field]:
            p[field] = {"type": "string", "enum": list(values)}
        for v in node.values():
            _enumerate(v, field, values)
    elif isinstance(node, list):
        for v in node:
            _enumerate(v, field, values)


# --------------------------------------------------------------------------
# Post-checks: the claims a grammar cannot refuse
# --------------------------------------------------------------------------

def _locwords(location: str) -> list[str]:
    stop = {"the", "and", "int", "ext", "city", "of", "a"}
    return [w for w in re.findall(r"[a-z']{4,}", (location or "").lower())
            if w not in stop]


def check_grounding(tr: dict, scene, entities: dict, speakers: list[str],
                    prior: dict | None = None) -> list[str]:
    """Violations of things that were knowable from data. Empty list is a pass.

    Each check corresponds to one observed failure. They are worth stating,
    because the case that motivated this module — a fabricated event asserted at
    95% confidence — contradicted the dossier, the model's own previous node and
    the state model simultaneously. All three were on disk. No judge was needed
    to see it; nobody had looked.
    """
    v: list[str] = []
    dec = tr.get("decision") or {}
    spec = tr.get("specimen") or {}

    # -- the binding, if the grammar was bypassed --
    b = tr.get("binding") or {}
    if b.get("location") and b["location"] != scene.location:
        v.append(f"binding.location is {b['location']!r}, scene is {scene.location!r}")

    # -- location: the free-text decision must be set where the scene is --
    key = _locwords(scene.location)
    body = (json.dumps(dec.get("resolution") or "") + " "
            + json.dumps(tr.get("craft") or {})).lower()
    if key and sum(1 for w in key if w in body) == 0:
        v.append(f"decision never mentions the bound location ({scene.location!r})")

    # -- roster: only people present speak, and people present should speak --
    said = [l.get("speaker") for l in (spec.get("lines") or []) if isinstance(l, dict)]
    for s in sorted(set(said) - set(speakers)):
        v.append(f"specimen gives lines to {s!r}, who is not on screen")
    # Silence is the other half, and it was the half that hid. One arm satisfied
    # the enum by repeating a single speaker six times and dropping the other
    # person in the room entirely — zero off-roster violations, one character
    # deleted. Both directions have to be checked.
    for s in speakers:
        if s not in said:
            v.append(f"specimen gives no lines to {s!r}, who is on screen")

    # -- state changes must name a variable that belongs to the named entity --
    for i, c in enumerate(dec.get("state_changes_implied") or []):
        if not isinstance(c, dict):
            continue
        eid, var = c.get("entity"), c.get("variable")
        if eid and eid not in entities:
            v.append(f"state_changes[{i}] names unknown entity {eid!r}")
            continue
        if eid and var:
            owned = set((entities[eid].get("state_variables") or {})) | \
                    set((entities[eid].get("state") or {}))
            if owned and var not in owned:
                v.append(f"state_changes[{i}]: {var!r} is not a variable of {eid!r}"
                         + (f" (it belongs to {_owner(entities, var)})"
                            if _owner(entities, var) else ""))
        if c.get("from") is not None and c.get("from") == c.get("to"):
            v.append(f"state_changes[{i}] is a no-op ({c.get('from')!r} -> same)")

        # Naming the right variable and moving it to a legal value are separate
        # questions, and only the first was being asked. An evaluation measured
        # 0 of 6 state changes valid in an arm this check scored clean, because
        # one model wraps values in objects while the domain holds bare strings —
        # so every value misses while every name is correct.
        spec_v = ((entities.get(eid) or {}).get("state_variables") or {}).get(var)
        if isinstance(spec_v, dict):
            dom = spec_v.get("domain") or spec_v.get("enum") or spec_v.get("values")
            to = c.get("to")
            if dom:
                val = to.get("value") if isinstance(to, dict) and "value" in to else to
                if val not in dom:
                    v.append(f"state_changes[{i}]: {json.dumps(val)[:40]} is outside the "
                             f"declared domain of {var!r}")

    # -- confidence must be earned --
    conf = dec.get("confidence")
    if isinstance(conf, (int, float)) and conf >= 85 and v:
        v.append(f"confidence {conf} asserted while {len(v)} grounding violation(s) stand")

    return v


def _owner(entities: dict, var: str) -> str | None:
    for eid, e in entities.items():
        if var in (e.get("state_variables") or {}) or var in (e.get("state") or {}):
            return eid
    return None


# --------------------------------------------------------------------------

VERIFY_SYSTEM = """\
You are checking a colleague's work against source records. You did not write it
and you have no stake in it being right.

Your only job is to find claims that CONTRADICT the records you are given. Not
claims you find dull, or would have written differently — contradictions.

For each one: quote the claim, name the record it contradicts, and quote that.
If a claim is merely unsupported rather than contradicted, say so separately;
those are different failures and only the first is disqualifying.

Return JSON conforming to the schema. Say plainly when you find nothing."""


VERIFY_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["contradictions", "unsupported", "verdict"],
    "properties": {
        "contradictions": {
            "type": "array",
            "items": {
                "type": "object", "additionalProperties": False,
                "required": ["claim", "contradicts", "evidence"],
                "properties": {
                    "claim": {"type": "string"},
                    "contradicts": {"type": "string",
                                    "enum": ["dossier", "prior_node", "state_model",
                                             "envelope", "itself"]},
                    "evidence": {"type": "string"},
                },
            },
        },
        "unsupported": {"type": "array", "items": {"type": "string"}},
        "verdict": {"type": "string", "enum": ["clean", "unsupported_only", "contradicted"]},
    },
}


def verify_prompt(node_id: str, tr: dict, scene, entities: dict,
                  prior: dict | None) -> str:
    """A call that only checks. Written separately from the call that produced it.

    The failure this addresses is a model rating its own wrong forecast at 95%.
    Self-assessment is not a capability the evaluation found to be present, and
    asking for it harder is the move already shown not to work. A different call
    with no authorship of the text is the cheap structural alternative.
    """
    involved = {c.get("entity") for c in (tr.get("decision") or {}).get(
        "state_changes_implied") or [] if isinstance(c, dict)}
    involved |= {p.get("entity") for p in (tr.get("psychology") or [])
                 if isinstance(p, dict)}
    dossiers = {eid: entities[eid] for eid in involved if eid in entities}

    return f"""\
VERIFY -> {node_id}

Below is a proposed analysis of a scene, and the records that were available
when it was written. Find claims in the analysis that CONTRADICT the records.

Pay particular attention to:
  - an event asserted about a character that their dossier rules out
  - a state variable moved that belongs to a different entity
  - anything inconsistent with what the previous nodes already established
  - a location or a cast member that is not the one given in the binding

THE BINDING (these are facts, not proposals)
{json.dumps(tr.get('binding') or {}, indent=1, ensure_ascii=False)}

THE ANALYSIS
{json.dumps(tr, indent=1, ensure_ascii=False)[:22000]}

DOSSIERS OF THE ENTITIES IT DISCUSSES
{json.dumps(dossiers, indent=1, ensure_ascii=False)[:14000]}

WHAT EARLIER NODES ESTABLISHED
{json.dumps(prior or {}, indent=1, ensure_ascii=False)[:6000] or '(this is the first)'}

SCHEMA
{json.dumps(VERIFY_SCHEMA, indent=1)}
"""


GROUNDING_CLAUSE = """\
--- THE BINDING IS NOT NEGOTIABLE ---

The `binding` object at the top of your output states the scene id, the location,
the time of day and who is on screen. These are facts you were handed, not
choices you are making. Write them first, exactly as given, and then reason
inside them.

Everything that follows must be consistent with what you just wrote:
  - The scene happens in that location. If your idea needs a different room, the
    idea is wrong, not the room.
  - Only the people in `on_screen` speak. All of them are there for a reason;
    a specimen that gives one of them nothing has misread the scene.
  - A state change names a variable belonging to the entity you named. Moving
    someone else's variable is not a bold choice, it is an error.

Before you assert that something happens to a character, check their dossier for
whether it is possible. Contradicting the record you were given is a harder
failure than being unadventurous."""
