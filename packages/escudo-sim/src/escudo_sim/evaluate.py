"""Evalúa políticas sobre el día 1 del simulador y imprime la tabla de línea base.

Uso: `uv run escudo-baseline --seed 2`
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass

from escudo_domain import Decision, FeatureExtractor, Outcome, evaluate
from escudo_sim.policies import Policy, blocked, naive_amount_rule, no_protection, rules_only
from escudo_sim.simulator import DAY, Labeled, Scenario, simulate


def featurize_evaluation_day(events: Sequence[Labeled]) -> list[tuple[dict[str, float], Labeled]]:
    """Procesa los 2 días en orden (el día 0 alimenta la historia) y devuelve solo el día 1."""
    fe = FeatureExtractor()
    pairs = [(fe.extract(e.transfer), e) for e in events]
    return [(f, e) for f, e in pairs if e.transfer.ts >= DAY]


@dataclass(frozen=True, slots=True)
class PolicyResult:
    metrics: dict[str, float]
    step_ups_per_1000_legit: float
    recall_by_scenario: dict[Scenario, float]


def run_policy(policy: Policy, day: Sequence[tuple[dict[str, float], Labeled]]) -> PolicyResult:
    outcomes: list[Outcome] = []
    step_ups = 0
    by_scenario: defaultdict[Scenario, list[bool]] = defaultdict(list)
    for f, e in day:
        decision = policy(f)
        was_blocked = blocked(decision, e)
        outcomes.append(Outcome(e.is_fraud, e.transfer.amount, was_blocked))
        step_ups += not e.is_fraud and decision is Decision.STEP_UP
        if e.is_fraud:
            by_scenario[e.scenario].append(was_blocked)
    legit = sum(1 for _, e in day if not e.is_fraud)
    return PolicyResult(
        metrics=evaluate(outcomes),
        step_ups_per_1000_legit=1000 * step_ups / legit if legit else 0.0,
        recall_by_scenario={s: sum(v) / len(v) for s, v in sorted(by_scenario.items())},
    )


BASELINES: dict[str, Policy] = {
    "sin protección": no_protection,
    "regla ingenua (monto >= 3 M)": naive_amount_rule(),
    "solo reglas Escudo": rules_only(),
}


def run_baselines(
    seed: int, n_customers: int = 1500
) -> tuple[list[tuple[dict[str, float], Labeled]], dict[str, PolicyResult]]:
    day = featurize_evaluation_day(simulate(seed, n_customers))
    return day, {name: run_policy(policy, day) for name, policy in BASELINES.items()}


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Línea base de Escudo sobre el simulador con semilla")
    parser.add_argument("--seed", type=int, default=2)
    parser.add_argument("--customers", type=int, default=1500)
    args = parser.parse_args(argv)
    day, results = run_baselines(args.seed, args.customers)
    fraud = [e for _, e in day if e.is_fraud]
    fraud_money = sum(e.transfer.amount for e in fraud) / 1e6
    print(
        f"Semilla {args.seed}: {len(day):,} transferencias en el día de evaluación, "
        f"{len(fraud)} fraudulentas, {fraud_money:.1f} M COP en fraude\n"
    )
    header = ("política", "dinero detenido", "recall", "precisión", "bloqueos legít./1000")
    print(f"{header[0]:30s} {header[1]:>16s} {header[2]:>8s} {header[3]:>10s} {header[4]:>21s}")
    for name, r in results.items():
        m = r.metrics
        print(
            f"{name:30s} {m['money_recall']:>16.1%} {m['recall']:>8.1%} {m['precision']:>10.1%} "
            f"{m['fp_per_1000_legit']:>21.1f}"
        )


if __name__ == "__main__":
    main()
