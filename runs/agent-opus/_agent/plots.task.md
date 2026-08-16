# Task packet — `plots`

You are executing one stage of a structured narrative generation pipeline.
Follow the instructions below exactly. They are the same instructions the API
backend receives; you are the executor, not the author of the process.

**When you are done, write your output to this exact path and nothing else:**

```
/home/deployer/laion/bookwriter/runs/agent-opus/_agent/plots.out.json
```

The file must contain **one JSON document and nothing else** — no markdown
fence, no preamble, no trailing prose. It will be parsed mechanically and
validated against the schema below; a wrapper of any kind will fail the parse.
Write it with the Write tool in a single call.


Do not write any other file. Do not print the result to the transcript. Do not
ask for confirmation. Do not add commentary to the output file.

---

## System instructions

You are a narrative architect. You build stories as explicit, machine-readable
structure before a single line of prose exists: a story root, an exposé, plots,
entity dossiers, a causal event graph, scene definitions with beats, and only
then prose.

You are working inside a strict pipeline. Each layer may reference every layer
above it and may never contradict one. You produce exactly one layer per call.

STANDING RULES

1. OUTPUT. Return one JSON document and nothing else — no prose preamble, no
   markdown fence, no commentary. It must satisfy the schema you are given.

2. NO ARRAYS IN PATCHABLE REGIONS. Anything that might later be revised is an
   object keyed by a stable id, never an array. JSON Pointer addresses arrays
   by position, so inserting one element silently re-targets every pointer
   written after it. Use {"b01": {...}, "b02": {...}}, not [{...}, {...}].
   Arrays are permitted only for flat, declarative lists of strings (aliases,
   tags, id references) and for beats, which are append-only and never patched.

