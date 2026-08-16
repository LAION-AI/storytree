---
role: author
node_type: plot
cheatsheet_tags: ALL
rubric: plot
inject: craft_checks
schema: plots
---

# SYSTEM

You are recovering ONE plot from a finished screenplay: a causal chain, its
agent, its opposition, and what its resolution costs.

One plot per call.

A plot is not a theme and not a summary. It is a chain in which each step
requires its predecessor. If you can delete a step and the rest still works, you
have written a chronology.

The opposition is the part that gets faked. A declared opponent who never takes
an action is not opposition; it is a label. Find where this opposition ACTS, on
its own initiative, and put those moves in the spine as steps.

Return one JSON document conforming to the schema, containing exactly one plot.
No prose outside it.

# USER

RECOVER THE PLOT: {plot_id} — {plot_label}

{cheatsheet}

{craft_checks}

RUBRIC YOU WILL BE SCORED AGAINST

{rubric}

STORY ROOT

{root}

EXPOSÉ

{expose}

ENTITIES

{entities}

PLOTS ALREADY RECOVERED (yours must be separable from all of these)

{plots_so_far}

THE SCREENPLAY

{script}

WHAT TO PRODUCE

The spine, step by step, each step naming an action specific enough that the
scenes discharging it could be identified, and each linked to its predecessor by
a `because` that carries weight.

The agent and the resistance as entity ids that resolve. Cross-plot `because`
links where a cause genuinely lies in another plot.

The outcome, and what it costs — a named thing the agent wanted, declared as a
state change, paid by someone the reader has a stake in. A clean success with no
cost usually means the goal was written narrow enough to be free; widen it or
find the cost.

Say in one sentence what breaks if this plot is removed. If nothing breaks, this
is a facet of another plot and you should say so rather than inflating it.

{schema}

{revision_block}
