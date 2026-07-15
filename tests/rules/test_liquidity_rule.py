from dataclasses import replace

from app.core.rule_status import RuleStatus
from app.models.investment_candidate import InvestmentCandidate
from app.models.investment_thesis import InvestmentThesis
from app.rules.liquidity import LiquidityRule
from tests.conftest import build_company, build_option


def _candidate_with(volume, open_interest) -> InvestmentCandidate:
    option = replace(
        build_option(delta=-0.20),
        volume=volume,
        open_interest=open_interest,
    )

    return InvestmentCandidate(
        company=build_company(),
        thesis=InvestmentThesis(approved=True),
        option=option,
    )


def test_sufficient_liquidity_should_pass():
    candidate = _candidate_with(volume=100, open_interest=600)

    result = LiquidityRule(
        minimum_volume=50, minimum_open_interest=500
    ).evaluate(candidate)

    assert result.status is RuleStatus.PASS


def test_volume_below_minimum_should_fail_and_block():
    candidate = _candidate_with(volume=10, open_interest=600)

    result = LiquidityRule(
        minimum_volume=50, minimum_open_interest=500
    ).evaluate(candidate)

    assert result.status is RuleStatus.FAIL
    assert result.blocker is True


def test_open_interest_below_minimum_should_fail_and_block():
    candidate = _candidate_with(volume=100, open_interest=50)

    result = LiquidityRule(
        minimum_volume=50, minimum_open_interest=500
    ).evaluate(candidate)

    assert result.status is RuleStatus.FAIL
    assert result.blocker is True


def test_missing_liquidity_data_should_pass():
    """
    Regression guard: missing volume/open_interest (IBKR account
    without an options data subscription, or data unavailable outside
    market hours) must not reject the contract - this was the
    "keep during development" behavior of the old LiquidityFilter
    service, preserved here.
    """
    candidate = _candidate_with(volume=None, open_interest=None)

    result = LiquidityRule(
        minimum_volume=50, minimum_open_interest=500
    ).evaluate(candidate)

    assert result.status is RuleStatus.PASS


def test_reads_thresholds_from_constitution_yaml_by_default():
    rule = LiquidityRule()

    assert rule.minimum_volume == 50
    assert rule.minimum_open_interest == 500
