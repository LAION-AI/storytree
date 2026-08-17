# 2 · The stage graph

Ten stages, from a parsed screenplay to a finished narrative graph. This section
sets out what each stage consumes and emits, which stages can run at the same time,
and where the pipeline genuinely has to stop and wait.

The distinction that organises the section: a **dependency edge** is any place where
stage B needs output from stage A. A **synchronisation barrier** is narrower — a
point where two *independent lineages* must both complete before anything downstream
can start. Dependency edges are everywhere and most of them can be pipelined or
streamed. Barriers cannot. There are two.

---

## 2.1 Stage 0 — parsing, which is not a stage

Before any agent runs, `screenplay.py` turns the source into scenes: slug lines,
character cues, parentheticals, dialogue, action, and an anchor table so each scene
can be re-sliced from the source deterministically. This is code, it is
deterministic, and it is the reason the whole design has a fixed unit to work in.

It is worth naming as a non-stage because the boundary matters: **the scene division
is given, and the event division is not.** Scene boundaries are typographic facts
about a screenplay. Event boundaries are a reading. Stage 2 exists because of that
asymmetry, and a prose corpus with no slug lines would need a stage 0 that is itself
a model call — which this design has not been tested on and does not claim to cover.

Measured on `reconstruct/runs/matrix`: 224 scenes. All per-stage unit counts below
use that figure.

---

## 2.2 The ten stages

| § | Stage | Consumes | Emits | Units | Shape |
|---|---|---|---|---|---|
| 3 | 1 · scene nodes | full script + one scene's text | one scene node per scene | 224 | fully independent |
| 4 | 2 · event boundaries | all scene nodes + script | scene → event assignment | 56, in 3 passes | parallel within a pass |
| 5 | 3 · event drafts | boundaries + member scene nodes + script | event draft + plot speculation | ~30 | fully independent |
| 6 | 4 · plots | all event drafts | plot list + membership | 1 + 5 + 1 | 3 phases, 5-wide in the middle |
| 7 | 5 · entities | scene nodes + event drafts + script | canonical ids + alias table | 4 | fully independent |
| 8 | 6 · profiles | plots + entity ids + everything below | one profile per entity | ~35 × 3 | independent across entities |
| 9 | 7 · root | plots + entities + events | story root | 3 | sequential chain |
| 9 | 8 · exposé | root + plots + events | exposé | 1 + ~5 + 1 | 3 phases |
| 10 | 9 · event rewrite | the whole tree + member scenes | final event nodes | ~30 | fully independent |
| 10 | 10 · scene rewrite | the whole tree + one scene's text | final scene nodes | 224 | fully independent |

Unit counts for stages 3, 6 and 9 are **assumed** — they depend on how many events
and entities the induction actually finds, which is the thing under test. Stage 2's
56 is arithmetic on 224 scenes (§4.2); the summary table's 57 counts the tail window
differently, and the exact number depends on how a partial final window is handled.

---

## 2.3 The graph

