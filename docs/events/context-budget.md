# The context budget

*Why the largest events were coming back truncated, and what now stops it.*

---

## The symptom

Two of roughly 1,180 event-layer generations ended with

```
stop processing: n_tokens = 32767, truncated = 1
```

Rare — about one in six hundred. It still mattered, for two reasons. The node comes back **cut
off rather than absent**, so nothing downstream can tell it apart from a node that was simply
written badly. And truncation is not random: it hits **the largest events**, which are the ones
carrying the most story.

## It was not bad luck, it was arithmetic

The composer sizes its own output from the scaffold:

```python
budget = 3000 + 360 * register_slots + 150 * entities   # capped at 18000
```

For the biggest event in the film, `ev-042` — nine scenes, thirty-three entities — that caps
out at **18,000**. Measured with the server's own tokenizer, its prompt is **15,680 tokens**.

```
15,680 prompt + 18,000 output = 33,680      window = 32,768
```

Nine hundred tokens over. Guaranteed, every run, for that event. The next-largest sat at
30,401 — inside the window with 2,400 tokens to spare, which is close enough that a slightly
longer scaffold would have pushed it over too.

Nothing in the pipeline was checking. The budget formula was written to size the *output* and
never asked whether the input left room for it.

## The fix, in two parts

### 1. A window that fits the work

Both servers now run at **65,536**. On this model the cost is almost nothing — about 350 MB per
GPU, because a sparse MoE's KV cache is small — and the headroom was already there.

Verified rather than assumed: a 62,437-token prompt with a fact planted around position 40,000,
well past the old limit, returned the right answer in 31 seconds. A window the server accepts
but the model cannot actually use would have failed that.

### 2. A guard, so this cannot happen silently again

Raising the window fixes today's numbers. It does not fix the *class* of problem — a longer
screenplay, a bigger scaffold, and the arithmetic goes wrong again. So `fit_to_context()` now
runs before every compose:

1. Count the prompt **exactly**, via the server's `/tokenize`. Estimating is not good enough:
   the overflow here is a few hundred tokens on a 33,000-token call, and a
   characters-per-token ratio is wrong by more than that.
2. If prompt + output will not fit, shrink the scene text — each scene capped, head and tail
   kept, never dropped, so every member scene stays represented.
3. If that is not enough, clamp the output budget, down to a floor of 3,500.
4. Below the floor, report the event as unfittable rather than attempt it. **A truncated node
   is worse than a missing one, because a missing one is visible.**

Anything trimmed or clamped is recorded on the node as `_context_fit` and lands in
`protocol.json` — a run whose largest events were quietly shortened has to be readable as such
afterwards.

## What measuring it turned up

Trimming the scene text is a **weak lever**. Capping every scene in `ev-042` to 400 characters
moved the prompt from 16,052 tokens to 15,314 — about 5%.

The scene text is not what fills the window. The **scene nodes** are: thirty-three entities
with their recorded changes, rendered as JSON. That is worth knowing before anyone tries to
solve a future context problem by feeding less screenplay, which is both the least effective
lever and the one that removes the composer's only independent check on the nodes.

## Numbers

| | |
|---|---|
| Window, before → after | 32,768 → 65,536 |
| Cost | ~350 MB per GPU |
| Verified retrieval depth | 62,437-token prompt, fact at ~40,000, answered correctly |
| Largest event prompt (`ev-042`) | 15,680 tokens |
| Its output budget | 18,000 tokens |
| Overflow under the old window | 912 tokens |

---

[The event node](../nodes/event-node.md) · [The StoryTree structure](../storytree-structure.md) · [Not copying the screenplay](../verbatim-policy.md)
