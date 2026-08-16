# False Weight

*A blacksmith's apprentice must retrieve a village relic stolen by raiders before the midwinter rite, or her mountain hamlet forfeits the protection three generations of iron have bought.*

`fantasy` · screenplay · adult · pov third_limited, past

## Shape

| layer | count |
|---|---|
| L4 plots | 2 |
| L3 entities | 15 |
| L5 events | 14 |
| L6 scenes | 14 |
| beats | 62 |
| patch ops | 64 |
| prose leaves | 7 |
| prose words | 5,910 |

Entities by type: character 2, concept 2, group 3, location 5, object 3

## Plots

### pl-01 — The Relic Before Midwinter

- **type** `external_main` · **outcome** `partial_success` · share 0.46
- **goal** Walk the winter pass, recover the stolen presentation-relic, and have it accepted with the year's iron tithe at the midwinter ground so Highkettle keeps its pass-protection and grain-right.
- **stakes** If the relic is not presented on time, the Hold closes the pass and withholds winter grain; the hamlet has no reserve of food, coin, fighters, or a replacement piece.
- **agent** ['ch-01'] vs **resistance** ['gr-02', 'lo-02', 'lo-03', 'gr-03', 'ob-02', 'pl-02']
- **events** 6 owned, 11 served

| step | function | events | because |
|---|---|---|---|
| st1 | given_compact | ev-001 | — |
| st2 | state_of_rupture | ev-002 | — |
| st3 | forced_commission | ev-003 | pl-02:st1 |
| st4 | ordeal_of_crossing | ev-004 | — |
| st5 | retrieval_by_craft | ev-005 | — |
| st6 | cost_of_return | ev-006 | — |
| st7 | bind | ev-010 | pl-02:st4, pl-02:st6 |
| st8 | public_presentation | ev-012 | pl-02:st8 |
| st9 | year_bought_on_false_weight | ev-012 | pl-02:st8 |

### pl-02 — What the House Is Owed

- **type** `relationship` · **outcome** `transformation_of_goal` · share 0.54
- **goal** Settle what she owes Orren for raising, craft, and the lie bound into the relic, and act on that settlement before the piece must be presented or refused.
- **stakes** If she cannot decide, she either spends the recovery on a fraud she now owns or risks a late, broken, or challenged presentation that starves the hamlet and still leaves the household unread.
- **agent** ['ch-01'] vs **resistance** ['ch-02', 'lo-01', 'ob-01', 'cn-01', 'gr-01', 'pl-01']
- **events** 8 owned, 11 served

| step | function | events | because |
|---|---|---|---|
| st1 | unsettled_household | ev-001 | — |
| st2 | forced_separation | ev-003 | pl-01:st3 |
| st3 | missed_hearing | ev-006 | pl-01:st6 |
| st4 | craft_recognition | ev-007, ev-008 | pl-01:st5 |
| st5 | admission_of_the_weld | ev-008 | — |
| st6 | present_indefensibility | ev-009 | — |
| st7 | unpaid_ledger | ev-010 | pl-01:st6 |
| st8 | point_of_no_return | ev-011 | pl-01:st7 |
| st9 | unforgiven_naming | ev-013 | pl-01:st8 |
| st10 | altered_household | ev-014 | — |

## Story tree (primary edges)

Each scene has exactly one parent event; each event exactly one parent plot.
Secondary memberships are shown in brackets.

- **pl-01** The Relic Before Midwinter
  - `ev-002` t4 — Raiders take the relic from the village chest and leave the unfinished tithe-iron behind.
    - `sc-002` d2 Rupture the given compact by stealing the relic and leaving the unfinished iron behind.
  - `ev-003` t6 — The hamlet sends Willa for the relic because Orren cannot cross and the tithe is still short.  _[also pl-02]_
    - `sc-003` d3 Force the commission that sends her out before the household debt can be spoken.
  - `ev-004` t8 — Willa walks the winter pass on foot; the crossing spends days and stamina she cannot spare.
    - `sc-004` d4 Spend irreplaceable walking time and stamina on the open winter pass.
  - `ev-005` t10 — Willa takes the relic from the sleeping camp by weight and craft, and kills no one for it.
    - `sc-005` d5 Recover the relic by craft and stealth without killing for a village object.
  - `ev-006` t12 — The return frostbites her hands and spends the hours in which Orren might have spoken first.  _[also pl-02]_
    - `sc-006` d6 Exact frost injury and the missed hearing as the price of bringing the piece back.
  - `ev-012` t24 — She presents the forged relic and thin tithe; the steward accepts both and the year is bought.  _[also pl-02]_
    - `sc-012` d12 Present the forged relic and thin tithe so the steward accepts a year without an inner test.
