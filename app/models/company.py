from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(slots=True, frozen=True)
class Company:
    """
    Represents a company listed in the market.
    """

    symbol: str
    name: str

    currency: str

    exchange: str

    sector: str

    industry: str

    country: str

    market_cap: int

    pe_ratio: Decimal | None

    eps: Decimal | None

    dividend_yield: Decimal | None

    description: str