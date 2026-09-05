# Top-down pilot traces — two worked examples

*Seed film for both: Shakespeare in Love (slug `awesomefilm__04385ea70696`).*
*Same step (T1/meta-themes), same composer (muse-spark-1.3), same 3 judges.*
*The only difference: Example A was built in one call (reasoning+artifact together),*
*Example B in two calls (deliberate first, build second).*

## Predecessor (the given story root, excerpt)

Film: **Shakespeare in Love**. The chain starts from this root; the meta-themes trace must derive from it:

```json
{
 "logline": "A blocked young playwright who has sold an unwritten comedy to a debt-ridden theatre must find his muse before opening in three weeks, but when the boy actor he chases for his Romeo is revealed as a noblewoman betrothed to a lord, their secret love rewrites his comedy into tragedy at the risk of law, debt and the Queen's command.",
 "premise": "In plague-closed London 1593 Will Shakespeare has sold Henslowe at the Rose an unwritten comedy 'Romeo and Ethel the Pirate's Daughter' to cover twelve pounds debt to moneylender Fennyman, claiming it is locked in his head (sc-005) while his gift has dried up (sc-007). When the Master of the Revels reopens the theatres (sc-019) he must deliver in three weeks. After burning his Romeo and Rosaline draft when he finds Rosaline with Tilney (sc-024) he hears a hatted youth calling himself Thomas Kent speak his Silvia verse (sc-030) and chases him by river taxi to the De Lesseps jetty (sc-033) where Thomas is revealed as Viola De Lesseps, a well-born lady who vows to have poetry and overwhelming love (sc-018) but is bought for Lord Wessex with the Queen's consent (sc-050). Viola binds her chest and buys a boy's wig (sc-039) to rehearse as Romeo, Will and Viola consummate in her bedroom while the Nurse masks the sound (sc-061), and their nights together are cross-cut with torchlit rehearsal as the same balcony verse is written in bed and spoken on stage (sc-086-088). The affair forces the play from comedy to tragedy (sc-099), t
```

## Example A — single call, 3.73 FAIL

tid `awesomefilm__04385ea70696::topdown::meta::themes` — gen 24.9s, 4469 tokens out

### Reasoning

Considered floskel candidates like love vs duty, art vs commerce, truth vs censorship in abstract form; rejected because they name no concrete situation later events must show. Considered closing the dilemma toward tragedy vindicated or love sacrificed; rejected because commit-late requires open alternatives. Layer above forces: dried-up gift and unwritten comedy sold for debt, Viola's vow vs purchased Wessex marriage with Queen's consent, bedroom verse tested on stage, comedy forced to tragedy, double-sale brawl, Tilney closure for woman on stage, Sam losing voice and Curtain gamble, Queen sustaining Master Kent fiction, and Twelfth Night transmutation. Built dilemma and questions only from those forced situations with sc-anchors and no new proper nouns.

### Target node (artifact)

```json
{
 "big_questions": [
  "Can verse show the very truth and nature of love for fifty pounds before the Queen (sc-103) when balcony lines written in bed between kisses must be tested on torchlit rehearsal and hold the house silent at the tomb (sc-086, sc-088, sc-172)?",
  "Must Viola's vow to have poetry and overwhelming love (sc-018) yield to a purchased marriage to Wessex with the Queen's consent (sc-050) and to Tilney's ban on displaying a woman enforced by closure of the Rose (sc-127, sc-128)?",
  "Can a dried-up gift (sc-007) claimed as locked in the head (sc-005) be cured by lived love rather than Dr Moth's charm (sc-008) while twelve-pound torture-debt to Fennyman (sc-002) and double-sale of the same Romeo to Henslowe and Burbage (sc-107) force a three-week opening (ev-015)?"
 ],
 "central_dilemma": {
  "dilemma": "Whether Will and Viola turn secret nights together into a tragedy that shows love's truth (sc-061, sc-099) at risk of law, debt and marriage, or survive by obedience to rank, company property and the Master of the Revels (sc-019, sc-107, sc-127)?",
  "pole_a": "Risk everything for lived love: consummate in the bedroom while the Nurse masks sound (sc-061), rewrite comedy to tragedy (sc-099), let Viola step on as Juliet when Sam loses his voice (sc-155) and gamble on the Curtain (sc-143) even if Tilney closes the Rose (sc-128).",
  "pole_b": "Yield to survival: deliver the unwritten comedy sold to Henslowe at the Rose to cover debt to Fennyman (sc-002, sc-005), accept Wessex's Queen-commanded marriage (sc-050), and obey plague closure and the ban on women on stage (sc-019, sc-127).",
  "stakes": "Whether the Queen sustains the Master Kent fiction to pardon imprisonment and let the play hold the house silent (sc-184, sc-172), or rank, law and debt close the playhouse, and love survives only transmuted into Twelfth Night for a shipwrecked Viola (sc-189, sc-192)."
 }
}
```

