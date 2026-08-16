# Missing Hours

*A calculating player enters a hyper-realistic 1984 Vermont battle royale to solve its hidden ritual and win a life-changing prize, treating every host as a renewable resource — until the missing hours start to stick.*

`science_fiction` · screenplay · adult · pov third_limited, present

## Shape

| layer | count |
|---|---|
| L4 plots | 3 |
| L3 entities | 33 |
| L5 events | 17 |
| L6 scenes | 17 |
| beats | 72 |
| patch ops | 160 |
| prose leaves | 4 |
| prose words | 2,880 |

Entities by type: character 9, concept 4, group 4, location 8, object 8

## Plots

### pl-01 — The Dawn Site

- **type** `external_main` · **outcome** `transformation_of_goal` · share 0.42
- **goal** Locate every Daywalker token and speak the dawn invocation at the one fixed site, ending the match in his favor and taking the single prize.
- **stakes** Unfed frenzy and elimination; a rival completing first; remaining trapped in the underclass that bought him the ticket.
- **agent** ['ch-01'] vs **resistance** ['ch-02', 'ch-03', 'ch-04', 'ch-05', 'ch-06', 'ch-07', 'ch-08', 'ch-09', 'pl-02', 'pl-03']
- **events** 8 owned, 8 served

| step | function | events | because |
|---|---|---|---|
| st1 | competent_entry | ev-001 | — |
| st2 | goal_lock | ev-003 | — |
| st3 | world_state_squeeze | ev-005 | — |
| st4 | forced_dependency | ev-008 | pl-02:st4 |
| st5 | resource_hardening | ev-010 | pl-02:st5 |
| st6 | rule_reversal | ev-014 | pl-02:st4 |
| st7 | ticking_choice | ev-015 | pl-02:st8 |
| st8 | withheld_invocation | ev-016 | pl-03:st5, pl-02:st8 |

### pl-02 — The Kept Hours

- **type** `investigation` · **outcome** `partial_success` · share 0.33
- **goal** Rebuild the missing hours from Polaroids and cassette until she holds a continuous night she can keep, and stop being emptied.
- **stakes** Sliding back into a wipe with no ballast; existential collapse if the evidence forces a simulation-belief without analog cover; remaining a renewable throat while the road out of town still loops.
- **agent** ['ch-02'] vs **resistance** ['ch-01', 'ch-03', 'pl-01']
- **events** 8 owned, 9 served

| step | function | events | because |
|---|---|---|---|
| st1 | ordinary_want | ev-002 | — |
| st2 | unseen_conjunction | ev-004 | pl-01:st1 |
| st3 | state_of_rupture | ev-006 | pl-01:st1 |
| st4 | inquiry | ev-007 | — |
| st5 | uncanny_recognition | ev-009 | pl-01:st4 |
| st6 | proof_as_weapon | ev-011 | — |
| st7 | experiment_backfire | ev-013 | pl-01:st5 |
| st8 | armed_vigil | ev-015 | pl-01:st6 |
| st9 | seized_continuity | ev-017 | pl-01:st8 |

### pl-03 — The Unremembered Customer

- **type** `growth_internal` · **outcome** `failure` · share 0.25
- **goal** Leave the match unmarked: take the prize, remain the customer no Host can place, and keep treating nights as inventory.
- **stakes** If the mask holds he takes the prize and cancels her kept hours with the match-end wipe; if it fails he loses the prize, his cover, a hand that will not regenerate, and the last self that could feed clean and walk away.
- **agent** ['ch-01'] vs **resistance** ['pl-01', 'ch-02']
- **events** 1 owned, 7 served

| step | function | events | because |
|---|---|---|---|
| st1 | mask_as_method | ev-001 | pl-01:st1 |
| st2 | first_leak | ev-009 | pl-02:st5 |
| st3 | divided_will | ev-012 | pl-02:st6 |
| st4 | moral_inversion | ev-014 | pl-01:st6 |
| st5 | want_versus_need | ev-015 | pl-02:st8 |
| st6 | irreversible_cost | ev-016 | pl-01:st8 |

## Story tree (primary edges)

Each scene has exactly one parent event; each event exactly one parent plot.
Secondary memberships are shown in brackets.

