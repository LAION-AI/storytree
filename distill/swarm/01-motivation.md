# 1 · The failure that inverts the direction

The pipeline this replaces builds a narrative graph downward. Story root, then
exposé, then plots, then entities, then events, then scenes. Each layer is handed
everything above it and asked to decompose one step further. It is the order a
writer works in, it gives every layer a target to satisfy, and it makes validation
tractable — a scene can be checked against its event because the event was written
first.

Four rubric passes over two arms found the same shape of failure in both, and in
both cases the failure was already present several layers above where it became
visible. This section sets out what was measured, why no individual call in either
run can be faulted, and what the top-down order was quietly assuming.

---

## 1.1 What was measured

All numbers in this subsection are **measured**, from `docs/07-quality-evaluation.md`
§15 and §15.3 (third pass) and §2–§4 (first pass). They come from two runs on two
different tasks.

### The forward arm: nine entities

`runs/lattice` is *forward* generation — invention from a brief, not reconstruction.
The brief (`briefs/lattice.md`) asks in terms for "roughly 45–60 scenes across
5 plots, 30–40 entities".

| | Qwen arm | GLM arm | brief asks |
|---|---|---|---|
| Entities declared | **9** | 17 | 30–40 |
| Locations | **1** | 6 | — |
| Concepts | **0** | 3 | — |

Nine against thirty. One location against a story whose central fact is a boundary
between a simulation and the physical world outside it. Zero concept entities in a
story that tracks the discovery, decoding and weaponisation of a language across
two acts.

Nothing objected. The entity artifact is schema-valid. Every id resolves. The
declared state variables are internally consistent, and in this arm they are
unusually good at it — Qwen's `init` values conform to their own declared
kind and domain on 30 of 30 variables, where GLM's `ch-01` conformed on 0 of 11.
The layer that under-populated the story by a factor of three is, by every
mechanical measure available, the cleaner of the two.

### What the event layer then did with nine entities

The event layer, one call per event, produced twenty-two events. Measured:

- **22 of 22 events are located at `lo-01`, "Vantage Municipal"** — the only
  location entity that exists. Four of them are Delphine, whom the brief places
  outside the simulation. `ev-022` reads "Kett sits in his office" while tagged
  `lo-01`. The GLM arm, with six locations, spread the same story across five of
  them.
- **`reversal: true` on 0 of 22 events**, including the climax and the ending.
  GLM: 7 of 20.
- **19 of 22 events have exactly one cause and exactly one effect.** The causal
  graph is a chain with one join, not a DAG.
- The story's last event is a scalar move of 5 points at **magnitude 10** — the
  schema's own anchor for "a flicker that leaves no mark".
- **34 of 34 declared state changes write to a variable the entity owns.** GLM
  managed 42 of 127. On the check that was actually being run, this layer is
  three times better than the one it is worse than.

### The ending its own state model could not hold

`ev-021`: *"She is ejected from Vantage, her mind still in the simulation, but her
body in the physical world … She holds the portable neural drive."*

Imogen is a resident. The brief defines residents as neural scans of people who
died between 2029 and 2044, and auditors as "residents given a partial exemption
from the forgetting". She has no body. She cannot hold an object in the physical
world.

The important part is where that error lives. It is not a stray sentence in prose.
It is written into the state model as `ch-01.spatial_location: vantage →
physical_world` at magnitude 100 — and the variable was declared, one layer up, by
the entity agent, with `domain: ["vantage", "physical_world"]`, for a character who
cannot occupy the second value. The event agent wrote a legal transition on a
legally declared variable. Every mechanical check passes, because the state model
is internally consistent and consistently wrong.

### The reconstruction arm: the same shape, a different symptom

`reconstruct/runs/matrix` is reconstruction of a real screenplay. Its motivating
failure is not under-declaration but leakage, and it has the same topology.

The entity layer scored **E1 = 2** on t0 discipline: the dossiers fold the ending
into fields describing the opening state. `lo-01.profile.significance.b01` reads,
verbatim, *"Trinity escapes through Room 303 in the opening; Neo is shot dead and
resurrected there in the climax."* `lo-01.arc.end_state` names the resurrection.
`ch-01.state_variables` includes `is_the_one`.

At the entity layer that is a stylistic lapse worth one rubric point. Downstream it
is fatal. The blind transition calls — the ones whose entire premise is that they
have not read the work — are handed those dossiers by `blind_context()`, which
strips outcome-bearing exposé keys and truncates plot spines but does not filter
entity profiles. So node 7 argues, as forward reasoning, that its choice "creates
the dramatic irony that will make the later return to this location (the death and
resurrection of Neo) land with devastating force", and node 8 that the hotel "will
return as the site of Neo's death and resurrection". Measured: **0 phrasal
hindsight tells** across all three nodes — no "as it turns out", no "we later
learn". The vocabulary ban was obeyed to the letter. The substance was not
available to be banned.

Node 7 also places Trinity in a scene whose envelope roster lists only `BIG COP`.
It had a reason: `lo-01.significance` told it that Trinity escapes through Room 303
in the opening.

---

## 1.2 No individual call was wrong

This is the claim the whole design rests on, so it is worth making precisely rather
than rhetorically.

Take the four failures above and ask, for each, which call should have behaved
differently *given what it was handed*.

