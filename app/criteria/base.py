from __future__ import annotations

from abc import ABC

from app.core.criterion_report import CriterionReport
from app.models.investment_candidate import InvestmentCandidate
from app.rules.base import Rule


class Criterion(ABC):
    """
    A Criterion groups related business rules.
    """

    name: str

    def __init__(self, rules: list[Rule]):
        self.rules = rules

    def evaluate(
        self,
        candidate: InvestmentCandidate,
    ) -> CriterionReport:

        report = CriterionReport(name=self.name)

        for rule in self.rules:
            report.results.append(
                rule.evaluate(candidate)
            )

        return report