- **pl-01** The Dawn Site
  - `ev-001` t2 — Hale maps closed Bennington and feeds three Hosts short of death, paying and tipping to lock a clean rotation.  _[also pl-03]_
    - `sc-001` d1 Competent entry: map the town, lock a clean three-Host rotation, and show manners as method.
  - `ev-003` t6 — Hale isolates the Daywalker Ritual as a finite set of locatable tokens and one dawn invocation at one fixed stone.
    - `sc-003` d3 Goal lock: reduce the match to locatable tokens and one dawn stone.
  - `ev-005` t10 — Rivals rewrite the town as UV cages, dry wards, a college cult, and a heartless body, while the rotation Hosts regain color.
    - `sc-005` d5 World-state squeeze: register five rivals only as weather that closes streets, wards, and easy blood.
  - `ev-008` t16 — Hale reads Ritual residue in Cora's stack, lifts two tokens, and pockets one print because every other decode is now closed.
    - `sc-008` d8 Forced dependency: spend her archive as the last decode and lift two tokens the long way around the lights.
  - `ev-010` t20 — The diner locks after dark, Denise refuses Hale's eye, and Main Street tightens into a UV corridor; the rotation dies.
    - `sc-010` d10 Resource hardening: the diner locks, the nurse refuses, the UV corridor closes, and the clean rotation dies.
  - `ev-014` t28 — Hale lifts the last token at Founders' Stone and understands that speaking the invocation would wipe every kept hour.  _[also pl-03]_
    - `sc-014` d14 Rule reversal: he lifts the last token at the stone and holds, in the same hand, the knowledge that speaking the words would wipe every kept hour.
  - `ev-015` t30 — Two hours before dawn Cora waits at the stone with a live UV lamp; Hale holds every token and takes the cassette.  _[also pl-02, pl-03]_
    - `sc-015` d15 Ticking choice: two hours to dawn, she waits with a live lamp, he holds every token and takes the cassette, and neither steps forward.
  - `ev-016` t32 — Hale withholds the invocation, gives Cora the tokens and cassette, and takes a sun-scorch that will not regenerate.  _[also pl-03]_
    - `sc-016` d16 Withheld invocation: he gives her the tokens and the cassette, takes a sun-scorch that will not regenerate, and remains the face in a stack the wipe cannot cancel.
- **pl-02** The Kept Hours
  - `ev-002` t4 — Cora photographs the empty diner and the careful customer, and records the last radio song to prove the town was real.
    - `sc-002` d2 Plant the unremarked face and the analog archive as her ticket-out proof, not as a case.
  - `ev-004` t8 — Anja stacks hypnotic writes on the same three Hosts Hale is draining, testing whether a lie can survive a sleep.
    - `sc-004` d4 Unseen conjunction: stack hypnotic writes on the same three Hosts already in Hale's margin.
  - `ev-006` t12 — After a third careful feed Cora wakes holding scraps of the night and finds Polaroids she does not remember taking.
    - `sc-006` d6 State of rupture: the third drain plus the stacked writes tear the wipe and hand her a night she did not keep.
  - `ev-007` t14 — Cora records the missing hours, matches her bruise to Denise, and the stack begins catching Ritual residue.
    - `sc-007` d7 Inquiry: turn scraps into a case, match a bruise, and catch ritual residue the wipe cannot take.
  - `ev-009` t18 — Cora flinches at Hale's face and pours anyway; he returns the Polaroid he should have kept.  _[also pl-03]_
    - `sc-009` d9 First leak: she flinches and pours; he returns the print he should have kept and misses the feed.
  - `ev-011` t22 — In the empty diner Cora plays the cassette; Hale's own calm feed instructions are on the tape.  _[also pl-03]_
    - `sc-011` d11 Proof as weapon: she plays his calm feed instructions back at him and the unremembered customer acquires a voice that survives sleep.
  - `ev-013` t26 — Anja sees Hosts comparing notes she did not implant and stacks one more write; the extra write multiplies the fragments.
    - `sc-013` d13 Experiment backfire: Anja treats public comparison as contamination and stacks one more write, which only multiplies the fragments walking around town.
  - `ev-017` t34 — Cora hides the tokens, clips Hale's still-developing face beside the tip jar, and keeps the hours the wipe cannot cancel.
    - `sc-017` d17 Seized continuity: she hides the tokens, clips his still-developing face beside the tip jar, and keeps the hours the wipe cannot cancel.
