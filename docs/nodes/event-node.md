# The event node

*What it is, what is in it, and what real ones look like. No background assumed.*


> **About the […] marks.** These are real node values, not rewritten ones. Where a node
> quoted the screenplay for eight or more consecutive words, the run is elided and marked
> `[…]` — the project's rule is that no such run reaches a published file. Nothing else is
> altered. `tools/check_no_leak.py` enforces this over every file git tracks, and
> `tools/redact_source_spans.py` does the eliding.


---

## In one paragraph

A screenplay is a list of scenes. A **story** is not. A raid, the killing that ends it and the
arrival of the people who were really hunting you are *one thing that happened*, told across
four scenes. An **event node** is that one thing: a run of consecutive scenes recorded as a
single unit, with — for every person and object involved — the state it **entered** in, what
**changed**, and the state it **left** in.

*The Matrix*'s 224 scenes group into roughly 50 events. Which is not a coincidence: it is
about how many things a two-hour film can afford to have happen.

## Why the layer exists at all

One property, and almost every design decision below exists to protect it:

> **exit(event N) = entry(event N+1)**

If that chain holds unbroken, you can ask *"what did this character know at this point in the
story, and how badly hurt were they?"* and get an answer by looking it up — without re-reading
the film. If it breaks anywhere, every layer above inherits the break, and a character can be
recorded as unharmed in one place and dying in another with nothing between them.

A scene node answers *what happened here*. An event node answers *where does that leave
everyone*.

---

## The fields

### The frame

Every row below is a real value from `ev-001`, the opening raid.

| Field | What it holds | From `ev-001` |
|---|---|---|
| `event_id` | the handle | `ev-001` |
| `scene_ids` | member scenes, in order | `["sc-001", "sc-002", "sc-003", "sc-004"]` |
| `title` | a name a person can hold in their head | *Trinity Kills the Cops; the Agents Arrive* |
| `summary` | what happened, with its causal joints | see below |
| `action` | the same, stripped to what is done | see below |
| `participants` | every entity carrying a state triple | Trinity · BIG COP · the cops · Agent Smith · Agent Brown · LIEUTENANT · Agent Jones |
| `locations` | where it plays | `HEART O' THE CITY HOTEL (Room 303)`, `(exterior)` |
| `boundary_reason` | why it starts and stops here | see below |

**`participants` is derived from the triples, not asserted.** The composer used to write
this list itself, and in an early build the list and the triples disagreed in **every single
node** — a name in one and not the other. It is now computed from the triples after they are
final, so the two cannot drift apart.

### `title`, `summary`, `action` — the same event at three grains

They are not redundant. Each answers a different question, and downstream code picks the one
it can afford.

**`title`** — for a human scanning fifty of them:

> Trinity Kills the Cops; the Agents Arrive

**`summary`** — what happened *and how it hangs together*. Note the causal joints: *closes
on*, *then*, *at the moment*, *simultaneously*:

> A four-officer raid on Room 303 of the fire-gutted Heart O' The City Hotel closes on Trinity
> at her keyboard: she submits to the guns, then, at the moment the Big Cop reaches to cuff
> her, she moves inhumanly fast and kills the entire squad, ending as the only one standing.
> Simultaneously, three suited Agents arrive outside, override the Lieutenant's territorial
> protest, and reveal that his two units are already dead; Brown then enters the hotel while
> Smith breaks off alone for the alley.

**`action`** — the same event with the interpretation taken out. What a camera would record:

> The police breach and take Trinity under guns; she complies, then converts the cuff into a
> massacre and walks away as the sole survivor. Outside, the Agents arrive, correct the
> Lieutenant's belief that his men are winning, and split to pursue — Brown through the lobby,
> Smith toward the alley.

The pair is a **cheap consistency check**. `summary` may explain; `action` may not. If
something appears in `action` that is not photographable, or if the two describe different
events, the node is wrong in a way that is visible without reading the film.

### `boundary_reason` — why the cut is here

The field that stops segmentation from being arbitrary. It must name the **question** the
event answers, and say that the next scene asks a different one:

