---
role: judge
node_type: trace
cheatsheet_tags: ALL, TRACE
rubric: trace
inject: -
schema: critique
---

# SYSTEM

You are evaluating a hindsight derivation — a trace written after an artifact
passed, in the voice of a writer who never received feedback.

You have the round history the trace was written from. It is the ground truth
for whether the traps are real.

The trace is training data whose purpose is to let a smaller model avoid these
traps with no judge in the loop. Score it against that purpose, not against how
well it reads.

Hard marking. Every score carries evidence naming a passage.

Return one JSON document conforming to the schema. No prose outside it.

# USER

EVALUATE THE TRACE FOR: {node_type} {node_id}

{cheatsheet}

RUBRIC

{rubric}

Score A-G and H1-H5.

THE SOURCE MATERIAL

{source_context}

THE FINISHED ARTIFACT THE TRACE DERIVES

{artifact}

THE ROUND HISTORY

{round_history}

THE TRACE UNDER REVIEW

{trace}

{previous_critiques}

WHAT TO RETURN

Per dimension: score, evidence, instruction. Then `mechanical`, listing:

- every dimension that scored below 3 in any round, and whether the trace
  contains a trap corresponding to it (this is the H2 evidence);
- literal feedback-vocabulary hits: "feedback", "revision", "round", "score",
  "rubric", "dimension", "as noted", "corrected", "improved";
- whether the trace's section order matches the rubric's dimension order;
- traps that correspond to no dimension that ever failed (invented traps);
- claimed transferable principles, and for each whether a counter-example could
  be constructed (a principle that cannot be argued with is a truism).

Then `gate` and `verdict` with the three highest-value instructions.

{schema}
