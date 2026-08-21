# EXP-003 · The bottom-up swarm, first full run on a 224-scene feature

**Status: refuted, on a cause the design did not anticipate.** The run completed
in 18.4 minutes with 373/373 calls succeeding and produced a valid artifact at
every one of the eight stages. It is nonetheless not an evaluation of bottom-up
reconstruction, because **stage 1 never received a single line of scene text.**
`stage1_scenes` tests `hasattr(scene, "start")` on a dataclass whose fields are
`start_char`/`end_char`, so all 224 scene agents were handed an empty scene and
the first 120,000 characters of a 133,937-character script. The scene layer that
every higher layer was induced from is, by measurement, 7.1% correspondent with
the scenes it claims to describe. n=224 nodes, 33 events, 6 plots, 219 entities,
40 profiles, 1 root, 1 exposé.

The bug is one line. Its consequences are not, and the interesting part of this
entry is what the eight stages did *with* a fabricated substrate — which stages
noticed, which repaired, which laundered it into something that reads well.

---

## Question

The swarm design (`distill/WHITEPAPER-SWARM.md`) claims that inverting the
pipeline — reading scenes first, blind of any superstructure, and inducing the
higher layers from them — structurally prevents the two failures four rubric
passes found in the top-down arm: under-declaration strangling the layers below,
and attention drift across a whole feature.

Does the first full run support that, and is each stage's artifact fit for the
purpose that stage exists to serve?

## Prediction

*No prediction was registered for this evaluation.* The whitepaper's own
pre-registered claims are used instead, since they were written before the run:

| # | Claim, as written in the whitepaper | Outcome |
|---|---|---|
| P1 | ≈27 min wall for all ten stages on 8×A100 | **Supported, and beaten** — 18.4 min for stages 1–8 |
| P2 | ≈4.55M output tokens, of which ≈2.32M for stages 1–8 | **Refuted** — 242,988, 9.6× short |
| P3 | Under-declaration cannot strangle the lower layers, because the lower layers are written first | **Untestable this run** — see §Stage 1 |
| P4 | Divergent naming is safe to permit because stage 5 repairs it procedurally | **Refuted** — the repair splits the antagonist three ways |
| P5 | "Every stage boundary needs its own mechanical check, or the failures simply move" | **Supported, painfully** — every stage had a check; every check verified a property other than the one that failed |
| P6 | A 27B model writing one sentence where a paragraph is needed is a capability limit, mitigated by one narrow task per call | **Mixed** — stage 6 is genuinely deep; stage 7 produced 685 tokens for the whole story root |

P5 is the finding worth keeping. Eight stages ran, all eight checks passed or
reported only trivia, and the run's central defect — that no agent had read the
work — was invisible to all of them.

## Design

Observational, n=1 run. No arms, nothing varied. Five artifacts sampled by hand
per stage, spread across the work rather than taken from the front (stages 7 and
8 have one artifact each and were read whole), plus four whole-population
metrics computed against the script and the scene map, described under §Metrics.
Comparison against the top-down artifacts already on disk at
`reconstruct/runs/matrix/artifacts/`, which cover the same work at the same
layers.

## Materials

| | |
|---|---|
| Code | `distill/swarm.py` — **untracked at time of run**; repo HEAD `3f4e1f8` |
| Design | `distill/WHITEPAPER-SWARM.md` |
| Model | `qwen3.8-27b`, 8 endpoints `127.0.0.1:8100–8107`, 8 concurrent each = 64 |
| Decoding | temperature 0.7, thinking off, schema-constrained JSON |
| Work | The Matrix, 224 scenes, 133,937 chars, `reconstruct/runs/matrix/script.normalized.txt` |
| Outputs | `reconstruct/runs/matrix/swarm/artifacts/`, protocol at `../protocol.json` |
| Log | `reconstruct/runs/swarm_full.log` |
| Baseline | `reconstruct/runs/matrix/artifacts/` (top-down, complete superstructure, 4 of 224 scenes) |

Totals from `protocol.json`: 1,104.6 s, 373 calls, 373 ok, 0 failed,
11,373,846 tokens in, 242,988 out.

## Metrics

Four population metrics were computed over all 224 nodes. Each is decidable from
`script_map.json` and the normalised script, so none of them grades against a
list this apparatus authored.

1. **Evidence-in-own-scene.** Every quoted span of ≥25 characters inside a
   `what_changes[].evidence` field, whitespace-normalised, tested for occurrence
   in (a) the scene's own character range and (b) anywhere in the script. Tests
   whether the node read its scene. Validated by hand on sc-206: the check
   agreed with the reading.
2. **Best-match scene.** Content words of the node's summary and evidence, idf-
   weighted over the 224 scene texts, scored against every scene; the arg-max is
   compared to the node's own id. Exploratory and noisy — a paraphrase can score
   its neighbour higher than itself — so it is reported as a distribution of
   offsets, not as a pass rate.
3. **Present-name grounding.** Each name in `present`, expanded through its
   alias set, tested for occurrence in the scene text. Over-counts: a character
   referred to only as "she" is really present and scores as a miss. Reported
   with that caveat and confirmed by hand on the five worst nodes.
4. **Verbatim leakage.** 8-gram overlap between generated prose and the script.

Stage-level artifacts were also re-checked against the pipeline's own checkers,
run at a different point in the sequence than the pipeline runs them.

---

## Stage 1 — scene nodes, blind of the tree

### Does it do its job?

