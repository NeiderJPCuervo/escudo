import math

import pytest

from escudo_domain import DEFAULT_RULES, FEATURES, FeatureExtractor, Transfer, haversine_km

BOGOTA = (4.7110, -74.0721)
MEDELLIN = (6.2442, -75.5812)


def tx(
    txn_id: str,
    ts: float,
    sender: str,
    receiver: str,
    amount: int,
    device: str,
    where: tuple[float, float] = BOGOTA,
    key_age_h: float = 999,
) -> Transfer:
    return Transfer(txn_id, ts, sender, receiver, amount, device, where[0], where[1], key_age_h)


def test_haversine_known_distances() -> None:
    assert haversine_km(*BOGOTA, *MEDELLIN) == pytest.approx(238.7, abs=0.1)
    assert haversine_km(*BOGOTA, *BOGOTA) == 0.0
    assert haversine_km(0, 0, 0, 180) == pytest.approx(math.pi * 6371.0088)


def test_first_transfer_has_no_history() -> None:
    f = FeatureExtractor().extract(tx("a", 0, "c1", "p1", 100_000, "cel"))
    assert set(f) == FEATURES
    assert f["first_tx"] == 1.0
    assert f["new_device"] == f["new_payee"] == 0.0  # sin historia no hay "nuevo"
    assert f["amount_ratio"] == 1.0
    assert f["speed_kmh"] == 0.0


def test_account_takeover_signals() -> None:
    fe = FeatureExtractor()
    fe.extract(tx("a", 0, "c1", "p1", 100_000, "cel"))
    f = fe.extract(tx("b", 600, "c1", "p2", 900_000, "otro", MEDELLIN, key_age_h=3))
    assert f["new_device"] == 1.0 and f["new_payee"] == 1.0
    assert f["amount_ratio"] == 9.0
    assert 1300 < f["speed_kmh"] < 1500  # ~239 km en 10 min: viaje imposible
    assert [r.id for r in DEFAULT_RULES if r.matches(f)] == ["viaje-imposible", "toma-de-cuenta"]


def test_speed_uses_one_minute_floor() -> None:
    fe = FeatureExtractor()
    fe.extract(tx("a", 0, "c1", "p1", 1, "cel"))
    f = fe.extract(tx("b", 0, "c1", "p1", 1, "cel", MEDELLIN))  # mismo segundo: relojes desalineados
    assert f["speed_kmh"] == pytest.approx(haversine_km(*BOGOTA, *MEDELLIN) * 60)


def test_receiver_fan_in_triggers_mule_rule() -> None:
    fe = FeatureExtractor()
    f: dict[str, float] = {}
    for i in range(6):
        f = fe.extract(tx(f"t{i}", i * 60, f"victima{i}", "mula", 300_000, f"cel{i}"))
    assert f["receiver_fan_in_1h"] == 6.0
    assert "destino-mula" in [r.id for r in DEFAULT_RULES if r.matches(f)]


def test_ewma_tracks_habits() -> None:
    fe = FeatureExtractor(ewma_alpha=0.5)
    fe.extract(tx("a", 0, "c1", "p1", 100, "cel"))
    fe.extract(tx("b", 10, "c1", "p1", 300, "cel"))  # promedio: 0.5*100 + 0.5*300 = 200
    f = fe.extract(tx("c", 20, "c1", "p1", 400, "cel"))
    assert f["amount_ratio"] == 2.0
