import pytest

from escudo_domain import DEFAULT_RULES, FEATURES, Condition, Decision, Rule


def test_parse_builds_conditions() -> None:
    r = Rule.parse("x", "new_device == 1 and amount_ratio >= 5", Decision.STEP_UP)
    assert r.conditions == (Condition("new_device", "==", 1.0), Condition("amount_ratio", ">=", 5.0))
    assert r.decision is Decision.STEP_UP


def test_boundaries_are_inclusive_where_declared() -> None:
    r = Rule.parse("x", "new_device == 1 and amount_ratio >= 5", Decision.STEP_UP)
    assert r.matches({"new_device": 1.0, "amount_ratio": 5.0})
    assert not r.matches({"new_device": 1.0, "amount_ratio": 4.999})
    assert not r.matches({"new_device": 0.0, "amount_ratio": 50.0})


@pytest.mark.parametrize(
    "expr",
    [
        "amount ~ 3",  # operador desconocido
        "__import__('os') == 1",  # intento de inyección: no se ejecuta, se rechaza
        "monto >= 1",  # feature inexistente
        "amount >= 1 or tx_1m > 3",  # OR no está en la gramática
        "amount >=",  # incompleta
        "amount >= mucho",  # valor no numérico
    ],
)
def test_invalid_rules_are_rejected_at_load_time(expr: str) -> None:
    with pytest.raises(ValueError):
        Rule.parse("mala", expr, Decision.REVIEW)


def test_default_rules_only_use_known_features() -> None:
    assert {c.feature for r in DEFAULT_RULES for c in r.conditions} <= FEATURES
    assert len({r.id for r in DEFAULT_RULES}) == len(DEFAULT_RULES)
