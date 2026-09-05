# Top-Down Generation Plan — From Story Root to Screenplay Prose

*Status: plan, not code. This document describes how to go from the most
abstract layer (story root) down to the most concrete one (scene prose),
using the ~370 existing story trees and their hindsight reasoning traces as
training material. Read the bottom-up pipeline first
(`00-DEFAULT-PIPELINE.md`), then this file.*

---

## 1. Goal in one paragraph

We already know how to go **bottom-up**: screenplay → scenes → events →
meta → entities → plots → root → exposé, plus hindsight reasoning traces
for every step (`reasoning_traces/`). What we do not yet have is the
reverse system: a user hands us a **story root**, and we build everything
below it — step by step, each step with written reasoning — until we reach
individual **scene cards**, and finally write the **scene prose itself**
(the leaves of the tree, i.e. what is screenplay text in the original
films).

The end goal is a model that can write **the next scene** given:

- the whole tree above it (root, exposé, plots, entities, events), plus
- the current scene's card (who is there, entry state, what must change), plus
- the cards of the 2 scenes before and the 2 scenes after it.

That model is trained on (tree + neighbourhood → prose) pairs recovered
from real films. This document explains the order of steps, what reasoning
each step needs, and how we get the training data.

---

## 2. Inventory — what layers already exist

Every layer below already exists bottom-up. The table lists what each
artifact contains and what its hindsight trace explains. Field names are
the real ones.

| # | Layer (artifact) | What it contains | Bottom-up built from | Traces (see `trace_specs.py`) |
|---|---|---|---|---|
| 0 | **Screenplay text** | the raw script; scene boundaries from `scriptforge/screenplay.py` | — (source) | — |
| 1 | **Scenes** `scenes/sc-*.json` | `scene_id, location, time_of_day, present, speaking, summary, what_changes[], objects_that_matter, event_hint, uncertain` + optional `minds[]` (wants / feels / shows / conceals), `connects_back, sets_up, dramatic_function` | scene text only (+ 3 preceding scenes as context); `minds` also sees the film's events | `scene_facts` (~145/film), `scene_minds` (~50/film) |
| 2 | **Events** `events/events.json` | `event_id, scene_ids[], title, summary, action, participants, locations, boundary_reason, state_triples[]` (entry/change/exit per entity per register: physical, positional, knowledge, relational, emotional, status, safety), `turns_on, affects_outside{enables, blocks_or_costs, off_screen_reactor}, carried_uncertainty[]` | scene nodes + scene text; scaffold (roster, change ledger) computed by code | `event_compose` (~31/film), `event_reconcile` (~15/film) |
| 3 | **Meta** `meta/meta.json` | `themes{big_questions[], central_dilemma}`, `external{conflicts[]}`, `internal{internal_conflicts[]}`, `relationships{relationship_arcs[]}`, `perspectives[]` (throughline views on the dilemma). Every item cites `event_id + scene_id` evidence | event digest (`build_digest`) | `meta_section` (4/film), `meta_perspectives` (1/film) |
| 4 | **Entities** `entities/profiles.json` | per entity: `name, type, profile, state_variables, arc, relationships[], plots[], salience` + `evidence[{scene_id, ...}]` | scene material for that entity (via its evidence scenes) | `entity_profile` (~6/film) |
| 5a | **Plots (definitions)** `plots/plots.json → definition` | per plot: `plot_id, spine, agent, goal, resistance, interference, stakes, outcome, screen_time_share, covers_synopsis` — *"what is this thread about"* (~3 sentences each) | central dilemma + big questions + event digest | `plot_identify` (1/film, contains all definitions) |
| 5b | **Plots (chains)** `plots/plots.json → chain` | per plot: ordered `chain[]` of event ids with causal links — *"which events carry this thread, and how does each enable the next"* | plot definition + event digest | `plot_chain` (~4/film) |
| 6 | **Story root** `root/story_root.json` | `logline, premise, genre/audience/tone, dramatic_structure, rules_of_the_world[], identification_value, entity_roster[]` + 76-dim plot embedding (52 genres + 24 dimensions, each with evidence string). Anti-floskel rule: every abstract claim needs a concrete anchor | event digest + meta + entity roster | `root` (1/film) |
| 7 | **Exposé** `expose/expose.json` | `ending_first` (how it ends, told first), `synopsis{s01, s02, …}` (5–10 causal sections), `jacket_copy` (sells without spoiling) | root + event digest + meta + entities | `expose` (1/film) |