- **pl-02** What the House Is Owed
  - `ev-001` t2 — At the forge, Willa and Orren weigh thin stock for the unfinished tithe while her debt to him stays unset.  _[also pl-01]_
    - `sc-001` d1 Establish the unfinished tithe, the pending compact, and the household debt she will not ask him to settle.
  - `ev-007` t14 — Before sleep Willa weighs the piece, reads the false weight and Orren's weld, and keeps it.  _[also pl-01]_
    - `sc-007` d7 Let craft read the recovered piece as a forty-year forgery and keep that reading inside the house.
  - `ev-008` t16 — She takes the reading to Orren; he admits the forty-year weld and the levy bound to himself.
    - `sc-008` d8 Take the craft reading to Orren so the weld and levy are admitted inside the house.
  - `ev-009` t18 — The old reasons fail now: the levy ends only with his death or a public breaking.
    - `sc-009` d9 Test the old reasons against a levy that cannot be moved, paused, or paid off.
  - `ev-010` t20 — She cannot settle the debt; keeping or exposing the piece both spend the recovery.  _[also pl-01]_
    - `sc-010` d10 Bind her between exposing the piece and spending the recovery on a fraud she now owns.
  - `ev-011` t22 — She partitions the costs: silence now, winter work, leaving at the spring opening of the pass.  _[also pl-01]_
    - `sc-011` d11 Partition the unpaid debt into silence, winter labor, and leaving when the pass opens.
  - `ev-013` t26 — She names the weld and levy as metal; he repeats the old reasons and is not forgiven.  _[also pl-01]_
    - `sc-013` d13 Name the weld and levy as metal after the year is bought, without granting pardon.
  - `ev-014` t28 — They return to work that is no longer home; she sets a true bar and the arm comes level.
    - `sc-014` d14 Return to shared work that is no longer home, and set a true bar until the arm comes level.

## State trajectories

### ch-01 — Willa

| where | event | variable | before | after | dim | mag |
|---|---|---|---|---|---|---|
| sc-003#b4 | ev-003 | `task` | `at_forge` | `commissioned` | social | 80 |
| sc-003#b5 | ev-003 | `location` | `forge_house` | `village` | spatial | 40 |
| sc-004#b1 | ev-004 | `location` | `village` | `winter_pass` | spatial | 50 |
| sc-004#b3 | ev-004 | `stamina` | `86` | `58` | physiological | 45 |
| sc-005#b1 | ev-005 | `location` | `winter_pass` | `raider_camp` | spatial | 30 |
| sc-006#b1 | ev-006 | `location` | `raider_camp` | `winter_pass` | spatial | 30 |
| sc-006#b2 | ev-006 | `hands_frosted` | `False` | `True` | physiological | 70 |
| sc-006#b3 | ev-006 | `stamina` | `58` | `30` | physiological | 60 |
| sc-007#b1 | ev-007 | `location` | `winter_pass` | `forge_house` | spatial | 40 |
| sc-007#b4 | ev-007 | `relic_knowledge` | `unread` | `read_as_forgery` | epistemic | 90 |
| sc-007#b5 | ev-007 | `task` | `commissioned` | `returned_with_piece` | social | 55 |
| sc-008#b2 | ev-008 | `relic_knowledge` | `read_as_forgery` | `reading_taken_to_orren` | epistemic | 75 |
| sc-010#b3 | ev-010 | `debt_account` | `unsettled` | `cannot_settle` | psychological | 80 |
| sc-011#b1 | ev-011 | `debt_account` | `cannot_settle` | `partitioned` | psychological | 85 |
| sc-011#b2 | ev-011 | `belonging` | `of_the_house` | `wintering_then_leaving` | social | 80 |
| sc-012#b1 | ev-012 | `location` | `forge_house` | `presentation_ground` | spatial | 40 |
| sc-012#b2 | ev-012 | `task` | `returned_with_piece` | `presented` | social | 70 |
| sc-013#b1 | ev-013 | `location` | `presentation_ground` | `forge_house` | spatial | 25 |

### ch-02 — Orren

