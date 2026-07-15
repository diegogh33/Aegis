from app.core.rule_status import RuleStatus
from app.rules.delta import DeltaRule
from tests.conftest import build_candidate


def test_delta_inside_range_should_pass():
    result = DeltaRule().evaluate(build_candidate(delta=-0.20))

    assert result.status is RuleStatus.PASS
    assert result.blocker is False


def test_delta_slightly_aggressive_should_warn_but_not_block():
    """
    WARNING is a deliberate tolerance band, not a rejection: a delta
    a bit more aggressive than preferred still passes the
    Constitution, just with a lower score.
    """
    result = DeltaRule().evaluate(build_candidate(delta=-0.28))

    assert result.status is RuleStatus.WARNING
    assert result.blocker is False


def test_delta_too_aggressive_should_fail_and_block():
    result = DeltaRule().evaluate(build_candidate(delta=-0.40))

    assert result.status is RuleStatus.FAIL
    assert result.blocker is True


def test_missing_delta_should_fail_and_block():
    result = DeltaRule().evaluate(build_candidate(delta=None))

    assert result.status is RuleStatus.FAIL
    assert result.blocker is True


def test_reads_thresholds_from_constitution_yaml_by_default():
    """
    Regression guard for the "Configuration First" principle,
    matching DTERule/LiquidityRule/SpreadRule's pattern: DeltaRule
    should read config/constitution.yaml when no explicit thresholds
    are given, not hardcode its own defaults.
    """
    rule = DeltaRule()

    assert rule.pass_min == -0.25
    assert rule.pass_max == -0.15
    assert rule.warning_min == -0.35