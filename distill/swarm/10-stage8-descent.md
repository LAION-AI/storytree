# 10 · The second descent

Stages 1 through 8 went up. This one comes back down.

The tree now exists and — this is the whole point of the inversion — it was induced
from the scenes rather than imposed on them. The plots came from what the events
turned out to be about. The entity list came from who was actually in the scenes.
The root and the exposé were written last, over a structure that had already been
read. Nothing above a scene was guessed before the scenes were read.

So the second descent rewrites the two lower layers with the tree in hand: **stage 9
rewrites the events, stage 10 rewrites the scenes.** These are the only two stages
that are strictly serial with respect to each other, because a scene agent needs its
parent event in final form and an event agent needs the plots in final form. Within
each stage everything is again concurrent.

---

## 10.1 Stage 9 — the event rewrite

Each event agent receives its own stage-3 draft, the member scene nodes from stage 1,
the consolidated plot list, the unified entity dictionary, and the script.

**What it may change.** The event's entry state, its state trajectory, its exit
state, its participant list, its causal links to other events, and — the field that
changes character between the two passes — its plot membership. In stage 3 that
field held a *speculation* ("this probably belongs to whatever the antagonist thread
turns out to be"). Here it holds a commitment: one primary plot, zero or more
secondary plots, each named by id.

**What it may not change.** The event boundaries. Which scenes belong to which event
was fixed in stage 2 by three passes of reconciliation and consolidated once; a
stage-9 agent that could re-cut boundaries would silently invalidate the plot
induction that was built on them, and would do so one event at a time with no agent
in a position to see the collision. If a boundary is wrong, that is a stage-2 defect
and it fails the stage-8→9 check (§11), not something an event agent patches
locally.

The rewrite is worth the calls because stage 3's drafts were written against an
unknown superstructure. An event that speculated "this is about trust" and turns out
to sit on the antagonist plot has an entry state written for the wrong question.

---

## 10.2 Stage 10 — the scene rewrite, and what a scene node finally is

Each scene agent gets exactly four things: **one scene's text**, **its parent event
in final form**, **the finished superstructure** (root, exposé, plots, entity
profiles, the event graph), and the **script**. It produces the leaf node of the
whole graph.

### Beats

A beat is the smallest unit that ends in a state change. Not a line, not an exchange
— a unit of interaction after which something about the world is different. The
existing validator already encodes two rules about them, and they carry over
unchanged: a scene with no beats is an error (`G18`), a scene where no beat carries
a change is an error, and beats inside one scene may not run backwards in story time
(`G14`). The last one exists because a scene's patch is the concatenation of its
beats' ops in scene order, and the fold in `narrativeforge/timeline.py` replays them
to produce `world_state(T)`. A beat list that runs backwards produces a world state
that is wrong in a way nothing downstream can detect.

Every beat therefore carries its changes as patch ops against the entity profiles
written in stage 6 — which is what makes the profiles' nested, addressable shape
load-bearing rather than decorative.

### Per-character mental simulation

The contract already exists. `narrativeforge/transitions.py` defines what a mental
simulation must contain, and stage 10 does not get to write a thinner one. Per
character, per unit:

- `entering_state` and `leaving_state` — where this person is *in themselves* at
  each end.
- `perception` — seven channels (sight, sound, touch, smell, taste, interoception,
  proprioception) plus `attention`, which is explicitly *what they are failing to
  notice*. Two characters in one room do not perceive the same room.
- `appraisal` — value at stake, valence on a bipolar scale, arousal, the
  self-conscious emotion named precisely, the moral reading *in their terms, not the
  author's*, and the somatic marker that arrives before any thought does.
- `social_norms` — the rules actually in force here, how present others would judge
  the act, how *absent* others would (the village, the dead, the institution), what
  standing is at risk, and where two norms in force contradict each other.
- `theory_of_mind` — one tower per other entity that matters, to three degrees:
  what A believes about B; what A believes B believes about A; what A believes B
  believes A believes. Plus `accuracy`: **where this model of the other is wrong and
  what the error will cost.** The schema's own comment is the argument — a theory of
  mind that is always correct produces no drama — and the grader in `score_transition`
  flags `tom_with_error == 0` as a gap for exactly that reason.
- `urges` — cravings, physical needs, what they consciously want from this moment,
  and what they are actually pursuing and would deny.
- `impairments` — six channels (physical, medical, magical, chemical, coercive,
  cognitive) plus the net effect on what they are capable of here.
- `deliberation` — the framing (usually where the real error is), at least two
  options weighed with predicted outcome and cost, the reasoning in *this character's
  own idiom*, and their known unknowns.
- `control` — **felt versus expressed**, the reason they differ, the leakage that
  escapes the control anyway, and the impulse that was inhibited.
- `trajectory` — at least two phases, each with a perceivable trigger. An entity
  identical at the end of a unit and at the start did not participate in it.

The scene rubric raises the bar above the transition schema in one specific place:
the full model is required at **scene start, scene end, and at every beat carrying
an important state change** — not just at the unit's two ends. Start-and-end-only
scores a 3 on S2, because the moment where the change actually happens is precisely
the moment being summarised away.

`control` deserves separate emphasis because it is the field the prose leaves depend
on. Dialogue lives in the gap between felt and expressed; the leakage — the hand,
the pause, the word chosen a half-second late — is the only part of an interior
another character can read, and therefore the only part a beat can turn on.

### Per-beat dramaturgical function

This is the field stage 1 could not have written, and it is the reason the second
descent exists at all.

Every beat must name **which plot it serves** and **why it earns its place**. Not a
category word. The scene rubric's S1 anchors make the standard explicit: a 3 is
"names a plot, but the dramaturgical goal is a category word — *raises tension*,
*develops character* — that would fit any change in any scene." A 5 names the
specific plot *and step* the beat discharges, and the function at this position in
the declared structure: setup for a named later payoff, reversal of a named earlier
value, a cost that makes a named later choice harder. The test is deletion — a
reader should be able to remove the beat and say exactly which later thing stops
working.

A beat that cannot pass that test is either mis-assigned or should not be a beat.

---

## 10.3 Why depth becomes producible on purpose here

The argument is not that a bigger schema produces better analysis. It is that the
earlier pipeline demonstrably had the instrument and pointed it at the wrong thing.

The measured evidence is in `docs/07-quality-evaluation.md` §4.1, and it is a clean
split:

- **3 of 3** blind transitions produced a `what_this_exposes` that genuinely revised
  a claim made earlier in the same document. One overturned its own nominated turning
  point; one relocated the scene's emotional centre from the protagonist to the
  operator. The instrument works.
- **0 of 3** honoured the envelope's `on_screen` roster. Two of three forecast the
  wrong *unit* entirely — a sequence where a beat was requested.

Node 9's best line in the whole evaluation — "the scene's tension is not in the
chase, it is in the wait; three seconds of standing still with a phone handset is
more frightening than the stairwell because Trinity's competence becomes useless" —
is a real dramaturgical reading of a scene the model had misidentified. That is what
depth by luck looks like: excellent craft judgement applied to a scene whose function
the agent had to guess at.

Stage 10 removes the guess. The agent is handed the plot the scene serves, the
event it sits inside, the entry and exit state its parent event declares, and the
profiles of everyone in it. When it writes "this beat earns its place because it
discharges `pl-02:st4`", that claim is checkable against data on disk (§11) rather
than being a rhetorical flourish.

## 10.4 Two constraints this stage inherits, and one thing it does not fix

**One deep structure per call.** Budget dilution is the most robust finding in this
project (`docs/05` §1): asking for four psychological analyses in one call produced
two hollow ones and 41 schema violations, at the same total output length as asking
for one. Stage 10 is therefore not one call per scene — it is a scaffold of roughly
six: craft, then one psychology block per character, then the specimen exchange,
then non-mind dynamics, then continuity, assembled mechanically. Measured on the same
scene and model, that took violations from 18.0 to 0.0 and complete blocks from 1-of-7
to 6-of-6, at 5.3 calls and 22,679 output tokens instead of 2 calls and 13,431. The
80% token increase is the difference between unusable and usable, and §12's estimates
are built on the scaffolded shape, not the single-call one.

**The presence sets are closed.** Speaking, present and referable are three different
sets (`presence.py`), and stage 10 may not widen any of them. Someone absent may be
thought *about* — that belongs in another character's theory of mind — and may not
act, speak, or have state moved.

**What this does not fix.** Knowing what a scene is for does not make a 27B model
write a paragraph where it would have written a sentence. EXP-002 is the closest
adjacent measurement and it points the right way but weakly: binding the location
made the analysis about the right conflict, and nine of twelve rubric dimensions rose
(50.0% → 61.7%) — but on one scene of three it cost 35% of the words and all three
dynamics blocks, and arm-wide theory-of-mind depth-3 fell from 10 to 6. Constraint
bought relevance and charged for it in volume. Whether handing the agent the
dramaturgical function buys depth rather than compliance is **untested**, and it is
the first thing a stage-10 run should be measured on (§13).
