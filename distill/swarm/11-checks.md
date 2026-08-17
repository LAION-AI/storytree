# 11 · The mechanical check at every stage boundary

**The governing rule: anything decidable from data on disk must never reach a model.**

Not "should preferably not". Must not. A judge asked whether a participant id exists
in the entity layer will answer, will sound confident, will be right most of the
time, and will cost a call. Set membership is not an opinion. The most expensive
failures this project has recorded were all decidable from files that were sitting
right there and that nobody had compared — the fabricated event asserted at 95%
confidence contradicted the dossier, the model's own preceding node, and the state
model **simultaneously**, and all three were on disk.

A swarm makes this rule load-bearing rather than merely tidy. Ten stages means nine
places where a defect can cross a boundary and become an input, and no single agent
is ever in a position to notice. The check at each boundary is the only thing
standing between a local error and a global one.

---

## 11.1 What "decidable" means

Five kinds of question, and nothing else belongs in a mechanical check:

| Kind | Example | Implemented in |
|---|---|---|
| Set membership | is this speaker one of the script's cues for this scene | `presence.presence_sets` |
| Referential resolution | does `caused_by: ev-014` name an event that exists | `check_integrity.check` |
| Ownership | is `spatial_location` a variable this entity declares | `grounding.check_grounding` |
| Domain membership | is `"severed"` inside the declared domain of that variable | `check_integrity`, `check_grounding` |
| Arithmetic and coverage | do screen-time shares sum to 1.00; does every plot have ≥1 event | `check_integrity.plot_coverage` |

Everything else — is this good, is this the right dramatic choice, is the theory of
mind interesting — is a judgement and belongs to §13.

Two facts make aggressive checking cheap here. Guided decoding is **free** on this
deployment (measured: 45.11 tok/s with a deep schema against 45.33 free-form, 0.5%
apart), so anything expressible as a grammar should be bound into the grammar rather
than checked afterwards. And the checks themselves are set operations over JSON —
microseconds against a 27B forward pass. There is no throughput argument for
skipping them.

But a grammar cannot express a *dependent* constraint. Which variables are legal
depends on which entity was named, and JSON Schema has no way to say so. Enumerating
the union of all entities' variables would permit exactly the failure worth catching
— a variable belonging to a different character — while looking like enforcement.
That class is deliberately left free in the schema and checked after generation.

---

## 11.2 What each stage boundary must assert

### 1 → 2 · scene nodes exist and are real

- Exactly one node per scene in `script_map.json`; no node names a scene that is not
  in the script. Coverage is a count, not a sample.
- `location` and `time_of_day` equal the slug line **exactly**, as a fact, not as
  keyword overlap.
- Every speaker named is a cue the script gives *for that scene*. Identifiers are
  still divergent at this point, so the comparison is over raw cue strings.
- **Not degenerate.** A stub that parses is worse than a missing node: it lands in
  the graph and poisons everything downstream. The observed case was a bare
  `{"ref": "sc-004"}` at 9 tokens with `finish_reason: stop`. Minimum word count,
  required top-level keys, and a document-length floor, then retry.

### 2 → 3 · the event boundaries are a partition

- Every scene belongs to at least one event and has **exactly one** parent event.
- No event is empty; no event contains a scene id that does not exist.
- The event count is neither 1 nor N. Both are the degenerate answers to "group
  these", and both would pass every other check.

### 3 → 4 · the event drafts are usable input

- Every participant named appears in at least one member scene's node. Alias-tolerant
  here, because unification has not run yet — this catches invention, not divergence.
- Entry state and exit state differ on at least one axis. An event where nothing
  changes is not an event, and this is the same assertion that `V1` scored 1.00 on
  in the earlier corpus: both event nodes, in different runs on different material,
  independently declared changes with `before == after`.
- The plot speculation is non-empty. It is stage 4's raw material; an empty one is a
  silently missing input.

### 4 → 6 · the plots close over the events

- Every event has ≥1 plot and exactly one `primary_plot`; every plot id resolves.
- Every plot has ≥1 event. `check_integrity` already reports `uncovered_plots`, and a
  plot with no events is a plot the induction hallucinated.
- Screen-time shares sum to 1.00. This is arithmetic and it has failed: measured 1.0
  for GLM and **1.2** for Qwen on the same forward run.

