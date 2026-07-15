from app.core.rule_status import RuleStatus
from app.rules.dte import DTERule
from tests.conftest import build_candidate


def test_dte_inside_range_should_pass():
    candidate = build_candidate(dte=35)

    result = DTERule(min_dte=30, max_dte=45).evaluate(candidate)

    assert result.status is RuleStatus.PASS


def test_dte_below_minimum_should_fail_and_block():
    candidate = build_candidate(dte=10)

    result = DTERule(min_dte=30, max_dte=45).evaluate(candidate)

    assert result.status is RuleStatus.FAIL
    assert result.blocker is True


def test_dte_above_maximum_should_fail_and_block():
    candidate = build_candidate(dte=60)

    result = DTERule(min_dte=30, max_dte=45).evaluate(candidate)

    assert result.status is RuleStatus.FAIL
    assert result.blocker is True


def test_dte_at_exact_boundaries_should_pass():
    min_candidate = build_candidate(dte=30)
    max_candidate = build_candidate(dte=45)

    rule = DTERule(min_dte=30, max_dte=45)

    assert rule.evaluate(min_candidate).status is RuleStatus.PASS
    assert rule.evaluate(max_candidate).status is RuleStatus.PASS


def test_reads_thresholds_from_constitution_yaml_by_default():
    """
    Regression guard for the "Configuration First" principle: DTERule
    should read config/constitution.yaml when no explicit min/max is
    given, not hardcode its own defaults like DeltaRule/
    NoUpcomingEarningsRule currently do.
    """
    rule = DTERule()

    assert rule.min_dte == 30
    assert rule.max_dte == 45
