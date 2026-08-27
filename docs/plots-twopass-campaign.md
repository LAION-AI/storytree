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


---

# Addendum (same day, evening): refinement loop, best-of-N, v3 seed fix

Same instrument as above (3x GLM-5.3 panel). Three experiments ran in
parallel; all panel numbers in one sweep (`runs/glm53_panel_experiments`).

## Self-critique -> revise loop (`distill/plot_layer_refine.py`)

Round 0 = the existing one-pass artifact; each round: hard self-critique
with executable instructions -> per-plot revision with cross-plot view ->
structural guard -> keep only if the self-judged mean does not drop.

| Arm | Baseline (panel) | Self-judge after loop | Panel after loop |
|---|---|---|---|
| Muse (from 3.33 layer) | 3.33 | loop rejected its own revision (3.2 -> 2.2), artifact unchanged | 3.33 (identical file) |
| Ornith (from v8 2.73) | 2.73 | revised twice, scored itself **4.0 PASS, flat 4s** | **2.53 (-0.20)** |

The hypothesis "self-refinement needs a calibrated self-judge" was
confirmed in both directions: the calibrated composer (Muse) correctly
detected that its revision was worse and kept the original (no-op); the
inflated composer (Ornith) degraded the artifact while awarding itself a
straight-4.0 pass. **Self-critique -> self-revision is falsified for this
task in both calibration regimes.** The valuable component is the
accept-only-if-better guard, not the revision.

## Best-of-N (five Muse one-pass samples, same prompt, temp 0.5)

Panel scores: **3.33 (original), 3.33 (s2)**, 2.93 (s3), 2.87 (s4),
2.47 (s5). Mean ~2.99, max 3.33 twice out of five. The 3.33 was not a
lucky outlier -- it is the muse one-pass **ceiling**, hit reproducibly.
Selection insures against bad draws (spread 0.86) but does not beat the
ceiling. Best-of-5 = 3.33.

## Two-pass v3 (film-spanning throughline seed, closure arc gate)

| Arm | v2 (dilemma seed) | v3 (throughline seed) |
|---|---|---|
| Muse | 2.07 | **3.00** (+0.93) |
| Ornith | 2.07 | 2.07 (P1 1.67) |

The seed diagnosis was correct and the fix moved Muse +0.93 -- and
v3-muse has **P4 = 4.0, the best arc-completeness of any arm in the whole
campaign** (the closure gate worked). But P1 = 2 and P5 = 2 still drag it
below the one-pass ceiling. Ornith did not benefit at all from the fixed
scaffold.

## Where the campaign lands

Eleven plot arms measured under one instrument. The ceiling is **3.33**
(Muse one-pass, reproducible); no structural, refinement or selection
scheme has beaten it; **P1 never exceeded 3.0 on any arm**. This is the
event-layer lesson replaying at layer scale: the mechanically harvestable
gains are harvested; the wall that remains (genuine causal enablement,
distinct framing of shared peaks) is composer capability. Ranked next
steps: (1) a stronger composer via HYPRLAB API (Grok/Opus -- the only
replicated gain in the project's history is a model swap), on BOTH the
one-pass prompt and the v3 scaffold; (2) cross-model link verification
(Muse composes, a different model refutes, Muse regenerates with named
faults); (3) revisit the P5 rubric wording (convergent climax events with
genuinely distinct framing still read as rehash to the judges).


## Judge x composer matrix (27.08.)

Both one-pass arms judged by three 3-judge panels, artifacts anonymised
(`runs/judge_matrix_ornith`, `runs/judge_matrix_muse`; GLM row from the
original panel):

| Judge | v8 (Ornith-composed) | Muse-composed | delta |
|---|---|---|---|
| Ornith panel | 3.53 | 3.87 | +0.33 |
| Muse panel | 2.60 | 3.07 | +0.47 |
| GLM-5.3 panel | 2.73 | 3.33 | +0.60 |

Findings: (1) the ranking Muse > v8 is judge-invariant -- even Ornith
prefers the layer it did not write. (2) Anonymised, Ornith shows no
self-preference; its earlier 4.6 self-score was an in-pipeline context
effect. But Ornith scores P1 at 4.33 on BOTH arms where GLM sees 2.0-2.33:
composer and judge share the same and-then blindness -- the strongest
argument yet that link verification must come from a different model.
(3) Muse-panel and GLM-panel are the same model/instrument, so their gap
is test-retest reliability: +-0.15-0.25 drift between panel draws;
between-arm differences under ~0.3 should not be over-read.
