#!/usr/bin/env python3
"""Top-down pilot generator: story root -> ... -> scene prose, with reasoning.

Runs the T1..T9 chain from docs/16-topdown-generation-plan.md on the
OpenCode Zen responses API (see zen_client.py), capped at --per-layer
traces per step (default 5). Every generation is one call returning an
explicit deliberation plus a JSON artifact:

    <reasoning> ... </reasoning>
    <artifact> ```json { ... } ``` </artifact>

Output is JSONL, one record per trace:
  {tid, seed, step, part, reasoning, artifact, usage, model, gen_s}
or {tid, seed, step, part, error} on failure. Dependents of a failed step
are skipped, never hallucinated on nothing. Re-running with the same --out
skips tids already present (resumable).

Seed (the "given" story root) comes from one HF film or a brief file:
  python3 topdown_generate.py --hf-dir /path/to/hf-dataset --film <slug> \\
      --out gen.jsonl --per-layer 5
  python3 topdown_generate.py --brief brief.txt --seed-name demo --out gen.jsonl

Only --steps t1,t4 (subset) runs just those steps, loading prior artifacts
with --resume-in gen.jsonl. Key via OPENCODE_API_KEY (see zen_client.py).

Cost note: two-call mode (reasoning first, artifact conditioned on it) is
the default -- it is what the plan (§6) mandates and what scores higher on
genuine derivation. Add --single-call for the legacy cheap mode (reasoning
+artifact in one call, roughly half the generation calls).
"""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from topdown_pairs import _cut  # noqa: E402
from zen_client import ZenClient, ZenError  # noqa: E402

SYS = ("You are a story architect working TOP-DOWN: from an abstract story "
       "root you derive ever more concrete layers. Commit late: open "
       "possibilities, do not close them. Never invent proper nouns the "
       "layers above did not establish. Answer with EXACTLY two tagged "
       "sections and nothing outside them:\n"
       "<reasoning> your deliberation: candidates considered, what you "
       "rejected and why, what the layer above forces </reasoning>\n"
       "<artifact> one ```json fenced block with the artifact </artifact>")

# Call 1 of the two-call default: deliberation ONLY. The artifact does not
# exist yet, so there is nothing to paraphrase -- this is what fixes D4
# (genuine derivation). Demands: candidates, rejections, near-miss.
REASON_SYS = ("You are a story architect working TOP-DOWN. This is step 1 of "
              "2: DELIBERATION ONLY. Commit late: open possibilities, do not "
              "close them. Never invent proper nouns the layers above did not "
              "establish.\n"
              "Do ALL of the following, in this order:\n"
              "1. List at least 2 candidate directions and what each would "
              "force the layers below to show.\n"
              "2. Reject all but one, with concrete reasons tied to the layers "
              "above -- never taste, always evidence.\n"
              "3. Name the near-miss: the rejected option closest to winning, "
              "and what would flip your choice.\n"
              "4. End with the decision plus the concrete anchors the next "
              "step must honour.\n"
              "Write NO artifact, NO JSON, NO final wording. Reasoning only, "
              "wrapped in <reasoning>...</reasoning> and nothing outside it.")

# Call 2 of the two-call default: build strictly from the deliberation.
# Carries the D2 (cite sources) and D5 (checklist) upgrades.
ARTIFACT_SYS = ("You are a story architect working TOP-DOWN. This is step 2 "
                "of 2: build the artifact STRICTLY from the deliberation below "
                "plus the layers above it.\n"
                "Rules:\n"
                "- Use only what the deliberation decided. If it left a gap, "
                "decide it now and flag it in one <note> line.\n"
                "- D2 groundedness: every claim leans on a named element of "
                "the layers above (field name or id). List them.\n"
                "- D5 coverage: the task names required keys -- confirm each "
                "is present before finishing.\n"
                "- D3 coherence: re-read your artifact for contradictions "
                "before finishing.\n"
                "Answer with <artifact> containing one ```json fenced block, "
                "plus optional <note> lines -- nothing else.")

