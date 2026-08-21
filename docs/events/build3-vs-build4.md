# Build 3 against build 4 — a null result

*Blind, three judges, nine paired events. The context fix bought nothing measurable, and the
run turned up a larger defect than the one it was fixing.*

---

## What was compared

Both are event-layer builds from the same scene layer with the same model. Three differences:

| | Build 3 | Build 4 |
|---|---|---|
| Context window | 32,768 — the largest event needed 33,680 | 65,536, plus a guard that counts exactly |
| Anti-copy prompting | none | worked before-and-after examples |
| Coverage | 41 of 57 events (stopped for the fix) | 58 of 59, whole film |

Both were then put through **identical** post-processing — the same chain repair, the same
corrected lint, the same paraphrase pass — so the comparison is of the compose stage and not
of how far each run happened to get.

## Method

Nine pairings, one per scene anchor present in both builds. Paired by **scene anchor**, never
by event id: segmentation moves between builds, so an id names different material.

Arm labels shuffle **per pairing**, so a judge who guesses one cannot carry the guess. The key
is written to a separate directory — an earlier evaluation left it beside the batches and two
of three judges read it. Fields that could identify a build are stripped.

Blinding is label-level, not perfect: a build that has been through the paraphrase pass reads
slightly differently. Hiding that would mean hiding a property under evaluation.

## Result

| Paarung | Anchor | Build 3 | Build 4 | Diff |
|---|---|---|---|---|
| pair-01 | sc-014 | 2.93 | 2.50 | −0.43 |
| pair-02 | sc-035 | 2.50 | 2.57 | +0.07 |
| pair-03 | sc-075 | 3.21 | 2.57 | −0.64 |
| pair-04 | sc-080 | 2.71 | 2.86 | +0.14 |
| pair-05 | sc-090 | 2.71 | 2.93 | +0.21 |
| pair-06 | sc-102 | 3.00 | 2.64 | −0.36 |
| pair-07 | sc-116 | 2.71 | 2.79 | +0.07 |
| pair-08 | sc-121 | 2.79 | 3.14 | +0.36 |
| pair-09 | sc-130 | 3.29 | 2.36 | −0.93 |
| **mean** | | **2.87** | **2.71** | **−0.17** |

Paired bootstrap over the nine pairings, 10,000 resamples: **95% CI [−0.45, +0.09]**,
P(build 4 better) = 0.11. **The interval contains zero.** Judges preferred build 3 four times,
build 4 four times, and called one a tie.

Neither passes the bar (mean ≥ 4.0, no dimension < 3.0). Build 3 means 2.87 with its weakest
dimension at 1.89; build 4 means 2.71 with its weakest at 1.56.

Only two dimensions moved in build 4's favour, and they are the two the changes aimed at:
**externalisation +0.44** and **leakage resistance +0.44**.

## Why the context fix bought nothing

It fixed something real — two truncated generations of roughly 1,180 became zero — but two in
1,180 cannot move a mean over nine nodes. This was predictable before the run and should have
been said before it, not after.

## Two biases, both against build 4

**The elision marks are read as defects.** Build 4 carries 10 visible `[...]` against build 3's
1, because it had more copied text and the paraphrase pass had to elide more often. A judge
names "an `action` field with literal elision markers" as a fault. The de-copying pass
penalises the build that needed it more.

**One dimension is invalid.** The judge briefing said a node "records a state triple across
seven registers". That is build 2's contract. Build 3 and 4 deliberately ask only for the
registers the scene layer recorded a change on — typically three to five. All three judges
marked V3 down for it, on both arms. The A/B holds because the error is symmetric; the
absolute level of V3 does not.

## The finding worth more than the comparison

All three judges independently reported fields breaking off mid-clause, with specific examples:
a `reading` "truncated at 'not seeing that Neo'", another ending in a corrupt non-Latin glyph.

> **Corrected.** This section first reported **23% of long fields truncated**. That number was
> wrong, and wrong the same way three other numbers in this project have been: the *check* was
> measuring the wrong thing. It counted any long field not ending in punctuation as truncated —
> but a state field is often written as a phrase, not a sentence. *"Commanding the room over a
> compliant suspect"* is a complete state description and was counted as damage.
>
> Measured properly — a field within three characters of its schema limit, or ending on a
> function word — build 4 truncates **2.5% / 2.3% of 6,263 fields**, an order of magnitude less
> than reported.

The judges' observation still stands, and points somewhere specific: **`reading` is where it
happens.** It has the tightest budget relative to what it is asked to hold, and the
theory-of-mind clause — the part that earns the dimension — is written last and so cut first.
Four of the five worst offenders are `reading` fields sitting exactly on the 320-character cap.

The cause remains the schema's `maxLength`. Under guided decoding a maxLength does not make a
model concise — **it cuts the sentence wherever the limit falls.** The fix is a bigger budget
where the content justifies it, not a uniform one.

## What the judges found that a lint could have

Ranked by how often it was cited, and all of it decidable without judgement — which means none
of it belonged in a prompt:

1. `moved: false` beside a `change` field narrating a movement
2. `unchanged_because` explaining the pipeline ("the scene layer recorded no change") rather
   than the world
3. one sentence pasted across every register of an entity
4. `affects_outside` reaching forward to outcomes from later in the film, stated as fact
5. quoted dialogue in state fields, which are supposed to be observable
6. the same object under two names in one node ("cellular phone" beside "the phone")
7. `unchanged_because` on registers the node does not contain

---

[The event node](../nodes/event-node.md) · [The context budget](context-budget.md) · [How scoring works](../rubric-explained.md)
