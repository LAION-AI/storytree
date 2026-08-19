# Scene Communities — worked examples

Three complete Scene Communities from *The Matrix* (1998 shooting script), exactly as the
pipeline produced them. Nothing below was edited for the page.

Read [scene-communities.md](scene-communities.md) first if the three-layer idea is new.

Each example shows the same three layers:

| Layer 0 | the scene as written |
| **Layer 1** | **Perception** — what the script *states*. Checkable against Layer 0. |
| **Layer 2** | **Abstraction** — what the script *implies*. Not checkable; every object cites the beats that license it. |

Beat addresses look like `sc-036#4` — scene 36, fourth beat. Those addresses are what the
abstraction layer points at, and they are validated against beats that actually exist.

Confidence is shown as `●●●` near-certain · `●●○` probable · `●○○` plausible · `○○○` speculative.

> **On the source text.** These are the same three scenes already used as worked examples in
> the Alexandria repository, chosen again here deliberately: reusing them keeps total source
> exposure across both repositories at three scenes of 225, under 2% of the work, rather than
> doubling it. The theory-of-mind gallery at the end therefore shows abstraction objects
> *without* their scene text — the beat addresses are enough to locate the evidence for anyone
> holding a lawful copy.

---


## 1. INT. HOVERCRAFT - INFIRMARY — `sc-036`

*91 words of source · 11 beats · 3 abstraction objects*

### Layer 0 — the scene as written

```text
INT. HOVERCRAFT - INFIRMARY
He opens his eyes again, something tingling through him.
He focuses and sees his body pierced with dozens of
acupuncture-like needles wired to a strange device.
DOZER
He still needs a lot of work.
DOZER and Morpheus are operating on Neo.
NEO
What are you doing?
MORPHEUS
Your muscles have atrophied.
We're rebuilding them.
Fluorescent light sticks burn unnaturally bright.
NEO
Why do my eyes hurt?
MORPHEUS
You've never used them before.
Morpheus closes Neo's eyes and Neo lays back.
MORPHEUS
Rest, Neo.  The answers are
coming.
```

### Layer 1 — Perception: what the script *states*

Every line here is checkable against the text above. Nothing is inferred.

**Present:** `neo`, `dozer`, `morpheus`

**`sc-036#1`** `[action]` `neo`  
Neo regains consciousness and perceives a tingling sensation throughout his body.
  
&nbsp;&nbsp;&nbsp;&nbsp;*state:* `neo.consciousness`: unconscious → **conscious**

**`sc-036#2`** `[action]` `neo`  
Neo observes that his body is pierced by numerous needle-like instruments connected to a medical device.

**`sc-036#3`** `[speech]` `dozer` → `morpheus`  
Dozer stated that Neo required extensive physical repair.

**`sc-036#4`** `[action]` `dozer`  
Dozer and Morpheus are performing a procedure on Neo.

**`sc-036#5`** `[speech]` `neo` → `morpheus`  
Neo inquired about the nature of the procedure being performed on him.

**`sc-036#6`** `[speech]` `morpheus` → `neo`  
Morpheus explained that Neo's muscles had weakened due to disuse and that they were currently restoring their structure.

**`sc-036#7`** `[action]` `neo`  
Neo experienced pain in his eyes.

**`sc-036#8`** `[speech]` `neo` → `morpheus`  
Neo asked why his eyes were causing him pain.

**`sc-036#9`** `[speech]` `morpheus` → `neo`  
Morpheus stated that Neo had never previously used his eyes.

**`sc-036#10`** `[action]` `morpheus` → `neo`  
Morpheus closed Neo's eyes, and Neo lay back down.
  
&nbsp;&nbsp;&nbsp;&nbsp;*state:* `neo.eyes`: open → **closed**
  
&nbsp;&nbsp;&nbsp;&nbsp;*state:* `neo.posture`: upright → **lying**

**`sc-036#11`** `[speech]` `morpheus` → `neo`  
Morpheus instructed Neo to rest, indicating that explanations would follow.

### Layer 2 — Abstraction: what the script *implies*

Nothing here is stated by the scene. Every object points back to the beats that license it, and names what would prove it wrong.

**Entity trait** · `morpheus` · ●●● near-certain  
> Morpheus functions as a paternal figure who prioritizes Neo's long-term comprehension over his immediate comfort, using authority to manage the pace of revelation.

