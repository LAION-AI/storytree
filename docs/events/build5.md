# Build 5 — scaffolding that binds

*Seven changes, six events, blind evaluation against the same six from build 4. The first
positive trend in this layer, and it is not yet significant.*

---

## Why build 5 exists

Build 4's blind evaluation was a null result, but the judges' written evidence was not. Almost
everything they cited was **decidable without judgement** — and anything decidable without
judgement does not belong in a prompt. This build moves those decisions into code.

It also closes a gap in the scaffolding: build 4 handed the previous event's exit states to the
first event of each wave only, so **48% of events started blind** and invented their own entry
states. A skeleton that is silent for every second event is a suggestion.

## The seven changes

**Structural, mine:**

1. **The chain closes after every event**, not every wave. With `--wave 1` the state chain is
   exact. The cost is half the throughput: only one endpoint works at a time.
2. **`entry` is set procedurally** where a previous exit exists, instead of being asked of the
   model. An entry that is *known* should not be a question.

**From the judges, all procedural:**

3. `moved: false` beside a `change` narrating a movement — the declaration wins, the narration
   moves to `change_asserted`.
4. One sentence pasted across every register of an entity — marked, not silently accepted.
5. `affects_outside` reaching forward to later outcomes in the film — flagged.
6. `unchanged_because` on a register that moved — removed.
7. The same object under two names — folded.

Plus the length budgets raised, `reading` most of all (320 → 560), and the budget stated in
the prompt instead of enforced silently.

> **A fold that would have destroyed the film's own pivot.** The first version of change 7
> folded `the Big Cop's cuffs` into `BIG COP` — and the cuffs are what `ev-001` turns on.
> Possessives and the person/object boundary are now exempt.

## What the changes did mechanically

Same six events, build 4 against build 5:

| | Build 4 | Build 5 |
|---|---|---|
| `moved: false` with a narrated movement | **280** | **0** |
| Registers per entity | 4.5 | **5.7** |
| Entries the chain repair had to fix afterwards | 15 (whole build) | **0** |
| Contradictions the chain repair had to fix | 334 (whole build) | **0** |
| Fields at their schema limit | 1.4% | 0.8% |
| Copied source runs after the pass | 0 | 0 |

The chain repair having **nothing to do** is the result worth naming. In build 4 it was
retroactively fixing 334 contradictions and 15 broken entries. In build 5 the skeleton holds
them before the model is asked.

## The blind evaluation

Six pairings, two judges, arm labels shuffled per pairing, key held separately. Two corrections
to the briefing, both fixing biases from the previous round: the register contract is now
described accurately, and `[...]` elision marks are declared neutral so the de-copying pass no
longer penalises whichever build needed it more.

| Pairing | Anchor | Build 4 | Build 5 | Diff |
|---|---|---|---|---|
| pair-01 | sc-001 | 2.43 | 3.29 | **+0.86** |
| pair-02 | sc-004 | 2.36 | 2.71 | +0.36 |
| pair-03 | sc-005 | 2.14 | 3.00 | **+0.86** |
| pair-04 | sc-012 | 3.21 | 3.07 | −0.14 |
| pair-05 | sc-014 | 3.00 | 3.00 | 0.00 |
| pair-06 | sc-017 | 3.00 | 2.93 | −0.07 |
| **mean** | | **2.69** | **3.00** | **+0.31** |

Paired bootstrap, 10,000 resamples: **95% CI [−0.01, +0.63]**, P(build 5 better) = **0.967**.
Judges preferred build 5 three times, build 4 twice, one tie.

**The interval touches zero.** This is a trend, not a result. Six pairings is a small sample,
and one of them is not independent: build 4's segmentation puts a single node across both
`sc-014` and `sc-017`, so pair-05 and pair-06 score the same build-4 node twice. Effective
sample is five.

Per dimension, the gains land on what the changes targeted:

| | Build 4 | Build 5 | Diff |
|---|---|---|---|
| G · independent-writer band | 3.00 | 3.83 | **+0.83** |
| F · psychological plausibility | 2.83 | 3.50 | **+0.67** |
| V3 · state triple completeness | 2.00 | 2.67 | **+0.67** |
| D · schema compliance | 1.67 | 2.17 | +0.50 |
| V5 · mental simulation | 2.67 | 3.17 | +0.50 |
| R2 · leakage resistance | 3.00 | 3.50 | +0.50 |
| R1 · fidelity of inference | 3.83 | 3.33 | **−0.50** |

`R1` is the one that fell, and it is the one to watch: build 5 writes more registers per
entity, so it makes more claims, so it has more to get wrong.

**Neither build passes the bar.** Build 5 means 3.00 with its weakest dimension at 2.00.

## Two defects build 5 introduced

**Stale carried state.** The carry map never expires, so an entity absent for two events can be
handed a state from before that gap. Measured: 1 of 10 procedurally carried entries. A judge
found more of them arriving through the scaffold rather than the overwrite — the prompt showed
a previous exit, the model copied it, and the same row's `unchanged_because` then placed the
character somewhere else entirely. The carry should be limited to the immediately preceding
event, and labelled with the event it came from so the model can update rather than inherit.

**Honesty scored as a fault.** Change 4 writes a `register_note` when one sentence fills
several registers. A judge read the note as the node "confessing" that five of six registers
are duplicates, and scored it down. That is fair — the fault is real and the note makes it
visible. But it means build 5's +0.31 was earned while declaring a defect that build 4 simply
concealed.

## What is next

The stale-carry fix, and then more pairings: at six, an interval this wide cannot settle
anything. The changes point the right way on the dimensions they were aimed at, which is more
than the previous two builds managed, and that is all this run establishes.

---

[Build 3 vs build 4](build3-vs-build4.md) · [The event node](../nodes/event-node.md) · [How scoring works](../rubric-explained.md)