### Judgement (3 blind judges, D1-D5)

|  | D1 plausible | D2 grounded | D3 coherent | D4 genuine derivation | D5 coverage |
|---|---|---|---|---|---|
| judge1 | 3 | 4 | 4 | 2 | 3 |
| judge2 | 4 | 5 | 5 | 3 | 4 |
| judge3 | 4 | 4 | 4 | 3 | 4 |
| **mean** | **3.67** | **4.33** | **4.33** | **2.67** | **3.67** |

**Overall 3.73 — FAIL**

## Example B — two calls, 5.0 PASS

tid `awesomefilm__04385ea70696::topdown::meta::themes` — gen 57.8s, ? tokens out

### Reasoning

Candidate Direction A — lived truth of love versus survival inside rank, law and debt: abstract claims about truth would have to be shown through bedroom consummation masked by the Nurse (sc-061) becoming balcony verse written in bed and spoken on stage in cross-cut (sc-086-088), about love would have to be shown through Viola's vow to have poetry and overwhelming love (sc-018) colliding with purchase for Lord Wessex with the Queen's consent (sc-050), about risk would have to be shown through turn from comedy to tragedy (sc-099), double-sale raid (sc-109), closure for displaying a woman (sc-128), stepping on as Juliet when Sam loses voice (sc-155) holding the house silent through deaths (sc-172), and pardon only because the Queen sustains the Master Kent fiction (sc-184) leading to Twelfth Night for a shipwrecked Viola (sc-189).

Candidate Direction B — debt-commerce lie manufacture versus poetry inspiration: abstract claims about commerce would have to be shown through torture-debt with boots on fire over twelve pounds (sc-002) and seizure (sc-019), claiming unwritten play locked in head (sc-005) while gift dried up (sc-007), haggling unwritten Romeo between Henslowe and Burbage (sc-009), hard three-week deadline to open (ev-015), fifty pounds wager on showing truth of love (sc-103), Fennyman terrified as Apothecary for forty ducats (sc-168), Curtain cannon flag and packed auditorium (sc-143). Abstract claims about inspiration would have to be shown through burning Romeo and Rosaline draft on finding Rosaline with Tilney (sc-024).

Candidate Direction C — self revealed through forbidden performance versus self confined to assigned rank role: abstract claims about identity would have to be shown through hatted youth calling himself Thomas Kent speaking Silvia verse (sc-030), chase by river taxi to De Lesseps jetty (sc-033), binding chest and buying boy's wig (sc-039) to rehearse as Romeo, violation triggering Tilney closure and arrest by pikemen (sc-127, sc-128, sc-183), stepping on as Juliet (sc-155) and pardon via sustained Kent fiction (sc-184).