- **pl-03** The Unremembered Customer
  - `ev-012` t24 — Hale starts a hypnotic overwrite that would take the last token cold, then stops mid-gesture.
    - `sc-012` d12 Divided will: he starts the overwrite that would take the last token cold, then stops mid-gesture because another write would burn the archive.

## State trajectories

### ch-01 — Hale

| where | event | variable | before | after | dim | mag |
|---|---|---|---|---|---|---|
| sc-001#b4 | ev-001 | `cash` | `100` | `74` | material | 25 |
| sc-001#b4 | ev-001 | `position` | `lo-01` | `lo-02` | spatial | 20 |
| sc-001#b5 | ev-001 | `hunger` | `35` | `12` | physiological | 55 |
| sc-001#b6 | ev-001 | `detachment` | `92` | `90` | psychological | 8 |
| sc-003#b1 | ev-003 | `position` | `lo-02` | `lo-01` | spatial | 15 |
| sc-003#b3 | ev-003 | `hunger` | `12` | `26` | physiological | 25 |
| sc-005#b5 | ev-005 | `hunger` | `26` | `41` | physiological | 30 |
| sc-006#b1 | ev-006 | `hunger` | `41` | `19` | physiological | 45 |
| sc-006#b1 | ev-006 | `position` | `lo-01` | `lo-02` | spatial | 15 |
| sc-008#b3 | ev-008 | `tokens_held` | `0` | `2` | material | 55 |
| sc-008#b3 | ev-008 | `hunger` | `19` | `45` | physiological | 40 |
| sc-008#b4 | ev-008 | `detachment` | `90` | `83` | psychological | 25 |
| sc-009#b3 | ev-009 | `cash` | `74` | `69` | material | 10 |
| sc-009#b4 | ev-009 | `cover` | `unremembered` | `leaking` | social | 60 |
| sc-009#b4 | ev-009 | `detachment` | `83` | `71` | psychological | 40 |
| sc-009#b5 | ev-009 | `hunger` | `45` | `53` | physiological | 20 |
| sc-010#b1 | ev-010 | `position` | `lo-02` | `lo-01` | spatial | 15 |
| sc-010#b5 | ev-010 | `hunger` | `53` | `67` | physiological | 35 |
| sc-010#b5 | ev-010 | `detachment` | `71` | `65` | psychological | 20 |
| sc-011#b1 | ev-011 | `position` | `lo-01` | `lo-02` | spatial | 15 |
| sc-011#b4 | ev-011 | `cover` | `leaking` | `named` | social | 70 |
| sc-011#b4 | ev-011 | `detachment` | `65` | `52` | psychological | 40 |
| sc-012#b2 | ev-012 | `detachment` | `52` | `34` | psychological | 55 |
| sc-012#b4 | ev-012 | `hunger` | `67` | `75` | physiological | 20 |
| sc-014#b1 | ev-014 | `position` | `lo-02` | `lo-06` | spatial | 30 |
| sc-014#b2 | ev-014 | `tokens_held` | `2` | `4` | material | 70 |
| sc-014#b3 | ev-014 | `detachment` | `34` | `22` | psychological | 40 |
| sc-014#b4 | ev-014 | `hunger` | `75` | `83` | physiological | 20 |
| sc-015#b4 | ev-015 | `hunger` | `83` | `91` | physiological | 35 |
| sc-015#b4 | ev-015 | `detachment` | `22` | `14` | psychological | 30 |
| sc-016#b1 | ev-016 | `tokens_held` | `4` | `0` | material | 80 |
| sc-016#b1 | ev-016 | `prize_claim` | `pursuing` | `forfeit` | world | 95 |
| sc-016#b2 | ev-016 | `sun_injury` | `none` | `hand_scorch` | physiological | 90 |
| sc-016#b2 | ev-016 | `hunger` | `91` | `97` | physiological | 25 |
| sc-016#b4 | ev-016 | `cover` | `named` | `archived` | social | 75 |
| sc-016#b4 | ev-016 | `detachment` | `14` | `6` | psychological | 50 |

### ch-02 — Cora Voss

