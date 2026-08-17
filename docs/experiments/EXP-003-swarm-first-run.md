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

- **sc-072.** Script, in full: the ship is quiet and dark, everyone is asleep —
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