Two things to notice:

- **Plots are two objects, not one.** `plot_identify` (the summaries: "there
  is a recruitment plot, a betrayal plot, …") and `plot_chain` (the
  membership lists: "this plot consists of ev-003 → ev-007 → …") are built
  by different calls, have different inputs, and fail in different ways.
  Any top-down plan must keep them separate: summaries come early (they
  steer everything), chains come late (they need events to exist).
- **Meta is the only layer that names the dilemma explicitly**
  (`central_dilemma`, `big_questions`, `perspectives`). Everything above
  scenes and below root either serves it or cites it.

---

## 3. Why the order matters — the lesson from the failure

An earlier version of this project built top-down (root first, everything
below inheriting from it) and failed in a way that was measured, not vague:
the root invented **9 entities where 30 were needed**, so all 22 events
happened at the one location that existed, and the ending placed a
character somewhere her own state model could not hold. Building bottom-up
instead gave **23 locations against 1 and 11 reversals against 0**
(`docs/nodes/expose-node.md`).

The rule that came out of that:

> **Errors flow downhill.** A wrong abstract layer poisons everything below
> it. A wrong concrete layer poisons one place — unless the layers above
> copy it.

So a top-down generator must obey two constraints at the same time:

1. **Start abstract, but commit late.** Each abstract step should open
   possibilities, not close them. Concrete numbers (how many entities, how
   many events, who is where) are decided as late as possible.
2. **Every step is checked against the step above, mechanically where
   possible** (counts, id references, state arithmetic), by a judge model
   where not. Never by the composer judging itself
   (`00-DEFAULT-PIPELINE.md` § Judging).

---

## 4. The ordering question — and the recommended answer

The question asked before this plan was written:

> Should we jump directly from story root to exposé, or write plot
> definitions first, or entities, or the meta layer? Where does the plot
> summary go vs. the concrete plot chains?

**Recommendation: do NOT go root → exposé directly.** Write the meta layer
first, then the plot summaries, then entities, and only then the exposé.

```
root → meta → plot summaries → entities → exposé
       (then: plot chains → events → scenes → prose, see §5)
```

Why, step by step:

1. **`root → meta` first.** The root says *what kind of story this is*
   (genre, audience, premise, rules of the world). The meta layer turns
   that into *what the story is about*: the central dilemma, the big
   questions, the conflicts, the relationship arcs, the perspectives. You
   need the big themes before you can name threads, because a plot is
   defined as **one perspective on the dilemma** — without the dilemma,
   plots are just "things that happen". Meta is also cheap (4 section calls
   + 1 perspectives call) and easy to judge.
2. **`meta → plot summaries (plot_identify)` second.** Given the dilemma
   and the big questions, name the 3–6 threads that each illuminate one
   perspective (spine, agent, goal, resistance, stakes, outcome). Keep this
   to summaries only — no event lists yet, because no events exist. This is
   the layer that decides *how many stories run in parallel and what each
   one wants*, which is exactly the information the entity layer needs.
3. **`plots(summaries) + meta → entities` third.** Now decide *who and what
   exists*: characters, creatures, locations, objects, factions. Each
   entity gets a profile, state variables, an arc sketch, and relationships
   — but only a sketch of the arc, because the events that fill it do not
   exist yet. Doing entities before the exposé matters: the exposé must
   introduce every named entity in context, so the cast has to be fixed
   before the exposé is written.
4. **`root + meta + plots(summaries) + entities → exposé` fourth.** Only
   now tell the story through once (ending first, then synopsis sections,
   then jacket copy). The exposé is a *consistency checkpoint*: if the
   threads, the cast, and the ending cannot be told as one causal story,
   something above is wrong — and it is still cheap to fix. An exposé
   written directly from the root, without meta/plots/entities, is a
   pretty paragraph that later layers quietly contradict (this is exactly
   what the failed top-down run produced).

