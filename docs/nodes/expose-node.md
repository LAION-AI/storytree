# The exposé and the story root

*Sketched, not built. No measured examples yet.*

---

## In one paragraph

The top two layers. The **story root** is the one-page identity of the work — what kind of
thing it is, who it is for, what it is about. The **exposé** is the story itself told once
through, in a few paragraphs: what happens, how it ends, what it costs.

Everything below them is more detailed. These two are what you would say if someone asked what
the film is.

## Why they are last, not first

This is the part of the project's history most worth knowing.

The original pipeline built **top-down**: write the story root, then the exposé, then plots,
then events, then scenes. It failed, and it failed in a way that was traceable rather than
vague. The root invented **nine entities where thirty were needed**. The exposé inherited that
poverty. By the time the pipeline reached events, all 22 of them happened at the one location
that existed, and the ending placed a character somewhere her own state model could not hold.

Reversing the direction fixed it: **23 locations against 1, 13 concepts against 0, 11 reversals
against 0.**

So the root and exposé are now the *last* things built, induced from everything below. They
are summaries of a story that already exists rather than promises a story must keep.

## The intended shape

From the existing artifacts, so the names are real:

**Story root** — `story_id`, `title`, `form`, `language`, plus genre, audience and tone.

**Exposé** — four views of the same story at different lengths and angles:

| Field | |
|---|---|
| `jacket_copy` | how it would be sold — the back of the book |
| `plot_summary_short` | the story in a paragraph |
| `plot_summary_long` | the story in a page |
| `ending_first` | the ending, the cost, the final image — recorded **first** |

`ending_first` is the unusual one. It exists because a story generated forwards without a known
ending tends to wander, and because the ending is the part a summary most often gets wrong: it
is easy to say what a film is about and hard to say what it settles.

## Status

**Not built bottom-up and not measured.** Earlier top-down artifacts exist but come from the
direction that failed. These layers depend on plots, which depend on events, which are still
below the quality bar.

**Examples get added when there are real ones.**

## Where to go next

[The StoryTree structure](../storytree-structure.md) · [The plot node](plot-node.md) · [The event node](event-node.md)
