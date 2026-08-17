# 4 · Stage 2 — event boundaries by sliding window

Stage 1 produced 224 independent readings of 224 scenes. Stage 2 asks the first
question that requires more than one scene at a time: **which scenes are part of the
same happening?**

Three passes. Windows of 10 at stride 5, then windows of 25 at stride 20, then one
consolidation that sees everything. 44 + 11 + 1 = **56 calls** for a 224-scene
feature. The output is a map `{event_id: [scene_ids]}` in which the scene lists are
permitted to be non-contiguous.

---

## 4.1 What an event is

An event is a unit of happening. A party. An earthquake. A battle. Two friends
walking. A household waking up.

It is not a scene, and the codebase is already explicit about this. `EVENTS_SCHEMA`
in `narrativeforge/schemas.py` carries the sentence: *"Events and scenes are NOT
identified with one another: one event may span several scenes, one scene may
contain several events."* Nor is it a plot beat — a plot beat is a *function* an
event performs, and functions are stage 4's business. Nor is it a location or a time
slice, though both are strong evidence.

The working test: an event is the largest span of story time over which you would
answer "what is happening?" with one noun phrase. The party is one event whether it
takes three scenes or thirty. The two friends walking is one event even though
nothing structural occurs in it, because "two friends walking" is what is happening.
An earthquake that runs under six intercut scenes is one event with six member
scenes, not six events.

This matters for granularity, and granularity is a measured failure. The forward
Qwen arm produced 22 events for a feature, which the evaluation calls "defensible in
itself — events are not scenes", and then finds the split is wrong in a specific
way: **three separate events for one investigation** (`detects` → `traces` →
`decodes`) while the refusal and reversal that the brief calls "the plot the others
are in service of" gets two. Three verbs about one activity is one event under the
test above. That failure is a definition failure, not a counting failure, which is
why the definition is stated here rather than a target number.

---

## 4.2 Why boundaries cannot be read off adjacency

The tempting implementation is a segmentation: walk the scene list, decide at each
boundary whether the event continues, done in 223 cheap decisions. It is wrong for
three separate reasons, and the third is the one that makes it unfixable.

**Intercutting.** Scenes 1 and 3 may be one party while scene 2 cuts to a car
outside. Under segmentation, scene 2 forces a boundary and the party becomes two
events that a later layer has to notice are the same party. Screenplays intercut
constantly, and the more competent the writing the more they do it.

**Scenes are not atomic with respect to events.** A scene can carry the end of one
event and the start of another. Segmentation assumes each scene has exactly one
label; the schema does not.

**The relation is a clustering over an ordered sequence, not a partition of it.** The
object being recovered is a set of scene *sets*, with a strong locality prior and
real long-range exceptions — a framing device whose two halves sit at scenes 4 and
211, a promise and the payoff it names. Any algorithm whose state is "the current
event" cannot express that, because the current event is not a well-defined thing.

**What code should do anyway.** Location, time-of-day and roster are computed
deterministically at stage 0 and 1 and are strong evidence. They are given to the
window agents as a *hint block*, not as a decision, for the reason §11 gives in
general: a hint that is decidable in code should be computed in code, and a
judgement that is not decidable in code should not be dressed as one. The same
location on two different days is not one event; two locations in one intercut
often are.

---

## 4.3 Why not one call over the whole scene layer

Because that has already been measured, on this exact task, and it failed.

**Measured** (`docs/02-forward-pipeline.md`): *"The events stage does not segment.
For a 224-scene work it produced 12,363 tokens — formally valid and far too
coarse."* Formally valid is the important half. Nothing objected. The artifact
passed, and the layer had not done the job.

That result is the local instance of the general finding in
`docs/05-model-behaviour.md` §1: **models have a per-call output budget and they
divide it rather than scaling it.** Requesting one deep structure gave 1 of 1
complete; requesting four gave 2 of 4, two of them hollow, and 41 schema violations
— at the same ~28,000 characters of output in every condition. Asking for more did
not produce more. It produced the same amount spread thinner.

A single call asked to segment 224 scenes is that experiment at n=224.

---

## 4.4 Windowing serves attention, not only speed

This is worth separating carefully, because the two justifications have very
different evidential status.

