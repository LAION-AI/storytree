# The forward pipeline — brief to screenplay

## Input

A markdown brief. Everything downstream inherits from it, so it is worth writing
properly. See `briefs/lattice.md` for a worked example. What actually matters:

- **Logline** — one sentence containing the reversal, not a premise summary.
- **The protagonist's internal conflict, stated concretely.** This is the field that
  most changes output quality. "She questions whether reality is real" produces
  philosophy-flavoured mush. "She is very good at a job whose actual function is to keep
  a prison running smoothly, and competence has been her identity" produces scenes.
- **In-world mechanics that must stay consistent** — the rules the story cannot break.
  Without these the model invents fresh mechanics per scene.
- **Direction notes** — how to write it, not what to write. "No character explains the
  world to another character who already knows it" is worth more than a page of plot.
- **Intended plot-embedding coordinates** — which of the 52 genres and 24 dimensions
  should be high and which deliberately low.

## Stages

```bash
python3 -m narrativeforge --project runs/x run --brief briefs/x.md \
    --backend hyprlab --model MODEL --response-format json_schema \
    --max-tokens 60000 --reasoning-effort none
```

Runs `story_root → expose → plots → entities → events → scenes`, each validated and
repaired before the next begins. Completed stages are skipped on re-run, so an
interrupted run resumes.

Then the node layer, one node per call with explicit reasoning:

```bash
python3 -m narrativeforge --project runs/x forge --max-tokens 60000 --reasoning-effort none
```

## The plot embedding

`story_root` carries a 76-dimension interpretable coordinate system: **52 genres** and
**24 dimensions**, each scored 0–5 *with an evidence string*. The evidence requirement is
what makes it useful — a number alone is guessed, a number with a defence is a judgement.
From a real run, action scored 1 of 5 with: *"Carriage operation involves timed physical
procedure and evasion of monitoring, but is procedural rather than action-driven."*

`normalize_embedding()` and `validate_embedding()` flag hedging — more than six genres
at ≥4 means the model has refused to commit.

## Known weaknesses

**The upper layers still batch.** All ~35 entities are produced in one call, all events
in one call, all plots in one. That is precisely the configuration measured to cause
budget dilution (`05-model-behaviour.md` §1) — and it fails in practice: an entities
stage was observed producing 89 validation errors, with the repair making it 126.

The scene layer was fixed by scaffolding. The layers above it have not been. Estimated
cost of fixing: one call per entity (~35), events in blocks of 20 (~12), one per plot
(5) — about **3 extra hours on a 66-hour run**, and it addresses an active failure rather
than improving something that already works. This is the highest-value outstanding change
in the codebase.

**The events stage does not segment.** For a 224-scene work it produced 12,363 tokens —
formally valid and far too coarse.

## Cost, measured

One complete feature (5 plots, 32 entities, 36 events, ~32 scenes), Grok 4.6 hosted:

```
41 calls · 734,807 in · 102,108 visible out · 520,211 reasoning
```

Reasoning was **83.6%** of everything generated. Locally at 24.26 tok/s with thinking
suppressed, a comparable run is ~1 h 35 min; with thinking left on, ~8 h.

## Output

```bash
python3 -m narrativeforge --project runs/x validate           # G1–G26
python3 -m narrativeforge --project runs/x state --entity ch-01 --at sc-012
python3 -m narrativeforge --project runs/x timeline
python3 -m narrativeforge --project runs/x site --out runs/x/site
python3 -m narrativeforge shelf --out site runs/x:written:MODEL
```

`site` builds a single self-contained HTML explorer: story root, exposé, plot graph,
browsable entity profiles, zoomable event DAG with inspector, scene timeline, screenplay,
import/export, and a chat co-writer with a 14-tool API for creating and patching every
layer. `include_prose=False` builds a structure-only viewer.
