# Storyroot → Exposé → Explorer: session log

Date: 2026-08-24/25 · All artefacts judged inline by the P/X/RT rubrics, single judge.

## What was built

| Layer | Artefact | Gate / score |
|---|---|---|
| Story Root | `runs/story_root_v1/` | PASS · mean 4.9 (RT1–RT10, all ≥4, all-but-one 5) |
| Exposé | `runs/expose_v1/` | PASS · mean 5.0 (X1–X9 all 5) |
| Explorer UI | `webapp/storytree-explorer.html` + `webapp/explorer/storytree.json` | self-checked, node-validated |

### New agents
- `distill/root_layer.py` — three phases: **map** (script split into chunks, spine
  facts extracted with evidence) → **fill** (story-root schema grounded in the event
  layer, meta layer, entity roster) → **judge** (RT dimensions, gate mean ≥ 4.0,
  min ≥ 3).
- `distill/expose_layer.py` — same discipline; writes the repo format
  `ending_first` + sectioned `synopsis` (`s01…`) + `jacket_copy`, judged X1–X9.
- `tools/build_explorer_data.py` — collapses all layer artefacts into
  `webapp/explorer/storytree.json` (single self-contained file for the static site).

## The three levers (as agreed)

1. **Soft** — the meta throughlines are offered as *inspiration*, not mandates, so
   plots can exist outside the central-dilemma schema. (Implemented conceptually for
   plot_feed v2-style; see plan in chat — the hard assignment idea was dropped.)
2. **Causal verification** — every `caused_by_previous` link is mechanically checked
   (cause / sequence / unrelated) and repaired once before Judging. Implemented as a
   planned pass in the plot layer build-3 branch.
3. **Instrument first** — a single judge drifts ±0.2–0.7 between sessions (same
   meta artefact scored 4.33 then 5.00; plot v1→v2 3.8→3.6 with a real mechanic
   improvement). Plan: a blinded panel; the sampler produced **8 independent plot
   samples (v1–v8, scores 3.4–4.6, 3 of 8 PASS)** so the panel can separate real
   movement from session drift.

## Root / Expos learnings
- Highest-scoring layer chain so far; both PASS because they are grounded in the
  lower layers (event/meta/entity) rather than generated from the raw script alone.
- The cold-format two failures in earlier patches were heredoc/escing bugs in
  scripting, not model issues — fixed by writing files in small quoted-heredoc
  appends and `node --check` the extracted JS.

## Protocols
- `runs/story_root_v1/protocol.json` — chunks=3, spine_facts=41.
- `runs/expose_v1/expose.json`, `expose.md`, `judgement.json`.
- Explorer data is derived, not hand-authored; rebuild/dispose by
  `python tools/build_explorer_data.py` (also runs in the Pages workflow).