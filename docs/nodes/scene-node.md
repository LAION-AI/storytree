# The scene node

*What it is, what is in it, and what real ones look like. No background assumed.*


> **About the […] marks.** These are real node values, not rewritten ones. Where a node
> quoted the screenplay for eight or more consecutive words, the run is elided and marked
> `[…]` — the project's rule is that no such run reaches a published file. Nothing else is
> altered. `tools/check_no_leak.py` enforces this over every file git tracks, and
> `tools/redact_source_spans.py` does the eliding.


---

## In one paragraph

A screenplay is prose written for people. A **scene node** is the same scene rewritten for a
machine: who was in the room, what happened, what changed as a result, and — where the scene
supports it — what the people in it wanted, feared and concealed. One node per scene. The
1998 shooting script of *The Matrix* has 224 scenes, so it has 224 scene nodes.

It is the bottom layer of the StoryTree and the only one measured directly against the
screenplay. Everything above it — events, plots, character profiles — is built from these
nodes rather than from the script, so an error here is inherited by everything above it.

## Why not just keep the screenplay?

Three reasons, in increasing order of importance.

**You cannot query prose.** "What did Neo know at this point?" has no answer you can look up
in a screenplay. In a node it is a field.

**Prose does not separate fact from reading.** A scene says a character is silent. Whether
that silence is fear, calculation or contempt is a judgement — a real one, that a director
must make, but a different kind of thing from "she is silent". The node keeps the two apart:
observations in one place, readings in another, clearly labelled.

**The screenplay is copyrighted; a structure is a different object.** The nodes record what
happens, not the words it happens in. Every published artifact in this project is checked so
that no run of eight or more consecutive words from the source survives into it. That is why
the examples on this page show nodes only, never the scenes they came from.

---

## The fields

Fourteen fields in four groups. Every example below is a real value from one of the three
nodes shown later on this page.

### 1. Where and who — the frame

| Field | What it holds | Real value |
|---|---|---|
| `scene_id` | the handle. Stable across the project; every layer above points at these. | `sc-029` |
| `location` | as named in the scene heading, not reinterpreted | `ROOM` · `NEO'S APARTMENT` · `DARK STREET` |
| `time_of_day` | `NIGHT`, `DAY`, or `UNSPECIFIED` | `UNSPECIFIED` — all three examples, because the headings do not say |
| `present` | everyone physically in the scene | `["MORPHEUS", "NEO", "TRINITY", "DARK FIGURE"]` |
| `objects_that_matter` | the props a later scene depends on | red pill · blue pill · circular mirrored glasses · cracked, burgundy-leather chairs |

Two things to notice.

**`present` lists a person twice under two descriptions** — `MORPHEUS` and `DARK FIGURE` are
the same man, and the scene is built on the reveal. The node records the screenplay's own
naming rather than tidying it, and folding the two together is the job of a later
canonicalisation step that knows the reveal has happened. Tidying it here would delete the
reveal.

**`objects_that_matter` is a judgement about the future.** From `sc-012`:

```jsonc
["Neo's PC and its screen",
 "the messages on the screen",
 "the door with its series of locks and chain",
 "Baudrillard's Simulacra and Simulations, hollowed out to hide computer disks",
 "an envelope of money (\"two grand\")",
 "Dujour's black leather motorcycle jacket and its pins",
 "a small white rabbit pin"]
```

The rabbit pin is four words in the screenplay and decides where Neo goes next. The bed, the
chair and the window are not listed at all. The test is *does a later scene depend on it* —
not *is it visible*.

### 2. What happened — the observations

| Field | What it holds | Real value |
|---|---|---|
| `summary` | what occurs, in the node's own words | see below |
| `what_changes` | **the field the layer exists for** | see the next section |

`sc-029`, the pill scene, compressed to five sentences:

> In a decaying room, a dark figure at the windows turns to reveal himself as Morpheus, who
> welcomes Neo and sits him down. Morpheus probes why Neo has come, reframing Neo's
> hacker-hero worship into a deeper, felt conviction that 'something is wrong with the world.'
> When Neo names 'The Matrix,' Morpheus defines it as an illusory world 'pulled over your
> eyes' […] then admits it cannot be explained, only seen. He offers Neo a final choice
> between a blue pill, which ends the story and returns him to comfortable ignorance, and a
> red pill, which means staying to learn the truth. Neo swallows the red pill, and Morpheus
> tells him to follow.

Compare `sc-024`, twenty-three words of screenplay, and the summary is honest about being
about nothing:

> The car carrying Neo moves through a dark, wet urban environment […] The scene is a brief
> transitional shot of the vehicle in motion, with no dialogue and no other visible
> characters.

**Proportionality is a scored dimension.** A node that gives a transitional shot the same
weight as the pill scene is wrong even if every sentence in it is true.

