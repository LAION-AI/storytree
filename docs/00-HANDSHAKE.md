# Handshake — read this first

You are picking up a project you have no memory of. This file is the fastest
path back to working state. Rewritten 22 August 2026, after the event-layer
campaign (builds 3–7).

---

## What this is

**storytree** generates screenplays as an explicit graph — story root, exposé,
plots, entity profiles, events, scenes, prose — and runs the same machinery
*backwards* to recover that graph from a finished screenplay (the 1998 Matrix
shooting script, 224 scenes). The reverse direction produces training data for
distilling narrative understanding into smaller models.

Repo: `christophschuhmann/storytree`. Working dir `/home/deployer/laion/bookwriter`.
`GH_TOKEN` is in `.env` (chmod 600, gitignored). **Never print tokens.** Push
ONLY via `tools/publish.sh <message-file>` — it gates the push on two leak
sweeps; twice a leak shipped because the sweep ran beside the push instead of in
front of it.

## The one-paragraph state

The scene layer is done and published clean (224 nodes, zero copied source
runs). The event layer is at **build 7**, which beat build 4 in the largest
blind evaluation run so far: **23 paired events, 4 independent judges, +0.69,
95% CI [+0.49, +0.88], preferred 20:3.** No dimension got worse. The bar
(mean ≥ 4.0, no dimension < 3.0) is still not met: build 7 means 3.32 with its
weakest dimension (internal consistency) at 2.09. The gains came from moving
decisions out of prompts into code; the remaining deficits have named causes
(§ next steps). Upper layers (plots, entities, exposé) are documented but
deliberately unbuilt — they depend on the event chain.

## Serving — what actually runs here

Everything local runs under **llama.cpp** (`llama-server`), NOT vLLM. (vLLM
served the Qwen 27B in the sibling project `project-alexandria`; do not confuse
the two.) Binary: `/home/deployer/models/llama.cpp.build/build/bin/llama-server`
(built from source, CUDA 12.8, arch 80).

**Ornith-1.5-397B** (sparse MoE, Q4_K_M GGUF) — the composer/judge workhorse.
Two instances, 4 GPUs each:

```bash
llama-server -m /home/deployer/models/Ornith-1.5-397B/Ornith-1.5-397B-Q4_K_M.gguf \
  --host 127.0.0.1 --port 8110 --device CUDA0,CUDA1,CUDA2,CUDA3 -sm layer -ngl 999 \
  -c 65536 -np 1 -fa on -b 2048 -ub 512 --jinja --alias ornith-1.5-397b
# second instance: port 8111, CUDA4-7
```

Facts you will otherwise rediscover the hard way:
* `-c 65536` is required. At 32,768 the largest event (33,680 tokens needed)
  truncated **by arithmetic, every run**. 64k costs only ~350 MB/GPU on this MoE
  and was verified with a needle at position ~40k (answered correctly).
* `-np 1` is correct: throughput is flat within one instance (41→44 tok/s) and
  doubles across instances. Parallelise across ports, not slots.
* ~44 tok/s generation; a full-film compose pass (wave=1, sequential for the
  state chain) runs ~4–5 min/event.
* The server's `/tokenize` endpoint gives exact counts — `fit_to_context()`
  uses it; estimates are off by more than the margin that matters.

**Qwen3.8-9B-Distill** (Q8_0 GGUF, `empero-ai/Qwen3.8-9B-Distill-GGUF`) — the
paraphrase workhorse, one spare-capacity GPU:

```bash
llama-server -m /home/deployer/models/Qwen3.8-9B-Distill/Qwen3.8-9B-Q8_0.gguf \
  --host 127.0.0.1 --port 8120 --device CUDA3 -ngl 999 -c 32768 -np 4 -fa on \
  --jinja --alias qwen38-9b
```

The 9B **cannot** rewrite a whole field (measured: 1/10 accepted vs 64/74 for
the 397B). Asked to rewrite **one marked span**, with code doing the splicing,
it clears ~71% at 1.8 s/field; the rest escalates to Ornith
(`--escalate-ports 8110,8111`), residue is elided. Final acceptance 95.8%.

Client: `EndpointPool` in
`/home/deployer/laion/project-alexandria/screenplay/src/screenplay_ku/client.py`
(prefix caching, JSON-schema guided decoding, round-robin over ports).

## Where the code is