No. It did not do a shallow version of its job; it did a different job.

`stage1_scenes` builds the scene text as

```python
text = script[scene.start:scene.end] if hasattr(scene, "start") else ""
```

`scriptforge.screenplay.Scene` declares `start_char` and `end_char`. There is no
`start`. `hasattr` returns False for all 224 scenes, the `THE SCENE` block of
every prompt was empty, and the guard that was meant to be defensive silently
selected the empty branch and reported nothing. Verified directly against the
parser.

The second half compounds it: the prompt appends `script[:120000]` of a
133,937-character file. **Scenes sc-183 to sc-224 — 42 scenes, the entire third
act — were not present anywhere in any stage-1 context window.** Nodes were
produced for all 42 anyway.

### What the measurements say

| Metric | Result |
|---|---|
| Quoted evidence spans ≥25 chars | 193 across 224 nodes |
| …found in the scene they are attributed to | **10 (5.2%)** |
| …found somewhere in the script | 126 (65.3%) |
| Nodes with ≥2 quoted spans and none in their own scene | 45 |
| Nodes whose text best matches their own scene (idf) | 16/224 (7.1%) |
| …restricted to sc-001–182 (script in context) | 8.8%, n=182 |
| …restricted to sc-183–224 (beyond the 120k cut) | **0.0%, n=42** |
| `present` names not findable in their own scene | 425/675 (63.0%), over-counted |

The offset distribution of metric 2 is not flat. Modes sit at +5 and +6 (60
nodes) with a strong positive bias — 129 nodes best-match a *later* scene, 79 an
earlier one. That is the signature of an agent trying to locate "scene 118" by
counting slug lines in a wall of script and landing a few headings past it.

### The failure, in three artifacts

- **sc-072.** Script, in full: the ship is quiet and [...] —
  11 words. The node returns a 400-character summary of the mess-hall breakfast,
  seven characters present, and two state changes with quoted dialogue.
- **sc-197.** Script: Neo springs up the apartment stairs — 14 words. The node
  returns *the same breakfast scene*, near-verbatim to sc-072's.
- **sc-206.** Script: Neo kicks in a third-floor window and the door numbers
  count backwards, 310, 309 — 23 words, no speakers, and 6,800 characters past
  the truncation point. The node returns the film's opening hotel raid: Trinity
  at a computer, the BIG COP entering with armed officers, a gunfight, three
  state changes and quoted evidence. None of it is in the scene. **This is the
  famous-film confound, caught in the act**, and it is the cleanest instance
  because the model had no text at all and produced a confident, schema-valid,
  internally consistent node anyway.

### On the 22 recorded violations

Confirmed as real, and a symptom — but the important point is how badly they
undercount. `check_stage1` tests three things: that a node exists, that
`what_changes` is non-empty, and that each change's `who` appears in `present`.
All three are *internal* consistency. Nothing in the check compares a node to its
scene, so a node that describes a different scene entirely, coherently, passes.
Of the 22, one is a no-op change and 21 are `who`-not-in-`present`, most of them
collective nouns the schema permits (`Crew`, `Group`, `Narrative Flow`,
`LOBBY`). Meanwhile 45 nodes quote evidence that does not exist in the scene
they are attributed to, and not one of those is in the violation list.

The underlying node quality is genuinely decent *as prose about The Matrix* —
mean summary 413 characters, mean 1.72 changes, axes used sensibly, evidence
fields carrying real dialogue. It is worthless as a scene layer.

### What would fix it

1. `script[scene.start_char:scene.end_char]`, and delete the `hasattr` guard.
   A guard that silently substitutes empty input for missing input is worse than
   a crash; if the attribute may be absent, `getattr(scene, "start_char")` should
   raise.
2. Assert non-empty scene text before dispatch, and fail the run rather than the
   call.
3. Never truncate the script by character count. `script[:120000]` deleted act 3
   and left no trace in `protocol.json`. If the script exceeds the context
   budget, that is a fact the protocol must record.
4. **Add a correspondence check to the stage-1 boundary.** For each node,
   require that at least one quoted evidence span of ≥25 characters occurs in the
   scene's own character range, and that at least one `present` name occurs in
   the scene text or in `script_map`'s speaker cues for that scene. Both are
   arithmetic over data on disk. On this run the first clause alone rejects 45
   nodes and every one of the fabrications above.

---

## Stage 2 — event boundaries by sliding window

### Does it do its job?

Mechanically, yes — and better than the design feared. Structurally, no, and the
reason is not the one the design was worried about.

33 events over 224 scenes. `repair_coverage` reported **zero** problems: pass C
emitted 224 scene ids, each exactly once, no duplicates, no omissions, no
`UNASSIGNED` bucket. A single call partitioning 224 items without arithmetic
error is a real result and should be recorded as one.

### The known architectural weak point: confirmed, but not as predicted

The design flagged pass C — one call, total authority over the final boundaries,
no verification above it, input kept deliberately small — as the weakest joint.
**It is not the failure here. Pass C did its job faithfully.**

The evidence: 14 of 33 events span more than 50 scenes, and the extremes are
absurd — ev-002 runs from scene 2 to scene 220, ev-003 from 12 to 221, ev-008
from 21 to 224. That looks like pass C gluing unrelated material together. It is
not. All 42 act-3 scenes were scattered across 11 earlier events, and they went
where their *nodes* said they belonged: sc-206's node describes the opening hotel
raid, and pass C placed sc-206 in ev-002, "The Hotel Raid and Escape". sc-183's
node describes the déjà-vu cats, and pass C placed it in ev-026, "The Hotel
Lafayette Ambush". sc-197's node describes the mess-hall breakfast, and pass C
placed it in ev-022, "Mission Briefing and Departure".

