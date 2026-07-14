from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(slots=True, frozen=True)
class Company:
    """
    Represents a company listed in the market.
    """

    # ------------------------------------------------------------------
    # Basic information
    # ------------------------------------------------------------------

    symbol: str
    name: str

    currency: str
    exchange: str

    sector: str
    industry: str
    country: str

    description: str

    # ------------------------------------------------------------------
    # Market data
    # ------------------------------------------------------------------

    market_cap: int

    pe_ratio: Decimal | None
    peg_ratio: Decimal | None

    eps: Decimal | None

    book_value_per_share: Decimal | None

    dividend_per_share: Decimal | None
    dividend_yield: Decimal | None

    beta: Decimal | None

    shares_outstanding: int | None

    # ------------------------------------------------------------------
    # Profitability
    # ------------------------------------------------------------------

    revenue_ttm: Decimal | None

    gross_profit_ttm: Decimal | None

    operating_margin: Decimal | None

    profit_margin: Decimal | None

    ebitda: Decimal | None

    roe: Decimal | None

    roa: Decimal | None

    # ------------------------------------------------------------------
    # Balance Sheet
    # ------------------------------------------------------------------

    total_assets: Decimal | None

    total_liabilities: Decimal | None

    debt_to_equity: Decimal | None

    # ------------------------------------------------------------------
    # Cash Flow
    # ------------------------------------------------------------------

    operating_cash_flow: Decimal | None

    free_cash_flow: Decimal | None

    # ------------------------------------------------------------------
    # Growth
    # ------------------------------------------------------------------

    quarterly_revenue_growth: Decimal | None

    quarterly_earnings_growth: Decimal | None

    # ------------------------------------------------------------------
    # Calendar
    # ------------------------------------------------------------------

    next_earnings: date | None = None