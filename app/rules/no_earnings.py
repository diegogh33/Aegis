from datetime import date
from decimal import Decimal

from app.core.result import RuleResult
from app.core.rule_status import RuleStatus
from app.rules.base import Rule


class NoUpcomingEarningsRule(Rule):

    id = "NO_EARNINGS"

    name = "No Upcoming Earnings"

    blocker = True

    def __init__(self, minimum_days: int = 14):
        self.minimum_days = minimum_days

    def evaluate(self, candidate):

        earnings = candidate.company.next_earnings

        if earnings is None:
            return RuleResult(
                rule_id=self.id,
                status=RuleStatus.PASS,
                score=Decimal("10"),
                message="No earnings date available",
            )

        days = (earnings - date.today()).days

        if days < self.minimum_days:
            return RuleResult(
                rule_id=self.id,
                status=RuleStatus.FAIL,
                score=Decimal("0"),
                message=f"Earnings in {days} days",
                blocker=True,
            )

        return RuleResult(
            rule_id=self.id,
            status=RuleStatus.PASS,
            score=Decimal("10"),
            message=f"Earnings in {days} days",
        )