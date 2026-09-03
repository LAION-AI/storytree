# Reasoning traces: teaching a smaller model *how* the story tree was reached

This directory generates **chain-of-thought reasoning traces** for every layer
of every story tree the pipeline builds, and packages them as a fine-tuning
dataset.

If you are an agent or a person arriving here cold, read this file top to
bottom. It explains what the traces are, why they are built backwards, what
runs in what order, and where every prompt lives.

---

## 1. The problem this solves

The [story-tree pipeline](../docs/00-DEFAULT-PIPELINE.md) turns a screenplay
into a seven-layer structured analysis. Each layer is produced by a large
model answering a carefully written prompt. The **output** of every one of
those calls is saved. The **reasoning** that produced it is not — the models
are called in non-thinking mode, so there is nothing to save.

That is fine for building trees. It is a problem if you want to train a
smaller, cheaper model to do the same job, because the smaller model has to
learn the *reasoning*, not just imitate the answer. Fine-tuning on
`(context -> answer)` pairs alone teaches a model to guess the shape of an
answer; it does not teach it how to get there. In our own experiments a
LoRA trained that way lost the ability to reason at all — it had never seen
a `<think>` block, so it stopped producing one.

## 2. The idea: reason backwards from a known-good answer

We already have thousands of *correct* layer outputs. So instead of asking a
model to solve the problem forwards (hard, and it might get it wrong), we
show it:

