# Prose system-prompt addendum

Derived entirely from `09-anthropic-prose-research.md`. Every clause maps to a numbered
finding there; the mapping table is below. Anything I could not trace was cut, and the cuts
are listed too.

Intended use: append to the scene-writing call's system prompt, after the schema
instructions. It aims to push a **non-Anthropic** model toward the qualities the research
actually supports — lexical and structural discipline — while avoiding the trap identified
in §C.2: an instruction to "show restraint" reproduces Claude's tics instead of GPT's unless
the restraint vocabulary is itself capped.

---

## The prompt

```
PROSE CONSTRAINTS

Emotion is carried by what a character does, chooses, or withholds — never by an
involuntary body reaction. Banned outright:

  mouth went dry · throat tightened · jaw tightened · stomach dropped ·
  blood ran/went cold · heart hammered/pounded · breath caught · pulse quickened ·
  chest tightened · fingers tightened around · knuckles white · eyes flicked ·
  gaze flicked · eyes snapped open · squeezed her eyes shut · shiver(s) down/up ·
  spine · skin crawled · felt a mix of

Dialogue tags: use "said" and "asked". Never append a voice modifier ("said, voice
low / flat / rough / tight / trembling", "barely above a whisper", "voice thick
with"), and never reuse the same tag template twice in a scene. Banned speech verbs:
rasped, hissed, purred, growled, breathed, wheezed, droned, stammered, shrieked,
chuckled darkly.

Banned phrases:
  couldn't help but · despite herself/himself · her/his eyes sparkled, gleamed,
  glinted, twinkled, glowed · half-lidded · husky · ministrations · dimly lit ·
  ethereal · kaleidoscope · cacophony · a testament to · tapestry · symphony ·
  delve · realm · myriad · the air was filled with · the air was thick with ·
  like a physical blow · took a step toward

Banned structures:
  - "Not just X, but Y" and every variant ("It wasn't X. It was Y."). This is the
    single most over-represented rhetorical pattern in LLM prose.
  - Tricolons for emphasis (three parallel items or clauses).
  - Ending a scene or section on a portentous one-line fragment.
  - More than two em dashes per thousand words.
  - Stating the theme. No aphorisms, no "truth is…", no sentence explaining what the
    scene meant. If deleting a sentence loses only the moral, delete it.

Do not overcorrect into silence. Withheld reactions are also a tic. Per scene use at
most ONE of: a character saying nothing; a character looking at something "for a long
time"; a described hand placement; an explicit clock time. Vary which one.

Imagery must be specific and load-bearing: name the actual object, material or
measurement rather than reaching for an abstraction. One fresh concrete image per
scene beats three decorative ones.

STRUCTURE

  - Establish who, where, and the problem within the first 120 words.
  - Every beat connects to the next by "because" or "therefore", never "and then".
  - The viewpoint character makes at least one decision on the page, and its
    consequence appears in this scene, not off-screen.
  - Stage one failure, refusal, or counter-force BEFORE any turn resolves. No instant
    validations, no soft antagonists, no consequences deferred off-screen.
  - Objects named in the scene must do something that changes an outcome. If an object
    is only symbolic, cut it.
  - A resolution must cost something nameable. Endings may be negative or unresolved;
    do not default to positive.

CONSISTENCY (check before returning)

  - Counts, ages, dates, elapsed time and clock times must be arithmetically consistent
    with everything already established. Recompute; do not estimate.
  - Every object has one location at a time. If it changes hands, say so.
  - A physical state asserted (sealed, empty, dark, frozen) stays true until something
    on the page changes it.

VARIETY ACROSS SCENES

  - Do not reuse the previous scene's opening move, closing move, or POV distance.
  - Vary tense, person, and chronology across the work; not every scene is close-third,
    past tense, linear.
```

Prompt body: ~3,500 characters — inside the 2,000–4,000 target.

---

## Provenance

