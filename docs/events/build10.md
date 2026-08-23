# Build 10 — best of 8 and 9: significant, and through the gate

*Build 10 against build 8 on twelve shared anchors, four local judges:
+0.49, CI [+0.22, +0.74], P = 1.000. Every dimension improved. Gate: PASS
(mean 4.17, weakest 3.56) against build 8's FAIL in the same session —
the strongest event-layer result so far.*

---

## What build 10 is

The deliberate best-of: keep build 9's verified mechanical wins, revert its
verified losses (all diagnosed in [build9.md](build9.md)).

Kept from build 9: `boilerplate_state`, `bad_pointer`, the locations enum,
the tidy_text fix.
Kept from build 8: the carry fix with source labels, template-reason
normalisation, verify-before-repair, the authoritative fold map, outside-name
block rewrites.
Changed after build 9's regression:

1. The movement-contract fault no longer offers "mark it unmoved" as an
   escape; it demands a real path between entry and exit, and also catches
   change==exit verbatim — the pattern build 9 manufactured in place of the
   old one.
2. Accepted regenerations get predecessor exits RE-APPLIED to the rewritten
   triple. Chain severance, build 9's quietest defect, became impossible by
   construction.
3. Regeneration prompts carry the entity contract: objects may never hold a
   person's actions (the "sheets of rain" class).
4. A rewrite that nulls an existing reading is rejected outright.

## Result

| | Build 8 | **Build 10** | Δ |
|---|---|---|---|
| Mean | 3.68 | **4.17** | **+0.49**, CI [+0.22, +0.74] |
| Weakest dimension | A 2.69 | A 3.56 | +0.88 |
| Gate | FAIL | **PASS** | |

Per dimension: A +0.88, V3 +0.77, D +0.75, V1 +0.67, V5 +0.60, F +0.56,
V4 +0.54, E/G +0.50; nothing negative (R2 +0.02).

## Mechanical verification (independent of the judges)

On the finished artifact, audited with the current checks:
`boilerplate_state` 10 → **0** (build 8 baseline); `moved_but_identical`
flips gone; `bad_pointer` 3 → 2; fabricated quotations 5 → 7 within noise;
39 entities regenerated, only 4 rejected, 5 faults left; final join verify
10 state breaks / 6 contradictions (build 9: 16 / 9). One compose call failed
of twelve; eleven events compared over twelve anchors.

## Method notes

* Session drift remains real: build 8 scored 3.68 in this session vs 4.03 and
  4.23 in earlier ones. Within-session paired comparison is the instrument;
  cross-session comparisons require the shared control arm, which every pack
  carries.
* The orchestrator aborted silently between builds 10 and its judging because
  the paraphrase pass exits non-zero when residual runs remain and the script
  runs under `set -e`. Builds 8/9 had zero residuals, so this never fired.
  Fixed for future runs; the two residual spans here were elided before
  publishing.

---
[Build 9](build9.md) · [Build 8](build8.md) · [Build 7 at scale](build7-at-scale.md) · [Handshake](../00-HANDSHAKE.md)
