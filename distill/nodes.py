"""Node-type registry: what each node type needs in context, and in what order.

Order is fixed by the specification: ROOT -> expose -> entities -> plots ->
events -> scenes -> beats. Beats are not a separate node type; they live inside
the scene node, because a beat is not independently gateable — the thing a judge
can score is the scene the beats compose.

Only ROOT is wired end to end here. The rest declare their context contracts and
raise `NotWired` when driven, so that adding one is a matter of writing its
`context()` and nothing else.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

REPO = Path(__file__).resolve().parent.parent
if str(REPO / "reconstruct") not in sys.path:
    sys.path.insert(0, str(REPO / "reconstruct"))


class NotWired(NotImplementedError):
    """A node type whose context builder has not been written yet."""


def _j(obj, indent: int = 1) -> str:
    return json.dumps(obj, indent=indent, ensure_ascii=False)


# --------------------------------------------------------------------------

@dataclass
class NodeType:
    name: str
    order: int
    rubric: str
    schema_key: str
    per_item: bool
    context: Callable[..., dict] | None = None
    parts: list[str] = field(default_factory=list)


def _root_context(run) -> dict:
    """Everything a ROOT call needs. Stable content first — the script and the
    rubric are byte-identical across rounds, so they sit in front of the
    revision block and the prefix cache survives."""
    from narrativeforge.schemas import SCHEMAS
    from distill import rubric as rubric_mod

    return {
        "overview": _j(run.overview),
        "script": run.script_text,
        "rubric": rubric_mod.as_prompt_text("root"),
        "schema": "SCHEMA (your output must validate against this):\n"
                  + _j(SCHEMAS["story_root"]),
    }


def _judge_root_context(run, artifact: dict) -> dict:
    from distill import rubric as rubric_mod
    return {
        "overview": _j(run.overview),
        "script": run.script_text,
        "rubric": rubric_mod.as_prompt_text("root"),
        "artifact": _j(artifact),
        "schema": "SCHEMA (your output must validate against this):\n"
                  + _j(rubric_mod.critique_schema("root")),
    }


REGISTRY: dict[str, NodeType] = {
    "root": NodeType("root", 0, "root", "story_root", per_item=False,
                     context=_root_context),
    "expose": NodeType("expose", 1, "expose", "expose", per_item=False),
    "entity": NodeType("entity", 2, "entity", "entities", per_item=True),
    "plot": NodeType("plot", 3, "plot", "plots", per_item=True),
    "event": NodeType("event", 4, "event", "events", per_item=True),
    "scene": NodeType("scene", 5, "scene", "scenes", per_item=True,
                      parts=["craft", "psychology", "specimen", "dynamics",
                             "continuity"]),
    "trace": NodeType("trace", 6, "trace", "-", per_item=True),
}

ORDER = [n for n, _ in sorted(REGISTRY.items(), key=lambda kv: kv[1].order)]


JUDGE_CONTEXT: dict[str, Callable] = {
    "root": _judge_root_context,
}


# --------------------------------------------------------------------------
# Scene sub-call instructions. One deep structure per call (docs/05 §1).
# --------------------------------------------------------------------------

SCENE_PARTS = {
    "craft": """\
Where the story stands entering this scene, what this scene is for, what the
scene must accomplish for its parent event and its parent plot, and — explicitly
— what you rejected and why. For every alternative you rejected, name the one
established fact that would have to be false for it to become the right choice.
No psychology in this part; that is the next call.""",

    "psychology": """\
ONE character: {character}. Nobody else, however tempting.

At scene start, at scene end, and at every beat carrying an important state
change: thought, feeling, intent, perception across every available channel,
expression, and beliefs about other minds. Displayed versus felt emotion, with
the leak specified. Internal conflict. Competing goals. Social concerns.
Theory of mind to three degrees with the error named and costed.

Then the whole-life block: at least three of the classes in your cheat sheet,
specific to this person at this hour of this day, and at least one that
measurably changes a line, a timing, an omission or an attention allocation
inside this scene.""",

    "specimen": """\
Six to ten lines of real dialogue at the turning point, spoken only by
characters on the envelope's roster. Then a cold re-read: run the swap test by
giving one character's line to another and say what breaks. If nothing breaks,
say so — that is a finding about the voices, not a failure of the exercise.""",

    "dynamics": """\
The entities that are not minds: the location, the objects, the groups, the
concepts in play. What forces act on each, what changes their meaning, and which
declared state variables move. The location must be the envelope's location.""",

    "continuity": """\
Which established facts this scene used, which standing rules it obeyed, which
contradictions it avoided, and — for every state change recorded anywhere in
this node — the plot it serves and the dramaturgical goal it serves at this
position in the declared structure. A change with no justification here is a
change that should not be in the node.""",
}
