from __future__ import annotations

from decimal import Decimal

from app.models.company import Company


class AlphaVantageMapper:
    """
    Converts Alpha Vantage JSON responses into domain models.
    """

    @staticmethod
    def company(data: dict) -> Company:

        def decimal_or_none(value: str | None) -> Decimal | None:
            if not value or value in ("None", "-", ""):
                return None

            return Decimal(value)

        def int_or_none(value: str | None) -> int | None:
            if not value or value in ("None", "-", ""):
                return None

            return int(value)

        return Company(
            # -----------------------------------------------------------------
            # Basic information
            # -----------------------------------------------------------------

            symbol=data["Symbol"],
            name=data["Name"],
            currency=data["Currency"],
            exchange=data["Exchange"],
            sector=data["Sector"],
            industry=data["Industry"],
            country=data["Country"],
            description=data["Description"],

            # -----------------------------------------------------------------
            # Market data
            # -----------------------------------------------------------------

            market_cap=int(data["MarketCapitalization"]),
            pe_ratio=decimal_or_none(data.get("PERatio")),
            peg_ratio=decimal_or_none(data.get("PEGRatio")),
            eps=decimal_or_none(data.get("EPS")),
            book_value_per_share=decimal_or_none(data.get("BookValue")),
            dividend_per_share=decimal_or_none(data.get("DividendPerShare")),
            dividend_yield=decimal_or_none(data.get("DividendYield")),
            beta=decimal_or_none(data.get("Beta")),
            shares_outstanding=int_or_none(data.get("SharesOutstanding")),

            # -----------------------------------------------------------------
            # Profitability
            # -----------------------------------------------------------------

            revenue_ttm=decimal_or_none(data.get("RevenueTTM")),
            gross_profit_ttm=decimal_or_none(data.get("GrossProfitTTM")),
            operating_margin=decimal_or_none(data.get("OperatingMarginTTM")),
            profit_margin=decimal_or_none(data.get("ProfitMargin")),
            ebitda=decimal_or_none(data.get("EBITDA")),
            roe=decimal_or_none(data.get("ReturnOnEquityTTM")),
            roa=decimal_or_none(data.get("ReturnOnAssetsTTM")),

            # -----------------------------------------------------------------
            # Balance Sheet
            # -----------------------------------------------------------------

            total_assets=None,
            total_liabilities=None,
            debt_to_equity=decimal_or_none(data.get("DebtToEquity")),

            # -----------------------------------------------------------------
            # Cash Flow
            # -----------------------------------------------------------------

            operating_cash_flow=decimal_or_none(data.get("OperatingCashflowTTM")),
            free_cash_flow=None,

            # -----------------------------------------------------------------
            # Growth
            # -----------------------------------------------------------------

            quarterly_revenue_growth=decimal_or_none(
                data.get("QuarterlyRevenueGrowthYOY")
            ),
            quarterly_earnings_growth=decimal_or_none(
                data.get("QuarterlyEarningsGrowthYOY")
            ),
        )