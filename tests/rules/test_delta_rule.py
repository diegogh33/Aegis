from datetime import date, timedelta
from decimal import Decimal

from app.core.rule_status import RuleStatus
from app.models.company import Company
from app.models.investment_candidate import InvestmentCandidate
from app.models.investment_thesis import InvestmentThesis
from app.models.option_contract import OptionContract
from app.rules.delta import DeltaRule


def build_company(next_earnings: date | None) -> Company:
    return Company(
        symbol="SAP",
        name="SAP SE",
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


def build_option(delta: float) -> OptionContract:
    return OptionContract(
        underlying="SAP",
        local_symbol="SAP",
        con_id=1,
        option_type="PUT",
        expiration=date.today() + timedelta(days=45),
        strike=Decimal("250"),
        exchange="SMART",
        currency="USD",
        multiplier=100,
        underlying_price=Decimal("280"),
        bid=Decimal("4.0"),
        ask=Decimal("4.2"),
        last=Decimal("4.1"),
        mark=Decimal("4.1"),
        delta=delta,
        gamma=None,
        theta=None,
        vega=None,
        implied_volatility=None,
        volume=None,
        open_interest=None,
    )


def build_candidate(delta: float) -> InvestmentCandidate:
    company = build_company(next_earnings=date.today() + timedelta(days=30))

    thesis = InvestmentThesis()

    option = build_option(delta=delta)

    return InvestmentCandidate(
        company=company,
        thesis=thesis,
        option=option,
    )


def test_delta_inside_range_should_pass():
    result = DeltaRule().evaluate(build_candidate(-0.20))

    assert result.status is RuleStatus.PASS


def test_delta_slightly_aggressive_should_warn():
    result = DeltaRule().evaluate(build_candidate(-0.28))

    assert result.status is RuleStatus.WARNING


def test_delta_too_aggressive_should_fail():
    result = DeltaRule().evaluate(build_candidate(-0.40))

    assert result.status is RuleStatus.FAIL