# The event layer

The first layer above scenes, and **the first layer in this project ever to be rubric-scored**
apart from scenes. There is no baseline: the V0–V5 tables in `docs/13` and `docs/14` are all
scene layer, and the handshake records that *"events, plots, profiles, exposé and root have
never been rubric-scored."*

So the number below is an absolute measurement, not a comparison. "2.89" means *the rubric
says this is a little below acceptable*, not *worse than something else*.

New to the scoring? [`docs/rubric-explained.md`](../rubric-explained.md) explains the
dimensions and why 3 means "acceptable" rather than "good".

---

## What an event is

A run of consecutive scenes that function as one unit of story — a confrontation and its
aftermath, a plan and its execution. Each node records, for every entity involved, a **state
triple** per register: what it entered in, what changed, what it left in.

```
  224 scene nodes
        │
        ├─ 1. segment    boundaries only, in overlapping windows, stitched deterministically
        ├─ 2. compose    one agent per event, from the scenes' state changes
        ├─ 2b. reconcile prose rewritten from the finished triples
        └─ 3. verify     neighbour pairs, seeing only the nodes — never the screenplay
```

The chain `exit(N) = entry(N+1)` is the property the layer exists to provide. Everything
downstream depends on being able to ask what state a character was in at a point in the story
without re-reading the film.

## Build 1 — the numbers

55 events over 224 scenes, 59 minutes. Coverage 224/224, no gaps, no duplicates.

| | |
|---|---|
| Events | 55 (1–14 scenes, mean 4.1) |
| State triples | 303 |
| Register entries | 1,224 |
| Outward effects | 131 |
| **Rubric mean (12 events, 3 judges)** | **2.89** |
| **Gate cleared** | **0 of 12** |

| Dimension | | | Dimension | |
|---|---|---|---|---|
| V5 mental simulation | **2.33** | | V1 change reality | 2.67 |
| A internal consistency | 2.42 | | V4 outward effect | 3.17 |
| D schema compliance | 2.42 | | E, G, R1 | 3.25 |
| B, V2, V3 | 2.58 | | C specificity, R2 | 3.67 |

Specificity is the one dimension that holds. Everything to do with *state* — consistency,
mental simulation, the triple itself — sits below acceptable.

## What went wrong, and whose fault it was

The judges returned 48 feedback items. Sorted by where the defect originates:

| Cause | Items |
|---|---|
| **Schema** (my design) | 26 |
| **Event layer** (the prompt/pipeline) | 16 |
| **Scene layer** (below) | 6 |

**More than half were caused by the schema.** That is the useful finding: the layer was
mostly not failing at judgement, it was filling a contract that permitted — sometimes
required — bad answers.

Quantified mechanically over all 55 events:

| Defect | Count |
|---|---|
| Placeholder entries (`"Not stated."`, `"unchanged"`) | **440** |
| Registers simply missing rather than marked unchanged | **900** |
| `unchanged_because` that concedes the change it denies | 32 |
| `participants` disagreeing with the triple key set | 7 |
| Quoted dialogue outside the one field allowed interiority | 3 |

**440 placeholder entries is the headline.** `entry: "Not stated."` breaks
`exit(N) = entry(N+1)` for every event that follows, which makes the layer's whole reason for
existing unenforceable. The compose prompt named this exact anti-pattern in its own text and
the model produced it 440 times anyway — *instructions repair local fields, structure repairs
global properties*, demonstrated again.

### Three defects were in my code, not the model's output

Recorded separately because they are the ones I would otherwise have blamed on the model:

1. **`brief()` dropped the scene layer's `uncertain` flags** before the composer ever saw
   them. The composer then asserted the flagged readings as fact. A doubt laundered into a
   claim purely by my projection function.
2. **The verifier was blind to the fields that were broken.** Its projection passed only
   `entry`/`exit`, never `change` or `unchanged_because` — so the unchanged/exit
   contradictions, the layer's most common defect, were structurally invisible to the check
   meant to police them.
