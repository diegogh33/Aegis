from app.core.rule_status import RuleStatus
from app.rules.company.company_approved_rule import CompanyApprovedRule
from tests.conftest import build_candidate


def test_approved_company_should_pass():
    result = CompanyApprovedRule().evaluate(build_candidate(approved=True))

    assert result.status is RuleStatus.PASS
    assert result.blocker is False


def test_watchlist_company_should_warn_but_not_block():
    """
    A company on the ATLAS watchlist ("seguimiento") isn't a confirmed
    investment thesis yet, but shouldn't be hidden from results
    either - it surfaces with a reduced score and a visible warning.
    """
    result = CompanyApprovedRule().evaluate(
        build_candidate(approved=False, watchlist=True)
    )

    assert result.status is RuleStatus.WARNING
    assert result.blocker is False


def test_never_analyzed_company_should_fail_but_not_block():
    """
    Regression test: a ticker with no ATLAS entry at all (e.g. never
    analyzed) used to be a hard block, producing an empty results
    table with no way to see what the market itself looked like. Now
    it still surfaces as a candidate, scored lower, with a visible
    FAIL - useful for exploring a new idea rather than requiring an
    ATLAS entry to exist first.
    """
    result = CompanyApprovedRule().evaluate(
        build_candidate(approved=False, watchlist=False)
    )

    assert result.status is RuleStatus.FAIL
    assert result.blocker is False
