# Reasoning transitions

Every node is produced by two calls: an explicit written deliberation, then the node
conditioned on it. The deliberation is a permanent artifact, scored and inspectable.

## Why not use the model's own reasoning

Because it is not reasoning, it is exhaust. Measured:

| | chars/token | ToM | Trajectory | Craft |
|---|---|---|---|---|
| `reasoning_content` | 0.17–0.95 | none | none | none |
| explicit transition | 4.18 | full | full | full |

The exposed trace is roughly an 18% summary. If you want deliberation you can inspect,
score, or feed forward, ask for it as output.

## What a transition contains

### craft — the dramaturgical decision, no psychology

Where the story stands. What this unit is *for* — what would be lost if it were cut. Why
here and not three scenes later. What collides: which external conflict, which internal.
And the rejected alternatives, including `nearly_chosen` and `what_would_flip_it`.

The near-miss is the most informative field on the page. It is the difference between a
choice and a first idea written down.

### psychology — one block per character, eleven fields

One call per character. Two characters in one call produces two half-blocks
(`05-model-behaviour.md` §1).

| Field | What it must contain |
|---|---|
| `perception` | What they see, hear, smell, physically feel *now*. The trigger for everything else |
| `appraisal` | vmPFC-style valuation: worth, valence, magnitude |
| `social_norms` | What one does here, and what deviating costs |
| `theory_of_mind` | What they think the other thinks; what they think the other thinks of *them*; one degree further. Plus `accuracy` — **where the model of the other is wrong and what the error will cost** |
| `urges` | What they want irrespective of wisdom |
| `impairments` | Fatigue, intoxication, fear, pain, time pressure |
| `deliberation` | dlPFC-style: what is weighed against what |
| `control` | Felt versus expressed — the gap that produces subtext |
| `trajectory` | **Phases across the unit**, each with the perceivable trigger for the shift |
| `intention` | What they now mean to achieve |
| `action` | What they do |

Two fields carry most of the weight and are the two most often skipped:

**`trajectory`.** A character does not stand still for the length of a scene. A single
frozen moment is not a trajectory and is rejected. At least two phases, preferably four,
each with a concrete trigger. Even in the scaffolded version this is the weakest field,
because it competes with ten others — giving it its own call is an obvious next step.

**`theory_of_mind.accuracy`.** A model of another person that is always right produces no
drama. The error, and its cost, is where the scene comes from.

### specimen — the falsifiable part

Six to ten real dialogue lines at the turning point, each with its subtext. Then a cold
re-read checking every risk the reasoning named: is it avoided, and which line proves it?

Plus a question the model must answer about itself: **could the two speakers swap lines
without anyone noticing?** If yes the scene is broken, and that failure is invisible from
inside.

Everything before this is unfalsifiable. An immaculate analysis and a dead scene look
identical on paper until somebody speaks. When budget got tight in the single-call
configuration, this is what got dropped — 0 specimen lines versus 7 — which is exactly
the wrong thing to lose. **Measuring the analysis is what it is for.**

### dynamics — the entities that are not minds

Locations, objects, groups, institutions have states and trajectories too. Which forces
act on them; which axes move — custody, control, cohesion, credence, condition, meaning;
and what the thing **means to the characters afterwards that it did not mean before**. An
object whose meaning never shifts is set dressing, not an entity.

### continuity — cite your sources

Every established fact leaned on names the node id or JSON pointer it came from. Which
world rules had to be obeyed. Which contradictions this node could plausibly have
introduced, and how they were avoided.

## Scoring

`score_transition()` and `grade()` produce `pass` / `thin` / `fail` from: word count,
theory-of-mind towers and how many reach depth 3, specimen line count, alternatives
rejected and nearly-chosen, complete psychology blocks, and dynamics coverage.

These are **structural** metrics. They count whether fields are filled and towers built —
not whether a scene lands. They also reward volume. Treat a `pass` as a floor, not a
verdict, and read the trajectories by hand.

One specific blind spot worth naming: asked for a trajectory from guarded to trusting,
a model returned five phases all valued `"guarded"`. Schema-valid, enum-valid, and empty.
A `flat trajectory` check now counts phases whose state never changes.

## The craft sheet

`craft.py` holds ~7,300 characters distilled from Frey's *How to Write a Damn Good Novel*
I and II plus other craft sources, injected into every generation prompt. It insists on
concrete internal conflicts, on both internal and external conflict in every scene, and
on showing through behaviour rather than explaining through dialogue.

Section 9 is different from the rest: **what a hard review of this system's own output
found.** The failure modes the pipeline actually exhibits, fed back into the prompt that
produces it.