RE_META = {
    "themes": ("central dilemma + big questions. ANTI-FLOSKEL: every abstract "
               "claim names a concrete situation that LATER events must show. "
               "Artifact: {\"big_questions\": [...], \"central_dilemma\": {...}}"),
    "external": ("outer conflicts. Artifact: {\"conflicts\": [...]}"),
    "internal": ("inner conflicts. Artifact: {\"internal_conflicts\": [...]}"),
    "relationships": ("relationship arcs. Artifact: {\"relationship_arcs\": [...]}"),
    "perspectives": ("throughline perspectives on the dilemma, one per future "
                     "plot. Artifact: {\"perspectives\": [...]}"),
}

REGISTERS = "physical, positional, knowledge, relational, emotional, status, safety"


def _parse(text):
    m = re.search(r"<reasoning>(.*?)</reasoning>", text, re.S)
    reasoning = m.group(1).strip() if m else None
    m2 = re.search(r"```json(.*?)```", text, re.S)
    blob = m2.group(1).strip() if m2 else None
    if blob is None:
        m3 = re.search(r"<artifact>(.*?)</artifact>", text, re.S)
        blob = m3.group(1).strip() if m3 else None
    artifact = None
    if blob:
        try:
            artifact = json.loads(blob)
        except Exception:
            pass
    return reasoning, artifact