| where | event | variable | before | after | dim | mag |
|---|---|---|---|---|---|---|
| sc-008#b3 | ev-008 | `disclosure` | `withheld` | `admitted` | epistemic | 85 |
| sc-009#b3 | ev-009 | `body_condition` | `54` | `44` | physiological | 40 |
| sc-012#b1 | ev-012 | `location` | `forge_house` | `presentation_ground` | spatial | 30 |
| sc-013#b1 | ev-013 | `location` | `presentation_ground` | `forge_house` | spatial | 25 |
| sc-013#b3 | ev-013 | `disclosure` | `admitted` | `renamed_without_pardon` | epistemic | 80 |
| sc-014#b1 | ev-014 | `household_role` | `master_of_house` | `coworker_after_break` | social | 85 |

### cn-01 — what is owed

| where | event | variable | before | after | dim | mag |
|---|---|---|---|---|---|---|
| sc-008#b4 | ev-008 | `old_reasons_status` | `unheard` | `heard_as_past` | epistemic | 70 |
| sc-010#b4 | ev-010 | `settlement` | `open` | `unpayable` | psychological | 75 |
| sc-011#b4 | ev-011 | `settlement` | `unpayable` | `partitioned` | psychological | 80 |

### cn-02 — the midwinter compact

| where | event | variable | before | after | dim | mag |
|---|---|---|---|---|---|---|
| sc-004#b4 | ev-004 | `days_until_rite` | `21` | `14` | world | 55 |
| sc-006#b5 | ev-006 | `days_until_rite` | `14` | `6` | world | 60 |
| sc-011#b5 | ev-011 | `days_until_rite` | `6` | `3` | world | 30 |
| sc-012#b4 | ev-012 | `status` | `pending_rite` | `standing_this_year` | political | 90 |
| sc-012#b4 | ev-012 | `days_until_rite` | `3` | `0` | world | 70 |

### gr-01 — Highkettle folk

| where | event | variable | before | after | dim | mag |
|---|---|---|---|---|---|---|
| sc-002#b5 | ev-002 | `grain_right` | `held_pending_rite` | `at_risk` | political | 80 |
| sc-011#b2 | ev-011 | `smith_labor` | `orren_and_apprentice` | `willa_covering_winter` | social | 60 |
| sc-012#b5 | ev-012 | `grain_right` | `at_risk` | `secured_one_year` | political | 90 |

### gr-02 — the far-slope band

| where | event | variable | before | after | dim | mag |
|---|---|---|---|---|---|---|
| sc-002#b4 | ev-002 | `camp_state` | `settled_poor` | `holding_theft` | material | 70 |
| sc-005#b4 | ev-005 | `camp_state` | `holding_theft` | `missing_the_piece` | material | 65 |

### gr-03 — the valley Hold

| where | event | variable | before | after | dim | mag |
|---|---|---|---|---|---|---|
| sc-012#b4 | ev-012 | `accepted_this_year` | `False` | `True` | political | 85 |
| sc-012#b4 | ev-012 | `pass_policy` | `protecting` | `renewed_one_year` | political | 80 |

### lo-01 — the forge-house

| where | event | variable | before | after | dim | mag |
|---|---|---|---|---|---|---|
| sc-003#b5 | ev-003 | `occupancy` | `both_present` | `orren_only` | spatial | 55 |
| sc-007#b1 | ev-007 | `occupancy` | `orren_only` | `both_present` | spatial | 45 |
| sc-012#b1 | ev-012 | `occupancy` | `both_present` | `empty` | spatial | 35 |
| sc-013#b1 | ev-013 | `occupancy` | `empty` | `both_present` | spatial | 30 |
| sc-014#b1 | ev-014 | `household_character` | `raising_home` | `shared_work_not_home` | social | 90 |
| sc-014#b1 | ev-014 | `occupancy` | `both_present` | `both_after_break` | spatial | 70 |

### lo-02 — the winter pass

| where | event | variable | before | after | dim | mag |
|---|---|---|---|---|---|---|
| sc-004#b2 | ev-004 | `traffic` | `none` | `willa_ascent` | spatial | 40 |
| sc-006#b4 | ev-006 | `traffic` | `willa_ascent` | `willa_return` | spatial | 35 |
| sc-007#b2 | ev-007 | `traffic` | `willa_return` | `none` | spatial | 20 |

### lo-03 — the lee camp

| where | event | variable | before | after | dim | mag |
|---|---|---|---|---|---|---|
| sc-005#b4 | ev-005 | `alertness` | `hungry_rest` | `piece_gone` | social | 70 |

### lo-04 — Highkettle village

| where | event | variable | before | after | dim | mag |
|---|---|---|---|---|---|---|
| sc-002#b3 | ev-002 | `chest_status` | `holding_relic` | `empty` | material | 85 |

