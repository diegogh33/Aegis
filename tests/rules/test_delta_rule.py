from app.core.rule_status import RuleStatus
from app.rules.delta import DeltaRule
from tests.conftest import build_candidate


def test_delta_inside_range_should_pass():
    result = DeltaRule().evaluate(build_candidate(delta=-0.20))

    assert result.status is RuleStatus.PASS


def test_delta_slightly_aggressive_should_warn():
    result = DeltaRule().evaluate(build_candidate(delta=-0.28))

    assert result.status is RuleStatus.WARNING


def test_delta_too_aggressive_should_fail():
    result = DeltaRule().evaluate(build_candidate(delta=-0.40))

    assert result.status is RuleStatus.FAIL