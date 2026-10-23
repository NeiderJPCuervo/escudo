"""Análisis asíncrono de grafo: cuentas mula (reciben de muchos y reenvían casi todo) y sus anillos."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence

from escudo_domain.events import Transfer


def pass_through_accounts(
    transfers: Sequence[Transfer], window_s: float = 3600, min_senders: int = 5, min_ratio: float = 0.8
) -> set[str]:
    """Cuentas que reciben de muchos remitentes distintos y reenvían casi todo dentro de la ventana."""
    inflow: defaultdict[str, list[Transfer]] = defaultdict(list)
    outflow: defaultdict[str, list[Transfer]] = defaultdict(list)
    for t in transfers:
        inflow[t.receiver].append(t)
        outflow[t.sender].append(t)
    mules: set[str] = set()
    for acct, ins in inflow.items():
        if len({t.sender for t in ins}) < min_senders:
            continue
        start = min(t.ts for t in ins)
        received = sum(t.amount for t in ins)
        forwarded = sum(t.amount for t in outflow.get(acct, ()) if start <= t.ts <= start + window_s)
        if forwarded >= min_ratio * received:
            mules.add(acct)
    return mules


class UnionFind:
    def __init__(self) -> None:
        self._parent: dict[str, str] = {}

    def find(self, x: str) -> str:
        self._parent.setdefault(x, x)
        while self._parent[x] != x:
            self._parent[x] = self._parent[self._parent[x]]  # compresión de camino (halving)
            x = self._parent[x]
        return x

    def union(self, a: str, b: str) -> None:
        self._parent[self.find(a)] = self.find(b)

    def groups(self) -> list[set[str]]:
        out: defaultdict[str, set[str]] = defaultdict(set)
        for x in self._parent:
            out[self.find(x)].add(x)
        return list(out.values())


def mule_rings(transfers: Sequence[Transfer], mules: set[str]) -> list[set[str]]:
    """Agrupa mulas conectadas entre sí o que alimentan a la misma cuenta colectora."""
    feeders: defaultdict[str, set[str]] = defaultdict(set)
    for t in transfers:
        if t.sender in mules:
            feeders[t.receiver].add(t.sender)
    uf = UnionFind()
    for t in transfers:
        if t.sender in mules and (t.receiver in mules or len(feeders[t.receiver]) >= 2):
            uf.union(t.sender, t.receiver)
    return [g for g in uf.groups() if len(g & mules) >= 2]
