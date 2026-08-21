# The entity node

*Sketched, not built. No measured examples yet.*

---

## In one paragraph

An **entity** is anything the story tracks: people, but also a ship, a phone line, a wall that
gives way. An **entity node** is everything about one of them across the whole film — who they
are, what they are like, how they change from first appearance to last, and who they are
connected to.

Where a [scene node](scene-node.md) says what Neo did in scene 29 and an
[event node](event-node.md) says what state he left event 4 in, an entity node says **who Neo
is over the whole story**.

## Why non-people count

It is tempting to make this a character layer. It should not be.

An event in *The Matrix* turns on a wall giving way. In an early build that wall was filed as a
*location string*, so the pivot of the event carried no state at all — nothing recorded that it
was intact before and breached after. A judge caught it.

The rule that came out of that: **anything whose state changes is an entity**. A phone line
that is cut, a ship that loses power, a pill that is swallowed. If the scenes record a change
to it, it gets tracked.

## The intended shape

From the existing artifacts, so the names are real:

| Field | |
|---|---|
| `entity_id` | `ch-02` — stable everywhere |
| `canonical_name` / `aliases` | one spelling, and every variant folded into it |
| `type` | person, vehicle, program, place, object, faction |
| `profile` | the standing description — what they are like when nothing is happening |
| `state_variables` | the dimensions this entity can change along |
| `state` | current values |
| `arc` | the path from first appearance to last |
| `relationships` | edges to other entities |
| `plots` | which threads this entity belongs to |
| `salience` | how much the story rests on them |

### The part that has to be got right

`arc` is where this layer earns its place, and it is the one thing that must not simply be
re-derived by a model reading the film again. It should be **assembled from the event layer's
state triples**: the entry of the first event the entity appears in, the exit of the last, and
the recorded path between.

That is the point of the chain `exit(N) = entry(N+1)` in the event layer. If it holds, an arc
is a *query*. If it does not, an arc is a fresh guess wearing the costume of a summary — and
there is no way to tell the two apart by looking at the output.

**Canonicalisation is not cosmetic here.** `NEO`, `Neo` and `Neo (V.O.)` reading as three
entities produces three thin arcs instead of one real one. Measured on the current film: 396
spellings fold to 364 entities.

## Status

**Not built and not measured.** It depends on the event layer's state chain, which is what the
current builds are working on. Building an entity layer on a broken chain would produce arcs
that look complete and are not — the most expensive kind of wrong, because nothing in the
output shows it.

**Examples get added when there are real ones.**

## Where to go next

[The StoryTree structure](../storytree-structure.md) · [The event node](event-node.md) · [The scene node](scene-node.md)
