# The plot node

*Sketched, not built. No measured examples yet — see the status note at the bottom.*

---

## In one paragraph

A film does not run one story. It runs several at once and braids them: Neo's recruitment, the
crew's mission, Cypher's betrayal, the Agents' hunt. A **plot node** is one of those threads
recorded on its own — who drives it, what they want, what stands in the way, and how it ends.

Where an [event](event-node.md) is a *slice of time*, a plot is a *line through time*. The same
scene usually belongs to one event and several plots.

## Why the layer exists

Two questions that neither scenes nor events can answer:

**"What is this scene doing?"** A scene where a character makes coffee is inert on its own and
load-bearing if it is the beat where a betrayal plot turns. The plot layer is what makes that
difference visible.

**"Is this story complete?"** A thread that is set up and never paid off is a defect a reader
feels but cannot locate. A structure that lists threads and their steps can be checked for
threads that start and never end.

## The intended shape

Field names below are the ones already in use in an earlier artifact
(`reconstruct/runs/matrix/artifacts/plots.json`), so they are real rather than invented:

| Field | |
|---|---|
| `plot_id` | `pl-03` |
| `spine` | the thread in one sentence |
| `agent` | whose plot it is — who is trying to make something happen |
| `goal` | what they want |
| `resistance` | what stands in the way |
| `interference` | how this plot disrupts *other* plots — the braiding |
| `stakes` | what it costs if it fails |
| `outcome` / `resolution_step` | how it ends, and where |
| `screen_time_share` | how much of the film it occupies |
| `covers_synopsis` | which part of the exposé this thread accounts for |

`interference` is the field that makes this a graph rather than a list. A plot that never
touches another plot is a subplot nobody would miss.

## Status

**Not built and not measured.** An earlier top-down run produced plot artifacts, but those came
from the direction that failed — the story root was written first and everything below
inherited its poverty. Nothing has been produced bottom-up from the [event layer](event-node.md),
which is where it should come from.

The event layer has to stabilise first: it currently scores below the bar, and a plot layer
induced from unreliable events would inherit the unreliability. Building it now would produce
numbers that measure the layer below rather than this one.

**Examples get added when there are real ones.** Nothing on this page is invented output.

## Where to go next

[The StoryTree structure](../storytree-structure.md) · [The event node](event-node.md) · [The scene node](scene-node.md)
