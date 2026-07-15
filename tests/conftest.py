from datetime import date, timedelta
from decimal import Decimal

from app.models.company import Company
from app.models.investment_candidate import InvestmentCandidate
from app.models.investment_thesis import InvestmentThesis
from app.models.option_contract import OptionContract


def build_company(
    next_earnings: date | None = None,
    symbol: str = "SAP",
) -> Company:
    """
    Builds a minimal but fully-populated Company for tests.

    All fundamental fields default to None; override next_earnings to
    exercise earnings-related rules.
    """
    return Company(
        symbol=symbol,
        name=f"{symbol} SE",
        currency="USD",
        exchange="NYSE",
        sector="Technology",
        industry="Software",
        country="Germany",
        description="Enterprise software company.",
        market_cap=200_000_000_000,
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
        next_earnings=next_earnings,
    )


def build_option(
    delta: Decimal | float | None = None,
    underlying: str = "SAP",
    dte: int = 45,
) -> OptionContract:
    """
    Builds a minimal but fully-populated OptionContract for tests.
    """
    return OptionContract(
        underlying=underlying,
        local_symbol=underlying,
        con_id=1,
        option_type="PUT",
        expiration=date.today() + timedelta(days=dte),
        strike=Decimal("250"),
        exchange="SMART",
        currency="USD",
        multiplier=100,
        underlying_price=Decimal("280"),
        bid=Decimal("4.0"),
        ask=Decimal("4.2"),
        last=Decimal("4.1"),
        mark=Decimal("4.1"),
        delta=None if delta is None else Decimal(str(delta)),
        gamma=None,
        theta=None,
        vega=None,
        implied_volatility=None,
        volume=None,
        open_interest=None,
    )


def build_candidate(
    delta: Decimal | float | None = None,
    next_earnings: date | None = None,
    approved: bool = False,
    dte: int = 45,
) -> InvestmentCandidate:
    """
    Builds a minimal but fully-populated InvestmentCandidate for tests.
    """
    return InvestmentCandidate(
        company=build_company(next_earnings=next_earnings),
        thesis=InvestmentThesis(approved=approved),
        option=build_option(delta=delta, dte=dte),
    )