| | |
|---|---|
| `distill/event_layer.py` | the whole event pipeline: segment → scaffold → compose → repair → chain → **audit → regenerate** → reconcile → verify → verbatim gate. CLI: `--segmentation` (reuse boundaries), `--limit N`, `--resume-from partial.json` (compose is the expensive stage; never redo it for a post-processing crash), `--ctx`, `--wave 1` (exact state chain) |
| `distill/event_scaffold.py` | procedural scaffold: film-wide roster (396 spellings → 364 entities), per-entity register demands, object restriction (physical/positional/status only), positional-MUST-MOVE from scene locations, `_terminal_for` (**six guards**, each from a real misfire — reuse it, never write a fresh keyword test; that mistake was made three times) |
| `distill/verbatim.py` | copied-source detection: exact gate (8+ tokens) + near gate (window overlap, order-insensitive) + dialogue/action role hints |
| `distill/paraphrase_pass.py` | span-level de-copying with the 9B + escalation; identifier-safe (entity names shortened consistently node-wide, never paraphrased); preserves numbers incl. spelled-out, names, unmoved-invariant, reading length |
| `distill/build_event_eval_pack.py` | blind A/B packs: pairing **by scene anchor** (ids shift between segmentations), labels shuffled per pairing, key to a separate dir |
| `distill/aggregate_event_eval.py` | paired bootstrap **over pairings** (the sampled unit), per-dimension table, gate check |
| `tools/check_no_leak.py` | sweeps everything `git ls-files` reports + `--message` for commit texts |
| `tools/redact_source_spans.py` | elision (JSON-structure-aware) |
| `tools/publish.sh` | the ONLY sanctioned push path |
| `distill/scene_variants.py` | scene layer (done; evidence capped at 7 words) |

Artifacts: `runs/scenes_ornith_v5` (scene layer, scored), `runs/scenes_ornith_v5_clean`
(published, 0 copied runs), `runs/events_build{3..7}` (6-event iterations),
`runs/events_build7_24` (23 events, sc-001..sc-114, the current best).
Screenplay text: `distill/runs/matrix/script.normalized.txt` +
`reconstruct/runs/matrix/script_map.json` (never committed; `.gitignore` matches
by filename anywhere).

## The event-layer campaign — what was done and learned

Full docs: `docs/events/build3-vs-build4.md`, `build5.md`, `build6.md`;
node format for outsiders: `docs/nodes/`; scoring: `docs/rubric-explained.md`.

| Build | Change | Blind result (6 anchors unless noted) |
|---|---|---|
| 3→4 | 64k context + anti-copy prompting | **null** (−0.17, CI [−0.45,+0.09]). Prompting did not reduce copying (0.88→1.10 runs/node) |
| 4→5 | chain closed per event; entry procedural; 5 judge findings → code | trend (+0.31, CI touches 0) |
| 5→6 | objects restricted; positional/terminal MUST-MOVE; dedup registers; carry map expires | **significant** (+0.33, CI [+0.06,+0.61]) — first ever |
| 6→7 | **audit→regenerate loop**: fabricated quotes, empty reasons, life/control contradictions, outside names → one entity redone with the fault named; V5 guard | +0.24 (n.s. at 6) |
| 4→7 | cumulative, **23 anchors, 4 judges** | **+0.69, CI [+0.49,+0.88], 20:3** |

The regeneration loop at scale: **108/108 entities accepted, 0 rejected.**
Acceptance requires: named fault gone, register set unchanged, reading not
shortened (the V5 guard — build 6 traded mind material for compliance and a
judge measured it; build 7 recovered V5 +0.83).

**The lessons, in order of how often they were re-learned:**

1. **Instructions repair local fields; structure repairs global properties.**
   Confirmed again: anti-copy prompting did nothing; schema+code changes moved
   every number that moved.
2. **Checkers measure themselves.** SEVEN instances this campaign: lint counted
   build-2's register contract (1505 phantom "missing"), entity-absent flagged
   objects for not being people (1013→19), truncation counted noun phrases as
   damage (23%→2.5%), placeholder list missed every new phrasing the model
   invented (0 reported, 23 real; **match by shape, not by list**), two
   unmoved-predicates wrong, outside-name counted spellings (9→4). When a number
   is surprising, audit the checker before the pipeline.
3. **Repairs must not manufacture faults.** repair_node wrote a template reason;
   audit_node flagged the template; regeneration undid it — 74 self-made faults
   in one run. Clear the field and let regeneration write from the scenes.
