# 9. Stage 7 — story root, then exposé

These are the two artifacts the top-down pipeline wrote **first**, before anyone had
read a scene, and they are the two that did the most damage when they were thin. A
story root declaring one location made every event happen in one location; an exposé
leaving a synopsis sentence with no plot responsible for it left a hole nothing
downstream could see. Here they are written last, from a tree that is already
complete, and the job changes from *declaration* to *description*.

That change is the whole argument. **The root is no longer a set of constraints on
the story; it is a summary of the story's own constraints, read off the finished
layers.** Nothing beneath it can be strangled by it, because nothing beneath it is
still to be written.

Two phases:

```
7a  story root   1 author + 1 critic + 1 revision       ~3 calls
7b  exposé       1 author + 4-5 doctors + 1 revision    ~7-8 calls
```

Roughly 59,000 output tokens and under half a minute of wall time — **assumed**
figures against the measured 2,812 tok/s aggregate in
`reports/qwen-local-deployment.md`. It is under 1.5% of the pipeline's output and it
determines how every downstream reader understands the work, which is the same
argument stage 4 makes for putting the strongest available model here
(`05-model-behaviour.md` §7: factuality 71 versus 44.7, eight calls out of hundreds,
nearly free).

---

## 9.1 The story root, derived rather than declared

`STORY_ROOT_SCHEMA` is unchanged from the forward pipeline, but in bottom-up order
most of its fields are now *readings* with a source underneath them:

| Field | Where it comes from now |
|---|---|
| `logline`, `premise` | the plot list, primarily `external_main` |
| `genre_primary`, `genre_secondary` | the events and the register of the script |
| `setting.places` | **the location entities that exist**, not a wish list |
| `setting.rules_of_the_world` | the `concept` entities and what the script never violates |
| `pov`, `style` | measured off the script — dialogue ratio is countable |
| `state_dimensions` | **the dimensions the event drafts actually used** |
| `constraints.plot_count`, `scene_count_target`, `event_count_target` | counts of what exists |
| `keep_in_mind` | standing notes for later layers, and for regeneration |

Two of those rows are worth pausing on.

`setting.places` was the field that failed. In the measured run
(`docs/07-quality-evaluation.md` §11, §15.3) the root named seven distinct places and
the entity layer declared one, and every event was therefore tagged to
`lo-01 Vantage Municipal`. The root and the entity layer disagreed and there was no
check between them, so the disagreement resolved in favour of the layer with fewer
options. Deriving `places` from the location entities makes the two agree **by
construction**; the remaining check is the reverse direction, that no place named in
the script is missing from both.

`state_dimensions` is the closed vocabulary the whole work's state changes may draw
from — physiological, emotional, epistemic, psychological, social, material, spatial,
legal, reputational, world, plus genre extensions for magical, technological and
political. Declared up front it is a guess about what the story will need. Derived
here it is the observed union over thirty event drafts, which is the only version of
that field with evidence behind it. If the derived set is narrower than the declared
default, that is information: the story does not do social state, and later
regeneration should not pretend it does.

The root's critic is a single agent with the same evidence rule as everywhere else —
**an objection cites the tree it contradicts**, not general taste — and the revision
is accepted only if it does not regress, per the acceptance test in §8.5.

### The one thing the root still declares

`constraints.target_word_count`, `audience`, `reader_promise`, and the act structure
the exposé will be checked against. Those are not readable off a reconstruction of
an existing work in any strong sense; a reconstruction can *observe* that a script
turns at roughly the 27% mark, and it can *name* the structure it appears to follow,
but calling it three-act is a claim about intent. The root should say which
structure it is asserting and on what basis, because §9.4 turns that assertion into
a criterion an agent will be graded on, and a criterion no one can trace back to a
stated commitment is a criterion nobody can fail honestly.

---

## 9.2 The exposé and what it is for

`EXPOSE_SCHEMA` carries five things, and the schema's own note says which half
matters: *the full-spoiler condensation is the important half; the jacket copy is
the marketing artifact.*

| Field | Requirement |
|---|---|
| `ending_first` | ending, cost, final image — decided before the opening sentence |
| `jacket_copy` | 120–150 words, in the register of the work, withholds the ending |
| `plot_summary_short` | 150–250 words, plain, chronological, **no withheld ending** |
| `plot_summary_long` | 700–1200 words, complete, every plot, every significant fate |
| `synopsis` | 450–550 words split one sentence per key `s01`, `s02`, … each with a `function` and a story-time rank |

