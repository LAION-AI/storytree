# Scene Communities

*An explainer for readers new to this project. For how the quality scores work, see
[`docs/rubric-explained.md`](../rubric-explained.md).*

---

## The name, and why it is the right one

A **Scene Community** is everything the system knows about one scene: the scene as written,
the facts it states, and the inferences those facts license — held together as one object.

The obvious name would be "scene node", because that is what the storytree pipeline calls the
scene layer. But a node is a single point, and this is not a single point: it is forty or
fifty small statements, densely cross-referenced to each other and sparsely referenced to
anything outside. In graph theory that structure has a name. It is a **community** — a
subgraph whose members are far better connected to each other than to the rest of the graph.
The term is not a metaphor here; it is a description of the shape.

So the object has two accurate descriptions at once, and both are useful:

|  | View | What it tells you |
|---|---|---|
| **Tree** | one node at the scene layer | *where this scene sits in the story* — its parent event, the plots it serves, the scenes either side |
| **Graph** | a community of cognitive objects | *what this scene is made of* — how its facts and inferences hold each other up |

The tree view is storytree's. The graph view is CogniTino's. They are the same object seen
from two directions, and a Scene Community is what you get when both are true at once.

---

## The problem this solves

Take a fragment of a screenplay:

```text
DOZER
He still needs a lot of work.

NEO
Why do my eyes hurt?

MORPHEUS
You've never used them before.
```

A machine reading this can be asked two very different kinds of question.

**The first kind is answered by the text.** Who spoke? Three people. What did Morpheus tell
Neo? That he had never used his eyes. Did anyone move? No. These are *facts about the
passage*, and there is a correct answer that anyone can check by rereading.

**The second kind is not answered by the text at all.** Does Neo believe Morpheus? Is
Morpheus telling him this now because it is true, or because it is the least frightening true
thing available? What does Dozer think of the man on the table? A screenwriter, a director,
and an actor all have to answer these to do their jobs, and none of the answers is written
down anywhere.

Most systems that read stories collapse these two kinds of question into one pass and produce
a muddle: confident-sounding summaries where checkable fact and unfounded guess are printed
in the same voice, with no way to tell which is which. That failure has a cost — you cannot
correct what you cannot locate, and you cannot trust anything if you cannot trust some of it
specifically.

**A Scene Community keeps them apart on purpose, in three layers.**

---

## The three layers

```
   ┌─ Layer 0 ─────────────────────────────────────────────┐
   │  The scene as written                                 │
   │  Read-only. The ground truth everything answers to.   │
   └───────────────────────┬───────────────────────────────┘
                           │
   ┌─ Layer 1 ─ PERCEPTION ▼───────────────────────────────┐
   │  What the script STATES                               │
   │  Ordered beats · who did what to whom · state changes │
   │  Every line checkable against Layer 0.                │
   │  Built by: Project Alexandria                         │
   └───────────────────────┬───────────────────────────────┘
                           │  grounded_in ▲  (every arrow mandatory)
   ┌─ Layer 2 ─ ABSTRACTION▼───────────────────────────────┐
   │  What the script IMPLIES                              │
   │  Mental states · theory of mind · authorial intent    │
   │  Nothing checkable. Everything traceable.             │
   │  Built by: CogniTino                                  │
   └───────────────────────────────────────────────────────┘
```

**Layer 1 is where facts live.** A beat is one indivisible thing that happens, numbered in
the order the audience receives it. Sorting every beat in the film by
`(scene, beat number)` reconstructs the order in which information was presented — which
means the film's *sequence* is a mechanical property of the data, not something a reader has
to trust prose to convey. Each beat has an address, like `sc-036#4`.

**Layer 2 is where reading lives.** These are the things a script does not say: what a
character wants, fears, misunderstands; what one believes another believes; what the writer
is setting up. They are inferences, and inferences can be wrong.

