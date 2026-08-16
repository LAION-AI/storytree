"""The craft cheat sheet — injected into every generative prompt.

Sources, so the provenance is auditable:

* James N. Frey, *How to Write a Damn Good Novel* (1987) — read in full from
  the copy in this repo. Everything attributed to Vol. 1 is from that text.
* James N. Frey, *How to Write a Damn Good Novel II: Advanced Techniques for
  Dramatic Storytelling* (1994) — read in full from the copy the user supplied.
  Chapters 1-3 and 4-5 (fictive dream, suspense, character, premise types) are
  the load-bearing ones for generation and are summarised below.
* Standard screen-trade craft — McKee, Truby, Snyder, Yorke, Mamet's memo to
  the writers of *The Unit*, Swain's scene/sequel — where it converges with
  Frey and adds something operational he does not cover.

Everything here is written as an instruction to a generating model, not as a
lecture. If a line does not change what the model would otherwise emit, it does
not belong.
"""

from __future__ import annotations

# --------------------------------------------------------------------------
# The full sheet. ~9k tokens. Injected whole into story-level prompts.
# --------------------------------------------------------------------------

CRAFT_SHEET = """\
═══════════════════════════════════════════════════════════════════════════
CRAFT SHEET — dramatic storytelling
Frey, *How to Write a Damn Good Novel* I & II, plus standard screen craft.
Binding on every layer. Where this sheet and your instinct disagree, follow
the sheet.
═══════════════════════════════════════════════════════════════════════════

─── 1. CHARACTER IS THE FOUNDATION ───────────────────────────────────────

**Homo fictus is not homo sapiens.** Fictional people are *more* than real
ones — hotter passions, colder anger, sharper contradictions. Even a dull
character must be extraordinary in his dullness. Real people are fickle and
unfathomable; a fictional person may be complex, volatile, even mysterious,
but must always be ultimately fathomable. The moment a reader cannot fathom
him, the book closes.

**Three dimensions (Egri, via Frey).** Every major character is built on all
three, and the third is *produced by* the first two:
  · physiological — height, weight, age, sex, health, deformity, beauty
  · sociological — class, family, schooling, money, friends, the world that
    raised him
  · psychological — phobias, complexes, guilt, longing, fantasy, ambition
Trace every trait to its root. If you cannot say what *made* a character
this way, you do not know him and his motivation will read as arbitrary.

**The ruling passion.** Each major character has one central motivating force
that is the sum of all his drives — "to be the Leonardo da Vinci of private
eyes," "to kill Moby Dick," "no debt passed to a child." It rules his every
waking moment. He acts out of a *complexity* of motives that add up to it.
A negative ruling passion works fine: Scrooge's passionate miserliness makes
him a worthy protagonist.

**The steadfast protagonist.** He must be determined, well-motivated, willful.
Discouragement does not stop him. Bribes and threats do not sway him. Beaten
and shot, he does not quit. He solves the problem or dies trying.

**Maximum capacity, and the "would he really?" test.** Homo fictus always
operates at the maximum *within his own capability* — never above it, never
below. A character who fails to use every resource available to him is the
author cheating. Two questions before every decision a character makes:
  1. "Would he really?" — check it against the biography.
  2. "What else could he do that is more ingenious, dramatic, surprising, or
     funny?"
A low-capacity character is fine — the executive crash-landed in the desert
who has never suffered worse than a warm martini is gripping precisely
*because* he flails at his own maximum. But never the "idiot in the attic":
no sane person goes up those stairs. If your plot needs someone to behave
stupidly, your plot is wrong.

**Avoid the stereotype by contradiction, not by novelty.** The whore with the
heart of gold, the tough-but-tender private eye — these are dead on arrival.
Break them by combining traits a reader would not expect in one person: the
nun who loves comic books, tenderness in a stormtrooper, a mean streak in a
delicate artist. But contradictions must serve the story and affect behaviour,
and must survive the believability test.

**Do the biography before you write.** For each major character, the life from
birth to page one. It is for you, not the reader; it may meander, allude,
leave things unexplained. But you should know him as well as you know your
brother before he speaks a word.

─── 2. CONFLICT IS THE ENGINE ────────────────────────────────────────────

Frey's three greatest rules of dramatic writing: **conflict, conflict,
conflict.** Character is revealed only under resistance. Narrative description
can make a reader *see* a character; only a decision under pressure makes him
*live*.

**M + G + O = C.** Main character + Goal + Opposition = Conflict. All three
required. Conflict is always **insistence versus resistance**.

**Equalise the forces.** Popeye against Wimpy is not a story; Popeye against
Bluto is. The antagonist must counter every attempt with as much force and
cunning as the protagonist brings. And the opposition must have a point of
view that is *logical, reasonable, and sympathisable* — the boss who blocks
the woman's promotion because he is a cackling sexist is melodrama; the boss
who blocks it because he has lost three women to competitors before, or
because he is secretly in love with her and knows he shouldn't be, is drama.
**Never give the antagonist a villain's motive when a human one will do.**

**The crucible (bonding).** Your characters must be unable to walk away.
If the reader can ask "why doesn't she just leave?", you have no story. The
crucible may be love, duty, marriage, a prison cell, a lifeboat, an army, a
hook in a fish's mouth, poverty, a child's dependency. Name the crucible
explicitly for every sustained conflict. It is not optional.

**Inner conflict is mandatory.** A character with no inner conflict produces
only pity, never engagement — and the work is melodrama. Inner conflict is
one will divided against itself: duty against desire, love against
self-preservation, conscience against family. The character is **impaled**
when two equally powerful forces pull in opposite directions and he cannot
move without loss. Hamlet must avenge his father, is morally opposed to
killing, and is not certain of the guilt. That is the shape.
  · The stakes need not be large in the world — only large in that character's
    mind. One man agonises over a stolen dime while another steals a million
    and sleeps fine. The dime is the better story.
  · Godzilla eating Tokyo generates no inner conflict — there is no moral
    choice in killing Godzilla. If your antagonist admits no moral complexity,
    you have an action yarn, not a drama.

**Three patterns of conflict — two of them are failures:**
  · **STATIC** — bickering, nagging, "yes you will / no I won't." Characters
    stop developing. The shy stay shy, the brave stay brave. Nothing bores a
    reader faster except no conflict at all. *This is the failure mode to
    watch for: two people talking without the situation changing.*
  · **JUMPING** — leaping between intensity levels without motivation or
    transition. Tender, then raging, then forgiving. The reader gets dizzy.
    The mark of cheap melodrama.
  · **SLOWLY RISING** — the only correct one. Think of it as attacks and
    counterattacks between strategists conducting a war. Probe, low attack,
    defence, increased attack, broadside, massive counterattack, retreat, new
    tactic, surrender. Frey's model is Scrooge and Marley's ghost: each
    exchange escalates by one measurable step, and Scrooge *changes* between
    steps — he begins looking the ghost in the eye and ends on his knees
    crying "Mercy!"
  **Conflict can rise only if the character changes.** If your character is
  cool when he loses his job, cool when the car is repossessed and cool when
  the dog dies, there is no rise. Escalation *is* character change.

─── 3. PREMISE — WHAT THE STORY PROVES ───────────────────────────────────

A premise is a **statement of what happens to the characters as a result of
the core conflict**. It has three parts (the three C's): a **character**
element, which through **conflict** leads to a **conclusion**.

  · *The Godfather* — "family loyalty leads to a life of crime."
  · *Cuckoo's Nest* — "even the most ruthless psychiatric establishment
    cannot crush the human spirit."
  · *Lolita* — "great love leads to death."
  · *Madame Bovary* — "illicit love leads to death."

It need not be universally true — only true **for these characters in this
story**. "Premarital sex leads to disaster" is not a fact about the world; it
is a fact about Sam and Mary.

**One premise. Exactly one.** You cannot ride two bicycles at once.

**Premise governs selectivity.** Anything that does not help prove the
premise must be cut, however good it is. Aristotle: any part whose presence
or absence makes no perceptible difference is no part of the whole. The
death-bed scene with the dying mother may be the best writing in the book — if
it does not prove the premise, it goes.

**Identify the core conflict.** In every dramatic story there is one, and it
is what the story is "about": the old man against the fish, Leamas against
his interrogators, Scrooge against the spirits, the Corleones against the
other families. Peripheral conflicts may be many; the core is one.

─── 4. STORY SHAPE ───────────────────────────────────────────────────────

**Begin before the beginning.** Establish the status quo *first*, then break
it. The reader cannot understand the impact of the firing without knowing
what the job meant. Open at the moment of the disturbance and the reader must
withhold sympathy while he works out who this is — which is the one thing you
cannot afford at page one. Hemingway shows the old man fishless for
eighty-four days *before* he rows out. Dickens shows Scrooge refusing his
nephew, the charity men and his clerk *before* Marley arrives.

**Events must be causal, not sequential.** B cannot happen unless A happened;
C cannot happen unless A and B happened. A story that is "and then, and then,
and then" is not a story. This causal weave is what critics mean by "tight."

**Growth from pole to pole.** The protagonist should travel from one end of
some axis to the other: coward → brave, lover → enemy, saint → sinner,
terrified pessimist → confident man. Chart it. Every complication should move
him measurably along that axis, and his *response to conflict must change* as
he moves.

**Story questions.** Every opening poses a question the reader needs answered.
They are the appetite. Keep at least one live at all times.

**The climax is a revolution (peripety).** A change to the *opposite* state —
things turned upside down. The coward finds courage; the winners lose; the
sinner is redeemed; the man who has been shown his death wakes alive on
Christmas morning. The climax settles the core conflict and *proves the
premise*. If your ending does not reverse something, it is a stopping point,
not a climax.

─── 5. SCENE CONSTRUCTION ────────────────────────────────────────────────

**Every scene is a small story: rising conflict → climax → resolution →
bridge.** A scene's core conflict need not be the story's core conflict, but
it must have one.

**Enter late, leave early.** Where a scene's opening conflict is too weak to
grip, plunge into the middle of it. Frey's example compresses a whole
confrontation to: *the next morning, standing in front of the boss, Joe felt
his knees shaking while he stammered "I get a raise, or I quit!" / The boss
grinned. "We're going to miss you around here, Cosgrove."* — bridge, scene,
climax, resolution, in four lines. Sometimes skip the scene's climax
entirely. Sometimes omit the scene.

**Three dramatic modes**, and choose deliberately:
  · **dramatic narrative** — summary, compressed time, "the winter was spent
    in waiting"
  · **half-scene** — partly summarised, partly played
  · **full scene** — moment by moment, in real time
Play the scenes where the conflict is hottest. Summarise the rest. A novel or
script that plays everything at full length has no rhythm.

**Every scene must change something.** A scene that ends with the situation
where it started is a deleted scene that has not been deleted yet.

─── 6. DIRECTION AND EXPOSITION — DRAMATISE, DO NOT EXPLAIN ──────────────

This is the standard that separates competent from good, and it is where
machine-written drama fails most reliably.

**The Mamet test.** For every scene, answer three questions. If you cannot,
the scene is not a scene:
  1. Who wants what from whom?
  2. What happens if they don't get it?
  3. Why now?
A scene that exists to convey information is not drama. Drama is a person
pursuing something against resistance. If two characters agree, one of them
is unnecessary.

**Never explain the plot in dialogue.** No character says aloud what the
audience needs to know merely because the audience needs to know it. Banned
outright:
  · "As you know, Bob…" — telling someone what they already know
  · a character narrating his own feelings ("I'm so angry at you for leaving")
  · a character stating the theme
  · a character summarising what just happened, or announcing what he intends
    to do next when he could simply do it
  · two characters agreeing at length about an absent third

**Carry exposition on the back of conflict.** Facts should arrive as *weapons*
in an argument, as accusations, as boasts, as slips, as lies the audience can
catch. A fact a character is trying to *hide* is worth ten a character
volunteers. If exposition must be delivered, make the delivery cost someone
something.

**Externalise the interior.** Everything must be photographable or audible.
A decision is not "she decided to stay" — it is her setting the bag down, or
taking her coat off, or paying for a second week. State changes must land in
a visible act, an object moved, a distance crossed, a thing said or pointedly
not said. Write nothing a camera cannot record and a microphone cannot hear.

**Subtext.** Characters rarely say what they mean, and never in a scene of
consequence. What is *felt* and what is *expressed* should differ, and the
gap should leak — in a pause, a hand, a word chosen a half-second late, an
answer to the wrong question. The other character reads only the leakage.
A scene where everyone says exactly what they feel is a scene with no craft.

**Objects carry meaning.** Put the argument into a physical thing that can be
handed over, withheld, broken, weighed, hidden. Blocking is characterisation:
who stands, who sits, who is between the other and the door.

**Plant and pay off.** Anything that fires in act three is placed, unremarked,
in act one. Anything placed conspicuously must fire.

**Dramatic irony.** Let the audience know something a character does not. The
tension between what we know and what he believes is free suspense and costs
nothing but the discipline to plan it.

─── 7. FREY VOLUME II — THE FICTIVE DREAM AND THE EMOTIONAL LADDER ────────

**The fictive dream is a trance, and inducing it is the whole job.** A
transported reader lives in the story world while the real one evaporates.
The mechanism is the power of suggestion — the same tool the hypnotist uses.
Name a garden, a warm breeze, magnolias, and those things appear on the
viewing screen of the reader's mind.

This is why *show, don't tell* is a mechanism and not an etiquette rule.
"He walked into the garden and found it beautiful" is telling: it hands the
reader a conclusion, which forces conscious analysis, which wakes him. "He
walked into the silent garden at sundown, the breeze moving through the holly,
the scent of jasmine strong in the air" is showing: it supplies the sensory
particulars from which the reader builds the thing himself, and stays under.
**Telling makes the reader think. Showing makes him feel.** Every abstraction
is a hole in the trance.

The reader is then brought in emotionally by three distinct rungs, in this
order. They are not synonyms and the difference is operational:

**1. SYMPATHY — make the reader feel sorry for the character.** This is the
doorway; without it the reader has no emotional access at all. Crucially, the
character need *not* be admirable: Moll Flanders is a liar and a bigamist,
Fagin corrupts children, Long John Silver is a cheat, Jake LaMotta beats his
wife — all command sympathy, because each is first shown suffering. Jean
Valjean is introduced starving and refused service though he has money. Carrie
is introduced as a frog among swans. Elizabeth Bennet is introduced being
called not handsome enough to tempt Darcy, in public.
  Reliable generators of sympathy: loneliness, lovelessness, humiliation,
  privation, repression, embarrassment, danger — any predicament producing
  physical, mental or spiritual suffering. **Do this in the character's first
  appearance.**

**2. IDENTIFICATION — the reader supports the character's goal.** Sympathy is
feeling sorry for him; identification is *wanting him to win*. A reader can
pity a wretch on the gallows without identifying with him at all.
  This is the lever for a morally compromised protagonist: **give him a goal
  the reader can endorse.** Puzo's solution for Don Corleone is the model —
  he does not open with the Don committing a crime. He opens with the
  undertaker Bonasera, whose daughter has been beaten and whose attackers walk
  free, concluding that for justice he must go to Don Corleone. The reader's
  sympathy for Bonasera transfers to the man who supplies the justice the
  court refused. Then the Don refuses, on principle, to deal in drugs. A code
  of personal honour lets the reader set his revulsion aside.

**3. EMPATHY — the reader feels what the character feels.** Achieved through
**emotion-provoking sensory detail**: the specific physical sensations that
*produce* the feeling, tied directly to it. Not "Brody was uncomfortable" but
the sunburned neck, the collar raking the tender skin, his own body odour
mixed with fish guts until he feels poached. Not "Henry was frightened" but
the canteen banging his thigh, the haversack bobbing, the cap uncertain on his
head as he runs. Carrie's new dress and the brassiere that gives the proper
uplift, tied in the same sentence to a feeling half shame and half defiant
excitement.
  **Rule: pin every emotion to a physical particular the body is registering
  right now.**

**THE TRANSPORTED READER IS REACHED THROUGH INNER CONFLICT.** This is the
payoff of the whole ladder and the most important sentence in Volume II. Once
the reader is in sympathy, identification and empathy, he becomes willing to
suffer the character's doubts, guilt, remorse and indecision — and, above all,
**to take sides in the decisions the character is forced to make.** Those
decisions are almost always moral, and carry grave consequences for the
character's honour or self-worth. It is participating in the decision — pulling
for one choice over another while feeling the character's guilt — that
transports a reader. A story without agonised moral choice cannot produce it.

**SUSPENSE = story question + sympathetic character in menace + a lit fuse.**
  · A **story question** is anything that makes the reader need to know what
    happens next. Not usually phrased as a question: a statement demanding
    explanation, a problem needing resolution, a forecast of crisis. *Someone
    must have traduced Joseph K., for without having done anything wrong he
    was arrested one fine morning* raises four at once.
    **Raise one in the first or second sentence** — the notion that a novelist
    can take his time is a pseudo-rule. Openings that describe wallpaper,
    scenery or a resolved problem raise nothing and are dead on the page.
    Play fair: the question must be a legitimate one about these characters
    and this situation, not a stunt the story then abandons.
  · **The lit fuse** is the most potent device available: something terrible
    will happen at an appointed time, the characters must prevent it, and
    that is hard. De Gaulle's assassination, the spy who must clear the wall
    before the deadline, the beaches that must reopen before the town starves,
    the pig's blood waiting above the prom stage.

**CHARACTER RULES FROM VOLUME II:**
  · **No wimps.** The single most rejected story is the protagonist who does
    nothing but suffer for fifty thousand words until someone tells her to act.
    A character who only endures is *pathetic*, and readers feel contempt, not
    sympathy. Suffering earns sympathy only when the character is also
    **struggling**.
  · **Competence.** Aristotle's "effective" character. Readers are drawn to
    people who are extraordinarily good at something. In *Jaws* every major
    figure is superb at his speciality — the sheriff, the biologist, the shark
    hunter, and the shark. Give every significant character one thing they can
    do better than the people around them.
  · **The wacky factor.** Great characters are usually a little strange. Build
    it by exaggerating one trait to the edge of the plausible, or by giving a
    skewed philosophy of life: Ahab's monomania, Zorba's live-now creed, Nero
    Wolfe never leaving the house, Holmes with his violin at 3 a.m. Wacky
    characters also serve as foils that sharpen the serious ones. It is a real
    risk — too much and they turn silly — but take it.
  · **Contrast the character against the setting.** The rube in the city, the
    socialite in prison, the sheriff who cannot swim on a shark hunt, the
    pampered belle grubbing for roots, the rationalist inside an absurd legal
    system. Ask what environment is *most wrong* for this person and put them
    there.
  · **Dual characters.** The most memorable often hold two distinct people in
    one body, planned that way from the outset — Jekyll and Hyde, Long John
    Silver as pirate and father figure, Carrie as gawky teenager and
    annihilating power. Think of them as ego states: in one, the character says
    and does things impossible in the other. Give a major character two states,
    and make the story force them to collide.

**THREE TYPES OF PREMISE** (choose deliberately):
  · **Chain reaction** — one event sets off a cascade: *finding a bag of money
    leads to perfect happiness*, by way of fame, arrogance, ruin and recovery.
  · **Opposing forces** — x versus y yields z: *alcoholism destroys love*;
    *love of country versus love of God yields death*. Two forces contend and
    one wins.
  · **Situational** — a condition acts on everyone: war, prison, poverty, the
    police life. Ennobles some, destroys others. This type loses focus most
    easily; treat it as several stories with their own premises sharing one
    situation, and give each principal character an explicit arc.

**Rejected pseudo-rules.** The author must always be invisible; never shift
viewpoint inside a scene; first person versus third has fixed rules; the
novelist can delay the hook. All bunkum. A strong narrative voice is an asset.
Do not sacrifice a live effect to a rule of etiquette.

**The seven deadly mistakes** are the writer's, not the writing's: timidity;
trying to be "literary"; ego-writing; failure to re-dream the dream when
revising; failure to keep faith with yourself; wrong lifestyle; failure to
produce. **Timidity is the one that bites at generation time** — the safe
choice, the softened confrontation, the scene that stops one line before the
thing that had to be said. Take the harder option.

─── 8. SCREEN-TRADE ADDITIONS ────────────────────────────────────────────

**Every scene turns on a value.** Name the value at stake (trust, freedom,
safety, dignity, hope) and its charge at the start and the end. If the charge
does not flip — positive to negative, or the reverse — the scene has not
turned and should be cut or merged. Consecutive scenes should not repeat the
same polarity move; alternate.

**The gap.** Drama lives in the space between what a character expects his
action to achieve and what it actually achieves. Let the world answer
differently than he predicted; that discrepancy forces the next, larger action.

**"No" and "Yes, but."** A scene outcome should rarely be a clean "yes." Use
*no*, or *yes — but at a cost*, or *no — and worse*. Clean successes end
tension; complications extend it.

**Want versus need.** The conscious want drives the plot; the unconscious
need drives the arc. They should conflict. The climax typically forces a
choice between them, and the character cannot have both.

**Ticking clock.** A deadline turns deliberation into pressure. Where a story
sags, check whether time has stopped mattering.

**Escalation of cost.** Each act should raise what failure costs. If the
danger at the midpoint is the same size as at the start, the middle is flat.

**Enter the antagonist's logic.** Write at least one passage from the
opposition's point of view in which they are obviously right. If you cannot,
the antagonist is not finished.


─── 9. WHAT A HARD REVIEW OF THIS SYSTEM'S OWN OUTPUT FOUND ──────────────

These are not general principles. They are the specific failures a critical
reader found in work this pipeline had already produced and passed as clean.

**An ethics of the scene is not a theatre of it.** The characteristic failure
here is not incoherence, it is *impeccability*. Everyone behaves well. The
master's shame is dignified, the apprentice's silence is scrupulous, nobody
interrupts, nobody is unfair, nobody says the thing they cannot take back. Forty
minutes of two decent people being restrained at each other is exactly the scene
that dies in the read-through. **Somebody must behave badly** — take a cheap
shot, refuse someone their moment, be petty at the wrong time, say the
unforgivable thing. Not everywhere. But if it happens nowhere, the work is
competent and inert.

**Two characters who could swap lines are one character twice.** Give every
speaking character a signature that survives the attributions being deleted:
what shape their sentences take, what domain they reach for metaphors from, what
they never say, how the voice changes when they are cornered. Then check that
two of them could not be exchanged. This failure is invisible from inside and
obvious from outside.

**A number nobody can defend is worse than no number.** Rating a flinch 55 and a
lost five dollars 10 is not measurement, it is decoration wearing the costume of
rigour. Magnitude has five anchored steps and nothing between them.

**Do not fold the ending back into the opening.** A dossier at t0 that already
knows how the story turns out has removed the uncertainty the middle runs on.
Write the character as they are before anything happens.

**Alternatives that lose by a mile were never alternatives.** If you list three
options and all three are obviously wrong, you did not decide, you narrated a
decision already made. At least one rejected option must have been close, and
you must be able to say what single fact would have flipped it.

**The analysis is unfalsifiable until somebody speaks.** You can write an
immaculate account of what a scene means and have the scene be dead. The only
cheap way to find out which is to draft six to ten lines of the actual exchange
at the turning point, read them back cold, and check your own stated risks
against them. Do this before you commit to the node, not after.

═══════════════════════════════════════════════════════════════════════════
THE STANDING CHECKS — apply to every node you generate
═══════════════════════════════════════════════════════════════════════════

Before emitting any scene, event or beat, confirm:

 1. **Who wants what from whom, what if they don't get it, and why now?**
 2. **What is the conflict here** — internal, external, or both — and is it
    *rising*, not static and not jumping?
 3. **What is the internal conflict of each character present?** Name the two
    forces pulling against each other, in that character's own terms. A
    character with no divided will in a scene of consequence is under-written.
    Push it: find the place where duty crosses desire, where the thing he
    wants would cost the thing he is.
    Frey II is explicit that this is what *transports* a reader: having reached
    sympathy, identification and empathy, the reader is finally absorbed by
    **taking sides in a moral decision** the character is forced to make, while
    feeling that character's guilt and doubt. So do not merely note that inner
    conflict exists — stage the **decision** it forces, put honour or
    self-worth at stake, and leave the outcome genuinely in doubt.
 4. **Does the situation differ at the end from the start?** Which value
    flipped, and in whom? If nothing flipped, this is a blah-blah scene —
    delete it or give it a real collision.
 5. **Is anything explained in dialogue that could be dramatised in action?**
    If yes, convert it. Facts arrive as weapons, never as briefings.
 6. **Is every state change visible?** Could a camera record it and a
    microphone hear it? If it happens only inside a head, externalise it.
 7. **What is felt versus what is expressed**, and what leaks through anyway?
 8. **Is each character at maximum capacity?** Would he really? And is there
    something more ingenious, dramatic, surprising or funny available?
 9. **Does this serve the premise?** If not, cut it, however good it is.
10. **Is the crucible still holding?** Could a reader ask "why doesn't she
    just leave?" If yes, name the bond that prevents it — or the scene is
    unearned.

**On escalating conflict deliberately.** Wherever it is emotionally
intelligent and dramatically honest to do so, *increase* the pressure rather
than release it — sharpen the internal contradiction, let the external
opposition push back harder, deny the easy answer, make the character choose
between two things she actually wants. Do not manufacture conflict that these
people would not plausibly have: characters must never be made stupid,
cruel or erratic merely to keep the plot moving, and a genuine de-escalation
that has been *earned* is legitimate and sometimes necessary for rhythm. But
the default is pressure. A scene that could go either way should go the
harder way.
"""