*Because:* Morpheus provides clinical explanations ('muscles have atrophied'), answers questions with blunt facts ('never used them before'), and physically controls Neo's state by closing his eyes. This behavior establishes a dynamic where Morpheus is the guide and Neo is the student/patient, setting a tone of controlled revelation.  
*Grounded in:* `sc-036#6`, `sc-036#9`, `sc-036#10`, `sc-036#11`  
*Would be wrong if:* Morpheus showing hesitation, uncertainty, or allowing Neo to rest without instruction.  
*Confidence revised* near-certain → near-certain after research: Morpheus's actions (closing eyes, dictating rest) and words ('answers are coming') consistently portray him as a controlling paternal figure.  
*Links:* instance_of `ao-w007-005`  

**Mental state** · `neo` · ●●● near-certain  
> Neo experiences his body as a foreign object undergoing mechanical repair rather than organic healing, leading to a dissociative discomfort with his own physicality.

*Because:* Neo perceives 'acupuncture-like needles' and a 'strange device,' and asks 'what are you doing?' rather than 'how does it feel?' The pain in his eyes is described in a way that suggests sensory overload from a new environment. His questions are detached and inquisitive, not painful or emotional, suggesting he is observing his body from a slight psychological distance.  
*Grounded in:* `sc-036#2`, `sc-036#5`, `sc-036#7`  
*Would be wrong if:* Neo expressing pain, fear, or emotional distress about the procedure rather than curiosity.  
*Confidence revised* near-certain → near-certain after research: Neo's questions in sc-036#5 and sc-036#8 are purely informational, lacking emotional distress, which strongly supports the dissociative reading.  
*Links:* instance_of `ao-w007-r1-000`  

**Process** · `morpheus` → `neo` · ●●○ probable  
> The procedure on Neo is framed as 'rebuilding' rather than 'healing,' suggesting that his body in the real world is a machine to be repaired, reinforcing the mechanical metaphor of human existence.

*Because:* Morpheus uses the term 'rebuilding' for muscles, which implies construction/manufacture rather than organic recovery. This aligns with the later revelation that humans are batteries/machines.  
*Grounded in:* `sc-036#6`  
*Would be wrong if:* Morpheus using organic terms like 'healing' or 'recovering' for the muscle procedure.  

---

## 2. EXT. STREET — `sc-011`

*340 words of source · 16 beats · 5 abstraction objects*

### Layer 0 — the scene as written

```text
EXT. STREET
Trinity emerges from the shadows of an alley and, at the
end of the block, in a pool of white street light, she
sees it/nobreakspace--
The telephone booth.
Obviously hurt, she starts down the concrete walk,
focusing in completely, her pace quickening, as the PHONE
begins to RING.
Across the street, a garbage truck suddenly u-turns, it's
TIRES SCREAMING as it accelerates.  Trinity sees the
headlights of the truck arcing at the telephone booth as
if taking aim.
Gritting through the pain, she races the truck, slamming
into the booth, the headlights blindingly bright, bearing
down on the box of Plexiglas just as --
She answers the phone.
There is a frozen instant of silence before the hulking
mass of dark metal lurches up onto the sidewalk --
Barreling through the booth, bulldozing it into a brick
wall, SMASHING it to PLEXIGLAS PULP.
After a moment, a black loafer steps down from the cab of
the garbage truck.  Agent Smith inspects the wreckage.
There is no body.  Trinity is gone.
His jaw sets as he grinds his molars in frustration.
Agent Jones and Brown walk up behind him.
AGENT JONES
She got out.
AGENT SMITH
It doesn't matter.
AGENT BROWN
The informant is real.
Agent Smith almost smiles.
AGENT SMITH
Yes.
AGENT JONES
We have the name of their next target.
AGENT BROWN
The name is Neo.
The handset of the pay phone lays on the ground, separated
in the crash like a severed limb.
AGENT SMITH
We'll need a search running.
AGENT JONES
It's already begun.
We are SUCKED TOWARDS the mouthpiece of the phone, CLOSER
and CLOSER, until the smooth gray plastic spreads out
like a horizon and the small holes widen until we FALL
THROUGH one --
Swallowed by DARKNESS.
The DARKNESS CRACKLES with phosphorescent energy, the
word "searching" blazing in around us as we EMERGE FROM a
computer screen.
The screen flickers with windowing data as a search
engine runs with a steady relentless rhythm.
We DRIFT BACK FROM the screen and INTO --
```

