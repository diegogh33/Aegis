from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class RuleStatus(str, Enum):
    """
    Result of evaluating a rule.
    """

    PASSED = "passed"

    FAILED = "failed"

    WARNING = "warning"

    NOT_APPLICABLE = "not_applicable"


@dataclass(slots=True, frozen=True)
class RuleResult:
    """
    Result of evaluating a single investment rule.
    """

    name: str

    status: RuleStatus

    explanation: str

    actual_value: str | None = None

    expected_value: str | None = None

    weight: int = 0

    score: int = 0

    blocking: bool = False