**The event agent that tagged Delphine's office as `lo-01`.** It was given a
location field typed as "a location entity id" and a set of declared location
entities containing exactly one member. There was no legal value that meant
"outside". The alternatives available to it were: emit `lo-01` (wrong, valid),
emit a string that resolves to nothing (wrong, invalid, and would have been caught
— but caught as an event-layer error), or refuse. It chose the only option that
passes. A well-behaved agent in an under-specified world produces exactly this.

**The event agent that wrote the impossible ending.** It moved a declared variable
between two members of that variable's declared domain. That is the most compliant
thing it could have done. To have refused, it would have had to know that the
entity layer's domain declaration contradicted a rule in the brief that the entity
layer had already read and the event agent had not been asked to check.

**The blind transition agent that reasoned about Neo's resurrection.** It was told
to reason from established facts and to cite them. It reasoned from an established
fact and cited it. The fact was in its context because a filter did not cover the
channel it arrived through. Instructing the agent harder would not have helped: it
was already scrupulous about the vocabulary of hindsight, which is precisely why
the phrasal check reported clean.

**The entity agent that declared nine entities.** This is the only one where a
better call was available, and even here the fault is thin. The brief's "30–40
entities" is one clause in a document the agent also had to satisfy on genre,
audience, register, mechanics and forbidden tics. Measured elsewhere in this
corpus: **models divide a per-call output budget rather than scaling it** (see
`docs/05-model-behaviour.md` §1 — requesting four psychological analyses in one
call produced two hollow ones and 41 schema violations, at the same total output
length as requesting one). An agent asked to satisfy a dozen constraints in one
emission satisfies the ones it is scored on. Nothing scored entity count.

So the propagation is silent by construction. Each call is locally optimal, each
artifact passes its own validator, and the error is only legible from a vantage
point no single call occupies. The Qwen forward run shipped **83 schema errors in
`events.json` unnoticed** in the reconstruction arm and **zero** in this one; the
difference in outcome between those two facts is nil, because the failure that
mattered was never a schema failure.

**A thin superstructure strangles every layer beneath it, silently, while passing
every check.**

---

## 1.3 What the top-down order assumed

The order is not arbitrary and it was not chosen carelessly. Three real arguments
support it:

1. **It matches how a writer works.** Premise, treatment, outline, pages. The
   pipeline's layer names are borrowed from a working vocabulary, which is a good
   sign about whether the layers carve anything real.
2. **It gives every call a target.** A scene agent that knows its event knows what
   the scene is for. Without that, a scene node is a description rather than a
   decision — and `docs/07` §2 records exactly that failure mode under the
   independent-writer dimension (G = 2.33 mean, the weakest of the seven
   universal dimensions, and the diagnosis is "restatement of the layer above in
   the local vocabulary").
3. **It makes validation cheap.** Checking a child against a declared parent is a
   set-membership test. Inducing the parent from the children is not.

But all three arguments assume something that is only sometimes true:
**that the superstructure is knowable before anything below it has been read.**

In forward generation this assumption is nearly defensible, because there is
nothing to read — the brief is the only evidence and the author is the source of
everything else. Nearly, but not quite: the lattice failure is a forward failure.
The brief *was* the evidence, and the entity layer under-read it. What top-down
generation actually assumes in the forward direction is not that the superstructure
exists but that a single call can extract it from the brief in one pass, with no
opportunity to revise once the consequences are visible. That is the assumption
that broke.

In reconstruction the assumption is simply false. The superstructure is a fact
about a document that exists. There is no sense in which the plots of a finished
screenplay are chosen; they are *found*. Asking a model to declare them before it
has read a scene is asking it to guess, and then binding 224 downstream calls to
the guess. The measured consequence in this corpus is node 4's plot layer: one plot
holding **42% of screen time and 20 of 28 synopsis sentences**, which the evaluator
called "a decomposition that has not decomposed", and **0 of 22** agent and
resistance references resolving to anything in the entity layer, because the plot
layer forward-declared ids (`neo`, `system_matrix`) that the entity layer then
silently renamed (`ch-01`) or could never have created (`neo_self_doubt` is not an
entity and never could be).

---

## 1.4 The inversion

Nothing above a scene is knowable with confidence before the scenes are read.
Everything above a scene is derivable once they are.

Both halves matter. The first is why top-down fails; the second is why bottom-up is
possible at all. A scene, read on its own, tells you who is in it, where it is, what
changes, and what it seems to be part of. Twenty scenes tell you where the events
are. Thirty events tell you what the plots are. The entity set is the union of
everything the scenes actually mention, which is a lower bound that no agent has to
guess at — and it is a lower bound of roughly the right size, because a story that
uses thirty-five things mentions thirty-five things.

That last point is the specific answer to the nine-entity failure, and it is worth
stating as a prediction rather than a claim: **an entity layer induced from 224
read scenes should land within the brief's declared range without being told the
range.** This is *assumed*, not measured. It is the cheapest thing in this design
to falsify and it should be falsified first.

What the inversion does not fix is set out in §14. Two limits are worth naming here
because they bound how much of the above is really addressed:

- **The compression failure is a capability limit, not a scheduling one.** A 27B
  model writing one sentence where a paragraph is needed will do that in any
  topology. The countermeasure — one narrow task per call — is measured to work
  (`docs/05` §1: 18.0 → 0.0 violations, 1 of 7 → 6 of 6 complete blocks) but it is
  a mitigation, not a repair.
- **Inducing a superstructure is a harder problem than imposing one.** Imposition
  is a single call; induction is a reconciliation across hundreds of independent
  readings that will disagree. This design moves the difficulty rather than
  removing it, and §11 and §14 are about where it lands.