| where | event | variable | before | after | dim | mag |
|---|---|---|---|---|---|---|
| sc-001#b5 | ev-001 | `blood_level` | `100` | `60` | physiological | 50 |
| sc-002#b4 | ev-002 | `archive_depth` | `6` | `8` | material | 20 |
| sc-005#b5 | ev-005 | `blood_level` | `60` | `88` | physiological | 35 |
| sc-006#b1 | ev-006 | `blood_level` | `88` | `54` | physiological | 45 |
| sc-006#b3 | ev-006 | `retained_night` | `0` | `24` | epistemic | 70 |
| sc-006#b3 | ev-006 | `existential_stability` | `88` | `76` | psychological | 35 |
| sc-006#b4 | ev-006 | `archive_depth` | `8` | `12` | material | 30 |
| sc-007#b1 | ev-007 | `retained_night` | `24` | `44` | epistemic | 40 |
| sc-007#b3 | ev-007 | `archive_depth` | `12` | `18` | material | 40 |
| sc-007#b4 | ev-007 | `existential_stability` | `76` | `67` | psychological | 25 |
| sc-009#b1 | ev-009 | `stance_on_hale` | `customer` | `flinch` | emotional | 55 |
| sc-009#b4 | ev-009 | `archive_depth` | `18` | `19` | material | 20 |
| sc-010#b5 | ev-010 | `blood_level` | `54` | `70` | physiological | 20 |
| sc-011#b3 | ev-011 | `stance_on_hale` | `flinch` | `investigator` | emotional | 50 |
| sc-011#b3 | ev-011 | `retained_night` | `44` | `60` | epistemic | 35 |
| sc-011#b4 | ev-011 | `existential_stability` | `67` | `55` | psychological | 35 |
| sc-012#b3 | ev-012 | `existential_stability` | `55` | `51` | psychological | 15 |
| sc-013#b3 | ev-013 | `retained_night` | `60` | `76` | epistemic | 30 |
| sc-013#b4 | ev-013 | `existential_stability` | `51` | `40` | psychological | 30 |
| sc-015#b1 | ev-015 | `position` | `lo-02` | `lo-06` | spatial | 40 |
| sc-015#b1 | ev-015 | `stance_on_hale` | `investigator` | `armed` | emotional | 60 |
| sc-017#b1 | ev-017 | `tokens_hidden` | `False` | `True` | material | 80 |
| sc-017#b2 | ev-017 | `position` | `lo-06` | `lo-02` | spatial | 25 |
| sc-017#b2 | ev-017 | `stance_on_hale` | `armed` | `archivist` | emotional | 55 |
| sc-017#b4 | ev-017 | `retained_night` | `76` | `94` | epistemic | 40 |
| sc-017#b4 | ev-017 | `archive_depth` | `19` | `24` | material | 30 |
| sc-017#b4 | ev-017 | `existential_stability` | `40` | `54` | psychological | 35 |

### ch-03 — Anja Reeve

| where | event | variable | before | after | dim | mag |
|---|---|---|---|---|---|---|
| sc-004#b1 | ev-004 | `position` | `lo-08` | `lo-02` | spatial | 20 |
| sc-004#b1 | ev-004 | `hunger` | `30` | `36` | physiological | 10 |
| sc-004#b2 | ev-004 | `writes_on_rotation` | `0` | `3` | technological | 55 |
| sc-004#b2 | ev-004 | `experiment_phase` | `baseline` | `stacking` | epistemic | 50 |
| sc-013#b1 | ev-013 | `noticed_comparison` | `False` | `True` | epistemic | 50 |
| sc-013#b1 | ev-013 | `position` | `lo-02` | `lo-01` | spatial | 15 |
| sc-013#b2 | ev-013 | `experiment_phase` | `stacking` | `doubling_down` | epistemic | 55 |
| sc-013#b2 | ev-013 | `writes_on_rotation` | `3` | `7` | technological | 50 |
| sc-013#b4 | ev-013 | `hunger` | `36` | `48` | physiological | 20 |
| sc-017#b4 | ev-017 | `experiment_phase` | `doubling_down` | `failed` | epistemic | 50 |

### ch-04 — Kerr

| where | event | variable | before | after | dim | mag |
|---|---|---|---|---|---|---|
| sc-005#b1 | ev-005 | `uv_grid_extent` | `0` | `48` | world | 55 |
| sc-010#b4 | ev-010 | `uv_grid_extent` | `48` | `74` | world | 40 |
| sc-015#b2 | ev-015 | `uv_grid_extent` | `74` | `90` | world | 30 |

