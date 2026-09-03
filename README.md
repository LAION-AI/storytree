# storytree

**New here? Start with [The StoryTree structure](docs/storytree-structure.md)** — the
layers, what each node contains, real examples from *The Matrix*, and where the measurements
are.

### Map of the parts

| I want to… | go to |
|---|---|
| understand the layers and what a tree contains | [`docs/storytree-structure.md`](docs/storytree-structure.md) |
| **run the pipeline that is in production today** | [`docs/00-DEFAULT-PIPELINE.md`](docs/00-DEFAULT-PIPELINE.md) — the normative recipe: which script, which model, which order |
| see the layer generators and their prompts | [`distill/`](distill/) |
| **generate chain-of-thought reasoning traces** from built trees, for fine-tuning a smaller model | [`reasoning_traces/`](reasoning_traces/) |
| extend this from single films to **whole TV seasons** | [`series-season-storytree-pipeline`](https://github.com/LAION-AI/series-season-storytree-pipeline) — separate repo, currently private |
| know what was measured, and what failed | [`docs/EXPERIMENT-LOG.md`](docs/EXPERIMENT-LOG.md), [`docs/07-quality-evaluation.md`](docs/07-quality-evaluation.md) |

**Explore the recovered tree live:** the [Storytree Explorer](https://projects.laion.ai/storytree/webapp/storytree-explorer.html)
renders the top-down chain — story root, exposé, meta layer, plots, events, entities,
scene layer — from a single data file. Rebuild it with
`python tools/build_explorer_data.py` (the Pages site is deployed from the `main` branch).


Generate screenplays as an explicit, inspectable graph — and run the same machinery
backwards to recover that graph from a finished screenplay.

Prose is the *last* thing this system writes. Before a single line of dialogue exists
there is a story root, an exposé, a set of plots, entity profiles with full state
dictionaries, an event chain, and scene profiles carrying entry state, state changes
and exit state. The screenplay is the leaves of that tree. Everything above it is
addressable, diffable, and can be regenerated at any point in story time.

## Why bother

A language model asked for "a screenplay" produces something that reads well for three
pages and then quietly forgets that a character is supposed to be dead. The failure is
not stylistic, it is bookkeeping: nothing in the generation process is tracking state,
so nothing can notice when state is violated.

This system makes the bookkeeping explicit and mechanical:

- **State is data, not prose.** Every entity has a state dictionary. Every beat emits
  RFC 6902 JSON Patch operations against it. The state of anything at time *T* is
  `apply(t0, concat(ops of every beat before T))` — a fold, computed, never remembered.
- **Structure is enforced, not hoped for.** Each event has exactly one parent plot; each
  scene exactly one parent event. 26 graph invariants (G1–G26) are checked
  deterministically, and the checker is itself tested against 23 injected errors.
- **Reasoning is written down.** Before each node is produced, the model writes an
  explicit deliberation — perception, appraisal, theory of mind to three degrees,
  trajectory across the unit, rejected alternatives, and a specimen of the actual
  dialogue. That trace is a first-class artifact, not a discarded scratchpad.

## The two directions

**Forward** (`narrativeforge/`) — brief in, screenplay out, via seven layers.

```
story root → exposé → plots → entities → events → scenes → prose
```

**Reverse** (`reconstruct/scriptforge/`) — a finished screenplay in, the whole graph
above it out, with each scene profile bound to exactly one real scene by anchor strings.

The reverse direction has one rule that makes it worth anything: **the reasoning is
written blind.** The model deliberating about scene 40 does not see scene 40. It sees
what earlier layers established plus the scene's outer envelope, and must *decide* what
should happen rather than *describe* what does. A model that knows the outcome can
justify it effortlessly, and such justifications are worthless. The blind constraint is
what turns the exercise into a measurement.

## What is in here

| Path | What it is |
|---|---|
| `narrativeforge/` | Forward pipeline: schemas, prompts, validator, timeline fold, CLI |
| `reconstruct/scriptforge/` | Reverse pipeline: screenplay parser, blind/sighted split, scaffolded assembly |
| `docs/` | Everything learned, written up — start with `01-architecture.md` |
| `reports/` | Deployment reports for running large models locally |
| `webapp/` | Single-file graph explorer, chat co-writer, published status pages |
| `runs/`, `reconstruct/runs/` | Experiment outputs (structure only; see Copyright) |
| `tests/` | 52 tests, including 23 injected-error detection cases |

## Documentation

**Resuming after a break, or new to this?** Start with [`docs/00-HANDSHAKE.md`](docs/00-HANDSHAKE.md) — state, what worked, what did not, and what was about to happen next.

Read in this order:

1. [`docs/01-architecture.md`](docs/01-architecture.md) — the layered graph, JSON Patch, the fold, and why there are no arrays in patchable regions
2. [`docs/02-forward-pipeline.md`](docs/02-forward-pipeline.md) — brief to screenplay
3. [`docs/03-reconstruction.md`](docs/03-reconstruction.md) — screenplay to graph, and the blind/sighted split
4. [`docs/04-reasoning-transitions.md`](docs/04-reasoning-transitions.md) — what a deliberation contains and why each field is there
5. [`docs/05-model-behaviour.md`](docs/05-model-behaviour.md) — **the most useful file here.** Measured failure modes: budget dilution, silent no-ops, hindsight leakage, and what actually fixed them
6. [`docs/06-local-inference.md`](docs/06-local-inference.md) — running a 754B model on 8×A100, and three confident predictions that measurement destroyed
7. [`docs/07-quality-evaluation.md`](docs/07-quality-evaluation.md) — rubric and scores
8. [`docs/08-operations.md`](docs/08-operations.md) — how to actually run it
9. [`docs/09-anthropic-prose-research.md`](docs/09-anthropic-prose-research.md) — what practitioners claim Anthropic models do better at prose, with evidence tiers. Contains a significant **negative** result
10. [`docs/09b-rp-ecosystem-evidence.md`](docs/09b-rp-ecosystem-evidence.md) — the roleplay-finetune ecosystem as revealed preference
11. [`docs/10-prose-system-prompt.md`](docs/10-prose-system-prompt.md) — an actionable prose addendum, every clause traced to a finding
12. [`docs/12-swarm-results.md`](docs/12-swarm-results.md) — **the bottom-up swarm's first two runs.** What the inversion proved, the bug that made the first run worthless, and the canary that would have caught it
13. [`docs/13-scene-experiments-data.md`](docs/13-scene-experiments-data.md) — raw scene-layer data and method
14. [`docs/14-rubric-scores-and-next-steps.md`](docs/14-rubric-scores-and-next-steps.md) — **all rubric scores, the oracle-ceiling analysis, and proposals**
15. [`docs/experiments/`](docs/experiments/README.md) — **the experiment log.** Every intervention tried, prediction recorded before the run, negative results kept. Written to be reconstructable without access to whoever ran it

## Quick start

```bash
python3 -m narrativeforge --project runs/demo run \
    --brief briefs/lattice.md --backend hyprlab \
    --model grok-4.6 --response-format json_schema

python3 -m narrativeforge --project runs/demo forge      # explicit reasoning, one node per call
python3 -m narrativeforge --project runs/demo validate    # G1–G26
python3 -m narrativeforge --project runs/demo state --entity ch-01 --at sc-012
python3 -m narrativeforge --project runs/demo site --out runs/demo/site
```

Reverse:

```bash
python3 -m scriptforge --project reconstruct/runs/x parse   --script path/to/script.txt
python3 -m scriptforge --project reconstruct/runs/x recover --stages story_root,expose,plots,entities,events
python3 tools/run_local_matrix.py reconstruct/runs/x sc-001 sc-002 --think off
```

Backends: any OpenAI-compatible endpoint (`HYPRLAB_BASE_URL`), or a spawned local agent.
Tested against Grok 4.6, GLM-5.2 hosted, and GLM-5.2 quantised on local A100s.

## Three findings worth your time even if you never run this

**Models do not scale effort to the task.** Ask for four psychological analyses in one
call and you get four hollow shells; ask four times for one and you get four complete
ones. Output volume was near-constant at ~28,000 characters regardless of what was
demanded. Restructuring to one deep structure per call took a scene from 41 schema
violations to 0, and from 0-of-4 to 4-of-4 passing. See `docs/05`.

**Sparse mixture-of-experts models break the standard inference optimisations.** On a
256-expert top-8 model, speculative decoding with a weak drafter was a *25% regression*,
and running 8 concurrent requests gave exactly zero aggregate throughput gain over 1.
Both for the same reason: every extra token in the batch pulls its own experts, so
widening the batch costs near-full weight traffic. The model's own trained draft head
cleared 79.6% acceptance and won 45% — the technique is strongly one thing or the other,
not mildly helpful. See `docs/06`.

**A performance flag that returns HTTP 200 has told you nothing.** `reasoning_effort:
"low"` on GLM-5.2 is a silent no-op that actually selects *maximum* effort, because the
chat template maps every value that is not the literal string `high` to `max`. Hidden
reasoning was 83.6% of all generated tokens. Verify by measuring `completion_tokens`,
never by checking that the call succeeded.

## Copyright

The reconstruction pipeline reads copyrighted screenplays to derive structure. It stores
results **by reference** — character offsets and anchor strings — and never copies the
prose. `--inline-prose` exists and is opt-in; published viewers are built with
`include_prose=False`. Source text files are gitignored and do not leave the machine
they were processed on. Committed artifacts contain structural fields only.

## Status

Working, actively used, not packaged. Python 3.11+, standard library only for the core
(the JSON Patch, JSON Pointer and JSON Schema implementations are hand-rolled so the
pipeline runs on a bare interpreter); `requests` for HTTP backends.