Rejection of B: fails evidence in layers above because logline frames blocked playwright finding muse where boy actor revealed as betrothed noblewoman rewrites comedy into tragedy at risk of law, debt and Queen's command — debt is listed as one risk among three, not the engine; premise engine is Viola's vow (sc-018) plus bedroom-stage cross-cut (sc-086-088) plus affair forcing comedy to tragedy (sc-099); narrative_vector conflict lists four pressures where Henslowe torture-debt (sc-002) sits alongside ban on women enforced by Tilney (sc-127), purchased Queen-commanded marriage (sc-050), and rival claim (sc-107) — B would force layers below to show only debt/commerce and drop the marriage ban; audience romance promise requires balcony lines born in whispers tested on stage (sc-076, sc-086) and silent tomb (sc-172) which B cannot deliver; POV requires intimate cross-cutting between bedroom and stage letting life become verse in real time which B replaces with counting-house view; generative question asks can a play show very truth and nature of love for fifty pounds before the Queen (sc-103) or must love yield to rank, law and survival — B keeps fifty pounds but loses truth-of-love test.

Rejection of C: fails evidence because while Thomas Kent reveal and binding/wig (sc-039) and stepping on (sc-155) are load-bearing, premise and rules make performance inseparable from debt enforcement physically (sc-002, sc-019), company property double-sale provoking raid and brawl (sc-107, sc-109), and Queen as supreme arbiter overruling Tilney (sc-184); genre_secondary is Backstage Theatre Farce alongside Historical Romantic Comedy-Drama, and theatre-history audience promise requires debt farce plus boy players losing voice (sc-154) plus Fennyman as Apothecary (sc-168) plus Curtain vindication — C would force layers below to show disguise without forcing debt farce; style pairs farcical debt and company brawls against un-bombastic tragic performance, so C alone breaks that pairing; narrative_vector goal requires delivering true play before law, debt and marriage close the playhouse, not only before identity is exposed.

Decision retained: Direction A integrated truth-through-lived-love versus yielding to rank-law-debt-commerce system, because only it compels layers below to show all four conflict pressures together, both audience promises together, POV cross-cut together, and generative question in full.

Near-miss is Direction B, closest to winning because debt farce is structurally load-bearing via rules of physical enforcement and company property, via hard three-week deadline, via fifty pounds wager (sc-103) which explicitly prices truth, and via secondary genre and second audience group. Flip condition: choice would flip to B if layers above foregrounded Henslowe torture and double-sale to Burbage and Fennyman Apothecary as the resolving proof, and downgraded Viola's vow (sc-018), bedroom consummation (sc-061), bedroom-stage cross-cut (sc-086-088), comedy-to-tragedy rewrite (sc-099), purchased marriage with Queen's consent (sc-050), stepping on as Juliet (sc-155), silent tomb (sc-172), and Queen sustaining Kent fiction (sc-184) from premise drivers to background color, or if POV were not bedroom-stage transmutation and generative question asked only about solvency before closure.

Decision plus concrete anchors next step must honour: any central dilemma must oppose showing very truth and nature of love priced at fifty pounds (sc-103) and proved by silent house at deaths (sc-172) against yielding to purchased marriage with Queen's consent (sc-050), ban on displaying female enforced by closure and pikemen (sc-127, sc-128, sc-183), debt torture and seizure (sc-002, sc-019), and double-sale raid over company property (sc-107, sc-109); any big questions must each name later situations to be shown — dried gift (sc-007) cured only by lived love not charm, vow (sc-018) tested by bedroom (sc-061) and cross-cut (sc-086-088), burned draft (sc-024) and tragedy turn (sc-099), youth speaking verse (sc-030) plus binding/wig (sc-039) leading to stepping on (sc-155), closure (sc-128) and pardon via Kent fiction (sc-184), and transmutation into Twelfth Night shipwreck survival (sc-189, sc-192) — with Master of Revels authority and Queen supremacy and three-week deadline as non-negotiable constraints.

### Target node (artifact)

