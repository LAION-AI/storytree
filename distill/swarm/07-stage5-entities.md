# 7. Stage 5 — entity unification

Stage 1 let the naming diverge on purpose. One agent wrote `ALICE M.`, another
`Alice Miller`, a third `the woman from the ferry`, and nothing stopped them,
because forcing agreement before anyone had read the work is precisely the
imposition this design removes. Stage 5 is the bill for that decision, and it is
paid procedurally.

It runs **concurrently with stage 4**. Plots and entities do not depend on each
other: plot induction reads event drafts and argues membership against the script;
entity unification reads the same drafts and the scene layer and argues about
identity. Neither needs the other's output. They rejoin at the barrier before stage
6, which is the first stage that needs both — a profile has to know which plots its
entity serves.

---

## 7.1 Four agents, by domain

| Agent | Domain | Entity types |
|---|---|---|
| 1 | **agents** — anything that decides | `character`, `creature` |
| 2 | **locations** — anywhere something happens | `location` |
| 3 | **objects** — things that are handled, owned, moved, destroyed | `object` |
| 4 | **everything else** — groups, rules, social and magical concepts | `group`, `concept` |

Each receives the scene layer, all event drafts, and the full script, and returns
the entities in its domain only.

The split is by domain rather than by alphabet or by count for a specific reason:
**the merge decision is domain-shaped.** Deciding whether `ALICE M.` and
`Alice Miller` are one person is a question about people — do they appear in the
same scene, does one have a property the other contradicts, does the script's
dialogue ever address them differently. Deciding whether `the east dock` and
`Dock 4` are one place is a question about geography and about how the script writes
its slug lines. An agent that holds both is doing two different jobs with one
budget, which is the §1 failure of `05-model-behaviour.md` in its usual dress.

"Anything that decides" is the boundary for agent 1 rather than "human", and it is
load-bearing. A dog that chooses, a ship's AI, a possessed sword that refuses to be
drawn — these get profiles, state variables and relationships, because later layers
express what happens to them as state change and a thing that decides has states
worth tracking. The schema has both `character` and `creature` for this and the
distinction between them is cosmetic; the distinction that matters is agency.

### The fourth agent is the one that gets skipped

Groups, rules and concepts are the domain most easily left empty, and leaving it
empty is a measured failure. In the comparison in `docs/07-quality-evaluation.md`
§15.3:

| | Qwen | GLM | brief asked for |
|---|---|---|---|
| Entities | **9** | 17 | 30–40 |
| Locations | **1** | 6 | — |
| Concepts | **0** | 3 | — |

GLM declared `cn-01 The Fault Language`, `cn-02 Carriage Methodology`,
`cn-03 Authority Institutional Language`. Those are the things that story tracks
state *on* — the fault language is discovered, decoded and weaponised across two
acts. In the run with zero concepts it was not an entity, **so its progression could
not be recorded as state at all**, and one character's `epistemic_fault_nature`
variable had to carry the entire investigation.

A concept is an entity when it has a state that changes and something in the story
turns on that change. A rule that is believed and then disbelieved, a language that
is unreadable and then read, an institution's authority that holds and then does
not. If nothing about it moves, it is background and belongs in the story root's
`rules_of_the_world`, not in the entity table.

Giving that domain its own agent does not guarantee it gets populated. It guarantees
that if it is empty, the emptiness is one agent's explicit output rather than a
silent omission inside a larger job — which at least makes it visible to the
boundary check.

---

## 7.2 What each agent returns

Not profiles. Stage 6 writes profiles. Stage 5 returns identity:

```
entity_id        lo-03
canonical_id     THE_EAST_DOCK
canonical_name   The East Dock
type             location
aliases          ["east dock", "Dock 4", "the dock", "DOCK - NIGHT"]
first_seen       sc-014
occurrences      [sc-014, sc-015, sc-031, ...]
salience         major | supporting | minor | mentioned
evidence         why these aliases are one thing
```

The `aliases` array is the actual product of the stage. It must contain **every
surface form any earlier agent used**, including the ones that were wrong, including
the ones that were sloppy, including bare descriptions like `the woman from the
ferry`. It is not a list of the character's nicknames in the fiction; it is the
key set for a find-and-replace across the whole tree. An alias missing from it is a
reference that will not be rewritten, and an unrewritten reference is a dangling id
at the next boundary check.

`evidence` is required for the same reason it is required in stage 3: a merge is an
inference, and an inference without its support cannot be reviewed or reversed. Two
names merged wrongly is the expensive error here — see §7.5 — and the evidence field
is what a human or a later check reads when the count looks off.

---

## 7.3 The naming standard

**A capitalised identity word, underscore-joined: `ALICE_MILLER`, `THE_EAST_DOCK`,
`THE_FAULT_LANGUAGE`, `HOUSE_VEREN`.**

The requirement this satisfies is unusual and worth stating precisely: the standard
exists so that **independent agents converge on the same string without
coordinating.** Four agents in stage 5 do not talk to each other. Nor did the 224
agents of stage 1, nor the thirty of stage 3. If the naming rule is expensive to
apply — a registry, a numbering scheme, a lookup — then agreement requires
communication, and communication across a swarm of this width is either a
bottleneck or a shared mutable state, and both are worse than the problem.

