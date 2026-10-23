"""Dominio de Escudo. Solo biblioteca estándar: el mismo código decide en el servidor y en Pyodide."""

from escudo_domain.events import Decision, Transfer
from escudo_domain.features import FEATURES, FeatureExtractor, haversine_km
from escudo_domain.graph import UnionFind, mule_rings, pass_through_accounts
from escudo_domain.metrics import Outcome, evaluate, percentile
from escudo_domain.model import LogisticModel, Thresholds, Verdict, decide
from escudo_domain.rules import DEFAULT_RULES, Condition, Rule
from escudo_domain.thresholds import best_threshold
from escudo_domain.windows import SlidingWindow, WindowStats

__all__ = [
    "DEFAULT_RULES",
    "FEATURES",
    "Condition",
    "Decision",
    "FeatureExtractor",
    "LogisticModel",
    "Outcome",
    "Rule",
    "SlidingWindow",
    "Thresholds",
    "Transfer",
    "UnionFind",
    "Verdict",
    "WindowStats",
    "best_threshold",
    "decide",
    "evaluate",
    "haversine_km",
    "mule_rings",
    "pass_through_accounts",
    "percentile",
]