4. **A model asked to fix a fault sometimes returns it.** Regeneration accepts
   only verified improvements; everything else keeps the original.
5. **JSON Schema cannot vary `required` per sibling** — the union forces
   registers onto entities that cannot have them; the model answers "n/a"
   honestly. Remove the impossible ones after parsing (only the impossible:
   trimming to what the scaffold *typed* deleted 312/404 registers).
6. **The 6-anchor treadmill.** ±0.28-wide CIs cannot resolve +0.3 effects.
   Iterate small, but *decide* at 23+.
7. Guards on text heuristics are earned, not designed: `_terminal_for` needed
   six (attributive, reporting verb, other subject, active participle, negation,
   object-after-terminal-word), each found by auditing all 517 entities, not by
   reasoning.

## Next steps to raise event scores (ranked)

The two weak dimensions are **A internal consistency (2.09)** and **D schema
compliance (2.57)**. All four judges independently named the same causes:

1. **Stale carried entries — the top A-killer.** The carry map now expires after
   one event, but the *scaffold* still shows "entry from previous event" text
   that the model copies into scenes it contradicts ("entering the hotel...
   then leaving the mess hall"). Fix: label carried text with its source event
   and instruct update-don't-inherit; better, have `apply_chained_entries`
   overwrite AFTER compose only when the entity appeared in the direct
   predecessor, and give the model no carried text at all for gaps.
2. **Template `unchanged_because` from the old-code compose runs** is still in
   `events_build7_24` nodes where regeneration missed them (audit pattern
   `_EMPTY_REASON` catches "nothing across sc-X"; extend it to "neither added
   nor removed in the ledger" and any sentence naming a scene id). One node had
   101 `"No recorded change on this register."` `change` fields — normalise
   those to `unchanged` in repair_node (shape-match, like `_PLACEHOLDER`).
3. **Act on verify_all.** It found 37 state breaks + 20 contradictions across
   22 joins and NOTHING consumes its findings. Feed them into the audit→
   regenerate loop as faults on the named entity (they carry event ids).
4. **`outside_name` faults have no entity** so regeneration never touches them
   (17 left). Route them to a node-level rewrite of the affects_outside block.
5. **Duplicate entity declarations** ("BIG COP"/"The Big Cop" with conflicting
   states) — the roster folds these but the model re-splits them; add the fold
   map to merge_duplicate_keys as authoritative.
6. **After that, the model.** The only replicated gain in the whole project is
   the model swap (+0.38, p=0.002, scene layer). Procedural rounds yield ~+0.3
   each and the mechanically decidable faults are mostly harvested. To reach
   4.0 (gap: 0.68), expect to need a stronger composer, not a seventh round of
   rules. Composing via HYPRLAB API (Grok/Opus) is untested for the event layer.

Also owed: the remaining 24 events (build7_24 covers sc-001..sc-114; the film
has 47 segmented events), and one event of the 24 failed compose — check
`b7_24.log` before reusing.

## Judge protocol (blind A/B) — do not re-derive

`build_event_eval_pack.py` → per-judge dirs with `pairings.json`, `rubric.txt`
(`docs/cognitino`-era 14-dim rubric, POSTURE: 3="acceptable"), `scenes.json`.
KEY goes to a separate dir — an early run left it beside the batches and 2 of 3
judges read it. Brief judges on: the register contract (NOT all seven; objects
= physical/positional/status), noun phrases ≠ truncation, `[...]` elisions
neutral, `off_screen_reactor` legitimately names absent parties, `_`-prefixed
fields are annotations. Every briefing error becomes a systematic scoring bias —
V3 was invalid for one whole round because the briefing described build 2's
contract. Judges must never quote >7 consecutive screenplay words.

## Standing rules

* No published artifact carries ≥8 consecutive source words. The scene layer's
  `evidence` fields are verbatim BY DESIGN but capped at 7 words.
* Push only via `tools/publish.sh`. Commit messages are swept too (one shipped
  a 9-word quote while explaining how quotes get shortened).
* The 140-file copied-text history predates the cleanup and is still in git
  history; removing it means a public force-push — **user's call, not yours**.
* GPU7 hosts a live voices demo (other project) — keep it free.
* The frozen scene SAMPLE and the fix_v* artifacts must not change; blind
  scores were computed on them.
