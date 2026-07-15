from datetime import date, timedelta

from app.core.recommendation import Recommendation
from app.strategies.cash_secured_put import CashSecuredPutStrategy
from tests.conftest import build_candidate


def test_approved_company_without_earnings_risk_should_not_be_rejected():
    candidate = build_candidate(
        delta=-0.20,
        approved=True,
        next_earnings=date.today() + timedelta(days=30),
    )

    report = CashSecuredPutStrategy().evaluate(candidate)

    assert report.passed is True
    assert report.recommendation is not Recommendation.REJECT


def test_not_approved_company_is_not_rejected_but_scores_lower():
    """
    Regression test: an unapproved/never-analyzed company used to be
    a hard block on its own, hiding the candidate from results
    entirely even with an otherwise perfect option. Now it still
    passes (nothing else blocks it), but the missing
    CompanyApprovedRule score keeps the recommendation from ever
    reaching STRONG_BUY/BUY.
    """
    approved_candidate = build_candidate(
        delta=-0.20,
        approved=True,
        next_earnings=date.today() + timedelta(days=30),
    )

    unapproved_candidate = build_candidate(
        delta=-0.20,
        approved=False,
        next_earnings=date.today() + timedelta(days=30),
    )

    approved_report = CashSecuredPutStrategy().evaluate(approved_candidate)
    unapproved_report = CashSecuredPutStrategy().evaluate(unapproved_candidate)

    assert approved_report.passed is True
    assert unapproved_report.passed is True
    assert unapproved_report.score < approved_report.score


def test_upcoming_earnings_should_be_rejected_even_if_approved():
    candidate = build_candidate(
        delta=-0.20,
        approved=True,
        next_earnings=date.today() + timedelta(days=5),
    )

    report = CashSecuredPutStrategy().evaluate(candidate)

    assert report.passed is False
    assert report.recommendation is Recommendation.REJECT


def test_dte_outside_range_should_be_rejected_even_if_approved():
    candidate = build_candidate(
        delta=-0.20,
        approved=True,
        next_earnings=date.today() + timedelta(days=30),
        dte=5,
    )

    report = CashSecuredPutStrategy().evaluate(candidate)

    assert report.passed is False
    assert report.recommendation is Recommendation.REJECT


def test_delta_far_outside_range_should_be_rejected_even_if_approved():
    candidate = build_candidate(
        delta=-0.60,
        approved=True,
        next_earnings=date.today() + timedelta(days=30),
    )

    report = CashSecuredPutStrategy().evaluate(candidate)

    assert report.passed is False
    assert report.recommendation is Recommendation.REJECT


def test_delta_in_warning_band_should_not_be_rejected():
    """
    A delta in the WARNING tolerance band (-0.35 to -0.25) should
    still pass the Constitution end to end - only a FAIL (outside
    -0.35/-0.15 entirely, or missing) blocks.
    """
    candidate = build_candidate(
        delta=-0.28,
        approved=True,
        next_earnings=date.today() + timedelta(days=30),
    )

    report = CashSecuredPutStrategy().evaluate(candidate)

    assert report.passed is True
    assert report.recommendation is not Recommendation.REJECT
