from app.core.result import RuleResult
from app.models.investment_candidate import InvestmentCandidate
from app.rules.base import Rule


class RuleEngine:
    """
    Executes every registered rule against an investment candidate.
    """

    def __init__(self, rules: list[Rule]):
        self.rules = rules

    def evaluate(
        self,
        candidate: InvestmentCandidate,
    ) -> list[RuleResult]:
        return [
            rule.evaluate(candidate)
            for rule in self.rules
        ]