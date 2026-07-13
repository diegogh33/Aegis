from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(slots=True, frozen=True)
class MarketData:
    """
    Real-time market data for an option contract.
    """

    bid: Decimal | None

    ask: Decimal | None

    last: Decimal | None

    mark: Decimal | None

    delta: Decimal | None

    gamma: Decimal | None

    theta: Decimal | None

    vega: Decimal | None

    implied_volatility: Decimal | None

    volume: int | None

    open_interest: int | None