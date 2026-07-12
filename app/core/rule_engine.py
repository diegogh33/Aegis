from app.core.result import RuleResult
from app.rules.base import Rule


class RuleEngine:

    def __init__(self, rules: list[Rule]):

        self.rules = rules

    def evaluate(self, candidate) -> list[RuleResult]:

        results = []

        for rule in self.rules:

            results.append(rule.evaluate(candidate))

        return results