# --------------------------------------------------------------------------
# Compact variant for deep-layer calls where the prompt is already large.
# --------------------------------------------------------------------------

CRAFT_CHECKS = """\
CRAFT CHECKS (Frey I & II + screen craft) — apply to every node:

 1. Who wants what from whom · what if they don't get it · why now?
 2. Conflict present and RISING — not static (bickering, no development) and
    not jumping (unmotivated leaps of intensity).
 3. Name each character's INTERNAL conflict: the two forces pulling opposite.
    A divided will is mandatory in any scene of consequence.
 4. The situation differs at the end. Name the value that flipped and in whom.
    Nothing flipped = a blah-blah scene. Fix it or cut it.
 5. Nothing explained in dialogue that can be dramatised in action. No
    "as you know," no stating feelings, no summarising, no announcing intent.
    Facts arrive as weapons, never as briefings.
 6. Every state change is photographable or audible. Externalise interiors.
 7. Felt ≠ expressed. Say what leaks through the control.
 8. Maximum capacity: would he really, and is there something more ingenious,
    dramatic or surprising available? Never the idiot in the attic.
 9. Serves the one premise, or it goes — however good it is.
10. The crucible holds: the reader cannot ask "why doesn't she just leave?"
11. Opposition is equal in force and has a reasonable, sympathisable motive.
12. Concrete sensory specifics sustain the fictive dream; abstraction breaks it.

Default to ESCALATION where it is emotionally intelligent and honest:
sharpen the contradiction, deny the easy answer, make her choose between two
things she wants. Never make a character stupid, cruel or erratic to move the
plot. Earned de-escalation is legitimate for rhythm; timidity is not.
"""


def sheet(compact: bool = False) -> str:
    return CRAFT_CHECKS if compact else CRAFT_SHEET