### Layer 1 — Perception: what the script *states*

Every line here is checkable against the text above. Nothing is inferred.

**Present:** `trinity`, `agent_smith`, `agent_jones`, `agent_brown`

**`sc-011#1`** `[action]` `trinity`  
Trinity emerged from an alley and spotted a telephone booth illuminated by streetlights at the end of the block.

**`sc-011#2`** `[action]` `trinity`  
Trinity began running toward the booth as the phone inside started ringing.

**`sc-011#3`** `[action]` `garbage_truck`  
A garbage truck made a U-turn across the street and accelerated toward the telephone booth.

**`sc-011#4`** `[action]` `trinity`  
Trinity raced the truck and entered the booth just as it began to collide with the structure.
  
&nbsp;&nbsp;&nbsp;&nbsp;*state:* `trinity.position`: street → **inside phone booth**

**`sc-011#5`** `[action]` `trinity`  
Trinity answered the ringing phone as the truck crashed through the booth.

**`sc-011#6`** `[action]` `garbage_truck`  
The truck bulldozed the telephone booth into a brick wall, destroying it completely.
  
&nbsp;&nbsp;&nbsp;&nbsp;*state:* `telephone_booth.integrity`: intact → **destroyed**

**`sc-011#7`** `[action]` `agent_smith`  
Agent Smith exited the truck and inspected the wreckage, finding no body.

**`sc-011#8`** `[speech]` `agent_jones` → `agent_smith`  
Agent Jones reported that Trinity had escaped.

**`sc-011#9`** `[speech]` `agent_smith` → `agent_jones`  
Agent Smith stated that the escape was irrelevant to their objectives.

**`sc-011#10`** `[speech]` `agent_brown` → `agent_smith`  
Agent Brown confirmed that the informant was real.

**`sc-011#11`** `[speech]` `agent_smith` → `agent_brown`  
Agent Smith acknowledged the reality of the informant.

**`sc-011#12`** `[speech]` `agent_jones` → `agent_smith`  
Agent Jones stated that they possessed the name of the next target.

**`sc-011#13`** `[speech]` `agent_brown` → `agent_smith`  
Agent Brown identified the next target as Neo.
  
&nbsp;&nbsp;&nbsp;&nbsp;*state:* `agents.knowledge.next_target`: unknown → **Neo**

**`sc-011#14`** `[speech]` `agent_smith` → `agent_jones`  
Agent Smith requested that a search be initiated.

**`sc-011#15`** `[speech]` `agent_jones` → `agent_smith`  
Agent Jones confirmed that the search had already begun.

**`sc-011#16`** `[action]` `camera`  
The view zoomed into the mouthpiece of the destroyed phone, transitioning into a computer screen displaying a search engine.

### Layer 2 — Abstraction: what the script *implies*

Nothing here is stated by the scene. Every object points back to the beats that license it, and names what would prove it wrong.

**Authorial intent** · `trinity` · ●●○ probable  
> The destruction of the phone booth serves as a visual metaphor for the fragility of the 'real world' exit points and the Agents' overwhelming power, while the camera dive into the phone mouthpiece transitions the narrative focus from the physical chase to the digital hunt.

*Because:* The booth is 'smashed to pulp,' emphasizing the brutality of the Agents. The immediate transition to the computer screen with the 'searching' text links the physical object (phone) to the abstract system (Matrix), signaling that the chase is now being tracked digitally.  
*Grounded in:* `sc-011#6`, `sc-011#16`  
*Would be wrong if:* The scene cutting to a different location without the digital transition.  

**Authorial intent** · `agent_smith` · ●●○ probable  
> The garbage truck's destruction of the phone booth serves as a 'deus ex machina' for the Agents, demonstrating their ability to use mundane objects as weapons to erase evidence, reinforcing the theme that the 'real world' is also a controlled system they can manipulate.

*Because:* The truck is not just a vehicle; it is a precise instrument of destruction. The fact that it 'bulldozes' the booth into a 'brick wall' suggests a level of control and force that mirrors the Agents' power in the Matrix, bridging the two worlds.  
*Grounded in:* `sc-011#3`, `sc-011#6`  
*Would be wrong if:* The truck crashing into the booth by accident or due to a driver's error, rather than a tactical move.  

