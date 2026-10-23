"""Umbral óptimo por costo de negocio (no por accuracy ni F1)."""

from __future__ import annotations

from collections.abc import Sequence


def best_threshold(
    scored: Sequence[tuple[float, bool, int]], fp_cost: int, review_cost: int
) -> tuple[float, int]:
    """Umbral t (se marca si score >= t) que minimiza: fraude no detenido + fricción + costo de revisión.

    `scored` = (score, es_fraude, monto). O(n log n): un barrido sobre los puntajes ordenados.
    """
    items = sorted(scored, key=lambda x: x[0], reverse=True)
    lost = sum(a for _, y, a in items if y)  # no marcar nada: se pierde todo el fraude
    best_t, best_cost = float("inf"), lost
    false_pos = 0
    for i, (s, is_fraud, amount) in enumerate(items):
        if is_fraud:
            lost -= amount
        else:
            false_pos += 1
        if i + 1 < len(items) and items[i + 1][0] == s:
            continue  # empates: el umbral no puede separarlos
        cost = lost + false_pos * fp_cost + (i + 1) * review_cost
        if cost < best_cost:
            best_t, best_cost = s, cost
    return best_t, best_cost