> The raid-and-fight unit ends when Trinity has wiped out her captors and the agents split to
> hunt her; the next scene shifts the story to Trinity's escape call, answering a different
> question (how she gets out) than the one just resolved (who wins the room).

That is the working definition of an event in this project: **a run of scenes that answers one
question.** When the question changes, the event ends. Compare `ev-002`, which ends where
*"will Trinity escape"* gives way to *"who is Neo"*.

---

## The substance

| Field | What it holds | From `ev-001` / `ev-002` |
|---|---|---|
| `state_triples` | **the core** — see the next section | 7 entities × 7 registers |
| `turns_on` + `turns_on_entity` | the pivot, and whose it is | see below |
| `affects_outside` | what this changes for things not in the event | 3 sub-fields, below |
| `carried_uncertainty` | what the scenes left unsettled | 5 items in `ev-001` |

### `turns_on` — the moment the event hinges on

One event, one pivot. The discipline is that it must be a **moment**, not a summary of the
event, and it must belong to a named entity.

`ev-001`, and note it is not the obvious choice:

> The pivot is the moment the Big Cop reaches with [...]: the contact the squad reads as the
> finish of a routine arrest is the trigger she was waiting for, inverting the raid in one
> instant.
>
> `turns_on_entity`: **Trinity**

"Trinity kills the cops" would have been the obvious pivot. The node instead picks the instant
where **two people read the same gesture differently** — one man finishing an arrest, one woman
starting a fight. That divergence is the event.

`ev-002` picks a physical impossibility rather than a psychological one:

> The impossible rooftop leap — Trinity committing fully to a gap that should kill her, and
> Agent Brown duplicating it exactly — which shatters the ordinary physics of the chase and
> reveals the pursuers as something other than men.

Both share a shape: the pivot is where **the audience's model of the world has to be
revised**, not where the most happens.

### `affects_outside` — three questions, not a list

Asked as one open field, this returned whatever came to mind. Split into three, each one has
an answer that can be checked. From `ev-001`:

| Sub-field | The question | |
|---|---|---|
| `enables` | what is now possible that was not | *converts the story from a contained police bust into a pursuit: Trinity is now a fugitive who has just killed a squad, and the Agents — with superior knowledge and a divided hunt — are set…* |
| `blocks_or_costs` | what is now impossible, and what it cost | *costs the police their entire Room 303 squad and their illusion of control, and strips the Lieutenant of any claim that his operation was handling the target* |
| `off_screen_reactor` | who reacts to this without appearing in it | *whatever command sent the Agents must now reckon with a squad wiped out and a target loose* |

`off_screen_reactor` is the one that earns its place. `ev-002` uses it to record the betrayal
that has already happened and that nobody on screen can yet name:

> The unseen informant (Cypher) has, by this escape's end, delivered a verified name to the
> Agents — his betrayal is now operationally live though no one on-screen yet names him.

A reader querying "when does Cypher's betrayal begin to bite?" gets an answer from an event
Cypher does not appear in.

### `carried_uncertainty` — doubt with a return address

Each item carries `what` and `from_scene`, so a doubt can be traced to the scene that raised
it. From `ev-001`:

```jsonc
[
  { "what": "Whether Trinity surrenders willingly or is setting a trap — her slow
             compliance is ambiguous.",                        "from_scene": "sc-001" },
  { "what": "What Trinity was doing on the computer before the cops entered.",
                                                               "from_scene": "sc-001" },
  { "what": "Whether any cop besides Trinity survives the gunfire.",
                                                               "from_scene": "sc-003" }
]
```

The rule is that an event may **carry** a doubt but not **resolve** it. The first item is the
interesting one: whether Trinity's compliance is real is exactly the question the pivot turns
on, and the node declines to settle it — because the scene declines to.

An earlier build stripped this field before the composer ever saw it, and the composer then
asserted the ambiguous reading as fact. That was a bug in my projection function, not in the
model: a doubt laundered into a claim by code.

---

## The state triple

For each entity, across seven **registers**:

`physical` · `positional` · `knowledge` · `relational` · `emotional` · `status` · `safety`

A **register** is a dimension a thing can change along. A character can be physically
unharmed, positionally trapped, and relationally betrayed all at once — three registers, three
different answers, and a downstream reader usually wants exactly one of them.

Each register holds:

```jsonc
{
  "moved": true,                          // did this register change?
  "entry": "The dominant authority of the raid — kicks the door, barks orders,
            believes he has won.",
  "change": "From procedural certainty at the head of a clean arrest to the first
             casualty of it...",
  "exit": "Dead — the first and most total casualty of the gap between what the squad
           believes and what Trinity is.",
  "unchanged_because": null,              // required when moved is false
  "evidence_scene": "sc-003"              // which member scene shows this
}
```

Three rules make this useful rather than decorative, and **all three are enforced by the
schema or by code, not by asking the model nicely** — because asking was tried first and did
not work:

1. **`exit` must follow from `entry` plus `change`.** A reader can check the arithmetic. If it
   does not follow, one of the three is wrong.
2. **When `moved` is false, `exit` must be *identical* to `entry`**, and
   `unchanged_because` must say why. Asserting a new state on a register you just said did not
   move is a contradiction — and it was the most common defect in earlier builds.
3. **`entry` is never "not stated."** It comes from the previous event's exit. An early build
   wrote a placeholder 440 times, which broke the chain for every event that followed.

### `reading` — the one interior field

Everything else in the node must be **photographable or audible**. Speech is recorded as what
was communicated, never as quoted lines. `reading` is the single exception, and it is for the
character's mind:

> *"She treats compliance as a purchase of seconds, not a surrender: the slowness of her hands
> is calculation."*

Not commentary about the screenplay — "Neo is the unwitting subject of a test" is a note about
the document, not a reading of Neo.

---

## Two real examples

From *The Matrix*, exactly as produced. Full JSON in
[`example-event-nodes.json`](example-event-nodes.json).

### `ev-001` — the opening raid

Four scenes (`sc-001`…`sc-004`), seven entities.

**Title:** *Trinity Kills the Cops; the Agents Arrive*

**`turns_on`** — the pivot, and note that it is not the obvious one:

> The pivot is the moment the Big Cop reaches with [...]: the contact the
> squad reads as the finish of a routine arrest is the trigger she was waiting for.

The obvious pivot would be "Trinity kills the cops". The node instead identifies **the moment
the two sides' readings of the same gesture diverge** — one man completing an arrest, one woman
starting a fight. That is the kind of judgement the layer is for.

**A moved register:**

```jsonc
"BIG COP": {
  "status": {
    "moved": true,
    "entry":  "The dominant authority of the raid — kicks the door, barks orders,
               believes he has won.",
    "change": "From procedural certainty at the head of a clean arrest to the first
               casualty of it...",
    "exit":   "Dead — the first and most total casualty of the gap between what the
               squad believes and what Trinity is.",
    "evidence_scene": "sc-003"
  }
}
```

**An unmoved register**, from the same event:

```jsonc
"Trinity": {
  "physical": {
    "moved": false,
    "entry": "Seated at the keyboard, undiscovered, hands on the keys.",
    "exit":  "Seated at the keyboard, undiscovered, hands on the keys.",
    "unchanged_because": "Her body's position at the keyboard is unchanged at the event's
                          open; the custody shift is recorded under status."
  }
}
```

Entry and exit are identical, as the rule requires, and the reason **points at the register
where the change actually lives**. That cross-reference is what keeps a "no change" from
reading as an oversight.

**`affects_outside`** — three separate questions, because as a free-form list it returned
whatever came to mind:

| | |
|---|---|
| `enables` | converts the story from a contained police bust into a pursuit |
| `blocks_or_costs` | costs the police their entire squad and their illusion of control |
| `off_screen_reactor` | whatever command sent the Agents must now reckon with a squad wiped out |

**`carried_uncertainty`** — the scenes flagged doubts, and the event carries them instead of
quietly resolving them:

