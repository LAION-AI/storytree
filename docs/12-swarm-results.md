# The swarm's first two runs, and what they showed

Written 17 August 2026. Companion to [`../distill/WHITEPAPER-SWARM.md`](../distill/WHITEPAPER-SWARM.md)
(the design), [`experiments/EXP-003-swarm-first-run.md`](experiments/EXP-003-swarm-first-run.md)
(the evaluation protocol), and [`../distill/swarm.py`](../distill/swarm.py) (the code).

**One-line summary: the architecture does what it was built to do, the
implementation did not, and the second run is honest but not yet good.**

---

## 1. What was built

The top-down pipeline wrote a story root first and everything else beneath it.
Four rubric passes traced its worst failures to that single decision: nine
entities declared where thirty to forty were needed, then all twenty-two events
at the one location that existed, then an ending placing a character somewhere
her own state model could not hold her. No individual call was wrong. **A thin
superstructure strangles every layer beneath it, silently, while passing every
schema check.**

The swarm inverts the direction. Eight stages, all parallel within themselves:

| Stage | Units | What it does |
|---|---|---|
| 1 | 224 | one agent per scene, blind of any tree |
| 2 | 56 | event boundaries by sliding window, three passes |
| 3 | 37 | one draft per event, each speculating about a plot that does not exist yet |
| 4 | 8 | plots induced from those speculations, one doctor per plot |
| 5 | 4 | canonical entity lists — agents, locations, objects, concepts |
| 6 | 40 | one profile per entity |
| 7 | 1 | the story root, written last |
| 8 | 7 | exposé plus five single-criterion doctors |

Three rules govern the code, each one earned by an earlier failure:

1. **Anything decidable from data on disk is decided in code.** A model asked
   whether a speaker is in a scene will sometimes get it wrong; a function will
   not.
2. **One narrow task per call.** Models divide a fixed output budget across
   whatever is requested rather than scaling to it.
3. **Never grade against a list this apparatus generated.** That measures
   compliance, not correctness.

---

## 2. The first run: 373 of 373 calls succeeded, and it was worthless

18.4 minutes for the whole 224-scene screenplay. Every call returned valid JSON.
The protocol recorded 71 check violations across eight stages, which looked like
a good first result.

It was not a result at all. An evaluation pass found this line:

```python
text = script[scene.start:scene.end] if hasattr(scene, "start") else ""
```

`Scene` carries `start_char` and `end_char`. There is no `start`. So `hasattr`
returned False for all 224 scenes, the guard substituted an empty string, and
**every agent received a blank scene** — writing fluent, schema-valid nodes from
the surrounding script alone.

Measured against the screenplay rather than against anything the harness
authored:

| | |
|---|---|
| Quoted evidence spans occurring in the scene they describe | **5.2%** (10 of 193) |
| Nodes best-matching their own scene by word overlap | **7.1%** (16 of 224) |
| Same, for the third act | **0 of 42** |

A second bug compounded it. `script[:120000]` on a 140,172-character file
**deleted the entire third act** — 42 scenes that no agent ever saw. Nodes were
produced for all of them anyway, and nothing in the protocol recorded the
truncation.

### The lesson, which is not "check your attribute names"

A guard that substitutes empty input for missing input is worse than no guard.
It converts a crash — loud, immediate, unmissable — into a confident wrong
answer that passes every downstream check. Every stage below stage 1 then worked
correctly on fabricated input, which is why the run looked healthy: stage 2
grouped the hallucinated scenes faithfully, stage 5 unified their invented
names, stage 8 wrote a synopsis of a story that had been reconstructed from
recall.

**Absent input must stop the run.** That is now an assertion, not a guard.

---

## 3. The canary

The evaluation suggested a check costing one call per run: give one agent a
deliberately blank scene. Anything it writes is recall, because it has nothing
else to write from.

It fired on its first execution:

```
canary (blank scene): model WROTE ANYWAY — recall is reaching the output
```

That is the whole mechanism of the failure in one line. The model does not
decline when it has no input; it produces something plausible. Given a famous
film, plausible and correct look identical from inside the pipeline.

This check would have caught the bug at scene two rather than after a full run
and an evaluation pass.

---

## 4. The corrected run

Four fixes: read the right attribute and assert non-empty; window the context
around the scene rather than truncating the head of the file; add a
correspondence check; add the canary.

| Stage | Time | Calls | Output tokens | Violations |
|---|---|---|---|---|
| 1 · scenes | 6.3 min | 224/224 | 97,475 | 285 |
| 2 · boundaries | 1.5 min | 56/56 | 32,043 | 1 |
| 3 · events | 4.6 min | 38/38 | 54,553 | 58 |
| 4 · plots | 5.5 min | 8/8 | 5,296 | 1 |
| 5 · entities | 5.5 min | 5/5 | 38,389 | 0 |
| 6 · profiles | 1.7 min | 40/40 | 36,147 | 1 |
| 7 · root | 0.5 min | 1/1 | 741 | 0 |
| 8 · exposé | 0.4 min | 7/7 | 3,140 | 0 |
| **total** | **20.5 min** | **373/373** | **268,087** | |

### Did the fix work? Partly, and the honest number is uncomfortable