### ch-05 — Ray Holtz

| where | event | variable | before | after | dim | mag |
|---|---|---|---|---|---|---|
| sc-005#b2 | ev-005 | `blood_monopoly` | `open` | `squeezed` | world | 50 |
| sc-010#b3 | ev-010 | `blood_monopoly` | `squeezed` | `dry` | world | 50 |

### ch-06 — Nico Vale

| where | event | variable | before | after | dim | mag |
|---|---|---|---|---|---|---|
| sc-005#b3 | ev-005 | `cult_count` | `0` | `14` | social | 40 |

### ch-07 — Wynn

| where | event | variable | before | after | dim | mag |
|---|---|---|---|---|---|---|
| sc-005#b4 | ev-005 | `heart_taken` | `False` | `True` | magical | 40 |

### ch-08 — Tom Briggs

| where | event | variable | before | after | dim | mag |
|---|---|---|---|---|---|---|
| sc-001#b2 | ev-001 | `blood_level` | `100` | `63` | physiological | 45 |
| sc-001#b2 | ev-001 | `somatic_mark` | `False` | `True` | physiological | 40 |
| sc-005#b5 | ev-005 | `blood_level` | `63` | `90` | physiological | 30 |
| sc-013#b3 | ev-013 | `retained_night` | `0` | `24` | epistemic | 40 |

### ch-09 — Denise Cole

| where | event | variable | before | after | dim | mag |
|---|---|---|---|---|---|---|
| sc-001#b3 | ev-001 | `blood_level` | `100` | `65` | physiological | 45 |
| sc-001#b3 | ev-001 | `bruise_visible` | `False` | `True` | physiological | 40 |
| sc-005#b5 | ev-005 | `blood_level` | `65` | `89` | physiological | 30 |
| sc-007#b2 | ev-007 | `retained_night` | `0` | `20` | epistemic | 45 |
| sc-007#b2 | ev-007 | `avoidance_of_hale` | `neutral` | `averted` | social | 35 |
| sc-007#b2 | ev-007 | `position` | `lo-04` | `lo-02` | spatial | 20 |
| sc-010#b2 | ev-010 | `avoidance_of_hale` | `averted` | `refusing` | social | 45 |
| sc-010#b2 | ev-010 | `position` | `lo-02` | `lo-04` | spatial | 15 |
| sc-013#b3 | ev-013 | `retained_night` | `20` | `38` | epistemic | 30 |

### cn-01 — The Daywalker Ritual

| where | event | variable | before | after | dim | mag |
|---|---|---|---|---|---|---|
| sc-003#b2 | ev-003 | `decoded_by_hale` | `rumor` | `tokens_and_site` | epistemic | 70 |
| sc-014#b3 | ev-014 | `decoded_by_hale` | `tokens_and_site` | `full_cost` | epistemic | 80 |

### cn-02 — The Memory Wipe

| where | event | variable | before | after | dim | mag |
|---|---|---|---|---|---|---|
| sc-006#b5 | ev-006 | `integrity` | `intact` | `seamed` | technological | 75 |
| sc-007#b4 | ev-007 | `integrity` | `seamed` | `leaking` | technological | 50 |
| sc-013#b3 | ev-013 | `integrity` | `leaking` | `torn` | technological | 60 |

### cn-03 — The awakening glitch

| where | event | variable | before | after | dim | mag |
|---|---|---|---|---|---|---|
| sc-004#b3 | ev-004 | `phase` | `latent` | `conjunct` | technological | 60 |
| sc-006#b5 | ev-006 | `phase` | `conjunct` | `torn` | technological | 80 |
| sc-013#b3 | ev-013 | `phase` | `torn` | `spreading` | technological | 70 |

### cn-04 — Existential collapse

| where | event | variable | before | after | dim | mag |
|---|---|---|---|---|---|---|
| sc-011#b4 | ev-011 | `town_risk` | `safe` | `exposed` | psychological | 50 |
| sc-013#b4 | ev-013 | `town_risk` | `exposed` | `critical` | psychological | 55 |

### gr-02 — The rotation Hosts

