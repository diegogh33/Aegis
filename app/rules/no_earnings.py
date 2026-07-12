from datetime import date

from app.core.result import RuleResult
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
                self.id,
                True,
                10,
                "No earnings date available"
            )

        days = (earnings - date.today()).days

        if days < self.minimum_days:
            return RuleResult(
                self.id,
                False,
                0,
                f"Earnings in {days} days",
                blocker=True
            )

        return RuleResult(
            self.id,
            True,
            10,
            f"Earnings in {days} days"
        )