from datetime import date, timedelta
from decimal import Decimal

from app.core.rule_engine import RuleEngine
from app.models.company import Company
from app.models.investment_candidate import InvestmentCandidate
from app.models.investment_thesis import InvestmentThesis
from app.models.option_contract import OptionContract
from app.rules.no_earnings import NoUpcomingEarningsRule


company = Company(
    ticker="SAP",
    name="SAP SE",
    current_price=Decimal("282.50"),
    next_earnings=date.today() + timedelta(days=25),
)

thesis = InvestmentThesis(
    fair_value=Decimal("320"),
    buy_price=Decimal("255"),
    quality_score=Decimal("92"),
    approved=True,
)

contract = OptionContract(
    ticker="SAP",
    expiration=date.today() + timedelta(days=45),
    strike=Decimal("250"),
    option_type="PUT",
    bid=Decimal("4.10"),
    ask=Decimal("4.30"),
    delta=-0.18,
    implied_volatility=0.31,
    open_interest=1200,
)

candidate = InvestmentCandidate(
    company=company,
    thesis=thesis,
    option=contract,
)

engine = RuleEngine(
    [
        NoUpcomingEarningsRule()
    ]
)

results = engine.evaluate(candidate)

for result in results:
    print(result)