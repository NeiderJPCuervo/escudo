from hypothesis import given
from hypothesis import strategies as st

from escudo_domain import Outcome, evaluate, percentile


def test_percentile_interpolates_like_numpy() -> None:
    assert percentile([1, 2, 3, 4], 0.5) == 2.5
    assert percentile([5], 0.99) == 5
    assert percentile([10, 20], 0.25) == 12.5


@given(st.lists(st.floats(-1e6, 1e6), min_size=1, max_size=50), st.floats(0, 1), st.floats(0, 1))
def test_percentile_bounds_and_monotonicity(xs: list[float], q1: float, q2: float) -> None:
    lo, hi = sorted((q1, q2))
    assert percentile(xs, 0) == min(xs) and percentile(xs, 1) == max(xs)
    assert percentile(xs, lo) <= percentile(xs, hi) + 1e-9


def test_evaluate_business_metrics() -> None:
    ev = evaluate(
        [
            Outcome(True, 100, True),
            Outcome(True, 300, False),
            Outcome(False, 10, True),
            Outcome(False, 10, False),
        ]
    )
    assert ev == {"precision": 0.5, "recall": 0.5, "money_recall": 0.25, "fp_per_1000_legit": 500.0}


def test_evaluate_handles_empty_classes() -> None:
    assert evaluate([]) == {"precision": 0.0, "recall": 0.0, "money_recall": 0.0, "fp_per_1000_legit": 0.0}
