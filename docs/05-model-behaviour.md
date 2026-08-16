# Measured model behaviour

Everything here was measured on real runs of this pipeline, not on benchmarks. Where a
prediction was falsified, the prediction is left in so the correction is visible.

---

## 1. Budget dilution — the single most important finding

**Models do not scale effort to the size of the task.** They have a per-call output
budget and they *divide* it.

Measured on GLM-5.2 against the transition schema, varying only how many psychological
analyses were requested in one call:

| Requested in one call | Complete blocks | Carried a trajectory | Schema violations |
|---|---|---|---|
| 1 | 1 of 1 | 1 of 1 | 5 |
| 2 | 0 of 2 | 0 of 2 | 16 |
| 4 | 2 of 4 | 2 of 4 | 41 |

At four, two of the four were hollow: `entity: null`, one field filled out of eleven.
Output length stayed near 28,000 characters in every condition. Asking for more did not
produce more; it produced the same amount spread thinner.

### The fix, and its effect

Ask for **one deep structure per call**, then assemble in code where nothing can
degrade:

```
call 1        craft, situation, interaction, decision  (no psychology at all)
call 2..n+1   ONE psychology block, one per character
call n+2      the specimen dialogue exchange
call n+3      dynamics for non-mind entities
call n+4      continuity
assemble      mechanically, then validate, then repair what still fails
```

Measured on the same scene, same model, same schema:

| | Violations | Words | Complete blocks | Specimen lines | Verdict |
|---|---|---|---|---|---|
| single call | 18.0 mean | 3,014 | 1 of 7 | 0 | 0 of 4 pass |
| scaffolded | **0.0** | 10,895 | **6 of 6** | 7 | **4 of 4 pass** |

Cost: 5.3 calls per scene instead of 2, and 22,679 output tokens instead of 13,431 — an
80% increase in tokens for the difference between unusable and usable.

### The column that matters most

**Specimen lines: 0 versus 7.** The single-call path never once wrote the dialogue.
That is the one artifact that makes the analysis falsifiable — an immaculate character
analysis and a dead scene look identical on paper until somebody speaks. It was the
first thing dropped when the budget got tight, which is exactly the wrong thing to drop.

A pipeline that only counts schema violations would not have noticed.

---

## 2. Hidden reasoning is 83.6% of generated tokens

Measured on a complete forward feature run: 520,211 reasoning tokens against 102,108
visible output. **Of every six tokens generated, one reaches the artifact.**

On a hosted API that is a billing line. On local hardware it is wall-clock: it takes a
full story from ~8.2 hours to ~2.6 hours.

### Three of the obvious switches are silent no-ops

Identical prompt, `max_tokens` 1500, measured against `/apply-template` and real
generations:

| Parameter | Tokens out | Hidden reasoning | Content | Effect |
|---|---|---|---|---|
| *(default)* | 1500 | 5,035 chars | **0** | all budget on thinking |
| `reasoning_effort: "low"` | 1500 | 4,934 chars | **0** | **silent no-op** |
| `reasoning_effort: "minimal"` | — | — | — | silent no-op |
| `reasoning: {"effort": "none"}` | — | — | — | silent no-op |
| `reasoning_effort: "none"` | 194 | 0 | 939 chars | works |
| `chat_template_kwargs: {"enable_thinking": false}` | 157 | 0 | 777 chars | works |

Read the first two rows again: the default burned its entire budget on hidden reasoning
and returned **zero content**, and `"low"` did precisely the same. It is not a mild
reduction — it is the maximum setting, reached through a name promising the opposite.

The cause is in the model's own chat template:

```jinja
{%- set effective_reasoning_effort = 'high' if reasoning_effort is defined
    and reasoning_effort == 'high' else 'max' -%}
```

Everything that is not the literal string `high` maps to **max**. Only llama.cpp's
special case for `"none"` escapes it.

**Generalisable rule: verify a performance parameter by measuring `completion_tokens`.
A parameter that returns HTTP 200 has told you nothing.**

### Does turning it off cost quality?

Tested rather than assumed, on three scenes of the Matrix reconstruction:

```
16 calls · 68,037 tokens · 56.8 min · 20.0 tok/s · reasoning = 0 chars
sc-001  24.3 min  6 calls  0 violations  pass
sc-002  16.0 min  5 calls  0 violations  pass
sc-003  16.6 min  5 calls  0 violations  pass
```

Three of three passed, matching the hosted model with thinking on, and beating it on
theory-of-mind depth for sc-001 (6 towers at depth 3 versus 4).

There is a specific reason to expect this pipeline to survive without hidden reasoning
that would not apply elsewhere: **the scaffold already forces the reasoning to be written
out explicitly into the schema.** Trajectories, theory of mind to three degrees, rejected
alternatives, the specimen exchange. The model is made to think on the page. Hidden
thinking on top is largely duplicated work.

Caveat: three scenes is a small sample, and the structural metrics reward volume.

---

## 3. The `reasoning_content` field is exhaust, not reasoning

Before building explicit transitions, we checked whether the model's own exposed
reasoning trace could serve instead.

