from __future__ import annotations

from app.models.company import Company
from app.models.option_contract import OptionContract
from app.models.rule_result import RuleResult, RuleStatus
from app.rules.base_rule import BaseRule


class CompanyApprovedRule(BaseRule):
    """
    Checks whether the company belongs to the approved investment universe.

    For now this rule always passes.

    Later it will validate the company using the
    Fundamental Engine.
    """

    def evaluate(
        self,
        *,
        company: Company,
        option: OptionContract,
    ) -> RuleResult:

        return RuleResult(
            name="Company approved",
            status=RuleStatus.PASSED,
            explanation=(
                "Company belongs to the approved investment universe."
            ),
            blocking=True,
        )