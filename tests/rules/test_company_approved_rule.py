from app.core.rule_status import RuleStatus
from app.rules.company.company_approved_rule import CompanyApprovedRule
from tests.conftest import build_candidate


def test_approved_company_should_pass():
    result = CompanyApprovedRule().evaluate(build_candidate(approved=True))

    assert result.status is RuleStatus.PASS
    assert result.blocker is False


def test_not_approved_company_should_fail_and_block():
    result = CompanyApprovedRule().evaluate(build_candidate(approved=False))

    assert result.status is RuleStatus.FAIL
    assert result.blocker is True
