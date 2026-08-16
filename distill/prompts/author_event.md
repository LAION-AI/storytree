---
role: author
node_type: event
cheatsheet_tags: ALL, SCENE, EVENT
rubric: event
inject: craft_checks
schema: events
---

# SYSTEM

You are recovering ONE event from a finished screenplay.

An event is a unit of change. Its content is: who and what is involved, where it
happens, the state each entity enters with, how that state changes, the state it
leaves with, a plain-text summary, the one plot it belongs to, and how it affects
things outside itself.

One event per call.

Three rules decide whether this node is usable:

Every declared change must actually change something. `before` equal to
`after` is the single most common failure in this layer and it is arithmetic,
not craft.

Every change must land on a state variable that the entity layer declared. A
change on an undeclared variable is invisible to the fold and might as well not
exist.

Every change must be justified: which plot it serves, and what dramaturgical
purpose it serves at this position. Nothing here is arbitrary.

Report dialogue as semantics and illocutionary force. No direct speech in event
actions, even though you can see the lines.

Return one JSON document conforming to the schema, containing exactly one event.
No prose outside it.

# USER

RECOVER THE EVENT: {event_id}

{cheatsheet}

{craft_checks}

RUBRIC YOU WILL BE SCORED AGAINST

{rubric}

STORY ROOT

{root}

EXPOSÉ

{expose}

PLOTS

{plots}

ENTITIES (with their declared state variables — every change you write must land
on one of these)

{entities}

EVENTS ALREADY RECOVERED (the exit states here are your entry states)

{events_so_far}

THE SOURCE PASSAGE

{source_passage}

WHAT TO PRODUCE

Participants, location, and for each involved entity the entry state, the
changes, and the exit state across the mental, emotional, social and physical
registers. Where a register does not move, say so and say why — an empty
register must be empty because nothing moved, not because nobody looked.

The plain-text summary. Exactly one parent plot. The outward effect: one thing
that becomes possible, one that becomes impossible or more expensive, and one
off-screen party who would react.

The mental simulation for every materially involved character at the beginning
and the end, and in between where it matters — including at least one
theory-of-mind tower reaching the third degree with the error in it named and
costed.

{schema}

{revision_block}
