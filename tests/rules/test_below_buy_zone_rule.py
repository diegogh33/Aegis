from dataclasses import replace
from decimal import Decimal

from app.core.rule_status import RuleStatus
from app.models.investment_candidate import InvestmentCandidate
from app.models.investment_thesis import InvestmentThesis
from app.rules.below_buy_zone import BelowBuyZoneRule
from tests.conftest import build_company, build_option


def _candidate(strike: str, buy_price: str | None, underlying_price: str = "280"):
    option = replace(
        build_option(delta=-0.20),
        strike=Decimal(strike),
        underlying_price=Decimal(underlying_price),
    )

    return InvestmentCandidate(
        company=build_company(),
        thesis=InvestmentThesis(
            approved=True,
            buy_price=Decimal(buy_price) if buy_price is not None else None,
        ),
        option=option,
    )


def test_strike_at_or_below_buy_price_passes():
    candidate = _candidate(strike="120", buy_price="135")

    result = BelowBuyZoneRule().evaluate(candidate)

    assert result.status is RuleStatus.PASS
    assert result.blocker is False


def test_strike_at_exact_buy_price_passes():
    candidate = _candidate(strike="135", buy_price="135")

    result = BelowBuyZoneRule().evaluate(candidate)

    assert result.status is RuleStatus.PASS


def test_strike_above_buy_price_fails_and_blocks():
    """
    Regression guard for the ACN example that motivated this rule:
    a strike above Diego's own ATLAS entrada_max would mean being
    assigned shares at a price he doesn't consider attractive - the
    whole point of the long-term strategy is the opposite.
    """
    candidate = _candidate(strike="140", buy_price="135")

    result = BelowBuyZoneRule().evaluate(candidate)

    assert result.status is RuleStatus.FAIL
    assert result.blocker is True


def test_no_buy_price_warns_but_does_not_block():
    """
    A ticker never analyzed in ATLAS (no entrada_max on record)
    shouldn't be excluded from this strategy entirely - it should
    surface with context (discount to current price) so Diego can
    judge it himself.
    """
    candidate = _candidate(strike="120", buy_price=None, underlying_price="135")

    result = BelowBuyZoneRule().evaluate(candidate)

    assert result.status is RuleStatus.WARNING
    assert result.blocker is False
    assert "%" in result.message
