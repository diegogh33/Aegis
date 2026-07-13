from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(slots=True, frozen=True)
class OptionContract:
    """
    Represents an option contract within the Aegis domain.

    This model is provider-agnostic. Any market data provider
    (Alpha Vantage, IBKR, Polygon, etc.) must map its own data
    into this structure.
    """

    # Underlying
    underlying: str

    # Contract
    option_type: str  # "put" | "call"

    expiration: date

    strike: Decimal

    # Prices
    bid: Decimal

    ask: Decimal

    last: Decimal | None

    mark: Decimal

    # Greeks
    delta: Decimal | None

    gamma: Decimal | None

    theta: Decimal | None

    vega: Decimal | None

    implied_volatility: Decimal | None

    # Liquidity
    volume: int

    open_interest: int