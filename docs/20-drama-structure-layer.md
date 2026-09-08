# 20 — The Drama Structure Layer

**Status: implemented in both directions, offline-tested, and built live on
The Matrix** — 10 anchors, 4 act bands, zero audit faults on the first pass
(§11). 8 offline tests cover the deterministic parts (screen positions,
anchor ordering, the audit, `plan_view`); 8 more cover the top-down step
`t2b` and its hand-off to the exposé; all 69 top-down tests pass, as do the
22 pair tests. The live route is `tools/serve_hyprlab.sh` → GLM-5.3
(§8a.5), since the free Muse/Zen route no longer accepts external clients.

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

The forward path gets the same layer as a *plan*, in the order the pipeline
can actually support:

```
brief → story root → meta layer (t1) → plot outlines (t2)
      → DRAMA STRUCTURE PLAN (t2b)   ← intended lens, intended anchors
      → entities (t3)
      → exposé (t4)                  ← written WITH meta + drama plan
      → event skeletons → chains → events → scene cards → prose
```

This is implemented in `reasoning_traces/topdown_generate.py` as step
**`t2b`** (`Chain.t2b_drama`), sitting between plots and entities. The
placement is forced by availability, not preference: the plan needs the
root, the meta layer and the plot outlines, all of which exist after `t2`,
and the exposé is the first consumer that benefits from knowing the intended
shape. `t4_expose` now receives the plan and is told to pace the synopsis
along its acts and land its ending. When no plan was built, the exposé
prompt is byte-identical to before, so old runs stay comparable.

### The schema cannot simply be reused — and why

