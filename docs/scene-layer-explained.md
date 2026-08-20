# The scene layer experiments, explained

*For a reader who has just arrived. No background assumed — if you have written a bit of
code and can read a table, that is enough.*

---

## First: a naming collision you will hit immediately

This project uses the string **V1** to mean two completely different things, and nothing in
the repository warns you. Both appear in the same tables.

| When you see | In this context | It means |
|---|---|---|
| **V0 … V5** | scene layer experiments | one of six **experimental conditions** — six different ways of prompting the model, compared against each other |
| **V1 … V5** | event layer rubric | one of five **scoring dimensions** — the questions a judge asks about an event node |

They are unrelated. Scene-variant V5 is a prompting strategy; event-rubric V5 is the question
*"is the mental simulation present at both endpoints?"*.

To keep them apart, this documentation now writes scene conditions as **`scene-V4`** and event
dimensions by name (**"outward effect"**) wherever both could appear. The underlying ids in
the code are unchanged, because renaming them would invalidate every score in `docs/13` and
`docs/14`.

---

## What the scene layer does

Take a screenplay. Split it into scenes. For each scene, have a language model produce a
structured **scene node**: who is present, what happens, what changes, what people want and
conceal, what it sets up.

That node is the atom of everything above it. If it is wrong, every layer built on it inherits
the error, and no amount of cleverness higher up recovers it. Which is why this layer got six
experimental conditions and everything else got none.

## How the experiments were run

**One thing changes at a time.** All six conditions use the same model, the same fifteen
scenes, the same output schema. Only the *prompt* differs. That is what makes the comparison
mean anything: if condition B beats condition A, the prompt is the reason, because nothing
else moved.

**The sample is frozen.** Fifteen scenes, chosen once to spread across the film and across
scene lengths, then never changed. Re-picking would make new numbers incomparable with old
ones — a mistake that is easy to make and impossible to undo.

**Two tiers of measurement:**

- **Tier 1 — mechanical.** Cheap checks a program can run: does every named character actually
  appear in the scene? Does at least one quoted piece of evidence occur verbatim? Are there
  changes where before equals after? This is a *floor*, not a quality judgement. It catches
  nodes that are broken, not nodes that are shallow.
- **Tier 2 — the rubric.** A separate model reads the real scene and scores six dimensions
  0–5. This is what decides. See [`rubric-explained.md`](rubric-explained.md).

---

## The six conditions

### `scene-V0` — the baseline
The production prompt as it already existed. Gives the model **~100,000 characters** of
screenplay as context for each scene.

### `scene-V1` — cut the context
Three changes at once, the biggest being: stop sending 100,000 characters. Send **the scene
plus its two neighbours**.

The reasoning is a measurement, not a hunch. The median scene in this screenplay is **45
words** — about 0.01% of that giant context window. The model was being handed the entire film
to describe a paragraph.

### `scene-V2` — split facts from minds
`scene-V1` showed that cutting context anchors a node to its own scene. But a scene read in
isolation *cannot* tell you why a character conceals something — that information is not on the
page, it accumulated over the scenes before it.

So two passes, because the two jobs want opposite context:

| | Pass A — what is observably there | Pass B — what is going on in minds |
|---|---|---|
| **sees** | the scene alone | pass A's facts, plus surrounding scenes |
| **may infer?** | no | yes, and must label what is inference |

### `scene-V3` — fix a hindsight leak
`scene-V2`'s pass B could see the *following* scene. So when it wrote "this sets up…", it was
not predicting — it was reading the answer and copying it. `scene-V3` cuts the forward view, so
the node knows only what a writer at that point in the story would know.

### `scene-V4` — gate the mind pass
Running pass B on every scene turned out to be actively harmful: it wrecked **calibration**,
because a twelve-word establishing shot with nobody in it got the same psychological analysis
as a confrontation.

So pass B only runs on scenes over **150 words**.

### `scene-V5` — a gate that transfers
`scene-V4`'s threshold is a number fitted to *this* screenplay. Measured: 150 words opens on
**22% of these 224 scenes**, because the median scene is 45 words. On a screenplay whose median
scene is 200 words, the same threshold opens on nearly everything and the gate stops gating.

