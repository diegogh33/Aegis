from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(slots=True, frozen=True)
class OptionMetrics:
    """
    Calculated metrics for an option contract.

    This model contains only derived values.
    No calculations should be implemented here.
    """

    # Returns

    premium: Decimal

    premium_percentage: Decimal

    annualized_return: Decimal

    return_on_cash: Decimal

    # Risk

    break_even: Decimal

    distance_to_strike_pct: Decimal

    margin_of_safety_pct: Decimal

    # Liquidity

    bid_ask_spread: Decimal

    bid_ask_spread_pct: Decimal

    liquidity_score: Decimal

    # Volatility

    implied_volatility: Decimal | None

    # Time

    days_to_expiration: int