from __future__ import annotations

from dataclasses import dataclass

from app.models.option_contract import OptionContract
from app.models.score_result import ScoreResult


@dataclass(frozen=True)
class ScoredOption:
    """
    Option together with its detailed score.
    """

    option: OptionContract
    score: ScoreResult