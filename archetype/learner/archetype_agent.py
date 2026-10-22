"""ARCHETYPE (B11) and its ablations.

    observations -> encoder -> relation model (principles) -> transfer confidence -> decisions
                 -> architecture constructor (from local primitives, by signature) -> evaluation -> refinement

Training: induce one principle per architectural transformation from the shared exploration, then (unless
ablated) run counterfactual experiments through the lab's anonymous knobs to test, refine and, where the
effect changes without any observable change, mark principles as needing an empirical test.

Ablation flags (config, all default True):
    structural_memory, contraindications, transfer_confidence, counterfactual, economics,
    regime_detection, structural_analogy, reconstruction
"""
from __future__ import annotations

import statistics
from typing import Any, Dict, List, Optional

from archetype.architecture import generate as Gen
from archetype.baselines.base import Agent, Ctx, Experience, compose_from, hill_climb, measure_effects
from archetype.learner.encoder import encode
from archetype.learner.relation import Row, fit_principle
from archetype.learner.transformations import TRANSFORMATIONS, apply, present
from archetype.memory.principles import HELP_DELTA, PrincipleStore
from archetype.transfer import decisions as D

LEARNER_VERSION = "archetype-learner-0.1"
CF_SOURCES, CF_BUDGET, HIDDEN_FLIP_RATE = 3, 22, 0.15


