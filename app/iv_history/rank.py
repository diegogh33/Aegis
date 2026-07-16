from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.iv_history.repository import IVSnapshot


@dataclass(frozen=True)
class IVRankResult:
    """
    Result of an IV Rank calculation attempt.

    `rank` is None when there isn't enough history yet - callers
    (IVRankRule) should treat that as "can't evaluate", not as a
    failing rank of 0.
    """

    rank: Decimal | None
    days_of_history: int
    minimum_days_required: int

    @property
    def has_enough_history(self) -> bool:
        return self.days_of_history >= self.minimum_days_required


def calculate_iv_rank(
    current_iv: Decimal,
    history: list[IVSnapshot],
    minimum_days_required: int = 90,
) -> IVRankResult:
    """
    IV Rank = (current IV - min IV in history) / (max IV - min IV in
    history), expressed as a 0-100 value.

    Returns rank=None if there isn't at least minimum_days_required
    days of history yet, or if every recorded IV in the window is
    identical (max == min, so the ratio is undefined) - both are
    "not enough signal to rank", not a 0 or 100.
    """

    days_of_history = len(history)

    if days_of_history < minimum_days_required:
        return IVRankResult(
            rank=None,
            days_of_history=days_of_history,
            minimum_days_required=minimum_days_required,
        )

    ivs = [snapshot.implied_volatility for snapshot in history]

    iv_min = min(ivs)
    iv_max = max(ivs)

    if iv_max == iv_min:
        return IVRankResult(
            rank=None,
            days_of_history=days_of_history,
            minimum_days_required=minimum_days_required,
        )

    rank = (current_iv - iv_min) / (iv_max - iv_min) * Decimal("100")

    # Clamp to [0, 100]: current_iv might fall outside the historical
    # min/max if it's the same-day snapshot already included in
    # `history` with a slightly different value, or due to rounding.
    rank = max(Decimal("0"), min(Decimal("100"), rank))

    return IVRankResult(
        rank=rank,
        days_of_history=days_of_history,
        minimum_days_required=minimum_days_required,
    )
