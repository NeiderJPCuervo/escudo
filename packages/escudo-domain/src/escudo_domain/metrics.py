"""Métricas de negocio: cuánto fraude se detiene y cuánto se molesta a los clientes legítimos."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass


def percentile(values: Sequence[float], q: float) -> float:
    """Percentil por interpolación lineal (como numpy por defecto)."""
    xs = sorted(values)
    pos = (len(xs) - 1) * q
    lo = int(pos)
    hi = min(lo + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (pos - lo)


@dataclass(frozen=True, slots=True)
class Outcome:
    is_fraud: bool
    amount: int
    blocked: bool  # REVIEW o DECLINE (STEP_UP cuenta como bloqueado si el cliente lo rechaza)


def evaluate(outcomes: Sequence[Outcome]) -> dict[str, float]:
    fraud = [o for o in outcomes if o.is_fraud]
    legit = [o for o in outcomes if not o.is_fraud]
    tp = sum(o.blocked for o in fraud)
    fp = sum(o.blocked for o in legit)
    money = sum(o.amount for o in fraud)
    return {
        "precision": tp / (tp + fp) if tp + fp else 0.0,
        "recall": tp / len(fraud) if fraud else 0.0,
        "money_recall": sum(o.amount for o in fraud if o.blocked) / money if money else 0.0,
        "fp_per_1000_legit": 1000 * fp / len(legit) if legit else 0.0,
    }