Pass C grouped a hallucinated scene layer correctly. The consequence is that
**the third act of this film has no event.** Not a badly-cut one — none. Neo's
death, the resurrection, the fight with Smith, the closing call: all 42 scenes
were absorbed as strays into events describing act 1.

The real weakness at this joint is the one that follows: pass C's authority is
unverifiable *upward*. It had no way to say "these nodes cannot all be the hotel
raid", and nothing above it could either, because the only property checked was
coverage — the property pass C was explicitly instructed to satisfy. A check that
verifies the instruction the model was given measures compliance, which is the
error EXP-002 recorded and the design says it has learned.

### What else fails

- **ev-026 holds 36 scenes**, of which 84–116 are contiguous: the walk to the
  Lafayette, the ambush, Mouse's death, the bathroom fight, Morpheus's sacrifice
  — five or six distinct happenings in one "event". `check_stage2` flags an
  event holding more than `max(6, len(nodes) // 6)` scenes. For 224 scenes that
  threshold is 37. The under-cut missed detection **by one scene.**
- **Passes A and B are not persisted.** 55 of the stage's 56 calls leave no
  artifact, so the stage cannot be audited, diffed, or re-run from its midpoint.
- 11 of 33 events are contiguous; the design correctly permits non-adjacency for
  cross-cuts, so non-contiguity alone is not evidence of anything.

### What would fix it

1. Save `2a-windows` and `2b-reconcile` output to `artifacts/boundaries_a.json`
   and `_b.json`. One `save()` call each.
2. Lower the oversize threshold to something a 224-scene work can trip:
   `max(8, len(nodes) // 12)` is 18 here, and would have caught ev-026.
3. Add a **span check** alongside the size check: flag any event whose scene
   indices span more than, say, 8× its member count. On this run that fires on
   all 14 wide events and is the only signal in the whole pipeline that would
   have surfaced the stage-1 damage before stage 8.

---

## Stage 3 — event drafts

### Does it do its job?

Yes, and it is the second-best stage in the run — which is itself the most
uncomfortable finding in this entry.

Mean `what_happens` 631 characters, mean 3.0 state changes with before/after and
a `why_it_matters`, 68 plot speculations across 33 events, every one carrying
evidence. The content is largely *correct about the film*. ev-024 records that
the Oracle tells Neo he is **not** the One — the detail popular summary gets
wrong, and the pipeline's own exposé later gets wrong. ev-029 correctly has
Cypher kill Dozer and *wound* Tank. ev-016 tracks Morpheus's glasses being
knocked off as a state change with a dramaturgical reading.

**But the quality is not coming from the scene layer.** Each stage-3 prompt
appends `script[:100000]`. The agent has the raw text and uses it; the scene
nodes are the least reliable thing in its context and it appears to have leaned
on them least. Stage 3 therefore *masked* the stage-1 damage rather than
propagating it, and the bottom-up premise — that higher layers are better when
induced from a read scene layer — **is not tested by this run at all.** Stages 3,
6 and 7 all receive the raw script; the only stage whose quality is genuinely
downstream of the scene nodes is stage 2, and that one failed.

### The 48 violations: refuted as stated

They are not what the protocol makes them look like. Recomputing the same check
against the artifacts *after* `apply_aliases` runs:

| | Count |
|---|---|
| `participant … in none of its scenes`, as recorded at check time | 48 |
| Same check, recomputed post-alias | **7** |

41 of 48 were name divergence — `Trinity` against `TRINITY`, `Agent Smith`
against `AGENT_SMITH` — which is *exactly what stage 1 is licensed to produce and
stage 5 exists to repair.* `check_stage3` runs at stage 3; `apply_aliases` runs
after stages 4 and 5. **The check is ordered before the repair it is checking.**
The largest violation count in the run is 85% an artifact of check ordering.

The 7 that survive are real and are inherited from stage 1's fabricated `present`
lists.

### What actually fails at stage 3

- **The confidence scale is uncontrolled.** The schema declares
  `"confidence": {"type": "integer"}` with no bounds and no description. 16 of 33
  events answered on 0–10 (`9`, `8`, `5`, `4`); 17 answered on 0–100 (`95`, `90`,
  `85`). Stage 4 reads both side by side and cannot tell a `9` from a `90`.
- **Duplicate participants after aliasing.** ev-032 lists `THE_AGENTS` three
  times, because Smith, Brown and Jones were rewritten to one id and nothing
  dedups the list. 11 duplicate entries across the stage.
- **Multi-entity `who` fields.** ev-029 has `"who": "Trinity, Neo, Apoc, Switch"`
  and `"who": "Trinity, Neo"` in its state blocks. These match no entity id and
  are invisible to stage 6's `c.get("who") == eid` filter, so those state changes
  are silently dropped from every profile.

### What would fix it

1. Move the participant check to after `apply_aliases`. 48 → 7, and all 7 real.
2. `"confidence": {"type": "integer", "minimum": 0, "maximum": 100}` with a
   description naming the scale.
3. Dedup every rewritten list inside `apply_aliases` — one `dict.fromkeys` call.
4. Make `who` a single-entity field the schema can enforce once entities exist;
   until then, reject `who` values containing `,` or ` and ` at the check.

