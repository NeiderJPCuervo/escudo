import math

from hypothesis import given
from hypothesis import strategies as st

from escudo_domain import best_threshold

scored = st.lists(
    st.tuples(st.integers(0, 100).map(lambda x: x / 100), st.booleans(), st.integers(1, 1000)),
    max_size=40,
)


def brute_cost(data: list[tuple[float, bool, int]], t: float, fp_cost: int, review_cost: int) -> int:
    return (
        sum(a for s, y, a in data if y and s < t)
        + fp_cost * sum(1 for s, y, _ in data if not y and s >= t)
        + review_cost * sum(1 for s, _, _ in data if s >= t)
    )


@given(scored, st.integers(0, 50), st.integers(0, 20))
def test_best_threshold_is_optimal(
    data: list[tuple[float, bool, int]], fp_cost: int, review_cost: int
) -> None:
    t, cost = best_threshold(data, fp_cost, review_cost)
    candidates = [math.inf, *{s for s, _, _ in data}]
    assert cost == min(brute_cost(data, c, fp_cost, review_cost) for c in candidates)
    assert brute_cost(data, t, fp_cost, review_cost) == cost


def test_no_data_means_flag_nothing() -> None:
    assert best_threshold([], fp_cost=10, review_cost=1) == (math.inf, 0)


def test_expensive_friction_raises_the_threshold() -> None:
    data = [(0.9, True, 1000), (0.6, False, 50), (0.5, True, 100), (0.2, False, 10)]
    cheap, _ = best_threshold(data, fp_cost=1, review_cost=0)
    expensive, _ = best_threshold(data, fp_cost=10_000, review_cost=0)
    assert cheap == 0.5 and expensive == 0.9
