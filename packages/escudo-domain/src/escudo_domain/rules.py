"""Reglas como datos, sin `eval`: una gramática mínima de comparaciones unidas por AND."""

from __future__ import annotations

import operator
from collections.abc import Callable, Mapping
from dataclasses import dataclass

from escudo_domain.events import Decision
from escudo_domain.features import FEATURES

_OPS: dict[str, Callable[[float, float], bool]] = {
    "<": operator.lt,
    "<=": operator.le,
    ">": operator.gt,
    ">=": operator.ge,
    "==": operator.eq,
}


@dataclass(frozen=True, slots=True)
class Condition:
    feature: str
    op: str
    value: float

    def holds(self, f: Mapping[str, float]) -> bool:
        return _OPS[self.op](f[self.feature], self.value)


@dataclass(frozen=True, slots=True)
class Rule:
    id: str
    conditions: tuple[Condition, ...]
    decision: Decision

    @classmethod
    def parse(cls, rule_id: str, expr: str, decision: Decision) -> Rule:
        """'new_device == 1 and amount_ratio >= 5' -> Rule. Gramática mínima: solo AND de comparaciones."""
        conditions = []
        for part in expr.split(" and "):
            feature, op, value = part.split()
            if feature not in FEATURES:
                raise ValueError(f"Feature desconocida: {feature!r}")
            if op not in _OPS:
                raise ValueError(f"Operador no permitido: {op!r}")
            conditions.append(Condition(feature, op, float(value)))
        return cls(rule_id, tuple(conditions), decision)

    def matches(self, f: Mapping[str, float]) -> bool:
        return all(c.holds(f) for c in self.conditions)


DEFAULT_RULES = (
    Rule.parse("viaje-imposible", "speed_kmh > 900 and km_from_last > 100", Decision.REVIEW),
    Rule.parse("rafaga", "tx_1m >= 5", Decision.REVIEW),
    Rule.parse(
        "toma-de-cuenta", "new_device == 1 and new_payee == 1 and amount_ratio >= 5", Decision.STEP_UP
    ),
    Rule.parse(
        "llave-recien-creada", "new_payee == 1 and key_age_h < 24 and amount >= 1000000", Decision.STEP_UP
    ),
    Rule.parse("destino-mula", "receiver_fan_in_1h >= 6", Decision.REVIEW),
)