### lo-05 — the midwinter ground

| where | event | variable | before | after | dim | mag |
|---|---|---|---|---|---|---|
| sc-012#b3 | ev-012 | `rite_status` | `not_yet` | `accepted` | political | 85 |
| sc-012#b3 | ev-012 | `occupancy` | `empty` | `presentation_done` | spatial | 40 |

### ob-01 — the village weight

| where | event | variable | before | after | dim | mag |
|---|---|---|---|---|---|---|
| sc-002#b2 | ev-002 | `custody` | `village_chest` | `raiders` | material | 90 |
| sc-005#b3 | ev-005 | `custody` | `raiders` | `willa` | material | 90 |
| sc-012#b2 | ev-012 | `custody` | `willa` | `steward_table` | material | 55 |
| sc-012#b3 | ev-012 | `presented_and_accepted` | `False` | `True` | political | 90 |
| sc-013#b1 | ev-013 | `custody` | `steward_table` | `returned_house` | material | 40 |

### ob-02 — the tithe-iron

| where | event | variable | before | after | dim | mag |
|---|---|---|---|---|---|---|
| sc-011#b3 | ev-011 | `completeness` | `unfinished` | `finished_thin` | material | 50 |
| sc-012#b2 | ev-012 | `custody` | `forge` | `steward_table` | material | 45 |
| sc-012#b2 | ev-012 | `completeness` | `finished_thin` | `presented` | material | 50 |
| sc-013#b1 | ev-013 | `custody` | `steward_table` | `returned_house` | material | 30 |

### ob-03 — the forge balance

| where | event | variable | before | after | dim | mag |
|---|---|---|---|---|---|---|
| sc-001#b2 | ev-001 | `last_weighing` | `idle` | `stock_check` | material | 25 |
| sc-014#b2 | ev-014 | `last_weighing` | `stock_check` | `true_bar_level` | material | 75 |
| sc-014#b2 | ev-014 | `in_use` | `False` | `True` | spatial | 20 |

### Final state

```json
{
 "ch-01": {
  "location": "forge_house",
  "stamina": 30,
  "hands_frosted": true,
  "relic_knowledge": "reading_taken_to_orren",
  "debt_account": "partitioned",
  "belonging": "wintering_then_leaving",
  "task": "presented"
 },
 "ch-02": {
  "location": "forge_house",
  "levy_paying": true,
  "disclosure": "renamed_without_pardon",
  "household_role": "coworker_after_break",
  "body_condition": 44
 },
 "lo-01": {
  "household_character": "shared_work_not_home",
  "occupancy": "both_after_break"
 },
 "lo-02": {
  "passability": "open_on_foot",
  "traffic": "none"
 },
 "lo-03": {
  "occupancy": "band_camped",
  "alertness": "piece_gone"
 },
 "lo-04": {
  "chest_status": "empty",
  "aware_of_forgery": false
 },
 "lo-05": {
  "rite_status": "accepted",
  "occupancy": "presentation_done"
 },
 "ob-01": {
  "custody": "returned_house",
  "presented_and_accepted": true,
  "publicly_intact": true
 },
 "ob-02": {
  "completeness": "presented",
  "custody": "returned_house"
 },
 "ob-03": {
  "last_weighing": "true_bar_level",
  "in_use": true
 },
 "gr-01": {
  "grain_right": "secured_one_year",
  "knows_forgery": false,
  "smith_labor": "willa_covering_winter"
 },
 "gr-02": {
  "hunger": 78,
  "camp_state": "missing_the_piece"
 },
 "gr-03": {
  "accepted_this_year": true,
  "pass_policy": "renewed_one_year"
 },
 "cn-01": {
  "settlement": "partitioned",
  "old_reasons_status": "heard_as_past"
 },
 "cn-02": {
  "status": "standing_this_year",
  "days_until_rite": 0,
  "challenge_made": false
 }
}
```

## Validation

**0 error(s), 8 warning(s)**

```
[WARNING] G19.count @ scenes: 14 scenes against a target of 8
[WARNING] G21 @ sc-008: scene has no prose leaf
[WARNING] G21 @ sc-009: scene has no prose leaf
[WARNING] G21 @ sc-010: scene has no prose leaf
[WARNING] G21 @ sc-011: scene has no prose leaf
[WARNING] G21 @ sc-012: scene has no prose leaf
[WARNING] G21 @ sc-013: scene has no prose leaf
[WARNING] G21 @ sc-014: scene has no prose leaf
```

