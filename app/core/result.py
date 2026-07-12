from dataclasses import dataclass


@dataclass(slots=True)
class RuleResult:

    rule_id: str

    passed: bool

    score: float

    message: str