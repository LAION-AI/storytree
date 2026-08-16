# EXP-002 · Grounding by construction rather than by instruction

**Status: supported.** Grounding violations fell 11 → 2 across three scenes.
Location adherence went 1/3 → 3/3 and off-roster speakers 2 → 0, both on the two
dimensions a prompt clause had failed to move in EXP-001. Output length did not
fall. n=3.

---

## Question

EXP-001 asked whether measured failures are instruction problems or capability
limits, and got a split answer: a clause fixed the *confidence* failure on both
items and **regressed** the *envelope-location* failure.

The proposed explanation was that confidence is a local field an instruction can
reach, while staying in the right room is a global consistency property that was
already stated in the prompt and did not become truer by being restated.

If that is right, the location and roster failures should yield to **structure**
where they did not yield to instruction. This experiment tests that.

## Prediction

*Recorded before running.*

Constraining location and speakers in the schema should drive both to zero,
because a grammar refuses what a request only discourages. State-variable
ownership should improve but **not** reach zero, because which variables are
legal depends on which entity was named, and JSON Schema cannot express that
dependency — it is checked afterwards instead.

Depth was expected to be unaffected in either direction: grounding governs
whether claims are admissible, not whether they are good.

## Design

Three arms on the same three scenes, everything else identical — same scaffold,
same schemas, same unfiltered dossiers (`STRIP_DOSSIERS=0`), thinking off and
verified by empty `reasoning_content`, one scene per endpoint, concurrently.

| Arm | Intervention |
|---|---|
| baseline | none |
| addendum | +4,561 chars of failure-derived instruction (EXP-001) |
| grounded | schema binding + post-check + one targeted repair |

The addendum arm has n=2; its sc-003 was not run.

### What "grounded" does

Four mechanisms, in descending order of how much they can be trusted:

1. **Bound in the schema.** A `binding` object is inserted as the *first*
   property, carrying `scene_id`, `location` and `time_of_day` as `const` and
   `on_screen` as a fixed-length enum. `specimen.lines[].speaker` and
   `state_changes_implied[].entity` become enums over the real cast and the real
   entity ids.
2. **First in the document.** Because `binding` is emitted before anything else,
   the model has written the ground truth into its own context before it reasons.
   This is what reaches the free-text fields a grammar cannot constrain.
3. **Checked mechanically** against data already on disk: dossier, prior nodes,
   state model.
4. **One targeted repair**, handing back the concrete violations, kept only if
   the count actually falls.

`state_changes_implied[].variable` is deliberately left free. Enumerating the
union of all entities' variables would permit exactly the failure worth catching
— a variable belonging to a different character — while looking like enforcement.

## Materials

| | |
|---|---|
| Model | `Qwen3.8-27B-Uncensored-FP8`, vLLM FP8/Marlin, one copy per GPU |
| Endpoints | `127.0.0.1:8100–8102` |
| Decoding | temperature 0.7, `enable_thinking: false` |
| Items | `sc-001`, `sc-002`, `sc-003` of `reconstruct/runs/matrix` |
| Code | `reconstruct/scriptforge/grounding.py` |
| Outputs | `reconstruct/runs/matrix/transitions_qwen_grounded/` |

```bash
export LOCAL_BASE_URL=http://127.0.0.1:8100/v1 LOCAL_MODEL=qwen3.8-27b
export MODEL_FAMILY=qwen STRIP_DOSSIERS=0 GROUNDED=1
python3 tools/run_local_matrix.py runs/matrix sc-001 --think off \
        --out transitions_qwen_grounded
```

## Results

| Scene | Arm | Violations | In location | Off-roster | Confidence | Specimen | Words |
|---|---|---|---|---|---|---|---|
| sc-001 | baseline | 2 | no | 0 | 95 | 8 | 6,445 |
| | addendum | 3 | no | 1 | 85 | 8 | 6,694 |
| | **grounded** | **0** | **yes** | **0** | 85 | 10 | 8,855 |
| sc-002 | baseline | 4 | yes | 1 | 90 | 8 | 4,470 |
| | addendum | 2 | no | 1 | 65 | 8 | 4,751 |
| | **grounded** | **0** | **yes** | **0** | 90 | 6 | 5,522 |
| sc-003 | baseline | 5 | no | 1 | 95 | 7 | 5,603 |
| | **grounded** | **2** | **yes** | **0** | 95 | 7 | 3,662 |

| Arm | n | Violations | In location | Off-roster | Mean confidence | Specimen | Words |
|---|---|---|---|---|---|---|---|
| baseline | 3 | 11 | 1/3 | 2 | 93 | 7.7 | 5,506 |
| addendum | 2 | 5 | 0/2 | 2 | 75 | 8.0 | 5,722 |
| **grounded** | 3 | **2** | **3/3** | **0** | 90 | 7.7 | 6,013 |

All three arms: 0 schema violations, all psychology blocks complete, 3/3 pass,
0.00% verbatim leakage.

## Interpretation

**The prediction held on both counts, including the negative one.**

Location went 1/3 → 3/3 and off-roster speakers 2 → 0. These are the two
dimensions the addendum failed to move — it scored 0/2 on location, *worse* than
baseline. Same model, same scenes, same failures: instruction did not fix them
and construction did.

**The remaining violations are the predicted ones.** Both are on sc-003, and both
are the case deliberately left unenforced: a state change naming
`spatial_location` on an entity that does not own that variable, and the derived
confidence violation that follows from it. The post-check caught it, the targeted
repair failed to fix it, and the harness kept the original because the repair did
not reduce the count. A remaining failure that was named in advance is a better
outcome than an unexplained zero.

**Grounding cost nothing in depth.** Words rose (5,506 → 6,013) and specimen
lines held (7.7). The concern that constraint would produce compliant, thinner
output did not materialise at this n.

**The two interventions are orthogonal and should compose.** Grounding left
confidence roughly at baseline (90 vs 93) because it contains no confidence
clause; the addendum moved confidence but not location. Each fixes what the other
does not. That is the natural next experiment — and per EXP-001's displacement
hypothesis it is not guaranteed, since the grounding clause adds instruction text
of its own.

### What does not follow

- Not that grounding improves *quality*. Every arm passed the structural check
  and scored 0 schema violations. This measures admissibility of claims, not
  whether the analysis is good. Only a rubric pass can say that.
- Not that fabrication is solved. The sc-003 case shows the class of error
  survives where enforcement is structurally impossible.
- Not that the addendum was worthless — it owns the confidence result, which
  grounding does not touch.

## Threats to validity

- **n=3, and n=2 for the addendum arm.** Directional.
- **Same measurement code defines and scores the violations.** `check_grounding`
  both drives the repair and reports the result, which risks scoring what is easy
  to enforce. The location finding was independently confirmed by reading all
  outputs in EXP-001; the roster and entity-ownership checks are set membership
  against data on disk and are hard to get wrong, but they are not independent.
- **A bug in the binding was caught only by a dry run.** The first version indexed
  a fixed schema path and silently failed to constrain speakers while correctly
  binding the location — a half-applied constraint reporting success. Had it not
  been dry-tested, the arm would have measured something other than its label.
- **Rubric scoring not yet run** on the grounded outputs.
- **Single sample per cell** at temperature 0.7; within-condition variance
  unmeasured.