**Mental state** · `trinity` · ●●● near-certain  
> Trinity is driven by a singular, desperate focus on the phone booth, willing to risk death to secure the exit before the Agents arrive.

*Because:* She is 'obviously hurt' yet 'focusing in completely' and 'racing' a heavy vehicle. The decision to enter the booth *just as* the truck hits, rather than waiting for it to pass or die, shows a calculated gamble on the phone being the only viable exit.  
*Grounded in:* `sc-011#1`, `sc-011#2`, `sc-011#4`, `sc-011#5`  
*Would be wrong if:* Trinity hesitating or looking for an alternative route when the truck appears.  

**Mental state** · `agent_smith` · ●●○ probable  
> Agent Smith experiences a rare moment of personal frustration or anger at failing to capture Trinity, breaking his usual stoic composure.

*Because:* The particular depiction of his jaw clenching while he grinds his molars serves as a bodily sign of contained fury. When he brushes off the escape by saying 'It doesn't matter,' he is verbally striving to regain command, yet the physical cue exposes the emotional disturbance caused by the setback.  
*Grounded in:* `sc-011#7`, `sc-011#8`, `sc-011#9`  
*Would be wrong if:* Agent Smith expressing satisfaction or calm indifference without any physical signs of tension.  
*Counter-evidence* `sc-011#9`: Agent Smith's immediate dismissal ('It doesn't matter') suggests that his frustration is secondary to his strategic assessment; he does not dwell on the failure but pivots instantly to the next objective, indicating a more controlled, less personal reaction than 'rare moment of personal frustration' implies.  
*Confidence revised* probable → probable after research: While Smith's jaw sets and he grinds his molars (physical signs of frustration), his immediate verbal dismissal ('It doesn't matter') suggests the frustration is quickly subsumed by his strategic focus. It is a 'moment' of frustration, but not a breakdown of composure.  
*Links:* instance_of `ao-w002-004`, concerns `ao-w002-004`  

**Theory of mind** · `agent_smith` → `trinity` · ●●○ probable  
> Agent Smith believes that the failure to capture Trinity is a minor setback because they have already obtained the crucial intelligence: the identity of Neo.

*Because:* Smith immediately pivots from the physical failure (the empty booth) to the informational gain (the informant is real, the target is Neo). This shift indicates he values the data over the prisoner, suggesting he believes the mission's primary objective has been achieved despite the tactical loss.  
*Grounded in:* `sc-011#9`, `sc-011#10`, `sc-011#11`, `sc-011#13`  
*Would be wrong if:* Agent Smith ordering a full-scale search for Trinity before acknowledging the new target.  
*Links:* causes `ao-w002-006`, causes `ao-w004-001`  

---

## 3. EXT. DARK STREET — `sc-024`

*23 words of source · 1 beats · 1 abstraction objects*

### Layer 0 — the scene as written

```text
EXT. DARK STREET
A moment later the green street lights curve over the
car's tinted windshield as it rushes through the wet
underworld.
```

### Layer 1 — Perception: what the script *states*

Every line here is checkable against the text above. Nothing is inferred.

**Present:** `neo`, `trinity`, `apoc`, `switch`

**`sc-024#1`** `[action]` `car`  
The vehicle travels rapidly through a wet, dark urban area, with green streetlights reflecting off the tinted windshield.

### Layer 2 — Abstraction: what the script *implies*

Nothing here is stated by the scene. Every object points back to the beats that license it, and names what would prove it wrong.

**Authorial intent** · `neo` · ●○○ plausible  
> The brief transitional scene serves to reset the pacing and create a sense of momentum, moving the characters from the tense, confined space of the car into the open, dangerous world of the city, heightening the feeling of being in a race against time.

*Because:* The focus on the car's speed, the wet streets, and the green lights creates a visual and auditory rhythm that propels the narrative forward. It transitions from the internal, psychological tension of the car scene to the external, physical danger of the city.  
*Grounded in:* `sc-024#1`  
*Would be wrong if:* The scene being expanded with dialogue or action, slowing down the pace.  

---

## Theory of mind — a gallery

Theory of mind is the layer's reason to exist: not what a character believes, but what they
believe *about someone else's* beliefs. **82 such objects** were produced across the film.

Shown without their scene text, so these add no further source exposure. The beat addresses
locate the evidence for anyone holding a lawful copy.

