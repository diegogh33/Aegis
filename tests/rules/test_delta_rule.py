from datetime import date, timedelta
from decimal import Decimal

from app.core.rule_status import RuleStatus
from app.models.company import Company
from app.models.investment_candidate import InvestmentCandidate
from app.models.investment_thesis import InvestmentThesis
from app.models.option_contract import OptionContract
from app.rules.delta import DeltaRule


def build_candidate(delta: float) -> InvestmentCandidate:
    company = Company(
        ticker="SAP",
        current_price=Decimal("280"),
        next_earnings=date.today() + timedelta(days=30),
    )

    thesis = InvestmentThesis()

    option = OptionContract(
        ticker="SAP",
        expiration=date.today() + timedelta(days=45),
        strike=Decimal("250"),
        option_type="PUT",
        bid=Decimal("4.0"),
        ask=Decimal("4.2"),
        delta=delta,
    )

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