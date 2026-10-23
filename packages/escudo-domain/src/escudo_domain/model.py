"""Modelo portable y combinación de decisiones (regla y modelo: gana la más severa)."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from math import exp

from escudo_domain.events import Decision
from escudo_domain.rules import Rule


@dataclass(frozen=True)
class LogisticModel:
    """Entrenado offline (scikit-learn); servido en Python puro desde JSON: corre igual en Pyodide."""

    version: str
    bias: float
    weights: Mapping[str, float]
    means: Mapping[str, float]
    stds: Mapping[str, float]

    @classmethod
    def from_json(cls, text: str) -> LogisticModel:
        d = json.loads(text)
        return cls(d["version"], d["bias"], d["weights"], d["means"], d["stds"])

    def score(self, f: Mapping[str, float]) -> tuple[float, dict[str, float]]:
        contrib = {k: w * (f[k] - self.means[k]) / self.stds[k] for k, w in self.weights.items()}
        z = self.bias + sum(contrib.values())
        p = 1 / (1 + exp(-z)) if z >= 0 else exp(z) / (1 + exp(z))  # sigmoide estable (sin overflow)
        return p, contrib


@dataclass(frozen=True, slots=True)
class Thresholds:
    step_up: float
    review: float
    decline: float


@dataclass(frozen=True, slots=True)
class Verdict:
    decision: Decision
    score: float
    reasons: tuple[str, ...]


def decide(f: Mapping[str, float], rules: Sequence[Rule], model: LogisticModel, th: Thresholds) -> Verdict:
    fired = [r for r in rules if r.matches(f)]
    score, contrib = model.score(f)
    if score >= th.decline:
        by_score = Decision.DECLINE
    elif score >= th.review:
        by_score = Decision.REVIEW
    elif score >= th.step_up:
        by_score = Decision.STEP_UP
    else:
        by_score = Decision.APPROVE
    decision = max([by_score, *(r.decision for r in fired)])  # gana la más severa
    top = sorted(contrib.items(), key=lambda kv: kv[1], reverse=True)[:3]
    reasons = tuple([f"regla:{r.id}" for r in fired] + [f"modelo:{k}" for k, v in top if v > 0])
    return Verdict(decision, score, reasons)
