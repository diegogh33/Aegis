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

    @classmethod
    def unknown(cls, symbol: str) -> Company:
        """
        Builds a placeholder Company for when fundamental data isn't
        available (e.g. Alpha Vantage doesn't recognize the ticker -
        common for non-US symbols without the right market suffix).

        Every rule/scoring path that reads Company fields other than
        next_earnings should be unaffected: NoUpcomingEarningsRule
        already treats next_earnings=None as "pass" (no earnings risk
        detectable), and nothing else in the Constitution or scoring
        reads Company data today.
        """

        return cls(
            symbol=symbol,
            name="(unknown - no data from Alpha Vantage)",
            currency="N/A",
            exchange="N/A",
            sector="N/A",
            industry="N/A",
            country="N/A",
            description="",
            market_cap=0,
            pe_ratio=None,
            peg_ratio=None,
            eps=None,
            book_value_per_share=None,
            dividend_per_share=None,
            dividend_yield=None,
            beta=None,
            shares_outstanding=None,
            revenue_ttm=None,
            gross_profit_ttm=None,
            operating_margin=None,
            profit_margin=None,
            ebitda=None,
            roe=None,
            roa=None,
            total_assets=None,
            total_liabilities=None,
            debt_to_equity=None,
            operating_cash_flow=None,
            free_cash_flow=None,
            quarterly_revenue_growth=None,
            quarterly_earnings_growth=None,
            next_earnings=None,
        )