**The speed argument is straightforward and secondary.** 56 calls, of which 44 are
independent, is a stage that finishes in well under a minute at the measured
aggregate throughput. But stage 2 is roughly 2.5% of the pipeline's estimated
tokens. If speed were the only argument, one big call would be fine.

**The attention argument is the real one, and it is partly inferred.** What is
measured is budget dilution (above) and the 12,363-token non-segmentation. What is
*not* measured anywhere in this corpus is a controlled experiment varying the number
of scenes in a window and observing where the quality of the boundary reading falls
off. The claim that "twenty scenes of attention drift less than two hundred" is an
**assumption**, supported by the two measurements above and by the general shape of
every other result in `docs/05`, but not directly tested. It should be tested, and
it is cheap to test: run pass A at window 10, 25 and 50 on the same script and
compare the pairwise co-membership matrices.

There is a specific mechanism that makes windowing more than a token-count trick,
and it is worth stating because it survives even if the drift claim is wrong.
**A window agent is asked a question it can actually answer.** Given ten scenes it
can hold every one of them in view and say which belong together. Given two hundred
it must compress before it can compare, and compression is exactly the operation
this model is measured to be bad at — the evaluation's summary of the failure is
"structurally strong, atomically unreliable", and boundary induction is an atomic
judgement made two hundred times.

---

## 4.5 The three passes

### Pass A — 44 windows of 10, stride 5

Each agent sees ten consecutive scene nodes (summary, location, time, roster,
`event_hint`) and the script span they cover. It returns a list of proposed events:
for each, a one- or two-sentence description and the member scene ids from within
its window. Member lists may be non-contiguous.

**Stride 5 on window 10 is chosen so that every scene is read by exactly two
windows** (except the first and last five). That is the property the whole pass
exists for: not coverage, which stride 10 would also give, but **two independent
readings of every scene**, from two different neighbourhoods. A scene at the centre
of one window sits at the edge of the other, so the two readings have genuinely
different context.

It also guarantees that every adjacent pair of scenes co-occurs inside at least one
window, so no boundary decision is ever forced by a window edge alone.

The cost is a factor of two in calls, paid on the cheapest stage in the pipeline.

### Between A and B — reconciliation that is not a model's job

Pass A's output is converted in code into a **pairwise co-membership matrix**: for
each pair of scenes seen together by at least one window, do the windows that saw
them agree that they belong to the same event?

Event *names* are ignored here entirely, for the same reason stage 1 tolerates
divergent naming (§3.6): two windows describing the same party as "the Vance
reception" and "the party at the estate" have not disagreed about anything. The
invariant is co-membership, which is name-free.

Three cases fall out, and only one of them reaches a model:

| Case | Handling |
|---|---|
| Both windows put A and B together | accept, in code |
| Both windows keep A and B apart | accept, in code |
| The windows disagree | escalate to pass B |

Connected components under unanimous agreement become provisional events without
any further model involvement. **In the expected case the large majority of pairs
are unanimous**, because most events are contiguous runs in one location, and pass
B is handed a short list of contested edges rather than a corpus. This is
**assumed** — the ratio of contested to unanimous pairs has not been measured and is
the number that determines whether pass B is cheap or is doing all the work.

### Pass B — 11 windows of 25, stride 20

Each agent sees twenty-five consecutive scene nodes, the provisional events from
pass A that overlap its range, and the contested edges within it, marked explicitly
as contested.

Twenty-five is chosen to be larger than any plausible single event but small enough
to keep the answerable-question property of pass A. Stride 20 gives a five-scene
overlap between consecutive B windows, so a dispute sitting at a B boundary is seen
whole by a neighbour.

Pass B does three things pass A structurally could not:

1. **Resolve intercuts wider than ten scenes.** A party running from scene 8 to
   scene 26 with two cutaways is invisible as one event to any window of 10.
2. **Merge over-split events.** The `detects` → `traces` → `decodes` failure is a
   pass-B correction: three proposed events describing one activity, visible as
   three only because no agent ever saw them side by side.
3. **Adjudicate the contested edges** with a strictly larger context than the
   windows that disagreed.

Pass B is *not* asked to name events, assign plots, or write anything beyond the
boundary list and a one-line description. It has one job.

