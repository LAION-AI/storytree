# scriptforge — reconstruction

A fork of `narrativeforge` that runs the pipeline **backwards**.

The forward system invents a story and writes it down. This one is handed a
finished screenplay and has to recover the structure that would have produced
it — story root, exposé, plots, entity dossiers, event chain, scene
definitions — such that **every scene node owns exactly one passage of the real
script**.

The artifacts come out in the same shape the forward pipeline produces, so the
viewer, the validator, the state fold and the co-writer all work on a
reconstruction without knowing it is one. The differences are additive: scene
nodes carry `bound_scene_id` and `divergence`, and the project carries
`script_map.json`.

---

## The constraint that shapes everything

> **The transition is blind. The node may cheat.**

A reasoning trace written with the finished script in view is worthless as
training data. It is hindsight wearing the costume of deliberation, and a corpus
of it teaches a model to *sound* like it is deciding while it is actually
copying.

So the pipeline splits every scene into two calls that see different things:

| | sees the layers so far | sees the passage | job |
|---|---|---|---|
| **blind transition** | yes | **no** | decide what should happen next and why |
| **sighted node** | yes | yes | describe what the script actually does |

The blind call gets one extra thing: a **production envelope** — the location,
the time of day, who is on screen, roughly how long the scene runs, all of it
read off the slug line and a word count, never off the content. That is the
information a writer has when told "this one plays in the office, two people,
about a page". It constrains without revealing.

Because the two calls are separated, the gap between them can be measured. Every
scene node records a `divergence`:

```json
"divergence": {
  "predicted_correctly": ["that she would refuse to name the cost"],
  "missed": ["that he asks about her boots instead of the railing"],
  "why": "The forecast reached for the confrontation; the writer went sideways
          into evidence, which is more in character and delays the collision.",
  "forecast_quality": 62
}
```

That record is not a by-product. It is a forecasting log that no amount of
post-hoc annotation can fake, and it is the most valuable thing here.

A crude leakage detector runs over every blind trace and flags phrases like
"the script", "as it turns out", "we later learn" — a trace written without
knowledge of the outcome has no reason to use them.

---

## Stage 0 is deterministic, on purpose

If a model were asked to quote scene boundaries back, it would paraphrase, and
paraphrase cannot be re-found in the source. So the split happens in code.

`screenplay.py` produces an **anchor table**: for every scene, its slug line, its
character span, and short verbatim head and tail quotes **grown until unique in
the document**. Given the table and the file, anyone recovers any scene's exact
text with a regex and no further intelligence.

Two details that turned out to matter:

- **Anchors are sliced verbatim, not rejoined from tokens.** An anchor built by
  splitting on whitespace and joining with single spaces does not occur in the
  source the moment it crosses a line break. Anchors that cannot be found are not
  anchors.
- **Matching is whitespace-tolerant.** The stored quote is literal, but the
  search treats any run of whitespace as equivalent, so anchors survive a file
  that has been re-wrapped, re-indented, or round-tripped through a PDF.

```bash
python3 -m scriptforge.recon_cli parse --script samples/tideline.fountain --list
```

```
scenes            5
coverage          98.0%
anchors unique    5/5
round trip        exact for every scene
```

---

## Running it

```bash
# see the shape and every prompt, without calling a model or spending anything
python3 -m scriptforge.recon_cli dryrun --script path/to/script.txt

# reconstruct
python3 -m scriptforge.recon_cli run --project runs/x --script path/to/script.txt

# just the upper layers, or a few scenes to sample quality first
python3 -m scriptforge.recon_cli run --project runs/x --script s.txt --stages upper
python3 -m scriptforge.recon_cli run --project runs/x --script s.txt --limit 3

# halve the cost by skipping the forecast (and lose the divergence record)
python3 -m scriptforge.recon_cli run --project runs/x --script s.txt --no-transitions

# validate the graph and the one-to-one binding
python3 -m scriptforge.recon_cli check --project runs/x
```

### Stages

```
S0  parse        deterministic — anchor table, no model
S1  story_root   the whole script; recovers rules, register, plot embedding
S2  expose       ending-first, sentence-keyed synopsis, both plot summaries
S3  plots        the chains the script actually runs
S4  entities     dossiers; declares the state variables the events may move
S5  events       the causal DAG, naming which parsed scenes each event plays in
S6  scenes       ONE NODE PER PARSED SCENE — blind transition, then sighted node
S7  bind         prose attached by reference to the anchor table
```

Only S6 runs the two-call split. The upper layers describe the work as a whole,
and there is nothing to forecast about a thing you are summarising.

---

## The script stays yours

By default `bind` writes `prose_refs.json` — spans and anchors — rather than
copying the screenplay into the project. The derived artifacts stay a
*description* of the script; the text stays in your file and is loaded on
demand. `--inline-prose` opts into embedding the passages when you want the
project to be self-contained offline.

This mirrors the whitepaper's rights hygiene, and it is also just better
engineering: one copy of the text, one place to fix it.

---

## What is checked

Everything the forward validator checks (G1–G21: state continuity, declare-then-
realise, causal acyclicity, referential integrity, no direct speech below the
exposé, no arrays in patchable regions …) plus reconstruction-specific rules:

- every parsed scene is owned by exactly one node, and no node claims two
- every node's `bound_scene_id` names a scene that actually parsed
- the anchor round trip reproduces each span exactly
- spans are ordered, non-overlapping, and cover ≥90% of the file
- blind traces contain no hindsight markers

```bash
python3 tests/test_screenplay.py     # 49 assertions
```

The suite includes the separation test, which asserts that no 60-character run
of a scene's text and no line of its dialogue appears in that scene's blind
prompt. That is the property the corpus's value depends on, so it is a
regression test rather than a one-time check.

---

## Cost

Measured on the sample, per call, input side:

| | tokens in |
|---|---|
| upper layers, 4 calls | ~30,000 |
| per scene, 2 calls | ~9,000 |

The upper layers carry the whole script four times, so they scale with script
length; the per-scene calls do not. For a 50-scene feature expect roughly
4 × (script) + 50 × 9k input, and output dominated by the blind transitions at
7,000–10,000 words each. `--no-transitions` roughly halves it.

---

## Status

Prepared and tested end to end **except** for a real reconstruction run — the
parser, the anchor round trip, the prompt wiring and the blind/sighted
separation are all verified, but no screenplay has been put through it yet.
Point it at one with `dryrun` first.