The synopsis being a sentence map rather than a paragraph is what makes every later
claim traceable: plots declare `covers_synopsis`, events bind to plot spine steps,
and a sentence with nothing pointing at it is visible. That is exactly how the
orphan was found — `s17`, covered by none of five plots, in a layer whose
`screen_time_share` also summed to **1.20**, which is not a share
(`docs/07-quality-evaluation.md` §11). Both are peripheral arithmetic; both survived
every check that existed until someone summed a column.

The `plot_summary_short` description in the schema is unusually blunt and worth
quoting because it names the failure it was written against: *the way an encyclopedia
summarises a plot, not the way a jacket sells one. Neutral third person, present
tense, no rhetorical questions, no teasing, no withheld ending. If a reader finishes
this and still does not know how it ends, it has failed.* Left to itself a model
writes jacket copy in every field, because jacket copy is what plot summaries look
like in its training data.

### The five actual requirements

1. **Understandable to someone who has never heard of the story.** Not a reminder
   for someone who has read it. The test is whether a reader with no prior context
   finishes it knowing who wants what, what stops them, and how it ends.
2. **In-world jargon is explained.** Every invented term, faction name, technology
   or rule is glossed the first time it matters, *in passing, without stopping to
   lecture*. A summary that says the protagonist "completes her carriage
   methodology" has told an outsider nothing.
3. **Every plot is honoured, implicitly, through events.** Not a paragraph per plot
   — that reads like a pitch document and it is not how a summary works. The
   relationship plot is present because the events that carry it are narrated as
   part of the chronology. The check is coverage: no plot may be inferable only from
   the plot list, and no synopsis sentence may be orphaned.
4. **It follows the act structure the root declares.** Whatever §9.1 asserted, the
   summary's shape has to match it — the turns land where the root says they land,
   and the escalation of cost is visible from act to act.
5. **It states what makes the protagonist someone an audience opens up to.** This
   is the requirement most often skipped and the hardest to fake. Not that she is
   likeable. Frey's material in `narrativeforge/craft.py` is specific about the
   mechanism: a ruling passion that governs every waking moment, a steadfastness
   that discouragement does not stop, and an inner conflict — *a character with no
   inner conflict produces only pity, never engagement*. A summary that gives the
   protagonist a goal but never says why a stranger would follow her through it has
   described the plot and not the story.

---

## 9.3 One criterion per doctor

Four or five agents, in parallel, each holding **exactly one** of the criteria above
and nothing else. Each has the exposé, the full tree, and the script.

| Doctor | Holds | Returns |
|---|---|---|
| 1 | outsider comprehensibility | every term, name or reference an outsider cannot resolve, with the sentence it appears in |
| 2 | plot coverage | per plot: which synopsis sentences carry it; per synopsis sentence: which plot claims it; orphans on both sides |
| 3 | act structure | where the turns actually fall in the summary, against the root's declaration |
| 4 | readability | sentences that do not parse on one pass, register drift, jacket-copy leakage into the summary fields |
| 5 *(optional)* | protagonist access | what the summary offers a reader as a reason to follow this person |

