from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(slots=True, frozen=True)
class OptionContract:
    """
    Provider-agnostic option contract.

    This is the only option model used inside Aegis.
    Any provider (IBKR, Polygon, Tradier, etc.) must map
    its own data into this model.
    """

    # ------------------------------------------------------------------
    # Underlying
    # ------------------------------------------------------------------

    underlying: str

    # ------------------------------------------------------------------
    # Contract
    # ------------------------------------------------------------------

    local_symbol: str

    con_id: int

    option_type: str  # "put" | "call"

    expiration: date

    strike: Decimal

    exchange: str

    currency: str

    multiplier: int

    # ------------------------------------------------------------------
    # Prices
    # ------------------------------------------------------------------

    bid: Decimal | None

    ask: Decimal | None

    last: Decimal | None

    mark: Decimal | None

    # ------------------------------------------------------------------
    # Greeks
    # ------------------------------------------------------------------

    delta: Decimal | None

    gamma: Decimal | None

    theta: Decimal | None

    vega: Decimal | None

    implied_volatility: Decimal | None

    # ------------------------------------------------------------------
    # Liquidity
    # ------------------------------------------------------------------

    volume: int | None

    open_interest: int | None