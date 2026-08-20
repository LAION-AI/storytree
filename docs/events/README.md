# The event layer

*For a reader who has just arrived. No background assumed.*

---

## Read this first: two things are both called "V1"

If you have looked at the scene layer documentation, you have seen conditions named V0 through
V5. **The V1–V5 on this page are unrelated to those.** It is an unfortunate collision in the
project's own naming, and it will confuse you if nobody says so.

| When you see | Where | It means |
|---|---|---|
| **V0 … V5** | scene layer | six **experimental conditions** — different ways of prompting, compared against each other |
| **V1 … V5** | *this page* | five **scoring dimensions** — questions a judge asks about an event node |

Scene-V5 is a prompting strategy. Event-V5 is the question *"is the character's mental state
recorded at both the start and the end?"*. Same letters, nothing in common.

On this page the five scoring dimensions are written **by name**, never by number, so the
collision cannot bite. New to the scoring scale itself?
See [`rubric-explained.md`](../rubric-explained.md) — especially why **3 means "acceptable",
not "good"**.

---

## What an event is, and why the layer exists

A screenplay is a list of scenes. But a story is not: a chase, a capture and the interrogation
that follows are *one thing that happened*, told across five scenes.

An **event** is a run of consecutive scenes that function as one unit of story. The event node
records, for every entity involved — people, but also a wall, a phone line, a ship — a **state
triple**:

```
   entry  ──►  change  ──►  exit
```

across seven registers: physical, positional, knowledge, relational, emotional, status, safety.

The point of the whole layer is one property:

> **exit(event N) = entry(event N+1)**

If that chain holds, you can ask *"what did this character know at this point in the story?"*
and get an answer without re-reading the film. If it breaks anywhere, everything downstream
inherits the break. Almost every design decision below exists to protect that chain.

## How it is built

```
  224 scene nodes
        │
        ├─ 1. segment    propose boundaries only, in overlapping windows
        ├─ 2. compose    one agent per event, writing from the scenes' state changes
        ├─ 2b. reconcile rewrite the prose from the finished triples
        └─ 3. verify     check neighbouring pairs — seeing only the nodes, never the script
```

Two choices worth explaining:

**Boundaries before content.** Segmenting is a separate, cheap stage. A bad boundary is cheap
to discover and cheap to redo; a bad boundary discovered *after* writing fifty-five full nodes
is not. The stitching is then done by ordinary code, not by the model, so coverage tiles by
construction — every scene in exactly one event, no gaps, no overlaps — rather than because
the model was asked nicely.

**The verifier is not allowed to see the screenplay.** It compares two adjacent nodes and only
the nodes. That is deliberate: it puts the verifier in the same position as everything
downstream, which will also only ever have the nodes. A verifier that could re-read the script
would find defects nobody downstream can be hurt by, and miss the ones they can.

## How it is evaluated

Same method as the scene layer:

1. Twelve of the fifty-five events, stratified by size (1 to 7 scenes), fixed seed.
2. **Three independent judges**, four events each.
3. Each judge reads the **actual scenes** from the screenplay via character offsets, so
   accuracy is checked against the source rather than against plausibility.
4. Fourteen dimensions scored 0–5. Nine are general (internal consistency, referential
   integrity, specificity, schema compliance, dramatic competence, psychological plausibility,
   and so on). Five are specific to this layer:

| Dimension | The question |
|---|---|
| **Change reality** | Are the recorded changes real transitions, or the action restated? |
| **Externalisation** | Is everything photographable or audible, rather than narrated interior? |
| **State triple completeness** | Does every entity have entry, change and exit on every register — and does `exit` actually follow from `entry` plus `change`? |
| **Outward effect** | Does the node say what this event changes for things *outside* it? |
| **Mental simulation** | Is each character's mental state recorded at both endpoints? |

5. **The bar**: mean ≥ 4.0 *and* no single dimension below 3.0.

