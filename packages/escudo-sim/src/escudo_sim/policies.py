"""Políticas de línea base y cómo se traduce una decisión en "dinero bloqueado"."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence

from escudo_domain import DEFAULT_RULES, Decision, Rule
from escudo_sim.simulator import Labeled, Scenario

Policy = Callable[[Mapping[str, float]], Decision]


def no_protection(_: Mapping[str, float]) -> Decision:
    return Decision.APPROVE


def naive_amount_rule(limit: int = 3_000_000) -> Policy:
    """Lo que haría un sistema sin diseño: revisar todo lo que supere un monto."""

    def policy(f: Mapping[str, float]) -> Decision:
        return Decision.REVIEW if f["amount"] >= limit else Decision.APPROVE

    return policy


def rules_only(rules: Sequence[Rule] = DEFAULT_RULES) -> Policy:
    def policy(f: Mapping[str, float]) -> Decision:
        return max([Decision.APPROVE, *(r.decision for r in rules if r.matches(f))])

    return policy


def blocked(decision: Decision, event: Labeled) -> bool:
    """REVIEW/DECLINE detienen el pago. STEP_UP lo detiene solo si el titular real rechaza: la víctima de una
    estafa APP confirma (está siendo engañada), por eso esas estafas solo se frenan mirando el destino."""
    if decision >= Decision.REVIEW:
        return True
    if decision is Decision.STEP_UP:
        return event.is_fraud and event.scenario is not Scenario.APP_SCAM
    return False
