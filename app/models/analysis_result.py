from __future__ import annotations

from dataclasses import dataclass, field

from app.models.company import Company
from app.models.rejected_contract import RejectedContract
from app.models.scored_option import ScoredOption


@dataclass(frozen=True)
class AnalysisResult:
    """
    Final result returned by AnalysisService.
    """

    company: Company
    contracts: list[ScoredOption]
    rejected: list[RejectedContract] = field(default_factory=list)