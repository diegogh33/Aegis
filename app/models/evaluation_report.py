from __future__ import annotations

from dataclasses import dataclass, field

from app.models.company import Company
from app.models.option_contract import OptionContract
from app.models.option_metrics import OptionMetrics
from app.models.rule_result import RuleResult


@dataclass(slots=True, frozen=True)
class EvaluationReport:
    """
    Final result of evaluating an investment opportunity.
    """

    company: Company

    option: OptionContract

    metrics: OptionMetrics

    score: int

    recommendation: str

    rule_results: list[RuleResult] = field(default_factory=list)

    notes: list[str] = field(default_factory=list)