class ArchetypeAgent(Agent):
    kind = "archetype"
    uses_lab = True

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(name, config)
        self.on = {k: bool(self.config.get(k, True)) for k in ("structural_memory", "contraindications", "transfer_confidence", "counterfactual",
                                                                "economics", "regime_detection", "structural_analogy", "reconstruction")}
        self.store = PrincipleStore()
        self.features: List[str] = []
        self.feature_sd: Dict[str, float] = {}
        self.patterns: List[List[str]] = []                 # transformation sets of the best training architectures (no primitive names)
        self.copies: List[Dict[str, Any]] = []              # only used by the "no reconstruction" ablation
        self.training = {"counterfactual_evaluations": 0, "counterfactual_environments": 0, "forgotten": 0}
        self._phi1: Dict[str, float] = {}
        self._best_v = 0.0

    # ------------------------------------------------------------------ training
    def fit(self, experience: List[Experience], lab: Any = None) -> None:
        if not self.on["structural_memory"]:
            return
        phis = {e.token: encode(e.view) for e in experience}
        self.features = sorted(next(iter(phis.values())))
        self.feature_sd = {f: (statistics.pstdev([p[f] for p in phis.values()]) or 1.0) for f in self.features}
        self.patterns = sorted({tuple(sorted(t for t in TRANSFORMATIONS if present(t, e.best_config))) for e in experience})
        self.patterns = [list(p) for p in self.patterns]
        self.copies = [{"phi": phis[e.token], "config": e.best_config} for e in experience]
        rows: Dict[str, List[Row]] = {t: [(phis[e.token], e.effects[t], e.token) for e in experience] for t in TRANSFORMATIONS}
        for i, t in enumerate(TRANSFORMATIONS):
            self.store.put(fit_principle(t, rows[t], self.features, f"P{i:02d}"))
        if self.on["counterfactual"] and lab is not None:
            self._counterfactuals(experience, phis, rows, lab)
        self.training["forgotten"] = self.store.forget()

    def _counterfactuals(self, experience, phis, rows, lab) -> None:
        """Spec §27: try to falsify each principle with single-property interventions on supporting environments."""
        support = {e.token: {t for t, p in self.store.principles.items() if p.predict(phis[e.token])["p_help"] >= 0.5 and e.effects[t] > HELP_DELTA} for e in experience}
        sources, covered = [], set()
        for _ in range(CF_SOURCES):
            tok = max(sorted(support), key=lambda k: (len(support[k] - covered), k not in sources))
            sources.append(tok)
            covered |= support[tok]
        by_token = {e.token: e for e in experience}
        step = 0
        new_rows: Dict[str, List[Row]] = {t: [] for t in TRANSFORMATIONS}
        hidden = {t: [0, 0] for t in TRANSFORMATIONS}     # [interventions without observable change on a supporting source, effect flips]
        for tok in sources:
            src = by_token[tok]
            for knob in range(lab.n_knobs):
                for direction in ("up", "down"):
                    ctx = lab.open(tok, knob, direction, CF_BUDGET)
                    _, eff = measure_effects(ctx, reps=2)
                    self.training["counterfactual_evaluations"] += ctx.used
                    self.training["counterfactual_environments"] += 1
                    phi = encode(ctx.view)
                    changed = any(abs(phi[f] - phis[tok][f]) > 1e-9 for f in self.features)
                    step += 1
                    for t, p in self.store.principles.items():
                        correct = (p.predict(phi)["p_help"] >= 0.5) == (eff[t] > HELP_DELTA)
                        flipped = (eff[t] > HELP_DELTA) != (src.effects[t] > HELP_DELTA) and abs(eff[t] - src.effects[t]) > 0.08
                        p.record_test(correct, step, "counterfactual", {"knob": knob, "direction": direction, "observable_change": changed, "effect": round(eff[t], 4)})
                        if not changed and src.effects[t] > HELP_DELTA:
                            hidden[t][0] += 1
                            hidden[t][1] += int(flipped)
                        if changed:
                            new_rows[t].append((phi, eff[t], ctx.view["token"]))
        for t, (n, flips) in hidden.items():
            # the effect vanished although nothing observable changed, repeatedly: an unobservable condition exists
            self.store.principles[t].hidden_sensitive = flips >= 2 and flips / n >= HIDDEN_FLIP_RATE
        # refine: re-induce every relation on passive + interventional rows, keeping the test history
        for i, (t, old) in enumerate(list(self.store.principles.items())):
            p = fit_principle(t, rows[t] + new_rows[t], self.features, old.id)
            # trust keeps the whole test history: out-of-bag checks of the old and the refined relation plus every counterfactual test
            p.support_count += old.support_count
            p.contradiction_count += old.contradiction_count
            for k in ("counterfactual_results", "hidden_sensitive", "last_tested"):
                setattr(p, k, getattr(old, k))
            changed_rule = [r["conditions"] for r in p.antecedent] != [r["conditions"] for r in old.antecedent] or len(p.contraindications) != len(old.contraindications)
            if p.hidden_sensitive:
                p.contraindications.append({"kind": "unobservable", "note": "effect changed under an intervention with no observable change; test before use"})
            tests = p.support_count + p.contradiction_count
            p.status = ("RETIRED" if old.status == "RETIRED" or (tests >= 8 and p.confidence < 0.35) else "CONTRADICTED" if p.confidence < 0.5
                        else "CONDITIONAL" if (changed_rule or p.hidden_sensitive) else "SUPPORTED")
            self.store.put(p)

    def snapshot(self) -> Dict[str, Any]:
        return {"learner_version": LEARNER_VERSION, "flags": self.on, "store": self.store.to_dict(), "patterns": self.patterns, "training": self.training}

    # ------------------------------------------------------------------ prediction
    def _predict(self, phi: Dict[str, float]) -> Dict[str, Dict[str, Any]]:
        return {t: p.predict(phi, use_relations=self.on["structural_analogy"], use_contraindications=self.on["contraindications"])
                for t, p in self.store.principles.items()}

    def transfer_scores(self, view: Dict[str, Any]) -> Optional[Dict[str, float]]:
        if not self.on["structural_memory"]:
            return None
        pred = self._predict(encode(view))
        return {t: (pred[t]["confidence"] if t in pred else 0.0) for t in TRANSFORMATIONS}

    # ------------------------------------------------------------------ acting
    def act(self, ctx: Ctx) -> None:
        self.report = {"decisions": {}, "environment_decision": "BUILD_NEW", "proposal": None, "prediction": None, "accepted": [], "tests": 0}
        patience = D.PATIENCE if self.on["economics"] else None
        if not self.on["structural_memory"]:
            best, self._best_v = hill_climb(ctx, Gen.BASE, None, patience=patience)
            return
        phi = self._phi1 = encode(ctx.view)
        if not self.on["reconstruction"]:
            return self._copy(ctx, phi, patience)
        pred = self._predict(phi)
        trusted, to_test, abstained = [], [], []
        for t, pr in pred.items():
            p = self.store.principles[t]
            d = D.decide(pr, p.hidden_sensitive, self.on["transfer_confidence"], self.on["contraindications"])
            if d in ("TRUST", "TEST") and apply(t, Gen.BASE, ctx.primitives)[0] == apply(t, Gen.BASE, ctx.primitives)[1]:
                d = "IGNORE"            # the local inventory cannot express this transformation
            self.report["decisions"][t] = {"decision": d, "confidence": round(pr["confidence"], 4), "expected": round(pr["expected"], 4), "principle": p.id}
            {"TRUST": trusted, "TEST": to_test, "ABSTAIN": abstained}.get(d, []).append(t)
        if not self.on["economics"]:
            to_test += abstained            # without economics every uncertain principle is tested
        # zero-evaluation prediction: what the frozen knowledge alone would build here
        predicted = [t for t in trusted + to_test if pred[t]["p_help"] >= 0.5]
        self.report["prediction"] = compose_from(predicted, ctx.primitives)
        if trusted and not to_test:
            ctx.declare(compose_from(trusted, ctx.primitives))           # zero-evaluation transfer
        base_v = ctx.evaluate(Gen.BASE)
        accepted = list(trusted)
        for t in sorted(to_test, key=lambda k: -pred[k]["expected"]):
            if ctx.remaining < 4:
                break
            c, new = apply(t, Gen.BASE, ctx.primitives)
            if ctx.mean(c) is None:
                ctx.evaluate(c)
            ctx.evaluate(new)
            need = max(D.ACCEPT_MIN, D.ACCEPT_FRACTION * pred[t]["expected"])
            if abs(ctx.mean(new) - ctx.mean(c) - need) < D.RETEST_BAND and ctx.remaining >= 4:
                ctx.evaluate(c)                     # too close to call: replicate the pair
                ctx.evaluate(new)
            delta = ctx.mean(new) - ctx.mean(c)
            self.report["tests"] += 1
            ok = delta >= need
            self.report["decisions"][t].update({"tested_delta": round(delta, 4), "outcome": "ACCEPTED" if ok else "REJECTED"})
            if ok:
                accepted.append(t)
        self.report["proposal"] = compose_from(accepted, ctx.primitives) if accepted else None
        self.report["accepted"] = accepted
        best, best_v = Gen.BASE, base_v
        if accepted:
            cfg = compose_from(accepted, ctx.primitives)
            if ctx.mean(cfg) is None and ctx.remaining > 0:
                ctx.evaluate(cfg)
            for e in ctx.trace:
                if ctx.mean(e["config"]) > best_v:
                    best, best_v = e["config"], ctx.mean(e["config"])
            self.report["environment_decision"] = "REUSE" if sorted(accepted) in self.patterns else "MODIFY"
        elif abstained:
            self.report["environment_decision"] = "ABSTAIN"
        ctx.declare(best)
        best, self._best_v = hill_climb(ctx, best, best_v, patience=patience)

    def _copy(self, ctx: Ctx, phi: Dict[str, float], patience: Optional[int]) -> None:
        """Ablation: no architecture reconstruction. Copies the best configuration of the structurally nearest training environment."""
        def dist(c):
            return sum(((phi[f] - c["phi"][f]) / self.feature_sd[f]) ** 2 for f in self.features)
        cfg = Gen.normalize_config(min(self.copies, key=dist)["config"], ctx.primitives)
        self.report.update({"proposal": cfg, "prediction": cfg, "environment_decision": "REUSE"})
        ctx.declare(cfg)
        base_v, v = ctx.evaluate(Gen.BASE), ctx.evaluate(cfg)
        best, best_v = (cfg, v) if v >= base_v else (Gen.BASE, base_v)
        ctx.declare(best)
        best, self._best_v = hill_climb(ctx, best, best_v, patience=patience)

    def phase2(self, ctx: Ctx, incumbent: Gen.Config) -> None:
        ctx.declare(incumbent)
        self.report["regime"] = {"detected": None}
        if not self.on["regime_detection"]:
            return
        if self.on["structural_memory"]:
            phi2 = encode(ctx.view)
            used = sorted({f for p in self.store.active() for f in p.features_used()})
            shift = max((abs(phi2[f] - self._phi1[f]) / self.feature_sd[f] for f in used), default=0.0)
            if shift > D.SHIFT_SD:
                keep = dict(self.report)
                self.act(ctx)
                self.report = {**keep, "phase2": self.report, "regime": {"detected": "observations", "shift": round(shift, 3)}}
                return
        v = ctx.evaluate(incumbent)
        if self._best_v - v > D.DROP:
            keep = dict(self.report)
            self.act(ctx)
            self.report = {**keep, "phase2": self.report, "regime": {"detected": "score_drop", "drop": round(self._best_v - v, 4)}}
