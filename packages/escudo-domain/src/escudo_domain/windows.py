"""Ventana deslizante por tiempo de evento.

Supuesto: el tiempo de una misma cuenta llega en orden (partición por cuenta en el bus de eventos, o el
sorted set de Redis en el camino síncrono).
"""

from __future__ import annotations

from collections import Counter, deque
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class WindowStats:
    count: int
    total: int
    distinct: int


class SlidingWindow:
    """Conteo, suma y contrapartes distintas en los últimos `span` segundos. O(1) amortizado."""

    def __init__(self, span: float) -> None:
        self.span = span
        self._events: deque[tuple[float, int, str]] = deque()
        self._total = 0
        self._distinct: Counter[str] = Counter()

    def add(self, ts: float, amount: int, counterparty: str) -> None:
        self._expire(ts)
        self._events.append((ts, amount, counterparty))
        self._total += amount
        self._distinct[counterparty] += 1

    def snapshot(self, now: float) -> WindowStats:
        self._expire(now)
        return WindowStats(len(self._events), self._total, len(self._distinct))

    def _expire(self, now: float) -> None:
        limit = now - self.span
        while self._events and self._events[0][0] <= limit:
            _, amount, cp = self._events.popleft()
            self._total -= amount
            self._distinct[cp] -= 1
            if not self._distinct[cp]:
                del self._distinct[cp]
