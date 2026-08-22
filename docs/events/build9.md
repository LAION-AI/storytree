# Build 9 — a measured regression, and what it taught

*Build 9 against build 8 on twelve shared anchors, four local judges: −0.31,
CI [−0.52, −0.10]. The first significant NEGATIVE result of the campaign, and
the most instructive: every mechanical target was hit, and the artifact still
got worse.*

---

## What build 9 changed

Kept from build 8: the carry fix, template-reason normalisation, the
verify-before-repair loop, the authoritative fold map, the paraphrase pass.
Added, from the build-8 judges' evidence:

1. `boilerplate_state` — the compose prompt's object rule pasted INTO state
   fields ("An object with no knowledge..." as Agent Jones' physical entry).
2. `moved_but_identical` — declared movements whose exit repeats their entry
   verbatim, previously counted by lint and consumed by no one.
3. `bad_pointer` — evidence_scene citations outside the scenes an entity
   appears in, computable from the same inventory shape as lint.
4. Locations closed to an enum of the member scenes' own locations.
5. `tidy_text` cuts dangling clauses even when they end in a period
   ("...is that she." shipped in build 8).

## Result

| | Build 8 | Build 9 |
|---|---|---|
| Mean | **4.23** | 3.92 |
| Gate | PASS | FAIL |
| Paired diff | −0.31, CI [−0.52, −0.10], P = 0.001 |

Every dimension moved down (V3 −0.62, A −0.56 largest).

## Finding 1 — panel drift between judging runs

The SAME build-8 artifact was scored in both pack runs: **4.03 in the pack-8
run, 4.23 in the pack-9 run.** The panel itself moves ±0.2 between sessions.
Within-run paired comparison stays valid — both arms share the session — but
absolute means are NOT comparable across runs, and any cross-run claim needs a
shared control arm re-judged in both. Corrected estimate of build 9's true
effect: roughly −0.1 to −0.3 rather than −0.31.

## Finding 2 — the checks worked, the repairs manufactured faults

The mechanical targets were all hit: `boilerplate_state` 10 → 0, fabricated
quotations 5 → 2, evidence pointers cleaned, MORE register slots (539 vs 481),
longer readings. And yet every dimension dropped. The mechanism, visible in
the judges' own evidence:

* **The unmoved escape hatch.** The fault text offered "either name the path,
  or mark it unmoved with a reason". Models take the lazy branch: Smith's
  positional register shipped `moved:false, exit unchanged` while its change
  narrated him taking Neo into custody. V3 fell 0.62 — more slots, less
  movement.
* **The second escape hatch.** Where the model kept `moved:true`, it made
  `change == exit` verbatim — Trinity's status and safety registers carried
  "no genuine triple" by the judges' reading. Fixing entry==exit created
  change==exit.
* **Regeneration severs the chain.** An accepted regeneration replaces the
  whole triple; predecessor exits are not re-applied. Entries borrowed from
  sc-011 appeared in later events — the exact continuity loss the carry fix
  had eliminated at compose time. A fell 0.56.
* **Objects regenerate badly.** Under the new faults, the "sheets of rain"
  object exited as "She leans against the railing, gazing out at the rain-
  swept street" — a fabricated person inside a weather object, counted by the
  judges under A, V2, R1 and R2 simultaneously.
* Round 1 audited 46 entities with faults — essentially every entity — and
  regenerated 43. Churn of that scale is not repair; it is a rewrite with
  extra steps.

This is lessons #2 and #3 of the build-3..7 campaign, re-earned with new
names: *when a number surprises you, audit the checker* — and *a repair must
not manufacture the fault it removes*. A checker whose remedy changes more
than the fault is part of the defect.

## What carries into build 10

Kept (verified wins): `boilerplate_state`, `bad_pointer`, the locations enum,
the tidy_text fix, everything from build 8.
Changed:
1. The movement-contract fault flags `moved:true` with change==entry or
   change==exit verbatim, and its text no longer offers the unmoved escape.
2. After each accepted regeneration, predecessor exits are re-applied to the
   rewritten triple — chain severance becomes structurally impossible.
3. Regeneration prompts are person/object aware: an object may never carry a
   person's actions.
4. An acceptance guard: a rewrite that nulls a reading the original had is
   rejected.

---
[Build 8](build8.md) · [Build 7 at scale](build7-at-scale.md) · [Handshake](../00-HANDSHAKE.md)
