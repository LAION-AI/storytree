# What Anthropic models are said to do better at prose — and what the evidence actually shows

Research for the structured-narrative-generation write-up. The question is not "is Claude
good at writing". It is: **which specific, nameable capabilities do practitioners and
benchmarks repeatedly attribute to Anthropic models that they say other models lack**, and
how well does each survive scrutiny.

Every claim below carries a source, a date, and an evidence tier. Where a popular claim did
not survive, the correction is left visible.

---

## Evidence tiers

| Tier | Meaning |
|---|---|
| **A** | Systematic benchmark with published methodology and inspectable data |
| **A′** | My own analysis computed over a tier-A benchmark's published data (derived, not the benchmark's own metric) |
| **B** | A practitioner making a specific falsifiable claim, with examples or a shipped artifact |
| **C** | Repeated anecdotal consensus across independent, identifiable sources |
| **D** | A single opinion |

---

## Executive summary — what actually recurs

Seven findings recur across independent sources and survive checking.

1. **Claude wins the discipline axes and loses the invention axes.** Across 124 models on
   EQ-Bench Creative Writing v3, Claude Opus 5 ranks **1st** on Consistent Voice & Tone,
   Show-Don't-Tell, Sentence Flow, Avoids Amateurish Prose, Strong Dialogue, Elegant Prose
   and Avoids Positivity Bias — and only 13th on Descriptive Imagery, 8th on Instruction
   Following, 7th on Emotional Depth, 6th on Creativity. Three independent benchmarks agree
   on this shape. **Tier A.**

2. **Low lexical slop, but frontier-model-specific — not a family property.** Claude Opus 5
   has the lowest slop score of all 126 longform models (5.64) and all 125 short-form ones
   (6.59). But the Claude *family* median on short-form (16.07) is **worse** than GPT-5's
   (13.10). "Claude doesn't write slop" is false as stated. **Tier A.**

3. **A measurable restraint signature in the n-grams.** Claude's most-repeated phrases are
   silences — "Nobody said anything", "without saying anything", "looked at it for a long
   time". GPT-5.2's and Gemini 3 Pro's are somatic tells — "mouth went dry" (26×), "throat
   tightened", "squeezed her eyes shut". The sharpest and most actionable contrast found.
   **Tier A′**, stable across three Claude versions.

4. **The folk claim that Claude leads on *subtext* is unsupported and contradicted.** In a
   29-model, 15,347-story stylometric study, dialogue subtext is led by Mistral Medium 3.1,
   then GPT-5 Pro and GPT-5.2. Claude leads dialogue *volume*, not subtext. **Tier A.** The
   most important negative result here.

5. **A recognisable "Claude cadence" is the strongest cross-source practitioner complaint.**
   Independent named sources converge on the same short list: "it's not X, it's Y", em-dash
   overuse, sentence-fragment-for-punch, "load-bearing", rule-of-three. **Tier C**, with
   many identifiable authors and dates.

6. **Refusal on ordinary creative prompts is real and version-specific.** Claude Opus 4.7
   completed only **347 of 400** story prompts on an independent benchmark; Fable 5 395/400,
   Opus 4.8 399/400. **Tier A** for the completion counts.

7. **Quality holds across long outputs where other models decay.** Over an eight-chapter
   novella, median chapter-1→chapter-8 score change is −0.73 for Claude vs −2.24 for
   everything else; 5 of 14 Claude models *improve* versus 2 of 112 non-Claude. **Tier A′**,
   and weakened by the judge being Claude Sonnet 4.

The through-line: **Claude's measured advantage is lexical and structural discipline, not
literary imagination.** It says less, repeats fewer stock phrases and holds a brief longer.
It does not, on available evidence, understand implication better than its competitors, and
on imagery and creativity it is beaten.

**A caveat that governs everything below.** Among frontier models the judged differences are
tiny: the spread across the top ten models is **0.22–0.94 points on a 20-point scale**,
against a full-field range of ~10–12 points. "Claude Opus 5 ranks 1st on Strong Dialogue"
means it beat GPT-5.5 by 0.05. The large, robust separations in this research are all in
**string-level metrics** (slop, n-grams), not in LLM-judge scores. That is itself a finding
worth putting in the paper: judge-scored axes compress at the frontier; lexical metrics
still discriminate.

---

## Method, and what I excluded

**Excluded: SEO content-marketing pages.** The top of general search for "Claude vs GPT
creative writing" is almost entirely affiliate content (`eesel.ai`, `arsturn.com`,
`buildmvpfast.com`, `myclaw.ai`, `supportgpt.app`, `inkfluenceai`, `pickaistool`,
`popvid.ai`). Several assert specific comparative test results with no methodology, no data
and no named author. None are used as evidence. Anyone repeating "Claude understands
subtext" is mostly citing this layer — one reason Finding 4 goes the other way.

