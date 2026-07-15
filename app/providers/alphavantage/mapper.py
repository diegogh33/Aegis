from __future__ import annotations

from decimal import Decimal

from app.models.company import Company


class UnknownCompanyError(Exception):
    """
    Raised when Alpha Vantage's OVERVIEW response doesn't contain
    company data - typically because the symbol isn't recognized
    (e.g. a non-US ticker without the market suffix Alpha Vantage
    expects, like "ITX" instead of "ITX.MC"). Alpha Vantage returns
    an empty JSON object ({}) for this case rather than an explicit
    error field, so this has to be detected by checking for the
    required keys rather than relying on the client's existing
    "Error Message"/"Information" handling.
    """


class AlphaVantageMapper:
    """
    Converts Alpha Vantage JSON responses into domain models.
    """

    @staticmethod
    def company(data: dict) -> Company:

        if "Symbol" not in data or "Name" not in data:
            raise UnknownCompanyError(
                "Alpha Vantage did not return company data for this "
                "symbol. This usually means the ticker isn't "
                "recognized (e.g. a non-US ticker needs a market "
                "suffix Alpha Vantage doesn't have, like '.MC')."
            )

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
            currency=data.get("Currency", "N/A"),
            exchange=data.get("Exchange", "N/A"),
            sector=data.get("Sector", "N/A"),
            industry=data.get("Industry", "N/A"),
            country=data.get("Country", "N/A"),
            description=data.get("Description", ""),

            # -----------------------------------------------------------------
            # Market data
            # -----------------------------------------------------------------

            market_cap=int_or_none(data.get("MarketCapitalization")) or 0,
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