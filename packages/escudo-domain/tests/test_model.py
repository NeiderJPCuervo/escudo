import json
import math

from hypothesis import given
from hypothesis import strategies as st

from escudo_domain import Decision, LogisticModel, Rule, Thresholds, decide

TH = Thresholds(step_up=0.5, review=0.8, decline=0.95)


def model(weight: float = 1.0, bias: float = 0.0) -> LogisticModel:
    return LogisticModel.from_json(
        json.dumps(
            {
                "version": "test",
                "bias": bias,
                "weights": {"tx_1m": weight, "new_payee": 0.5},
                "means": {"tx_1m": 1.0, "new_payee": 0.0},
                "stds": {"tx_1m": 2.0, "new_payee": 1.0},
            }
        )
    )


def test_score_is_sigmoid_of_bias_plus_contributions() -> None:
    m = model(weight=1.5, bias=-0.3)
    p, contrib = m.score({"tx_1m": 5.0, "new_payee": 1.0})
    assert contrib == {"tx_1m": 1.5 * (5.0 - 1.0) / 2.0, "new_payee": 0.5}
    assert math.isclose(p, 1 / (1 + math.exp(-(-0.3 + 3.0 + 0.5))))


def test_sigmoid_never_overflows() -> None:
    m = model(weight=1e6)
    assert m.score({"tx_1m": -1e6, "new_payee": 0.0})[0] == 0.0
    assert m.score({"tx_1m": 1e6, "new_payee": 0.0})[0] == 1.0


def test_rule_severity_wins_over_low_score() -> None:
    rule = Rule.parse("rafaga", "tx_1m >= 5", Decision.REVIEW)
    v = decide({"tx_1m": 5.0, "new_payee": 0.0}, [rule], model(weight=-10.0), TH)
    assert v.decision is Decision.REVIEW
    assert v.reasons[0] == "regla:rafaga"


def test_high_score_declines_and_explains() -> None:
    v = decide({"tx_1m": 20.0, "new_payee": 1.0}, [], model(weight=3.0), TH)
    assert v.decision is Decision.DECLINE
    assert v.reasons == ("modelo:tx_1m", "modelo:new_payee")  # ordenadas por contribución


@given(st.floats(-5, 5), st.floats(-5, 5))
def test_decision_is_monotonic_in_score(a: float, b: float) -> None:
    m = model(weight=1.0)
    lo, hi = sorted((a, b))
    f_lo, f_hi = {"tx_1m": 1.0 + 2 * lo, "new_payee": 0.0}, {"tx_1m": 1.0 + 2 * hi, "new_payee": 0.0}
    assert decide(f_lo, [], m, TH).decision <= decide(f_hi, [], m, TH).decision