---

## Stage 4 — plots induced from the speculations

### Does it do its job?

Partly. Six plots, not three — the smoke-test count does not replicate, and the
concern is **refuted**. Six is a defensible number for this work: a main line, a
character line, a relationship line, an antagonist line, a thematic line.

### What is good

The induction genuinely used the speculations. p-002, "Cypher's Arc of
Disillusionment and Betrayal", cites its member events inline — *"It begins with
his skepticism (ev-001, ev-018), moves to his secret contact with Agent Smith
(ev-009, ev-022)"* — which is a thread argued from evidence rather than named
from memory. Sixteen of 33 events sit in exactly one thread; the rest in two, as
the design permits.

### What fails

- **Two plots are `kind: "main"`.** p-001 "Neo's Awakening and Journey to the
  One" and p-003 "The Resistance's Struggle and Morpheus's Faith". The schema
  enum allows any number; JSON Schema cannot express "at most one".
- **ev-033 belongs to no thread**, and the check says so and nothing acts. The
  cause is traceable: p-003's doctor recommended removing ev-002, ev-011 and
  ev-033, the consolidator applied the removals and did not honour the coverage
  invariant, and `check_stage4` *reports* the orphan where stage 2's
  `repair_coverage` would have *fixed* it. The pipeline has the right mechanism
  one stage earlier and does not reuse it.
- **The doctor panel carries no information.** All six doctors returned
  `needs_members_moved`. None returned `sound`; none returned `should_dissolve`.
  Six parallel calls that all produce the middle verdict are six calls that did
  not discriminate. Their prose is good — p-006's doctor correctly calls the
  thematic thread *"a hodgepodge of distinct philosophical concepts that do not
  form a single coherent arc"* — but the verdict field is dead.
- **A factual regression from its own source.** p-002 says Cypher kills *"Dozer
  and Tank"*. Its own ev-029, which the plot agent was shown, says Tank is
  wounded and survives to shoot Cypher. The plot layer is less accurate than the
  event layer it was induced from.
- **The relationship plot has two events and stops in act 2.** p-004, "Neo and
  Trinity's Bond", contains ev-004 and ev-018 and nothing else, because the
  resolution of that thread — Trinity's declaration, the kiss, the resurrection
  — is in the 42 scenes that never became an event. The plot layer cannot
  represent an ending that the event layer does not contain.

Every plot description here could have been written from a one-paragraph summary
of the film. That is weak evidence on its own, since plot descriptions are
generic by nature, and the inline event citations argue against it. But the
layer contains nothing draft-specific whatsoever.

### What would fix it

1. After consolidation, in code: demote all but the first `main` to `subplot`,
   and append any event in no thread to a named `UNPLACED` thread rather than
   letting it vanish. Both are the `repair_coverage` pattern, applied one stage
   later.
2. Give the doctor a verdict it can only reach with evidence: replace the
   three-way enum with a required `events_to_remove` / `events_to_add` pair plus
   a per-event one-line justification, and let `sound` be the case where both
   are empty. A verdict that costs nothing to give will always be given.

---

## Stage 5 — entity unification

### Does it do its job?

No. This is the stage the design leans on hardest — it is what makes stage 1's
permitted naming chaos safe — and it is the stage that fails most consequentially.

219 entities: 30 agents, 16 locations, 159 objects, 14 concepts.
`check_stage5` reported **zero violations.**

### What is good, and it is real

