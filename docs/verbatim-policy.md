# Not copying the screenplay

*Why a node may not quote its source, how that is checked, and what happens to the text that
slips through.*

---

## The rule

> **No published artifact may contain eight or more consecutive words from the source
> screenplay.**

Eight is a convention, not a legal threshold, and it is deliberately strict. The point is
structural: StoryTree records *what happened*, and a node that reproduces the words it
happened in has stopped recording and started copying. The rule keeps the distinction from
eroding one summary at a time.

Names, numbers, dates, times and place names are exempt in effect — they are facts, they must
stay exact, and rewording them makes the node wrong. `Room 303` stays `Room 303`.

## What went wrong

The rule existed and was checked. The check walked **one directory**. Asked whether
`docs/cognitino` was clean it answered honestly that it was, and said nothing about
`docs/nodes` — which had just been published carrying a twenty-four word run of dialogue.

Widening it to everything git tracks found the same defect in **140 files**, the longest run 48
words. Then running the new detector over the current pipeline output found the real scale:

| | Nodes | Nodes with a copied run | Runs | Longest |
|---|---|---|---|---|
| Scene layer (Ornith V5) | 224 | **210 (94%)** | 905 | 50 words |
| Event layer (build 3, partial) | 40 | 19 (48%) | 35 | 13 words |

The scene layer is worse because it reads the screenplay directly. The event layer mostly reads
scene nodes, and copies about a quarter as much.

### The cause was in the instructions, not the model

`what_changes` accounted for 428 of the 905 runs, and the reason is written into the prompt:

> *Every piece of evidence you cite must be COPIED from the scene, word for word.*

The `evidence` field is **supposed** to be verbatim — that is what makes a claim checkable
against the page — and the tier-1 check enforces it. The pipeline was demanding the thing the
publication rule forbids, and both were working correctly.

## The resolution

Not "stop quoting". A field whose job is to be exact has to stay exact. Instead:

**`evidence` is bounded below the bar.** At most seven words: still copied, still checkable,
never a copyable run. Same mechanism the scene anchors use.

**Everything else is paraphrased at generation time.** Both system prompts now carry the rule
with a worked before-and-after, because naming an anti-pattern without showing it does not
work — the project has measured that:

```
on the page:  "I said, is everything in place?"
in your node: she asks a second time whether everything is ready

on the page:  The lamp swings above the table, throwing shadows that refuse to settle
in your node: the lamp keeps swinging and the shadows never come to rest
```

**What still slips through is caught and rewritten.** Prompting reduces this; it does not
eliminate it. So there is a pass after the build.

---

## The three-stage pass

```
   build the layer
        │
   1. check        distill/verbatim.py — every string in every node
        │
   2. trim         evidence and anchors cut to 7 words: exact by design
        │
   3. paraphrase   everything else rewritten by a small model
        │
   4. check again  a rewrite that still carries a run is retried, then elided
```

Run automatically at the end of a build as a **report**:

```
verbatim gate — scene layer
  exact runs (>= 8 source words): 905 in 210/224 nodes, longest 50
  by field: {'what_changes': 428, 'summary': 261, 'minds': 187, ...}
  near hits (review only): 818
```

It reports rather than blocks. A four-hour build that has just finished should not be thrown
away by a check whose fix needs a model and a decision about which endpoint to spend.

The fix itself:

```bash
python3 distill/paraphrase_pass.py \
    --nodes runs/scenes_x --source SCRIPT \
    --ports 8110 --model qwen3.8-27b --out runs/scenes_x_clean

# or gate a build in CI and change nothing:
python3 distill/paraphrase_pass.py --nodes runs/scenes_x --source SCRIPT --check-only
```

### Why a small model is the right tool

This is a local edit with a **hard, machine-checkable success condition**. Nothing about it
needs the model that built the node. A 27B running beside the big one costs almost nothing,
and if it fails the fallback is elision — which is always available and always safe.

That is the property that makes using a model here acceptable at all: **the pass can never
make the artifact worse than eliding would.**

### What the rewriter is required to preserve

A rewrite is rejected and retried if it:

- still contains an eight-word run,
- drops a **number** — including a written-out one. The first version protected only digits,
  so a rewrite turning *"a two-hundred-fifty pound sack"* into *"a heavy body"* passed while
  deleting the number it was meant to protect,
- drops a **name**. Not every capitalised word: the words the node itself treats as entities,
  plus anything in caps. Protecting every capitalised word forced a needless elision because a
  rewrite dropped the word *"Savior"* from inside a quotation,
- changes length by more than a factor of about two in either direction.

After three attempts the span is elided and marked `[…]`.

---

## Two gates, because one is easy to slip past

**Exact** — eight consecutive source tokens. Cheap, decisive, and what the rule actually says.

**Near** — a ten-content-word window of which seven also appear together somewhere in the
source, ignoring stopwords, word endings and **order**. It catches the rewrite that turns

> The lamp swings above the table, throwing shadows that refuse to settle

into

> the lamp kept swinging, its shadows refusing to settle

which defeats the exact gate while copying the sentence whole.

The near gate is a **review signal, never an automatic rewrite**. A node that legitimately
describes the same events trips it about 3.7 times per scene node, which is the price of
catching the reworded copy. Anything that treated it as a defect count would be measuring the
subject matter, not the node.

> **A false start worth recording.** The near gate was first built as consecutive matching
> content-word stems. It did not work: a crude stemmer does not fold *relentlessly/relentless*
> or *rang/ring*, and one unfolded word in the middle breaks the run. Order was the wrong thing
> to depend on.

## Where a copied run came from

Each hit is labelled `dialogue`, `action` or `heading`, so the rewriter can be told whether to
produce reported speech or a description. The label is a **hint with a confidence, not a
claim**: this screenplay came out of a PDF with most of its indentation destroyed, and
indentation is what separates a dialogue block from an action paragraph. Two weak signals are
combined — distance below a character cue, and line width.

The width is **measured from the document**, not fixed. Dialogue is wrapped narrower than
action in every screenplay, but how narrow is a property of the file: here dialogue runs to 33
characters at the 90th percentile and action to 53. A constant tuned on one film is the
definition of what does not transfer — the mind-pass gate learned this the expensive way.

## The files

| | |
|---|---|
| `distill/verbatim.py` | detection only. Both gates, run location, role labelling. A detector that also fixes things is a detector nobody can test. |
| `distill/paraphrase_pass.py` | the rewrite pass, with `--check-only` |
| `tools/check_no_leak.py` | the publication sweep, over everything `git ls-files` reports |
| `tools/redact_source_spans.py` | elision, for text already published |
| `tests/test_verbatim.py` | including the apostrophe case and the two gates' disagreement |

## Still open

**Git history.** The 140 files were cleaned in the working tree. The runs are still in earlier
commits, and removing them means rewriting history and force-pushing a public repository.

**Context truncation.** Unrelated but found alongside: two of roughly 1,180 event-layer
generations hit the 32,768-token context limit and were truncated. Rare, but the largest events
are exactly the ones that overflow, and they are the ones worth the most.

---

[The StoryTree structure](storytree-structure.md) · [The scene node](nodes/scene-node.md) · [The event node](nodes/event-node.md)