Judges were also asked for something beyond scores: **structured feedback naming the field, the
failure pattern, the fix, and — critically — whether the defect originates in this layer, the
scene layer below, or the schema itself.** A defect caused by the layer below will not be fixed
by improving this one, and knowing which is which is what makes the feedback actionable.

---

## Build 1 — results

**This is the first time any layer above scenes has ever been scored in this project.** The
handshake records that events, plots, profiles, exposé and root had never been rubric-scored.

**So there is no baseline.** "2.89" means *the rubric says this sits a little below
acceptable*. It does not mean "worse than something else" — there is nothing to be worse than.

| | |
|---|---|
| Events built | 55, covering 224/224 scenes, no gaps or duplicates |
| Build time | 59 minutes |
| State triples | 303 · register entries 1,224 |
| **Rubric mean** (12 events, 3 judges) | **2.89** |
| **Bar cleared** | **0 of 12** |

**Weakest first:**

| Dimension | Score |
|---|---|
| Mental simulation | **2.33** |
| Internal consistency | 2.42 |
| Schema compliance | 2.42 |
| Referential integrity · Externalisation · State triple completeness | 2.58 |
| Psychological plausibility · Change reality | 2.67 |
| Outward effect | 3.17 |
| Dramatic competence · anti-fake · fidelity | 3.25 |
| **Specificity** · reconstruction | **3.67** |

Read that shape rather than the average. **Specificity holds** — the nodes are about *these*
scenes, not generic. **Everything to do with state fails** — consistency, the triple itself,
mental simulation. The layer is writing about the right material and recording it badly.

## What went wrong, and whose fault it was

48 feedback items, sorted by origin:

| Cause | Items |
|---|---|
| **The schema — my design** | **26** |
| The event layer's prompt and pipeline | 16 |
| The scene layer below | 6 |

**More than half were caused by the schema.** That is the useful result: the layer was mostly
not failing at judgement, it was faithfully filling in a contract that *permitted* — sometimes
required — bad answers.

Counted mechanically across all 55 events:

| Defect | Count |
|---|---|
| **Placeholder entries** (`"Not stated."`, `"unchanged"`) | **440** |
| **Registers simply missing** rather than marked unchanged | **900** |
| `unchanged_because` that concedes the change it denies | 32 |
| `participants` disagreeing with the actual entity list | 7 |
| Quoted dialogue outside the one field permitted to hold it | 3 |

**The 440 placeholders are the headline.** `entry: "Not stated."` breaks
`exit(N) = entry(N+1)` for every event that follows — the one property the layer exists to
provide. The prompt names this exact anti-pattern in its own text, with an example, and the
model produced it 440 times anyway.

That is this project's most-repeated lesson arriving again: **instructions repair local fields;
structure repairs global properties.** If a value must never appear, a schema has to forbid it.
Asking does not work.

### Three of the defects were in my code, not the model's output

Separated out because they are the ones I would otherwise have blamed on the model:

1. **The projection function dropped the scene layer's uncertainty flags** before the composer
   ever saw them. The composer then asserted the flagged readings as fact. A doubt laundered
   into a claim purely by my own code.
2. **The verifier was blind to the fields that were broken.** It passed only `entry` and `exit`
   to the checking agent — never `change` — so the most common defect class in the layer was
   structurally invisible to the check meant to police it.
3. **The placeholder detector did not know the word "unchanged"**, which accounted for 36 of 42
   entries in one event.

### And a correction to the module's own documentation

A judge found — and I verified — that **48 of 224 scene nodes cite event ids** inherited from
an older 18-event artifact. So the claim in the code that this layer is built purely
"bottom-up" from scenes was **wrong**: the scenes had already been told roughly where the event
boundaries were, by a *different* segmentation than this one produces. The docstring now says
so.

## What the verifier found that was *not* a defect

The verifier reported 51 state breaks across 54 joins, which looks alarming. The largest
cluster is not an error.

Neo **exits** one event seized and interrogated, and **enters** the next waking in his own bed.
Checked against the screenplay: those really are consecutive scenes. **The film deliberately
leaves open whether the interrogation happened.** The verifier found a genuine property of the
storytelling — which is what it is for. 31 of 54 joins are completely clean.

