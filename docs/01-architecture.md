# Architecture

## The layers

Seven layers, each one a JSON document with its own schema. Everything above `prose` is
structure; `prose` is the only layer a reader would recognise as a screenplay.

```
story_root    genre, audience, style, premise, 76-dimension plot embedding
    │
expose        short and long plot summaries, synopsis, ending-first statement
    │
plots         the threads running through the work, each with its own spine
    │
entities      characters, creatures, locations, objects, groups, concepts
    │         — each with a full, patchable state dictionary
events        what happens, in story-time order; exactly one parent plot each
    │
scenes        discourse-order units; exactly one parent event each
    │         — entry state, beats, exit state
prose         the screenplay itself
```

Two structural rules, enforced by the validator rather than by convention:

- **Every event has exactly one parent plot.** It may *participate* in several (the
  `plots` array), but exactly one owns it. Without this the plot layer degenerates into
  tagging and you can no longer ask "what is this plot actually made of".
- **Every scene has exactly one parent event.** Same reasoning one level down.

## State, and the fold

The central design decision: **state at time T is never stored, it is computed.**

Each entity's profile carries an initial state dictionary at `t0`. Beats — the smallest
unit inside a scene — are the *only* authors of change, and they express change as
RFC 6902 JSON Patch operations. The state of anything at any point is then:

```
world_state(T) = apply(t0, concat(ops of every beat before T))
```

This is `timeline.fold()`. Canonical ordering is
`(event.story_time.index, scene.discourse_index, beat.beat)` — story time first so that
flashbacks and non-linear discourse fold correctly.

Consequences worth understanding:

- **Event-, scene- and plot-level state summaries are derived views**, not sources of
  truth. If a scene's declared exit state disagrees with the fold, the fold wins and the
  validator raises it (G17).
- **Any inconsistency is mechanically findable.** "Character claims to hold the key in
  scene 30 but dropped it in scene 12" is not a reading problem, it is a diff.
- **You can regenerate a character sheet at any timestep** without asking a model
  anything: `narrativeforge state --entity ch-01 --at sc-012`.

## Why patchable regions contain no arrays

JSON Pointer addresses array members by index. Insert one element at the front and every
pointer after it silently retargets — and a story is nothing *but* a long sequence of
insertions.

So everywhere the schema wants "a list of things that may later be patched", it uses an
object keyed by a stable id instead:

```json
"backstory": {
  "b01": {"text": "She grew up on the coast."},
  "b02": {"text": "Her sister was scanned three years later."}
}
```

`assert_no_arrays()` enforces this at validation time on the patchable subtrees. Arrays
are still allowed in regions nothing will ever patch (a list of genre tags, say).

This is also what makes **sentence-addressable backstories** work. A backstory is not a
paragraph, it is a dictionary of sentences with stable keys. A later revelation can patch
`/entities/ch-01/profile/backstory/b04/text` without rewriting anything else, and the
patch is a legible one-line diff.

## The validator

`validate.py` implements G1–G26, checked deterministically with no model involved:

| Group | What it catches |
|---|---|
| G1–G6 | Referential integrity — every id referenced exists, parents are single |
| G7–G12 | Ordering and coverage — story time monotonic, every plot discharged by events, every event realised by scenes |
| G13–G16 | Patch legality — pointers resolve, no arrays in patchable regions, no no-op patches |
| G17–G20 | State coherence — declared states agree with the fold, values stay in declared ranges |
| G21–G26 | Craft floor — continuity facts cited, no t0 leakage, distinct voices, non-identity patches |

The checker is validated against 23 deliberately injected errors and currently detects
23 of 23. That number, not the number of tests passing, is the thing to watch: a
validator that never fires is indistinguishable from a broken one.

## Reasoning transitions

Each node is produced by **two** calls, not one: first an explicit written deliberation,
then the node itself conditioned on it. The deliberation is stored permanently.

This exists because of a measurement. A model's own `reasoning_content` — the hidden
thinking most APIs expose — turned out to be a ~18% summary running at 0.17–0.95
characters per token, with essentially zero coverage of theory of mind, trajectory, or
craft. Explicit written-out transitions run at 4.18 characters per token and score
`pass` on the structural check. The hidden trace is not a reasoning artifact; it is
exhaust. See `04-reasoning-transitions.md`.

## Reading the code

| File | Why you would open it |
|---|---|
| `narrativeforge/schemas.py` | The seven layer schemas — the actual contract |
| `narrativeforge/timeline.py` | `fold()`, canonical ordering |
| `narrativeforge/jsonpatch.py` | RFC 6902/6901, and the deliberate lenient extensions |
| `narrativeforge/validate.py` | G1–G26 |
| `narrativeforge/transitions.py` | What a deliberation must contain, and how it is scored |
| `narrativeforge/craft.py` | ~7,300-character craft sheet injected into prompts |
| `reconstruct/scriptforge/screenplay.py` | Slug-line parser, anchor table, PDF-extraction rescue |
| `reconstruct/scriptforge/reverse.py` | `blind_context()` — the leak prevention |
| `reconstruct/scriptforge/scaffold.py` | One deep structure per call |