Then the concrete half (see §5): exposé + plot summaries → plot chains
(once events exist) → events → scenes → prose.

In short: **abstract meaning first (meta), then threads (plot summaries),
then cast (entities), then the story told once (exposé) — and only then
the machinery (chains, events, scenes, prose).**

---

## 5. The full top-down chain

### 5.1 The diagram

Bottom-up (what exists today — screenplay in, tree out):

```
screenplay text
  │  parse (scriptforge) → scenes bound by anchors
  v
SCENES (facts + minds)
  │  segment → scaffold → compose → reconcile → verify
  v
EVENTS (state triples, turns_on, affects_outside)
  │  4 section calls + perspectives, evidence-cited
  v
META (dilemma, questions, conflicts, arcs, perspectives)
  │  scene material per entity
  v
ENTITIES (profiles, arcs, relationships)
  │  identify (summaries) → chain (membership), causal
  v
PLOTS (definitions + chains)
  │  fill from events + meta + roster
  v
ROOT
  │  write from root + events + meta + entities
  v
EXPOSE
```

Top-down (what this plan proposes — root in, prose out):

```
STORY ROOT (given by user: logline, premise, genre, audience,
              rules, identification value, embedding)
  │  T1: expand into dilemma + questions + conflicts + arcs
  v
META (central_dilemma, big_questions, conflicts, arcs, perspectives)
  │  T2: name one thread per perspective (summaries only)
  v
PLOT SUMMARIES (plot_identify: spine/agent/goal/resistance/stakes/outcome)
  │  T3: cast the threads (profiles, state vars, arc sketches)
  v
ENTITIES (profiles + relationships; arcs sketched, not filled)
  │  T4: tell the story once; consistency checkpoint
  v
EXPOSE (ending_first + synopsis s01..sN + jacket_copy)
  │  T5: fix beats — how many events, one question per event,
  │      which plot owns which event
  v
EVENTS (skeleton: scene-count, boundary reasons, turns_on sketches,
          affects_outside sketches; triples NOT yet filled)
  │  T6: assign each event's member events to plots (causal chains)
  v
PLOT CHAINS (plot_chain: event membership per plot, causal spine)
  │  T7: fill state triples per event (entry/change/exit per register),
  │      reconcile prose to triples, verify chain exit(N)=entry(N+1)
  v
EVENTS (filled: state triples + reconciled prose)
  │  T8: cut each event into scenes (who/where/what-changes/minds gating)
  v
SCENES (scene cards: present, summary, what_changes, minds,
          sets_up/connects_back, dramatic_function, uncertain)
  │  T9: write dialogue + action from card + neighbourhood
  v
PROSE (screenplay text, one scene at a time)
```

Read it as: **meaning → threads → cast → story-once → beats →
membership → state → cards → dialogue.** Each arrow is one reasoning
transition (§6).

### 5.2 What each transition produces (object → object)

| Transition | From → To | New information created |
|---|---|---|
| T1 | root → meta | dilemma, questions, conflicts, arcs, perspectives |
| T2 | meta → plot summaries | plot definitions (no chains) |
| T3 | meta + plot summaries → entities | cast, profiles, relationships, arc sketches |
| T4 | root + meta + plots + entities → exposé | ending-first, synopsis sections, jacket copy |
| T5 | exposé + plots + entities → event skeletons | event list, per-event question, owner plot, scene counts |
| T6 | event skeletons + plot summaries → plot chains | per-plot ordered event membership, causal links |
| T7 | event skeletons + scenes-context → filled events | state triples, reconciled prose, verified chain |
| T8 | filled events → scene cards | per-scene frame, changes, minds, edges |
| T9 | scene card + neighbourhood + tree → prose | dialogue + action for one scene |

---

## 6. Reasoning needed per transition

Every transition is **two calls, not one**: first an explicit written
deliberation, then the node conditioned on it (`04-reasoning-transitions.md`).
The deliberation is stored permanently and is a first-class training
artifact. Never use the model's hidden `reasoning_content` — measured at
~18% of an explicit trace, with no theory of mind, trajectory, or craft.

