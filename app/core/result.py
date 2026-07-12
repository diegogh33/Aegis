from dataclasses import dataclass

from app.core.rule_status import RuleStatus
from app.core.types import Score


@dataclass(slots=True)
class RuleResult:
    """
    Result returned after evaluating a business rule.
    """

    rule_id: str

    status: RuleStatus

    score: Score

    message: str

    blocker: bool = False

    @property
    def passed(self) -> bool:
        return self.status is RuleStatus.PASS

    @property
    def warning(self) -> bool:
        return self.status is RuleStatus.WARNING

    @property
    def failed(self) -> bool:
        return self.status is RuleStatus.FAIL