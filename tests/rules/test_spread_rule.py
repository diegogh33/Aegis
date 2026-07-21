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


def test_long_term_section_uses_wider_spread_threshold():
    """
    Regression test from real NFLX --long-term run: the mar-2027
    strike 55 (spread 6.6%) and jun-2027 strike 56 (spread 9.2%)
    were valid long-term candidates that would have been rejected
    under the recurring 5% limit. long_term_put.spread.maximum_percent
    is 10 in constitution.yaml, allowing these through.
    """
    rule = SpreadRule(config_section="long_term_put")

    assert rule.maximum_percent == Decimal("10")

    # 6.6% spread (mar-2027 strike 55): passes long_term, fails recurring
    candidate_66 = _candidate_with(bid=Decimal("2.85"), ask=Decimal("3.05"))
    assert SpreadRule(maximum_percent=Decimal("10")).evaluate(candidate_66).status is RuleStatus.PASS
    assert SpreadRule(maximum_percent=Decimal("5")).evaluate(candidate_66).status is RuleStatus.FAIL
