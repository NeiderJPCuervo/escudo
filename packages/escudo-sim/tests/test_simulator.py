from collections import Counter

import pytest

from escudo_sim import DAY, Labeled, Scenario, simulate


@pytest.fixture(scope="module")
def events() -> list[Labeled]:
    return simulate(seed=7, n_customers=300)


def test_same_seed_same_world() -> None:
    assert simulate(seed=3, n_customers=250) == simulate(seed=3, n_customers=250)


def test_different_seed_different_world() -> None:
    a = [e.transfer for e in simulate(seed=3, n_customers=250)]
    b = [e.transfer for e in simulate(seed=4, n_customers=250)]
    assert a != b


def test_too_few_customers_fails_with_clear_message() -> None:
    with pytest.raises(ValueError, match="n_customers debe ser >= 200"):
        simulate(seed=1, n_customers=199)


def test_events_are_sorted_by_time(events: list[Labeled]) -> None:
    ts = [e.transfer.ts for e in events]
    assert ts == sorted(ts)


def test_labels_are_consistent(events: list[Labeled]) -> None:
    for e in events:
        assert e.is_fraud == (e.scenario is not Scenario.LEGIT)
        assert e.transfer.amount >= 0


def test_attacks_only_happen_on_evaluation_day(events: list[Labeled]) -> None:
    assert all(e.transfer.ts >= DAY for e in events if e.is_fraud)


def test_every_attack_scenario_is_present(events: list[Labeled]) -> None:
    counts = Counter(e.scenario for e in events)
    assert set(counts) == set(Scenario)
    assert counts[Scenario.MULE_OUT] == 15  # 5 anillos x 3 mulas
    assert counts[Scenario.TRAVEL] == 10
    assert 25 <= counts[Scenario.ATO] <= 75  # 25 víctimas, 1 a 3 envíos cada una
    assert 50 <= counts[Scenario.BURST] <= 80  # 10 víctimas, 5 a 8 envíos cada una


def test_simulation_includes_hard_legit_cases(events: list[Labeled]) -> None:
    legit = [e.transfer for e in events if not e.is_fraud]
    assert any(t.receiver_key_age_h < 48 for t in legit)  # llaves nuevas legítimas
    assert any("-nuevo-" in t.device for t in legit)  # cambios de celular
    assert sum(t.amount >= 3_000_000 for t in legit) > 0  # compras grandes ocasionales
