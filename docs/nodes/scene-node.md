# The scene node

*What it is, what is in it, and what real ones look like. No background assumed.*

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

A scene node has fourteen fields. They fall into four groups.

### 1. Where and who — the frame

| Field | |
|---|---|
| `scene_id` | `sc-029`. Stable across the whole project; every layer above points at these. |
| `location` | as named in the scene heading — `ROOM`, `HEART O' THE CITY HOTEL` |
| `time_of_day` | `NIGHT`, `DAY`, or `UNSPECIFIED` when the script does not say |
| `present` | everyone physically in the scene |
| `objects_that_matter` | things that matter to the plot — a phone, a wall, a pill. Not every prop: the ones a later scene depends on. |

### 2. What happened — the observations

| Field | |
|---|---|
| `summary` | what occurs, in the node's own words |
| `what_changes` | **the most important field** — see below |

### 3. What it means — the readings

| Field | |
|---|---|
| `minds` | per character: what they want, feel, show and conceal |
| `dramatic_function` | what this scene does *for the story*, as distinct from what happens in it |
| `sets_up` / `connects_back` | what it makes possible later; what earlier scene it depends on |

### 4. Honesty about limits

| Field | |
|---|---|
| `uncertain` | what the scene genuinely does not settle |
| `_mind_pass` | whether the interiority pass ran here, and why — see *gating* below |

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
