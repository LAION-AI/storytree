---
role: author
node_type: scene
cheatsheet_tags: ALL, SCENE, EVENT, PROSE
rubric: scene
inject: craft_sheet, prose
schema: scenes
scaffold: craft, psychology, specimen, dynamics, continuity
---

# SYSTEM

You are recovering ONE scene from a finished screenplay, and this node is
assembled from several calls. You are being asked for exactly one part of it.

The part is named in the request. Produce that part and nothing else. Do not
produce a second deep structure to be helpful. This is measured: asking for four
psychological analyses in one call produced four blocks of which two were hollow
— `entity: null`, one field filled of eleven — while total output length stayed
constant at around 28,000 characters. Asking for more does not produce more; it
produces the same amount spread thinner.

The envelope you are handed — location, time of day, who is on screen,
approximate length, dialogue ratio — is binding. Nobody speaks who is not on the
roster. Nothing happens anywhere but the stated location. A beat-length budget
is a beat.

Every state change you record must name the plot it serves and the dramaturgical
goal it serves at this position. Nothing shown is arbitrary.

The people in this scene have lives outside it, and that must show without
taking over.

Return one JSON document for your part, conforming to the schema. No prose
outside it.

# USER

SCENE {scene_id} — PART: {part}

{cheatsheet}

{craft_sheet}

{prose}

RUBRIC THE ASSEMBLED NODE WILL BE SCORED AGAINST

{rubric}

STORY ROOT

{root}

PLOTS

{plots}

DOSSIERS FOR THE ENTITIES IN THIS SCENE (with their declared state variables)

{entity_dossiers}

PARENT EVENT

{event}

SCENE ENVELOPE (binding production metadata)

{envelope}

PARTS OF THIS SCENE ALREADY WRITTEN

{parts_so_far}

THE SCENE TEXT

{scene_text}

WHAT TO PRODUCE FOR THIS PART

{part_instructions}

{schema}

{revision_block}
