# Plot-layer two-pass campaign — results and the seed finding

Date: 2026-08-26. Question under test (user hypothesis): does a multistep
process — first identify which events belong to which plot (from script +
scene + event + meta layer), then write coherent chains in a second pass —
beat the one-pass composers?

All numbers are the same instrument: 3× GLM-5.3 panel via Zen
(`tools/glm_panel_judge.py`), rubric byte-identical to `plot_layer.py`
(P1–P5), arms anonymised. Self-judgements shown only to track bias.

## The full table

| Arm | Composer | Process | Panel | Self-judge |
|---|---|---|---|---|
| `plot_layer_muse` | GLM-5.3 | one-pass | **3.33** FAIL | 2.6 (harsher than panel) |
| `plot_layer_v8` (online) | Ornith | one-pass | 2.73 FAIL | 4.6 (**+1.9 inflated**) |
| `plot_layer_twopass_v1` | Ornith | two-pass v1 | 2.13 FAIL | 4.0 (**+1.9 inflated**) |
| `plot_layer_qwen38fn` | Qwen3.8 | one-pass | 2.07 FAIL | 2.0 (calibrated) |
| `plot_layer_twopass_v2_muse` | GLM-5.3 | two-pass v2 | 2.07 FAIL | 2.4 (calibrated) |
| `plot_layer_twopass_v2_ornith` | Ornith | two-pass v2 | 2.07 FAIL | 3.0 (mildly inflated) |

Both v2 arms landed on **identical panel scores with the identical
per-dimension shape** (P5 = 1.33 both): given the same flawed scaffold,
the composer stopped mattering. That is clean isolation — the scaffold,
not the model, set the ceiling.

## What the two-pass structure DID fix (keep this)

- **Zero structural chain faults, first time ever** (v1 and v2, both
  composers): `event_id` and `enabled_by` as JSON-schema enums over the
  plot's member ids + a lint for order/duplicates/backward links. Every
  earlier run had order breaks, duplicate citations or unknown ids.
- **Plot identities stopped collapsing into whole-film retellings** (the
  Qwen failure mode) — five distinct stance+carrier plots by construction.
- **The verify→regenerate pattern transfers**: adversarial per-link checks
  refuted 0–4 links per chain; one Ornith regeneration was accepted
  (4→2 refuted), all others correctly rejected by the
  accept-only-if-better guard (repairs must not manufacture faults).
- Ornith's self-judge inflation **replicated a third time** on v1
  (4.0 vs 2.13); interestingly v2's self-judge (3.0 vs 2.07) was less
  inflated — thinner, more inspectable chains seem harder to flatter.

## What broke it: two design errors, one per version

**v1 — the coverage gate was a padding generator.** Forcing every event
into ≥1 plot (a rule imported from `plot_cover.py`) bulk-assigned 35
orphans; the judges then cited exactly those events as padding (P3=2) and
the inflated 17/18-event chains as and-then texture (P1=2). Plots do not
tile the film. Coverage must be a report, not a gate.

**v2 — the seed was wrong, and it dominated everything.** Pass 0 derived
the five plot identities from the meta layer's `perspectives` — which are
five stances on the film's ONE central dilemma (the Morpheus decision).
Consequence, named unanimously by all judges on both composers:

- all five plots cluster on the same late-film sequence
  (capture–torture–rescue: ev-025/030/031/032/034 claimed by 3–4 plots
  each) → **P5 1.33**, the worst redundancy of the whole campaign;
- arcs end before the story's real resolution (ev-044/045 missing) →
  P4 down; the "resolution in the final third" gate passed formally on
  ev-038 while the arc dangled — the gate checked position, not closure;
- the society perspective "lives out both horns" by definition → a
  built-in P2 violation.

The controlled comparison that proves it: Muse one-pass (film-spanning,
self-derived identities) 3.33 vs Muse two-pass (dilemma-anchored
identities) 2.07 — same composer, same judges, only the seed differs.

## The refined lessons

1. "Structure repairs global properties" holds for **form** (order,
   membership confinement, dedup — all fixed), but **causal substance and
   framing live upstream in the seed**. A scaffold amplifies its seed,
   good or bad; five dilemma-stances seeded five overlapping retellings
   of the dilemma.
2. Meta-layer perspectives are stances on a *decision*, not throughlines
   of a *film*. Plot identities must span the story: tested from act one,
   resolved at the story's end.
3. Positional gates check positions. Arc closure needs a semantic check
   ("does the last chain event resolve THIS stance?"), not a percentile.
4. Enum-constrained `enabled_by` produces well-formed, not true, causation
   — the verify→regenerate loop is the right tool but needs a composer
   whose regenerations pass lint (Muse's mostly did not; Ornith's did).

## Where this leaves the hypothesis

Not confirmed, not refuted. The one-pass ceiling so far is Muse's 3.33 on
prompt quality alone. The two-pass machinery is the only thing that has
ever produced structurally clean chains — but it has not yet run with a
correct seed. The decisive v3 experiment: keep the v2 machinery, replace
Pass 0's seed with film-spanning throughline definitions (the one-pass
`prompt_a` style, constrained to the five throughline *types* but free in
scope), strengthen the arc gate to closure ("the resolution event must
turn on this plot's stance and nothing may dangle after it"), and run it
on Muse first (best composer). Artifacts: `runs/plot_layer_twopass_v*`,
panels in `runs/glm53_panel_twopass*`; code `distill/plot_layer_twopass.py`.
