# 14 · Where a swarm is worse than an oracle

The inversion removes two measured failure modes. It does not remove failure. It
trades a small number of large, visible errors for a large number of small, invisible
ones, and this section is the honest accounting of what that trade costs.

---

## 14.1 A stage-boundary error propagates to everything downstream

This is the mechanism the whole project exists because of, and inverting the order
does not abolish it — it relocates it.

The measured case: a run declared **nine entities** where the brief asked for thirty
to forty. Only one location entity existed, so the event layer placed **22 of 22
events** at it. The story then ended with a character in a place her own state model
could not hold. No individual call was wrong. Every layer passed its schema check.
The error was in a boundary and it reached the leaves.

In the bottom-up design the same shape is available at every one of nine boundaries,
and the blast radius is not uniform:

| Boundary | What a defect corrupts | Blast radius |
|---|---|---|
| 5 · entity unification | every node in the tree, procedurally | **total** |
| 2 · event boundaries | all event drafts, all plots, all plot membership | very large |
| 4 · plots | every event's and every beat's dramaturgical function | large |
| 6 · profiles | every state change and every patch op below | large |
| 1 · scene nodes | the induction inputs for everything above | large but diffuse |
| 3, 7, 8, 9 | one layer and its children | contained |

**Stage 5 is the worst case and it deserves naming as such.** It is the only stage
whose output is applied *procedurally* to every other artifact in the tree. A merge
error there is not a bad node; it is a systematic rewrite of the whole graph, applied
by code that cannot tell it is wrong.

An oracle holding the entire work in one context can, at least in principle, notice
that the exposé and scene 180 disagree. **A swarm agent cannot, by construction.** That
is the price of bounded attention, and it is exactly the property the design is buying
attention-drift resistance with. §11 recovers the *decidable* part of that supervision.
It does not recover the rest, and there is no plan here that does.

Three things a swarm structurally cannot check, and which nobody in it holds:

- **Global aesthetic coherence.** Whether the tone drifts, whether act two sags,
  whether the escalation curve actually escalates. Stage 4's doctors hold one plot
  each; stage 8's hold one criterion each. Nobody holds the story.
- **Taste under conflict.** When two plots both want a scene, an oracle trades off. The
  swarm resolves it in a consolidation call that has read the event drafts and not the
  scenes.
- **The absent thing.** An oracle can notice that a story has no antagonist. Induction
  from what is present cannot induce what is missing — and under-declaration, the
  founding failure, is precisely a failure of absence.

---

## 14.2 More stages means more places for an error to hide

Ten stages, nine boundaries, ~1,840 calls per script (§12). The top-down forward run
was ~29 calls. The error surface is not comparable.

Three specific consequences.

**You cannot see the check you did not write.** Every mechanical check in §11 exists
because a specific failure was found by reading or by an evaluation. The checks are a
record of what has already gone wrong, not a covering set. The domain-membership check
was added only after a discrepancy between two numbers that should have agreed; before
that, an entire class of error was invisible while the checker reported clean.

**A wrong check is worse than a missing one.** EXP-002 is the case. `allowed_speakers()`
built its roster from the wrong source, the schema then *mandated* the error, and the
post-check compared the output against the same invented roster and reported success.
An absent check leaves you uncertain. A wrong check makes you confident.

**Nobody will read 1,840 nodes.** Every substantive failure this project has found was
found by a human or a strong model *reading the outputs*: the 24-year offset between a
backstory's `text` and its `when`, the sibling labelled `estranged_sibling` under three
sentences describing a death, Trinity's IRS hack attributed to Neo, the verbatim
retrieval of a Smith line. None of these were caught by the apparatus. Reading does not
scale to 1,840 nodes, still less to 184,000 across a hundred scripts. **The swarm's
quality assurance has to be mechanical, and mechanical assurance is precisely what the
failures above evade.**

---

## 14.3 Identifier unification is a genuine merge problem

Stage 1 deliberately permits agents to diverge on names, on the argument that forcing
agreement before anyone has read the work is the imposition being removed. Stage 5 is
supposed to repair that procedurally. **The naming standard — a capitalised identity
word, `ALICE_MILLER`, chosen so independent agents converge without coordinating — is a
heuristic, and it fails in ways that are specific and predictable.**

- **Two people, one identity word.** A father and son with the same name. Two
  characters both called Alice. The standard offers nothing.
- **One person, several identity words.** Screenplays do this deliberately: a character
  is `WOMAN IN RED` for two scenes and named in the third. An agent reading scene 2
  cannot know, and *should* not know.
- **Roles versus persons.** `BIG COP` is a role. If the same officer is named later,
  both must merge — and the evidence that they are the same is in the prose, not in the
  cues.
- **Identity change as a plot point.** A disguise, an alias, a reveal. Merging these
  destroys the dramatic irony the story is built on; not merging them leaves the tree
  with two entities for one person. **There is no rule that gets this right without
  reading the story, which is what stage 5 is supposed to avoid needing.**

The current resolver is already fuzzier than the standard suggests. `presence.py` falls
back to a substring match — `k in _norm(cue) or _norm(cue) in k` with a length guard of
3 — which will happily unify `AGENT` with `AGENT_SMITH` in either direction. That is in
production code today, not a hypothetical.

And the failure has already cost a score. In the top-down run the plots layer
forward-declared an entity as `neo` and the dossier layer silently renamed it `ch-01`
without back-filling an alias. Across all five plots, **0 of 22** agent/resistance
references resolved. Referential integrity scored **1** — catastrophic and systemic —
on a node whose other dimensions were fine.