```json
{
 "central_dilemma": {
  "dilemma": "Can a play show the very truth and nature of love for fifty pounds before the Queen [generative_question, sc-103] or must love yield to rank, law and survival [narrative_vector.goal]?",
  "truth_pole": "Show truth through lived love: Viola's vow to have poetry and overwhelming love [sc-018, narrative_vector.motivation, premise] made flesh in bedroom consummation masked by the Nurse [sc-061] and cross-cut as the same balcony verse written in bed and spoken on stage [sc-086-088, sc-076, pov, style], forcing the play from comedy to tragedy [sc-099, premise] after burning the Romeo and Rosaline draft [sc-024], proved when Viola steps on as Juliet when Sam loses voice [sc-155, sc-154] and holds the packed house silent through the deaths [sc-172, audiences romance_promise, narrative_vector.goal]",
  "survival_pole": "Yield to the rank-law-debt-commerce system to survive: purchased marriage to Lord Wessex with the Queen's consent [sc-050, narrative_vector.conflict, logline], ban on displaying a female enforced by Tilney closure and arrest by pikemen in the Queen's name [sc-127, sc-128, sc-183, rules_of_the_world], debt torture with boots on fire over twelve pounds and seizure [sc-002, sc-019, rules_of_the_world, narrative_vector.conflict], double-sale of the same Romeo to Henslowe and Burbage provoking raid and real brawl over company property [sc-107, sc-109, sc-009, rules_of_the_world], under Master of the Revels authority and hard three-week deadline to open [ev-015, sc-019, rules_of_the_world] with the Queen as supreme arbiter who alone can sustain the Master Kent fiction to pardon imprisonment [sc-184, rules_of_the_world]"
 },
 "big_questions": [
  "Can a dried-up gift [sc-007, narrative_vector.motivation, premise] be cured only by lived love and writing, not by Dr Moth's love charm and snake bracelet [sc-007, sc-008, forbidden_tics], when Will burns his Romeo and Rosaline draft on finding Rosaline with Tilney [sc-024, premise] and only recovers verse when bedroom consummation masked by the Nurse [sc-061] becomes balcony verse written in bed and spoken torchlit on stage in cross-cut [sc-086-088, sc-076, pov, style] forcing comedy to tragedy [sc-099, logline]?",
  "Can Viola's vow to have poetry and overwhelming love [sc-018, narrative_vector.motivation, audiences romance_promise] survive her purchase for Lord Wessex with the Queen's consent [sc-050, narrative_vector.conflict], when the hatted youth calling himself Thomas Kent speaking Silvia verse [sc-030, premise] chased by river taxi to De Lesseps jetty [sc-033] binds her chest and buys a boy's wig [sc-039, premise] to rehearse as Romeo and must finally step on as Juliet when Sam loses his voice [sc-155, sc-154, premise]?",
  "Can showing the very truth and nature of love priced at fifty pounds [sc-103, generative_question, narrative_vector.goal] and proved by holding the house silent through the deaths [sc-172] survive law and commerce, when violation of the ban on women triggers Tilney closure [sc-127, sc-128, rules_of_the_world] and arrest by pikemen [sc-183], debt torture and seizure [sc-002, sc-019, rules_of_the_world] plus double-sale raid and brawl [sc-107, sc-109] threaten the company under a hard three-week deadline [ev-015] and Master of the Revels authority, requiring pardon only because the Queen sustains the Master Kent fiction as supreme patron and arbiter [sc-184, rules_of_the_world, audiences backstage_promise, genre_secondary]?",
  "If love must yield to rank, law and survival, can lived love still be transmuted into language that outlives separation [narrative_vector.motivation, style], when after closure [sc-128], stepping on [sc-155], silent tomb [sc-172] and pardon via Kent fiction [sc-184] Will begins Twelfth Night for a shipwrecked Viola [sc-189, premise] where Viola survives shipwreck [sc-192, audiences romance_promise] under Queen supremacy and Master of Revels order?"
 ]
}
```

### Judgement (3 blind judges, D1-D5)

|  | D1 plausible | D2 grounded | D3 coherent | D4 genuine derivation | D5 coverage |
|---|---|---|---|---|---|
| judge1 | 5 | 5 | 5 | 5 | 5 |
| judge2 | 5 | 5 | 5 | 5 | 5 |
| judge3 | 5 | 5 | 5 | 5 | 5 |
| **mean** | **5.0** | **5.0** | **5.0** | **5.0** | **5.0** |

**Overall 5.00 — PASS**

---
*Generated 2026-09-05 via reasoning_traces/topdown_generate.py + topdown_judge.py.*