> *"Whether Trinity surrenders willingly or is setting a trap — her slow compliance is
> ambiguous."* — from `sc-001`

An earlier build dropped these before the composer ever saw them, and the composer then
asserted the flagged reading as fact. That was a bug in the code, not the model: a doubt
laundered into a claim by a projection function.

---

## How an event is built

```
  224 scene nodes
        │
        ├─ 1. segment    propose boundaries only — cheap, and cheap to redo
        ├─ 2. scaffold   compute the roster and change ledger — no model involved
        ├─ 3. compose    one agent per event
        ├─ 4. reconcile  rewrite the prose from the finished triples
        └─ 5. verify     compare neighbouring events — seeing only nodes, never the script
```

Four choices worth explaining, each of which came from a measured failure.

**Boundaries before content.** A bad boundary found after writing fifty full nodes is
expensive; found before, it costs one cheap call. The stitching is then done by ordinary code,
so coverage tiles **by construction** — every scene in exactly one event — rather than because
the model was asked to be careful.

**The scaffold is computed, not requested.** Before any model call, code derives from the
member scenes: the entity roster, which scenes each entity appears in, every recorded change in
order, and the mind material already found. The model receives a **filled roster rather than a
blank form**. This exists because earlier builds asked the model to name its own entities and
cite its own evidence, and judges found a police unit handed the ship operator's state — a
bookkeeping failure on facts the scene layer already had right.

**The composer sees three overlapping views**: the scaffold, the scene nodes in order, and the
**actual scene text**. With an explicit precedence when they disagree: screenplay, then scene
nodes, then its own reading.

**The verifier is denied the screenplay.** It compares two adjacent nodes and only the nodes.
That is deliberate — it puts the verifier in the same position as everything downstream, which
will also only ever have the nodes. A verifier that could re-read the script would find
defects nobody downstream can be hurt by, and miss the ones they can.

### What the verifier found that was not a defect

It once reported that a character exits one event seized and interrogated, and enters the next
waking in his own bed. Checked against the screenplay: those really are consecutive scenes.
**The film deliberately leaves open whether the interrogation happened.** The verifier found a
genuine property of the storytelling — which is what it is for.

---

## How it is measured

Fourteen dimensions, 0 to 5, scored blind by three independent judges reading the real scenes.
Nine are general — internal consistency, referential integrity, specificity, schema
compliance, dramatic competence, psychological plausibility. Five belong to this layer:

| | The question |
|---|---|
| **Change reality** | are the changes real transitions, or the action restated? |
| **Externalisation** | is everything photographable or audible? |
| **State triple completeness** | does `exit` follow from `entry` plus `change`? |
| **Outward effect** | does the node say what this changes for things outside it? |
| **Mental simulation** | is each character's mind recorded at both endpoints? |

Alongside the rubric runs a **lint**: every defect a machine can decide, counted and
normalised per register slot. A check a machine can run is a check a human should never spend
a rubric pass on.

**Results so far are in [`docs/events/`](../events/), including a null result reported as
one.** The current build is running; nothing about it is claimed here until it has been
measured.

---

## Glossary

| Term | |
|---|---|
| **event** | a run of consecutive scenes that function as one unit of story |
| **register** | a dimension a thing changes along; seven fixed ones |
| **state triple** | entry → change → exit for one entity on one register |
| **scaffold** | the part computed from the layer below before any model is asked |
| **roster** | the closed list of entities an event may record. Closed means: no additions. |
| **segmentation** | deciding where one event ends and the next begins |
| **reconcile** | rewriting prose *after* the triples are final, so it cannot contradict them |
| **lint** | mechanical defect checks, no judgement involved |
| **canonicalisation** | folding `NEO`, `Neo` and `Neo (V.O.)` into one entity |

## Where to go next

| | |
|---|---|
| [The StoryTree structure](../storytree-structure.md) | how this layer fits with the others |
| [The scene node](scene-node.md) | the layer below, which this is built from |
| [Event layer results](../events/) | three builds, what each measured |
| [How scoring works](../rubric-explained.md) | the dimensions, and what 0–5 mean |