Doc 18 proposed that the plan "uses the same schema with planned rather than
observed anchors". Taken literally that does not work: in the observed
schema every anchor references `event_ids` from a closed enum, and **at
planning time no events exist** — they are only invented at `t7`, five steps
later. An anchor in the forward direction is an intention ("a commitment
that closes off retreat"), not a pointer.

The resolution is a plan-shaped variant, produced by
`drama_structure_layer.plan_view()`:

| observed | plan |
|---|---|
| `anchors[].event_ids` (enum of real events) | *dropped* |
| `anchors[].change` | `intended_change` |
| `screen_position` (computed from event order) | `intended_position` (a target the planner states) |
| `evidence[]` with event/scene ids | *dropped* |
| `exposition.closes_or_reframes_event_id` | *dropped* |
| act boundaries by anchor id | unchanged — plan-internal, still valid |
| lens, acts, Hero's-Journey statuses, ending axes | unchanged |
| `version: "1.0"` | `version: "plan-1.0"` |

The version string is how any downstream tool tells an intention from an
observation.

### Measuring structural drift

The point of planning the structure is to find out afterwards whether the
generated story actually has it. After a forward run:

1. build the tree bottom-up from the generated scenes, up to the drama
   layer, giving an **observed** structure with real event references;
2. match planned anchors to observed ones by kind and order;
3. report, per anchor: found / missing / found-but-displaced (planned
   position vs. observed `screen_position`), plus observed anchors the plan
   never asked for.

Step 3 is the same shape as `tools/compare_root_vs_drama.py`, which already
does this matching between the root's turning points and the drama layer's
anchors. Generalising that comparator to plan-vs-observed is the remaining
piece; the two artifacts it needs both exist now.

## 8a. Does the design hold up? Five things worth knowing

These came out of actually wiring both directions and building the layer on
a real film. They are recorded here rather than smoothed over.

**1. The overlap with `root.dramatic_structure` is real, and the direction
resolves it.** The story root has always emitted its own
`dramatic_structure` — an act count plus a handful of turning points, each
with a free-text `where` naming event and scene ids. That is the same
subject the new layer covers, in less detail and with no controlled
vocabulary. The two can disagree, and by default they are built
independently, so nothing stops them.

- *Bottom-up*: the drama layer is built **before** root, so with
  `DRAMA_TO_UPPER=1` root receives it and is told to fill its
  `dramatic_structure` from the analysis and not contradict it. The flag is
  therefore not only an experiment — it is also the consistency mechanism.
  With the flag off, `tools/compare_root_vs_drama.py` measures how far apart
  the two drifted.
- *Top-down*: the dependency reverses. Root is decided first and legitimately
  constrains the plan, which is why `t2b`'s context includes the root.

Neither direction is wrong, but the artifact means different things in each,
which is what the `version` field records.

**2. The top-down direction leaked the answer, in three places.** This one
was caught by *reading a generated trace*, not by reasoning about the code,
and it is worth spelling out because it is easy to reintroduce.

The first top-down trace opened: *"the story root, the five throughline
outlines and the meta layer are already written, and they are riddled with
event ids and causal claims"*, and then: *"The root's `dramatic_structure`
field has already committed to act_count: 3 with named turning points at
ev-004, ev-010, ev-023, ev-032, ev-044–045."* The planner had been handed
the answer, so it spent its reasoning validating rather than deriving — the
trace was worthless as supervision.

Three separate leaks, all from the same cause: this root, meta layer and
plot set were derived **bottom-up** from a finished film, while a genuine
top-down run generates all three from a brief and none of them can contain
event ids.

| leak | fix |
|---|---|
| `root.dramatic_structure` — literally the answer to the step | `planning_root_view()` drops the field |
| event/scene ids in the root, plot outlines and the meta layer's evidence pointers | the same helper, plus `ID_RE` scrubbing on the other two |
| event ids inside the *target*'s own free-text rationales (`why_this_lens`: "the red-pill birth (ev-010/ev-011)") — the trace generator sees the target | `plan_view()` now unbinds text, not just structural fields |

The third was only visible after fixing the first two: the regenerated trace
*still* cited `ev-010`, because stripping `event_ids` lists does not touch
prose that names the same events. Structural stripping alone is not enough.

After all three fixes the trace carries **zero** event ids and names beats
descriptively — "the pod, the near-drowning, 'no going back'" — which is
what a planner who has not written any scenes yet would actually say. Both
the trace spec and the generator step `t2b` use the same two helpers, so
they see identical material.

This is the hindsight-leakage failure mode from
[`docs/05-model-behaviour.md`](05-model-behaviour.md) appearing in a new
place, and it is the reason the bottom-up pipeline's own rule — *the model
deliberating about scene 40 does not see scene 40* — has to be restated for
every new direction, not assumed to carry over.

**3. Anchors are grounded in events, and only loosely in scenes.** The
analyst sees the event digest, which lists each event's scene ids but not
what happens in those scenes. So when it writes an evidence pointer
`(ev-012, sc-041)` it can pick a *member* scene of the right event but has
no basis for choosing *which* member. The audit enforces membership, not
aptness — a wrong-but-member scene id passes.

This is inherited from the meta layer, which has exactly the same shape, so
the drama layer is no worse than its sibling. It is still a real weakness.
The fix is affordable: a one-line-per-scene index (id, location, ~110-char
summary) for The Matrix is 29.4k characters against the event digest's
29.7k, taking the prompt from ~11k to ~17k tokens. That is a change to the
layer's inputs and therefore needs a measured comparison before it becomes
the default — it is the obvious next experiment, not an oversight.

**4. Passes can outgrow an 8k output budget.** On The Matrix (47 events, 224
scenes) the `mode` pass twice produced exactly 8,000 completion tokens —
`finish_reason=length`, which `EndpointPool` rejects outright rather than
accepting a truncated artifact. Each truncation burns a full retry
(~100 seconds). The layer now asks for 16k, unlike the 8k the other layers
use, because its per-item rationales are long.

**5. The free model route is gone; the layer is model-agnostic anyway.** As
of 2026-09-08 the OpenCode Zen free tier refuses every non-OpenCode client
(`MissingSessionID`: *"OpenCode's free tier can only be used in OpenCode"*),
which is what the whole VPN/proxy exit pool existed to work around — the
pool now reports 0/1084 healthy for that reason, not because of IP metering.
`tools/hyprlab_shim.py` + `tools/serve_hyprlab.sh` provide the same local
`EndpointPool` interface against a paid OpenAI-compatible endpoint serving
**GLM-5.3 — the same model Muse 1.2 was**, so model identity is preserved
and only the route changed. That upstream intermittently answers valid
requests with a 400 that resolves on retry, so the shim retries transient
codes itself instead of burning the pool's attempts.

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

## 11. What the first live build produced (The Matrix)

Built 2026-09-08 from the reference tree's own artifacts
(`runs/events_build10_full` + `runs/meta_layer_v2b`, 47 events over 224
scenes), GLM-5.3 via the Hyprlab shims. Reproduce with:

```bash
bash tools/serve_hyprlab.sh 8300 3
python3 distill/drama_structure_layer.py \
  --events runs/events_build10_full/events.json \
  --meta   runs/meta_layer_v2b/meta.json \
  --out    runs/drama_matrix --ports 8300,8301,8302 --model glm-5.3 \
  --source distill/runs/matrix/script.normalized.txt
```

**21 minutes, 10 anchors, 4 act bands, 10 sequences, audit round 1: 0
faults, 0 verbatim runs.** A clean first pass — every cited event existed,
every cited scene belonged to its cited event, the acts were contiguous
from START to END, and every `supported` Hero's-Journey stage cited an
anchor. No regeneration round was needed.

### The discipline held where it matters

The interesting test is whether the layer obeys *function beats percentile*
when the two disagree. On The Matrix they do:

- The **Oracle scene (ev-023, 42%)** is labelled `reframing_reveal`, with
  `midpoint` and `recognition` as secondary functions, and the argument is
  functional, not positional: *"Neo stops pursuing 'being the One' and
  begins operating as an ordinary man bound by loyalty."*
- The event nearest the literal middle (ev-025, 52%) is labelled
  `pinch_point`, not midpoint.

The lens rejections are specific rather than pro-forma: `archplot` was
rejected because it "describes the plot-class, not the act machinery";
`kishotenketsu` because "the spine is conflict-driven and goal-directed;
the twist is earned by causality". The Hero's Journey came out `organising`
with 11 of 12 stages `supported` and `reward` left `ambiguous` — refused
rather than forced. The single diagnostic, `unresolved_thread`, scoped
itself correctly: *"expected for a franchise instalment, flagged as
context."*

### Cross-layer agreement with the story root

`tools/compare_root_vs_drama.py` on the same film, with the two layers built
**independently** (no `DRAMA_TO_UPPER`):

| | |
|---|---|
| root turning points matched to a drama anchor | **6 of 6** |
| anchors the root does not name | 4 (`opening_situation`, `first_trial`, `pinch_point`, `all_is_lost`) |
| acts | root 3; drama 3 + 1 coda band ("Denouement — Escape and the new world") |

Every beat the root independently located, the drama layer located too, on
the same events. The root is a strict subset — which is the expected healthy
shape, since the root names ~5 beats and the layer may name up to 14. The
apparent 3-vs-4 act difference is a closing denouement band, not a
disagreement; the comparator now separates coda bands from acts so this
reads correctly instead of looking like a contradiction.

This is a single film and therefore evidence, not proof. It is, though, the
cheapest available check that the layer is describing the same story the
rest of the tree describes, and it can be run over any tree that has both
artifacts.

### Reasoning traces

Five specs for this film, both directions, generated through the same
runner as every other layer:

| tid | context | target |
|---|---|---|
| `drama_structure::mode` | 44.1k chars | 4.9k |
| `drama_structure::anchors` | 41.1k | 13.4k |
| `drama_structure::acts` | 45.1k | 8.0k |
| `drama_structure::patterns_ending` | 43.2k | 4.8k |
| `drama_plan::all` (top-down) | 33.8k | 24.5k |

The bottom-up contexts each carry the condensed cheat sheet plus the event
digest, exactly as the generator saw them. The top-down context carries the
cheat sheet, the story root, the plot outlines and the condensed meta layer,
all three unbound from event references per §8a.2 — the planning direction
has no events, so nothing it sees may name one.

The traces show the cheat sheet doing its job, which is the point of putting
it in the context. From the `mode` trace, ruling out a lens rather than
asserting one:

> The spine is a single active protagonist […] that smells like archplot.
> But archplot describes the plot-class, not the act machinery; the task
> asks for the least-forcing structural lens, and I should test whether the
> act structure is actually visible.

From the `patterns_ending` trace, reaching for the false-positive table
before labelling anything:

> That smells like a genuine monomyth rather than an overfit — but the
> reference warns me about false positives, so I should test each stage
> against its trap before concluding.

And the `acts` trace independently noticed the same three-acts-plus-coda
tension described above, and reasoned about it instead of smoothing it over:

> That's a problem: ds-08 is the crisis, not an act boundary per se... or is
> it? […] the target has four units […] So the analyst treated the
> denouement as a separate short unit rather than fold[ing it in].

That is the behaviour hindsight traces are supposed to teach: exploring,
noticing friction, and resolving it — not narrating the answer backwards.

## 12. File map

| file | role |
|---|---|
| `distill/drama_structure_layer.py` | the generator: 4 passes, deterministic positions, audit, regeneration |
| `distill/prompts/dramaturgy_condensed.md` | the prompt-injected cheat sheet (keep consistent with doc 19) |
| `docs/19-dramaturgy-cheatsheet.md` | the full analyst reference the condensed sheet derives from |
| `docs/18-dramatic-structure-extension.md` | original proposal: schema rationale, label plan, rubric |
| `tools/build_tree.sh` | runs the stage after meta; `DRAMA_TO_UPPER=1` feeds it upward |
| `distill/plot_layer.py` / `root_layer.py` / `expose_layer.py` | accept optional `--drama` context |
| `reasoning_traces/trace_specs.py` (`drama_specs`) | 4 hindsight-trace specs per film, bottom-up |
| `reasoning_traces/trace_specs.py` (`drama_plan_specs`) | 1 spec per film for the top-down (planning) direction |
| `reasoning_traces/topdown_generate.py` (`t2b_drama`) | the top-down generator step; feeds `t4_expose` |
| `tools/compare_root_vs_drama.py` | cross-layer consistency: root turning points vs. drama anchors |
| `tools/hyprlab_shim.py`, `tools/serve_hyprlab.sh` | local `EndpointPool`-compatible route to GLM-5.3 (see §8a.5) |
| `tools/build_explorer_data.py`, `webapp/storytree-explorer.html` | the explorer's drama zone: anchor timeline, acts, Hero's-Journey table, ending axes |
| `tests/test_drama_structure.py` | offline tests of the deterministic parts, incl. `plan_view` |
| `tests/test_topdown.py` | offline tests of the `t2b` step and the exposé hand-off |
| `<tree>/drama/drama_structure.json` | the artifact |