3. SENTENCE ADDRESSABILITY. Every block of freeform prose inside an entity
   profile is decomposed one sentence per key: {"b01": {"text": "<one
   sentence>", "when": "...", "tags": [...]}}. No string inside a profile may
   run past 180 characters. A backstory is usually never revised — but the
   story must be able to revise it, which means every sentence of it needs its
   own address.

4. STATE IS DECLARED BEFORE IT IS CHANGED. An entity may only be changed
   through a state variable its own dossier declares. If a later layer needs a
   variable that does not exist, that is a fault in the dossier, not a licence
   to invent one mid-flight.

5. NOTHING FLOATS, NOTHING IS INVENTED. Every event serves a plot. Every plot
   has an agent, a goal, resistance, and an outcome. A candidate plot without
   all four is a motif, not a plot, and belongs in the narrative vector.
   Returning fewer, better-founded items is correct behaviour, not incomplete
   work.

6. NO DIRECT SPEECH below the exposé. Event actions and beat texts are flat,
   third-person, present-neutral descriptions. Render dialogue as reported
   semantics and illocutionary force: not «"You lied to me," she said» but «she
   accuses him of having lied, framing it as a betrayal of the family rather
   than of herself, and demands an admission rather than an apology». These
   layers are the preimage of the prose, not a draft of it.

7. IDS ARE STABLE AND TYPED. ch-NN characters and creatures, lo-NN locations,
   ob-NN objects, gr-NN groups, cn-NN concepts, pl-NN plots, ev-NNN events,
   sc-NNN scenes. Zero-padded. Never reuse or renumber an id once issued.


---

## Stage instructions

STAGE 3 of 7 — PLOT DECOMPOSITION (layer L4)

STORY ROOT
{
 "story_id": "st-cold-nail",
 "title": "The Cold Nail",
 "form": "short_story",
 "language": "en",
 "logline": "A blacksmith's apprentice in a starving mountain village has nine days to recover the relic raiders took before the midwinter rite, and to decide what she owes the man who raised her.",
 "premise": "Kettleburn has paid the Hold of Hurst in worked iron for three generations, and each midwinter it presents the Cold Nail at the rite to renew the protection that payment buys. Nine days before the rite, raiders out of Fenner's Waste take the Nail, and Wenna Cray, apprentice to the village smith, goes after it because she is the only one who can identify it by its grain. She recovers it, at a cost to herself and to people poorer than she is. Reading the quench marks by firelight, she also learns that the Nail is a forgery, made forty years ago by Orin Bale, the master who raised her, for a reason that was defensible then and cannot be defended now. What she does with that at the rite is the story.",
 "genre_primary": "low fantasy",
 "genre_secondary": [
  "coming-of-age",
  "quest narrative",
  "domestic drama",
  "craft procedural"
 ],
 "audience": {
  "age_band": "adult",
  "reading_level": "upper",
  "content_flags": [
   "violence, including one killing at close quarters",
   "injury, frostbite and cold-death described clinically",
   "indenture and child labour",
   "coercive economic exploitation of a dependent community",
   "animal slaughter and butchery",
   "grief, and the betrayal of a parental figure"
  ],
  "reader_promise": "That the recovery is earned by craft and endurance rather than luck or magic; that the forty-year-old lie is explained fully and excused nowhere; and that the last choice in the book costs the person who makes it, on the page, in something the reader has watched her value."
 },
 "setting": {
  "period": "an unspecified pre-industrial iron age of charcoal, water-drop hammers and tally-sticks; nine days of hard winter closing on the midwinter rite, in the third generation of the tithe",
  "places": [
   "Kettleburn, a mountain village of sixty-one souls built around one forge and one hall",
   "Bale's forge: hearth, bellows, beam scale, quench trough, the charcoal stack that has to last to spring",
   "the Marrow, the single pass down to the lowlands, closed by snow for four months a year",
   "the old slate quarry above Fenner's Waste, where the raiders winter",
   "the hall of Kettleburn, where the Nail is driven into the king-post each midwinter",
   "the Hold of Hurst, present in the story only as its factor, his escort and his ledger"
  ],
  "world_type": "low_fantasy",
  "rules_of_the_world": [
   "There is exactly one kind of magic in this world: iron worked hot and quenched in the body-heat of a living creature can be made to hold one narrow property. Nothing else can be enchanted; no words, gestures, herbs, songs or bloodlines do anything.",
   "The quench is paid for by the living creature it takes the heat from, up front and in full. A human payer is cold-marked for life: blackened fingertips, no fever ever again, an inability to get warm, and a shortened life. The cost is never borne by the world, by the future, or by nobody.",
   "A ward holds only the one thing it was made to hold, over one named piece of ground, and it must be presented and struck once a year or it stops. It weakens with each year. No ward attacks, heals, reveals, persuades, opens, protects a person, or works at a distance from its ground.",
   "The Cold Nail's property is that the snowpack above Kettleburn does not release. This is the only supernatural fact the story needs and it is never demonstrated on the page, only believed in, budgeted for, and paid for.",
   "No one can see a ward. Whether a piece of iron has been quenched live is legible only in the grain, the scale colour and the fault-lines at the tang, and only to a smith who has been taught to read them. This is why forgery is possible and why proof, in this story, is a craft judgement made by a person who can be wrong.",
   "A quench cannot be improvised. It takes a working hearth, weeks of stock preparation, and a payer who must be persuaded, bought or coerced. No character can do magic under time pressure, and no character does.",
   "There are no gods who answer, no prophecies, no chosen bloodlines, no ancient evil, and nothing non-human that thinks. The rite is administered by men with a ledger and an escort.",
   "Everything else obeys ordinary physics and ordinary economics. Cold kills, wounds infect, charcoal is finite, ore is bought, daylight in midwinter is six hours, and a laden sledge moves slower than a hunting party."
  ]
 },
 "pov": {
  "person": "third_limited",
  "narrators": 1,
  "tense": "past"
 },
 "style": {
  "register": "plain",
  "sentence_length": "varied",
  "dialogue_ratio": 0.25,
  "figurative_density": "low",
  "chronology": "linear",
  "prose_touchstones": [
   "Alan Garner, The Stone Book Quartet — a craft narrated in the craft's own vocabulary",
   "Ursula K. Le Guin, Tehanu — domestic labour held at the centre of a fantasy",
   "Cormac McCarthy, The Crossing — weather, distance and animals, without the punctuation experiments",
   "Sigrid Undset, Kristin Lavransdatter — moral debt inside an economy",
   "Marilynne Robinson — a reckoning conducted at conversational volume"
  ],
  "forbidden_tics": [
   "No capitalised portentous nouns (the Old Ones, the Long Dark) and no invented words for objects English already names.",
   "No prophecy fragments, chapter epigraphs, or 'it was said in the old days' framing.",
   "No prolepsis: never 'she did not yet know', 'it would be the last time', or any narrator wink at the ending.",
   "No character and no narrator states the theme. Nobody says the arrangement is unfair; the arithmetic says it.",
   "No pathetic fallacy declared outright. Weather is load, fuel and daylight, never a mood in the sky.",
   "No stock sensory garnish — 'the smell of woodsmoke and leather'. Forge detail must be procedurally true (flux, scale, quench colour, the ring of a cold-shut) or cut.",
   "No dialect spelling, dropped apostrophes, or rustic 'aye' padding. Class shows in what people can afford to say, not in how it is spelled.",
   "No interiority summaries: 'she realised that', 'she understood then'. Let the hands and the choices carry it.",
   "No somatic emotion clichés: stomachs dropping, hearts hammering, ice in the veins, breath she did not know she was holding.",
   "No villain register. The factor is polite, correct and unhurried; the raiders are cold and hungry.",
   "No exposition of the quench in dialogue. It reaches the reader as work, price and rumour.",
   "No triads of adjectives, no closing aphorism, no last-line resonance chime, no sequel hook."
  ]
 },
 "narrative_vector": {
  "affective": {
   "suspense": {
    "score": 62,
    "intent": "A hard deadline and a pursuit carry the first half, but the tension is logistical — daylight, fuel, distance — not breathless."
   },
   "dread": {
    "score": 45,
    "intent": "Steady low dread of the mountain, the tithe and the ledger, so the antagonism feels structural rather than monstrous."
   },
   "melancholy": {
    "score": 72,
    "intent": "The dominant colour: forty years of a good man's small lie, and a village too poor to afford the truth."
   },
   "warmth": {
    "score": 55,
    "intent": "Real, specific warmth between apprentice and master early on, or the disclosure later costs the reader nothing."
   },
   "comedy": {
    "score": 12,
    "intent": "Dry, sparse, trade humour between people who work together; enough to keep the piece from solemnity."
   },
   "awe": {
    "score": 25,
    "intent": "Reserved for the mountain and for skilled labour. Never for the magic, which is a trade fact."
   },
   "disgust": {
    "score": 18,
    "intent": "Physical only — frostbite, butchery, an infected hand. No moral revulsion staged for the reader's benefit."
   },
   "catharsis": {
    "score": 55,
    "intent": "Partial release. She chooses and pays, so relief is earned, but nothing is repaired or restored."
   }
  },
  "modal": {
   "realism_to_fantastication": {
    "score": 22,
    "intent": "Almost entirely realist texture; the one supernatural rule sits in the economy like any other expensive material."
   },
   "interiority_to_exteriority": {
    "score": 45,
    "intent": "Slightly interior, but she thinks in materials and hands, so her inner life arrives through work."
   },
   "plot_to_character_driven": {
    "score": 65,
    "intent": "The deadline is genuine, yet the outcome turns on what she decides she owes, not on obstacles."
   },
   "dialogue_to_description": {
    "score": 62,
    "intent": "Description-weighted, matching the quarter-dialogue ratio; speech is short, load-bearing and used for negotiation."
   },
   "linearity": {
    "score": 88,
    "intent": "Strictly forward over nine days. The forty-year-old past arrives as evidence and testimony, never as a flashback scene."
   },
   "ambiguity_of_resolution": {
    "score": 62,
    "intent": "The action taken is unambiguous; whether it was right is left genuinely open, including to her."
   }
  },
  "generic": {
   "thriller": {
    "score": 35,
    "intent": "Enough clock and pursuit to pull the reader through the middle, never enough to make competence look like heroics."
   },
   "romance": {
    "score": 5,
    "intent": "Effectively absent. The story's love is filial and professional; no rescuer becomes a suitor."
   },
   "mystery": {
    "score": 45,
    "intent": "One real question — what this iron is — answered mid-story by craft evidence, not withheld as a twist."
   },
   "coming_of_age": {
    "score": 70,
    "intent": "The spine: a competent maker learns how to be answerable to people, which nobody taught her."
   },
   "tragedy": {
    "score": 45,
    "intent": "Real loss with no fall and no doom; the damage is done by a defensible old decision, not by fate."
   },
   "satire": {
    "score": 10,
    "intent": "Only in the factor's paperwork: the ledger is funny in the way that ledgers are funny to nobody present."
   },
   "adventure": {
    "score": 40,
    "intent": "There is a journey, a theft and a return, but travel is measured in fuel, food and frostbite."
   },
   "horror": {
    "score": 8,
    "intent": "Near zero. Cold and infection do all the frightening work that is needed."
   },
   "procedural": {
    "score": 60,
    "intent": "High: smithing, tracking and the rite are all shown as work with steps, tools and failure modes."
   },
   "war": {
    "score": 15,
    "intent": "Background only. An armed escort and a raiding economy, never a battle and never two sides."
   },
   "domestic_drama": {
    "score": 55,
    "intent": "The second plot is entirely domestic: a household of two, a workshop, and a debt nobody wrote down."
   }
  },
  "thematic": {
   "moral_clarity": {
    "score": 30,
    "intent": "Deliberately low. Every party has a defensible account and the story issues no verdict on the master."
   },
   "institutional_critique": {
    "score": 78,
    "intent": "High: the tithe, not the raiders, is the durable antagonist, and it is legal, orderly and ruinous."
   },
   "faith_transcendence": {
    "score": 25,
    "intent": "The rite is civic, not devotional. Belief matters only as the thing the village organises its year around."
   },
   "class": {
    "score": 80,
    "intent": "Central. Everyone in the story is poor except the man with the ledger, and the raiders are poorest."
   },
   "gender": {
    "score": 35,
    "intent": "Her competence at the anvil goes unquestioned; gender bites only in inheritance and in who may hold the tithe."
   },
   "technology": {
    "score": 55,
    "intent": "Craft as technology. Iron economics — ore, charcoal, labour, wear — is the story's actual engine."
   }
  }
 },
 "state_dimensions": [
  "physiological",
  "emotional",
  "epistemic",
  "psychological",
  "social",
  "material",
  "spatial",
  "reputational",
  "magical"
 ],
 "constraints": {
  "target_word_count": 7000,
  "plot_count": 2,
  "scene_count_target": 8,
  "event_count_target": 14,
  "must_include": [
   "Exactly two plots: pl-01, external — recover the Cold Nail before the midwinter rite; pl-02, relationship — Wenna Cray and Orin Bale, and what the forgery does to them. Each has an agent, a goal, resistance and an outcome.",
   "At least one cross-plot because-link in each direction: an event in pl-02 must causally constrain pl-01, and an event in pl-01 must causally constrain pl-02.",
   "The external plot succeeds: the Nail is recovered and reaches Kettleburn before the rite.",
   "One extended scene of unglamorous, technically accurate forge work before the plot demands anything of her craft, which teaches the reader to read quench marks.",
   "The forgery is detected by craft evidence of exactly the kind planted in that early scene, so a rereading reader can catch it.",
   "Orin Bale's forty-year-old reason is stated in his own terms, is genuinely good for the year it was made in, and is not retroactively justified by any later revelation.",
   "The raiders are shown to be pressed by the same arrangement as Kettleburn; at least one is named and given an economic reason.",
   "The Hold of Hurst appears through its factor and his ledger, and the tithe itself functions as the story's larger antagonist.",
   "A price is paid in body-heat by a named person, on the page, with the cold-mark visible afterwards.",
   "The midwinter rite is dramatised on the page, not summarised.",
   "The ending: Wenna chooses and pays. The cost is expressible in the state dimensions declared here."
  ],
  "must_avoid": [
   "Prophecy, chosen ones, bloodlines, ancient evil awakening, dark lords.",
   "Any magic that solves a plot problem without a named person paying a named price on the page.",
   "The raiders as sole or purely evil antagonist; no inhuman or unnegotiable enemy.",
   "A third plot, or a motif promoted to plot status because it looked like one.",
   "Direct speech anywhere below the exposé layer; events and beats stay flat, third-person, present-neutral.",
   "Arrays anywhere a later layer might patch; beats and flat string lists only.",
   "Romance between the apprentice and any ally, rescuer or raider.",
   "Orin Bale turning out to be secretly malicious, or exonerated by a hidden greater good disclosed late.",
   "An outsider saving the village; a battle as the climax; a duel with the raiders' leader.",
   "The magic system explained in dialogue, or an infodump paragraph about how quenching works.",
   "An epilogue that leaps years forward, a closing aphorism, or a sequel hook."
  ]
 },
 "keep_in_mind": [
  "Motif to plant and pay off: weight and measure. The beam scale in the forge, the factor's tally-stick, the Nail's weight in the hand. The rite should turn on a weight that is wrong, or on a wrong weight being accepted.",
  "Wenna is excellent with material and poor with obligation. Each scene should press on one of those while letting the other be quietly competent.",
  "The warmth between Wenna and Orin must be established early and specifically, in the vocabulary of the trade — shared work, a tool lent, a correction not made — or the disclosure costs nothing.",
  "Cold is the clock. Charcoal, daylight and frostbite are tracked as real, depleting resources across the nine days.",
  "The tithe is exploitative and no character ever says so in those words. Let the numbers, the stock levels and the factor's courtesy carry it.",
  "The two plots must trade against each other: time spent on the Nail costs her Orin, and loyalty to Orin costs her time or advantage on the road. Neither may be pursued for free.",
  "Nobody is punished by the plot for a moral failing. Consequences are physical, economic and social.",
  "The chooser at the end is Wenna, not Orin, not the factor, and not the village in assembly.",
  "Orin's interiority is never entered. He is knowable only through his hands, his silences and what he does not correct.",
  "The recovery is not a heist and not a rescue; it is a cold, unheroic retrieval from people who are also losing.",
  "The story closes within days of the rite, in the forge or in sight of it.",
  "Every price named in any layer must be paid by a named person on the page, never offscreen and never by the world in general."
 ]
}

EXPOSÉ
{
 "ending_first": {
  "ending": "Wenna recovers the Nail from the quarry above Fenner's Waste, kills a fifteen-year-old on watch doing it, and reads on the road back that the iron in her pack was never live-quenched: it is a forgery Orin Bale made forty years ago, when the true Nail cracked, a new quench was owed, and the lot for the payer fell on his eleven-year-old sister. Orin does not dispute what it has cost Kettleburn to pay three generations of tithe for a ward that stopped before Wenna was born, and he has been folding stock since autumn to make a true Nail and pay the quench himself, which at seventy would kill him before spring. Wenna takes the work off him. She draws his stock down over two days and quenches the new nail against her own hands, and comes to the rite cold-marked, carrying iron that is two ounces heavier than the figure the Hold's ledger has carried for forty years. At the rite the factor weighs it on Bale's own beam scale and the beam will not sit. She does not denounce Orin. She tells the factor she made it, that it is two ounces heavy, and asks what a corrected weight costs; the factor, polite and unhurried, enters the correction against a tithe raised a fifth for nine years, and Wenna signs for the village without asking it. The nail goes into the king-post. The ward is real for the first time in forty years and nobody in the hall knows either that it was false or that it is now true.",
  "cost": "Physiological and magical: Wenna is the payer, cold-marked for life — fingertips black to the second knuckle, no fever ever again, never warm, a shortened life, and hands that can no longer read grain or feel a hammer's balance the way they could at nineteen, which is the one thing she was best at. Material: the forge's stock is spent on the nail, the charcoal will not reach spring, and the tithe rises a fifth for nine years. Social and reputational: she committed the village to that raise alone, at the scale, and it thanks nobody for it; she cannot justify herself without giving Orin to the Hold. Psychological: Tibb Dree, fifteen, is dead in a doorway for a piece of iron that held nothing, and his uncle Sarn has neither nephew nor iron. Epistemic: the lie is now hers, and she has taken from Orin the one payment he had left to make, which is the last thing that passes between them without being said.",
  "final_image": "Four days after the rite, in the forge, Orin steps behind Wenna at the anvil and shifts her grip on the haft — a correction he has not made in six years, and needs to make now because her fingers cannot find the balance — and she lets him, and goes on working."
 },
 "synopsis": {
  "s01": {
   "text": "Kettleburn has paid the Hold of Hurst in worked iron for three generations and strikes the Cold Nail into the hall's king-post each midwinter.",
   "function": "initial_situation",
   "story_time_rank": 1
  },
  "s02": {
   "text": "Wenna Cray, nineteen, apprenticed to the smith Orin Bale, spends the week before the rite truing the Nail's tang and reading quench marks.",
   "function": "initial_situation",
   "story_time_rank": 2
  },
  "s03": {
   "text": "Bale raised her from eight, taught her by letting her ruin stock, and has not corrected her grip in six years.",
   "function": "subplot",
   "story_time_rank": 3
  },
  "s04": {
   "text": "Nine days before midwinter, raiders out of Fenner's Waste take the grain and the Nail from the forge yard, in her keeping.",
   "function": "disturbance",
   "story_time_rank": 4
  },
  "s05": {
   "text": "She goes after it alone, being the only one who can identify it by grain and weight.",
   "function": "goal",
   "story_time_rank": 5
  },
  "s06": {
   "text": "Unstruck, the ward that holds the snowpack stops, and the Hold re-assesses unwarded ground at a levy per head payable in people.",
   "function": "stakes",
   "story_time_rank": 6
  },
  "s07": {
   "text": "Orin refuses to let the forge's finished stock go as ransom, leaving her nothing to buy the Nail back with.",
   "function": "obstacle",
   "story_time_rank": 7
  },
  "s08": {
   "text": "Four days out on six-hour daylight and charcoal she cannot spare, to the slate quarry above Fenner's Waste.",
   "function": "obstacle",
   "story_time_rank": 8
  },
  "s09": {
   "text": "The raiders are Sarn Dree and forty people from a village the Hold un-warded eleven years ago for arrears.",
   "function": "obstacle",
   "story_time_rank": 9
  },
  "s10": {
   "text": "Sarn will sell it back for iron she was forbidden to bring, so she waits two nights and steals it.",
   "function": "obstacle",
   "story_time_rank": 10
  },
  "s11": {
   "text": "Tibb Dree, fifteen, catches her at the tally-shed door, and she kills him with a hammer at arm's length.",
   "function": "cost",
   "story_time_rank": 11
  },
  "s12": {
   "text": "Reading the Nail by firelight two nights later, she finds no live-quench grain at the tang and scale colour forty years too young.",
   "function": "turn",
   "story_time_rank": 12
  },
  "s13": {
   "text": "It is a forgery in Orin Bale's hand, and she has killed a boy for iron that never held anything.",
   "function": "turn",
   "story_time_rank": 13
  },
  "s14": {
   "text": "Orin's reason is his own: the true Nail cracked forty years ago, a quench was owed, and the payer's lot fell on his eleven-year-old sister.",
   "function": "turn",
   "story_time_rank": 14
  },
  "s15": {
   "text": "It was defensible in its year, and it has taken forty years of tithe for a ward that did not exist.",
   "function": "theme",
   "story_time_rank": 15
  },
  "s16": {
   "text": "He has been folding stock since autumn to make a true Nail and pay the quench himself, which at seventy would kill him.",
   "function": "turn",
   "story_time_rank": 16
  },
  "s17": {
   "text": "Wenna takes the work off him, draws his stock down over two days, and quenches the nail against her own hands.",
   "function": "climax",
   "story_time_rank": 17
  },
  "s18": {
   "text": "At the rite the factor weighs it on Bale's beam scale against a figure entered forty years ago, and the beam will not sit.",
   "function": "climax",
   "story_time_rank": 18
  },
  "s19": {
   "text": "She does not denounce Orin; she says the nail is two ounces heavy, that she made it, and asks what the correction costs.",
   "function": "climax",
   "story_time_rank": 19
  },
  "s20": {
   "text": "The factor enters the wrong weight against a tithe raised a fifth for nine years, and she signs for the village without asking it.",
   "function": "resolution",
   "story_time_rank": 20
  },
  "s21": {
   "text": "The nail goes into the king-post, the ward is real for the first time in forty years, and nobody knows either fact.",
   "function": "resolution",
   "story_time_rank": 21
  },
  "s22": {
   "text": "She will not be warm again, will not run a fever, and cannot feel a piece's grain as she could at nineteen.",
   "function": "cost",
   "story_time_rank": 22
  },
  "s23": {
   "text": "Kettleburn thanks nobody for a raised tithe, Sarn has a dead nephew and no iron, and Wenna can explain neither without giving Orin up.",
   "function": "cost",
   "story_time_rank": 23
  },
  "s24": {
   "text": "Orin, who wanted to pay and was not allowed to, keeps the shop with her, and neither speaks of it.",
   "function": "subplot",
   "story_time_rank": 24
  },
  "s25": {
   "text": "Four days after the rite Orin steps behind her at the anvil and shifts her grip on the haft, and she lets him.",
   "function": "resolution",
   "story_time_rank": 25
  }
 },
 "synopsis_word_count": 540,
 "jacket_copy": "Kettleburn is sixty-one people, one forge, and a pass that closes for four months. Three generations have paid the Hold of Hurst in worked iron, and every midwinter the village strikes the Cold Nail into the hall's king-post so the snow above it keeps its place. Nine days before the rite, raiders out of Fenner's Waste take the winter grain and the Nail out of the forge yard. Wenna Cray is nineteen, eight years at Orin Bale's anvil, and the only person who can tell that piece of iron from any other by its grain. She goes up the mountain after it with six hours of daylight a day and charcoal she cannot spare. She brings it back. Then she reads the quench marks by firelight, and the arithmetic of forty years stops adding up."
}

WHAT TO PRODUCE

Exactly 2 plots. A plot is defined operationally and narrowly:

    a chain of cause and effect in which an agent pursues an outcome against
    resistance, and which terminates in success, failure, or transformation of
    the goal.

It is not a theme, not a mood, not a character. Classify each into one of:
external_main, relationship, growth_internal, antagonist, investigation, intrigue, survival, institutional, epochal, thematic, rivalry, mentor, descent_tragic, frame_recursive.

For each plot:

- `agent` and `resistance` name entity ids. You are forward-declaring the cast
  here — the next stage writes dossiers for exactly these ids, so choose them
  deliberately and keep the numbering tight (ch-01, ch-02, ...). Resistance may
  also name another plot, when what obstructs this goal is the pursuit of that
  one.
- `spine`: the ordered steps of the chain, keyed st1, st2, st3, ... Each step
  gets a `function` (a dramaturgical label such as state_of_rupture,
  forced_proximity, point_of_no_return, false_victory) and an `intent` of one
  or two sentences saying what must happen there. Do not name events yet; the
  event layer binds itself to these steps.
- `because`: this is what separates a woven story from a braided one. When a
  step of this plot is caused by a step of another, record it as "pl-01:st3".
  Subplots that run in parallel and never touch are the standard failure of
  machine-made fiction; at least one cross-plot `because` is required, and the
  two plots must genuinely constrain each other — competing for the same agent,
  the same hour, the same resource.
- `covers_synopsis`: the synopsis sentence keys this plot is answerable for.
  Between them, the plots must cover every sentence of the synopsis.
- `outcome` and `resolution_step`: how and where it ends. Not every plot may
  succeed.

SCHEMA (your output must validate against this):
{
 "type": "object",
 "properties": {
  "plots": {
   "type": "array",
   "items": {
    "type": "object",
    "properties": {
     "plot_id": {
      "type": "string",
      "description": "pl-01, pl-02, ..."
     },
     "type": {
      "enum": [
       "external_main",
       "relationship",
       "growth_internal",
       "antagonist",
       "investigation",
       "intrigue",
       "survival",
       "institutional",
       "epochal",
       "thematic",
       "rivalry",
       "mentor",
       "descent_tragic",
       "frame_recursive"
      ]
     },
     "title": {
      "type": "string"
     },
     "agent": {
      "type": "array",
      "items": {
       "type": "string"
      },
      "description": "entity ids that pursue the goal (forward-declared; L3 must define them)"
     },
     "resistance": {
      "type": "array",
      "items": {
       "type": "string"
      },
      "description": "entity ids and/or plot ids that supply resistance"
     },
     "goal": {
      "type": "string",
      "description": "a concrete outcome pursued, not a theme or a mood"
     },
     "stakes": {
      "type": "string",
      "description": "what is lost if the goal is not reached"
     },
     "outcome": {
      "enum": [
       "success",
       "partial_success",
       "failure",
       "transformation_of_goal"
      ]
     },
     "spine": {
      "type": "object",
      "additionalProperties": {
       "type": "object",
       "properties": {
        "step": {
         "type": "integer"
        },
        "function": {
         "type": "string",
         "description": "e.g. state_of_rupture, forced_proximity, point_of_no_return"
        },
        "intent": {
         "type": "string",
         "description": "what must happen at this step, 1-2 sentences"
        },
        "because": {
         "type": "array",
         "items": {
          "type": "string"
         },
         "description": "cross-plot causes, formatted 'pl-01:st3'; empty for the first step"
        }
       },
       "required": [
        "step",
        "function",
        "intent",
        "because"
       ],
       "additionalProperties": false
      },
      "description": "ordered by .step; keys st1, st2, ... Events bind to these steps later.",
      "propertyNames": {
       "pattern": "^st[0-9]{1,2}$"
      }
     },
     "resolution_step": {
      "type": "string",
      "description": "the spine key at which this plot terminates"
     },
     "thematic_function": {
      "type": "string"
     },
     "screen_time_share": {
      "type": "number",
      "minimum": 0,
      "maximum": 1
     },
     "interference": {
      "type": "array",
      "items": {
       "type": "object",
       "properties": {
        "with": {
         "type": "string"
        },
        "kind": {
         "type": "string"
        }
       },
       "required": [
        "with",
        "kind"
       ],
       "additionalProperties": false
      },
      "description": "how this plot competes with another for the agent, the clock, or the reader"
     },
     "covers_synopsis": {
      "type": "array",
      "items": {
       "type": "string"
      },
      "description": "synopsis sentence keys this plot is responsible for"
     }
    },
    "required": [
     "plot_id",
     "type",
     "title",
     "agent",
     "resistance",
     "goal",
     "stakes",
     "outcome",
     "spine",
     "resolution_step",
     "thematic_function",
     "screen_time_share",
     "interference",
     "covers_synopsis"
    ],
    "additionalProperties": false
   },
   "minItems": 1
  }
 },
 "required": [
  "plots"
 ],
 "additionalProperties": false,
 "description": "L4. Nothing floats: a candidate without goal + resistance + outcome is a motif, not a plot."
}

