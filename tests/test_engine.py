"""Self-tests for the patch engine, the fold, and the validator.

Run with:  python3 tests/test_engine.py

The second half is an injected-error suite: the whitepaper's phase-0 exit
criterion is that the validator catches >90% of deliberately introduced faults,
so each case breaks a valid story in one specific way and asserts that the
matching rule fires.
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from narrativeforge import jsonpatch, timeline, validate  # noqa: E402

PASS, FAIL = [], []


def check(name: str, condition: bool, detail: str = "") -> None:
    (PASS if condition else FAIL).append(name)
    print(f"  {'ok  ' if condition else 'FAIL'}  {name}{'' if condition else '  <- ' + detail}")


# --------------------------------------------------------------------------
# A minimal but complete two-plot story
# --------------------------------------------------------------------------

def fixture() -> dict:
    entities = {"entities": {
        "ch-01": {
            "entity_id": "ch-01", "type": "character", "canonical_name": "Vesna",
            "aliases": ["the oathkeeper"], "salience": "major", "plots": ["pl-01", "pl-02"],
            "profile": {
                "backstory": {
                    "b01": {"text": "She swore the warden's oath at seventeen.", "when": "age 17", "tags": ["oath"]},
                    "b02": {"text": "Her brother drowned the winter after.", "when": "age 18", "tags": ["wound"]},
                },
                "speech_signature": {
                    "sentence_shape": "short, declarative, verb first",
                    "vocabulary_domain": "water, depth, weight, the rule book",
                    "verbal_tic": "states a measurement instead of an opinion",
                    "never_says": "sorry",
                    "under_stress": "goes silent and does the thing",
                },
            },
            "relationships": {"ch-02": {"kind": "sister_of", "valence": 30, "notes": {}}},
            "state_variables": {
                "oath_intact": {"kind": "bool", "description": "whether the oath still binds her",
                                "dimension": "psychological", "init": True},
                "trust_in_sister": {"kind": "scalar", "description": "how far she trusts Mira",
                                    "dimension": "social", "range": [0, 100], "init": 60},
            },
            "state": {"oath_intact": True, "trust_in_sister": 60},
            "arc": {"start_state": "bound", "end_state": "free and alone"},
        },
        "ch-02": {
            "entity_id": "ch-02", "type": "character", "canonical_name": "Mira",
            "aliases": [], "salience": "major", "plots": ["pl-02"],
            "profile": {
                "backstory": {"b01": {"text": "She left the valley at fifteen.", "when": "age 15", "tags": []}},
                "speech_signature": {
                    "sentence_shape": "long, hedged, trailing clauses",
                    "vocabulary_domain": "money, weather, other people's opinions",
                    "verbal_tic": "answers a question with a question",
                    "never_says": "a plain yes",
                    "under_stress": "talks more and faster",
                },
            },
            "relationships": {"ch-01": {"kind": "sister_of", "valence": -20, "notes": {}}},
            "state_variables": {
                "secret_known": {"kind": "bool", "description": "whether Vesna knows what she did",
                                 "dimension": "epistemic", "init": False},
            },
            "state": {"secret_known": False},
            "arc": {"start_state": "hiding", "end_state": "exposed"},
        },
        "lo-01": {
            "entity_id": "lo-01", "type": "location", "canonical_name": "The Ashen Ford",
            "aliases": [], "salience": "supporting", "plots": ["pl-01"],
            "profile": {"backstory": {"b01": {"text": "The ford has taken four travellers in ten years.", "when": "standing", "tags": []}}},
            "relationships": {},
            "state_variables": {"passable": {"kind": "bool", "description": "whether it can be crossed",
                                             "dimension": "spatial", "init": True}},
            "state": {"passable": True},
            "arc": {"start_state": "open", "end_state": "flooded"},
        },
    }}

    plots = {"plots": [
        {"plot_id": "pl-01", "type": "external_main", "title": "Cross before the thaw",
         "agent": ["ch-01"], "resistance": ["lo-01", "pl-02"],
         "goal": "reach the far bank before the ford floods", "stakes": "the valley starves",
         "outcome": "success",
         "spine": {
             "st1": {"step": 1, "function": "state_of_need", "intent": "The crossing becomes urgent.", "because": []},
             "st2": {"step": 2, "function": "point_of_no_return", "intent": "She commits to the ford.",
                     "because": ["pl-02:st2"]},
         },
         "resolution_step": "st2", "thematic_function": "duty outlasts affection",
         "screen_time_share": 0.6,
         "interference": [{"with": "pl-02", "kind": "competing_demand_on_agent"}],
         "covers_synopsis": ["s01", "s02"]},
        {"plot_id": "pl-02", "type": "relationship", "title": "What Mira did",
         "agent": ["ch-02"], "resistance": ["ch-01"],
         "goal": "keep the truth of the drowning buried", "stakes": "her sister's love",
         "outcome": "failure",
         "spine": {
             "st1": {"step": 1, "function": "state_of_concealment", "intent": "Mira conceals.", "because": []},
             "st2": {"step": 2, "function": "exposure", "intent": "Vesna learns it.", "because": []},
         },
         "resolution_step": "st2", "thematic_function": "a secret kept is a debt accruing",
         "screen_time_share": 0.4, "interference": [], "covers_synopsis": ["s03"]},
    ]}

    events = {"events": {
        "ev-001": {
            "event_id": "ev-001", "story_time": {"index": 1, "label": "day 1", "duration_min": 30},
            "primary_plot": "pl-01", "plots": ["pl-01"],
            "plot_bindings": [{"plot": "pl-01", "step": "st1"}],
            "location": "lo-01", "participants": ["ch-01", "lo-01"],
            "summary": "The thaw begins and the ford starts to close.",
            "action": "Vesna reaches the ford at first light and finds the water higher than the "
                      "marker stone. She measures the rise against her own knee and calculates the "
                      "hours left. The far bank is still visible. She does not cross, because the "
                      "provisions are not loaded and the mules are two hours behind her on the road.",
            "state_changes": [
                {"entity": "lo-01", "variable": "passable", "path": "/lo-01/state/passable",
                 "dimension": "spatial", "before": True, "after": False, "magnitude": 75},
            ],
            "caused_by": [], "causes": ["ev-002"],
            "causal_note": "The thaw is the first mover of the story.",
            "reversal": False, "plot_function": "inciting", "is_root": True, "is_sink": False,
        },
        "ev-002": {
            "event_id": "ev-002", "story_time": {"index": 2, "label": "day 1, noon", "duration_min": 20},
            "primary_plot": "pl-02", "plots": ["pl-01", "pl-02"],
            "plot_bindings": [{"plot": "pl-02", "step": "st1"}, {"plot": "pl-02", "step": "st2"}],
            "location": "lo-01", "participants": ["ch-01", "ch-02"],
            "summary": "Mira's account of the drowning collapses under questioning.",
            "action": "Mira offers to carry the provisions across alone. Vesna asks why she knows "
                      "the depth of the channel so exactly, and Mira answers with a date that does "
                      "not match the one she gave ten years earlier. Vesna does not accuse her. She "
                      "recalculates everything she believed about the winter her brother died.",
            "state_changes": [
                {"entity": "ch-02", "variable": "secret_known", "path": "/ch-02/state/secret_known",
                 "dimension": "epistemic", "before": False, "after": True, "magnitude": 100},
                {"entity": "ch-01", "variable": "trust_in_sister", "path": "/ch-01/state/trust_in_sister",
                 "dimension": "social", "before": 60, "after": 10, "magnitude": 75},
            ],
            "caused_by": ["ev-001"], "causes": ["ev-003"],
            "causal_note": "Only the forced wait at the ford put the two of them in one place.",
            "reversal": True, "plot_function": "midpoint_of_pl-02", "is_root": False, "is_sink": False,
        },
        "ev-003": {
            "event_id": "ev-003", "story_time": {"index": 3, "label": "day 1, dusk", "duration_min": 15},
            "primary_plot": "pl-01", "plots": ["pl-01", "pl-02"],
            "plot_bindings": [{"plot": "pl-01", "step": "st2"}],
            "location": "lo-01", "participants": ["ch-01"],
            "summary": "Vesna crosses alone and abandons the oath that bound her to her sister.",
            "action": "Vesna loads the provisions herself and enters the water at dusk, against the "
                      "warden's rule that forbids a night crossing. Halfway across she stops fighting "
                      "the current and lets it carry her downstream to the shallows, which is a thing "
                      "the oath explicitly forbids and which no one alive will ever be able to prove.",
            "state_changes": [
                {"entity": "ch-01", "variable": "oath_intact", "path": "/ch-01/state/oath_intact",
                 "dimension": "psychological", "before": True, "after": False, "magnitude": 100},
            ],
            "caused_by": ["ev-002"], "causes": [],
            "causal_note": "She crosses alone only because she can no longer trust Mira to carry anything.",
            "reversal": False, "plot_function": "climax_of_pl-01", "is_root": False, "is_sink": True,
        },
    }}

    scenes = {"scenes": {
        "sc-001": {
            "scene_id": "sc-001", "discourse_index": 1, "chapter": 1,
            "primary_event": "ev-001", "events": ["ev-001"],
            "primary_plot": "pl-01", "plots": ["pl-01"],
            "story_time_label": "day 1, first light", "location": "lo-01", "pov": "ch-01",
            "narrative_mode": "scene", "present": ["ch-01"], "offstage_referenced": ["ch-02"],
            "entry_states": {"lo-01": {"passable": True}, "ch-01": {"oath_intact": True, "trust_in_sister": 60}},
            "beats": [
                {"beat": 1, "event_id": "ev-001", "type": "action",
                 "text": "Vesna walks the bank at first light and reads the water against the marker "
                         "stone, counting the hours the crossing has left.",
                 "participants": ["ch-01", "lo-01"], "changes": []},
                {"beat": 2, "event_id": "ev-001", "type": "discovery",
                 "text": "The rise passes the stone while she watches, which puts the ford past the "
                         "depth the warden's rule permits and closes it to loaded animals.",
                 "participants": ["lo-01"],
                 "changes": [{"entity": "lo-01", "variable": "passable", "dimension": "spatial",
                              "before": True, "after": False, "magnitude": 75,
                              "op": {"op": "replace", "path": "/lo-01/state/passable", "value": False}}]},
            ],
            "exit_states": {"lo-01": {"passable": False}},
            "dramatic_function": "sets the clock", "tension_in": 20, "tension_out": 45,
            "questions_opened": {"q01": "Can she cross in time?"}, "questions_closed": [],
            "target_words": 700,
            "continuity_facts": {
                "ch-01": {"present": True, "conscious": "awake", "position": "on the bank",
                          "holding": [], "condition": "cold, dry"},
                "lo-01": {"present": True, "conscious": "absent", "position": "the ford",
                          "holding": [], "condition": "rising, past the marker"},
            },
        },
        "sc-002": {
            "scene_id": "sc-002", "discourse_index": 2, "chapter": 1,
            "primary_event": "ev-002", "events": ["ev-002", "ev-003"],
            "primary_plot": "pl-02", "plots": ["pl-01", "pl-02"],
            "story_time_label": "day 1, noon to dusk", "location": "lo-01", "pov": "ch-01",
            "narrative_mode": "scene", "present": ["ch-01", "ch-02"], "offstage_referenced": [],
            "entry_states": {"ch-01": {"trust_in_sister": 60, "oath_intact": True},
                             "ch-02": {"secret_known": False}, "lo-01": {"passable": False}},
            "beats": [
                {"beat": 1, "event_id": "ev-002", "type": "dialogue",
                 "text": "Mira volunteers to carry the load across alone, framing it as practicality "
                         "rather than penance, and Vesna asks how she knows the channel so well.",
                 "participants": ["ch-01", "ch-02"], "changes": []},
                {"beat": 2, "event_id": "ev-002", "type": "revelation",
                 "text": "Mira gives a date that contradicts the one she gave ten years ago, and "
                         "Vesna understands that her sister was at the water the night the boy drowned.",
                 "participants": ["ch-01", "ch-02"],
                 "changes": [
                     {"entity": "ch-02", "variable": "secret_known", "dimension": "epistemic",
                      "before": False, "after": True, "magnitude": 100,
                      "op": {"op": "replace", "path": "/ch-02/state/secret_known", "value": True}},
                     {"entity": "ch-01", "variable": "trust_in_sister", "dimension": "social",
                      "before": 60, "after": 10, "magnitude": 75,
                      "op": {"op": "replace", "path": "/ch-01/state/trust_in_sister", "value": 10}},
                 ]},
                {"beat": 3, "event_id": "ev-003", "type": "decision",
                 "text": "Vesna loads the provisions herself and enters the water at dusk, taking the "
                         "downstream drift the warden's rule forbids and telling no one.",
                 "participants": ["ch-01"],
                 "changes": [
                     {"entity": "ch-01", "variable": "oath_intact", "dimension": "psychological",
                      "before": True, "after": False, "magnitude": 100,
                      "op": {"op": "replace", "path": "/ch-01/state/oath_intact", "value": False}},
                 ]},
            ],
            "exit_states": {"ch-01": {"trust_in_sister": 10, "oath_intact": False},
                            "ch-02": {"secret_known": True}},
            "dramatic_function": "exposure and the cost of it", "tension_in": 45, "tension_out": 90,
            "questions_opened": {}, "questions_closed": ["q01"],
            "target_words": 1100,
            "continuity_facts": {
                "ch-01": {"present": False, "conscious": "awake", "position": "in the water",
                          "holding": ["ob-provisions"], "condition": "soaked, downstream"},
                "ch-02": {"present": True, "conscious": "awake", "position": "the near bank",
                          "holding": [], "condition": "still"},
            },
            "someone_behaves_badly": {
                "who": "ch-01",
                "what": "She asks the question she already knows the answer to, in front of "
                        "her sister, and makes her say it out loud.",
            },
        },
    }}

    expose = {
        "ending_first": {"ending": "She crosses alone.", "cost": "the oath and the sister",
                         "final_image": "a warden's badge left on a stone"},
        "jacket_copy": " ".join(["word"] * 130),
        "synopsis": {
            "s01": {"text": "A thaw closes the only ford before the valley's provisions can cross.",
                    "function": "disturbance", "story_time_rank": 1},
            "s02": {"text": "Vesna must cross before nightfall or the valley starves.",
                    "function": "goal", "story_time_rank": 2},
            "s03": {"text": "Her sister Mira's offer to help exposes a lie about a drowning ten years old.",
                    "function": "turn", "story_time_rank": 3},
        },
        "synopsis_word_count": 40,
    }

    root = {"title": "The Ashen Ford", "form": "short_story", "language": "en",
            "constraints": {"plot_count": 2, "scene_count_target": 2}}

    return {"root": root, "expose": expose, "plots_doc": plots,
            "entities_doc": entities, "events_doc": events, "scenes_doc": scenes}


# --------------------------------------------------------------------------

def test_pointer_and_patch() -> None:
    print("\njson pointer / patch")
    doc = {"a": {"b~c": {"d/e": 1}}, "list": [1, 2, 3]}
    check("escapes ~ and / in tokens", jsonpatch.resolve(doc, "/a/b~0c/d~1e") == 1)
    check("resolves array index", jsonpatch.resolve(doc, "/list/1") == 2)
    check("missing key raises", not jsonpatch.exists(doc, "/a/nope"))

    out = jsonpatch.apply_patch({"x": 1}, [{"op": "replace", "path": "/x", "value": 2}])
    check("replace", out == {"x": 2})
    out = jsonpatch.apply_patch({}, [{"op": "add", "path": "/x", "value": 5}])
    check("add", out == {"x": 5})
    out = jsonpatch.apply_patch({"x": 1, "y": 2}, [{"op": "remove", "path": "/y"}])
    check("remove", out == {"x": 1})

    try:
        jsonpatch.apply_patch({"x": 1}, [{"op": "replace", "path": "/nope", "value": 2}])
        check("replace on missing path fails", False, "no error raised")
    except jsonpatch.JsonPatchError:
        check("replace on missing path fails", True)

    try:
        jsonpatch.apply_patch({"x": 1}, [{"op": "test", "path": "/x", "value": 9}])
        check("failed test raises", False, "no error raised")
    except jsonpatch.JsonPatchError:
        check("failed test raises", True)

    original = {"x": 1}
    jsonpatch.apply_patch(original, [{"op": "replace", "path": "/x", "value": 2}])
    check("apply is non-destructive by default", original == {"x": 1})

    a = {"k": {"p": 1, "q": 2}}
    b = {"k": {"p": 9}, "n": True}
    check("diff round-trips", jsonpatch.apply_patch(a, jsonpatch.diff(a, b)) == b)

    check("finds arrays in patchable regions",
          jsonpatch.assert_no_arrays({"profile": {"scars": [{"t": "x"}]}}) == ["/profile/scars"])
    check("allowlists declarative arrays",
          jsonpatch.assert_no_arrays({"aliases": ["a", "b"]}) == [])


def test_fold() -> None:
    print("\nstate fold")
    fx = fixture()
    fold = timeline.fold(fx["entities_doc"], fx["events_doc"], fx["scenes_doc"])
    check("every patch applies", not fold.errors, "; ".join(fold.errors))
    check("beats fold in story-time order",
          [r.key for r in fold.order] == ["sc-001#b1", "sc-001#b2", "sc-002#b1", "sc-002#b2", "sc-002#b3"],
          str([r.key for r in fold.order]))

    check("t0 is the untouched dossier layer",
          fold.world_t0["ch-01"]["state"] == {"oath_intact": True, "trust_in_sister": 60})
    check("state after ev-002 reflects only what happened by then",
          fold.state_after_event("ev-002")["ch-01"]["state"] == {"oath_intact": True, "trust_in_sister": 10},
          json.dumps(fold.state_after_event("ev-002")["ch-01"]["state"]))
    check("final state", fold.final["ch-01"]["state"] == {"oath_intact": False, "trust_in_sister": 10})
    check("t0 is not mutated by the fold",
          fold.world_t0["ch-01"]["state"]["trust_in_sister"] == 60)

    check("event patch is derived from its beats wherever they live",
          fold.event_patch("ev-002") == [
              {"op": "replace", "path": "/ch-02/state/secret_known", "value": True},
              {"op": "replace", "path": "/ch-01/state/trust_in_sister", "value": 10}])
    check("scene patch spans several events",
          len(fold.scene_patch("sc-002")) == 3)
    check("plot patch collects across events",
          len(fold.plot_patch("pl-02", fx["events_doc"]["events"])) == 3)

    replayed = jsonpatch.apply_patch(fold.world_t0, fold.scene_patch("sc-001") + fold.scene_patch("sc-002"))
    check("replaying scene patches reproduces the final state", replayed == fold.final)

    check("state_at resolves markers",
          fold.state_at("sc-001")["lo-01"]["state"]["passable"] is False)
    history = fold.entity_history("ch-01")
    check("entity history is ordered and complete",
          [h["variable"] for h in history] == ["trust_in_sister", "oath_intact"],
          str([h["variable"] for h in history]))


def test_valid_story() -> None:
    print("\nvalidator on a well-formed story")
    report = validate.validate_story(**fixture())
    check("no errors", report.ok, report.as_text(limit=12))
    schema_issues = validate.validate_artifact("entities", fixture()["entities_doc"])
    check("entities match the schema", not schema_issues, str(schema_issues[:3]))
    schema_issues = validate.validate_artifact("scenes", fixture()["scenes_doc"])
    check("scenes match the schema", not schema_issues, str(schema_issues[:3]))
    schema_issues = validate.validate_artifact("events", fixture()["events_doc"])
    check("events match the schema", not schema_issues, str(schema_issues[:3]))


# --------------------------------------------------------------------------
# Injected-error suite
# --------------------------------------------------------------------------

def _break(mutator) -> list[str]:
    fx = fixture()
    mutator(fx)
    return [f.rule for f in validate.validate_story(**fx).errors]


def test_injected_errors() -> None:
    print("\ninjected errors (each must be caught)")

    cases = [
        ("G5 contradicted before-value", "G5", lambda fx:
            fx["scenes_doc"]["scenes"]["sc-002"]["beats"][1]["changes"][1].update({"before": 55})),
        ("G5 declared entry state disagrees with the fold", "G5.scene", lambda fx:
            fx["scenes_doc"]["scenes"]["sc-002"]["entry_states"]["lo-01"].update({"passable": True})),
        ("G5 declared exit state disagrees with the fold", "G5.scene", lambda fx:
            fx["scenes_doc"]["scenes"]["sc-002"]["exit_states"]["ch-01"].update({"oath_intact": True})),
        ("G11 patch targets a nonexistent path", "G5.path", lambda fx:
            fx["scenes_doc"]["scenes"]["sc-001"]["beats"][1]["changes"][0]["op"].update(
                {"path": "/lo-01/state/no_such_var"})),
        ("G4 event changes an undeclared variable", "G4", lambda fx:
            fx["events_doc"]["events"]["ev-001"]["state_changes"][0].update({"variable": "invented"})),
        ("G15 beat changes something its event never declared", "G15.undeclared", lambda fx:
            fx["events_doc"]["events"]["ev-003"]["state_changes"].clear()),
        ("G15 event declares a change no beat realizes", "G15.unrealized", lambda fx:
            fx["scenes_doc"]["scenes"]["sc-002"]["beats"][2]["changes"].clear()),
        ("G1 event serves no plot", "G1", lambda fx:
            fx["events_doc"]["events"]["ev-001"].update({"plots": [], "primary_plot": "pl-01"})),
        ("G1 primary plot is not among the plots served", "G1", lambda fx:
            fx["events_doc"]["events"]["ev-001"].update({"primary_plot": "pl-02"})),
        ("G2 spine step no event discharges", "G2.bind", lambda fx:
            fx["plots_doc"]["plots"][0]["spine"].update(
                {"st3": {"step": 3, "function": "coda", "intent": "unbound", "because": []}})),
        ("G3 causal edges disagree", "G3.sym", lambda fx:
            fx["events_doc"]["events"]["ev-001"]["causes"].clear()),
        ("G3 cause runs backwards in story time", "G3.time", lambda fx:
            fx["events_doc"]["events"]["ev-001"]["story_time"].update({"index": 9})),
        ("G6 scene's primary event is not among its events", "G6", lambda fx:
            fx["scenes_doc"]["scenes"]["sc-001"].update({"primary_event": "ev-003"})),
        ("G6 event realized by no scene", "G6.uncovered", lambda fx:
            fx["scenes_doc"]["scenes"]["sc-002"].update({"events": ["ev-002"]})),
        ("G7 primary edges do not form one tree", "G7.tree", lambda fx:
            fx["scenes_doc"]["scenes"]["sc-001"].update({"primary_plot": "pl-02", "plots": ["pl-02"]})),
        ("G8 reference to an entity with no dossier", "G8", lambda fx:
            fx["events_doc"]["events"]["ev-001"]["participants"].append("ch-99")),
        ("G10 direct speech in a beat", "G10", lambda fx:
            fx["scenes_doc"]["scenes"]["sc-001"]["beats"][0].update(
                {"text": 'She said, "the water is too high," and turned away from the bank ' * 2})),
        ("G12 array inside a patchable region", "G12", lambda fx:
            fx["entities_doc"]["entities"]["ch-01"]["profile"].update({"scars": [{"where": "hand"}]})),
        ("G13 undecomposed prose block in a profile", "G13", lambda fx:
            fx["entities_doc"]["entities"]["ch-01"]["profile"].update({"backstory_long": "x" * 400})),
        ("G14 beats run backwards in story time inside a scene", "G14", lambda fx:
            fx["scenes_doc"]["scenes"]["sc-002"]["beats"].reverse()),
        ("G16 duplicate story-time index", "G16", lambda fx:
            fx["events_doc"]["events"]["ev-002"]["story_time"].update({"index": 1})),
        ("G17 t0 state disagrees with the declared init", "G17", lambda fx:
            fx["entities_doc"]["entities"]["ch-01"]["state"].update({"trust_in_sister": 99})),
        ("G20 value leaves its declared range", "G20", lambda fx:
            fx["scenes_doc"]["scenes"]["sc-002"]["beats"][1]["changes"][1].update(
                {"after": 900, "op": {"op": "replace", "path": "/ch-01/state/trust_in_sister", "value": 900}})),
    ]

    caught = 0
    for name, expected_rule, mutator in cases:
        rules = _break(mutator)
        hit = any(rule.startswith(expected_rule) for rule in rules)
        caught += hit
        check(f"{expected_rule:<16} {name}", hit, f"fired instead: {sorted(set(rules))[:6]}")

    rate = caught / len(cases)
    print(f"\n  injected-error detection rate: {caught}/{len(cases)} = {rate:.0%}")
    check("detection rate >= 90% (whitepaper phase-0 exit criterion)", rate >= 0.9, f"{rate:.0%}")


# --------------------------------------------------------------------------

if __name__ == "__main__":
    test_pointer_and_patch()
    test_fold()
    test_valid_story()
    test_injected_errors()
    print(f"\n{'=' * 60}\n{len(PASS)} passed, {len(FAIL)} failed")
    if FAIL:
        print("failed: " + ", ".join(FAIL))
    raise SystemExit(1 if FAIL else 0)
