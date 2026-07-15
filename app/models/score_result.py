from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScoreResult:

    delta: float
    spread: float
    volume: float
    annualized_return: float

    @property
    def total(self) -> float:

        return round(
            self.delta
            + self.spread
            + self.volume
            + self.annualized_return,
            2,
        )