# 6. Stage 4 — plots induced from the events

This is the first stage that produces something the top-down pipeline would have
produced *first*. Everything under it already exists: 224 scene nodes, a fixed event
boundary list, and one draft per event carrying a plot speculation with evidence.
The question stage 4 answers is not *what plots should this story have* but **what
plots does this story already have, given thirty independent readings of it**.

That is a different and much easier question, and it is checkable in a way the
top-down version never was.

---

## 6.1 Shape of the stage

Three phases, two of them serial and one wide:

```
4a  induction     1 agent    reads every event draft + speculation → proposes the plot list
4b  panel         5 agents   one plot each, in parallel, argues membership against the script
4c  consolidation 1 agent    reconciles the five reports into the final plot list
```

Seven calls, roughly 31,000 output tokens, ~0.2 minutes of wall time — assumed
figures against the measured 2,812 tok/s aggregate. This is the smallest stage in
the pipeline by volume and among the most consequential by effect, which is the
argument for putting the strongest available model on it. `05-model-behaviour.md` §7
makes that case with numbers: factuality inside reasoning traces was 71 for Grok 4.6
against 44.7 for GLM-5.2, the upper layers are a fraction of a percent of call
volume, and an error there propagates to every scene beneath it.

---

## 6.2 Phase 4a — induction

One agent, holding all thirty event drafts with their speculations, and not holding
the script. That omission is deliberate. Its job is aggregation over readings, and a
model that can re-read the source will re-derive rather than aggregate — which
discards the thirty independent readings that stage 3 exists to produce, and
substitutes one reading made under a much larger context load. The script comes back
in at phase 4b, where the claims get tested against it.

It proposes a plot list across the types in `narrativeforge/schemas.py`:

| Type | What it tracks |
|---|---|
| `external_main` | the concrete goal pursued in the world |
| `relationship` | what happens between two people |
| `antagonist` | the opposing force's own campaign, with its own goal and logic |
| `growth_internal` | what changes inside the protagonist |
| `thematic` | the argument the story is making, as a plot rather than a mood |

Five is the working default, not a rule. A story with two protagonists may need two
relationship plots; a chamber piece may have no meaningful antagonist plot separate
from the main one. **The count is whatever the speculations support, and the panel
in 4b is sized to match it** — five doctors because five plots, not five plots
because five doctors.

Each plot must carry a `goal`, a `stakes`, `resistance`, an `outcome` and a `spine`
of ordered steps. The schema's own note is the operative filter: *nothing floats — a
candidate without goal + resistance + outcome is a motif, not a plot.* The most
common induction error is a theme promoted to a plot: "the cost of loyalty" is not a
plot, it is what a plot is about. The test is whether you can name who pursues what
against whose resistance, and what is lost if they fail.

The induction agent also emits, per plot, the list of event ids whose speculations
supported it. That is what phase 4b argues about, and it is what makes the induction
falsifiable rather than merely plausible.

---

## 6.3 Membership rules

Three, and they are enforced mechanically at the stage boundary, not requested in a
prompt:

1. **Every event belongs to at least one plot.** An event that no plot claims is
   either a real orphan — a sign the plot list is incomplete — or an event that
   should not exist. Either way it is a finding, and it must surface rather than be
   silently dropped. The top-down pipeline had the mirror of this failure: a
   synopsis sentence, `s17`, orphaned with no plot responsible for it
   (`docs/07-quality-evaluation.md` §14).

2. **An event may serve two plots.** This is the normal case for the good ones. The
   scene where the protagonist lies to her partner to protect the investigation
   advances the external plot and damages the relationship plot in one move; the
   whole craft of interlocking structure is events that do double duty. Forcing a
   single assignment would flatten exactly the events that carry the most weight,
   and stage 3's `alternative` field exists to catch them.

3. **Exactly one of them is `primary_plot`.** Multi-membership is legal; ambiguous
   ownership is not. Every event has exactly one parent plot, so the tree above the
   event layer is a tree and can be walked, counted and checked. The `plots` array
   is the DAG; `primary_plot` is the spanning tree over it.

There is no upper bound on membership beyond what the panel will accept, but an
event claimed by four plots is nearly always an event described too vaguely to be
excluded from anything. The panel should say so; whether it reliably does is
unmeasured.

---

## 6.4 Phase 4b — one doctor per plot

Five agents run in parallel. Each receives **one plot**, the full script, every event
draft, and the induction agent's claimed membership list for that plot only. Its job
is adversarial in one direction: it argues, against the script, which events actually
belong to its plot, which claimed events do not, and which unclaimed events should.

Each returns:

```
confirmed    event ids that belong, with the script evidence
rejected     claimed event ids that do not, with why
added        unclaimed event ids that should, with the script evidence
spine        the ordered steps, and which event discharges each
verdict      whether this is a plot at all, or a motif that should be dissolved
```

