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


def test_not_approved_company_should_be_rejected_even_with_good_delta():
    candidate = build_candidate(
        delta=-0.20,
        approved=False,
        next_earnings=date.today() + timedelta(days=30),
    )

    report = CashSecuredPutStrategy().evaluate(candidate)

    assert report.passed is False
    assert report.recommendation is Recommendation.REJECT


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