Salience is honest. 153 of 159 objects are tagged `minor`, so the object flood is
self-limiting rather than unmanaged, and only 49 entities are eligible for
profiling. The lists are draft-specific, not film-specific: `PRIESTESS`,
`SPOON_BOY`, `BLIND_MAN`, `META_CORTECHS` (the film's spelling is MetaCortex).
This layer read the script.

### What fails

**The antagonist has two canonical identifiers in the same artifact.** The
concepts agent produced `THE_AGENTS` with `Agent Smith`, `Agent Brown` and
`Agent Jones` among its aliases. The agents agent produced `AGENT_SMITH`,
`AGENT_BROWN`, `AGENT_JONES` separately. Both survive. `alias_map` is a flat
`dict` built by iterating the four lists in order, so an alias string present in
two entities is decided by whichever is written last — and matching is
exact-string and case-sensitive. Result:

| Alias string, lowercased | Canonicals it maps to |
|---|---|
| `agent smith` | `THE_AGENTS`, `AGENT_SMITH` |
| `agent brown` | `THE_AGENTS`, `AGENT_BROWN` |
| `agent jones` | `THE_AGENTS`, `AGENT_JONES` |
| `police officers` | `POLICE_OFFICERS`, `POLICE` |
| `sentinel` | `SENTINEL`, `SENTINELS` |
| `heart o' the city hotel` | `HEART_O_CITY_HOTEL`, `HEART_O_THE_CITY_HOTEL` |
| …9 more | |

**14 alias strings resolve to a different entity depending on capitalisation.**
In the finished scenes.json, sc-003 has `AGENT_SMITH` present and sc-167 has
`THE_AGENTS` — the same character, two ids, one artifact. `POLICE` also absorbed
`Agents (standing)`, so an Agent is aliased to the police.

**The code-level precedence guard was defeated by one character.** The comment
above it is explicit: *"Asking each agent to stay in its lane is an instruction;
enforcing it is arithmetic."* The arithmetic dedups on the exact id string. The
agents agent emitted `CYpher` — malformed against its own stated standard — and
the objects agent emitted `CYPHER`. Different strings, so both survived, and
both later received a full profile with contradictory state variables.

Seven near-duplicate ids survive across the four lists once case, plurals and a
leading `THE_` are normalised: `CYpher`/`CYPHER`, `SENTINEL`/`SENTINELS`,
`CONSTRUCT`/`THE_CONSTRUCT`, `ORACLE_S_APARTMENT`/`ORACLES_APARTMENT`,
`DRIVE_CHAIR`/`DRIVE_CHAIRS`, `NEEDLE`/`NEEDLES`, `MACHINES`/`THE_MACHINES`.

**Locations are misfiled as objects.** `MAIN_DECK`, `MESS_HALL`, `INFIRMARY`,
`DOJO`, `ROOFTOP`, `STAIRWELL`, `BASEMENT`, `FIRE_ESCAPE` all sit in the objects
list. Precedence cannot help — they have no competing id in the locations list.

**The over-merge destroys distinctions the story turns on.** `HOTEL_LAFAYETTE`
absorbs Room 1313, Room 808 and Room 608; `HEART_O_CITY_HOTEL` absorbs Room 303;
`BODIES` absorbs *"Morpheus's body"* — a living captive — along with three
corpses; `MOUSE_COMPUTER` is the canonical id for every generic computer in the
script, which reads as belonging to the character Mouse.

**And the check saw none of it,** because `check_stage5` tests for
under-declaration (`total < 15`), fewer than two locations, no concepts, and
exact-id duplicates. All four pass while the antagonist is split three ways. This
is P5 in its purest form.

### Compared to the top-down arm

Worse. `reconstruct/runs/matrix/artifacts/entities.json` has 36 entities with
typed ids (`ch-01`, `lo-01`, `gr-01`), an alias list, a salience, plot
membership, and a sentence-addressable profile keyed `b01`/`b02` — the patchable
structure the project brief requires. The swarm's entity layer is larger, flatter
and internally inconsistent. The whitepaper's motivating "nine entities" failure
is against an older run; the top-down artifact currently on disk does not exhibit
it.

### What would fix it

1. **Canonicalise in code before building the map.** Uppercase, strip
   non-alphanumerics, drop a leading `THE_`, singularise; dedup on that normal
   form with the existing agents > locations > objects > concepts precedence.
   Fixes `CYpher`/`CYPHER`, the three Agents, `SENTINEL`/`SENTINELS` and the rest
   in one pass.
2. **Build the alias map case-insensitively, and make a collision fatal** rather
   than last-write-wins: if two entities claim the same normalised alias and
   resolve to different canonicals, that is a merge conflict and must be raised,
   not silently decided by dict ordering.
3. **Dedup lists after rewriting** — removes `THE_AGENTS` ×3.
4. **Add an over-merge check**: flag any entity whose alias set contains two
   strings that the *agents* list also holds as separate ids. `THE_AGENTS`
   holding `Agent Smith` while `AGENT_SMITH` exists is decidable arithmetic.

---

## Stage 6 — entity profiles

### Does it do its job?

Yes — this is the best stage in the run, and the only one that would survive as
written. 40 profiles, mean 2.8 state variables, mean description 564 characters,
zero check violations, and the violations checked (variable count, initial value
inside its own declared domain) are the right ones.

### What is good

`AGENT_SMITH`'s state model is exactly what the design asks for: variables with a
closed domain and a `why` that names the transitions.

```
target_status: [active_hunt, target_escaped, target_captured, target_interrogated]
  why: "Moves from active_hunt to target_escaped after Trinity survives the
        garbage truck crash; moves to target_captured when Neo is arrested…"
```

`TRINITY`'s six variables each cite a real event id — `pilot_capability` moves in
ev-032, `knowledge_of_cypher` in ev-029. `CYpher`'s profile earns its length:
*"his betrayal is not born of malice but of a profound exhaustion with the
truth"* is a reading, not a summary. Nothing here is generic-character filler.

### What fails

- **Three of the 40 profiles are duplicates of another profile.** `CYpher`
  (agent) and `CYPHER` (object) are the same person with two different, mutually
  inconsistent state models. `ORACLE_S_APARTMENT` (location) and
  `ORACLES_APARTMENT` (object) are the same room. `META_CORTECHS_OFFICE` and
  `META_CORTECHS` likewise. 7.5% of the profile budget spent contradicting
  itself, inherited whole from stage 5.
- **The cap truncates the last kind, always.** `stage6_profiles` flattens
  `agents + locations + objects + concepts` and takes `[:40]`. 49 entities were
  eligible. The nine dropped are all at the tail: `THE_CONSTRUCT`,
  `HEART_O_CITY_HOTEL`, `ORACLE_APARTMENT`, `SENTINELS`, `DRIVE_CHAIRS`,
  **`RULES_OF_THE_MATRIX`**, **`POLICE`**, **`ELECTROMAGNETIC_PULSE`**,
  `FETUS_FIELDS`. The world-mechanics concepts — the ones the design says exist
  so that world state can be tracked at all — are precisely what a fixed cap on a
  kind-ordered list eats. A cap of 49 would have cost 9 more calls out of 373.
- **One schema is applied to four kinds of thing.** `wants`, `fears`,
  `internal_conflict` and `speech` are asked of every entity, so the
  Nebuchadnezzar has fears (*"being detected by Sentinels"*) and a speech style
  (*"None (non-living entity), but characterized by the hum of turbines"*), and
  THE_MATRIX has an internal conflict. Some of it is unexpectedly good; the
  `speech` field for a hovercraft is pure schema-satisfaction.
- **`TRINITY`'s description is 111 characters** against a `minLength` of 100 —
  *"A skilled fighter and pilot on the Nebuchadnezzar who falls in love with Neo
  and is instrumental in his journey."* The second lead received the thinnest
  description of any major character, and that sentence is the received summary
  of the film with nothing in it from these scenes. `NEO`'s is 750 characters.
  A `minLength` floor sets a floor; it does not distribute effort.
- **`CYPHER`'s `why` fields are bare event-id lists** — `"ev-009, ev-021,
  ev-022, ev-029"` — which satisfies the schema description ("Which event moves
  this") while carrying no information about the transition.
- **The critic and the revision are not implemented.** The whitepaper specifies
  105 calls for this stage: one author, one critic arguing with evidence, one
  revision per entity. The implementation makes 40 calls, one per entity, and
  stops. The stage's own quality mechanism did not run.

---

## Stage 7 — story root, written last

### Does it do its job?

Barely. One call, 685 output tokens for the entire root of a feature. The
whitepaper specifies root **plus revision**; the revision is not implemented.

### What is good

Writing it last visibly helped in one place. `genre` is *"Philosophical cyberpunk
action-thriller blending existentialist sci-fi with martial arts combat and noir
detective elements"* — specific, multi-clause, and not one word, which is what
the schema and the top-down failure both demanded.

### What fails

- **The turning points are out of story order and omit the climax.** Three are
  listed: the Red Pill Choice, Cypher's Betrayal, the Oracle's Prophecy. The
  Oracle precedes the betrayal in the work. There is no act-3 turn at all, for
  the same reason as everywhere else. `turning_points[].where` is a free string,
  so nothing can be ordered and nothing can be checked.
- **`style` describes the film, not the screenplay.** *"A sleek, high-contrast
  visual aesthetic characterized by cool green digital overlays and stark,
  desaturated environments."* The green has textual basis — the script has
  green-electric rivers and electric-green equipment — but "high-contrast",
  "desaturated" and "visual aesthetic" are the vocabulary of someone describing
  the 1999 release, not the vocabulary of someone who read 133,937 characters of
  action and dialogue. Suggestive rather than conclusive.
- **`pitch` opens "A disgraced hacker named Neo"** — Neo is not disgraced
  anywhere in the text.
- Two audiences, both the obvious ones. Four themes, all the received ones.

### Compared to the top-down arm

Worse, and structurally so. `story_root.json` from the top-down run carries
`logline`, `premise`, `genre_primary`/`genre_secondary`, `setting`, `pov`,
`plot_embedding`, `constraints`, `keep_in_mind`, and a nine-value
`state_dimensions` vocabulary (physiological, emotional, epistemic,
psychological, social, material, spatial, technological, world) that the layers
below can bind state variables to. The swarm root has no such vocabulary, which
is why stage 6's state variables are ad-hoc per entity and cannot be compared
across the cast.

---

## Stage 8 — exposé and its doctors

### Does it do its job?

No. It produces a readable 614-word synopsis that **stops before the story
ends**, and contradicts the pipeline's own event layer on the single most
important beat in it.

### What is good

The doctor panel is the best-executed mechanism in the run. Five single-criterion
doctors, mean score 2.4/5, each specific and each correct:

- readability (2/5) caught the tonal break where the synopsis stops narrating and
  starts analysing: *"a direct, analytical statement about audience perception"*;
- structure (3/5) caught that Cypher's betrayal is placed before the Hotel
  Lafayette ambush against the event list's own ordering;
- identification (2/5) caught that the synopsis *"relies on abstract, expository
  labels ('quiet intensity,' 'hidden potential,' 'underdog') rather than showing
  specific, relatable behaviors"*.

Verbatim leakage is nil: **0 of 616 8-grams** in the exposé occur in the script,
and 73 of 19,745 (0.37%) across all 40 profiles, those being quoted dialogue in
evidence fields where quotation is the point.

### What fails

- **The synopsis ends at the rescue of Morpheus.** No death in room 303, no
  resurrection, no Smith, no closing call. The final sentence is *"As he rescues
  Morpheus, the weight of his destiny settles upon him, marking the end of his
  ignorance and the beginning of his true role."* A synopsis that omits the
  climax and the resolution has not described the work.
- **No doctor noticed.** Not the structure doctor, not the plot-coverage doctor.
  None of the five criteria is completeness, and the event digest they were shown
  also ends there, so the panel could not see the hole from inside. A panel of
  single-criterion doctors is exactly as complete as its list of criteria.
- **It contradicts its own event layer.** The exposé says of the Oracle *"She
  confirms Neo's destiny"*. The pipeline's own ev-024 says she *"confirms he is
  not the One but possesses the gift"*, which is what the script says. The
  received version of the scene overrode the correct record the pipeline had
  already produced and put in the prompt.
- **A fabrication:** *"Dozer, the ship's cook"*. The string `cook` does not occur
  in the script except inside `cookie`.
- **The revision ignored the note it was given.** The readability doctor asked
  for the analytical commentary to be removed; the final text still contains
  *"his disorientation and fear of the unknown make him relatable, mirroring the
  audience's initial confusion"* — which is `root.identification.vulnerable`,
  copied out of the root and pasted into narrative prose.
- **`word_count` is self-reported and wrong.** Declared 468; actual 614, a 31%
  error on a number that is one `len(text.split())` away.

### Compared to the top-down arm

**Clearly worse, and the mechanism is identifiable.** The top-down `expose.json`
carries `ending_first` as a required field — the ending written before anything
else — plus `jacket_copy`, `plot_summary_short`, `plot_summary_long`, and a
28-sentence synopsis keyed `s01`…`s28` so individual sentences are addressable.
Its synopsis runs through the subway fight, room 303, Trinity's kiss, the EMP and
the closing phone call. Same model family, same work, same layer. The only
structural difference is that one schema required the ending up front and the
other did not.

---

## The famous-film confound

Nothing in this design detects a model reproducing a received summary instead of
reading the work. The question was whether that happened. It did, and the run
happens to be a near-perfect natural experiment for it, because 42 scenes had
*no* textual evidence available in any context window.

**Positive detections, in descending order of strength:**

1. **The 42 act-3 nodes.** Zero of 42 correspond to their own scene. sc-206's
   node reproduces the film's opening — Trinity, the BIG COP, the gunfight — with
   quoted dialogue as `evidence`, from a 23-word scene about a man kicking in a
   window. With nothing to read, the agent wrote what it remembered, at full
   confidence, in valid schema, with no `uncertain` entries.
2. **The Oracle contradiction at stage 8.** The pipeline's event layer had the
   scene right and the exposé overwrote it with the popular version. This is the
   strongest evidence that recall competes with, and can beat, evidence already
   in the prompt.
3. **TRINITY's profile description.** One received sentence where every other
   major got a paragraph of reading.
4. **The root's `style` field**, describing the release print.

**Counter-evidence, and it is substantial:** the entity layer is unmistakably
reading *this draft*. `PRIESTESS`, `SPOON_BOY`, `BLIND_MAN`, Room 1313, and
`META_CORTECHS` — the draft's spelling, not the film's MetaCortex. Stage 3's
event drafts get details right that received summary gets wrong. So the model is
not simply reciting.

**The finding is sharper than "it recites".** The pipeline substitutes received
knowledge *precisely where its evidence is absent*, produces it in the same
register and the same schema as its grounded output, marks nothing as uncertain,
and no stage boundary can tell the two apart. A design whose central premise is
"read the scenes first" has no defence against an agent that did not.

The cheap canary: run one stage-1 agent with the scene text deliberately blanked
and measure what it still produces. Anything it writes is recall. On this run
that test costs one call and would have caught the bug before scene two.

---

## What does not follow

- **Not that bottom-up reconstruction is refuted.** It was not run. Stage 1 read
  nothing, so P3 — that writing the lower layers first prevents a thin
  superstructure from strangling them — is untested. The stage-2 failure is
  downstream of the bug, not of the inversion.
- **Not that the higher stages are as good as they look.** Stages 3, 6 and 7 all
  receive the raw script directly. Their quality is evidence that a 27B model
  reads a screenplay well, not evidence that induction from a scene layer works.
  Stage 2 is the only stage whose input is purely the scene layer, and it is the
  one that failed.
- **Not that the swarm is faster than estimated in any useful sense.** 18.4
  minutes against ≈17 minutes estimated for stages 1–8 is a wash, and the output
  volume is 9.6× below estimate because stage 1 had nothing to describe. The
  throughput claim is unmeasured until the run is repeated with scene text.
- **Not that the doctor panels are working.** Stage 8's panel is good and
  incomplete; stage 4's panel returned the same verdict six times. Two panels,
  two different failure modes, n=1 each.
- **Not that the top-down arm is better overall.** It is better at entities,
  plots, root and exposé, and it has 4 scene nodes to the swarm's 224. The
  comparison is only meaningful layer by layer, and it is only stated here for
  the superstructure layers where both arms are complete.

## Threats to validity

- **n=1 run, no repeats, temperature 0.7.** Every count in this entry is a
  single sample. Which specific scene a hallucinating agent lands on is certainly
  variance; that it hallucinates is not.
- **The central finding is a code bug, which makes every stage-level judgement
  conditional.** Stages 2 through 8 are being marked on their handling of
  degraded input. A rerun with scene text may move any of them in either
  direction. The stage-5 alias defects and the stage-4/7/8 schema defects are the
  exceptions — none of them depends on stage 1.
- **Metric 2 (best-match scene) is noisy and was not independently validated.**
  Adjacent scenes in a cross-cut share vocabulary, so an offset of ±1 or ±2 means
  little. The +5/+6 mode and the 0/42 result for act 3 are outside that noise.
  Metric 3 over-counts and is stated as an upper bound.
- **Metric 1 measures only quoted spans of ≥25 characters.** 193 spans across 224
  nodes: many nodes contribute none, so it is a sample of the population, not a
  census.
- **The comparison arm is not matched.** The top-down artifacts were produced by
  a different pipeline, possibly a different model, at an unrecorded date, and
  cover 4 of 224 scenes. Superstructure comparisons are fair; anything below is
  not.
- **`distill/swarm.py` was untracked when the run executed.** The exact code that
  produced these artifacts is reconstructible only from the working tree.
- **The evaluator wrote the metrics and read the samples.** No independent rubric
  pass has scored these artifacts.

---

## Improvements, cheapest first

Each names the stage and the mechanism. Everything above the line is code, not
prompt; the project has already measured that instructions repair local fields
and fail on global consistency.

| # | Stage | Fix | Mechanism | Cost |
|---|---|---|---|---|
| 1 | 1 | `script[scene.start_char:scene.end_char]`; delete the `hasattr` guard; assert non-empty before dispatch | Attribute name. A guard that silently substitutes empty input for missing input must be a crash | one line |
| 2 | all | Stop truncating the script by character count. If it exceeds budget, record the truncation in `protocol.json` and fail loudly | `script[:120000]` deleted act 3 of a 133,937-char file and left no trace | one line + a protocol field |
| 3 | 3 | Move the participant check to after `apply_aliases` | Check ordered before the repair it checks: 48 violations → 7, all real | move two lines |
| 4 | 5 | Dedup every rewritten list inside `apply_aliases` | `THE_AGENTS` ×3 in ev-032 | one `dict.fromkeys` |
| 5 | 8 | Compute `word_count` in code; drop it from the schema | Declared 468, actual 614 | one line |
| 6 | 3 | `confidence: {minimum: 0, maximum: 100}` with the scale named in the description | 16 of 33 events answered 0–10, 17 answered 0–100, and stage 4 compares them | one schema edit |
| 7 | 6 | Raise the cap to the eligible count, or allocate per kind | A flat `[:40]` over a kind-ordered list always eats the last kind: it deleted `RULES_OF_THE_MATRIX`, `ELECTROMAGNETIC_PULSE`, `POLICE`, `SENTINELS` | one line, +9 calls |
| 8 | 2 | Persist passes A and B | 55 of 56 calls currently leave no artifact; the stage cannot be audited or resumed | two `save()` calls |
| 9 | 4 | In code after consolidation: demote all but the first `main` to `subplot`; append any thread-less event to an `UNPLACED` thread | JSON Schema cannot say "at most one main". `check_stage4` reports the ev-033 orphan; stage 2's `repair_coverage` shows the pattern for fixing it | ~15 lines |
| 10 | 5 | Canonicalise ids in code before building the alias map — uppercase, strip non-alphanumerics, drop a leading `THE_`, singularise — then dedup on the normal form with the existing precedence | The precedence guard dedups on the exact id string and was defeated by `CYpher` vs `CYPHER`. Fixes 7 near-duplicate ids in one pass | ~20 lines |
| 11 | 5 | Build the alias map case-insensitively and make a collision **fatal** rather than last-write-wins | 14 alias strings resolve to different canonicals depending on capitalisation; the antagonist has two ids in one artifact | ~15 lines |
| 12 | 1 | **Correspondence check at the stage-1 boundary**: require ≥1 quoted evidence span of ≥25 chars to occur in the scene's own character range, and ≥1 `present` name to occur in the scene text or its `script_map` speaker cues | The only check that can catch a fluent node describing the wrong scene. Rejects 45 nodes on this run, including every fabrication named above | ~30 lines, all arithmetic |
| 13 | 8 | Add `ending` as a **required field emitted before `text`**, as the top-down `expose.json` does with `ending_first` | The single structural difference between an exposé that reaches the end of the story and one that stops at the rescue | one schema edit |
| 14 | 7 | Make `turning_points[].where` an enum over the real event ids, and assert in code that the list is non-decreasing in event order | The EXP-002 pattern exactly: bind in the schema, check the dependency the schema cannot express. Catches the Oracle-after-Cypher inversion and the missing act-3 turn | ~20 lines |
| 15 | 2 | Lower the oversize threshold to `max(8, n // 12)`, and add a **span check**: flag any event whose scene indices span more than 8× its member count | The 36-scene ev-026 missed the current threshold by one. The span check fires on all 14 wide events and is the only signal in the pipeline that surfaces stage-1 damage before stage 8 | ~10 lines |
| 16 | 5 | Over-merge check: flag any entity whose alias set contains two strings the *agents* list holds as separate ids | `THE_AGENTS` holding `Agent Smith` while `AGENT_SMITH` exists is decidable arithmetic | ~10 lines |
| 17 | 6 | Split the profile schema by kind — `wants`/`fears`/`internal_conflict`/`speech` required for agents, absent for locations, objects and concepts, which get affordances, constraints and rules instead | One schema for four kinds forces a hovercraft to have a speech style | ~40 lines |
| 18 | 1 | **Blank-scene canary**: one agent per run with its scene text deliberately empty. Anything it writes is recall | The only test in this design that can detect received-summary substitution. Would have caught this run's bug at scene two | one call |
| 19 | 4 | Replace the doctor's three-way verdict enum with required `events_to_remove` / `events_to_add` plus a per-event justification; `sound` is the case where both are empty | All six doctors returned the same middle verdict. A verdict that costs nothing to give will always be given | one schema edit |
| 20 | 8 | Add a sixth doctor holding "does this reach the end of the story", and give the panel the full event list rather than `what_happens[:250]` | Five doctors, none holding completeness, all missed a synopsis with no third act | one list entry |
| 21 | 6, 7 | Implement the critic-and-revision loops the whitepaper specifies | Stage 6 is 40 calls where the design says 105; stage 7 is 1 where the design says 3. The stages' own quality mechanisms have never run | ~80 lines |
| 22 | 7 | Adopt the top-down root's `state_dimensions` vocabulary and bind stage-6 state variables to it | Without a shared axis vocabulary, state variables are ad-hoc per entity and cannot be compared, aggregated or patched across the cast — which the project brief requires | design change |

**The first twelve are a day's work and change the run's conclusion.** 1, 2 and
12 are the ones without which nothing else is worth measuring.
