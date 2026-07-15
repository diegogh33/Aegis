from __future__ import annotations

from decimal import Decimal

from app.core.result import RuleResult
from app.core.rule_status import RuleStatus
from app.rules.base import Rule


class CompanyApprovedRule(Rule):
    """
    Checks whether the company belongs to the approved investment universe.

    Approval is driven by InvestmentThesis.approved, which reflects a
    conscious decision (e.g. after fundamental analysis) that this company
    is eligible for options income strategies.
    """

    id = "COMPANY_APPROVED"

    name = "Company approved"

    blocker = True

    def evaluate(self, candidate):

        if candidate.thesis.approved:
            return RuleResult(
                rule_id=self.id,
                status=RuleStatus.PASS,
                score=Decimal("10"),
                message="Company belongs to the approved investment universe.",
            )

        return RuleResult(
            rule_id=self.id,
            status=RuleStatus.FAIL,
            score=Decimal("0"),
            message="Company is not in the approved investment universe.",
            blocker=True,
        )