The last field matters more than it looks. **A doctor must be able to conclude that
its own plot does not exist.** A panel where every member's incentive is to justify
its assignment produces five plots regardless of whether the story has five, and the
failure is invisible because each report is individually coherent. `05-model-behaviour.md`
§6 records the general form of this: two retrospective traces of the same beat, each
internally airtight and mutually incompatible — *internal coherence is not evidence
of insight; it is evidence of fluency*.

### Why one doctor per plot rather than one doctor for all five

Two reasons, and the first is measured.

**Budget dilution.** `docs/05-model-behaviour.md` §1 varied only the number of deep
structures requested in a single call, holding model, schema and scene constant:

| Requested in one call | Complete blocks | Carried a trajectory | Schema violations |
|---|---|---|---|
| 1 | 1 of 1 | 1 of 1 | 5 |
| 2 | 0 of 2 | 0 of 2 | 16 |
| 4 | 2 of 4 | 2 of 4 | 41 |

Output length stayed near 28,000 characters in every condition. **Asking for more
did not produce more; it produced the same amount spread thinner.** At four, two of
the four were hollow — `entity: null`, one field of eleven filled. A single doctor
holding five plots is exactly the four-structure condition with one more structure,
and the predicted result is five membership reports of which two are real and three
are assertions. That prediction is an extrapolation from the measurement, not itself
measured on this stage.

The scaffolded fix measured on the same scene, same model, same schema — one deep
structure per call, assembled in code — went from 18.0 mean violations to 0.0, from
1 of 7 complete blocks to 6 of 6, and from 0 specimen dialogue lines to 7. It cost
5.3 calls instead of 2 and 80% more output tokens. Here the equivalent cost is four
extra calls out of roughly 690 in the whole pipeline.

**Attention.** The second reason is less quantified. A doctor holding one plot reads
thirty event drafts asking one question of each. A doctor holding five reads the same
thirty asking five questions of each, with the five competing inside one attention
budget over a context that already contains the full script. The windowing argument
from stage 2 applies unchanged: twenty scenes of attention drift less than two
hundred, and one question drifts less than five. We have not measured attention drift
directly on this pipeline; the evidence is the budget-dilution table above and the
general shape of the failures it produced.

There is a real cost to the split, and it should be stated. **Five doctors each
holding one plot cannot see the interference between plots.** A doctor for the
relationship plot arguing that event 14 belongs to it does not know that the
antagonist doctor is arguing the same thing for the same event with equal
conviction. Cross-plot structure — the `interference` field of the plot schema, the
`because` cross-references between spine steps — is invisible from inside a single
plot. That is what phase 4c is for, and it is the phase with the least margin.

---

## 6.5 Phase 4c — consolidation

One agent, holding the five doctor reports, the induction agent's original list, and
the event drafts. It is not re-deciding; it is resolving a small number of specific
conflicts:

- **Contested events.** Two doctors both claim event 14 as confirmed. Legal —
  multi-membership is the point — but one of them has to be `primary_plot`. The
  consolidator decides which, and the criterion is which plot's spine would have a
  hole without it.
- **Orphans.** An event no doctor confirmed. Either the plot list is missing a
  thread, or the event is real but subordinate and should be attached to the plot it
  most nearly serves. The consolidator must say which, in a field, and an orphan
  that survives consolidation is a hard failure at the boundary check.
- **Dissolutions.** A doctor that returned *this is a motif, not a plot*. Its events
  have to be redistributed, and the consolidator does that explicitly rather than by
  dropping them.
- **Interference.** The one thing no doctor could see. Which plots compete for the
  protagonist, for the clock, for screen time.

The consolidator does **not** get to invent a sixth plot. If the orphan set implies
a missing thread, that is a re-run of 4a with the finding fed back, not a quiet
insertion at the last step — the whole value of the panel is that plots have been
argued against the script, and a plot added at 4c has been argued against nothing.
Whether a re-run is ever actually needed in practice is unknown; on the runs to hand
this stage has not been executed.

---

## 6.6 Boundary check before stage 6

Decidable from data, so no model touches it:

- every event id has a `primary_plot`, and it is a member of its own `plots` array
- every event's `plots` array is non-empty
- every plot id referenced by an event exists in the plot list
- every plot has at least one event whose `primary_plot` it is — a plot no event
  parents is a plot with no spine, whatever it claims
- every spine step of every plot is discharged by at least one event
- no plot is missing `goal`, `stakes`, `resistance` or `outcome`
- **reversal floor**: at least one event in each plot carries `reversal: true`

The last one is a direct import from `docs/07-quality-evaluation.md` §15.4, where it
was proposed after a run shipped 22 events across a plot with **zero reversals,
including at the climax**. It is one line of code and it catches a flat climax, which
is otherwise invisible to every referential-integrity check in the system. Every
check that existed at the time asked whether a claim was *admissible*; none asked
whether it *mattered*.