```
        script
          │
          ▼
   ┌─────────────┐
   │  stage 0    │  parse (deterministic)
   └──────┬──────┘
          │  224 scene texts, verbatim anchors
          ▼
   ╔═══════════════════════════════════════════════════╗
   ║  STAGE 1 · scene nodes            224 agents      ║
   ║  blind of root, plots, events                     ║
   ╚═══════════════════════════════════════════════════╝
          │  224 scene nodes, names not yet unified
          ▼
   ╔═══════════════════════════════════════════════════╗
   ║  STAGE 2 · event boundaries                       ║
   ║    pass A   44 windows of 10, stride 5   ║ ─┐     ║
   ║    pass B   11 windows of 25, stride 20  ║  │ seq ║
   ║    pass C    1 consolidation, sees all   ║ ─┘     ║
   ╚═══════════════════════════════════════════════════╝
          │  scene → event assignment
          ▼
   ╔═══════════════════════════════════════════════════╗
   ║  STAGE 3 · event drafts           ~30 agents      ║
   ║  entry state · movement · exit state · SPECULATION║
   ╚═══════════════════════════════════════════════════╝
          │
          ├───────────────────────────┬───────────────────────┐
          ▼                           ▼                       │
   ╔═══════════════════╗      ╔═══════════════════╗           │
   ║ STAGE 4 · plots   ║      ║ STAGE 5 · entities║           │
   ║  draft      1     ║      ║  agents      1    ║           │
   ║  doctors    5  ∥  ║      ║  locations   1  ∥ ║           │
   ║  consolidate 1    ║      ║  objects     1    ║           │
   ║                   ║      ║  other       1    ║           │
   ╚═════════╤═════════╝      ╚═════════╤═════════╝           │
             │                          │                     │
             └────────────┬─────────────┘                     │
                          ▼                                   │
        ══════════ BARRIER 1 ═══════════                       │
        plots and canonical ids must both                      │
        be fixed before any profile is written                 │
                          │                                    │
          ┌───────────────┴───────────────┐                    │
          ▼                               ▼                    │
   ╔═══════════════════╗          ╔═══════════════════╗        │
   ║ STAGE 6 · profiles║          ║ STAGE 7 · root    ║        │
   ║  ~35 × (write →   ║          ║  write → critique ║        │
   ║  critique → revise)║   ∥     ║  → revise    (seq)║        │
   ║  independent across║         ╚═════════╤═════════╝        │
   ║  entities          ║                   ▼                  │
   ║                    ║         ╔═══════════════════╗        │
   ║                    ║         ║ STAGE 8 · exposé  ║        │
   ║                    ║         ║  draft  1         ║        │
   ║                    ║         ║  doctors ~5    ∥  ║        │
   ║                    ║         ║  revise 1         ║        │
   ╚═════════╤══════════╝         ╚═════════╤═════════╝        │
             │                              │                  │
             └──────────────┬───────────────┘                  │
                            ▼                                  │
        ══════════ BARRIER 2 ═══════════                        │
        the entire superstructure must exist                    │
        before the second descent begins                        │
                            │                                   │
                            ▼                                   │
   ╔═══════════════════════════════════════════════════╗        │
   ║  STAGE 9 · event rewrite          ~30 agents      ║◀───────┘
   ║  now sighted on root, exposé, plots, profiles     ║  (scene nodes
   ╚═══════════════════════════════════════════════════╝   and script
                            │                               carried forward
                            ▼                               to both)
   ╔═══════════════════════════════════════════════════╗
   ║  STAGE 10 · scene rewrite        224 agents       ║
   ║  beats · per-beat changes · mental simulation     ║
   ║  · per-beat dramaturgical function                ║
   ╚═══════════════════════════════════════════════════╝
                            │
                            ▼
                    narrative graph
```

---

## 2.4 Which stages are embarrassingly parallel, and which are not

**Genuinely embarrassingly parallel — no agent needs any other agent's output:**

- **Stage 1**, 224 ways. Each agent gets the script and one scene. There is no
  shared mutable state, no ordering constraint, and no communication. This is the
  purest case in the pipeline and it is also the largest, which is the whole
  economic argument.
- **Stage 3**, ~30 ways. Each event agent reads a disjoint set of scene nodes.
  Events do overlap in the entities they touch, but stage 3 is not asked to
  reconcile that — reconciliation is stage 5's job, deliberately.
- **Stage 5**, 4 ways. The four agents partition by entity kind, so their outputs
  are disjoint by construction. They read the same inputs; they write to different
  keys.
- **Stage 9**, ~30 ways, and **stage 10**, 224 ways. Both are pure fan-out over a
  frozen tree.
- **Stage 6 across entities**, ~35 ways. Within one entity the three calls are a
  chain (write → critique → revise); across entities nothing is shared.

**Parallel within a phase, sequential across phases:**

- **Stage 2.** Pass A's 44 windows are independent of each other; pass B's 11 are
  independent of each other; pass C is one call. But B cannot start before A
  finishes and C cannot start before B. Three phases, maximum width 44.
- **Stage 4.** One draft, then five doctors in parallel (one plot each), then one
  consolidation. Three phases, maximum width 5.
- **Stage 8.** Same shape as 4: draft, ~5 single-criterion doctors in parallel, one
  revision. Maximum width 5.

**Strictly sequential:**

- **Stage 7**, three calls in a chain. It is three calls, so this costs nothing.

The distribution is the point. The two stages that dominate token volume — 1 and 10,
together roughly 79% of the estimated output (see §12) — are the two with no
internal ordering at all. The stages with real sequencing are stages 2, 4, 7 and 8,
which together are on the order of 70 calls. **The serialisation is concentrated
where the work is not.**

---

## 2.5 The two barriers

### Barrier 1 — plots and entities before profiles and root

Stages 4 and 5 both depend only on stages 1–3, so they run concurrently. Stages 6
and 7 need both.

A profile has to say which plots its entity serves, which requires the plot list. It
has to be written under a canonical identifier, which requires stage 5's alias
table — otherwise the same character gets two profiles under two names, and the
merge problem moves from the scene layer (where it is cheap, because scene nodes are
small and structured) into the profile layer (where it is not, because two profiles
of one person cannot be merged without deciding which claims survive).

The story root needs both for a weaker reason: it declares the world's rules and the
cast, and a root written against a provisional entity list is the exact failure §1
describes.

This barrier is real in the sense that it cannot be pipelined. Stage 6 cannot start
on the entities that stage 5 has already resolved, because stage 5's four agents
each emit one dictionary at the end of one call — there is no partial output to
consume. That is a design choice and it could be relaxed (four agents emitting
streamed per-entity records would let stage 6 start early), but the gain is small:
stage 5 is 4 calls.