| Measure | Run 1 (blank scenes) | Run 2 (real scenes) |
|---|---|---|
| Content-word overlap with the correct scene ≥30% | 6% | **25%** |
| Node matches its own scene better than a random one | — | **56%** |

The fourfold rise shows real text is reaching the model and changing what it
writes. But 25% is weak, and **56% is barely above the 50% a coin would give.**

This is not yet a working reconstruction. It is a pipeline that now receives its
input correctly and still leans heavily on something other than that input.

Two candidate explanations, neither yet tested:

- **Context dominance.** A scene may be 200 characters against a 100,000-character
  context window. The scene is there; it is also 0.2% of what the model is
  reading.
- **Recall.** The canary proves the model will write without input. With a famous
  film it may prefer recall even when input is present.

These are distinguishable by one experiment: run the same pipeline on
`reconstruct/runs/tideline`, a synthetic script no model can have memorised. If
correspondence rises there, the problem is recall. If it does not, it is context
dominance. That experiment is cheap and has not been run.

---

## 5. A fifth measurement bug, in a check written the same day

Stage 1 reported 285 violations, 216 of them "no evidence span occurs in the
scene it describes". Before reporting that as a quality finding, the check
itself was examined.

The schema asked for `evidence: "What in the scene shows this."` — an invitation
to *describe*. The model described:

> "She slowly puts her hands behind her head in response to the BIG COP's command."

The check tested whether that string occurred **verbatim** in the scene. It does
not, because it is a paraphrase, correctly produced as instructed. So 216 of the
285 violations were the harness marking compliant output wrong.

This is the **fifth** instance in this project of the same failure shape:

| # | Check | What it actually did |
|---|---|---|
| 1 | trajectory flatness | tested a field the schema never had |
| 2 | leak detector | tokenised raw JSON, so punctuation blocked every match |
| 3 | grounding | read another schema's field names |
| 4 | arm comparison | averaged over different node counts and compared the results |
| 5 | correspondence | tested for a quote where the schema asked for a paraphrase |

**Every one produced a confident number computed over the wrong thing, and not
one failed loudly.** Three were caught by an independent evaluator, one by
recomputing arithmetic, one by reading the schema next to the check.

The fix here was to change the *contract*, not the check: `evidence` now demands
a verbatim span of at least 25 characters copied from the scene. That makes
correspondence exactly decidable rather than statistically estimated — and the
next measurement will mean something.

---

## 6. What the inversion does prove

Set aside the implementation. The architectural claim was that reading first
prevents the under-declaration that strangles everything below. On that, the
evidence is clear:

| | Top-down | Swarm |
|---|---|---|
| Location entities | **1** | **23** |
| Concept entities | **0** | **13** |
| Events carrying a reversal | 0 of 22 | **11 of 37** |
| Total entities | 36 | 104 |

The top-down run could not move its story to a second location because only one
existed. It could not track the antagonist's humiliation because he had three
state variables. Neither constraint appears here: the layers that need places and
mechanisms have places and mechanisms, because they were derived from scenes that
actually contain them.

**And it is fast.** 20.5 minutes for a 224-scene feature, 373 calls, none failed.
The equivalent top-down run with a feedback loop was estimated at 19 hours. The
difference is not hardware — it is that every stage is parallel within itself.

---

## 7. What is worse than the top-down pipeline

Two things, recorded because a one-sided report is not worth having:

**Stage 5 produces a flat list, not a typed graph.** 104 entities with no
salience ordering, an antagonist split across two identifiers, and alias strings
whose canonical form depends on capitalisation. The top-down run produced 36
typed, patch-addressable entities. Fewer, but usable by the fold.

**Stage 8 stops early.** The exposé reaches roughly two thirds of the story and
stops. The top-down exposé reaches the end, and the only structural difference is
that its schema requires an `ending_first` field. That is a one-line fix and it
demonstrates the general point: schema requirements outperform instructions.

---

## 8. Where this leaves the question of autonomy

Not ready, and for a reason worth stating precisely.

Everything that failed in these two runs failed **silently**. The empty scenes,
the deleted third act, the paraphrase-versus-quote mismatch — none of them
produced an error, a warning, or an anomalous number. The first run reported 71
violations across 373 successful calls and looked like a good day's work.

For an autonomous run over a hundred books, the requirement is not that nothing
goes wrong. It is that when something goes wrong, **a number moves**. The canary
is the first check in this system that satisfies that requirement by
construction: it has no input, so anything it produces is evidence of a specific
failure.

The next three steps, cheapest first:

1. **Run the corrected pipeline on `tideline`**, the synthetic script. Separates
   recall from context dominance and costs one run.
2. **Re-measure correspondence** with the verbatim-span contract, which makes the
   number exact.
3. **Give stage 5 a type system and stage 8 an `ending_first` field** — both
   one-line schema changes that address measured deficits against the top-down
   arm.

---

## Reproducing

```bash
python3 distill/swarm.py reconstruct/runs/matrix --out <dir> --per-endpoint 8
```

Eight vLLM endpoints on ports 8100–8107, one Qwen3.8-27B copy per A100. The
run's own protocol lands at `<dir>/protocol.json` with per-stage timings, token
counts and check violations.

The broken first run is kept at `reconstruct/runs/matrix/swarm_v1_empty_scenes`
as evidence rather than deleted.

*Source screenplays are read for structure and never copied into artifacts;
committed outputs contain structural fields only.*
