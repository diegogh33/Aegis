from __future__ import annotations

from datetime import date

from pydantic import BaseModel

from app.core.types import Money


class OptionContract(BaseModel):
    """
    Represents an option contract.
    """

    ticker: str

    expiration: date

    strike: Money

    option_type: str

    bid: Money

    ask: Money

    last: Money | None = None

    delta: float | None = None

    gamma: float | None = None

    theta: float | None = None

    vega: float | None = None

    implied_volatility: float | None = None

    open_interest: int | None = None

    volume: int | None = None