from __future__ import annotations

from abc import ABC, abstractmethod

from app.core.result import RuleResult
from app.models.investment_candidate import InvestmentCandidate


class Rule(ABC):
    """
    Base class for every business rule.
    """

    id: str

    name: str

    weight: float = 1.0

    blocker: bool = False

    @abstractmethod
    def evaluate(
        self,
        candidate: InvestmentCandidate,
    ) -> RuleResult:
        """
        Evaluates an investment candidate.
        """
        raise NotImplementedError