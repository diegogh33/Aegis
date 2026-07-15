from dataclasses import replace
from decimal import Decimal

from app.core.rule_status import RuleStatus
from app.models.investment_candidate import InvestmentCandidate
from app.models.investment_thesis import InvestmentThesis
from app.rules.spread import SpreadRule
from tests.conftest import build_company, build_option


def _candidate_with(bid, ask) -> InvestmentCandidate:
    option = replace(build_option(delta=-0.20), bid=bid, ask=ask)

    return InvestmentCandidate(
        company=build_company(),
        thesis=InvestmentThesis(approved=True),
        option=option,
    )


def test_tight_spread_should_pass():
    candidate = _candidate_with(bid=Decimal("4.0"), ask=Decimal("4.1"))

    result = SpreadRule(maximum_percent=Decimal("5")).evaluate(candidate)

    assert result.status is RuleStatus.PASS


def test_wide_spread_should_fail_and_block():
    candidate = _candidate_with(bid=Decimal("2.0"), ask=Decimal("5.0"))

    result = SpreadRule(maximum_percent=Decimal("5")).evaluate(candidate)

    assert result.status is RuleStatus.FAIL
    assert result.blocker is True


def test_missing_bid_ask_should_pass():
    """
    Regression guard: missing bid/ask (no market data subscription,
    or outside market hours) must not reject the contract - same
    "keep during development" behavior as LiquidityRule.
    """
    candidate = _candidate_with(bid=None, ask=None)

    result = SpreadRule(maximum_percent=Decimal("5")).evaluate(candidate)

    assert result.status is RuleStatus.PASS


def test_zero_ask_should_pass_without_dividing_by_zero():
    candidate = _candidate_with(bid=Decimal("0"), ask=Decimal("0"))

    result = SpreadRule(maximum_percent=Decimal("5")).evaluate(candidate)

    assert result.status is RuleStatus.PASS


def test_reads_threshold_from_constitution_yaml_by_default():
    rule = SpreadRule()

    assert rule.maximum_percent == Decimal("5")
