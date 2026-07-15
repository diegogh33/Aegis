from datetime import date
from decimal import Decimal

from app.config.settings import Settings
from app.core.result import RuleResult
from app.core.rule_status import RuleStatus
from app.rules.base import Rule


class NoUpcomingEarningsRule(Rule):
    """
    Rejects candidates whose next earnings date falls within
    minimum_days.

    Reads minimum_days from constitution.yaml
    (cash_secured_put.earnings.minimum_days) via Settings by default,
    following DTERule's pattern.
    """

    id = "NO_EARNINGS"

    name = "No Upcoming Earnings"

    blocker = True

    def __init__(
        self,
        minimum_days: int | None = None,
        settings: Settings | None = None,
    ):
        if minimum_days is None:

            settings = settings or Settings()

            minimum_days = settings.get(
                "cash_secured_put", "earnings", "minimum_days"
            )

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