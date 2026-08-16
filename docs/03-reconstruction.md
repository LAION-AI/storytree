# Reconstruction — screenplay to graph

Given a finished screenplay, recover the whole structure above it: story root, exposé,
plots, entities, events, and one scene profile bound to each real scene.

## Why do this for a work that already exists

Two reasons, and the first is the important one.

**It is the only way to measure the pipeline.** For an invented story there is no ground
truth — you cannot say whether the reconstructed psychology is *right*, only whether it
is internally consistent. For a known work there is a real scene to compare against, and
the comparison is informative.

**The graph is what can be reused.** A version for a different audience, a different
length, a different medium — all of those operate on the structure, not the finished
prose.

## The rule that makes it worth anything

**The deliberation is written blind.**

The model reasoning about scene 40 does not see scene 40. It sees what earlier layers
established plus the scene's outer envelope — location, time of day, who appears,
approximate length, position in the work — and must **decide** what should happen rather
than **describe** what does.

Drop this constraint and the exercise collapses. A model that knows the outcome can
justify it effortlessly; backwards, every decision looks inevitable. Such analyses read
as profound and contain nothing.

The *writer* may then see the scene — `SIGHTED_SYSTEM` — because binding a profile to
real text requires reading it. Only the reasoning is blind.

```
BLIND_SYSTEM    decide what should happen        no scene text
SIGHTED_SYSTEM  bind the decision to real text   scene text available
blind_context() strips outcome-bearing keys, truncates plot spines
```

`blind_context()` exists because of a caught leak: a trace argued *"The synopsis requires
her escape here"* — blind to the screenplay, but not to a **reconstructed synopsis that
named the outcome.** Leak prevention has to cover derived artifacts, not just the source.

## Parsing

`screenplay.py` handles slug lines, character cues, parentheticals, dialogue and action,
then builds an anchor table so each scene can be re-split from the source deterministically.

Anchors are sliced **verbatim** from the source and matched with a whitespace-tolerant
regex. An earlier version rebuilt them by rejoining split tokens, so they never matched
across line breaks — anchors that cannot find their own scene.

PDF extraction needs rescue. `preclean()` and `looks_like_pdf_extraction()` handle lost
indentation, page furniture, and scene numbers glued to slug lines in several dialects
(`105`, `105A`, `A105`). Before this, a real screenplay PDF parsed to **zero** scenes.

## Scene-level assembly

Scaffolded, one deep structure per call — see `05-model-behaviour.md` §1 for why:

```
1  craft        where the story stands, what this scene is for, what was rejected
2..n  psychology  ONE character per call, eleven fields
n+1  specimen   6–10 real dialogue lines at the turning point, plus a cold re-read
n+2  dynamics   locations, objects, groups: what forces act, what changes meaning
n+3  continuity which facts were used, which rules obeyed, which contradictions avoided
```

`characters_in_scene()` resolves who to analyse from three sources — speaker cues,
aliases, and the participants the event layer already recorded — and **returns
unresolved cues separately rather than dropping them.** An unresolvable speaker is a hole
in the entity layer and should be visible. An earlier version matched canonical names
only, found one speaker in a two-speaker scene, and produced a scaffolded run that
analysed *fewer* characters than the baseline it was meant to beat.

## The specimen, and why it matters more here than in forward generation

In reconstruction the real dialogue already exists, so writing your own looks redundant.
It is the opposite: it is **the only falsifiable prediction in the whole procedure.**

"This character will open up here" cannot be checked. Six concrete lines can be laid
beside the real ones. Everything else in a deliberation is assertion; this is forecast.

Three things follow:

- **Self-test.** Writing the lines forces the model to test its own analysis. An
  immaculate analysis whose lines come out dead is a common and otherwise invisible
  failure.
- **Divergence record.** Predicted against actual, over hundreds of scenes, measures
  whether the model *understands* drama or merely reproduces it. This is the real
  scientific yield.
- **Leak detector.** If blindness is compromised anywhere, it shows here first: the
  predictions get suspiciously good.

Judge divergence by dramatic function, not similarity. A different line achieving the
same turn is a success. The same line reached by different reasoning is more interesting
than either.

## Degenerate-response handling

A `{"ref": "sc-004"}` stub — 9 tokens, `finish_reason: stop` — was once accepted as a
transition. `_degenerate()` now enforces `MIN_TRANSITION_WORDS = 400` and required
top-level keys, with three retries. **A fake node is worse than a missing one:** the
missing one is visible.

## Cost

Measured, per scene, scaffolded, thinking off, locally at 24.26 tok/s:
**5.3 calls, 22,679 output tokens, ~18.9 minutes.**

| Scope | Scenes | Scaffolded, warm cache |
|---|---|---|
| Upper layers only | — | **1.3 h** |
| TV episode | 40 | 12 h |
| Feature | 120 | 35 h |
| Feature, finely cut | 224 | 66 h |

The upper layers are remarkably cheap — 302,997 in / 93,293 out over five calls. If all
you want is the structure of an existing work, that is a lunch break, not a project.

Leaving hidden reasoning on multiplies all of it by ~6.1.

## Copyright

Structure is derived; prose is stored **by reference** — offsets and anchors in
`prose_refs.json`, never copies. `--inline-prose` is opt-in. Published viewers use
`include_prose=False`. Source text files are gitignored. Committed artifacts contain
structural fields only — verified: no scene artifact carries a text or prose field.
