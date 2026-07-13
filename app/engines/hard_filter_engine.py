from __future__ import annotations

from app.models.company import Company
from app.models.option_contract import OptionContract
from app.models.rule_result import RuleResult
from app.rules.base_rule import BaseRule
from app.rules.company.company_approved_rule import (
    CompanyApprovedRule,
)


class HardFilterEngine:
    """
    Executes all mandatory investment rules.

    If a blocking rule fails, the opportunity is rejected.
    """

    def __init__(self) -> None:

        self._rules: list[BaseRule] = [
            CompanyApprovedRule(),
        ]

    def evaluate(
        self,
        *,
        company: Company,
        option: OptionContract,
    ) -> list[RuleResult]:

        results: list[RuleResult] = []

        for rule in self._rules:
            results.append(
                rule.evaluate(
                    company=company,
                    option=option,
                )
            )

        return results