### Barrier 2 — the whole tree before the second descent

Stage 9 is where the design earns the word *descent*. Every agent from here on sees
the complete superstructure, which is the thing stage 1 was denied on purpose.

The barrier is total. A scene rewrite agent needs the root's style rules, the
exposé's act structure, its own event's boundaries and function, the plot its event
serves, and the profiles of everyone in the room. Missing any one of those and it is
back to writing blind, which stage 1 already did better because stage 1 was not
pretending.

The join here is between stage 6 (profiles) and stage 8 (exposé), which ran
concurrently. Stage 6 is the long pole — ~105 calls against stage 8's ~7 — so in
practice barrier 2 is "wait for the profiles".

### What is not a barrier, and why the distinction is worth keeping

Four other edges look like barriers and behave differently:

- **1 → 2.** Pass A's first window needs only scene nodes 1–10. In principle stage 2
  streams behind stage 1 and costs nothing. In practice pass C needs all 224 anyway,
  so the saving is bounded by pass A + pass B, which is small. This is a
  *pipelinable* edge, not a barrier — worth knowing if stage 1 turns out to be
  slower than estimated.
- **2 → 3** and **3 → 4.** These are fan-ins to a single call, not joins of two
  lineages. They stall, but there is nothing to coordinate: one consumer, one
  producer set.
- **9 → 10.** Pure fan-out from a frozen artifact. Stage 10 could in principle start
  on any scene whose event has been rewritten, making this pipelinable too. Since
  stage 9 is ~30 calls against stage 10's 224, the saving is again small.

Calling all of these "barriers" would be technically defensible and operationally
misleading. The two labelled barriers are the two places where **a failure in one
branch stalls an unrelated branch**, which is the property that matters when
something goes wrong at three in the morning.

---

## 2.6 What flows along the edges

Each edge carries a specific contract, and the contracts are as much of the design
as the topology. Stated compactly, with the sections that own them:

| Edge | What crosses it | Owned by |
|---|---|---|
| 0 → 1 | verbatim scene text + full script | §3 |
| 1 → 2 | scene nodes: participants, location, what changes, one-line summary | §3, §4 |
| 2 → 3 | `{event_id: [scene_ids]}` — non-contiguous sets permitted | §4 |
| 3 → 4 | event drafts including free-text plot *speculation* | §5, §6 |
| 3 → 5 | every name any agent used, in context | §5, §7 |
| 4 → 6/7 | plot list, membership, primary-plot assignment | §6 |
| 5 → 6/7 | `{canonical_id: [aliases]}`, applied procedurally to the whole tree | §7 |
| 6/8 → 9 | root, exposé, plots, profiles — frozen | §10 |
| 9 → 10 | final event nodes with boundaries and function | §10 |

Two of these are worth flagging now because they are where the design is least
certain, and both are argued in their own sections rather than here:

- **3 → 4 carries a guess.** Event agents speculate about a plot layer that does not
  exist yet. §5 argues this is necessary rather than sloppy; it is also the edge
  most likely to inject a systematic bias, since thirty agents guessing
  independently may still guess the same wrong thing.
- **5 → everything is a procedural rewrite**, not a negotiation. The alias table is
  applied by code across the scene and event layers. §7 gives the identifier
  standard; it is a heuristic, and a merge that is wrong here is wrong everywhere
  downstream at once.

---

## 2.7 Why the shape is the whole argument

The measured aggregate throughput on this deployment is **2,812.6 tok/s** across
eight A100s at 64 concurrent on schema-constrained JSON, against a single-stream
decode rate an order of magnitude lower (`reports/qwen-local-deployment.md` §8.2 —
measured, 93% of linear scaling across the eight endpoints). That ratio is only
available to a workload that can present 64 independent requests at once.

The top-down pipeline cannot. It is serial by construction: the entity layer needs
the plot layer, the event layer needs the entity layer, and within a layer the
single-emission design produced one call per layer. Adding GPUs to it does close to
nothing.

This design is not faster because the model is faster. It is faster because 690 of
its ~690 calls sit in stages where hundreds of them are simultaneously ready. The
quality argument in §1 and the throughput argument here are the same argument seen
from two sides: **the reason a stage can be parallel is that its agents do not need
each other's answers, and the reason they do not need each other's answers is that
each is reading the source rather than the layer above.**

The estimates that follow from this — ~27 minutes against 28 hours serially — are in
§12, together with the one unverified dependency they rest on (prefix caching across
concurrent slots, measured at 48.9× on time-to-first-token for a *sequential* warm
prefix, and **not yet measured across 64 simultaneous requests**).