### 5 → everything · the alias dictionary is a total function

This is the boundary that repairs what stage 1 deliberately permitted, and it is the
one place a *fixed-point* check is the right instrument.

- No alias maps to two canonical ids. If `Alice` resolves to both `ALICE_MILLER` and
  `ALICE_VANE`, the merge is wrong and no downstream check can recover.
- Canonical ids are unique and conform to the naming standard.
- **After the procedural rewrite, zero unresolved names remain anywhere in the scene
  layer or the event drafts.** Run the resolver again over its own output; if it
  finds anything, the rewrite was not total. That is a cheap, decisive check and it
  needs no judge.

### 6 → 9 · the profiles can hold the story

- Every entity referenced anywhere has a profile.
- `init` conforms to the `kind` and `domain` the same profile declares. Measured
  failure: **62 of 62** state-variable init contracts violated in one run and 0 of 30
  in another, on the same schema. The mini-validator types `init` as `_ANY`, so this
  passes schema validation while making the declared domain decorative.
- **Shape agreement.** A domain of bare strings with an init of `{"status": "..."}`
  can never match, so every later change silently misses. This invalidated an entire
  state layer while leaving every schema check green, and it is the check that
  separates the two models: ownership passed 127/127 on a run where in-domain landing
  was 42/127.
- Every location a character's domain permits exists as a declared location entity
  (`domain_names_unknown_place`). Declaring a place only inside a domain lets the
  story go somewhere that was never built.
- ≥2 location entities once there are >5 events (`too_few_locations`). This is the
  assertion that would have caught the founding failure: nine entities declared where
  thirty to forty were asked for, and then all 22 events at the single location that
  existed.
- Each character has enough variables to carry what happens to them. A crude count
  against the number of events they participate in is enough — the measured failure
  was an antagonist with three variables, so his humiliation and contempt had nowhere
  to live and were dropped without trace.

### 7/8 → 9 · root and exposé

Least mechanically checkable of the boundaries, and the honest position is to say so.
Two things are still decidable: every synopsis key is covered by at least one plot,
with **no orphans and no phantoms** (measured 28/28 on one run, 16/17 on another),
and every entity or location the exposé names exists in the entity layer.

### 9 → 10 · the event layer is internally coherent

This boundary is already implemented in full, in `tools/check_integrity.py`:

- participants resolve; causal links resolve in both directions; every event has a
  cause or is explicitly `is_root`
- every state change names a declared entity, **and** a variable that entity owns,
  **and** actually moves it, **and** lands on a value inside the declared domain —
  four separate assertions, and conflating any two of them has already produced a
  wrong number
- no character in two places at one story time (`bilocation`)
- not every event at one location (`single_location`)

### 10 → prose · the scene nodes

`presence.assert_presence`, plus the beat rules:

- **Both directions of the roster.** Someone given lines who does not speak, *and*
  someone who speaks and is given no lines. Only one direction was checked once, and
  the arm satisfied the enum by repeating a single speaker six times and dropping the
  other person in the room: zero off-roster violations, one character deleted.
- No state change for someone not present; no psychology block for someone not
  present; the binding's location is the scene's location; `on_screen` lists nobody
  absent and nobody twice.
- Beats exist, at least one carries a change, and story time does not run backwards
  inside a scene (`G14`/`G18`).
- Every beat's plot id resolves **and** names a plot the parent event serves. A beat
  that discharges a plot its own event does not belong to is a mis-assignment, and it
  is decidable.
- Every patch op applies against the folded world state. The fold *is* the check —
  if the ops do not apply, the timeline is already wrong.

---

## 11.3 Never grade against a list your own apparatus generated

This is the most expensive lesson in `docs/experiments/EXP-002-grounding-scaffold.md`
and it generalises past this project.

The grounded arm reported **11 → 2 violations and 2 → 0 off-roster speakers**. Both
numbers were artifacts. `allowed_speakers()` had been built on `characters_in_scene()`,
which unions the script's speaker cues with *event participants*. On a scene whose
script gives one speaking cue, the enum held three, and `binding.on_screen` carried
`minItems = maxItems = 3`. The schema therefore **mandated** that two characters not
in the scene be listed as present. The model complied and gave them lines. An
independent rubric pass scored that as the arm's worst single failure — and the
harness had required it.

