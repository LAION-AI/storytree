# Build 6 — the first significant result

*Eight more findings moved out of the prompt and into code. +0.33, 95% CI [+0.06, +0.61].
The interval no longer contains zero.*

---

## Result

Six pairings, two blind judges, **identical segmentation** so the builds differ only in what the
composer did.

| Pairing | Anchor | Build 5 | Build 6 | Diff |
|---|---|---|---|---|
| pair-01 | sc-001 | 2.86 | 3.00 | +0.14 |
| pair-02 | sc-004 | 2.79 | 2.64 | −0.14 |
| pair-03 | sc-005 | 2.36 | 2.71 | +0.36 |
| pair-04 | sc-012 | 2.79 | 2.86 | +0.07 |
| pair-05 | sc-014 | 2.43 | 3.21 | **+0.79** |
| pair-06 | sc-017 | 2.29 | 3.07 | **+0.79** |
| **mean** | | **2.58** | **2.92** | **+0.33** |

Paired bootstrap, 10,000 resamples: **95% CI [+0.06, +0.61]**, P(build 6 better) = 0.993.
Judges preferred build 6 in **five of six** pairings.

All six pairings are independent this time: build 5's segmentation gives one distinct node per
anchor, unlike the build 4 comparison where one node covered two anchors.

**Neither build passes the bar.** Build 6 means 2.92 with its weakest dimension at 2.00.

### Per dimension

| | Build 5 | Build 6 | Diff |
|---|---|---|---|
| **V3 · state triple completeness** | 2.33 | 3.50 | **+1.17** |
| **V1 · change reality** | 1.83 | 2.67 | **+0.83** |
| A · internal consistency | 1.33 | 2.00 | +0.67 |
| C · specificity | 2.67 | 3.33 | +0.67 |
| D · schema compliance | 1.33 | 2.00 | +0.67 |
| V2 · externalisation | 2.00 | 2.50 | +0.50 |
| R1 · fidelity of inference | 2.50 | 2.83 | +0.33 |
| B · referential integrity | 3.00 | 2.83 | −0.17 |
| E · dramatic competence | 3.33 | 3.17 | −0.17 |
| V5 · mental simulation | 3.33 | 3.17 | −0.17 |

The gains land exactly where the changes were aimed. The three small losses are worth naming:
one judge found build 6's mind material thinner — "seven substantive character readings with
traced mechanism against the other arm's single truncated one" — so **V5 was traded for
contract compliance**, and that trade should not be repeated indefinitely.

## Defects, measured

| | Build 5 | Build 6 |
|---|---|---|
| Placeholder states (`n/a`, "An object") | 30 | **0** |
| Duplicated registers | 64 | **0** |
| Pipeline reasons in `unchanged_because` | 9 | **0** |
| Broken-off fields | 19 | 10 |
| Registers per entity | 5.7 | 4.2 |

The drop in registers is the point: 119 registers were removed that an object cannot have.

## What made the difference

Judges named the register contract in every pairing they separated. The weaker arm gave objects
`knowledge` and `emotional` filled with "An inanimate object; no emotional state" or with a
verbatim copy of the physical text; the stronger held objects to physical/positional/status.

## A fault of my own, and the near-miss after it

Build 6 first came out with **44 placeholders — worse than build 5.** The object rule was in the
scaffold, but **JSON Schema cannot vary `required` per sibling**, so `compose_schema` demands the
union of every entity's registers. One person needing `emotional` forces it onto every object in
the event, and the model answered honestly — *"Not applicable to an object"* — which the lint
then counted as the forbidden placeholder. The model did what it was told; the wiring was wrong.

Fixing it nearly caused worse. My first filter trimmed each entity to the registers the scaffold
had **typed**, which removed **312 of 404 registers**, including many a person legitimately
holds. Caught against the backup and narrowed to the registers an object cannot have: 119.

## Still open

Three faults both judges found that no procedural rule addresses yet:

1. **Fabricated quotations.** A Morpheus line in `carried_uncertainty` that the source does not
   contain, in both arms. Nothing checks a quotation against the scene text.
2. **Cypher leakage persists.** Both arms name him and his bargain in scenes he is not in. The
   new detector flags it on the node; nothing yet acts on the flag.
3. **`unchanged_because` boilerplate.** My replacement text — "nothing across sc-005, sc-006 acts
   on this entity's knowledge" — was itself called out as mechanical. Replacing a pipeline
   sentence with a templated one moved the problem rather than solving it.

---

[Build 5](build5.md) · [Build 3 vs build 4](build3-vs-build4.md) · [The event node](../nodes/event-node.md)
