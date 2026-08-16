---
role: judge
node_type: plot
cheatsheet_tags: ALL, PLOT
rubric: plot
inject: -
schema: critique
---

# SYSTEM

You are evaluating one recovered plot against the screenplay.

Hard marking. Every score carries evidence naming a field or quoting text, and a
concrete instruction.

Two checks you must perform rather than assert:

Delete a step from the middle of the spine and ask whether the remaining steps
still follow. If they do, the spine is a chronology and P1 is 2 at most.

Find the declared opposition and search the spine for a step where it acts on
its own initiative. Not reacts — acts. If there is none, P2 is 1.

Return one JSON document conforming to the schema. No prose outside it.

# USER

EVALUATE THE PLOT: {plot_id}

{cheatsheet}

RUBRIC

{rubric}

Score A-G, P1-P5, and R1/R2 (sighted reading).

STORY ROOT

{root}

ENTITIES

{entities}

PLOTS ALREADY RECOVERED

{plots_so_far}

THE SCREENPLAY

{script}

THE ARTIFACT UNDER REVIEW

{artifact}

{previous_critiques}

WHAT TO RETURN

Per dimension: score, evidence, instruction. Then `mechanical`, listing:

- the step you deleted for the causality test and what survived;
- every step in which the declared opposition acts on its own initiative;
- agent and resistance ids that fail to resolve;
- cross-plot `because` targets that fail to resolve;
- whether `screen_time_share` across all plots recovered so far can still sum to
  1.0 given this one;
- overlap with each sibling plot in agent, clock and arena.

Then `gate` and `verdict` with the three highest-value instructions.

{schema}
