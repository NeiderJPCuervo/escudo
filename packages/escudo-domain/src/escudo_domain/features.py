"""Features en tiempo de decisión: lo que se sabía de la cuenta ANTES de aprobar la transferencia."""

from __future__ import annotations

from math import asin, cos, log10, radians, sin, sqrt

from escudo_domain.events import Transfer
from escudo_domain.windows import SlidingWindow


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = radians(lat1), radians(lat2)
    a = sin((p2 - p1) / 2) ** 2 + cos(p1) * cos(p2) * sin(radians(lon2 - lon1) / 2) ** 2
    return 2 * 6371.0088 * asin(sqrt(a))


FEATURES = frozenset(
    {
        "amount",
        "amount_log",
        "amount_ratio",
        "first_tx",
        "new_device",
        "new_payee",
        "tx_1m",
        "sum_1h",
        "payees_1h",
        "km_from_last",
        "speed_kmh",
        "key_age_h",
        "receiver_fan_in_1h",
    }
)


class _SenderState:
    __slots__ = ("avg_amount", "devices", "last", "n", "payees", "w1h", "w1m")

    def __init__(self) -> None:
        self.w1m, self.w1h = SlidingWindow(60), SlidingWindow(3600)
        self.devices: set[str] = set()
        self.payees: set[str] = set()
        self.last: Transfer | None = None
        self.avg_amount = 0.0
        self.n = 0


class FeatureExtractor:
    """Estado por cuenta. Las features describen lo que se sabía ANTES de aprobar la transferencia."""

    def __init__(self, ewma_alpha: float = 0.1) -> None:
        self._alpha = ewma_alpha
        self._senders: dict[str, _SenderState] = {}
        self._inbound: dict[str, SlidingWindow] = {}

    def extract(self, t: Transfer) -> dict[str, float]:
        s = self._senders.setdefault(t.sender, _SenderState())
        inbound = self._inbound.setdefault(t.receiver, SlidingWindow(3600))
        s.w1m.add(t.ts, t.amount, t.receiver)
        s.w1h.add(t.ts, t.amount, t.receiver)
        inbound.add(t.ts, t.amount, t.sender)
        km = speed = 0.0
        if s.last is not None:
            km = haversine_km(s.last.lat, s.last.lon, t.lat, t.lon)
            speed = km / max((t.ts - s.last.ts) / 3600, 1 / 60)  # mínimo 1 min: evita dividir por ~0
        f = {
            "amount": float(t.amount),
            "amount_log": log10(max(t.amount, 1)),
            "amount_ratio": t.amount / s.avg_amount if s.n else 1.0,
            "first_tx": float(s.n == 0),
            "new_device": float(s.n > 0 and t.device not in s.devices),
            "new_payee": float(s.n > 0 and t.receiver not in s.payees),
            "tx_1m": float(s.w1m.snapshot(t.ts).count),
            "sum_1h": float(s.w1h.snapshot(t.ts).total),
            "payees_1h": float(s.w1h.snapshot(t.ts).distinct),
            "km_from_last": km,
            "speed_kmh": speed,
            "key_age_h": min(t.receiver_key_age_h, 720.0),
            "receiver_fan_in_1h": float(inbound.snapshot(t.ts).distinct),
        }
        s.devices.add(t.device)
        s.payees.add(t.receiver)
        s.avg_amount = t.amount if s.n == 0 else (1 - self._alpha) * s.avg_amount + self._alpha * t.amount
        s.n += 1
        s.last = t
        return f
