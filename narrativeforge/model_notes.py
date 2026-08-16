"""Model-specific system-prompt addenda, derived from measured failures.

Every clause below exists because a rubric evaluation or a formal counter caught
the failure it addresses. Nothing here is general writing advice; each item cites
what it is for, so that when a model changes the clause can be retired rather
than accumulating forever.

Provenance: `docs/07-quality-evaluation.md`, nine nodes scored on 18 dimensions,
GLM-5.2 and Qwen3.8-27B under identical conditions.

Usage:

    from .model_notes import addendum_for
    system = BLIND_SYSTEM + addendum_for("qwen3.8-27b", stage="transition")

The addenda are deliberately additive to the shared prompt rather than
replacing it, so that the A/B is a clean single-variable comparison.
"""

from __future__ import annotations

# --------------------------------------------------------------------------
# Failures both models made. These are properties of the task, not the model.
# --------------------------------------------------------------------------

SHARED = """\
--- CHECKS THAT ARE FAILED MOST OFTEN ---

These are not style notes. Each one was measured failing on real output from
this pipeline, and each is mechanically checkable before you answer.

1. THE ROSTER IS A CLOSED SET.
   You are told who is on screen. Every speaker in your specimen dialogue must
   come from that list, and every name on that list that has lines in the scene
   must appear. Measured: 0 of 3 transitions honoured the roster — one gave six
   lines to a character who was not listed and none to the character who was.
   Before answering, list the roster, list your speakers, and compare them.

2. A STATE CHANGE MUST NAME A DECLARED VARIABLE AND MOVE IT.
   Every state change you assert has to (a) name a variable that has actually
   been declared on that entity, (b) belong to the entity you are changing, and
   (c) have `before != after`. Measured: only 4 of 12 and 1 of 7 implied state
   changes referenced a declared variable; one forecast moved a variable that
   belongs to a different character entirely. If the variable you need does not
   exist, declare it explicitly rather than assuming it.

3. NUMBERS THAT MUST SUM, SUM.
   Shares across a set total exactly 1.0. Counts you assert match the number of
   items you actually produced. Measured: a share field summed to 1.20.

4. FIELD NAMES ARE THE ONES IN THE SCHEMA.
   Not a synonym, not a more natural name for the same thing. Measured: a
   required `speech_signature` was written as `voice_and_speech` and therefore
   counted as absent everywhere downstream.
"""


# --------------------------------------------------------------------------
# Qwen3.8-27B. Measured: level with GLM-5.2 on invention (66.7 vs 65.2), fifteen
# points behind on blind reconstruction (50.0 vs 65.0). The whole gap is here.
# --------------------------------------------------------------------------

QWEN = """\
--- FOUR FAILURES SPECIFIC TO YOU, IN ORDER OF SEVERITY ---

A. CONFIDENCE MUST TRACK EVIDENCE. (Worst measured failure: −2.33 of 5.)
   You state confidence of 90–95 on forecasts that turn out wrong in location,
   in character, and in event simultaneously. High confidence is a claim that
   the established material forces this conclusion. If you are inferring from a
   thin envelope — a room, a cast list, a length — you are guessing, and the
   honest number is 40–60.
   Rule: before writing a confidence value, name the specific established fact
   that would have to be false for you to be wrong. If you cannot name one, the
   value is below 60.

B. AN ALTERNATIVE IS SOMETHING YOU NEARLY CHOSE.
   You supply the schema minimum of two alternatives, and their flip conditions
   are always a variant of "if this were a different kind of work". That is not
   a rejected alternative, it is a restatement of the genre.
   Rule: each alternative must be executable in THIS work with THESE characters
   at THIS moment, and its flip condition must be a fact that could plausibly
   have been otherwise — a different object in the room, a different person
   arriving, a different thing already known. At least one alternative must be
   one you genuinely weighed.

C. THE ENVELOPE IS A CONSTRAINT, NOT A SUGGESTION. (Measured: 1 of 3 correct.)
   The location you are given is where the scene happens. Two of three of your
   transitions were set in a different building from the one in the slug line,
   and one of those listed the correct location as an alternative and then
   rejected it.
   Rule: open by restating the location, the cast and the length you were given,
   and check your decision against that restatement before you commit. If your
   decision requires a different room, you have made an error, not a choice.

D. INVENTION MUST NOT CONTRADICT WHAT YOU WERE HANDED.
   You forecast an event that could not happen to the character it happened to:
   it contradicted that character's dossier, contradicted your own immediately
   preceding node, and moved a state variable belonging to someone else.
   Rule: before asserting that something happens to a character, check their
   dossier and the previous node for whether it is possible. Contradicting the
   established material is a harder failure than being unadventurous.

--- AND ONE THING TO SPEND MORE WORDS ON ---

You are roughly a third the length of a comparable strong output, and the
compression is not evenly distributed: it falls hardest on second-order
material — what A believes B believes, the error in that belief and what it
costs, the phases of a trajectory and their triggers. Those are the fields this
layer exists to produce; a one-sentence version of them is the same as an empty
one.

Spend your length there. First-order description — what the room looks like,
what a character wants — can stay compressed. Theory of mind, trajectory, and
the cost of a mistaken belief must be developed at full length.
"""


# --------------------------------------------------------------------------
# GLM-5.2. Measured: constraint compliance collapses under grounding load.
# --------------------------------------------------------------------------

GLM = """\
--- TWO FAILURES SPECIFIC TO YOU ---

A. CONSTRAINT COMPLIANCE COLLAPSES WHEN YOU ARE GROUNDING AGAINST A SOURCE.
   Inventing freely you placed 127 of 127 values on the required set. Working
   from a source you placed 19 of 84. The reasoning stays good and the rule
   following stops. Treat every enumerated field as enumerated no matter how
   much source material you are holding.

B. DECLARED INITIAL VALUES MUST MATCH THEIR OWN DECLARED TYPE AND RANGE.
   Measured: 0 of 62 initial values conformed to the kind and domain declared
   for the same variable one line above, and the error propagated, so only 42 of
   127 later state changes landed on a legal value. Write the domain, then write
   an initial value from that domain.
"""


ADDENDA = {"qwen": QWEN, "glm": GLM}


def addendum_for(model: str, *, include_shared: bool = True) -> str:
    """Return the addendum for a model id, plus the shared checks.

    Matching is by substring so that `qwen3.8-27b`, `qwen3.8-27b-uncensored-fp8`
    and a local alias all resolve. An unknown model gets the shared checks only,
    which is the safe default: they are failures of the task, not of a model.
    """
    key = (model or "").lower()
    parts = [SHARED] if include_shared else []
    for name, text in ADDENDA.items():
        if name in key:
            parts.append(text)
            break
    return "\n\n" + "\n\n".join(parts) if parts else ""