| where | event | variable | before | after | dim | mag |
|---|---|---|---|---|---|---|
| sc-007#b2 | ev-007 | `comparing_notes` | `False` | `True` | social | 60 |
| sc-010#b5 | ev-010 | `rotation_viable` | `True` | `False` | world | 70 |

### gr-03 — The willing donors

| where | event | variable | before | after | dim | mag |
|---|---|---|---|---|---|---|
| sc-005#b3 | ev-005 | `formed` | `False` | `True` | social | 40 |

### gr-04 — The tribute network

| where | event | variable | before | after | dim | mag |
|---|---|---|---|---|---|---|
| sc-005#b2 | ev-005 | `active` | `False` | `True` | political | 45 |

### lo-01 — Main Street

| where | event | variable | before | after | dim | mag |
|---|---|---|---|---|---|---|
| sc-005#b1 | ev-005 | `uv_coverage` | `0` | `48` | world | 55 |
| sc-005#b1 | ev-005 | `crossing_safe_for_guests` | `True` | `False` | spatial | 60 |
| sc-010#b4 | ev-010 | `uv_coverage` | `48` | `74` | world | 40 |

### lo-02 — Al's Depot Diner

| where | event | variable | before | after | dim | mag |
|---|---|---|---|---|---|---|
| sc-010#b1 | ev-010 | `after_dark_policy` | `open` | `locked` | social | 55 |
| sc-017#b2 | ev-017 | `register_display` | `notes_only` | `hale_polaroid` | material | 65 |
| sc-017#b3 | ev-017 | `window_artifact` | `none` | `roll_bar` | technological | 40 |

### lo-03 — Briggs & Son Hardware

| where | event | variable | before | after | dim | mag |
|---|---|---|---|---|---|---|
| sc-005#b1 | ev-005 | `uv_stock` | `48` | `16` | material | 40 |

### lo-04 — Bennington Memorial

| where | event | variable | before | after | dim | mag |
|---|---|---|---|---|---|---|
| sc-005#b2 | ev-005 | `blood_stores` | `stocked` | `squeezed` | material | 50 |
| sc-005#b2 | ev-005 | `night_access` | `open_enough` | `badge_only` | social | 40 |
| sc-010#b2 | ev-010 | `night_access` | `badge_only` | `sealed` | social | 40 |
| sc-010#b3 | ev-010 | `blood_stores` | `squeezed` | `dry` | material | 50 |

### lo-05 — The Treeline Woods

| where | event | variable | before | after | dim | mag |
|---|---|---|---|---|---|---|
| sc-005#b4 | ev-005 | `body_at_treeline` | `False` | `True` | world | 45 |

### lo-06 — Founders' Stone

| where | event | variable | before | after | dim | mag |
|---|---|---|---|---|---|---|
| sc-014#b2 | ev-014 | `tokens_present` | `absent` | `with_hale` | material | 50 |
| sc-015#b2 | ev-015 | `uv_encroaching` | `False` | `True` | world | 45 |
| sc-016#b1 | ev-016 | `tokens_present` | `with_hale` | `with_cora` | material | 50 |
| sc-016#b2 | ev-016 | `sun_on_stone` | `False` | `True` | world | 60 |
| sc-017#b1 | ev-017 | `tokens_present` | `with_cora` | `hidden_nearby` | material | 70 |

### lo-07 — The Loop Road

| where | event | variable | before | after | dim | mag |
|---|---|---|---|---|---|---|
| sc-017#b3 | ev-017 | `fog_read` | `weather` | `static` | technological | 40 |

### lo-08 — Bennington College

| where | event | variable | before | after | dim | mag |
|---|---|---|---|---|---|---|
| sc-005#b3 | ev-005 | `cult_visible` | `False` | `True` | social | 35 |

### ob-01 — Cora's Polaroid camera

| where | event | variable | before | after | dim | mag |
|---|---|---|---|---|---|---|
| sc-002#b2 | ev-002 | `film_left` | `12` | `10` | material | 10 |
| sc-006#b4 | ev-006 | `film_left` | `10` | `6` | material | 15 |
| sc-007#b3 | ev-007 | `film_left` | `6` | `2` | material | 15 |
| sc-016#b3 | ev-016 | `film_left` | `2` | `1` | material | 10 |

### ob-02 — The Polaroid stack

