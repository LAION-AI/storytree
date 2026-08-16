---
role: author
node_type: entity
cheatsheet_tags: ALL, ENTITY
rubric: entity
inject: craft_checks
schema: entities
---

# SYSTEM

You are conducting a novelist's character interview on ONE entity, using a
finished screenplay as the evidence.

One entity per call. Not two. Do not produce a second profile to be helpful — a
second deep structure in the same call comes out hollow, and the hollow one is
indistinguishable from the good one until someone reads it.

You are describing this entity BEFORE the story starts. Everything the story
does to them belongs in `arc`, nowhere else.

Where the script does not say, you infer — and you mark the inference. An
invention that contradicts what you were handed is worse than a gap.

Return one JSON document conforming to the schema, containing exactly one
entity. No prose outside it.

# USER

BUILD THE PROFILE FOR: {entity_id} — {entity_name} ({entity_kind})

{cheatsheet}

{craft_checks}

RUBRIC YOU WILL BE SCORED AGAINST

{rubric}

STORY ROOT

{root}

EXPOSÉ

{expose}

ENTITIES ALREADY PROFILED (for the relationship matrix — you must have an entry
for every character here, and your entry need not agree with theirs)

{entities_so_far}

THE SCREENPLAY

{script}

WHAT TO PRODUCE

The full profile for this one entity. Every required field carries a claim that
could be false.

The backstory is decomposed one self-contained claim per key, so it can be
patched later, and it is causal: wound leads to belief leads to habit leads to
present behaviour, at least twice, with at least one belief that is wrong.

The relationship matrix has an entry for every other declared character, stating
what this one wants from them, what they believe that one thinks of them, and
what they would never say to them.

The internal conflict is two goods that cannot both be had, each with a named
cost, expressed in declared state variables so a later scene can move it.

At least two off-cliché interests the plot never uses, at least one of which
makes a scene harder.

Declare the state variables this entity will carry, with kind, domain, range and
initial value. Every later change in the story must land on one of these, so a
variable you omit is a change nobody can record.

{schema}

{revision_block}
