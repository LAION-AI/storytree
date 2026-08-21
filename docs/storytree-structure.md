# The StoryTree structure

*The map. Start here if you have not seen this project before.*

---

## What StoryTree is

A screenplay is prose written for people to read. **StoryTree turns it into a graph a machine
can query** — and runs the same machinery backwards to generate screenplays from such a graph.

The interesting half is the backwards direction, but the measurable half is the forwards one:
take a finished film, take it apart, and check whether the pieces are right. That is what most
of this repository is about.

## The layers

Each layer describes the story at a different grain. Every layer is built from the one below
it, never from the screenplay directly — except the scene layer, which is the only one that
touches the source.

```
   story root      one page: genre, audience, what the whole thing is about
        │
   exposé          the story told once, in a few paragraphs
        │
   plots           the threads. A film runs several at once and braids them.
        │
   events          runs of scenes that form one unit of story          ~50 for a feature
        │
   scenes          one node per scene: who, what, what changed        224 for The Matrix
        │
   ─────────────── the screenplay itself ───────────────
```

**Why bottom-up.** An earlier version of this project built top-down — story root first,
everything below inheriting from it. It failed in a specific way: the root invented nine
entities where thirty were needed, so all 22 events happened at the one location that existed,
and the ending placed a character somewhere her own state model could not hold. Reading scenes
first and inducing upward produced **23 locations against 1** and **11 reversals against 0**.

The direction matters because errors flow downhill. A wrong root poisons everything; a wrong
scene node poisons one scene — unless the layers above copy it, which is why every layer above
scenes is checked against the layer below.

---

## The node pages

Each layer's node type gets its own page: what it is at a high level, the format, and real
examples from *The Matrix* — the nodes themselves, never the screenplay text.

| Layer | Page | Status |
|---|---|---|
| **Scene** | **[The scene node](nodes/scene-node.md)** | ✅ explained, with 3 real examples |
| **Event** | **[The event node](nodes/event-node.md)** | ✅ explained, with 2 real examples |
| Plot | [The plot node](nodes/plot-node.md) | 🚧 format sketched, no examples yet |
| Exposé | [The exposé node](nodes/expose-node.md) | 🚧 format sketched, no examples yet |
| Entity | [The entity node](nodes/entity-node.md) | 🚧 format sketched, no examples yet |
| Story root | *(with the exposé page)* | 🚧 |

The three marked 🚧 have not been built or measured. Their pages describe the intended shape
and say plainly that nothing has been produced yet — examples get added when there are real
ones, not invented ones.

---

## How anything here is judged

Everything is scored the same way, and the scale is deliberately harsh.

**0 to 5, whole numbers only.** The anchor to understand is **3 = "acceptable, would survive
review with notes"** — not "good". A node that fills every field correctly, contains no errors
and adds no judgement scores **3 at best**. That is why scores in this project cluster between
3 and 4 and why nothing has yet averaged 4.0.

**The bar** is mean ≥ 4.0 *and* no single dimension below 3.0. The second half matters: a node
averaging 4.2 with a 2 on fidelity does not pass. One serious defect is not redeemed by
strength elsewhere.

**Blind.** Judges do not know which system produced which node. The first evaluation in this
project was not blind, and when it was repeated blind, **every configuration dropped about 0.4
and the bar that had been reported as cleared turned out never to have been cleared by
anything.**

Full explanation: [How the scoring works](rubric-explained.md).

### A naming collision you will hit

The scene layer's six experimental configurations are called **V0–V5**. The event layer's
rubric dimensions are *also* called **V1–V5**. Unrelated. Scene-V5 is a way of prompting;
event-V5 is the question "is the mental state recorded at both endpoints?". Where both could
appear, the docs write `scene-V4` and spell out event dimensions by name.

---

## What has been learned so far

The results worth knowing before reading anything else:

**The model mattered more than the machinery.** Three attempts to improve the scene layer by
adding structure — an intermediate knowledge layer, narrower windows, an extra deepening pass —
lost or did nothing (−0.44, ±0.00, −1.07). Swapping in a much larger model, with the pipeline
untouched, gained **+0.38 and replicated on a second disjoint sample** (p = 0.002). It is the
only result here that reproduced.

**Structure repairs what instructions cannot.** Repeated so often it is the project's house
rule. A prompt naming an anti-pattern with an example still produced it 440 times; a schema
that cannot express it produced it 18 times. If a value must never appear, forbid it — do not
ask.

**Measurement is where the errors live.** Eight measurement errors are catalogued in the
handshake, every one producing a confident number computed over the wrong thing, and not one
failing loudly. Several more have been added since — including a check that was blind to the
field it was meant to police, and a schema that demanded "exactly seven registers" as a count
and was satisfied by writing the same register seven times.

---

## Reading order

**If you are new**, in this order:

1. [The StoryTree structure](storytree-structure.md) — this page
2. [The scene node](nodes/scene-node.md) — the bottom layer, with examples
3. [The event node](nodes/event-node.md) — the layer above it
4. [How the scoring works](rubric-explained.md) — what the numbers mean

**If you want the experiments:**

| | |
|---|---|
| [The scene layer experiments](scene-layer-explained.md) | six configurations, what worked, what did not |
| [Model comparison](ornith/) | the one change that reproduced |
| [Event layer results](events/) | four builds, including two null results |
| [Build 3 vs build 4](events/build3-vs-build4.md) | the blind comparison, and the defect it turned up |
| [Build 5](events/build5.md) | scaffolding that binds — the first positive trend |
| [Build 6](events/build6.md) | **the first significant result: +0.33, CI excludes zero** |
| [The abstraction-layer attempt](cognitino/results.md) | a design that lost, recorded in full |
| [Not copying the screenplay](verbatim-policy.md) | the rule, how it is checked, and the paraphrase pass |
| [Handshake](00-HANDSHAKE.md) | the fastest path back to working state |
