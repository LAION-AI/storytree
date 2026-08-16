"""The author/judge loop.

    author writes  ->  mechanical prechecks  ->  judge scores  ->  gate
        pass  -> store, then write the hindsight trace and loop on that
        revise -> author revises with the critique in hand, judge keeps its
                  previous critiques so it can say improved / held / regressed

Two design decisions worth naming, both defended in the white paper:

The gate is recomputed in code from the scores. A judge's own `gate.passed` is
the one field it has an incentive to get wrong and it costs nothing to check.

Mechanical prechecks run before a judge call is spent. `docs/07 §12.4` concluded
that 0/3 roster compliance and 1/3 location compliance "are not prompt problems
at this point. They are missing assertions." A precheck failure returns the
artifact to the author with the failing assertion as the instruction, and no
judge tokens are burned.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from . import nodes, promptlib
from . import rubric as rubric_mod
from .store import Store


@dataclass
class RoundResult:
    round_no: int
    artifact: dict
    critique: dict | None
    gate: rubric_mod.Gate | None
    prechecks: list[str] = field(default_factory=list)


@dataclass
class LoopResult:
    node_id: str
    node_type: str
    passed: bool
    rounds: int
    artifact: dict
    final_gate: rubric_mod.Gate | None
    history: list[RoundResult]


# --------------------------------------------------------------------------
# Mechanical prechecks. Cheap, deterministic, and they catch the failures the
# corpus shows both evaluated models making.
# --------------------------------------------------------------------------

def precheck(node_type: str, artifact: dict, run=None) -> list[str]:
    findings: list[str] = []

    blob = json.dumps(artifact, ensure_ascii=False)
    if len(blob) < 200:
        findings.append(
            "degenerate response: the document is under 200 characters. A fake "
            "node is worse than a missing one."
        )
        return findings

    if node_type == "root":
        emb = (artifact.get("plot_embedding") or {})
        if not emb.get("genres") and not emb.get("dimensions"):
            findings.append("plot_embedding is empty; score every key on the rubric.")
        style = artifact.get("style") or {}
        if run is not None and "dialogue_ratio" in style:
            measured = run.overview.get("mean_dialogue_ratio")
            if measured is not None and abs(style["dialogue_ratio"] - measured) > 0.05:
                findings.append(
                    f"style.dialogue_ratio is {style['dialogue_ratio']}, the "
                    f"measured ratio is {measured}. Use the measured value."
                )
        for key in ("logline", "premise"):
            if not (artifact.get(key) or "").strip():
                findings.append(f"{key} is empty.")
        forbidden = style.get("forbidden_tics") or []
        if not forbidden:
            findings.append("style.forbidden_tics is empty; name the habits this "
                            "script conspicuously avoids.")

    if node_type == "event":
        for ev in _iter_items(artifact, "events"):
            for change in ev.get("state_changes", []) or []:
                if change.get("before") == change.get("after"):
                    findings.append(
                        f"{ev.get('event_id')}: state change on "
                        f"{change.get('variable')} has before == after."
                    )

    if node_type == "scene" and run is not None:
        env = getattr(run, "current_envelope", None) or {}
        roster = {s.upper() for s in (env.get("on_screen") or [])}
        for line in _specimen_speakers(artifact):
            if roster and line.upper() not in roster:
                findings.append(
                    f"specimen speaker {line!r} is not on the envelope roster "
                    f"{sorted(roster)}."
                )
    return findings


def _iter_items(artifact: dict, key: str):
    block = artifact.get(key)
    if isinstance(block, dict):
        return list(block.values())
    if isinstance(block, list):
        return block
    return [artifact] if artifact.get("event_id") else []


def _specimen_speakers(artifact: dict) -> list[str]:
    out = []
    def walk(node):
        if isinstance(node, dict):
            if "speaker" in node and isinstance(node["speaker"], str):
                out.append(node["speaker"])
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)
    walk(artifact)
    return out


# --------------------------------------------------------------------------

def run_node(*, node_type: str, node_id: str, run, store: Store,
             author_backend, judge_backend, max_rounds: int | None = None,
             verbose: bool = True) -> LoopResult:
    """Drive one artifact through the loop. Resumable: any round already on disk
    is loaded rather than re-generated."""
    from narrativeforge.schemas import SCHEMAS

    spec = nodes.REGISTRY[node_type]
    if spec.context is None:
        raise nodes.NotWired(
            f"node type {node_type!r} has a rubric and prompts but no context "
            f"builder yet — write nodes._{node_type}_context()."
        )
    max_rounds = max_rounds or rubric_mod.MAX_ROUNDS

    author_prompt = promptlib.load_prompt("author", node_type)
    judge_prompt = promptlib.load_prompt("judge", node_type)
    schema = SCHEMAS.get(spec.schema_key, {})

    history: list[RoundResult] = []
    critique: dict | None = None
    artifact: dict = {}
    gate: rubric_mod.Gate | None = None

    for round_no in range(1, max_rounds + 1):
        # ---- author --------------------------------------------------
        artifact = store.load_round(node_id, round_no, "draft")
        if artifact is None:
            ctx = spec.context(run)
            if critique is not None:
                ctx["revision_block"] = promptlib.revision_block(critique, round_no)
            system, user = promptlib.render(author_prompt, ctx)
            if verbose:
                print(f"  [r{round_no}] author  {len(system) + len(user):,} prompt chars")
            artifact = author_backend.complete_json(
                system, user, schema, stage=f"{node_type}.author",
                tag=f"{node_id}.r{round_no}.draft")
            store.save_draft(node_id, round_no, artifact)

        # ---- mechanical prechecks -----------------------------------
        findings = precheck(node_type, artifact, run)
        if findings:
            if verbose:
                print(f"  [r{round_no}] precheck FAILED ({len(findings)})")
                for f in findings:
                    print(f"          - {f}")
            critique = {
                "node_id": node_id, "round": round_no, "source": "mechanical",
                "scores": [],
                "mechanical": {"precheck_failures": findings},
                "gate": {"min_score": 0, "mean": 0.0, "passed": False},
                "verdict": {"decision": "revise", "top_instructions": findings[:3]},
            }
            store.save_critique(node_id, round_no, critique)
            history.append(RoundResult(round_no, artifact, critique, None, findings))
            continue

        # ---- judge ---------------------------------------------------
        critique = store.load_round(node_id, round_no, "critique")
        if critique is None or critique.get("source") == "mechanical":
            jctx = nodes.JUDGE_CONTEXT[node_type](run, artifact)
            if history:
                jctx["previous_critiques"] = (
                    "YOUR PREVIOUS CRITIQUES OF THIS ARTIFACT — say per dimension "
                    "whether it improved, held or regressed, and repeat once any "
                    "instruction that was not followed.\n\n"
                    + json.dumps([h.critique for h in history if h.critique],
                                 indent=1, ensure_ascii=False)
                )
            system, user = promptlib.render(judge_prompt, jctx)
            if verbose:
                print(f"  [r{round_no}] judge   {len(system) + len(user):,} prompt chars")
            critique = judge_backend.complete_json(
                system, user, rubric_mod.critique_schema(spec.rubric),
                stage=f"{node_type}.judge", tag=f"{node_id}.r{round_no}.critique")
            critique.setdefault("node_id", node_id)
            critique["round"] = round_no
            weak = rubric_mod.evidence_ok(critique)
            if weak:
                critique.setdefault("mechanical", {})["evidence_warnings"] = weak
            store.save_critique(node_id, round_no, critique)

        gate = rubric_mod.evaluate_gate(critique, spec.rubric)
        history.append(RoundResult(round_no, artifact, critique, gate))
        if verbose:
            print(f"  [r{round_no}] gate    mean={gate.mean:.2f} min={gate.minimum} "
                  f"{'PASS' if gate.passed else 'revise'}"
                  + (f"  below: {[d for d, _ in gate.below]}" if gate.below else ""))
        if gate.passed:
            store.save_artifact(node_id, artifact, gate=gate.as_dict(),
                                rounds=round_no)
            return LoopResult(node_id, node_type, True, round_no, artifact, gate,
                              history)

    store.save_artifact(node_id, artifact, gate=(gate.as_dict() if gate else
                                                 {"passed": False}),
                        rounds=len(history))
    return LoopResult(node_id, node_type, False, len(history), artifact, gate,
                      history)


# --------------------------------------------------------------------------

def dataset_records(result: LoopResult, store: Store, *,
                    run_id: str) -> list[dict]:
    """Turn one completed node into fine-tuning records.

    Four kinds, all kept:
      author_draft   context -> artifact, tagged with the round and the gate
      judge_critique context + artifact -> critique   (the judge LoRA's data)
      revision       artifact + critique -> revised artifact
      trace          artifact + history -> hindsight derivation
    """
    records: list[dict] = []
    base = {"run": run_id, "node_id": result.node_id,
            "node_type": result.node_type, "passed": result.passed}
    for entry in result.history:
        if entry.critique is None:
            continue
        records.append(dict(base, kind="judge_critique", round=entry.round_no,
                            artifact=entry.artifact, critique=entry.critique))
        records.append(dict(base, kind="author_draft", round=entry.round_no,
                            artifact=entry.artifact,
                            gate=entry.gate.as_dict() if entry.gate else None))
    for prev, nxt in zip(result.history, result.history[1:]):
        if prev.critique:
            records.append(dict(base, kind="revision",
                                round=nxt.round_no,
                                before=prev.artifact,
                                critique=prev.critique,
                                after=nxt.artifact))
    return records
