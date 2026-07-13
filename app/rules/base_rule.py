from __future__ import annotations

from abc import ABC, abstractmethod

from app.models.company import Company
from app.models.option_contract import OptionContract
from app.models.rule_result import RuleResult


class BaseRule(ABC):
    """
    Base class for every investment rule.
    """

    @abstractmethod
    def evaluate(
        self,
        *,
        company: Company,
        option: OptionContract,
    ) -> RuleResult:
        ...