| Clause | Finding | Basis |
|---|---|---|
| Somatic-tell ban list | 3, §C.2 | Measured top n-grams: gpt-5.2 "mouth went dry" 26×, "fingers tightened around" 14×, "throat tightened" 8×, "blood went cold" 8×, "eyes flicked" 18×; Gemini 3 Pro "squeezed her eyes shut" 4×, "eyes snapped open" 4×. 16 somatic n-grams in gpt-5.2's top-30 vs ≤2 for all 14 Claude models |
| "shivers down/up", "spine", "felt a mix of", "barely above a whisper", "couldn't help but", "despite herself", eye-sparkle set, "half-lidded", "husky", "ministrations", "dimly lit", "ethereal", "kaleidoscope", "cacophony", "the air was filled with", "the air was thick with", "voice thick with" | 2 | All verified present as literal entries in the Sukino SillyTavern banned-token list (375 lines, checked line-by-line: e.g. L23 " air was filled with", L32 "barely above a whisper", L145 "felt a mix of", L235–241 shiver set, L358 " air was thick with", L374–376 "voice thick with") |
| Voice-modifier tag ban; no repeated tag template | 3 | Gemini 3 Pro's profile is dominated by "said, his voice dropping / her voice flat / trembling / rough / steady / devoid"; gpt-5.2 by "said, voice low / rough / flat / tight". The repeated *template* is the tell, not any single instance |
| Speech-verb ban | 3 | Gemini 3 Pro top repetitive words: rasped, wheezed, hissed, grunted, droned, shrieked, stammered, whimpered. "chuckles darkly" from the Sukino list |
| "a testament to", "tapestry", "delve", "realm", "myriad" | 2 | NousResearch/autonovel `ANTI-SLOP.md` Tier 1 "kill on sight"; corroborated by antislop-sampler examples ("a tapestry of", "a testament to") |
| "Not just X, but Y" ban | 2, §C.1 | 25% of EQ-Bench's slop score is the not-x-but-y family; autonovel calls it "the single most overused rhetorical pattern in LLM output"; and it is the #1 cross-sourced practitioner-named tic in §C.1 (Zvi, Breen, Jones, two HN threads) |
| Tricolon ban; em-dash cap; no portentous closing fragment | §C.1 | The other three items on the cross-sourced practitioner tic list: rule-of-three, em-dash overuse, fragment-for-punch. Em-dash cap number from autonovel ("1–2 per page") |
| Ban on stating the theme / aphorisms | 4 | Claude-vs-GPT-5 rubric report's named failure mode: "Expository compression and didactic statements ('truth is…,' 'beauty is…') flatten subtext and reduce discovery at peak beats" |
| Cap on silence beats, "long time", hand placements, clock times | §C.2 | Claude's own measured tics: "Nobody said anything" 7×, "without saying anything" 3×, "put her hand flat" 4×, "looked at it for a long time" 4×, "ten past four"/"ten past eleven". Without a cap, a restraint instruction swaps one tic register for another |
| Imagery must be specific and load-bearing | 1, §C.8 | Descriptive Imagery is Claude Opus 5's *weakest* axis (13th of 124) and Creativity 6th, against 1st-place ranks on all the discipline axes. §C.8: the criticism that survives scrutiny is under-writing, not over-writing — so the prompt must push *for* imagery while banning decorative slop |
| Orientation in 120 words; because/therefore; on-page decision with visible consequence; objects must do work | 5 | Verbatim advantages listed for Claude in the rubric head-to-head: orientation "within the first ~120 words", "because/therefore chains", "decisive, on-page choices with visible consequences", objects "used to effect change rather than stay symbolic" |
| Stage a failure before the turn; no instant validations or soft antagonists; resolution must cost | §C.3 | Claude's named failure mode — "Convenience and low-cost resolutions (instant validations, soft antagonists, off-screen consequences) undercut pressure and earnedness" — plus the report's own remedy: "stage at least one failure beat or counter-force before the turn" |
| Endings may be negative or unresolved | §C.3 | `writing_styles`: "Positive endings dominate" across all 29 models; ambiguous endings concentrate in GPT-5.1, Gemini 3 Pro, Mistral Large 3 |
| Arithmetic / object-location / state-persistence checks | §C.5 | Verified failure catalogue: counts drifting (7→6 fragments; 17→18→19 gears), "Sixteen weeks is not 'three months'", sealed-and-kept, full-then-empty, object in pocket after being given away |
| Vary opening/closing move, POV distance, tense, person, chronology | §C.4 | Within-model diversity: Claude ranks 9th/14th/16th/25th of 29; `writing_styles` also finds ~100% past tense, 99.8% earnest stance, 82–99% linear chronology across all models — the homogeneity is industry-wide |

