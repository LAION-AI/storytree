# 5. Stage 3 — event drafts, one agent per event

Stage 2 hands over a list of events and, for each, the set of scene ids that belong
to it. Nothing else about the event is decided: not what it is for, not who owns it,
not which thread of the story it advances. Stage 3 fills that in, one agent per
event, all of them concurrent.

At this point in the pipeline **there is still no story root, no exposé, no plot list
and no entity table.** That is the whole point of the inversion, and it is what makes
this stage's job unusual: the agent has to describe a unit of narrative machinery
without being told what machine it is part of.

---

## 5.1 What the agent is given

Three things, in this order:

```
the full script                     ~40,000 tokens for a feature, byte-identical
                                    across every agent in the stage
the event's member scene nodes      stage-1 output for exactly its own scenes
the boundary record from stage 2    the one- or two-sentence statement of what
                                    this event is, and which scenes are in it
```

The script is there because the scene nodes are summaries and summaries lose the
thing that decides an argument. The member scene nodes are there because they
already contain per-scene state readings, and re-deriving them would be waste and
would also produce a second, differing set. The boundary record is fixed input, not
a suggestion: **stage 3 may not re-cut the event.** If an agent believes the
boundary is wrong it says so in a field and proceeds anyway; a stage that both
writes the event and decides where the event stops has no fixed point to converge
on, and stage 2 already spent three passes reaching one.

What the agent does *not* get is any other event's draft. Thirty agents each holding
the other twenty-nine drafts is thirty times the prefill for a coordination benefit
that stage 4 is going to provide properly anyway.

---

## 5.2 What it writes

The draft is the event schema of `narrativeforge/schemas.py` minus everything that
requires a superstructure that does not exist yet. Concretely:

| Field | What it is | Notes |
|---|---|---|
| `participants` | every entity involved | free naming; stage 5 unifies |
| `entry_state` | the state each participant is in when the event opens | |
| `state_changes` | what moves, in which dimension, by how much | dimension from the closed vocabulary; magnitude on the five anchored steps 10/25/50/75/100 |
| `exit_state` | the state each participant is in when it closes | must be `entry_state` with `state_changes` applied |
| `action` | what happens, third person, no direct speech | 60–160 words |
| `summary` | ≤30 words | |
| `causal_note` | why this follows from what came before | |
| `plot_speculation` | **which larger thread this serves** | see §5.3 |

Two fields of the real event schema are deliberately absent: `primary_plot` and
`plots`. They cannot be filled honestly before stage 4 exists, and a field filled
dishonestly is worse than a field left empty — the pipeline has already been bitten
by a stub that parsed cleanly and poisoned everything downstream (`05-model-behaviour.md`
§4). `location` is written as a name, not an id, for the same reason.

The entry/exit pair is not decoration. It is the invariant that makes the whole
graph foldable later: **exit must equal entry plus the declared changes**, and that
is a mechanical check, not a judgement, so it belongs in stage 11's boundary check
and never in a model call.

### The three-variable trap, at the event layer

The measured failure in `docs/07-quality-evaluation.md` §21 is that the film's
antagonist was declared with three state variables — `pursuit_phase`,
`escape_desire_revealed`, `status` — and his contempt, nausea and humiliation had
nowhere to live. The clerk was honest and reported `not_expressible`; the dossier
was thin.

In the top-down pipeline that constraint arrived *before* anyone had read a scene.
Here the order is reversed, so the event agent writes state changes in free
vocabulary and stage 6 derives the variable set from what the events actually needed.
**The variable vocabulary is a consequence of the events rather than a prior
restriction on them.** Whether that actually produces richer dossiers is unmeasured
— it is the mechanism by which it *should*, and the comparison against the top-down
arms on disk is §13's job.

---

## 5.3 The speculation, and why it is required

The last field asks the agent to say **which larger plot it thinks this event
serves**, with the plot list not yet in existence.

Every instinct in a schema-driven pipeline says to forbid this. The agent cannot
know the answer; asking it to produce one invites the exact confabulation the rest
of the design works to suppress. The reason it is required anyway:

**Stage 4 has to induce the plot list from something.** The alternative is one agent
reading thirty bare event descriptions and deciding, from scratch, what threads run
through them. That agent has read no scene closely. It sees thirty summaries and
infers structure from summaries — which is a compressed, second-hand view, and
compression is precisely where this model class loses the second-order material
(§5.5). The speculations are the raw material: thirty independent readings, each
made by an agent that *did* read its own event's scenes against the full script,
each proposing what thread it sits on. Stage 4's job stops being invention and
becomes aggregation, which is a much easier job and a checkable one.