Doctor 2's output is nearly mechanical and that is deliberate — it is the orphan
check written as a report rather than a judgement, and the parts of it that are truly
decidable (does every plot id appear in some sentence's coverage) belong in the
boundary check, not in a model call.

### Why not one doctor with a four-item checklist

Because a checklist in one call is the four-structures condition of
`05-model-behaviour.md` §1, and that condition is measured:

| Requested in one call | Complete blocks | Carried a trajectory | Schema violations |
|---|---|---|---|
| 1 | 1 of 1 | 1 of 1 | 5 |
| 2 | 0 of 2 | 0 of 2 | 16 |
| 4 | 2 of 4 | 2 of 4 | 41 |

Output length was near 28,000 characters in every condition. **The budget does not
grow with the ask; it divides.** Four criteria in one call predicts two real
critiques and two that name the criterion and assert compliance — and the two that
go hollow are not random. The measured analogue is the specimen dialogue: in the
single-call condition the model wrote **0** specimen lines against 7 in the
scaffolded one, and the specimen is the single falsifiable artifact in the whole
node. *It was the first thing dropped when the budget got tight, which is exactly
the wrong thing to drop.*

Applied here, the criterion most likely to go hollow is the one that requires the
most work to evaluate honestly. That is doctor 1: checking outsider comprehensibility
means going term by term and simulating a reader who does not know the world, which
is expensive, while asserting "the summary is comprehensible to a new reader" is
free and looks identical in the output. Coverage and act structure are cheaper to
check and would survive; comprehensibility and protagonist access would be the ones
reduced to a sentence of praise.

The counter-evidence for the fix is on the same page. The scaffolded arm — one deep
structure per call, assembled in code — measured 0.0 schema violations against 18.0,
6 of 6 complete blocks against 1 of 7, and 4 of 4 passing against 0 of 4, for 5.3
calls instead of 2 and 80% more output tokens. Here the cost is three extra calls
out of roughly 690 in the pipeline.

**Asking harder does not substitute.** §8 of the same document records that prompts
demanding completeness, warning about placeholders and insisting "there is no later"
did not move budget dilution at all. Structure did.

### What the split costs

The same thing it costs in stage 4: no doctor sees the trade-offs between criteria.
The single most common real tension in an exposé is doctor 1 against doctor 4 —
explaining the jargon costs words, and the summary has a word budget, so full
comprehensibility and clean readability pull against each other inside a fixed
length. Neither doctor can see that it is asking for something the other's criterion
forbids. The reviser is the only agent that sees both, and it is the agent with the
least room, since it gets one pass.

An alternative worth naming and rejecting: let the doctors see each other's reports
and negotiate. That reintroduces serialisation into the one stage where parallelism
is nearly free, and there is no measurement suggesting negotiated critique is better
than reconciled critique. It is a candidate for the experiment list, not for the
default.

---

## 9.4 One revision, against all of it

The exposé author receives its own draft and **all** doctor reports at once, and
revises once. Not one revision per doctor, and not a loop.

One pass rather than four sequential ones because sequential revision has a
characteristic failure: each pass optimises for the criterion in front of it and
degrades the ones already satisfied, and with no acceptance test the last criterion
wins. That is the same shape as the repair loop in `05-model-behaviour.md` §5 that
turned 89 validation errors into 126 and saved the result anyway. The lesson stated
there is the governing one: **a self-correction step needs an acceptance test, or it
is just another way to introduce errors.**

So the revision is accepted only if:

- every word-count band in the schema still holds
- no synopsis key is removed (later layers cite them; removing `s09` breaks every
  reference to it) — keys may be added, and additions renumber nothing
- the coverage report does not get worse: no plot loses its last carrying sentence,
  no sentence becomes newly orphaned
- no blocking objection is silently dropped; each is resolved or refused in writing
- the result is not a stub

Rejection keeps the pre-revision draft. A worse exposé that addressed more criticism
is still a worse exposé.

---

## 9.5 Boundary check before the second descent

Decidable from data, so no model touches it:

- every synopsis key matches `^s[0-9]{2,3}$`, has a `function` from the closed list,
  and a unique `story_time_rank`
- `synopsis_word_count` is within 450–550 and matches the actual count
- every word-count band holds for `jacket_copy`, `plot_summary_short`,
  `plot_summary_long`
- **every synopsis key is claimed by at least one plot's `covers_synopsis`** — the
  `s17` orphan, mechanised
- **every plot claims at least one synopsis key**
- `screen_time_share` across all plots sums to 1.0 within tolerance — the 1.20 that
  survived every check until someone summed it
- every place in `setting.places` resolves to a location entity, and every location
  entity appears in `setting.places`
- every dimension in `state_dimensions` is one of the closed vocabulary, and the set
  covers every dimension used by any event state change
- `ending_first.ending` is consistent with the terminal events of every plot — this
  one is only *partly* decidable, and the decidable part is that the plots' declared
  `outcome` values are all reflected

That last item is where the measured "impossible ending" failure would have been
caught: a run ended with a character in a place her own state model could not hold,
and every referential check passed, because each check asked whether a claim was
admissible and none asked whether it was true of this story. The mechanical version
here is narrow and does not catch the general case. **The general case is what §13's
rubric is for, and it needs a reader.**