class Chain:
    def __init__(self, seed, root, per_layer=5, max_tokens=8192,
                 single_call=False, client=None):
        self.seed = seed
        self.root = root
        self.N = per_layer
        self.max_tokens = max_tokens
        self.single_call = single_call
        self.client = client or ZenClient()
        self.meta = {}
        self.plots = []
        self.entities = []
        self.expose = None
        self.skeletons = []
        self.chains = {}
        self.events = []
        self.cards = []
        self.proses = []

    # -- plumbing ------------------------------------------------------
    def tid(self, step, part):
        return "%s::topdown::%s::%s" % (self.seed, step, part)

    def call(self, tid, user):
        t0 = time.time()
        try:
            if self.single_call:
                raw, usage = self.client.generate(
                    user, instructions=SYS, max_output_tokens=self.max_tokens)
                reasoning, artifact = _parse(raw)
                usage = {"mode": "single", "calls": [usage]}
            else:
                r1, u1 = self.client.generate(
                    user, instructions=REASON_SYS,
                    max_output_tokens=self.max_tokens)
                reasoning, _ = _parse(r1)
                if not reasoning:
                    # Fall back to the raw text: an untagged deliberation is
                    # still a deliberation. Only fail on truly empty output.
                    stripped = re.sub(r"</?reasoning>", "", r1).strip()
                    reasoning = stripped or None
                if not reasoning:
                    return {"tid": tid, "seed": self.seed,
                            "error": "empty deliberation, artifact call skipped",
                            "gen_s": round(time.time() - t0, 1)}
                r2, u2 = self.client.generate(
                    "DELIBERATION (decided, do not reopen):\n" + reasoning +
                    "\n\nNOW BUILD FROM IT, using this context:\n" + user,
                    instructions=ARTIFACT_SYS,
                    max_output_tokens=self.max_tokens)
                _, artifact = _parse(r2)
                if artifact is None:
                    m = re.search(r"```json(.*?)```", r2, re.S)
                    if m:
                        try:
                            artifact = json.loads(m.group(1).strip())
                        except Exception:
                            pass
                usage = {"mode": "two-call", "calls": [u1, u2]}
            rec = {"tid": tid, "seed": self.seed, "reasoning": reasoning,
                   "artifact": artifact, "usage": usage,
                   "model": self.client.model, "gen_s": round(time.time() - t0, 1),
                   "prompt": user}
            if not reasoning or artifact is None:
                rec["error"] = "unparsable model output"
            return rec
        except ZenError as e:
            return {"tid": tid, "seed": self.seed, "error": str(e)[:300],
                    "gen_s": round(time.time() - t0, 1)}

    def ctx(self, obj, budget=6000):
        return _cut(obj, budget)

    # -- steps ---------------------------------------------------------
    def t1_meta(self):
        jobs = []
        for section in list(RE_META)[:self.N]:
            user = ("STORY ROOT:\n%s\n\nWrite the '%s' part of the META layer. %s"
                    % (self.ctx(self.root), section, RE_META[section]))
            jobs.append((self.tid("meta", section), "meta", section, user))
        return jobs

    def t2_plots(self):
        user = ("STORY ROOT:\n%s\n\nMETA:\n%s\n\nDefine at most %d PLOTS. A plot "
                "is ONE perspective on the dilemma, as a causal thread: "
                "spine, agent, goal, resistance, stakes, outcome. Cover each "
                "big question with a thread; name rejected threads in reasoning. "
                "Artifact: {\"plots\": [{...}]}"
                % (self.ctx(self.root), self.ctx(self.meta), self.N))
        return [(self.tid("plots", "all"), "plots", "all", user)]

    def t3_entities(self):
        jobs = []
        names = self._cast_names()
        for i, name in enumerate(names[:self.N]):
            extra = ("Full cast (fix it now, at most %d entities, comma separated): "
                     % self.N) if i == 0 else ""
            user = ("META:\n%s\n\nPLOTS:\n%s\n\n%sWrite the profile of entity "
                    "'%s': type, profile, state variables, arc sketch, "
                    "relationships. Invent no factual past beyond the layers "
                    "above. Artifact: {\"name\": ..., \"type\": ..., ...}"
                    % (self.ctx(self.meta), self.ctx(self.plots), extra, name))
            jobs.append((self.tid("entity", "p%02d" % i), "entity", name, user))
        return jobs

    def _cast_names(self):
        agents = []
        for p in self.plots:
            a = p.get("agent")
            if a and a not in agents:
                agents.append(str(a))
        while len(agents) < min(self.N, 3):
            agents.append("Entity-%d" % (len(agents) + 1))
        return agents[:self.N]

    def t4_expose(self):
        user = ("ROOT:\n%s\n\nMETA:\n%s\n\nPLOTS:\n%s\n\nENTITIES:\n%s\n\nTell "
                "the story once. ending_first: how it ends, plainly, with cost "
                "and final image. synopsis: 5 numbered causal sections s01..s05 "
                "introducing every named entity in context. jacket_copy: sell "
                "without spoiling. Artifact: {\"ending_first\": ..., "
                "\"synopsis\": {...}, \"jacket_copy\": ...}"
                % (self.ctx(self.root), self.ctx(self.meta),
                   self.ctx(self.plots), self.ctx(self.entities)))
        return [(self.tid("expose", "all"), "expose", "all", user)]

    def t5_skeletons(self):
        jobs = []
        prev = []
        for i in range(self.N):
            user = ("EXPOSE:\n%s\n\nPLOTS:\n%s\n\nENTITIES:\n%s\n\nSKELETONS SO "
                    "FAR:\n%s\n\nDefine event skeleton #%d (at most %d events "
                    "total): the ONE question it answers, its owner plot "
                    "(exactly one), scene count 1-4, pivot sketch. Artifact: "
                    "{\"event_id\": \"ev-%03d\", \"question\": ..., "
                    "\"owner_plot\": ..., \"n_scenes\": ...}"
                    % (self.ctx(self.expose), self.ctx(self.plots),
                       self.ctx(self.entities), self.ctx(prev, 2000),
                       i + 1, self.N, i + 1))
            jobs.append((self.tid("skeleton", "ev-%03d" % (i + 1)),
                         "skeleton", "ev-%03d" % (i + 1), user))
            prev.append({"event_id": "ev-%03d" % (i + 1)})
        return jobs

    def t6_chains(self):
        jobs = []
        ev_ids = [s.get("event_id") for s in self.skeletons]
        for p in self.plots[:self.N]:
            pname = (p.get("plot_id") or p.get("name") or p.get("spine")
                     or "plot")
            user = ("PLOT:\n%s\n\nEVENT SKELETONS:\n%s\n\nMark which events "
                    "belong to THIS plot, in order, each enabled by the previous "
                    "one INSIDE this plot. Perspective discipline: only events "
                    "that move THIS outlook; no padding. Artifact: "
                    "{\"plot\": \"%s\", \"chain\": [{\"event_id\": ..., "
                    "\"why\": ...}]}"
                    % (self.ctx(p), self.ctx(self.skeletons), pname))
            jobs.append((self.tid("chain", str(pname)[:24]), "chain",
                         str(pname)[:24], user))
        void = [e for e in ev_ids]
        _ = void
        return jobs

    def t7_events(self):
        jobs = []
        prev = None
        for s in self.skeletons[:self.N]:
            user = ("SKELETON:\n%s\n\nPREVIOUS FILLED EVENT:\n%s\n\nPLOTS:\n%s\n\n"
                    "ENTITIES:\n%s\n\nFill this event: title, summary, action "
                    "(photographable only), state triples for at most 4 entities "
                    "over registers [%s] (entry/change/exit + evidence scene "
                    "number), turns_on as a MOMENT, affects_outside "
                    "{enables, blocks_or_costs, off_screen_reactor}. Exit states "
                    "must continue the previous event. Echo the skeleton's "
                    "event_id and n_scenes unchanged. Artifact: full event object."
                    % (self.ctx(s), self.ctx(prev, 2000), self.ctx(self.plots),
                       self.ctx(self.entities), REGISTERS))
            jobs.append((self.tid("event", s.get("event_id", "?")), "event",
                         s.get("event_id", "?"), user))
            prev = s
        return jobs

    def t8_cards(self):
        jobs, plan = [], self._scene_plan()
        prev_cards = []
        for sid, ev in plan:
            user = ("EVENT:\n%s\n\nPREVIOUS CARDS:\n%s\n\nWrite scene card %s: "
                    "location, present (who is there), summary, what_changes[] "
                    "(REAL transitions: who/axis/before/after, never restated "
                    "action), minds ONLY if an exchange happens (wants/feels/"
                    "shows/conceals per speaker), dramatic_function (its job, "
                    "and what it is NOT doing), uncertain[]. Artifact: the card."
                    % (self.ctx(ev, 3000), self.ctx(prev_cards, 3000), sid))
            jobs.append((self.tid("card", sid), "card", sid, user))
            prev_cards.append({"scene_id": sid})
        return jobs

    def _scene_plan(self):
        plan = []
        sk = {s.get("event_id"): s for s in self.skeletons}
        for ev in self.events[:self.N]:
            eid = ev.get("event_id", "?")
            n = ev.get("n_scenes") or sk.get(eid, {}).get("n_scenes") or 1
            for k in range(min(int(n), 3)):
                if len(plan) >= self.N:
                    return plan
                plan.append(("sc-%03d" % (len(plan) + 1), ev))
        if not plan and self.events:
            plan = [("sc-001", self.events[0])]
        return plan[:self.N]

    def t9_prose(self):
        jobs = []
        cards = self.cards or [{"scene_id": sid} for sid, _ in self._scene_plan()]
        for i, card in enumerate(cards[:self.N]):
            before = cards[max(0, i - 2):i]
            after = cards[i + 1:i + 3]
            user = ("TREE ABOVE:\n%s\n\nTARGET CARD:\n%s\n\nNEIGHBOUR CARDS "
                    "(context only):\n%s\n\nBLIND RULE: you see NO other scene's "
                    "prose -- only cards. Decide what happens from the card, do "
                    "not describe seen prose. Reason (craft: what this scene is "
                    "for + rejected alternative; psychology per speaker: "
                    "perception, wants, theory of mind incl. where a model of "
                    "the other is WRONG, trajectory in phases with triggers; "
                    "specimen: 6-10 dialogue lines with subtext + the swap test; "
                    "continuity: which tree facts used, by id). Then write ONLY "
                    "this scene's dialogue+action. Artifact: {\"scene_id\": ..., "
                    "\"scene_text\": ...}"
                    % (self.ctx({"root": self.root, "expose": self.expose,
                                 "plots": self.plots, "entities": self.entities}),
                       self.ctx(card, 3000),
                       self.ctx({"before": before, "after": after}, 4000)))
            sid = card.get("scene_id", "sc-%03d" % (i + 1))
            jobs.append((self.tid("prose", sid), "prose", sid, user))
        return jobs

    # -- driver --------------------------------------------------------
    STEPS = ["t1", "t2", "t3", "t4", "t5", "t6", "t7", "t8", "t9"]

    def run_step(self, step, skip=()):
        if step == "t1":
            jobs = self.t1_meta()
        elif step == "t2":
            jobs = self.t2_plots() if self.meta else []
        elif step == "t3":
            jobs = self.t3_entities() if self.plots else []
        elif step == "t4":
            jobs = self.t4_expose() if (self.meta and self.plots) else []
        elif step == "t5":
            jobs = self.t5_skeletons() if self.expose else []
        elif step == "t6":
            jobs = self.t6_chains() if (self.plots and self.skeletons) else []
        elif step == "t7":
            jobs = self.t7_events() if self.skeletons else []
        elif step == "t8":
            jobs = self.t8_cards() if self.events else []
        elif step == "t9":
            jobs = self.t9_prose() if self.events else []
        else:
            jobs = []
        recs = []
        for tid, st, part, user in jobs:
            if tid in skip:
                continue
            rec = self.call(tid, user)
            rec.update({"step": st, "part": part})
            recs.append(rec)
            self._ingest(st, part, rec.get("artifact"))
        return recs

    def _ingest(self, step, part, artifact):
        if not artifact:
            return
        if step == "meta":
            self.meta[part] = artifact
        elif step == "plots":
            self.plots = artifact.get("plots", [])[:self.N]
        elif step == "entity":
            self.entities.append(artifact)
        elif step == "expose":
            self.expose = artifact
        elif step == "skeleton":
            self.skeletons.append(artifact)
        elif step == "chain":
            self.chains[part] = artifact
        elif step == "event":
            self.events.append(artifact)
        elif step == "card":
            self.cards.append(artifact)
        elif step == "prose":
            self.proses.append(artifact)

    def load_state(self, records):
        for r in records:
            self._ingest(r.get("step"), r.get("part"), r.get("artifact"))


