# Bottom-up narrative reconstruction with an agent swarm

**Status: draft.** This file holds the 1,000-word summary and the full section
plan. Each section is written into `swarm/` as a separate file so that a rate
limit or a crash costs one section, not the document. Sections marked *pending*
have their one-line brief here and no prose yet.

---

## Summary

The system this replaces reconstructs a screenplay top-down: story root first,
then exposé, plots, entities, events, scenes. Four rubric evaluations found the
same failure at the bottom and traced it to the top. A run declared nine entities
where the brief asked for thirty to forty; the event layer then placed all
twenty-two events at the single location that existed, and the story ended with a
character in a place her own state model could not hold. No individual call was
wrong. **A thin superstructure strangles every layer beneath it, silently, while
passing every schema check.**

The inversion is the fix. Nothing above a scene is knowable with confidence
before the scenes are read, and everything above a scene is *derivable* once they
are. So: read the scenes first, blind of any superstructure, and let the higher
layers be induced from what is actually there rather than imposed on it.

**Stage 1 — scene nodes, blind of the tree.** Each scene gets one agent, handed
the complete script and that scene's text, and asked for a scene node with no
knowledge of root, plots or events. All 224 run concurrently. Names will diverge
between agents — one writes `ALICE M.`, another `Alice Miller` — and that is
accepted here and repaired later, because forcing agreement before anyone has
read the work is exactly the imposition being removed.

**Stage 2 — event boundaries by sliding window.** An event is a unit of
happening: a party, an earthquake, a battle, two friends walking, a household
waking up. Scenes 1 and 3 may belong to one party while scene 2 cuts elsewhere,
so boundaries cannot be read off adjacency. A first pass runs windows of ten
scenes at stride five, each window naming which scenes belong to which event in
one or two sentences. A second pass takes those results in windows of
twenty-five at stride twenty and reconciles them. A third pass sees everything —
both rounds, the scene layer, the full script — and fixes the final boundary
list. Windowing is not only for speed: twenty scenes of attention drift less than
two hundred.

**Stage 3 — event drafts, one agent each.** Each event agent receives its fixed
boundaries, its member scene nodes and the script, and writes the event: entities
involved, entry state, how the state moves, exit state, what happens, and — with
the plots not yet defined — a *speculation* about which larger thread it serves.
That speculation is deliberate. It is the raw material stage 4 induces from, and
the agent is told to reason rather than invent.

**Stage 4 — plots induced from the events.** One agent reads every event draft
with its speculations and proposes the plot list: main plot, relationship plot,
antagonist plot, character-growth plot, thematic plots. Every event belongs to at
least one; an event may serve two. Five script doctors then take one plot each,
in parallel, and argue about membership against the script. A final agent
consolidates.

**Stage 5 — entity unification, concurrent with stage 4.** Four agents work in
parallel over the scene layer, event drafts and script: one for *agents* (anyone
who decides — people, animals, robots), one for locations, one for objects, one
for everything else (groups, rules, social and magical concepts). Each returns a
dictionary of canonical identifiers with every alias any earlier agent used, so
the divergence permitted in stage 1 is repaired procedurally rather than
negotiated. The naming standard is a capitalised identity word — `ALICE_MILLER` —
chosen so independent agents converge without coordinating.

**Stages 6–8 — profiles, root, exposé.** Once plots and entities are fixed, one
agent per entity writes a full profile; a critic argues against it with evidence
from the script; the author revises. Concurrently the story root is written and
revised, then the exposé, which is critiqued by four or five doctors each holding
exactly one criterion — outsider comprehensibility, plot coverage, act structure,
readability — and then revised once against all of it.

**Stages 9–10 — the second descent.** Now everything above exists, the events and
then the scenes are rewritten by agents that can finally see the whole tree. Each
scene agent gets one scene, its event, the finished superstructure, and the scene
text, and produces the final node: beats, per-beat state changes, per-character
mental simulation with theory of mind, and for every beat its dramaturgical
function. This is where the depth the earlier pipeline produced by luck becomes
producible on purpose, because the agent knows what the scene is *for*.

**Why this is fast.** Every stage is embarrassingly parallel within itself. The
measured aggregate on eight A100s with one 27B model per GPU is **2,812 tokens
per second** at 64 concurrent requests on schema-constrained JSON. The whole
pipeline is roughly 4.55 million output tokens, which is **about 27 minutes**
against 28 hours if run serially — a 63× speedup that comes from the shape of the
work, not from faster hardware.

**Why it should also be better.** Each of the two measured failure modes is
addressed structurally rather than by instruction. Under-declaration cannot
strangle the lower layers because the lower layers are written first. Attention
drift is bounded because no agent holds more than it can attend to. And the
compression that shrinks second-order material is countered by giving each agent
exactly one thing to do.

**What this does not fix.** A 27B model's tendency to write one sentence where a
paragraph is needed is a capability limit, not a scheduling problem; the
countermeasure is one narrow task per call, and that is a mitigation. Identifier
unification is a real merge problem and the standard is a heuristic, not a
guarantee. And a swarm of small agents produces more places for an error to hide
than a single oracle does — every stage boundary needs its own mechanical check,
or the failures simply move.