### Pass C — one consolidation, total scope

One agent, seeing pass B's eleven proposals, the one-line summary of every scene,
and the full script.

Pass C exists for the three things no window can do:

1. **Long-range events.** A framing device at scenes 4 and 211. A promise and its
   payoff that are one happening in the story's terms. No window will ever place
   them together because no window contains both.
2. **B-boundary disputes.** Eleven windows produce ten seams.
3. **Global sanity.** Every scene assigned to at least one event; no event with zero
   scenes; the event count not absurd for the length. Most of these are decidable in
   code and belong there (§11) — pass C is handed the *violations*, not asked to
   check for them.

**The obvious objection is that pass C reintroduces exactly the attention problem
windowing was meant to avoid.** It is a fair objection and the answer is that pass
C's *scope* is total but its *input* is small. It reads eleven proposals and 224
one-line summaries, not 224 full scene nodes; the full script is available for
lookup rather than as the working set. That is a few thousand tokens of structure,
not a corpus.

This is a mitigation, not a proof. Pass C is the single call in stage 2 with the
most authority and the least verification, and if stage 2 goes wrong quietly, this
is where. §14 treats it as such.

---

## 4.6 How disagreement is actually resolved

Stated as a rule set, because "the passes reconcile" is not a mechanism:

1. **Unanimous pairwise co-membership is binding** and is applied in code. No later
   pass is asked to revisit it, and no later pass is shown it as a question.
2. **A contested pair is decided by the widest agent that saw both scenes.** Pass B
   overrules pass A within its range; pass C overrules pass B. The justification is
   not authority but evidence: a wider window saw strictly more of the thing being
   judged.
3. **Merges are cheaper than splits and are preferred at equal confidence.** An
   over-merged event is visible downstream — a stage-3 agent handed twenty scenes
   that are two happenings will say so, because it has to write one entry state and
   one exit state and cannot. An over-split event is invisible: two coherent
   half-events look exactly like two events. This asymmetry is a design assumption
   and it is not measured; it is the reason the passes are biased toward merging.
4. **Names are never evidence.** Disagreement is defined on co-membership only.
5. **Nothing is discarded silently.** Every contested pair and its resolution is
   written to the stage-2 artifact with the pass that decided it, so a downstream
   failure can be traced to a boundary decision rather than guessed at.

Rule 3 deserves one more sentence, because it is the place this section is most
likely to be wrong. It assumes stage 3 will notice and report an incoherent event
rather than smoothing it into a plausible paragraph. The measured prior is not
encouraging: the model's strongest dimension is specificity (C = 4.67 mean) and its
weakest is judgement about what belongs (G = 2.33), which is precisely a model that
writes a convincing paragraph about a unit that should not exist. §11 therefore
places a mechanical check here — an event whose member scenes span more than one
location-and-day without an intercut marker is flagged, not trusted.

---

## 4.7 Cost, and what it assumes

| Pass | Calls | Width | Depends on |
|---|---|---|---|
| A | 44 | all independent | all of stage 1 |
| — | 0 | code | pass A |
| B | 11 | all independent | pass A + the code step |
| C | 1 | — | pass B |

**56 calls in three sequential phases, maximum width 44.** Estimated output is on
the order of 112,500 tokens (§12) — an **estimate**, not a measurement, and it
assumes pass A windows return short structured lists rather than prose.

The window and stride numbers are arithmetic on 224 scenes: window 10 at stride 5
gives 43 grid-aligned windows plus a tail window, and window 25 at stride 20 gives
10 plus a tail. A different scene count changes both. The summary table in
`WHITEPAPER-SWARM.md` records 57 rather than 56; the difference is how the tail
window is counted and neither figure is load-bearing.

The genuinely unverified quantities in this stage are two, and both are cheap to
measure on a single script:

- **The contested-pair fraction after pass A.** If it is small, pass B is a cleanup
  and the design works as described. If it is large, pass B is doing the real work
  and pass A is an expensive prior, which would argue for starting at window 25.
- **Whether window size affects boundary quality at all.** If the co-membership
  matrices at window 10, 25 and 50 agree, the attention argument in §4.4 is wrong
  and stage 2 should be one pass. That would be a good result to find, and it is one
  experiment.