| where | event | variable | before | after | dim | mag |
|---|---|---|---|---|---|---|
| sc-002#b2 | ev-002 | `frame_count` | `6` | `8` | material | 25 |
| sc-002#b2 | ev-002 | `content_flag` | `town_proof` | `hale_unremarked` | epistemic | 35 |
| sc-006#b4 | ev-006 | `frame_count` | `8` | `12` | material | 30 |
| sc-007#b3 | ev-007 | `frame_count` | `12` | `18` | material | 40 |
| sc-007#b3 | ev-007 | `content_flag` | `hale_unremarked` | `ritual_residue` | epistemic | 65 |
| sc-008#b4 | ev-008 | `frame_count` | `18` | `17` | material | 20 |
| sc-009#b4 | ev-009 | `frame_count` | `17` | `18` | material | 25 |
| sc-015#b3 | ev-015 | `content_flag` | `ritual_residue` | `dawn_site` | epistemic | 40 |
| sc-016#b3 | ev-016 | `frame_count` | `18` | `19` | material | 30 |
| sc-016#b3 | ev-016 | `content_flag` | `dawn_site` | `hale_face` | epistemic | 70 |

### ob-03 — The cassette of kept hours

| where | event | variable | before | after | dim | mag |
|---|---|---|---|---|---|---|
| sc-007#b1 | ev-007 | `track` | `last_song` | `missing_hours` | epistemic | 55 |
| sc-011#b2 | ev-011 | `track` | `missing_hours` | `hale_instructions` | epistemic | 75 |
| sc-015#b3 | ev-015 | `holder` | `ch-02` | `ch-01` | material | 45 |
| sc-016#b1 | ev-016 | `holder` | `ch-01` | `ch-02` | material | 40 |
| sc-017#b3 | ev-017 | `track` | `hale_instructions` | `leader_hiss` | epistemic | 35 |

### ob-04 — The Daywalker tokens

| where | event | variable | before | after | dim | mag |
|---|---|---|---|---|---|---|
| sc-008#b3 | ev-008 | `assembled` | `0` | `2` | material | 55 |
| sc-008#b3 | ev-008 | `holder` | `scattered` | `ch-01` | material | 50 |
| sc-014#b2 | ev-014 | `assembled` | `2` | `4` | material | 70 |
| sc-016#b1 | ev-016 | `holder` | `ch-01` | `ch-02` | material | 70 |
| sc-017#b1 | ev-017 | `holder` | `ch-02` | `hidden` | material | 75 |

### ob-05 — Portable UV lamp

| where | event | variable | before | after | dim | mag |
|---|---|---|---|---|---|---|
| sc-015#b1 | ev-015 | `holder` | `lo-03` | `ch-02` | material | 50 |
| sc-015#b2 | ev-015 | `powered` | `False` | `True` | technological | 55 |

### ob-06 — Hardware invoice for UV tubes

| where | event | variable | before | after | dim | mag |
|---|---|---|---|---|---|---|
| sc-005#b1 | ev-005 | `issued` | `False` | `True` | epistemic | 30 |
| sc-007#b3 | ev-007 | `holder` | `lo-03` | `ch-02` | material | 30 |

### ob-07 — The tip jar

| where | event | variable | before | after | dim | mag |
|---|---|---|---|---|---|---|
| sc-001#b4 | ev-001 | `amount` | `86` | `94` | material | 15 |
| sc-009#b3 | ev-009 | `amount` | `94` | `98` | material | 8 |
| sc-017#b2 | ev-017 | `polaroid_clipped_beside` | `False` | `True` | material | 70 |

### ob-08 — Polaroid of Hale's face

| where | event | variable | before | after | dim | mag |
|---|---|---|---|---|---|---|
| sc-016#b3 | ev-016 | `exists` | `False` | `True` | material | 85 |
| sc-016#b3 | ev-016 | `holder` | `none` | `ch-02` | material | 70 |
| sc-017#b2 | ev-017 | `holder` | `ch-02` | `lo-02` | material | 50 |

### Final state

