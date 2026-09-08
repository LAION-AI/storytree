# 20 — The Drama Structure Layer

**Status: implemented and offline-tested** (7 tests over the deterministic
parts, module imports, spec-builder integration). The first live end-to-end
run is pending: at the time of writing every Muse/Zen egress path is down
(0/1085 pool candidates healthy). Nothing else blocks it — the stage is
wired into `build_tree.sh`, so the next tree built after the pool recovers
gets a drama layer automatically.

This document explains, in plain language, what the
drama structure layer is, why it is its own layer rather than a rewrite of
the meta layer, exactly where it sits in the bottom-up and top-down paths,
how its prompts carry the dramaturgy cheat sheet, how its reasoning traces
are produced, and what is deliberately switched off until it has been
measured.

It is the implementation decision for the proposal in
[18 — Dramatic-Structure Extension](18-dramatic-structure-extension.md) and
uses the vocabulary of the
[19 — Dramaturgy Cheat Sheet](19-dramaturgy-cheatsheet.md). One thing
changed against doc 18: the analysis is **not** stored as a subtree of the
meta layer (`meta.dramatic_structure`). It is a **separate layer with its own
directory, its own generator, and its own reasoning traces**. Doc 18's
schema ideas, evaluation rubric and phase plan otherwise still apply.

---

## 1. What this layer is, in one breath

The meta layer answers *what is this story about* — the central dilemma, the
conflicts, the relationship arcs. The drama structure layer answers *how is
this story built*:

- Which structural lens actually fits — three-act, five-act, eight-sequence,
  kishotenketsu, episodic, ensemble, framed, nonlinear — or honestly
  `ambiguous`?
- Where do the load-bearing turns sit — inciting incident, commitment,
  midpoint, crisis, climax, denouement — each proven by a causality test,
  never placed by page percentage?
- How does the story segment into acts, and what changes at each boundary?
- Does the Hero's Journey genuinely organise it, partially, or not at all —
  with `not_applicable` treated as a valid, informative answer?
- What kind of ending is it, on independent axes (plot closure, question
  result, fortune direction, character movement, final gesture)?