3. **The placeholder regex did not know the word "unchanged"**, which was 36 of 42 entries in
   one event.

### And one correction to this module's own docstring

A judge found, and I verified, that **48 of 224 scene nodes cite `ev-XXX` ids** inside
`minds` and `sets_up` — inherited from an earlier 18-event artifact via the scene prompt's
`event_hint`. The event layer is therefore *not* purely bottom-up: it induces from scenes that
had already been told roughly where the boundaries were, and those ids belong to a different
segmentation than the one produced here. The docstring claimed otherwise and now says this.

## What the verifier found that was *not* a defect

The verify pass reported 51 state breaks across 54 joins. Most are real, but the largest
cluster is not an error: Neo exits `ev-003` seized and interrogated and enters `ev-004` waking
in his own bed. Checked against the screenplay — `sc-020` is the interrogation room, `sc-021`
is his apartment. **The film deliberately leaves open whether the interrogation happened.**
The verifier found a genuine property of the narrative, which is what it is for. 31 of 54
joins are clean.

One judge made the same point from the other side: an event confidently misreads a character
with glowing white eyes as "a latent observer" when he is Agent Smith. That is wrong, and it
is *affirmative evidence the layer is reasoning from its inputs rather than recalling the
film* — worth protecting while the error is fixed.

## Build 2 — what changed

Every fix below traces to a specific judge finding.

**Schema**
- `moved` boolean, so changed/unchanged is machine-readable. Build 1 expressed it four
  different ways across four nodes; a boolean can only be read one way.
- **All seven registers required**, fill-or-mark-unchanged. Build 1 let 900 go missing.
- `safety` register added — the axis that duplicate `knowledge` registers were smuggling.
- `affects_outside` typed into `enables` / `blocks_or_costs` / `off_screen_reactor`, because
  as a free list it delivered only whatever came to mind.
- `turns_on_entity` required: the thing an event turns on must itself have a state. Build 1
  turned an event on a bulging wall demoted to a location string.
- `carried_uncertainty`, so scene-level doubt travels instead of being promoted to fact.

**Prompt**
- The previous event's exit states are supplied as context, so `entry` has something to be.
- `reading` constrained to the character's mind, not commentary about the document.
- Non-person entities explicitly in scope: a wall, a phone line, a ship.
- Externalisation rule reconciled with the state registers — record them by their evidence.

**Pipeline**
- Deterministic chain repair: placeholder entries filled from the previous event's exits.
- Duplicate entity and register keys merged, conflicts recorded rather than hidden.
- `participants` derived from the triples instead of asserted alongside them.
- **New reconcile stage**: prose rewritten *after* the triples are final, so a summary can no
  longer contradict its own record.
- A `lint` report counting all six mechanical defect classes, so a judge never again spends a
  rubric pass on something a machine can decide.

**Below the layer** — the scene mind pass was gated on a fixed 150-word threshold, which
opened on 22% of scenes (measured: 49 of 224, matching `docs/13` exactly). Every scene in one
judge's batch fell under it, so there was no mental material to build V5 on. V5 replaces the
threshold with a signal that transfers — ≥2 speaker cues, or one cue above the work's own 75th
percentile — and opens on 93 of 224. The scene layer is being rebuilt with it.

## Honest limits

- **12 of 55 events scored, one film, one judge model.** Stratified by event size with a fixed
  seed, but small.
- **No baseline.** Whether 2.89 is good or bad for a first build of a layer is not something
  this measurement can answer.
- The judges are the same model family that produced the nodes.
- Build 2 has not been scored yet. Every claim about it above is a description of an intended
  fix, not a measured improvement.

## What is published here, and what is not

`blind_eval.json`, `protocol.json`, `sample_nodes.json` and the feedback *classes* are in this
folder. The judges' full feedback is **withheld**: to justify a finding they quote the
screenplay, up to twenty consecutive words, which makes their output as useful for auditing as
it is unpublishable. Same rule as everywhere else in this project — structure travels, source
text does not. Caught by the pre-commit sweep, not by design.