- the same material the real generator saw (the scene text, the event
  digest, the entity evidence — whatever that layer's inputs were), **and**
- the answer that was actually produced and passed quality review,

and ask it to reconstruct **the reasoning that would plausibly lead there** —
as if still exploring, weighing alternatives, ruling things out — without
simply restating the answer.

This is *hindsight rationalisation*. It is much easier than solving forwards,
and it produces reasoning that is grounded in the specific material rather
than generic. Here is a real trace fragment (entity layer, character
"Charlie Dalton"):

> Starting from what the material actually names — sc-003 lists CHARLIE
> DALTON by full name in the present list for the Old Stone Chapel [...]
> For age and gender there is nothing explicit. The banner carriers in
> sc-003 are called 16-year-old, but Charlie is not one of them. He appears
> with his mother in sc-004 [...] so I could be tempted to assign 16-17 and
> male, but the material never states it, so I should note the grouping and
> adolescent boarding context **without inventing a number**.

and the target profile it was reasoning towards indeed says *"The research
does not state an explicit age or gender"*. The reasoning matches the answer
because it was derived against it.

### The honest caveat

A hindsight trace is a **plausible** derivation, not the actual one. Nothing
guarantees the real generator "thought" this way. What the traces are good
for is teaching a model the *shape* of correct reasoning over this material —
what to look at, what to weigh, what to refuse to invent. Treat them as
high-quality synthetic supervision, not as ground truth about cognition.

## 3. What runs, in what order

```
   ┌──────────────────────────────────────────────────────────────┐
   │ A. story trees already built by the movie pipeline           │
   │    trees/<slug>/{scenes,events,meta,entities,plots,root,...}  │
   └───────────────────────────┬──────────────────────────────────┘
                               │
                  trace_specs.py  ── for each layer, rebuild EXACTLY
                               │     the (task, context, target) the real
                               │     generator worked with
                               v
   ┌──────────────────────────────────────────────────────────────┐
   │ B. a "spec" per unit of work                                 │
   │    ~250-370 specs per film, across 11 layer types            │
   └───────────────────────────┬──────────────────────────────────┘
                               │
        ┌──────────────────────┴───────────────────────┐
        │                                              │
   trace_run.py                                  cot_follower.py
   (batch: everything at once,                   (daemon: watches for newly
    for trees that already exist)                 finished trees, traces them
        │                                          as they appear)
        └──────────────────────┬───────────────────────┘
                               v
   ┌──────────────────────────────────────────────────────────────┐
   │ C. one JSONL line per trace                                  │
   │    {tid, slug, layer, part, cot, gen_s}                      │
   └───────────────────────────┬──────────────────────────────────┘
                               │
                  build_sft_dataset.py
                               v
   ┌──────────────────────────────────────────────────────────────┐
   │ D. fine-tuning dataset                                        │
   │    system / user / assistant, where assistant is              │
   │    <think>{reasoning}</think>{the target JSON}                │
   └──────────────────────────────────────────────────────────────┘
```

## 4. The files

| file | what it does |
|---|---|
| `config.py` | Resolves the three paths everything needs, from env vars. Start here if something cannot find anything. |
| `trace_specs.py` | **The heart of it.** For each of the 11 layer types, rebuilds the exact `(task, context, target)` triple the production generator worked with. Every task prompt lives here. |
| `trace_run.py` | Batch runner. Builds specs for a list of trees, generates every missing trace, appends to JSONL. Resumable: re-running skips what is already there. |
| `cot_follower.py` | Daemon. Watches the tree directory and traces trees as the pipeline finishes them. See §6 — its scheduling is the non-obvious part. |
| `build_sft_dataset.py` | Joins traces back to their specs and writes `train.jsonl` / `eval.jsonl` in `<think>` format, plus per-layer splits. |
| `hindsight_pilot.py` | The original 5-plot pilot, with a 3-judge quality panel. Kept because it is how the approach was validated before scaling. |
| `hindsight_scale.py` | The plot-layer-only scale-up, with retry-until-quality-threshold. Superseded by `trace_run.py` for all layers, kept for its judging rubric. |

## 5. The 11 layer types, and what each trace explains

A film yields roughly 250-370 specs. The distribution is heavily skewed
toward scenes, because there are many scenes and only one root:

| layer | one trace per… | typical count per film |
|---|---|---|
| `scene_facts` | scene | ~145 |
| `scene_minds` | scene with interiority | ~50 |
| `event_compose` | event | ~31 |
| `event_reconcile` | event whose prose was rewritten | ~15 |
| `entity_profile` | character/object profiled | ~6 |
| `meta_section` | meta section (themes, external, internal, relationships) | 4 |
| `plot_chain` | plot | ~4 |
| `plot_identify` | film | 1 |
| `meta_perspectives` | film | 1 |
| `root` | film | 1 |
| `expose` | film | 1 |

### Bottom-up, with one deliberate exception

The layers are traced bottom-up: each trace's *context* contains only
material from layers **below** it, exactly as the real generator had it.
`scene_facts` sees only raw scene text; `event_compose` sees scene nodes;
`root` sees events + meta + entities.

The exception is `scene_minds`, whose context includes the film's finished
**events** — a layer above it. That is not an oversight, it mirrors
production: the real minds pass is given event context so it can tell what a
scene sets up. (In production this is fed from a hardcoded path that
supplies *the wrong film's* events — a real bug, documented in
the series pipeline repo. Trace generation uses the correct
film's events instead, so the traces are better grounded than the artifacts
they explain. That mismatch is noted here rather than hidden.)

## 6. How the follower works, and why it is breadth-first

`cot_follower.py` runs alongside the tree-building pipeline. Every cycle it:

1. rescans the tree directory for trees that have a `manifest.json` **and**
   every artifact a spec needs;
2. skips trees already fully traced (a marker file per tree, so a restart is
   cheap and never rebuilds specs for thousands of finished films);
3. buckets all still-missing specs **by layer**;
4. works **one layer** — the cheapest layer, by the priority order below,
   that still has pending work anywhere — then rescans.

```
plot_identify → plot_chain → root → expose → meta_perspectives →
meta_section → entity_profile → event_reconcile → event_compose →
scene_minds → scene_facts
```

**Why this order matters.** The first version processed one tree at a time,
finishing it completely before starting the next. Interrupt that at any point
and you have a handful of complete trees and hundreds with nothing. The
breadth-first version instead finishes the cheap, information-dense layers
for *every* tree before starting the expensive ones — `scene_facts` alone is
~55% of all specs. Interrupt it at any point and every tree has its plots,
root, exposé, meta and entities traced, and the dataset is usable.

The follower uses **its own model endpoints**, deliberately separate from the
ones the tree builders use, so the two never compete for the same capacity.

## 7. Reproducing a run

```bash
export STORYTREE_TREES=/path/to/trees
export SCREENPLAY_KU_SRC=/path/to/project-alexandria/screenplay/src
export TRACE_OUT=/path/to/output

# One-off batch over trees that already exist
python3 trace_run.py --ports 8100,8101,8102 --workers 40

# ...or run continuously alongside the pipeline
python3 cot_follower.py --ports 8110,8111 --workers 15

# Then package for training
python3 build_sft_dataset.py --holdout 0.05
```

`build_sft_dataset.py` holds out whole **films**, never individual examples —
otherwise a film's scene traces would train while its root trace evaluates,
and the eval number would be meaningless.

## 8. What was actually produced

Measured on a real run, all 11 layers, 366 films:

- **91,454 traces**, generated at ~4,200/hour against a pool of LLM endpoints
- **~83M training tokens** as `<think>`-format SFT examples
- median trace length ~4,900 characters for the reasoning-heavy layers,
  ~1,600 for scene facts
- 100% of target JSON re-parsed cleanly when packaged

Quality was spot-checked with a 3-judge panel during the pilot (mean 4.75/5
across 5 dimensions, judge-to-judge disagreement 0.16), and a grounding
check confirmed that scene/event IDs appearing in a trace come from that
trace's own film 6-118× more often than from a different film — i.e. the
traces are specific, not generic.

## 9. Related

- The pipeline that builds the trees these traces explain:
  [`docs/00-DEFAULT-PIPELINE.md`](../docs/00-DEFAULT-PIPELINE.md)
- The layer generators whose prompts these traces mirror: [`../distill/`](../distill/)
- Extending all of this from single films to TV seasons:
  [series-season-storytree-pipeline](https://github.com/LAION-AI/series-season-storytree-pipeline) (separate repo, currently private)
