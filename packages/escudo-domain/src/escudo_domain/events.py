"""Tipos base: la transferencia que se decide y las decisiones posibles."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum


class Decision(IntEnum):  # el valor numérico es la severidad: max() combina decisiones
    APPROVE = 0
    STEP_UP = 1  # pedir confirmación al cliente
    REVIEW = 2  # retener y enviar a un analista
    DECLINE = 3


@dataclass(frozen=True, slots=True)
class Transfer:
    txn_id: str
    ts: float  # epoch en segundos (UTC)
    sender: str  # cuenta origen
    receiver: str  # cuenta destino (llave ya resuelta)
    amount: int  # pesos colombianos
    device: str
    lat: float
    lon: float
    receiver_key_age_h: float  # antigüedad de la llave destino
