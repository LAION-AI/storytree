# The roleplay-finetune ecosystem as evidence

Companion to [`09-anthropic-prose-research.md`](09-anthropic-prose-research.md). That file
asks what benchmarks measure; this one asks a different question with a different kind of
answer: **what have practitioners spent money and compute to imitate?**

Revealed preference is weaker than measurement but stronger than opinion. A finetuner who
writes a training pipeline to reproduce a model's prose has made a costly, falsifiable
commitment that a forum post has not.

All URLs fetched 2026-08-15/16.

---

## 1. The canonical case: Magnum

`anthracite-org` shipped a model family whose stated purpose is imitating Claude's prose.
The mission sentence is identical across the family:

> "This is a series of models designed to replicate the prose quality of the Claude 3
> models, specifically Sonnet and Opus."
> — [`anthracite-org/magnum-v4-72b`](https://huggingface.co/anthracite-org/magnum-v4-72b), 2024-09

Present verbatim on v1-72b (2024-06-17), v2-72b, v3-34b, and every v4 size (9b–123b).

Training sets named on the v4 card: `c2_logs_32k_llama3_qwen2_v1.2`,
`kalo-opus-instruct-22k-no-refusal`, `lodrick-the-lafted/kalo-opus-instruct-3k-filtered`,
`anthracite-org/nopm_claude_writing_fixed`, `kalo_opus_misc_240827`, `kalo_misc_part2`.

**The family stops at v4** (Nov 2024). No v5 exists. Successor work moved to other authors.

### Downstream restatements

- [`DS-Archive/L3.3-70B-Magnum-v4-SE`](https://huggingface.co/Doctor-Shotgun/L3.3-70B-Magnum-v4-SE),
  Jan 2025 — "The objective, as with the other Magnum models, is to emulate the prose style
  and quality of the Claude 3 Sonnet/Opus series of models on a local scale, so don't be
  surprised to see 'Claude-isms' in its output."
- [`Delta-Vector/Rei-12B`](https://huggingface.co/Delta-Vector/Rei-12B), 2025-01 — "designed
  to replicate the prose quality of Anthropic's Claude 3 series."

**And the counter-example, from the same author**:
[`Delta-Vector/Tor-8B`](https://huggingface.co/Delta-Vector/Tor-8B) trains on the *same*
Claude-derived sets but states it "aims to have generally good prose and writing **while not
falling into claude-isms**." The same data, the opposite aesthetic goal. That single
contrast is the most honest summary of the ecosystem's view: the style is desirable and
recognisable, and recognisability is itself the complaint.

## 2. Datasets built from Claude output

| Dataset | Date | What the card says |
|---|---|---|
| [`Nopm/Opus_WritingStruct`](https://huggingface.co/datasets/Nopm/Opus_WritingStruct) | 2024-07 | generated with Claude 3 Opus, to have it "more openly use its excellent prose" |
| [`Gryphe/Opus-WritingPrompts`](https://huggingface.co/datasets/Gryphe/Opus-WritingPrompts) | 2025-01 | 3,008 stories from Claude Opus |
| [`Gryphe/ChatGPT-4o-Writing-Prompts`](https://huggingface.co/datasets/Gryphe/ChatGPT-4o-Writing-Prompts) | 2025-01 | the deliberate GPT-4o control set, same prompts |
| [`Gryphe/Sonnet3.5-Charcard-Roleplay`](https://huggingface.co/datasets/Gryphe/Sonnet3.5-Charcard-Roleplay) | 2024-08 | 9,736 dialogues, each generated in one call "to prevent AI incoherence" |
| [`kalomaze/Opus_Instruct_25k`](https://huggingface.co/datasets/kalomaze/Opus_Instruct_25k) | 2024-07 | Opus instruction data |
| [`nothingiisreal/Claude-3-Opus-Instruct-15K`](https://huggingface.co/datasets/nothingiisreal/Claude-3-Opus-Instruct-15K) | 2024-07 | "Claude is weird when prompted zero-shot" |

**The Gryphe pair is the sharpest artifact here.** The Opus and GPT-4o sets cover the same
prompts, and the card states the GPT-4o counterpart was added "for KTO training purposes" —
that is, **Opus as chosen, GPT as rejected**, at dataset-construction time. Somebody built a
preference dataset whose preference direction is "sounds more like Claude".

### The 2026 wave, and how small it is

[`Gryphe/WorldSim-Opus-3.6-35B-A3B`](https://huggingface.co/Gryphe/WorldSim-Opus-3.6-35B-A3B)
(2026-05) is the main current-generation prose-targeted Claude distill: 50% aggregated Opus
4.6 reasoning traces, 40% long-form narrative roleplay with full traces. Its companion
dataset [`Gryphe/Opus-4.6-Reasoning-24k`](https://huggingface.co/datasets/Gryphe/Opus-4.6-Reasoning-24k)
has 24,138 rows aggregated from seven community trace dumps.

Otherwise **the Claude-named HF landscape in 2026 has shifted away from prose entirely.**
Querying by downloads returns reasoning and agentic distills. Two checked directly
(`AnkitAI/Parable-Qwen3-8B-Claude-Fable-5`, `empero-ai/Qwythos-9B`) are coding/agentic trace
distills with no prose claim. **The prose-distillation wave was 2024.**

## 3. What practitioners say they want, ranked by recurrence

1. **Prose quality as separable from intelligence.** The Magnum mission sentence is the most
   copied sentence in the ecosystem, restated verbatim by three unrelated finetuners.
2. **Nuance.** [Marinara](https://spicymarinara.github.io/) (top preset author, 2026-04):
   "Claude is the king of nuance."
3. **Steerability, not just quality.** Same source: "the instruction-following skill is so
   good that you can easily get rid of the most overused phrases." Sudowrite's docs praise
   Sonnet 4.5 for following instructions "rather than smoothing everything into generic prose."
4. **Style mimicry.** NovelCrafter's official help: "For natural sounding prose, that can
   mimic your style, use an Anthropic Claude model such as Sonnet."
5. **A recognisable voice, framed as a feature** — see §4.
6. **Measurably less slop** — corroborates Finding 2 in file 09.

### The complaints are equally consistent

Cost; positivity bias; NSFW restrictiveness; and the house style. From
[Purachina's Director Preset](https://platberlitz.github.io/): "I still find myself getting
**Opus fatigue**. It has a **'Claude voice'** — a character card that isn't defined enough
will be overtaken by Claude's personality… The positivity bias is intense."

Note the same author observes the effect is **version-specific**: "Friction Mode… especially
in Opus. For some reason, **Sonnet doesn't really have this problem.**"

## 4. SillyTavern's own documentation

The strongest single line, because it is official documentation of a neutral tool making a
comparative claim ([API Connections](https://docs.sillytavern.app/usage/api-connections/),
last commit 2026-02-16):

> **OpenAI (ChatGPT)** — … Very logical. Creative style can be repetitive and predictable
> **Claude (by Anthropic)** — Recommended for users who want their AI chats to have a
> creative, unique writing style … Requires a specific prompting style and utilization of
> prefills for reply steering

Claude-specific engineering in the codebase: `claude_assistant_prefill`,
`claude_assistant_impersonation`, dedicated `convertClaudeMessages()`, a dedicated config
block, and its own reasoning-effort column. Notably, `PROMPT_PROCESSING_TYPE.CLAUDE` was the
original name of what is now the generic `MERGE` mode — **Claude's message format became the
default shape other backends are converted into.**

**Negative finding worth recording:** SillyTavern ships *no* Claude preset. All are
community-distributed. Do not cite the docs for the banned-strings feature either — a
repo-wide grep for "banned" in `SillyTavern-Docs` returns zero hits.

### Revealed preference: bridges built to reach Claude

Three separate projects exist solely to route a Claude *subscription* into a roleplay
frontend — [claude-code-proxy](https://github.com/horselock/claude-code-proxy) (184★),
[claude-code-sillytavern-bridge](https://github.com/MissSinful/claude-code-sillytavern-bridge),
[SillyTavern-ClaudeSubscription](https://github.com/LukaTheHero/SillyTavern-ClaudeSubscription).
The second states the motive plainly: "Claude Code CLI is how you access Claude's best models
on a subscription plan — but it's designed for coding, not long-form fiction."

## 5. The anti-slop lists, and where they came from

The provenance chain matters, because it contains a fact that cuts against the whole framing:

```
rentry.org/claudeisms  (≤2023-11, Claude 1&2 era)
    → AlpinDale/gptslop (2023-11-19)
    → KoboldCpp v1.76 banned_strings + antislop-sampler (Oct 2024)
    → Sukino's SillyTavern list (2025)
    → slop-forensics / EQ-Bench Slop Score (2025)
```

**The canonical slop vocabulary originated as a list of *Claude* tics.** The oldest artifact
is titled "Claudeisms", collected during the Claude 1 and 2 era, and
[`AlpinDale/gptslop`](https://github.com/AlpinDale/gptslop) carries `claudeslop.yaml` with 48
entries whose header comment credits that rentry — against a `gptslop.yaml` of just 5.

That has an uncomfortable implication for file 10's ban list: several phrases now used as
generic anti-slop filters entered the corpus as complaints about Claude specifically. The
phrases have since spread across all models, so the list is still correct as a filter — but
"these are the phrases that make text sound like a bad LLM" and "these are Claude's tics"
have a shared origin, and a paper should not present the first without knowing the second.

Sources, with sizes, for reconstruction:

| Artifact | Size | URL |
|---|---|---|
| Sukino's SillyTavern list | ~364 entries | [HF](https://huggingface.co/Sukino/SillyTavern-Settings-and-Presets/raw/main/Banned%20Tokens.txt) |
| antislop-sampler default | 517 phrase/multiplier pairs | [GitHub](https://github.com/sam-paech/antislop-sampler) |
| antislop full list | 50,084 entries | mirrored in `EQ-bench/creative-writing-bench/data/` |
| slop-forensics word list | 1,000 words | [GitHub](https://github.com/sam-paech/slop-forensics) |
| slop-forensics bigrams / trigrams | 200 / 200 | same |
| EQ-Bench Slop Score lists | 1,648 words / 200 bigrams / 430 trigrams | [methodology](https://eqbench.com/slop-score.html) |
| MerijnHendriks gist | 643 entries | [gist](https://gist.github.com/MerijnHendriks/494bf3af882597bbdfb7713035f032af) |

Two structural observations more useful than the lists themselves:

**The lists are morphology-aware by construction.** Sukino's guide instructs banning "from
the root" — ban `steeling h` to catch *herself*, *himself*, *hard*, *harder*. This is the
practical answer to the evasion problem file 10 flags: a literal ban on "mouth went dry"
invites "her mouth was dry".

**An 80-entry combinatorial "eyes" matrix** appears in the community list: each of ten
pronoun forms crossed with eight stems (`alight, full, gleam, glint, glow, shin, sparkl,
twinkl`). The tic is a *template*, not a phrase — which is exactly the finding file 10
records for dialogue tags.

**A prompt-level alternative exists.** [NemoEngine](https://github.com/NemoVonNirgend/NemoEngine)'s
anti-slop module is a *taxonomy* rather than a wordlist — named categories (tension-deflecting
quips, sarcastic narration, lampshading, blood-as-substance, eyes-as-emotion-readout,
silence-as-communication, authorial intrusion, poeticised blood, hyperbolic adverbs, dead
idioms) each with examples. For our purposes a taxonomy generalises where a wordlist does
not, and it is the better model for a judge rubric.

## 6. The rival paradigm, which should be contrasted

Not everyone imitates Claude. [`nbeerbower/Gemma4-Gutenberg-31B`](https://huggingface.co/nbeerbower/Gemma4-Gutenberg-31B)
(2026-06) targets **human public-domain literary fiction** instead, aiming for "story and
interiority over static description, controlled pacing over relentless adjective-stacking,
and an active dispreference for 'AI slop' phrasing."

Distilling from a strong model and distilling from human literature are different bets. A
paper that only documents the first is describing half the field.

## 7. Negatives worth recording

Documented so that later work does not re-search them:

- **Major RP finetuners who never mention Claude**: TheDrummer (Cydonia, Rocinante, Anubis),
  sophosympatheia (Midnight-Miqu, New-Dawn), zerofata, allura-org. The
  Claude-as-target framing is narrower than folklore suggests.
- **`anthracite-org/c2_logs_*` cards are undocumented** — they say only "cleaned up proxy
  queue errors." The community reading that `c2` means Claude proxy logs is **not evidenced
  on the cards**. Do not cite them as self-declared Claude data.
- **Gated or unavailable**: `nothingiisreal/c2-logs-cleaned` (401),
  `Sao10K/Claude-3-Opus-Instruct-15K` (401), `XeyonAI/MN-Helcyon-Claude-Opus-12b` (401).
- **Do not conflate**: "Weep" is by the same author as PixiJB but is a DeepSeek-R1 preset.
- **Could not verify**: "Avani", "Chatstream", "Q1F" as named Claude presets. `rentry.org`
  slugs `/gptslop`, `/antislop`, `/claudeslop`, `/sloplist`, `/unslop` all 404.
- **Recommend omitting**: SEO comparison sites and affiliate "Best LLM for writing" blogs,
  which recur in search and are internally inconsistent.

## 8. What this adds to file 09

File 09's conclusion was that Claude's measured advantage is *lexical and structural
discipline, not literary imagination*. Nothing here contradicts that, and two things sharpen
it:

**The ecosystem agrees the style is distinctive** — enough to spend compute imitating it, and
enough that a competing finetune advertises *avoiding* it. Distinctiveness is not the same as
quality, and the ecosystem treats them as separate axes even when praising it.

**The slop lists began as Claude complaints.** Any claim that Claude "avoids slop" needs to
name a version and a date, because the vocabulary now used to define slop was assembled by
people annoyed at Claude 1 and 2.