There is also a diagnostic use. Thirty speculations that all name recognisably the
same three or four threads is evidence that the threads are really in the script.
Thirty speculations that scatter is evidence that either the script is unusually
diffuse or stage 2 cut the events badly. **Agreement across independent readers is
the only cheap signal of structure the pipeline has at this point**, and it costs
one field.

### Speculate is not invent

The distinction is carried by the prompt and enforced by the field shape:

```
plot_speculation: {
  claim:      "what thread this event serves"     one sentence
  evidence:   [ script citations ]                 what in the text supports it
  confidence: low | medium | high
  alternative:"the other reading, if there is one" or null
}
```

Three rules:

1. **Reason from the script, not from genre.** "This is the mentor-death beat
   because thrillers have one at the midpoint" is invention. "This is a mentor
   thread because the older man has now twice given the protagonist an instruction
   she followed against her own judgement, in scenes 14 and 31" is reasoning. The
   `evidence` array is what makes the difference inspectable: **a claim with an
   empty evidence array is rejected mechanically**, before any model sees it.

2. **Mark the inference as inference.** `confidence` is not a formality. Stage 4
   weights the speculations, and an event that says *low* is telling stage 4 not to
   build a plot on it alone. Requiring the marker also does work inside the call —
   the alternative to "the model is uncertain and says so" is not "the model is
   certain", it is "the model is uncertain and asserts anyway", which is what the
   hindsight-leak review in `05-model-behaviour.md` §6 calls *confidence out of
   proportion to the evidence available*.

3. **Do not name plots you cannot see.** The agent describes the thread in its own
   words; it does not emit a plot id, does not invent `pl-03`, and does not attempt
   to reconcile with any other event. Naming is stage 4's and stage 5's problem, and
   an agent that guesses at ids creates the illusion of agreement where there is
   none.

The `alternative` field is there because the single most useful thing a speculation
can say is *this event reads two ways*. Events that serve two plots are legal and
expected (§6.3), and the events that do are usually the ones an agent found
genuinely ambiguous. Forcing a single reading here would throw that away.

---

## 5.4 The leakage risk, and what it is not

This stage is **sighted** — the agent has the script — so the blind-reasoning
discipline of `docs/03-reconstruction.md` does not apply and no leak check is
needed. Stage 3 is describing a work that exists; it is not predicting one. The
blind constraint matters at stage 10 for the scene-level deliberation, and for
forward generation, and nowhere here.

What *is* a risk is the opposite: a sighted agent writing a plot speculation that is
a paraphrase of the script's marketing rather than a reading of its structure. A
well-known film will pull the model toward the received summary of that film. The
`evidence` requirement is the only defence in place, and it is a partial one —
citations can be selected to support a received reading as easily as an observed
one. **This is not currently measured and there is no counter-check for it.** If
reconstruction of well-known works produces suspiciously canonical plot lists while
reconstruction of obscure ones does not, that is the tell, and comparing the two is
cheap.

---

## 5.5 Why one agent per event

Same reason as everywhere else in this design: `05-model-behaviour.md` §1. Asking
one call for four psychological analyses produced two hollow ones and 41 schema
violations, with output length essentially unchanged. Models divide a fixed budget
rather than scaling it.

An event draft carries entry state, exit state, a set of dimensioned changes, an
action paragraph and a speculation with evidence. That is one deep structure. Two
events in one call is the measured failure mode, and the fact that the two events
are more similar to each other than two characters are does not help — the
measurement varied only the count.

Cost, from the estimate table in `WHITEPAPER-SWARM.md`: roughly 30 calls, ~180,000
output tokens, about 1.1 minutes of wall time at the measured 2,812 tok/s aggregate.
**Those token and call figures are assumed; the 2,812 tok/s is measured**
(`reports/qwen-local-deployment.md`). This is the cheapest substantial stage in the
pipeline — under 4% of total output tokens — which is a good property for a stage
whose output every later stage depends on.

---

## 5.6 What the boundary check verifies

Before stage 4 may start, mechanically and with no model involved:

- every event id from stage 2 has exactly one draft
- every draft's member scenes match stage 2's assignment exactly
- every scene id appears in at least one event's membership
- `exit_state` equals `entry_state` with `state_changes` applied, per participant
- every `state_changes` entry names a dimension from the closed vocabulary
- every `magnitude` is one of 10, 25, 50, 75, 100
- `plot_speculation.evidence` is non-empty
- no draft is shorter than a minimum word count, and no draft is a stub

The last one is the cheap version of the degenerate-response guard: a document
under 200 bytes of JSON is a retry, not a node. **A fake node is worse than a
missing one** — that is measured, not assumed, and it cost a run before it was
caught.
