from dataclasses import dataclass, field
from decimal import Decimal

from app.core.recommendation import Recommendation
from app.core.result import RuleResult


@dataclass(slots=True)
class EvaluationReport:
    """
    Final report returned by the RuleEngine.
    """

    results: list[RuleResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not any(
            result.blocker and not result.passed
            for result in self.results
        )

    @property
    def score(self) -> Decimal:
        return sum(
            (result.score for result in self.results),
            start=Decimal("0"),
        )

    @property
    def blockers(self) -> list[RuleResult]:
        return [
            result
            for result in self.results
            if result.blocker and not result.passed
        ]

    @property
    def recommendation(self) -> Recommendation:

        if not self.passed:
            return Recommendation.REJECT

        if self.score >= Decimal("90"):
            return Recommendation.STRONG_BUY

        if self.score >= Decimal("75"):
            return Recommendation.BUY

        return Recommendation.WATCH