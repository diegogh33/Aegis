from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class MarketData:
    """
    Live market data for an option contract.
    """

    # Underlying
    underlying_price: Decimal | None

    # Prices
    bid: Decimal | None
    ask: Decimal | None
    last: Decimal | None
    mark: Decimal | None

    # Greeks
    delta: Decimal | None
    gamma: Decimal | None
    theta: Decimal | None
    vega: Decimal | None
    implied_volatility: Decimal | None

    # Liquidity
    volume: float | None
    open_interest: int | None