### 3. What it means — the readings

| Field | What it holds | Real value |
|---|---|---|
| `minds` | per character: wants, feels, shows, conceals | see the next section |
| `dramatic_function` | what the scene does *for the story* | see below |
| `sets_up` | what it makes possible later | pointers forward |
| `connects_back` | what earlier scene it depends on | pointers back |

**`dramatic_function` is not a second summary.** It names the scene's job. `sc-029`:

> It converts Neo's vague, lifelong dread into a named enemy and then into an irreversible,
> self-chosen commitment, so that the catastrophe of unplugging feels earned rather than
> inflicted — the scene's job is the crossing of the threshold, not the consequences past it.

The last clause is the useful part: it says what the scene is **not** doing. A scene that tried
to also deliver the consequences would be doing two jobs badly.

**`sets_up` and `connects_back` are what make this a graph.** Each entry names a target and
says what the dependency *is* — a bare id would be an edge with no content. From `sc-029`:

```jsonc
"sets_up": [
  "ev-006: Neo swallowing the pill as the act that lets the crew trace and unplug him.",
  "ev-007 / ev-008: The irreversible 'no going back' — his body must be recovered and
   rebuilt because there is no return to his old life.",
  "ev-009: The payoff of 'you have to see […]' — Morpheus now owes Neo the
   visible truth he could not be told."
],
"connects_back": [
  "sc-028: Trinity's advice licenses Neo's direct, unguarded answers to Morpheus.",
  "sc-028: Neo's pounding heart carries into this scene's physical nervousness at the
   threshold."
]
```

Two entries point at `sc-028` for **different reasons** — one about permission to speak, one
about a body still reacting. Collapsing them into one edge would lose the second.

> **A wrinkle worth knowing.** Some `sets_up` entries cite `ev-` ids, which means the scene
> layer saw an event artifact from an earlier run. So the layer is *not* purely bottom-up, and
> anything that treats it as independent evidence for the event layer is overstating its
> case. Stated here rather than buried, because it affects how the numbers should be read.

### 4. Honesty about limits

| Field | What it holds | Real value |
|---|---|---|
| `uncertain` | what the scene genuinely does not settle | see below |
| `_mind_pass` | whether the interiority pass ran, and why | `ran: 2 speakers — an exchange` |

`sc-012` raises three things and settles none of them:

```jsonc
["Whether the on-screen messages are sent by a real external party or are a hallucination.",
 "Whether Neo's \"feeling of unrealness\" is caused by the messages, exhaustion, or
  something else.",
 "Whether Dujour's white rabbit pin is a deliberate signal meant for Neo or a coincidence
  he interprets as one."]
```

All three are questions the *film* is deliberately not answering yet. An empty `uncertain` —
as in `sc-029`, which settles what it raises — is a claim, not an omission.

> **Not every node carries all fourteen fields.** `sc-024` has seven: a twenty-three word
> transitional shot has no `objects_that_matter`, no `dramatic_function` worth asserting and
> nothing uncertain. Absent is different from empty, and both are different from wrong.

---

## `what_changes` — the field the layer exists for

A scene is not a list of things that occur. It is a place where **something becomes different**,
and the rest of the story depends on which side of that difference we are on.

Each entry has four parts:

```jsonc
{
  "who":      "NEO",
  "axis":     "knowledge",     // what kind of thing changed
  "before":   "A legendary hacker meeting his idol, expecting a straightforward encounter.",
  "after":    "Confronted with the reality that his lifelong unease points to a hidden,
               enslaving system he can no longer un-know.",
  "evidence": "..."            // what in the scene shows this
}
```

**`axis`** is the dimension along which something moved: `knowledge`, `location`, `condition`,
`trust`, `status`, `resolve`. It matters because a character can change in several ways at
once, and a downstream reader usually cares about one of them.

**The distinction that decides whether this field is worth anything:**

```
not a change   door: closed → open                (that is the action, restated)
not a change   before: "not explicitly stated"    (an unstated before is not a before)
a change       neo.trust: provisional → staked    (later scenes depend on which side we are on)
```

This is also the hardest thing to get right. Across every configuration tested in this
project, "change reality" has been the weakest scored dimension — around 2.6 to 3.4 out of 5.

---

## `minds`, and why it does not always run

`minds` records, per character: what they **want**, what they **feel**, what they **show**,
and — the part that carries the most information — what they are **concealing and from whom**.

Naming an emotion is not the bar:

> **weak** — "Trinity is tense during the escape."
> **strong** — "She treats compliance as a purchase of seconds, not a surrender: the slowness
> of her hands is calculation."

**The gate.** Running this pass on every scene made results *worse*, not better: a twelve-word
establishing shot with nobody in it received the same psychological analysis as a
confrontation, which wrecked the score for proportionality. So it is gated on whether the
scene contains an exchange:

