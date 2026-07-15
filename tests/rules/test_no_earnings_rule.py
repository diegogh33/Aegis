from datetime import date, timedelta

from app.core.rule_status import RuleStatus
from app.rules.no_earnings import NoUpcomingEarningsRule
from tests.conftest import build_candidate


def test_no_earnings_date_should_pass():
    result = NoUpcomingEarningsRule().evaluate(
        build_candidate(next_earnings=None)
    )

    assert result.status is RuleStatus.PASS


def test_earnings_far_away_should_pass():
    candidate = build_candidate(
        next_earnings=date.today() + timedelta(days=30)
    )

    result = NoUpcomingEarningsRule(minimum_days=14).evaluate(candidate)

    assert result.status is RuleStatus.PASS


def test_earnings_too_close_should_fail_and_block():
    candidate = build_candidate(
        next_earnings=date.today() + timedelta(days=5)
    )

    result = NoUpcomingEarningsRule(minimum_days=14).evaluate(candidate)

    assert result.status is RuleStatus.FAIL
    assert result.blocker is True


def test_reads_minimum_days_from_constitution_yaml_by_default():
    rule = NoUpcomingEarningsRule()

    assert rule.minimum_days == 14