---

## Cut for lack of evidence

Listed so the discipline is visible, and because the first two are the instructions a reader
would most expect to see.

- **"Vary sentence length; no more than two consecutive sentences of similar length."** The
  obvious rhythm rule. Cut: no source gives per-model sentence-length distributions, and
  `writing_styles`'s rhythm axis publishes no ranking naming Claude (09 §"could not find").
  EQ-Bench's "Sentence Flow" is a judge impression, not a measurement. The nearest traceable
  thing is the ban on repeated *clause templates*, which is in the prompt and is evidenced.
- **Anything about giving two characters distinguishable voices.** No benchmark measures
  within-story inter-character voice separability. Nothing to trace an instruction to — and
  09 flags this as the most publishable gap for us.
- **Anything about the "assistant voice" leaking into narration.** Widely asserted, never
  measured.
- **"the air was thick with"-style fiction-cadence phrases as *Claude* tics.** The phrase is
  in the prompt, but sourced to the Sukino RP list as a generic cliché — **not** as a Claude
  tic, because 09 found no source making that attribution.
- **A broader "don't moralise" rule.** The theme-statement clause traces to a specific rubric
  finding; a general anti-preaching rule does not, and the primary threads asserting it were
  unreachable (Reddit blocked).

---

## What this will not fix

- **Homogeneity across a long work.** The most relevant weakness (§C.4) is that a model's
  stories resemble each other. A ban list removes shared *vocabulary*; it does not create
  structural variance, and the diversity spread across all 29 models was only 0.047 — that
  looks like a property of the training distribution, not of prompting. If our scenes come
  out samey, the fix belongs in the planning layer (forcing different scene shapes in the
  plot spine), not here.
- **Continuity.** The consistency block will catch some arithmetic, but §C.5 shows frontier
  models contradicting themselves inside 800 words. Self-check instructions are weak against
  this; the state-fold and validator are the actual defence. `05-model-behaviour.md` §8
  already found that asking harder does not fix structural failures — only structure does.
  Do not treat this prompt as a substitute.
- **Subtext.** Nothing here produces it. The research found no model that reliably does, and
  found the popular belief that Claude does to be unsupported (Finding 4). The prompt can
  forbid *stating* the theme; it cannot make implication land.
- **Ban-list evasion.** Banning "mouth went dry" invites "her mouth was dry". Enforcement
  wants a post-hoc string check with morphological variants — ideally the slop-forensics
  lists — not trust in instruction-following.
- **The frontier-compression problem.** Finding 1's caveat applies to any evaluation we run:
  judged axes separate the top ten models by only 0.22–0.94 points on a 20-point scale. If
  we A/B this prompt with an LLM judge we will probably measure nothing. **Score it with the
  string-level slop metric**, which has a ~10× dynamic range across models, and only then
  look at judge scores.
- **It is untested.** Every clause traces to a finding, but the prompt as a whole has not
  been run against our pipeline. The first check should be generating a scene set with and
  without this block and scoring both on slop, per the 05 methodology.