**A constant tuned on fifteen scenes of one film is the definition of what will not transfer.**

So `scene-V5` gates on a signal that means the same thing anywhere:

- **≥ 2 speaker cues** — an exchange. Someone wants something from someone else, which is when
  inner life becomes legible at all.
- **1 cue, and long for *this* work** (its own 75th percentile) — a monologue or a reaction
  scene, in a film where that is substantial.

Measured here: this opens on **93 of 224 scenes** instead of 49.

---

## What actually happened

### The published scores were wrong

The original evaluation reported `scene-V4` at 4.16 and `scene-V5` at 4.06, both clearing the
quality bar of 4.0.

That evaluation had a flaw its own author recorded: **one judge, who could see which condition
it was scoring, and who had helped design the conditions.** A blind re-run was ranked as the
top priority for exactly this reason.

The blind re-run was done. Three independent judges, condition labels shuffled, key withheld:

| Condition | Published | **Blind** |
|---|---|---|
| `scene-V4` | 4.16 | **3.63 – 3.88** |
| `scene-V5` | 4.06 | **3.66 – 3.74** |
| `scene-V1` | 4.02 | **3.51 – 3.57** |

**Every condition drops ~0.4, and none clears the bar.** The claim that the bar had been
cleared does not survive blinding.

There is a lesson here worth more than the scores: *a measurement taken by someone who knows
which arm they are looking at, and who wants one of them to win, will drift in that direction
without anyone lying.* Blinding is cheap. It should have been done first.

### `scene-V4` and `scene-V5` cannot be told apart

Across every blind round, they score within noise of each other. Judge variance between rounds
moved a single condition's mean by up to **0.24** — larger than the gap between them.

**Any difference under about 0.25 in this project is not a finding.**

### What did not work: adding more machinery

Three attempts to improve on `scene-V4` by adding structure. All lost:

| Attempt | Result |
|---|---|
| A separate "knowledge layer" between the text and the analysis | **−0.44** |
| Narrower processing windows | **±0.00** |
| A second pass adding depth on top of `scene-V4` | **−1.07** |

The pattern is consistent: **every attempt to append more analysis cost more in proportion and
accuracy than it gained in insight.** Two of the three forced content onto scenes that could
not carry it — a twelve-word shot receiving four paragraphs about someone's psyche.

### What did work: a bigger model

The one change that helped was leaving the pipeline completely alone and putting a larger
model behind it. Not one line of code changed — the model name is a command-line argument.

| | 27B model | 397B model |
|---|---|---|
| Overall | 3.51 | **3.89** |
| **Emotional intelligence** | 2.93 | **3.80** |

**+0.38, and it replicated** on a second, entirely separate set of fifteen scenes (+0.378,
p = 0.017; pooled over both, p = 0.002). It is the only result in this line of work that
reproduced.

The cost is real: **4.7× the compute time, four GPUs instead of one, 224 GB of weights.**

---

## The finding worth carrying to other projects

Three structural changes lost. One model swap won, and won on the exact dimension the
structural changes were built to improve.

**The bottleneck was the model, not the scaffold.** Before building more pipeline, it is worth
checking whether the pipeline is what is limiting you.

Two caveats so this is not over-read:
- One screenplay, one judge model family, fifteen scenes per sample.
- The model comparison is clean because *only* the model changed. The three scaffold
  comparisons each changed several things at once, so "the scaffold does not help" is weaker
  evidence than "this bigger model does".

## Where the numbers live

| | |
|---|---|
| [`rubric-explained.md`](rubric-explained.md) | the six dimensions, and what 0–5 mean |
| [`ornith/`](ornith/) | the model comparison and its replication |
| [`cognitino/results.md`](cognitino/results.md) | the three scaffold attempts that lost |
| [`events/`](events/) | the layer above this one |
| `docs/13`, `docs/14` | the original, non-blind scores — **superseded**, kept for provenance |