A judge made the same point from the other direction: one event confidently misreads a
character with glowing white eyes as "a latent observer" when he is in fact the antagonist.
That is wrong — and it is *affirmative evidence the system is reasoning from its inputs rather
than recalling the famous film from memory*. Worth protecting while the error gets fixed.

---

## Build 2 — what changed and why

Every change below traces to a specific judge finding.

**Schema — making bad answers impossible rather than discouraged**

| Change | Because |
|---|---|
| `moved` boolean per register | Build 1 expressed changed-vs-unchanged four different ways in four nodes. A boolean can only be read one way. |
| All seven registers required | 900 went missing rather than being marked unchanged. Missing is indistinguishable from overlooked. |
| New `safety` register | Duplicate `knowledge` registers were smuggling a second axis, and it was almost always exposure to danger. |
| `affects_outside` typed into three named slots | As a free-form list it delivered only whatever came to mind — one item, or none of the useful kinds. |
| `turns_on_entity` required | One event turned on a wall giving way, but the wall had been filed as a *location string*, so the pivot of the event carried no state at all. |
| `carried_uncertainty` | So a scene's recorded doubt travels instead of being silently promoted to fact. |

**Prompt**
- The previous event's exit states are now supplied, so `entry` has something to *be*.
- The interiority field is constrained to the character's mind, not commentary about the script.
- Non-person entities explicitly in scope.

**Pipeline — deterministic repairs, no model call**
- Placeholder entries filled from the previous event's exits, and marked as chained.
- Duplicate entity and register keys merged, with conflicts **recorded rather than hidden**.
- `participants` derived from the triples instead of asserted alongside them.
- **A new reconcile stage** rewrites the prose *after* the triples are final — so a summary can
  no longer contradict its own record, which Build 1 did.
- **A lint report** counting all six mechanical defect classes. Every one of those was found by
  a judge reading nodes by hand; none of them needs judgement to detect. A check a machine can
  run is a check a human should never spend a rubric pass on.

**Below this layer** — the scene mind pass was gated on a fixed 150-word threshold, which opens
on only 22% of scenes here. Every scene in one judge's batch fell below it, so there was simply
*no mental material* for this layer to build "mental simulation" from — which alone caps that
dimension regardless of anything done here. The scene layer is being rebuilt with the gate that
transfers (see [`scene-layer-explained.md`](../scene-layer-explained.md)), opening on 93 of 224.

---

## What is next, in order

1. **Rebuild scenes with the transferable gate**, then rebuild events on top. *(running)*
2. **Re-score Build 2** against the same rubric, same method. The honest comparison needs the
   same judges' successors on the same twelve events.
3. **Check whether the lint counts actually fall.** 440 placeholders and 900 missing registers
   are now mechanically counted, so the fixes either move those numbers or they do not.
4. **Fix the scene-layer defects the judges surfaced** — one scene merges two units across a
   cut, and uncertainty flags need to survive into this layer rather than being dropped.
5. **Then the layers above**: plots, entity profiles, exposé, story root. None has ever been
   scored.

## Honest limits

- **12 of 55 events, one film, one judge model family.** Stratified with a fixed seed, but small.
- **No baseline exists**, so "2.89" cannot be called good or bad for a first build — only
  measured against the rubric's own anchors.
- The judges belong to the same model family that produced the nodes. A shared blind spot would
  be invisible to this design.
- **Build 2 has not been scored.** Everything in the Build 2 section is a description of an
  intended fix, not a measured improvement. It will be measured before it is claimed.

## What is published here, and what is not

`blind_eval.json`, `protocol.json`, `sample_nodes.json` and the feedback *classes* are in this
folder. The judges' full feedback is **withheld**: to justify a finding they quote the
screenplay, up to twenty consecutive words, which makes their output as useful for auditing as
it is unpublishable. Structure travels; source text does not.
