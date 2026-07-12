from decimal import Decimal

from app.core.result import RuleResult
from app.core.rule_status import RuleStatus
from app.rules.base import Rule


class DeltaRule(Rule):
    """
    Evaluates whether the option delta is within the acceptable range.
    """

    id = "DELTA"

    name = "Delta"

    blocker = False

    def __init__(
        self,
        pass_min: float = -0.25,
        pass_max: float = -0.15,
        warning_min: float = -0.35,
    ):
        self.pass_min = pass_min
        self.pass_max = pass_max
        self.warning_min = warning_min

    def evaluate(self, candidate):

        delta = candidate.option.delta

        if delta is None:
            return RuleResult(
                rule_id=self.id,
                status=RuleStatus.FAIL,
                score=Decimal("0"),
                message="Delta unavailable",
            )

        if self.pass_min <= delta <= self.pass_max:
            return RuleResult(
                rule_id=self.id,
                status=RuleStatus.PASS,
                score=Decimal("10"),
                message=f"Delta {delta:.2f} is inside the preferred range.",
            )

        if self.warning_min <= delta < self.pass_min:
            return RuleResult(
                rule_id=self.id,
                status=RuleStatus.WARNING,
                score=Decimal("6"),
                message=f"Delta {delta:.2f} is acceptable but more aggressive than preferred.",
            )

        return RuleResult(
            rule_id=self.id,
            status=RuleStatus.FAIL,
            score=Decimal("0"),
            message=f"Delta {delta:.2f} is outside the allowed range.",
        )