The post-check could not see any of this, because it compared the output against the
same roster that produced it. **"Off-roster speakers: 0" meant only that the model
obeyed a roster the harness had invented.** Corrected against the script's own cues,
the real numbers were 5.3 → 4.0 violations per scene, and one of the corrected
columns had gone the *wrong* way (domain violations 2 → 5, because binding entity ids
exposed value errors that had previously short-circuited before the value was ever
examined).

The model, incidentally, diagnosed the fault in writing, inside the artifact, in
`what_this_exposes`: the Lieutenant *"is not in the valid ID list but is clearly
present in the narrative description… a conflict between the strict ID list and the
narrative logic."* Nobody read it until the rubric pass.

Two rules follow, and both are cheap:

1. **Ground truth comes from the source artefact, never from a derived one.** Who
   speaks is the script's speaker cues. Event participants describe who a scene is
   *about* — a different and larger set, and using it as ground truth measures
   compliance, not correctness.
2. **A fixed length does not verify presence, it mandates it.** `minItems`/`maxItems`
   on a roster is how a constraint manufactures the failure it was meant to prevent.
   Bound *who* may appear; check *how many* afterwards.

---

## 11.4 Three measurement bugs, none of which failed loudly

Recorded together because the shape is the finding.

**(a) The invented roster.** Described above. Produced a confident 2 → 0 that
measured obedience to a list the apparatus wrote. Found by an independent rubric
evaluation, not by the checker.

**(b) The check that read the wrong key.** Two schemas name the same fields
differently — the transition schema uses `from`/`to`, the ensemble clerk emits
`before`/`after`. The grounding check read only one pair. So `to` came back `None`,
the domain test flagged a violation on **every single state change**, and the no-op
test, gated on `from is not None`, **never ran at all**. Three reported violations
were all false and two real no-ops went unseen. The comment left in
`grounding.py` is the right summary: *a check that reads the wrong key does not fail
loudly, it lies.*

**(c) Ownership mistaken for validity.** The ownership check passed **127/127** on a
run where an independent evaluator measured **42/127** state changes "landing on a
declared, in-domain value". Both numbers were correct. The variable *names* were
right and the *values* were wrong, because one model writes `"after": {"status":
"severed"}` against a domain of bare strings and can therefore never match. Two
different questions had been collapsed into one, and the one being asked was the
easier one.

A fourth, caught before it cost anything and worth recording as the near-miss:
`bind_schema` originally indexed a fixed schema path and silently did nothing when the
specimen schema was passed on its own. It bound the location correctly and left every
speaker unconstrained — **a half-applied constraint that reports success.** A dry run
caught it. Had it not, the arm would have measured something other than its label.

None of these raised. None crashed. Each returned a number, and each number was
computed correctly over the wrong thing. Two were found by an evaluation that was not
looking for them; one was found because two numbers that should have agreed did not.

The countermeasure that follows is not "write better checks" — it is
**reconciliation**. Every mechanical counter that matters should have a second,
differently-derived number it can be compared against, and a disagreement should be
treated as an alarm rather than a rounding difference. The 127-versus-42 discrepancy
is the only one of the four that was found by the apparatus itself, and it was found
precisely because a second number existed.

---

## 11.5 What a failing check does

Detection alone has a poor record here. A prompt clause fixed a local field and
regressed a global one; schema binding fixed what the clause could not. So:

- **Every assertion carries the sentence that would have prevented it.**
  `presence.py` stores guidance alongside each violation kind, and `briefing_for()`
  assembles the level-appropriate note that is injected as the swarm descends — so an
  agent is told what the checker will check, *in the checker's own words*, at the
  moment it is about to write the thing being checked.
- **Repairs need an acceptance test.** The repair loop has been observed making things
  worse: 89 errors in, 126 out, and the old code saved the result anyway. Now the
  violation count is compared before and after and a regressive patch is rejected. A
  self-correction step without an acceptance test is just another way to introduce
  errors.
- **A missing node beats a fake one.** On a check failure the node is retried, and on
  repeated failure quarantined rather than written. The swarm can tolerate a hole; it
  cannot tolerate a plausible lie, because every stage below will build on it.
