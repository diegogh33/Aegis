from dataclasses import dataclass

from app.core.types import Score


@dataclass(slots=True)
class RuleResult:
    """
    Result returned after evaluating a business rule.
    """

    rule_id: str

    passed: bool

    score: Score

    message: str

    blocker: bool = False