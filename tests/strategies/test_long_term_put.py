from dataclasses import replace
from datetime import date, timedelta
from decimal import Decimal

from app.core.recommendation import Recommendation
from app.models.investment_candidate import InvestmentCandidate
from app.models.investment_thesis import InvestmentThesis
from app.strategies.long_term_put import LongTermPutStrategy
from tests.conftest import build_company, build_option


def _candidate(
    strike: str,
    underlying_price: str,
    dte: int,
    delta: str,
    buy_price: str | None = None,
    approved: bool = True,
    next_earnings=None,
):
    option = replace(
        build_option(delta=delta, dte=dte),
        strike=Decimal(strike),
        underlying_price=Decimal(underlying_price),
    )

    return InvestmentCandidate(
        company=build_company(next_earnings=next_earnings),
        thesis=InvestmentThesis(
            approved=approved,
            buy_price=Decimal(buy_price) if buy_price is not None else None,
        ),
        option=option,
    )


def test_acn_real_example_passes_end_to_end(iv_history_repository):
    """
    Regression test built directly from the real trade that motivated
    this strategy: ACN dropped to ~$135, Diego sold a $120 strike PUT
    expiring in November (~133 DTE) for an $8.80 premium, with $120
    at or below his own ATLAS buy-zone ceiling for the stock.
    """
    candidate = _candidate(
        strike="120",
        underlying_price="135",
        dte=133,
        delta="-0.27",
        buy_price="135",
        next_earnings=date.today() + timedelta(days=200),
    )

    strategy = LongTermPutStrategy(iv_history_repository=iv_history_repository)
    report = strategy.evaluate(candidate)

    assert report.passed is True
    assert report.recommendation is not Recommendation.REJECT


def test_short_dte_is_rejected_even_with_good_delta_and_price(iv_history_repository):
    """
    A contract that would be perfectly fine for the recurring
    strategy (30-45 DTE) should be rejected here - the long-term
    strategy requires at least 90 DTE.
    """
    candidate = _candidate(
        strike="120",
        underlying_price="135",
        dte=35,
        delta="-0.20",
        buy_price="135",
        next_earnings=date.today() + timedelta(days=200),
    )

    strategy = LongTermPutStrategy(iv_history_repository=iv_history_repository)
    report = strategy.evaluate(candidate)

    assert report.passed is False
    assert report.recommendation is Recommendation.REJECT


def test_delta_within_recurring_range_but_outside_long_term_range_is_rejected(
    iv_history_repository,
):
    """
    -0.20 is squarely inside the recurring strategy's preferred range,
    but this test uses a delta far outside long_term_put's -0.10/-0.30
    range entirely (-0.45) to confirm DeltaRule with
    config_section="long_term_put" is actually being applied, not the
    recurring strategy's thresholds.
    """
    candidate = _candidate(
        strike="120",
        underlying_price="135",
        dte=133,
        delta="-0.45",
        buy_price="135",
        next_earnings=date.today() + timedelta(days=200),
    )

    strategy = LongTermPutStrategy(iv_history_repository=iv_history_repository)
    report = strategy.evaluate(candidate)

    assert report.passed is False
    assert report.recommendation is Recommendation.REJECT


def test_strike_above_buy_zone_is_rejected(iv_history_repository):
    candidate = _candidate(
        strike="140",
        underlying_price="135",
        dte=133,
        delta="-0.15",
        buy_price="130",  # ceiling below the strike
        next_earnings=date.today() + timedelta(days=200),
    )

    strategy = LongTermPutStrategy(iv_history_repository=iv_history_repository)
    report = strategy.evaluate(candidate)

    assert report.passed is False
    assert report.recommendation is Recommendation.REJECT


def test_no_atlas_entry_does_not_block_the_long_term_strategy(iv_history_repository):
    """
    Diego's explicit requirement: this strategy should work for a
    one-off dip even without a prior ATLAS analysis - CompanyApprovedRule
    is non-blocking (established in an earlier commit) and
    BelowBuyZoneRule warns without a buy_price rather than rejecting.
    """
    candidate = _candidate(
        strike="120",
        underlying_price="135",
        dte=133,
        delta="-0.20",
        buy_price=None,
        approved=False,
        next_earnings=date.today() + timedelta(days=200),
    )

    strategy = LongTermPutStrategy(iv_history_repository=iv_history_repository)
    report = strategy.evaluate(candidate)

    assert report.passed is True