**The arrow between the layers is the whole design.** Every object in Layer 2 must cite the
Layer 1 beats that license it — by address, and the addresses are checked against beats that
actually exist. An inference that cannot point at its evidence is not recorded, because an
ungrounded claim about a character's mind is indistinguishable from an invention about a
character's mind.

---

## What an inference looks like

Every Layer 2 object carries five things, and the last two are the unusual ones:

| Field | |
|---|---|
| **Claim** | the inference, stated plainly |
| **Because** | the reasoning that gets there |
| **Grounded in** | the beat addresses that license it |
| **Confidence** | `speculative` · `plausible` · `probable` · `near-certain` |
| **Would be wrong if** | the concrete thing that would defeat it |

The confidence scale is deliberately coarse. A system that reports "0.85 confident" about a
fictional character's inner life is claiming a precision it does not have; four bands are
about as fine as the evidence can actually support.

The last field matters most. Requiring every inference to name what would disprove it forces
a distinction that is otherwise easy to blur: *"Morpheus is being protective"* survives any
possible scene and is therefore worthless, while *"Morpheus is withholding the full prognosis,
and would not be if Neo's condition were reversible"* can be checked against what happens
next. An inference nobody can imagine being wrong is not a hypothesis. It is a mood.

---

## How the layers get built

Both layers are built by many small agents working in parallel rather than one agent reading
the whole film, because a model reading 225 scenes at once attends to none of them properly.

1. **Perception.** Agents take a few scenes each and extract beats. Each sees the whole
   screenplay for context, but may only record facts from its own scenes.
2. **Abstraction — drafting.** New agents take five scenes each and write inferences.
3. **Abstraction — research.** *Each agent then tries to break its own drafts*, searching the
   script for evidence that contradicts them, and downgrading confidence where it finds any.
   A researcher who only ever confirms has not researched.
4. **Connection.** Agents that owned neighbouring stretches compare notes and link what
   belongs together, in a widening tree — five scenes, then ten, then twenty, then forty —
   which is how a belief formed in scene 12 gets connected to the moment it is broken in
   scene 47.
5. **Editing.** One agent walks the whole graph in order, making sure "Agent Smith", "Smith"
   and `agent_smith` are recognised as one entity. This step is deliberately *not*
   parallelised: it carries a running list of decisions so later batches reuse earlier ones,
   and parallel workers would each invent their own naming and recreate the mess.

---

## How it is checked

The two layers can fail in completely different ways, so they are checked differently.

A Layer 1 fact can be wrong by contradicting the script, so it is checked against the script.
A Layer 2 inference *cannot* be checked that way — it is supposed to say things the script
does not. Its failure modes are its own:

| | The failure |
|---|---|
| **Ungrounded** | an inference with no evidence pointer, or one pointing at a beat that does not exist |
| **Restatement** | an "inference" that merely rephrases the beat it cites |
| **Uniform confidence** | everything marked `probable`, which means the confidence field is decoration |
| **Never contradicted** | a research pass that only ever confirmed |
| **Disconnected** | objects with no links — a list, not a graph |

**Restatement is the one worth explaining**, because it is invisible to every other check. An
object that says *"Morpheus told Neo he had never used his eyes"* is grounded, well-formed,
on-topic, and adds exactly nothing — it has copied a fact from Layer 1 and relabelled it as
insight. It passes a grounding check perfectly. It is caught by measuring how much of the
statement's wording overlaps the beat it points at.

Every check ships with a deliberately broken input that it must reject. A check that has only
ever been seen to pass is indistinguishable from a check that cannot fail.

---

## Worked examples

Three complete Scene Communities — the scene as written, its perception layer, and its
abstraction layer — are in [`examples.md`](examples.md). They are chosen to show different
regimes: a dialogue-heavy exchange, a dense action scene, and a very short scene where there
is little to infer and the system says so.

## Where this sits

A Scene Community is one node of the storytree at the scene layer. Above it sit events,
plots, the exposé and the story root; below it sits the prose. The layers above have not yet
been rebuilt this way — the scene layer was the one that needed it most, because it is where
the inner lives of characters actually have to be decided.