**One design rule follows and it is worth taking.** Merge errors are asymmetric. An
over-merge — two people collapsed into one — is catastrophic and nearly invisible,
because the resulting entity resolves everywhere and every check passes. An under-merge
— one person left as two — shows up as a coverage hole, a character who appears in
scenes 1–4 and never again, and is mechanically detectable. **Tune the standard to fail
toward under-merge, and check for under-merge explicitly** (an entity whose scene
appearances form a suspicious contiguous prefix or suffix is a merge candidate). This
is a mitigation with a cost — some genuine merges will be missed — and it is the right
trade because one direction is recoverable and the other is not.

---

## 14.4 Compression of second-order material is a capability limit

`docs/05` §1 measures it directly. Asking GLM-5.2 for more psychological analyses in
one call did not produce more analysis; it produced the same ~28,000 characters spread
thinner. At four requested, two were hollow — `entity: null`, one field filled out of
eleven — and schema violations rose from 5 to 41.

One task per call is the countermeasure and it works: violations 18.0 → 0.0, complete
blocks 1-of-7 → 6-of-6, specimen lines 0 → 7, at 5.3 calls instead of 2 and an 80%
token increase. **But it is a mitigation, not a fix, because the division does not stop
at the call boundary — it continues inside the call.** A single psychology block asks
for eleven sub-structures, and the model divides its budget across those too.

The evidence that it is the *second-order* material that goes is consistent across
three independent measurements:

- The **specimen exchange** was the first thing dropped when budget got tight — 0 lines
  versus 7 — and it is the one artifact that makes the analysis falsifiable. The schema
  says so in as many words: everything above it is unfalsifiable until somebody speaks.
- Under grounding constraint, arm-wide **theory-of-mind depth-3 fell from 10 to 6**, and
  one scene lost 35% of its words and **all three dynamics blocks**.
- The counters that survive best are the concrete ones — sensorium, trajectory phases.
  The ones that degrade are the abstract, weakly-anchored ones: d2 and d3 towers, the
  `accuracy` field naming where a character's model of another is wrong,
  felt-versus-expressed divergence.

**§10 makes this pressure worse by design.** The scene rubric requires the full mental
model at *every important-change beat*, not just at the scene's two ends. That is
several times more second-order material per scene, requested from the model that
compresses second-order material. Splitting further — one call per theory-of-mind tower
— is the obvious next mitigation, and at some point call overhead and loss of
within-block coherence dominate. **Nobody has measured where that point is.** Until
somebody does, the depth requirement in §10 and the compression finding in `docs/05` §1
are in unresolved tension, and the tension is a capability limit, not a scheduling
problem.

---

## 14.5 Structurally valid and semantically empty

This is the failure this project has produced most often and detects least well.

**The case on disk: a node that reported success twice.** In the grounded arm, `sc-001`
carries `verdict: "pass", gaps: []` in its own `_run_stats.json` — a clean structural
grade — and the grounding post-check reported zero off-roster speakers. Two independent
green lights. An independent rubric pass then scored the same node as the arm's worst
single failure: six lines given to two characters who are not in the scene, because the
harness's own roster had mandated their presence. Both self-reports were computed
correctly, over the wrong thing.

Alongside it, two smaller shapes of the same failure: the hollow psychology blocks
above (`entity: null`, one of eleven fields), and the degenerate stub — a bare
`{"ref": "sc-004"}`, 9 tokens, `finish_reason: stop`, valid JSON, permissive schema,
straight into the graph.

**Why a swarm makes this strictly worse.** Every existing countermeasure is a
*volume-or-presence* test: a 200-byte floor on the JSON, `MIN_TRANSITION_WORDS = 400`,
required top-level keys, and `grade()`'s gap list, which counts towers, phases, senses,
options and specimen lines. Not one of them can distinguish a field that is filled from
a field that is true. They all measure that something is there.

That is a workable defence when a human reads the outputs afterwards. At 1,840 calls
per script it is the *only* defence, and it is the defence a model under budget
pressure satisfies most easily — by writing something in every slot.

Three partial countermeasures, and their limits:

1. **The specimen exchange is the only falsifier in the instrument.** An immaculate
   character analysis and a dead scene look identical on paper until somebody speaks.
   Keep it mandatory, keep `risks_checked` (every named risk tested against the actual
   lines), and keep `voices_distinct`. The limit: three separate nodes declined the swap
   test on a technicality and one then reframed the failure as a deliberate choice.
2. **Reconciliation, not thresholds** (§11.4). Every counter that matters gets a second,
   differently-derived number, and disagreement is an alarm. This is what caught
   127-versus-42. It is the only self-detection this project has ever managed.
3. **A missing node beats a fake one.** Quarantine rather than write. The swarm can
   tolerate a hole; it cannot tolerate a plausible lie, because every stage below builds
   on it — and the bottom-up design has more "below" than the top-down one did.

---

## 14.6 Summary of the position

**Mitigated, with evidence:** budget dilution (one task per call, measured 18.0 → 0.0
violations); attention drift (bounded windows); location and roster drift (schema
binding, measured 1/3 → 3/3 in location); repair-loop regression (an acceptance test,
measured rejecting two regressive patches).

**Accepted, with the cost stated:** no agent holds the whole story, so global coherence
and taste under conflict are unsupervised; the merge standard is tuned to fail toward
the recoverable direction and will therefore miss some genuine merges.

**Unknown, and needing a measurement before the design should be trusted:** whether
prefix caching holds across concurrent long-context slots (§12.3); where the
diminishing return on further call-splitting sits; and whether knowing a scene's
dramaturgical function actually buys depth rather than compliance (§13.4, ablation 4).

The strongest honest claim available today is narrower than the summary's: **the
bottom-up ordering removes two failure modes that were measured, is cheaper by an
architecture-attributable 22×, and introduces an error surface roughly sixty times
larger that is defended only by checks written in response to failures already seen.**
Whether that trade is good is an empirical question and it has not been answered.
