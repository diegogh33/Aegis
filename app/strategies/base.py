from __future__ import annotations

from abc import ABC

from app.core.evaluation_report import EvaluationReport
from app.core.rule_engine import RuleEngine
from app.models.investment_candidate import InvestmentCandidate
from app.rules.base import Rule


class Strategy(ABC):
    """
    Base class for every investment strategy.
    """

    def __init__(self, rules: list[Rule]):
        self._engine = RuleEngine(rules)

    def evaluate(
        self,
        candidate: InvestmentCandidate,
    ) -> EvaluationReport:
        return self._engine.evaluate(candidate)