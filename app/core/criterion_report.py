from dataclasses import dataclass, field

from app.core.result import RuleResult


@dataclass(slots=True)
class CriterionReport:
    """
    Aggregates the results of several rules that belong to the same
    investment criterion.
    """

    name: str

    results: list[RuleResult] = field(default_factory=list)

    @property
    def score(self) -> float:
        if not self.results:
            return 0.0

        return sum(r.score for r in self.results) / len(self.results)

    @property
    def passed(self) -> bool:
        return all(
            r.passed or not r.blocker
            for r in self.results
        )