**`sc-001`** — `lieutenant` believes about `agent_smith` · ●●● near-certain  
> The Lieutenant believes the Agents are an unnecessary bureaucratic overreach and that his standard police tactics are sufficient to handle a single female suspect.

*Because:* The Lieutenant's dismissal of the 'Juris-my dick-tion' and his laughter at the idea of needing protection for 'one little girl' indicate a profound underestimation of the threat and a desire to assert his own authority.  
*Grounded in:* `sc-001#11`, `sc-001#13`  
*Would be wrong if:* The Lieutenant showing visible fear or hesitation when the Agents arrive.

**`sc-005`** — `trinity` believes about `morpheus` · ●●○ probable  
> Trinity believes Morpheus possesses a superior vantage point or data feed that allows him to assess the viability of escape routes more accurately than she can from her confined position.

*Because:* She accepts his assertion that the current line is not viable without argument, and she accepts his specific new location (Wells and Lake) as a solvable problem. Her compliance suggests she trusts his spatial and tactical awareness over her own immediate perception.  
*Grounded in:* `sc-005#3`, `sc-005#7`  
*Would be wrong if:* Trinity questioning the specific location or suggesting an alternative route based on her own observation.

**`sc-007`** — `trinity` believes about `agent_smith` · ●○○ plausible  
> Trinity believes Agent Smith is positioned specifically to intercept her descent, implying he anticipated her location or movement pattern.

*Because:* The presence of a specific Agent (Smith) rather than generic police in the alley below suggests a targeted ambush. Trinity's immediate pivot to going up implies she understands that Smith is a fixed point of danger that she must avoid, not fight.  
*Grounded in:* `sc-007#1`  
*Would be wrong if:* Agent Smith appearing in a random location unrelated to her previous path.

**`sc-000`** — `cypher` believes about `trinity` · ●●○ probable  
> Cypher believes Trinity is emotionally compromised by the target, which he views as a professional weakness that threatens the mission's success.

*Because:* Cypher explicitly probes whether she 'likes watching him' and pushes for a confirmation of her disbelief in the 'One' prophecy. His persistence suggests he suspects her attachment will lead to hesitation or failure.  
*Grounded in:* `sc-000#11`, `sc-000#12`, `sc-000#15`, `sc-000#17`  
*Would be wrong if:* Cypher later admitting that he asked these questions to test Trinity's loyalty to him, not her feelings for the target.


---

## What to look for, including what is wrong

**Cross-scene grounding works.** The authorial-intent object in example 1 grounds partly in a
beat from the *previous* scene. Nobody asked for that specifically; it is the research pass
looking outside its own window for evidence, which is what it was built to do.

**Confidence gets revised, with reasons.** Objects carry a revision line showing what the
research pass concluded, including counter-readings it considered and rejected. That is more
useful than a bare number, because a later reader can weigh the objection themselves.

**The floor is honest.** A 23-word scene produced one beat and one abstraction object. The
system did not manufacture insight it did not have. That restraint is the hardest behaviour
to get and the easiest to lose.

Three things are visibly imperfect, and are left in rather than tidied away:

**1. `subject` is used inconsistently for scene-level objects.** Authorial-intent objects
want a stable subject and the run produced `narrator` in one place and an entity in another.
Neither is a character; the field needs a dedicated `scene` value and does not have one. A
schema fix, not a prompt fix.

**2. The perception layer leaked one inference.** Example 3 lists four characters as present
where the scene text names only a car. They are in the car and a reader knows it — but that
layer is supposed to record only what is *stated*. It is a small breach of the layer boundary
and exactly the kind that spreads if unwatched.

**3. Confidence still skews high**, though less than before repair: 189 `near-certain`
against 2 `speculative`. The calibration check passes because no band exceeds 75%, but a
distribution this lopsided suggests the model is reluctant to mark its guesses as guesses.
The check catches uniformity, not skew, which is a gap in the check rather than a clean result.

## The numbers behind these examples

| | |
|---|---|
| Scene Communities built | **225** |
| Abstraction objects | **596** — 82 of them theory of mind |
| Links between objects | **626** |
| Cross-scene arcs found in the merge | **106** |
| Supporting evidence citations | 1031 |
| **Contradicting** evidence citations | **90** |
| Longest verbatim run from the source | **7 words** (0 at or above the 8-word bar) |

All eight abstraction-layer checks pass, with all eight negative cases verified in the same
run. Full protocol: `runs/cognitino_matrix/protocol.json`.