**Reddit was inaccessible.** Reddit blocks Anthropic's crawler; `reddit.com` could not be
fetched or domain-filtered, and `old.reddit.com`, `api.reddit.com` and mirrors (redlib,
safereddit) all returned 403
([support.anthropic.com/en/articles/8896518](https://support.anthropic.com/en/articles/8896518)).
This is the single largest hole in the research, and it is not neutral: the RP/long-chat
complaints about repetition, positivity bias and in-character moralising are Reddit-native.
**No claim here rests on Reddit**, and several items in "could not find evidence for" are
there because the primary threads were unreachable rather than because they are false.

**Automated page summarisation proved unreliable; every load-bearing number was re-verified
from raw source.** One automated read of the `lechmazur/writing_styles` README reported
"Claude Opus 4.1: highest dialogue subtext". A second read of the same README named Mistral
Medium 3.1. Fetching the raw markdown settled it: Mistral leads, and the Claude attribution
was fabricated by the summariser — in the direction the query implied. **Every figure below
was pulled from raw CSV/JSON/markdown.** For the paper: automated evidence-gathering
silently invents attributions that flatter the framing of the prompt.

---

## Finding 1 — The per-axis profile: discipline yes, invention no

**Claim.** Claude's strengths cluster on control and cleanliness; its relative weaknesses
cluster on imagery, emotional range and inventiveness.

**Evidence tier: A.** EQ-Bench Creative Writing v3 scores each output on 15 rubric axes.
Computed from the raw chart data
([`creative_writing_chartdata.js`](https://eqbench.com/creative_writing_chartdata.js),
124 models, retrieved 2026-08-16), Claude Opus 5's rank per axis:

| Axis | Rank /124 | Value | Field leader |
|---|---:|---:|---|
| Consistent Voice & Tone | **1** | 18.12 | — |
| Show-Don't-Tell | **1** | 16.21 | — |
| Sentence Flow | **1** | 17.10 | — |
| Avoids Amateurish Prose | **1** | 17.29 | — |
| Strong Dialogue | **1** | 17.08 | — |
| Elegant Prose | **1** | 16.83 | — |
| Avoids Positivity Bias | **1** | 17.60 | — |
| Avoids Purple Prose | 2 | 16.36 | gpt-5.3-chat 16.52 |
| Pacing | 3 | 16.93 | kimi-k3 17.05 |
| Coherent | 4 | 18.11 | claude-fable-5 18.14 |
| Believable Characters | 4 | 17.14 | horizon-alpha 17.23 |
| Creativity | 6 | 15.49 | horizon-alpha 15.92 |
| Emotional Depth | 7 | 16.41 | gpt-5 16.63 |
| Instruction Following | 8 | 18.43 | gpt-5.5 18.60 |
| Descriptive Imagery | 13 | 16.98 | gpt-5 17.58 |

The shape is consistent: everything Claude leads is a *negative* virtue (avoids X, stays
consistent, doesn't overwrite); everything it trails on is *generative* (imagery,
creativity, emotional depth).

**Two caveats, both serious.**

- **The judge is Claude Sonnet 4.6** for this benchmark
  ([creative-writing-bench](https://github.com/EQ-bench/creative-writing-bench)). Claude
  judging Claude is an uncontrolled self-preference confound. It is most suspicious exactly
  where benchmark and practitioner opinion diverge most: Claude ranks **1st on "Avoids
  Positivity Bias"** while positivity bias and sycophancy are among the loudest practitioner
  complaints (§C.3). I would not report the positivity-bias rank without that flag.
- **The margins are inside the noise.** See the top-ten spread caveat in the summary.

**Assessment.** The *shape* is well supported because it replicates on two benchmarks with
different authors and protocols (§5). The *ranks* should not be quoted without the judge
caveat.

---

## Finding 2 — Slop: real, large, and version-specific

**Claim.** Frontier Claude models emit measurably fewer stock LLM phrases than any other
model measured. This does not generalise to the Claude family.

**Evidence tier: A.** The slop score is computed by **string matching against a fixed list,
not by an LLM judge** — so unlike everything in Finding 1 it is immune to the judge-bias
confound. Methodology: 60% slop words, 25% "not-x-but-y" patterns, 15% slop trigrams, lists
derived by `slop-forensics` from ten models' outputs versus human text
([eqbench.com/slop-score.html](https://eqbench.com/slop-score.html),
[slop-forensics](https://github.com/sam-paech/slop-forensics)).

Longform, by vendor family (lower = less slop), from raw CSV in
[`creative_writing_longform.js`](https://eqbench.com/creative_writing_longform.js), n = 126,
retrieved 2026-08-16:

| Family | n | Median slop | Best |
|---|---:|---:|---:|
| **claude** | 14 | **13.26** | 5.64 |
| kimi | 6 | 16.60 | 9.67 |
| gpt-5 | 14 | 18.79 | 10.76 |
| grok | 3 | 40.11 | 27.41 |
| glm | 7 | 46.93 | 16.51 |
| qwen | 13 | 47.58 | 34.28 |
| deepseek | 11 | 49.27 | 19.59 |
| gemini | 8 | 51.57 | 29.01 |
| mistral | 7 | 55.90 | 42.78 |

**The short-form benchmark does not replicate the family-level result.** From
[`creative_writing.js`](https://eqbench.com/creative_writing.js), n = 125: gpt-5 13.10,
kimi 15.51, **claude 16.07**, grok 25.80, qwen 26.68, deepseek 27.84, glm 27.94,
gemini 28.73, mistral 47.09, llama 49.29. Claude is best on longform and third on
short-form.

What is consistent is the top individual model: Claude Opus 5 at 5.64 (longform) and 6.59
(short-form), lowest in both.

**Trend over versions, tier A′** (longform overall score / slop): claude-3.7-sonnet slop
25.99 → sonnet-4.5 12.99 → opus-4-5 20.22 → opus-4-6 16.86 → sonnet-4-6 10.56 → opus-4-8
9.39 → opus-4-7 9.06 → fable-5 8.31 → **opus-5 5.64**. Overall score rises monotonically
over the same sequence, 58.4 → 86.3.

**Assessment.** Well supported for frontier models; **overstated as a family property**.
The useful output is not the ranking but the *list* — see Finding 3 and file 10.

---

## Finding 3 — The restraint signature (most actionable result)

**Claim.** Claude's characteristic repetitions are withholdings — silence, refusal to react,
elapsed time. Other models' are involuntary body reactions and voice-modifier dialogue tags.

**Evidence tier: A′**, from per-model n-gram profiles published alongside the longform
leaderboard (`slopData` block in
[`creative_writing_longform.js`](https://eqbench.com/creative_writing_longform.js),
retrieved 2026-08-16). These are frequency counts over the benchmark corpus, not judgements.

**Claude Opus 5 — top repetitive phrases (counts):** "Nobody said anything" (7), "put her
hand flat" (4), "Neither of them said anything" (3), "nothing for a long time" (3), "stood
there with his hands hanging" (3), "without saying anything" (3), "ten past four" (3).

**Claude Opus 4.7:** "long time ago" (7), "made a small sound" (5), "said, without looking"
(4), "neither of them said anything" (4), "looked at him for a long moment" (4).

**Claude Sonnet 4.6:** "eighteen months ago" (6), "three weeks ago" (5), "looked at it for a
long time" (4), "going to say something" (4), "stood in the doorway for a moment" (3).

**GPT-5.2:** "mouth went dry" (26), "Mara's eyes flicked" (18), "fingers tightened around"
(14), "said, voice low" (11), "Mara's throat tightened" (8), "blood went cold" (8).

**Gemini 3 Pro Preview:** "voice lacked conviction" (5), "like a physical blow" (5), "eyes
snapped open" (4), "said, his voice dropping" (4), "squeezed her eyes shut" (4), "said, her
voice trembling" (3).

To check this is a pattern rather than cherry-picking, I regex-classified every model's
published top-30 bigram+trigram lists into "somatic tell" and "silence/withholding":

- All 14 Claude models: somatic hits ≤ 2 (usually 0); silence hits 2–10.
- gpt-5.2: 16 somatic. gpt-5.4-nano: 11. mistral-medium-3.1: 10. Mistral-Small-3.2: 9.
  GLM-4.7-Flash: 7. Mistral-Large-3: 7. Qwen3-Max: 6.

Caveats: my own regex over published top-30 lists; small counts; hand-drawn categories. The
effect is consistent enough across 14 Claude models versus ~70 others that I trust the
direction, not the magnitude.

**Version note:** claude-3.5-sonnet and claude-3-7-sonnet show *zero* silence n-grams. The
restraint signature belongs to the 4.x/5 generation, not to Claude historically.

**Revealed-preference corroboration, tier B.** The `anthracite-org/magnum` finetune series
states its purpose verbatim: "This is a series of models designed to replicate the prose
quality of the Claude 3 models, specifically Sonnet and Opus"
([magnum-v4-72b card](https://huggingface.co/anthracite-org/magnum-v4-72b), 2024-09). Two of
six training sets are Claude-derived (`kalo-opus-instruct-22k-no-refusal`,
`nopm_claude_writing_fixed`). Spending compute to imitate a model's prose is stronger
evidence of a perceived difference than forum opinion — but it dates to the Claude 3 era and
speaks to Opus 3's reputation, not current models.

---

## Finding 4 — Subtext: the claim does not survive (negative result)

**Claim under test.** "Claude is better at subtext — characters meaning something other than
what they say." **Verdict: not supported; contradicted by the only direct measurement.**

**Evidence tier: A.** `lechmazur/writing_styles` scored 15,347 flash-fiction stories from 29
models on ~10 numeric style axes including explicit *dialogue subtext*
([repo](https://github.com/lechmazur/writing_styles), data generated December 2025, README
updated 2025-12-18). Verbatim from raw README:

> "Claude Sonnet 4.5 (no reasoning) and Mistral Large 3 use the most dialogue by volume …
> On *dialogue subtext*, Mistral Medium 3.1 leads, followed by GPT-5 Pro and GPT-5.2
> (medium reasoning)."

Claude appears there for dialogue *volume* and is absent from the subtext ranking.

**Corroborating negative, tier A.** The same author's rubric head-to-head of Claude Opus 4.1
vs GPT-5 (medium), built from three independent blinded critics with every quoted example
verified against source text
([raw report](https://raw.githubusercontent.com/lechmazur/writing_styles/main/inter_llm_comparison_summaries/claude-opus-4-1-20250805-0K__vs__gpt-5-medium.txt)),
lists under **RUBRIC: FAILURE MODES** for Claude:

> "A: Expository compression and didactic statements ('truth is…,' 'beauty is…') flatten
> subtext and reduce discovery at peak beats."

and gives GPT-5 the advantage on "voice and line craft … consistently more original and
musically controlled, with fresh metaphors".

**Contested — the other side, and it is a real tension.**
- The same report faults GPT-5 for "softer stakes and under-pressurized climaxes" and
  metaphor density that "veils mechanics or spatial logic".
- Claude Opus 5 ranks **1st of 124 on Show-Don't-Tell** in Finding 1 — which is close to a
  subtext proxy, and points the opposite way. Note the version gap: the didacticism finding
  is about **Opus 4.1**, the Show-Don't-Tell rank is **Opus 5**. It is entirely possible
  this was fixed.
- Finding 3's silence n-grams are arguably a *mechanism* for subtext even if the subtext
  axis does not rank Claude highly.

I present all three and pick none. What is safe to say: **no source supports Claude leading
on subtext, and one measures it leading elsewhere.**

**Assessment.** For the paper this is the most useful correction, because it inverts the
intuition that a strong prose model needs less structural scaffolding. The evidence says the
opposite: Claude's edge is structure, and its named prose failure is stating the theme.

---

## Finding 5 — Structure, causality, and decisions on the page

**Claim.** Claude's advantage is procedural legibility: clear cause-and-effect, early
orientation, decisions made on the page with visible consequences.

**Evidence tier: A**, same head-to-head report. Verbatim overview:

> "Across the set, A most consistently delivers clear causal spines with legible stakes,
> on-page decisions, and element use that drives outcomes; B most consistently offers
> distinctive voice, fresh image-systems, and deeper motif/thematic integration."

Specific Claude advantages listed: crisp orientation "within the first ~120 words",
"because/therefore chains" that "tighten options and culminate in decisive, on-page
choices", objects used "to effect change rather than stay symbolic", and "tone discipline
favors clarity and restraint".

**Corroborating, tier A.** On [`lechmazur/writing`](https://github.com/lechmazur/writing) —
44 models, 537 direct pairings, 62,860 evaluator judgements, each pair shown in both orders,
required story elements matched within pair, leaderboard retrieved 2026-08-16 — Claude Opus
5 ranks 1st (4.2, 96% estimated win chance), Claude Fable 5 2nd (3.3), Kimi K3 3rd (3.0),
GPT-5.6 Sol 4th (2.9).

**Caveats.** The evaluator roster is not named in the README, so self-preference
contamination cannot be ruled out. And *older* Claude models sit at ranks 13 and 15 on the
same board, below GPT-5.4 — this is a result about the current generation, not about Claude.

**Assessment.** Reasonably well supported, replicated across two benchmarks by different
authors, and consistent with Finding 1's axis shape. Most directly relevant to our pipeline:
Claude's edge is in exactly the layer we scaffold explicitly.

---

## Finding 6 — Refusal on ordinary creative prompts

**Claim.** Some Claude versions decline a material fraction of ordinary creative-writing
prompts.

**Evidence tier: A** for the counts, **D** for the interpretation. Verbatim footnotes from
the raw [`lechmazur/writing` README](https://github.com/lechmazur/writing) (retrieved
2026-08-16):

> "† Claude Opus 4.7 completed 347 of 400 stories."
> "‡ Claude Opus 4.8 high completed 399 of 400 stories."
> "§ Claude Fable 5 high completed 395 of 400 stories."

53 of 400 is 13.25%. **The README says "completed", not "refused"** — incompletion could be
API errors or truncation. The benchmark author reportedly attributed it to refusals in an X
post, which I could not verify and do not rely on. What is solid: Opus 4.7 failed to produce
a usable story on 13% of ordinary creative briefs where its sibling versions failed on 0.25%
and 1.25%.

**Practitioner corroboration, tier C/D.** Multiple identifiable authors report Opus 4.7 as
the regression point specifically:
- Bram Cohen, "Why Is Claude Turning Into An Asshole?", 2026-06-14 — reports Claude "frames
  everything as an argument between you and it" and that chat quality declined "clearly
  inversely correlated to their ability to code"
  ([bramcohen.com](https://bramcohen.com/p/why-is-claude-turning-into-an-asshole); HN
  discussion 48533308, where several commenters report never seeing it).
- HN 48919965 (~2026-07-16): a commenter reports Claude "too preachy and judgey for anything
  else" and ending a chat over a disallowed word; versions named Opus 4.6 (fine) → 4.7
  (worse) ([news.ycombinator.com/item?id=48919965](https://news.ycombinator.com/item?id=48919965)).
- HN 47801971, "Opus 4.7 is horrible at writing"
  ([link](https://news.ycombinator.com/item?id=47801971)).

**Assessment.** The completion counts are hard evidence of a version-specific problem and
line up with independent dated complaints naming the same version. That convergence is what
makes this credible; neither half would be convincing alone. Note the implication: **Claude
version choice matters more than Claude-vs-competitor for this failure mode.**

---

## Finding 7 — Long-form durability

**Claim.** Claude models hold output quality across a long generation where others decay.

**Evidence tier: A′.** The EQ-Bench longform benchmark has the model write an eight-chapter
novella (~1000 words/chapter) and judges each chapter separately
([longform-writing-bench](https://github.com/EQ-bench/longform-writing-bench)). Per-chapter
scores are published, so chapter-1→chapter-8 drift is directly computable. I computed it;
the benchmark does not publish it as a metric.

Over all 126 models:

| Group | n | Median ch1→ch8 change | Improved |
|---|---:|---:|---:|
| Claude | 14 | **−0.73** | 5 / 14 |
| Everything else | 112 | −2.24 | 2 / 112 |

Restricted to the top 30 by overall score, controlling for "good models decay less": Claude
median +0.06 (5 of 9 improved), non-Claude median −0.57 (1 of 21 improved).

| Rank | Model | Score | Slop | ch1 | ch8 |
|---:|---|---:|---:|---:|---:|
| 1 | claude-opus-5 | 86.3 | 5.64 | 17.51 | **18.04** |
| 2 | claude-fable-5 | 83.0 | 8.31 | 17.10 | **17.43** |
| 3 | claude-opus-4-7 | 81.8 | 9.06 | 16.77 | **16.99** |
| 4 | gpt-5.6-sol | 81.7 | 11.98 | 17.16 | 16.95 |
| 5 | claude-opus-4-8 | 80.8 | 9.39 | 16.89 | 16.85 |
| 6 | claude-sonnet-4-6 | 79.9 | 10.56 | 16.49 | 16.55 |
| 7 | kimi-k3 | 79.6 | 9.67 | 17.02 | 16.20 |

**Judge-bias caveat, stated plainly.** The judge is **Claude Sonnet 4** (README: "Models on
the EQ-Bench leaderboard are evaluated with Claude Sonnet 4 as a judge"). Claude judging
Claude is an uncontrolled self-preference confound and the *absolute* rankings should be
discounted for it. The degradation result is somewhat more robust, because a constant
self-preference offset cancels in a within-model chapter-1-vs-chapter-8 difference — but
only if the bias is constant across chapters, which is untested. **Treat this as suggestive,
not settled.** Re-running with a non-Anthropic judge would be cheap and worthwhile; I would
not cite it in a paper without that.

**And note the tension with §C.5** — this says quality holds over eight chapters while §C.5
shows self-contradiction inside 800 words. The judge scores prose quality, not factual
consistency. They are not measuring the same thing.

---

## Counter-evidence

### C.1 The "Claude cadence" — the strongest practitioner consensus found

**Tier C.** Independent, identifiable, dated sources converge on the same short list of
tics. This is the most cross-corroborated practitioner claim in the research — and it is a
criticism.

| Tic | Independent sources |
|---|---|
| "It's not X, it's Y" / binary antithesis | Zvi Mowshowitz; Breen; Carrie Jones; HN 49296740; HN 49040857 |
| Em-dash overuse | BSWEN; Carrie Jones; HN 49296740 |
| Sentence-fragment-for-punch paragraphs | Carrie Jones; HN commentary |
| "load-bearing" | Larsson; HN 48905248 |
| "worth stating plainly", "carry the argument" | HN 49040857 |
| Rule of three / three-part lists | Zvi Mowshowitz |

- Jerod Santo (Changelog), "Claude's writing style has me on edge", June 2026 — he now spots
  the voice "on Reddit, I see it on X, I see it on Hacker News, and I see it on LinkedIn",
  and finds the constant authentication check draining. 609-point HN thread
  ([jerodsanto.net](https://jerodsanto.net/2026/06/claudes-writing-style-has-me-on-edge/)).
- Johanna Larsson, "How to stop Claude from saying load-bearing", 2026-07-14 — built tooling
  because readers are "ripping your hair out" over "load-bearing" and "honest takes"
  ([jola.dev](https://jola.dev/posts/how-to-stop-claude-from-saying-load-bearing)).
- HN 49296740 (~2026-08-14) on Opus 5: top comment says it "writes too elliptically"; a
  highly-upvoted reply describes a fixed template — setup, bullets, twist, bottom line —
  applied to "every prompt"
  ([link](https://news.ycombinator.com/item?id=49296740)).
- HN 49040857 (~2026-07-25): Opus 5 retains claudisms that Fable 5 drops — "carry the
  argument", "worth stating plainly" — with a proposal for "an annoying English benchmark"
  ([link](https://news.ycombinator.com/item?id=49040857)).
- Benjamin Breen (historian, UC Santa Cruz), Res Obscura — names "the infamous 'it's not
  that; it's this' formula", while also writing that "the most recent Anthropic models
  actually write quite well"
  ([resobscura](https://resobscura.substack.com/p/what-is-happening-to-writing)).
- Carrie Jones (fiction author), 2026-03-21 — story-level tells: em-dash per paragraph,
  fragment-paragraphs before hooks, self-declaratory sentences; cites a Claude sample from
  the NYT AI-writing quiz
  ([livinghappy](https://livinghappy.substack.com/p/what-makes-a-story-look-like-ai-wrote)).
- Pangram (AI-detection vendor), 2024-12-06 — Claude's built-in style presets barely move
  the needle: variants "still sound pretty similar to Claude's normal writing style" and all
  stayed detectable. Single vendor study
  ([pangram.com](https://www.pangram.com/blog/claude-writing-styles)).

**Important scope limit.** These are tics of the **essay/analysis register**, not of fiction.
No source found names fiction-cadence phrases ("the air was thick with", "something shifts",
"a beat") as *Claude* tics. Claude's measured *fiction* tics are the different set in §C.2.

### C.2 Claude's own fiction tics

From the n-gram profiles in Finding 3, tier A′:

- **Silence as the default beat.** "Nobody said anything", "Neither of them said anything",
  "without saying anything". Used as often as GPT-5 uses "throat tightened" — the same
  reflex pointed the other way.
- **Hand choreography.** "put her hand flat" (4), "put both her hands flat", "stood there
  with his hands hanging", "put his hand over his mouth".
- **Duration beats.** "looked at it for a long time", "looked at him for a long moment",
  "stood there for a long time".
- **Numeric specificity as texture.** "ten past four", "ten past eleven", "eighteen months
  ago", "three weeks ago"; in the word list, an obsession with "eleven".
- **Concrete-object vocabulary.** doorframe, windowsill, sill, sash, ledger, tarp,
  clipboard, spanner, cardigan.

For file 10 this is the load-bearing point: **instructing a model toward "restraint" without
constraining the restraint vocabulary reproduces Claude's tics instead of GPT's.** A ban
list must cover both registers.

### C.3 Positivity bias and soft resolution — genuine, and contested by the benchmark

**Tier A** from the Claude-vs-GPT-5 rubric report's failure modes:

> "A: Convenience and low-cost resolutions (instant validations, soft antagonists,
> off-screen consequences) undercut pressure and earnedness."

Its remedy is explicit: "stage at least one failure beat or counter-force before the turn."

**Corroborating at family level, tier A.** `writing_styles` finds "Positive endings
dominate" across all 29 models, with ambiguous endings concentrated in GPT-5.1, Gemini 3 Pro
Preview and Mistral Large 3 — **Claude is not among the leaders for ambiguous endings.** So
restraint in the sense of *refusing to resolve* is not a Claude property; its restraint is
lexical and reactive, not structural.

**Sycophancy, tier C/D.** The Register, 2025-08-13 quotes a user: "Claude is way too
sycophantic, saying 'You're absolutely right!' … on a sizable fraction of responses"
([theregister.com](https://www.theregister.com/2025/08/13/claude_codes_copious_coddling_confounds/)).
Repeated user issues exist on `anthropics/claude-code` (#7112, #5124). This is coding
context, not fiction.

**Directly contested by Finding 1**, where Claude Opus 5 ranks **1st of 124 on "Avoids
Positivity Bias"**. Given the judge is Claude Sonnet 4.6, I read this divergence as more
likely to indict the benchmark than the practitioners — but I cannot prove that, and it
stays flagged as contested.

### C.4 Claude is not the most stylistically varied model

**Tier A**, `writing_styles` within-model diversity (weighted Gower mean pairwise distance
across a model's own stories, 0–1): GPT-5 (medium) 0.218 and GPT-5.2 (medium) 0.215 lead;
Kimi K2 Thinking 0.210 is 5th; **Claude Opus 4.1 9th (0.202), Sonnet 4.5 Thinking 14th
(0.197), Sonnet 4.5 16th (0.195), Opus 4.5 25th (0.189)** of 29. Claude's stories resemble
each other more than GPT-5's do.

For a system generating many scenes, this is the finding that should worry us most: it
predicts sameyness across a long book and is not fixable by a ban list. Note the total
spread is small (0.047) — the ranking is real, the effect modest, and homogeneity is
industry-wide (≈100% past tense, 99.8% earnest stance, 82–99% linear chronology).

### C.5 Continuity errors at 600–800 words

`writing_styles` publishes per-model failure catalogues with quoted source text
(`poor_writing/`). Claude's entries are dominated by **state and arithmetic contradictions**,
not prose failures. Verified from `poor_writing/claude-opus-4-5-20251101-0K.txt` and
`...opus-4-1...txt`:

- An object given away and still in the giver's pocket a beat later.
- "sealed inside" and "kept" used of the same letters; a shell "full to bursting" then "the
  empty shell".
- Counts drifting mid-scene (seven fragments become six and still "complete"; seventeen,
  eighteen, then nineteen gears).
- Timeline arithmetic that does not close ("Sixteen weeks is not 'three months'").
- A character both 17 and "fourteen, like you are now".

**This is not evidence Claude is uniquely bad** — every model has such a file, and GPT-5.2's
lists state contradictions too. The finding is that **even the top-ranked prose model
produces continuity violations at 800 words**, which is a direct argument for the explicit
state-tracking layer this project builds.

There is a tension worth naming: Finding 7 says Claude holds up over eight chapters, while
this shows it contradicting itself inside one short story. The likely reconciliation is that
the longform judge scores *prose and chapter quality*, not cross-chapter factual
consistency — **nobody is measuring the thing §C.5 measures at novella length.** That gap is
a research opportunity for us.

**Practitioner corroboration, tier B/D.** BSWEN's 301K-word novel writeup (2026-02-24)
reports eye colour drifting "from 'storm clouds' to 'blue' across chapters" and forgotten
character habits by chapter 80, with a self-reported ~40% detail-error rate over long form
(method unclear)
([docs.bswen.com](https://docs.bswen.com/blog/2026-02-23-claude-creative-writing-pros-cons/)).
Kelly Balthrop names "temporal confusion" — "Claude treats all narrative information as
equally present" — and dialogue where characters explain "things they both already know"
([wbalthrop](https://wbalthrop.substack.com/p/writing-fiction-with-claude), 2025-11-17).

### C.6 The regression debate — both sides

**"Newer Claude is worse at prose":**
- Zvi Mowshowitz, "Claude Opus 4.6 Escalates Things Quickly" — notes "AI slop-style writing
  in its now-longer replies" and quotes multiple named users, e.g. "Opus 4.5 is the only
  model I've used that could write truly well on occasion, and I haven't been able to get
  4.6 to do that"
  ([thezvi](https://thezvi.substack.com/p/claude-opus-46-escalates-things-quickly)).
  Multiple independent users, one post.
- HN 47801971, "Opus 4.7 is horrible at writing": "It feels like they tuned it so hard for
  logic and coding that it lost its soul."
- HN 48608839 (~2026-06-21): getting worse "from version to version, descending into self
  parody" ([link](https://news.ycombinator.com/item?id=48608839)).
- Opus 3 nostalgia is organised: Anthropic retired Opus 3 in Jan 2026 but kept it for paid
  users ([deprecation note](https://www.anthropic.com/research/deprecation-updates-opus-3)),
  and a "Stop Killing Claude" petition argues models "are not interchangeable tools".

**"Newer Claude is better":**
- `lechmazur/writing`, 2026-08-14: Claude Opus 5 is **#1** of 44 models; older Claudes rank
  13th and 15th.
- EQ-Bench longform overall, monotone improvement: claude-3.5-sonnet 58.4 → sonnet-4.5 71.4
  → opus-4-5 73.1 → opus-4-6 77.7 → sonnet-4-6 79.9 → opus-4-8 80.8 → opus-4-7 81.8 →
  fable-5 83.0 → **opus-5 86.3**. Slop falls in the same direction.
- Several HN commenters in 49296740 and 48533308 report never seeing the degradation and
  attribute it to Claude Code vs web UI, or to prompting.

**How to read the contradiction.** Benchmarks measure per-output craft quality; the
complaints are about *stylistic sameness and recognisability*, which no benchmark scores.
Both can be true simultaneously, and the diversity result in §C.4 is the bridge: quality up,
variety not.

### C.7 Anthropic's own segmentation is evidence

Anthropic ships **Fable 5**, a creative-writing-specific model, which outranks general Opus
4.7/4.8 on both benchmarks. Shipping a separate fiction model is an implicit concession that
general-purpose Claude was not the right tool for prose.

### C.8 The purple-prose complaint points the wrong way

Practitioners complain about Claude overwriting (BSWEN: "Claude uses em-dashes excessively
in creative writing," requiring "extensive post-editing"). But on the benchmark, **Avoids
Purple Prose is one of Claude's best axes** (Opus 5 ranks 2nd of 124). The practitioner and
benchmark complaints are about *different failures*: floridity versus flatness and sameness.
Finding 1 shows Claude's genuinely weak axes are Descriptive Imagery and Creativity — i.e.
the criticism that survives is **under**-writing, not over-writing.

### C.9 Other models on specific axes — mostly unsourceable

- **Kimi:** K2 took #1 on EQ-Bench creative writing in July 2025
  ([dbreunig](https://www.dbreunig.com/2025/07/31/how-kimi-rl-ed-qualitative-data-to-write-better.html)).
  As of Aug 2026 K3 is #3 on `lechmazur/writing` behind two Claudes. Real, but a closed
  window.
- **DeepSeek "unhinged/more human" prose:** widely asserted, never traceable to a citable
  source. DeepSeek's measured slop is far worse (V4-Pro 21.83 vs opus-5 5.64).
- **Gemini for long-context continuity:** asserted everywhere, sourced nowhere credible —
  every instance found traces to SEO comparison sites. **Do not cite.**
- **"GPT for structure, Claude for prose":** the most repeated division of labour found, and
  every instance is on a commercial comparison site. Folk consensus of unclear provenance —
  and note Finding 5 says the opposite (Claude's edge *is* structure).

---

## What I could not find evidence for

Stated plainly, because a padded section is worse than an honest gap.

- **Voice separability between characters.** No benchmark measures whether two characters in
  the same story sound different from each other. `writing_styles` measures *model* style
  fingerprints and dialogue volume, not within-story inter-character distinctiveness. No
  eval, dataset or quantified practitioner claim found. **This is a cheap gap our project
  could fill**, and probably the most publishable one on this list.
- **The "assistant voice" leaking into narration.** Widely referenced; no measurement, and
  no source isolating it per model with examples.
- **Instruction adherence to a *style constraint* over thousands of tokens.** Finding 7
  measures quality persistence, not constraint persistence. No source tests "hold this
  stylistic rule for 8,000 words" per model.
- **Prose rhythm / sentence-length variation.** `writing_styles` has a rhythm axis but
  publishes no per-model ranking naming Claude; no source gives sentence-length
  distributions per model. EQ-Bench's "Sentence Flow" is a judge impression, not a measure.
- **Dramatic structure — scene turns, escalation, withholding.** Finding 5 speaks to causal
  escalation qualitatively; there is no dedicated measurement and no per-model numbers.
- **Fiction-cadence phrases as Claude tics** — "the air was thick with", "something shifts",
  "a beat", "somewhere between X and Y". **No source attributes these to Claude.** They are
  documented as generic RP/fine-tune clichés (Sukino list) but not as Claude's. Anyone
  asserting them needs separate evidence.
- **"Shivers down the spine" / "ministrations" as Claude tics.** Documented as
  Character.AI/fine-tuned-RP clichés; nothing pins them on Claude.
- **Sycophancy specifically in fiction** (characters forgiving too easily, conflict
  dissolving). [`lechmazur/sycophancy`](https://github.com/lechmazur/sycophancy) benchmarks
  narrator-bias sycophancy and academic work exists generally
  ([arxiv 2310.13548](https://arxiv.org/pdf/2310.13548)), but neither measures the fiction
  failure mode. §C.3 is the closest real evidence and it is qualitative.
- **A working novelist leaving Claude for cost or context reasons.** All such material found
  is SEO pricing content or coding-workflow content. No fiction-writer testimony.
- **Anthropic primary documentation** for the "long conversation reminder" text and for any
  official "less preachy in 4.8" claim. Both currently rest on secondary sources and are not
  relied on here.

---

## Sources

All retrieved 2026-08-16 unless noted; every figure re-verified from raw data files.

**Tier A benchmarks**
- EQ-Bench Longform Creative Writing v3 — <https://eqbench.com/creative_writing_longform.html>; raw <https://eqbench.com/creative_writing_longform.js> (126 models)
- EQ-Bench Creative Writing v3 — <https://eqbench.com/creative_writing.html>; raw <https://eqbench.com/creative_writing.js> (125 models); per-axis raw <https://eqbench.com/creative_writing_chartdata.js> (124 models)
- EQ-Bench Slop Score methodology — <https://eqbench.com/slop-score.html>
- longform-writing-bench (judge = Claude Sonnet 4) — <https://github.com/EQ-bench/longform-writing-bench>
- creative-writing-bench v3 (judge = Claude Sonnet 4.6) — <https://github.com/EQ-bench/creative-writing-bench>
- slop-forensics — <https://github.com/sam-paech/slop-forensics>; antislop-sampler — <https://github.com/sam-paech/antislop-sampler>
- lechmazur/writing (44 models, 62,860 judgements) — <https://github.com/lechmazur/writing>
- lechmazur/writing_styles (29 models, 15,347 stories, Dec 2025) — <https://github.com/lechmazur/writing_styles>
- Claude Opus 4.1 vs GPT-5 rubric head-to-head — <https://raw.githubusercontent.com/lechmazur/writing_styles/main/inter_llm_comparison_summaries/claude-opus-4-1-20250805-0K__vs__gpt-5-medium.txt>
- Per-model failure catalogues — `poor_writing/claude-opus-4-5-20251101-0K.txt`, `poor_writing/claude-opus-4-1-20250805-0K.txt`, same repo
- lechmazur/position_bias — <https://github.com/lechmazur/position_bias>; lechmazur/sycophancy — <https://github.com/lechmazur/sycophancy>
- Kimi K2 EQ-Bench #1, 2025-07-31 — <https://www.dbreunig.com/2025/07/31/how-kimi-rl-ed-qualitative-data-to-write-better.html>

**Tier B practitioner artifacts**
- anthracite-org/magnum-v4-72b, 2024-09 — <https://huggingface.co/anthracite-org/magnum-v4-72b>
- Sukino SillyTavern banned-phrase list (375 entries, verified line count) — <https://huggingface.co/Sukino/SillyTavern-Settings-and-Presets/raw/main/Banned%20Tokens.txt>
- NousResearch/autonovel ANTI-SLOP.md — <https://raw.githubusercontent.com/NousResearch/autonovel/master/ANTI-SLOP.md>
- hardikpandya/stop-slop — <https://github.com/hardikpandya/stop-slop>
- Pangram, Claude writing styles, 2024-12-06 — <https://www.pangram.com/blog/claude-writing-styles>

**Tier C/D practitioner commentary**
- Jerod Santo, June 2026 — <https://jerodsanto.net/2026/06/claudes-writing-style-has-me-on-edge/>
- Johanna Larsson, 2026-07-14 — <https://jola.dev/posts/how-to-stop-claude-from-saying-load-bearing>
- Zvi Mowshowitz on Opus 4.6 — <https://thezvi.substack.com/p/claude-opus-46-escalates-things-quickly>
- Bram Cohen, 2026-06-14 — <https://bramcohen.com/p/why-is-claude-turning-into-an-asshole>
- Benjamin Breen, Res Obscura — <https://resobscura.substack.com/p/what-is-happening-to-writing>
- Carrie Jones, 2026-03-21 — <https://livinghappy.substack.com/p/what-makes-a-story-look-like-ai-wrote>
- Kelly Balthrop, 2025-11-17 — <https://wbalthrop.substack.com/p/writing-fiction-with-claude>
- Jessica Waldron, 2026-02-01 — <https://theinvisiblepen.substack.com/p/the-plot-twist-i-didnt-see-coming>
- Kenny Kane, July 2026 — <https://kenny-kane.com/claude-for-writing-a-book>
- BSWEN 301K-word novel, 2026-02-24 — <https://docs.bswen.com/blog/2026-02-23-claude-creative-writing-pros-cons/>
- Novelcrafter model guidance — <https://www.novelcrafter.com/help/faq/ai-and-prompting/what-ai-should-i-use>
- The Register on sycophancy, 2025-08-13 — <https://www.theregister.com/2025/08/13/claude_codes_copious_coddling_confounds/>
- HN threads: [47801971](https://news.ycombinator.com/item?id=47801971), [48533308](https://news.ycombinator.com/item?id=48533308), [48608839](https://news.ycombinator.com/item?id=48608839), [48919965](https://news.ycombinator.com/item?id=48919965), [49040857](https://news.ycombinator.com/item?id=49040857), [49296740](https://news.ycombinator.com/item?id=49296740)

**Background**
- Sycophancy in language models — <https://arxiv.org/pdf/2310.13548>
- Anthropic Opus 3 deprecation — <https://www.anthropic.com/research/deprecation-updates-opus-3>
- Anthropic crawler / Reddit access — <https://support.anthropic.com/en/articles/8896518>
