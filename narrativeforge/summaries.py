"""The specification for the two plot summaries.

Defined once and imported everywhere it is needed — the exposé prompt, the
backfill tool, and (mirrored) the reconstruction fork — because the same text
maintained in three places is the same text until the day it isn't.

The failure this exists to prevent is subtle and very common. A model that has
just built a world writes its summary in that world's own vocabulary: "he
collects the ritual tokens", "the wipe is torn", "his rotation dies". Every one
of those is meaningful to someone who has read the story and noise to everyone
else. The summary reads as fluent and conveys almost nothing.

Naming a mechanic is not explaining it. The test is operational: what is it
physically, how does it work, what does it cost, and what happens if it fails.
"""

from __future__ import annotations

SUMMARY_SPEC = """\
THE TWO PLOT SUMMARIES

`plot_summary_short` — 150-250 words for a story set in the ordinary world.
Where the world runs on invented machinery that has to be explained before the
plot is legible, up to 300 words. That is the only thing that buys extra room:
EXPLANATION OUTRANKS THE CEILING, and nothing else does. Cut subplots, cut
minor characters, cut every adjective — but never ship an unexplained mechanic
to stay under a word count.
`plot_summary_long`  — 700-1200 words, in paragraphs broken by movement.

Both are ENCYCLOPEDIA PLOT SUMMARIES, not jacket copy. You are informing, not
seducing. Neutral third person, present tense, strictly chronological in story
time, the ending given away. No rhetorical questions, no "but everything changes
when…", no atmosphere, no imitation of the work's own voice.

WHO YOU ARE WRITING FOR

An intelligent adult who knows nothing about this story and is reading at
ordinary speed, not studying. They will not re-read a sentence to decode it and
they will not hold an unexplained term in their head hoping it resolves later.
Everything must land on the first pass.

1. OPEN WITH ORIENTATION, THEN NARRATE

   Before any plot event, establish in this order:
     · what KIND of work this is — form and genre, in plain words
     · WHEN and WHERE it is set
     · the CENTRAL SITUATION or conceit, stated so a stranger grasps it
     · WHO we follow, and what they are trying to get
     · the two or three RULES the plot actually turns on

   A reader who stops after the opening should be able to say what kind of story
   this is, where it happens, what the situation is, and who to follow.

2. EXPLAIN EVERY INVENTED MECHANIC OPERATIONALLY

   This is where these summaries usually fail. Any rule, ritual, institution,
   technology, currency, class of object or piece of world-machinery that the
   plot turns on must be explained the first time it matters — and explained by
   what it DOES, not by what it is called.

   For each one, the reader needs, in a clause or a sentence:
     · what it physically is
     · how it works, concretely
     · what it costs, or what it requires
     · what happens if it fails, or if someone breaks it

   NAMING IS NOT EXPLAINING. "He collects the ritual tokens" tells a stranger
   nothing: what is a token, how many are there, where do they come from, why
   does anyone want them? Write instead what they are and what having them
   means — "a fixed set of small objects hidden around the town; whoever gathers
   all of them and speaks the words at dawn wins and leaves".

   The same applies to every piece of in-world shorthand. If the story calls
   something a wipe, a rotation, a levy, a compact, an overwrite, a residue —
   do not use the word until you have said what it is. After that you may use it
   as shorthand, because by then it means something.

3. NO BARE PROPER NOUNS FOR MECHANICS

   A capitalised name with no function attached is decoration. Every invented
   proper noun gets its job stated at first appearance: not "the Daywalker
   Ritual", but "the Daywalker Ritual, a dawn ceremony that ends the game for
   whoever completes it".

4. GIVE QUANTITIES AND STAKES WHERE THEY DRIVE DECISIONS

   How many are there, how long is left, what is lost by failing, who else
   wants it. A reader cannot feel a constraint they cannot measure.

5. THE TEST

   Read your own summary as a stranger. At every sentence, could they ask
   "wait — what is that?" or "why does that matter?" If yes, that sentence is
   not finished. This applies to the short one as much as the long one: the
   short one has less room, so it explains fewer mechanics, not the same number
   more briefly. Drop a subplot before you drop an explanation.

   Explanations are woven in at the point of use, one clause each. Do not open
   with a paragraph of worldbuilding and do not append a glossary.

6. THE LONG VERSION ALSO MAKES THE SHAPE LEGIBLE

   Say plainly what the two or three separate threads are and how they cross, so
   a reader can follow which is which, and cover the fate of every significant
   character.
"""


def spec() -> str:
    return SUMMARY_SPEC