- **two or more speaker cues** — someone wants something from someone else, which is when
  inner life becomes legible at all; or
- **one cue, and long for this particular screenplay** (its own 75th percentile) — a monologue
  or a reaction scene.

`_mind_pass` records the decision so it is auditable:

```
ran: 2 speakers — an exchange
skipped: 0 speaker(s), 23 words — below this work's threshold
```

In *The Matrix*, this opens on **102 of 224 scenes**. A scene with no `minds` is usually not an
omission — it is the gate saying there was nothing to read.

> **Why not just a word count?** An earlier version used "150 words or more". That number was
> fitted to this screenplay, whose median scene is 45 words, and would open on nearly
> everything in a screenplay whose median is 200. A constant tuned on one film is the
> definition of what does not transfer.

---

## Three real examples

All three are from *The Matrix*, exactly as the pipeline produced them. The full JSON is in
[`example-scene-nodes.json`](example-scene-nodes.json).

### A. A scene rich in interiority — `sc-029`

Four people, three changes, three minds read.

```jsonc
{
  "scene_id": "sc-029",
  "location": "ROOM",
  "time_of_day": "UNSPECIFIED",
  "present": ["MORPHEUS", "NEO", "TRINITY", "DARK FIGURE"],

  "summary": "In a decaying room, a dark figure at the windows turns to reveal himself as
              Morpheus, who welcomes Neo and sits him down. Morpheus probes why Neo has
              come...",

  "what_changes": [
    { "who": "NEO", "axis": "knowledge",
      "before": "A legendary hacker meeting his idol, expecting a straightforward encounter.",
      "after":  "Confronted with the reality that his lifelong unease points to a hidden,
                 enslaving system he can no longer un-know." }
  ],

  "minds": [
    { "who": "MORPHEUS",
      "wants": "To get Neo to name his own dissatisfaction and then commit to the truth —
                to convert a fan meeting into a genuine, self-chosen recruitment.",
      "feels": "A controlled, patient certainty. He is not testing a hypothesis; he is
                executing a ritual he has done before, and the certainty is the point —
                he already knows Neo will say yes, so his pressure can be gentle." }
  ],

  "_mind_pass": "ran: 2 speakers — an exchange"
}
```

Note what the `minds` entry does that a summary cannot: it separates **what Morpheus is doing**
(applying gentle pressure) from **why the pressure can be gentle** (he already knows the
answer). That is a directorial reading, and it is filed as one.

### B. A crowded scene — `sc-012`

Five present, three speakers, three minds. Also **three entries in `uncertain`** — the scene
raises things it does not settle, and the node says so instead of guessing.

### C. The floor — `sc-024`

One entity, one change, **no `minds` at all**, and `_mind_pass` reading
`skipped: 0 speaker(s), 23 words`.

This is the system behaving correctly. A 23-word transitional shot has no inner life to read,
and the node does not manufacture one. **Restraint on small scenes is harder to get than depth
on large ones**, and it is the behaviour most easily lost when a pipeline is pushed to produce
more.

---

## How a node is checked

Two tiers, and they answer different questions.

**Tier 1 — mechanical, cheap, run on every node.** Does every named character actually appear
in the scene? Does at least one quoted piece of evidence occur verbatim in it? Are there
changes where `before` equals `after`? This is a **floor**: it catches nodes that are broken,
not nodes that are shallow.

**Tier 2 — the rubric.** A separate model reads the real scene and scores six dimensions from
0 to 5: fidelity, completeness, specificity, change reality, emotional intelligence,
calibration. This is what decides. See [`rubric-explained.md`](../rubric-explained.md), and be
aware that **3 means "acceptable", not "good"**.

---

## Glossary

| Term | |
|---|---|
| **node** | one structured record about one thing. A scene node describes one scene. |
| **layer** | all the nodes of one kind. The scene layer is all 224 scene nodes. |
| **axis** | the dimension a change happens along — knowledge, location, trust |
| **register** | the event layer's name for the same idea, from a fixed list of seven |
| **gate** | a rule deciding whether an expensive step runs at all |
| **schema** | the machine-checkable shape a node must have. A field the schema forbids cannot be written, which is stronger than asking. |
| **rubric** | the list of questions a judge scores a node against |
| **tier 1 / tier 2** | mechanical checks / judged quality |
| **speaker cue** | a character name on its own line, marking who speaks next |
| **blind evaluation** | judges score without knowing which system produced what |

## Where to go next

| | |
|---|---|
| [The StoryTree structure](../storytree-structure.md) | how this layer fits with the others |
| [The event node](event-node.md) | the layer directly above |
| [How scoring works](../rubric-explained.md) | the six dimensions, and what 0–5 mean |
| [The scene layer experiments](../scene-layer-explained.md) | six configurations, what worked and what did not |