def load_jsonl(path):
    recs = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                recs.append(json.loads(line))
    return recs


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--film", default=None, help="HF film slug used as seed root")
    src.add_argument("--brief", default=None, help="brief text file used as seed")
    ap.add_argument("--hf-dir", default=None)
    ap.add_argument("--seed-name", default=None)
    ap.add_argument("--out", required=True)
    ap.add_argument("--per-layer", type=int, default=5)
    ap.add_argument("--steps", default="t1,t2,t3,t4,t5,t6,t7,t8,t9")
    ap.add_argument("--model", default=os.environ.get("ZEN_MODEL", "muse-spark-1.3-contributor-free"))
    ap.add_argument("--max-tokens", type=int, default=8192)
    ap.add_argument("--single-call", action="store_true",
                    help="legacy cheap mode: reasoning+artifact in one call. "
                         "Default is two-call (deliberate first, build second), "
                         "which scores higher on genuine derivation (D4).")
    ap.add_argument("--resume-in", default=None)
    args = ap.parse_args(argv)

    if args.film:
        if not args.hf_dir:
            raise SystemExit("--film needs --hf-dir")
        film = json.loads(Path(args.hf_dir, "data", args.film + ".json")
                          .read_text(encoding="utf-8"))
        seed = film.get("slug", args.film)
        root = (film.get("layers", {}) or {}).get("root") or {}
        root = {"film_title": film.get("title"), **root}
    else:
        seed = args.seed_name or Path(args.brief).stem
        root = {"brief": Path(args.brief).read_text(encoding="utf-8")[:6000]}

    client = ZenClient(model=args.model)
    chain = Chain(seed, root, per_layer=args.per_layer,
                  max_tokens=args.max_tokens, single_call=args.single_call,
                  client=client)
    if args.resume_in:
        chain.load_state([r for r in load_jsonl(args.resume_in)
                          if r.get("artifact")])

    done = set()
    out_path = Path(args.out)
    prior = []
    if out_path.exists():
        prior = load_jsonl(str(out_path))
        done = {r.get("tid") for r in prior}
    chain.load_state([r for r in prior if r.get("artifact")])
    out = out_path.open("a", encoding="utf-8")
    n_new = n_err = 0
    with out:
        for step in [s for s in args.steps.split(",") if s in Chain.STEPS]:
            for rec in chain.run_step(step, skip=done):
                out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                out.flush()
                done.add(rec["tid"])
                n_new += 1
                n_err += bool(rec.get("error"))
                print("%s %-8s %s" % (
                    "ERROR" if rec.get("error") else "ok",
                    rec.get("step"), rec["tid"]), flush=True)
    print("wrote %d new (%d errors)" % (n_new, n_err))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
