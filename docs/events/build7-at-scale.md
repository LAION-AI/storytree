# Build 7 at scale — 23 anchors, four judges

*The cumulative comparison: build 7 against build 4, covering sc-001..sc-114.
+0.69, 95% CI [+0.49, +0.88], preferred 20:3. The strongest result in the project.*

---

## Result

| | Build 4 | Build 7 |
|---|---|---|
| Mean over 23 pairings | 2.63 | **3.32** |
| Judge preference | 3 | **20** |
| Pairings won | 3 (all < 0.25) | 20 (largest +1.57) |
| Gate | FAIL (weakest 1.22) | FAIL (weakest 2.09) |

Paired bootstrap over 23 pairings, 10,000 resamples: **+0.69, CI [+0.49, +0.88],
P = 1.000.** The three single-step comparisons before this (+0.31, +0.33, +0.24)
sum to almost exactly this value — the changes compose rather than cancel.

## Per dimension — nothing got worse

| | Build 4 | Build 7 | Diff |
|---|---|---|---|
| V3 · state triple completeness | 2.09 | 3.70 | **+1.61** |
| D · schema compliance | 1.22 | 2.57 | **+1.35** |
| G · independent-writer band | 2.87 | 3.83 | +0.96 |
| F · psychological plausibility | 3.00 | 3.87 | +0.87 |
| V1 · change reality | 2.13 | 3.00 | +0.87 |
| V5 · mental simulation | 2.78 | 3.61 | **+0.83** |
| C · specificity | 3.17 | 3.87 | +0.70 |
| V2 · externalisation | 2.78 | 3.35 | +0.57 |
| E · V4 · B · R2 · A · R1 | | | +0.43 … +0.17 |

V5 rising +0.83 matters: build 6 had traded mind material for contract
compliance, and the regeneration loop's reading-length guard was built to stop
that. It did — 9 of 14 dimensions now sit above 3.0 (build 4: 5 of 14).

## What separated the arms

All four judges, independently, named the same two things: **the register
contract** (objects held to physical/positional/status vs. objects carrying
"an inanimate tool, not a knower") and **the `unchanged` discipline** (world
reasons vs. "the scene layer recorded no change"). Both are things that moved
from the prompt into code. One judge noted the separation cuts both ways — in
the one pairing where the contract-breaching arm was build 7's, it lost.

The regeneration loop ran at scale for the first time: **108 of 108 entities
accepted, 0 rejected.**

## What still blocks the bar (mean 4.0, no dimension < 3.0)

Gap: 0.68 mean, and A (2.09) / D (2.57) below the floor. The judges' evidence
names the causes precisely; they are the ranked next steps in the
[handshake](../00-HANDSHAKE.md):

1. **Stale carried entry states** — the top A-killer, cited by all four judges
   ("entering the hotel... then leaving the mess hall").
2. **Template reasons from the old-code compose pass** that regeneration missed
   — one node carries 101 `"No recorded change on this register."` fields.
3. **verify_all findings (37 state breaks, 20 contradictions) feed nothing.**
4. `outside_name` faults carry no entity, so regeneration never touches them.
5. Duplicate entity declarations the model re-splits after the roster folds them.
6. After the procedural tail is harvested: a stronger composer model. The only
   replicated gain in the project is a model swap (+0.38, p=0.002).

## Caveats

* One of 24 events failed compose; 23 were compared.
* Both arms carry two shared upstream faults judges flagged (a "five dead
  candidates" invention; Cypher's bargain leaking into early events) — these
  depress both sides equally and do not affect the comparison.
* Absolute numbers are not comparable to earlier rounds: the judge briefing was
  corrected twice (register contract, elision marks), and briefing errors are
  systematic score shifts.

---

[Build 6](build6.md) · [Build 5](build5.md) · [Build 3 vs 4](build3-vs-build4.md) · [Handshake](../00-HANDSHAKE.md)
