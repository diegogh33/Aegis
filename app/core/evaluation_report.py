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
    def max_score(self) -> Decimal:
        """
        The maximum score this report could have if every rule
        returned PASS. Each rule's own PASS score can differ (10 is
        the common case today), so this is computed per report rather
        than assumed as a fixed constant - it stays correct as rules
        are added, removed, or given different PASS values.
        """

        return Decimal(len(self.results)) * Decimal("10")

    @property
    def blockers(self) -> list[RuleResult]:
        return [
            result
            for result in self.results
            if result.blocker and not result.passed
        ]

    @property
    def recommendation(self) -> Recommendation:
        """
        STRONG_BUY/BUY thresholds are 90%/75% of max_score - not
        fixed absolute values. Regression note: this used to compare
        `score` (max 60 with the current 6 Constitution rules) against
        fixed thresholds of 90/75, which made STRONG_BUY and BUY
        mathematically unreachable for any candidate, approved or not.
        """

        if not self.passed:
            return Recommendation.REJECT

        if self.score >= self.max_score * Decimal("0.90"):
            return Recommendation.STRONG_BUY

        if self.score >= self.max_score * Decimal("0.75"):
            return Recommendation.BUY

        return Recommendation.WATCH