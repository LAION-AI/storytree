# Build 8 — the carry fix, the verify loop closed, and local judges

*Build 8 against build 7_24 on twelve shared anchors, four independent judge
passes on the local Ornith endpoints: +0.14, CI [−0.12, +0.40] — and build 8
is the first event-layer arm to pass the gate.*

---

## What changed from build 7 to build 8

All five are code, not prompts, continuing the campaign's one replicated
lesson (structure repairs global properties; instructions repair local fields):

1. **The stale-carry bug.** The compose loop handed *every* event of a wave
   the last composed node's exits labelled "entry from the previous event" —
   with `wave > 1`, event N+2 inherited event N+1's state verbatim, which is
   exactly the "entering the hotel ... then leaving the mess hall" fault all
   four build-7 judges named as the top A-killer. Only the event whose true
   predecessor has finished now receives carried state; the rest derive their
   entries from the scenes. Carried rows are labelled with their source event,
   and both scaffold and prompt say UPDATE, don't inherit — the scenes win.
2. **Template reasons normalised by shape.** `_EMPTY_REASON` extended ("no
   recorded change", "neither added nor removed", any sentence naming a scene
   id); `repair_node` clears them and the audit raises the matching fault so
   regeneration writes a reason in the world.
3. **verify_all feeds repair.** Joins are verified BEFORE the regenerate loop;
   every state break and contradiction becomes a named fault on its entity in
   the later event of the pair. Build 7 measured 37 breaks and 20
   contradictions across 22 joins and consumed none of it.
4. **`outside_name` faults got a consumer**: `regenerate_affects_outside`
   rewrites the whole block with the flagged names named, accepted only if the
   flags clear and no slot was bought cheaply.
5. **The roster fold map is authoritative** in `merge_duplicate_keys`, so the
   composer cannot re-split "BIG COP"/"The Big Cop" into conflicting states.

## The judging instrument changed too — so both arms were re-judged

Earlier rounds were judged through an external backend. Build 8 was judged by
four independent passes of **agents-as-judges on our own Ornith endpoints**
(`distill/judge_events.py`): the same docs/cognitino-era 14-dimension rubric,
the same corrected briefing, blind packs keyed outside the repository.

When the judge changes, every number changes calibration. So the baseline was
re-judged first:

| comparison, same new panel | diff | 95% CI | note |
|---|---|---|---|
| build 4 → build 7_24 (23 anchors) | +0.18 | [−0.04, +0.39] | direction reproduces; absolute means are NOT comparable with the old panel's numbers |
| **build 7_24 → build 8 (12 anchors)** | **+0.14** | **[−0.12, +0.40]** | not significant at n = 12 |

## Result

| | Build 7_24 | **Build 8** |
|---|---|---|
| Mean over 12 pairings × 4 judges | 3.88 | **4.03** |
| Weakest dimension | 3.04 (A) | **3.35 (A)** |
| Gate (mean ≥ 4.0, no dim < 3.0) | FAIL | **PASS — first ever** |

Per dimension, nothing broke and the targeted dimensions moved most:
A +0.31, D +0.40, V3 +0.25, R1 +0.31; worst movement C/R2 −0.04.

## Caveats

* One of twelve compose calls failed; eleven events were compared over twelve
  anchors (two anchors share an event span).
* The judges' holistic preference split 24:24 while the per-dimension means
  favour build 8 — and 36 of 48 preferences went to whichever arm sat in
  position A. Position bias is measured, not claimed away; future packs should
  counterbalance presentation order per judge.
* The first pack run lost the judges' `reason` field in the row writer; the
  evidence clauses survived and carry this analysis. Fixed in the writer.

## What the judges' evidence says comes next

Mined from the 72 sub-3 scores: object-contract boilerplate leaking into
person registers ("An object with no knowledge..." as Agent Jones' physical
entry), `moved:true` registers with identical entry/exit, registers filled
from the wrong event, duplicate location pointers, and the V5 ceiling —
theory of mind stops at degree two, errors stated but never costed. These are
build 9's targets; all mechanical or scaffold-shaped.

---
[Build 7 at scale](build7-at-scale.md) · [Handshake](../00-HANDSHAKE.md)
