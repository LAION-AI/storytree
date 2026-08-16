---
role: author
node_type: trace
cheatsheet_tags: ALL
rubric: trace
inject: -
schema: trace
---

# SYSTEM

You are writing the derivation of an artifact that is already finished and has
already passed review.

Write it as the person who produced it in one pass — someone who had done this
often enough to see the traps coming and never needed to be told. Go from the
source material to the finished artifact, showing the judgement at each step.

You are given the round history: the earlier drafts and what was wrong with
them. That history is your material for the traps, and it must never appear as
history. You are not describing a correction. You are describing a writer who
anticipated the mistake and did not make it.

Concretely:

Never write "the feedback", "on revision", "in the second round", "the score",
"the rubric", "the dimension", or "as noted above". Never repair. Anticipate.

Do not walk the rubric's dimensions in order. That is the shape of a document
written from the rubric, and it is visible.

Cover what NOT to do, using the actual problems the earlier rounds hit. Phrase
each as a temptation with its reason: the obvious move here is X, which fails
because Y. A trap list that does not correspond to what really went wrong is
decoration.

End with at least one principle that would transfer to a different story, is
non-obvious, and could be argued with.

This trace is training data. Its purpose is to let a smaller model avoid these
traps with no judge in the loop. A trace that reads beautifully and teaches
nothing has failed.

Return one JSON document conforming to the schema. No prose outside it.

# USER

WRITE THE DERIVATION FOR: {node_type} {node_id}

{cheatsheet}

RUBRIC YOU WILL BE SCORED AGAINST

{rubric}

THE SOURCE MATERIAL THE ARTIFACT WAS DERIVED FROM

{source_context}

THE FINISHED ARTIFACT

{artifact}

THE ROUND HISTORY — your material for the traps, never to be referenced as
history

{round_history}

WHAT TO PRODUCE

The derivation, in the voice described above. Show what you looked at, what you
concluded, and — at least once — the evidence that would have forced a different
conclusion.

Then the traps: one entry per dimension that fell below the gate in any round,
each phrased as a temptation with its reason, each recognisable as something a
writer would actually be tempted to do.

Then the transferable principles.

{schema}

{revision_block}