| Transition | Reasoning must cover | Reuse existing hindsight traces? |
|---|---|---|
| T1 root → meta | Which dilemma the premise implies; candidate dilemmas considered and rejected; which conflicts carry it; what evidence (future events) would ground each claim | **Partially.** `meta_section` / `meta_perspectives` traces show how claims are grounded in events — reuse as *grounding* examples, but the direction is reversed (we invent claims that future events must then honour). New forward traces needed. |
| T2 meta → plot summaries | One thread per perspective; agent/goal/resistance per thread; interference between threads (braiding); rejected threads; coverage check (does every big question have a thread?) | **Yes, as shape.** `plot_identify` traces show what a good definition looks like. New forward traces needed for the generative direction. |
| T3 → entities | Who each plot needs; who can be merged; non-person entities (locations, objects) whose state will change; relationships; arc sketches; canonical names | **Yes, as shape.** `entity_profile` traces show grounding discipline ("do not invent"). Forward version adds: *decide the cast*, then justify minimality. |
| T4 → exposé | Ending first (what settles, what it costs, final image); synopsis sections in causal order; every named entity introduced in context; jacket copy without spoilers | **Yes, as shape.** `expose` traces show agreement with layers below. Forward version: *promise* the layers below must keep. |
| T5 → event skeletons | How many events (target ~50 for a feature, scaled by story); one question per event; owner plot per event (exactly one); scene counts per event | No existing trace covers segmentation top-down. New. Smallest, cheapest reasoning. |
| T6 → plot chains | Per plot: which events belong (perspective discipline, no padding); causal enablement event→event *inside this plot*; rejected memberships | **`plot_chain` traces are directly reusable** as supervision for membership discipline — same task, same inputs (plot + event layer), only the event layer is now generated, not recovered. |
| T7 → filled events | Per entity per register: entry/change/exit; pivot (`turns_on`) as a moment, not a summary; `affects_outside` (enables / blocks-or-costs / off-screen-reactor); carried uncertainty | **`event_compose` + `event_reconcile` traces are directly reusable.** This is the same composition task. Keep the reconcile step (rewrite prose from finished triples) — it is what prevents prose/triple drift. |
| T8 → scene cards | Per scene: frame (who/where), `what_changes[]` (real transitions, not restated action), minds gating (only where an exchange exists), `sets_up`/`connects_back` edges, `dramatic_function`, `uncertain` | **`scene_facts` + `scene_minds` traces are directly reusable** — same task (card from event + neighbours), plus the minds gate. |
| T9 card → prose | The final leaf step; see §7. Craft sheet + psychology + specimen apply here (`04-reasoning-transitions.md`: craft, psychology per character, specimen dialogue, dynamics, continuity with citations) | No existing trace writes prose from a card. **New.** This is the training target of §7. |

Summary: **T6, T7, T8 can be supervised by the hindsight traces we already
have** (same task, same shape). **T1–T5 and T9 need new forward reasoning
traces**, collected by running the top-down chain on real roots with a
strong model and keeping the deliberations.

---

## 7. The final step — writing one scene (the training target)

This is the step the whole plan points at. Everything above exists so that
this step has something to stand on.

### 7.1 What the model sees (input)

```
THE TREE ABOVE (budgets: root ~8k chars, exposé ~12k,
  relevant plot chains ~8k, entity profiles of who is present ~8k,
  current + neighbouring events ~15k)
THE CURRENT SCENE CARD (present, entry states, what must change,
  dramatic_function, sets_up / connects_back)
THE NEIGHBOURHOOD (cards of 2 scenes before + 2 scenes after,
  each ~1-2k chars: who, what happens, what changes)
THE RULES (world rules from root; craft sheet; verbatim policy:
  never copy tree wording into dialogue)
```

### 7.2 What the model writes (output)

1. **Reasoning first** (stored, scored): craft (what this scene is for, why
   here, rejected alternatives), psychology per present character
   (perception, appraisal, theory of mind to 3 degrees + where the model of
   the other is wrong, trajectory in ≥2 phases with triggers, intention,
   control/gap), specimen (6–10 dialogue lines at the turning point with
   subtext + the swap test: could two speakers exchange lines unnoticed?),
   continuity (which tree facts are leaned on, by id; which contradictions
   were avoided).
2. **Then the prose**: dialogue + action for this scene only.

