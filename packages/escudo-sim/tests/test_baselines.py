"""Regresión: el simulador del repo debe reproducir la tabla de línea base publicada en la propuesta (§13).

Si cambias el simulador a propósito, actualiza estas cifras Y la propuesta en el mismo commit.
"""

import pytest

from escudo_sim import Labeled, PolicyResult, run_baselines

type Baseline = tuple[list[tuple[dict[str, float], Labeled]], dict[str, PolicyResult]]


@pytest.fixture(scope="module")
def baseline() -> Baseline:
    return run_baselines(seed=2)


def pct(x: float) -> float:
    return round(100 * x, 1)


def test_evaluation_day_shape(baseline: Baseline) -> None:
    day, _ = baseline
    fraud = [e for _, e in day if e.is_fraud]
    assert len(day) == 6526
    assert len(fraud) == 231
    assert round(sum(e.transfer.amount for e in fraud) / 1e6, 1) == 156.4


@pytest.mark.parametrize(
    ("policy", "expected"),
    [
        ("sin protección", (0.0, 0.0, 0.0, 0.0)),
        ("regla ingenua (monto >= 3 M)", (22.9, 3.0, 31.8, 2.4)),
        ("solo reglas Escudo", (44.2, 35.1, 47.4, 14.3)),
    ],
)
def test_published_baselines(
    baseline: Baseline, policy: str, expected: tuple[float, float, float, float]
) -> None:
    """(dinero detenido %, recall %, precisión %, bloqueos legítimos por 1000)."""
    m = baseline[1][policy].metrics
    got = (pct(m["money_recall"]), pct(m["recall"]), pct(m["precision"]), round(m["fp_per_1000_legit"], 1))
    assert got == expected


def test_cli_prints_the_baseline_table(capsys: pytest.CaptureFixture[str]) -> None:
    from escudo_sim.evaluate import main

    main(["--seed", "2"])
    out = capsys.readouterr().out
    assert "6,526 transferencias" in out and "231 fraudulentas" in out
    assert "solo reglas Escudo" in out and "44.2%" in out