The controlled vocabulary is deliberately **form-agnostic**. Nothing in it
assumes a feature film: the lenses include episodic, framed, parallel and
kishotenketsu forms, screen order and story chronology are stored separately,
and every framework claim can be `absent` or `not_applicable`. That is what
makes the same layer usable for classical three-act screenplays, exotic
structures, and — later — novels and whole TV seasons
([series-season-storytree-pipeline](https://github.com/LAION-AI/series-season-storytree-pipeline)).

## 2. Why a separate layer, not a bigger meta layer

Doc 18 originally proposed `meta.dramatic_structure` inside the meta layer.
We build it as a sibling layer instead, for four practical reasons:

1. **Nothing gets rebuilt.** The meta layer, its prompts, its judge and its
   373 existing trees stay exactly as they are. A tree without a `drama/`
   directory is simply a tree built before the layer existed — still valid.
2. **Reasoning traces come for free, in parallel.** The trace pipeline
   (`reasoning_traces/`) works per layer. A new layer means a new spec
   builder and four new traces per film; extending the *meta* layer would
   have meant regenerating meta traces for every tree.
3. **It can be built concurrently.** In the bottom-up path the drama layer
   needs only events + meta. It runs right after meta and does not block
   entities; in a future parallel scheduler the two could run side by side.
4. **Consumption is a switch, not a surgery.** Layers above (plots, root,
   exposé) receive the drama layer as *optional extra context* behind a
   flag. Turning the flag off restores today's measured pipeline exactly.

## 3. Where it sits — bottom-up

```
screenplay text
  → scene layer → event layer → meta layer
                                   │
                                   ├─→ DRAMA STRUCTURE LAYER   (new)
                                   │      inputs: events + condensed meta
                                   │      output: drama/drama_structure.json
                                   ▼
                     entity layer → plot layer → story root → exposé
                          (each optionally ALSO sees the drama layer,
                           only when DRAMA_TO_UPPER=1 — see §6)
```

`tools/build_tree.sh` runs the stage between meta and entities:

```bash
run_stage drama "$T/drama/drama_structure.json" \
  python3 distill/drama_structure_layer.py --events ... --meta ... \
    --out "$T/drama" --ports "$(ports_now)" --model "$MODEL" --source "$SRC"
```

It is stage-level resumable like every other stage: if the output file
exists, the stage is skipped.

## 4. How the generator works

`distill/drama_structure_layer.py`. Four passes, in order, each returning
schema-validated JSON with event/scene-id enums so the model *cannot* cite
material that does not exist:

| pass | produces | sees |
|---|---|---|
| 1 `mode` | narration mode, primary lens + defended alternatives, central dramatic question, values at stake, clock/urgency, exposition analysis | cheat sheet + condensed meta + event digest |
| 2 `anchors` | the structural anchors (controlled vocabulary, ≤14), each with events, evidence, the change it causes, and a why-this-function argument | cheat sheet + pass-1 mode + event digest |
| 3 `acts` | act segmentation using the anchors as boundaries, plus optional sequences with named escalation patterns | cheat sheet + mode + anchors + digest |
| 4 `patterns_ending` | Hero's-Journey applicability and per-stage statuses, the ending on five independent axes, at most a few diagnostics | cheat sheet + anchors + digest |

Three things are **deterministic, never asked from the model**:

- `screen_position` per event — the fraction of the story's scenes that lie
  before the event's middle, computed from the ordered event list;
- anchor ids (`ds-01`, `ds-02`, …) — assigned in screen order after
  generation;
- the sort order of anchors.

After the four passes an **audit** proves what a machine can prove: every
cited event exists, every cited scene belongs to its cited event, acts are
contiguous (`START → ds-x → … → END`, no gaps), acts do not run backwards
when narration is linear, a Hero's-Journey stage marked `supported` must cite
anchors, and no eight-word run of the screenplay survives verbatim. Faulty
passes are regenerated with the fault named — the same audit-and-regenerate
discipline as the meta and event layers. Everything is written to
`drama/drama_structure.json` plus a `protocol.json` with timings, audit
rounds and gate results.

Offline tests for the deterministic parts: `tests/test_drama_structure.py`.

## 5. The cheat sheet rides along in every prompt

The analyst's context always contains
**`distill/prompts/dramaturgy_condensed.md`** — a ~10 KB condensation of the
full [dramaturgy cheat sheet](19-dramaturgy-cheatsheet.md): the
non-negotiable rules (*describe before naming*, *frameworks are lenses*,
*function beats percentile*, *no invented psychology*), the full anchor
vocabulary with recognition signals and the classic confusions, the lens
definitions, the Vogler stages with their false-positive traps, the ending
axes, and the analysis procedure.

Why a condensed copy rather than the full 1,400-line document: the sheet is
in the context of **every one of the four calls** for **every tree**, so its
size is a per-tree cost multiplied by the whole corpus. The condensed file
is the prompt-facing artifact; doc 19 is the reference it is condensed from.
**If you edit one, keep the other consistent** — the condensed file says so
in its header.

## 6. Feeding the layers above — a switch, default OFF

`plot_layer.py`, `root_layer.py` and `expose_layer.py` all accept an
optional `--drama <file>`. When given, a compact digest (lens, question,
anchors with events and positions, acts, ending — the rationales are
dropped) joins their context:

- **plots** can align chains with the actual turning points;
- **root** fills its `dramatic_structure` field from the analysis instead of
  re-deriving it, and must not contradict it;
- **exposé** can pace the synopsis along the acts and honour the actual
  ending type.

In `build_tree.sh` this is controlled by one environment variable:

```bash
DRAMA_TO_UPPER=1 tools/build_tree.sh <slug>   # feed drama to plots/root/expose
tools/build_tree.sh <slug>                     # today's measured pipeline, unchanged
```

**Default is OFF, deliberately.** Plots (3.33), root (4.80) and exposé
(4.44) have measured baselines in
[00-DEFAULT-PIPELINE.md](00-DEFAULT-PIPELINE.md), and that file's rule is:
deviate only with a new measured comparison. The switch becomes the default
only after an A/B on the fixed 3-judge GLM-5.3 panel (same instrument, shared
control arm) shows the drama context helps — the interesting hypothesis is
that anchor/act awareness lifts plot-layer P1 (causal enablement), the known
weak dimension. Until then the flag exists so the experiment is one command,
not a code change.

## 7. Reasoning traces for the new layer

The trace pipeline treats the drama layer like any other layer
(see [`reasoning_traces/README.md`](../reasoning_traces/README.md) for how
hindsight traces work). Additions:

- `trace_specs.py` gained `drama_specs`: **4 specs per film** — `mode`,
  `anchors`, `acts`, `patterns_ending`. Each spec's context reconstructs
  exactly what the generator saw, **including the condensed cheat sheet**,
  and later passes include the earlier passes' results, mirroring
  production.
- `trace_run.py`'s `LAYER_ORDER` places `drama_structure` right after the
  expose layer — it is cheap (4 per film) and information-dense, so the
  breadth-first follower finishes it for every tree early.
- The follower's readiness check does **not** require `drama/` — the 373
  legacy trees stay traceable without it. A tree built by the updated
  `build_tree.sh` has its drama layer on disk before plots/root/expose
  exist, so the follower can never mark such a tree fully-traced while the
  drama specs are still missing.
- **Backfilling legacy trees**: build the drama layer for an old tree (the
  stage-resume in `build_tree.sh` will only add the missing stage), delete
  the tree's marker in `cot_done_trees/`, and the follower — or
  `trace_run.py --layers drama_structure` — picks up the 4 new specs.

## 8. Where it sits — top-down

The forward path gets the same layer as a *plan*, per the user-chosen order:
first the skeleton, then both analysis layers, then the prose-facing exposé
written with both in mind:

```
brief → story root → plot outlines
      → meta layer (planned)
      → DRAMA STRUCTURE LAYER (planned: intended lens, intended anchors)
      → exposé          ← written WITH meta + drama structure in context
      → entities → events → scenes → prose
```

Two rules keep this honest (both from doc 18 §Top-down counterpart):

1. The planned layer uses the **same schema** as the observed one — planned
   anchors instead of found anchors. Downstream generation may deviate from
   the plan only by recording the deviation.
2. After a forward tree is generated, the normal **bottom-up analyzer runs
   over the result** and the observed structure is compared with the plan.
   Structural drift becomes measurable instead of anecdotal.

The top-down pilot (`reasoning_traces/topdown_generate.py`, doc 16) does not
yet include this step; its insertion point is after the root/plots stages and
before exposé generation. That wiring is the next top-down work item, not
part of this change.

## 9. Novels, series, exotic forms

Nothing in the layer's contract mentions screenplays except its inputs
(events built from scenes). Anything the pipeline can decompose into scenes
and events — a novel's chapters, a season's episodes — can be analysed with
the identical vocabulary, because:

- the lens list covers non-conflict-centred (`kishotenketsu`), episodic,
  framed, parallel/ensemble and nonlinear organisation;
- `screen_position` vs. story chronology handles frames and mosaic
  narratives;
- serial forms record `cliffhanger` anchors and season-vs-episode scope
  instead of misdiagnosing open threads as defects (doc 19 §7);
- every framework claim may be `absent`/`not_applicable`, so the analysis
  never coerces a novel into a screenplay template.

For TV seasons the entry point is the
[series-season-storytree-pipeline](https://github.com/LAION-AI/series-season-storytree-pipeline)
(private): its Stage 0 reconstructs scenes from transcripts; from the event
layer upward the drama structure layer applies unchanged, once per episode
and once per season arc.

## 10. Evaluation

- **Automatic invariants** are implemented in the generator's audit (§4) and
  run on every build.
- **Judged quality** uses doc 18's six-dimension rubric (lens
  appropriateness, anchor fidelity, act segmentation, exposition analysis,
  archetype restraint, cross-layer consistency), scored by the sanctioned
  3-judge GLM-5.3 panel, reported by lens and genre, never only as a global
  mean. This judging is not wired into the build (the in-pipeline judges of
  other layers are smoke tests only, per 00-DEFAULT-PIPELINE §Judging); it
  is the instrument for the DRAMA_TO_UPPER A/B and for spot-checking corpus
  batches.

## 11. File map

| file | role |
|---|---|
| `distill/drama_structure_layer.py` | the generator: 4 passes, deterministic positions, audit, regeneration |
| `distill/prompts/dramaturgy_condensed.md` | the prompt-injected cheat sheet (keep consistent with doc 19) |
| `docs/19-dramaturgy-cheatsheet.md` | the full analyst reference the condensed sheet derives from |
| `docs/18-dramatic-structure-extension.md` | original proposal: schema rationale, label plan, rubric |
| `tools/build_tree.sh` | runs the stage after meta; `DRAMA_TO_UPPER=1` feeds it upward |
| `distill/plot_layer.py` / `root_layer.py` / `expose_layer.py` | accept optional `--drama` context |
| `reasoning_traces/trace_specs.py` (`drama_specs`) | 4 hindsight-trace specs per film |
| `tests/test_drama_structure.py` | offline tests of the deterministic parts |
| `<tree>/drama/drama_structure.json` | the artifact |