What makes a rule cheap to converge on:

- **Deterministic from the text.** The identity word is what the script calls the
  thing most often, upcased. No agent has to know what any other agent chose.
- **No sequence numbers in the canonical id.** `ch-01` is fine as a storage key
  assigned in code after the fact; it is useless as something four agents must agree
  on, because ordering is arbitrary and each agent would number from its own domain.
- **Case- and punctuation-normalising.** `ALICE M.`, `Alice Miller` and `alice
  miller` all collapse toward the same shape, which means near-misses are visible as
  near-misses rather than as unrelated strings.
- **Human-readable in a diff.** Every downstream artifact references these ids;
  a reviewer scanning a scene node should be able to see who is in it without a
  lookup table.

The `THE_` prefix on places and concepts is a small ugliness kept on purpose: it
matches how scripts name them, so it is what an agent reaches for first.

**This is a heuristic and it does not guarantee convergence.** Two agents can
legitimately disagree about which word is the identity word — `THE_EAST_DOCK` versus
`DOCK_FOUR` — and nothing in the rule breaks the tie. The rule reduces the size of
the merge problem; it does not eliminate it. It is chosen because it is the cheapest
thing that reduces it, not because it is sufficient.

---

## 7.4 The procedural rewrite

Once the four dictionaries are merged into one alias map, the rewrite is **code, not
a model call.**

```
1  build the alias map                 alias (normalised) → canonical_id
2  detect collisions                   one alias claimed by two canonical ids
3  assign storage ids                  ch-NN, lo-NN, ob-NN, gr-NN, cn-NN
4  rewrite every reference             scene nodes, event drafts, plot agent/resistance
5  report unresolved                   any name in the tree not in the map
```

Step 5 is the important one and it is the direct analogue of a fix already made
elsewhere in this codebase. `characters_in_scene()` originally matched canonical
names only, found one speaker in a two-speaker scene, and produced a run that
analysed fewer characters than the baseline it was meant to beat. The fix was to
**return unresolved cues separately rather than dropping them** — an unresolvable
speaker is a hole in the entity layer and should be visible. Same rule here: a name
appearing in the tree that no dictionary claims is not quietly left alone. It is
reported, and it is a stage-boundary failure if it names anything with a state
change attached to it.

Nothing about steps 1–5 requires judgement, which is why none of it is a model call.
The rule from §11 applies: **what is decidable from data must never reach a model.**
A model asked to apply 400 substitutions will apply most of them.

---

## 7.5 Being honest: this is a merge problem

Identifier unification is the classic record-linkage problem and it has the classic
two-sided failure, neither side of which the pipeline currently measures.

**Over-merging** — two distinct entities collapsed into one. Two guards, two docks,
two members of the same house with the same surname. This is the expensive error,
because it is nearly invisible downstream: the merged entity has a coherent profile,
a plausible state vector and a full occurrence list, and it silently makes both
originals' arcs incoherent. It looks like exactly the same artifact as a correct
merge.

**Under-merging** — one entity split across two ids. Cheaper, because it shows up:
two profiles with overlapping backstories, two entities whose occurrence sets never
intersect but whose descriptions do, and an entity count above what the script
supports. A reviewer notices. A mechanical check can notice too.

The available defences are all partial:

- an alias claimed by two canonical ids is a hard collision and fails the boundary
  check — this catches some over-merges and no under-merges
- two canonical ids whose occurrence sets are disjoint and whose canonical names
  share a normalised token are a warning — this catches some under-merges
- the `evidence` field makes any individual merge reviewable, at the cost of a human
  reading it

None of this has been run. **The stage has not been executed, no merge-error rate
has been measured, and the numbers in the throughput table for it — 4 calls, 24,000
tokens — are assumed.** The claim being made is narrow: unification after the fact
with an explicit alias map is a *better-conditioned* problem than agreement before
the fact, because it is repairable and inspectable, and because the alternative
imposes a naming decision on 224 agents before any of them has read anything. That
is an argument about which problem to have, not a claim that this one is solved.

---

## 7.6 What the count check is for, and what it cannot do

`docs/07-quality-evaluation.md` §17 recommends flooring the entity count against the
brief's target, because a run shipped 9 entities against a brief asking for 30–40
and nothing objected. In the bottom-up design there is no brief to floor against at
this point — the story root does not exist yet, by construction — so the floor has
to come from the tree itself:

- every location named in a scene node's setting must resolve to a location entity
- every speaker cue in the script must resolve to an agent entity
- every entity named in any event's `participants` must exist
- no single location may carry more than ~60% of events (the collapsed-ontology
  warning from §15.4, where all 22 events landed in the one declared location,
  including four that happen outside it)

The 60% threshold is a judgement, not a measurement. It is set where it is because
the observed failure was 100% and a legitimate bottle-episode is plausible at 60;
it should be tuned once there are enough runs to tune it on.

The structural argument for why this stage should not need the floor at all: the
lower layers were written first, so a location exists because a scene happened
there, not because a planner remembered to declare it. **Under-declaration cannot
starve layers that were already written.** Whether that holds in practice is exactly
what §13 has to measure, and until it does, the checks stay.
