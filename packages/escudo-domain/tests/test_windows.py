from hypothesis import given
from hypothesis import strategies as st

from escudo_domain import SlidingWindow, WindowStats

# (salto de tiempo, monto, contraparte, fracción de la ventana que avanza el reloj antes de consultar)
steps = st.lists(
    st.tuples(
        st.sampled_from([0.0, 0.5, 1.0, 7.0, 30.0, 120.0, 4000.0]),
        st.integers(1, 100),
        st.sampled_from("abcde"),
        st.sampled_from([0.0, 0.5, 1.0]),
    ),
    min_size=1,
    max_size=60,
)


@given(span=st.sampled_from([1.0, 60.0, 3600.0]), steps=steps)
def test_window_matches_brute_force(span: float, steps: list[tuple[float, float, str, float]]) -> None:
    w = SlidingWindow(span)
    events: list[tuple[float, int, str]] = []
    clock = 0.0  # el tiempo por cuenta es monótono
    for gap, amount, cp, advance in steps:
        ts = clock + gap
        events.append((ts, int(amount), cp))
        w.add(ts, int(amount), cp)
        now = clock = ts + advance * span
        live = [e for e in events if e[0] > now - span]
        assert w.snapshot(now) == WindowStats(len(live), sum(e[1] for e in live), len({e[2] for e in live}))


def test_event_exactly_span_old_is_expired() -> None:
    w = SlidingWindow(60)
    w.add(0.0, 10, "a")
    assert w.snapshot(59.9) == WindowStats(1, 10, 1)
    assert w.snapshot(60.0) == WindowStats(0, 0, 0)  # ventana (now - span, now]


def test_distinct_counts_counterparties_not_events() -> None:
    w = SlidingWindow(60)
    for ts in (1.0, 2.0, 3.0):
        w.add(ts, 5, "misma")
    w.add(4.0, 5, "otra")
    assert w.snapshot(4.0) == WindowStats(4, 20, 2)