---

## Sections

Each is a separate file under `distill/swarm/`. Status is `pending` until written.

| § | File | What it must contain |
|---|---|---|
| 1 | [`01-motivation.md`](swarm/01-motivation.md) | The measured failure that motivates inversion: nine entities, one location, twenty-two events, an impossible ending — and why no single call was wrong. |
| 2 | [`02-architecture.md`](swarm/02-architecture.md) | The full stage graph, what each stage consumes and emits, what runs concurrently with what, and where the two synchronisation barriers are. |
| 3 | [`03-stage1-scenes.md`](swarm/03-stage1-scenes.md) | The blind scene agent: prompt shape, what it sees, the node schema, why it must not see the superstructure, and how divergent naming is tolerated. |
| 4 | [`04-stage2-events.md`](swarm/04-stage2-events.md) | Sliding-window event-boundary induction: window and stride choice, the reconciliation pass, the final consolidation, and how non-adjacent scenes are grouped. |
| 5 | [`05-stage3-event-drafts.md`](swarm/05-stage3-event-drafts.md) | The per-event agent: state in, state out, what "speculate about the plot" means and why it is required rather than forbidden. |
| 6 | [`06-stage4-plots.md`](swarm/06-stage4-plots.md) | Plot induction from event speculations, the parallel doctor panel with one plot each, and consolidation. Membership rules. |
| 7 | [`07-stage5-entities.md`](swarm/07-stage5-entities.md) | The four unification agents, the canonical-identifier standard, the alias dictionary, and the procedural rewrite that applies it across the whole tree. |
| 8 | [`08-stage6-profiles.md`](swarm/08-stage6-profiles.md) | One agent per entity, the critic with its evidence requirement, the revision loop, and the craft criteria the critic applies. |
| 9 | [`09-stage7-root-expose.md`](swarm/09-stage7-root-expose.md) | Story root, then exposé with a panel of single-criterion doctors, then one consolidated revision. Why one criterion per doctor. |
| 10 | [`10-stage8-descent.md`](swarm/10-stage8-descent.md) | The second descent: event rewrite, then scene rewrite with beats, mental simulation and per-beat dramaturgical function. |
| 11 | [`11-checks.md`](swarm/11-checks.md) | The mechanical check at every stage boundary. What is decidable from data and must never reach a model. Presence, ownership, domain membership, coverage. |
| 12 | [`12-throughput.md`](swarm/12-throughput.md) | Concurrency and token estimates per stage, the prefix-cache dependency, and what the numbers assume versus what was measured. |
| 13 | [`13-evaluation.md`](swarm/13-evaluation.md) | How to tell whether this is better: the rubric, the mechanical counters, and the specific comparisons against the top-down arms already on disk. |
| 14 | [`14-risks.md`](swarm/14-risks.md) | Where a swarm is worse than an oracle, what a stage-boundary error costs, and the failure modes this design introduces. |

---

## Throughput, first estimate

From measured numbers: 2,812.6 tok/s aggregate across 8 GPUs at 64 concurrent on
schema-constrained JSON; 45 tok/s single-stream.

| Stage | Units | Output tokens | Wall |
|---|---|---|---|
| 1 · scene nodes | 224 | 1,568,000 | 9.3 min |
| 2 · event boundaries (3 passes) | 56 | 112,500 | 0.7 min |
| 3 · event drafts | ~30 | 180,000 | 1.1 min |
| 4 · plots (draft, panel, final) | 7 | 31,000 | 0.2 min |
| 5 · entity unification | 4 | 24,000 | 0.1 min |
| 6 · profiles + critics + revision | 105 | 350,000 | 2.0 min |
| 7 · root + revision | 3 | 27,000 | 0.2 min |
| 8 · exposé + doctors + revision | 8 | 32,000 | 0.2 min |
| 9 · event rewrite | ~30 | 210,000 | 1.2 min |
| 10 · scene rewrite | 224 | 2,016,000 | 11.9 min |
| **Total** | **~689 calls** | **4,550,500** | **≈ 27 min** |

Serially at 45 tok/s the same work is **28 hours**. The 63× is the shape of the
work, not the hardware.

**One dependency dominates and is not yet verified.** Every stage-1 and stage-10
agent needs the full script in context — roughly 40,000 tokens for a feature. At
64 concurrent that is 2.5 million prefill tokens per stage if nothing is cached.
Prefix caching was measured at **48.9×** on this deployment, and the script is a
byte-identical prefix across all 224 calls, so it should cost once. **If prefix
caching does not hold across concurrent slots, stage 1 and stage 10 each gain
roughly 15 minutes and the total roughly doubles.** That is the first thing to
measure and it is cheap: one stage, one timing.

For 100 screenplays: ~45 hours of 8-GPU wall time, **≈360 GPU-hours** — against
the ~15,000 GPU-hours estimated for the top-down design with a three-round
feedback loop. The difference is almost entirely that the top-down design is
serial by construction and this one is not.

*These are estimates built on measured rates, not a measured run. Treat the
27 minutes as an upper-bound-shaped guess until stage 1 has actually run.*