| | chars/token | ToM coverage | Trajectory coverage | Craft coverage |
|---|---|---|---|---|
| `reasoning_content` | 0.17–0.95 | none | none | none |
| explicit written transition | 4.18 | full | full | full |

The exposed trace is roughly an 18% summary. It is not a window into the deliberation;
it is a compressed byproduct. If you want reasoning you can inspect, score, or feed
forward, you have to ask for it as output.

---

## 4. Degenerate responses, and why a fake node is worse than a missing one

GLM-5.2 sporadically returns stubs. Observed: a bare `{"ref": "sc-004"}` (9 tokens,
`finish_reason: stop`), an empty content string, and — on the *identical prompt that had
just failed* — a full 10.7k document.

Frequency in our logs: 1 of 13 calls for glm-5.2, 0 of 64 for grok-4.6. Thirteen calls
is not a sample, and a hosted router could be responsible rather than the model. Treat
this as robustness against the transport layer, not as a property of the weights.

The important part is the response. A stub that parses as JSON will pass a schema check
if the schema is permissive, land in the graph, and poison everything downstream. So:

```python
if isinstance(doc, dict) and len(json.dumps(doc)) < 200:
    retry()          # a fake node is worse than a missing one
```

Plus a `_degenerate()` check with a minimum word count for transitions
(`MIN_TRANSITION_WORDS = 400`) and required top-level keys.

---

## 5. The repair loop can make things worse

Observed live:

```
validation: 89 error(s), repair attempt 1
repair patch did not apply: op[8] (add /entities/ch-02/profile/backstory/b04a/text):
    missing key 'b04a'
validation: 89 error(s), repair attempt 2
applied 23 repair op(s)
validation: 126 error(s) remain — quarantining
```

Eighty-nine errors in, one hundred and twenty-six out, and the old code **saved the
result anyway**. Three distinct bugs, all now fixed:

**(a) `add` cannot create intermediate containers.** The model emits one op for a full
path; RFC 6902 requires a separate op per level. The model thinks in paths, the standard
wants steps. Since patchable regions are objects all the way down, auto-vivifying missing
*objects* is unambiguous and does what the author meant. Missing *array* indices still
raise — that intent is genuinely unclear.

**(b) One bad op discarded eighty-nine good ones.** All-or-nothing is correct for the
fold, where a half-applied patch leaves the world state quietly wrong. It is wrong for a
repair patch. `apply_best_effort()` applies each op independently and returns the
failures for feedback.

**(c) No check that the repair helped.** Now the violation count is compared before and
after; a regressive patch is rejected and the previous document kept.

After the fix, from a live run: `repair rejected: 0 -> 6 schema error(s), reverting` —
twice. Both would previously have been saved as damage.

**The general lesson: a self-correction step needs an acceptance test, or it is just
another way to introduce errors.**

---

## 6. Hindsight leakage in reconstruction

When reconstructing, the deliberation must be written blind. Early traces leaked.

Found by an Opus reviewer: a trace arguing *"The synopsis requires her escape here"* —
the model was reasoning from a reconstructed synopsis that named the outcome. The blind
context was blind to the screenplay but not to earlier reconstructions of it.

Fix: `blind_context()` strips outcome-bearing keys and truncates plot spines before the
context is handed to a blind call.

Detectable tells, in rough order of usefulness:
1. Explicit references to what the work "requires" or "will" do
2. Specimen dialogue suspiciously close to the real lines
3. Retrospective framing — "as it turns out", "this sets up"
4. Confidence out of proportion to the evidence available

An earlier review also found two retrospective traces of the *same beat* that were each
internally airtight and mutually incompatible. Internal coherence is not evidence of
insight; it is evidence of fluency.

---

## 7. Model comparison, as measured

Opus review across factuality, emotional intelligence, dramatic quality, plausibility:

| | Reasoning traces | Factuality within them | Finished outputs |
|---|---|---|---|
| Grok 4.6 | ~80 | 71 | ~73 |
| GLM-5.2 | 58.0 | 44.7 | 72.6 |

The interesting result is the gap between columns. GLM's *reasoning* is much worse than
Grok's while its *outputs* are equivalent. Whatever the deliberation is doing, its
quality correlates weakly with what comes out.

The reviewer's verdict on Grok is worth keeping: **"constraint-checking is real work, the
deliberation is theatre."** The parts of a trace that reference specific established
facts do work. The parts that narrate a decision process are largely performance.

Practical consequence: put the strongest available model on the **upper layers**. They
are ~8 calls out of ~1,800 — 0.4% of volume — and they determine everything downstream.
An error in the entity layer propagates to every scene. Factuality 44.7 versus 71 is
exactly the axis that matters there, and eight calls at the better model is nearly free.

---

## 8. Things that turned out not to matter

- **Asking harder.** Prompts demanding completeness, warning about placeholders, and
  insisting "there is no later" did not move budget dilution. Structure did.
- **Retrying the same prompt.** Feeding the *actual violations* back works; asking again
  and hoping does not.
- **Higher reasoning effort.** Between `high` and `max`, no measurable quality
  difference on our schema — only tokens.