### 7.3 The blind rule

The model writing scene N **does not see the prose of any other scene** —
only their cards. It must *decide* what should happen from the card and the
tree, not *describe* prose it has seen. A model that sees the target prose
can justify it effortlessly and learns nothing. (Same rule as the reverse
pipeline's blind deliberation; see README § The two directions.)

### 7.4 Where training pairs come from

For every scene of every finished tree (~145 scenes × ~370 films ≈ 50k
pairs): input = (tree layers above + target card + ±2 neighbour cards)
reconstructed from the stored artifacts, output = (forward reasoning +
original scene prose, or a paraphrase where copyright requires it).
Hold out whole **films**, never individual scenes — otherwise a film's
neighbourhood trains while its target evaluates.

---

## 8. Validation and evaluation (reuse, do not reinvent)

- **Structure: `narrativeforge/validate.py` G1–G26.** Every event has exactly
  one parent plot; every scene exactly one parent event; no arrays in
  patchable regions; declared states agree with the fold
  (`timeline.fold()`). The checker already catches 23/23 injected errors —
  run it after every transition, not just at the end.
- **State chain: `exit(N) = entry(N+1)`.** Enforced by schema/code in T7,
  never by asking. Entity arcs are *assembled* from event triples, not
  re-guessed.
- **Quality: the 3-judge GLM panel** (`tools/glm_panel_judge.py`),
  anonymised, averaged — the one sanctioned instrument
  (`00-DEFAULT-PIPELINE.md` § Judging). Rules: never composer-as-judge;
  panel of 3; one fixed instrument; shared control arm per batch. Gaps
  under ~0.3 are noise.
- **Prose checks:** `check_no_leak.py` (no 8-word runs from source reach
  published files), specimen swap test, flat-trajectory check.
- **Measure through the path that will actually run.** The series Stage 0
  lesson: a parser reporting 45 boundaries standalone meant nothing while
  the builder silently fell back to zero scenes end-to-end. Every number in
  this plan must come from the real chain, not from a component in
  isolation.

---

## 9. Implementation — phases

```
Phase 0  Reconstruct (tree → T9 training pairs). No generation yet:
         build (tree + card + ±2 cards → prose) pairs for all finished
         films. Defines the data contract T9 will be trained on.
Phase 1  T1–T4 (root → meta → plot summaries → entities → exposé).
         One call per unit (one meta section, one entity, one plot at a
         time — never batch; cf. budget dilution, `02-forward-pipeline.md`).
         Validate with panel + shared control.
Phase 2  T5–T6 (event skeletons → plot chains). Supervise T6 with existing
         plot_chain traces.
Phase 3  T7–T8 (filled events → scene cards). Supervise with existing
         event/scene traces. Enforce exit=entry chain + minds gate.
Phase 4  T9 (card → prose). Collect new forward reasoning traces on real
         cards; train the next-scene model; eval blind on held-out films.
Phase 5  Close the loop: generate a full story top-down from a held-out
         root and judge it with the same panel that judges recovered trees.
```

Highest value first: **Phase 0** (bounds the whole project and needs no
model calls), then **T2/T6** (plots are the known weak layer — P1 genuine
causal enablement never exceeded 3.0 in 11 measured arms; if top-down plots
fail, nothing below can succeed).

---

## 10. Open questions (not decisions)

1. One call per entity/event/plot/scene (proven against budget dilution at
   the scene layer) vs. batched upper layers (the known weakness in
   `02-forward-pipeline.md`)? Default: one call per unit until measured.
2. How much tree fits in context for T9? The full event digest (~330k chars
   for a season, ~50k for a film) does not fit — tiered reduction, never
   concatenation (cf. series design doc).
3. Forward trace collection budget: reasoning is ~84% of tokens on
   reference runs (`02-forward-pipeline.md` § Cost). Price T1–T5 + T9
   traces before scaling.
4. Copyright: training pairs store structure by reference (offsets,
   anchors), never prose, unless `--inline-prose` is explicitly opted into.
   Published viewers build with `include_prose=False`.

---

*Next step: implement Phase 0 (pair reconstruction) and return with a
measured count of usable pairs before writing any generator prompts.*