```json
{
 "ch-01": {
  "hunger": 97,
  "tokens_held": 0,
  "detachment": 6,
  "cover": "archived",
  "cash": 69,
  "sun_injury": "hand_scorch",
  "prize_claim": "forfeit",
  "position": "lo-06"
 },
 "ch-02": {
  "blood_level": 70,
  "retained_night": 94,
  "archive_depth": 24,
  "stance_on_hale": "archivist",
  "existential_stability": 54,
  "tokens_hidden": true,
  "position": "lo-02"
 },
 "ch-03": {
  "hunger": 48,
  "writes_on_rotation": 7,
  "experiment_phase": "failed",
  "noticed_comparison": true,
  "position": "lo-01"
 },
 "ch-04": {
  "hunger": 28,
  "uv_grid_extent": 90,
  "eliminated": false
 },
 "ch-05": {
  "hunger": 32,
  "blood_monopoly": "dry",
  "eliminated": false
 },
 "ch-06": {
  "hunger": 22,
  "cult_count": 14,
  "eliminated": false
 },
 "ch-07": {
  "hunger": 40,
  "heart_taken": true,
  "eliminated": false
 },
 "ch-08": {
  "blood_level": 90,
  "retained_night": 24,
  "somatic_mark": true,
  "position": "lo-03"
 },
 "ch-09": {
  "blood_level": 89,
  "retained_night": 38,
  "avoidance_of_hale": "refusing",
  "bruise_visible": true,
  "position": "lo-04"
 },
 "lo-01": {
  "uv_coverage": 74,
  "crossing_safe_for_guests": false
 },
 "lo-02": {
  "after_dark_policy": "locked",
  "register_display": "hale_polaroid",
  "window_artifact": "roll_bar"
 },
 "lo-03": {
  "uv_stock": 16,
  "after_hours_open": true
 },
 "lo-04": {
  "blood_stores": "dry",
  "night_access": "sealed"
 },
 "lo-05": {
  "body_at_treeline": true
 },
 "lo-06": {
  "sun_on_stone": true,
  "uv_encroaching": true,
  "tokens_present": "hidden_nearby"
 },
 "lo-07": {
  "closed": true,
  "fog_read": "static"
 },
 "lo-08": {
  "cult_visible": true
 },
 "ob-01": {
  "holder": "ch-02",
  "film_left": 1
 },
 "ob-02": {
  "holder": "ch-02",
  "frame_count": 19,
  "content_flag": "hale_face"
 },
 "ob-03": {
  "holder": "ch-02",
  "track": "leader_hiss"
 },
 "ob-04": {
  "assembled": 4,
  "holder": "hidden"
 },
 "ob-05": {
  "holder": "ch-02",
  "powered": true
 },
 "ob-06": {
  "issued": true,
  "holder": "ch-02"
 },
 "ob-07": {
  "amount": 98,
  "polaroid_clipped_beside": true
 },
 "ob-08": {
  "exists": true,
  "holder": "lo-02"
 },
 "gr-01": {
  "remaining": 6
 },
 "gr-02": {
  "comparing_notes": true,
  "rotation_viable": false
 },
 "gr-03": {
  "formed": true
 },
 "gr-04": {
  "active": true
 },
 "cn-01": {
  "decoded_by_hale": "full_cost",
  "invocation_spoken": false,
  "match_running": true
 },
 "cn-02": {
  "integrity": "torn"
 },
 "cn-03": {
  "phase": "spreading"
 },
 "cn-04": {
  "town_risk": "critical"
 }
}
```

## Validation

**0 error(s), 14 warning(s)**

```
[WARNING] G19 @ expose.synopsis: 816 words, target 450-550
[WARNING] G21 @ sc-005: scene has no prose leaf
[WARNING] G21 @ sc-006: scene has no prose leaf
[WARNING] G21 @ sc-007: scene has no prose leaf
[WARNING] G21 @ sc-008: scene has no prose leaf
[WARNING] G21 @ sc-009: scene has no prose leaf
[WARNING] G21 @ sc-010: scene has no prose leaf
[WARNING] G21 @ sc-011: scene has no prose leaf
[WARNING] G21 @ sc-012: scene has no prose leaf
[WARNING] G21 @ sc-013: scene has no prose leaf
[WARNING] G21 @ sc-014: scene has no prose leaf
[WARNING] G21 @ sc-015: scene has no prose leaf
[WARNING] G21 @ sc-016: scene has no prose leaf
[WARNING] G21 @ sc-017: scene has no prose leaf
```

