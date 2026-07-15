from dataclasses import replace
from decimal import Decimal

from app.providers.ibkr.provider import _closest_strikes, _closest_to_target_delta
from tests.conftest import build_option


def _option_at_strike(strike: str):
    return replace(build_option(delta=None), strike=Decimal(strike))


def test_keeps_strikes_closest_to_underlying_price():
    contracts = [
        _option_at_strike("200"),
        _option_at_strike("250"),
        _option_at_strike("280"),
        _option_at_strike("300"),
        _option_at_strike("350"),
    ]

    result = _closest_strikes(
        contracts, underlying_price=Decimal("280"), limit=3
    )

    strikes = [c.strike for c in result]

    assert strikes == [Decimal("280"), Decimal("300"), Decimal("250")]


def test_limit_larger_than_available_returns_all():
    contracts = [
        _option_at_strike("250"),
        _option_at_strike("280"),
    ]

    result = _closest_strikes(
        contracts, underlying_price=Decimal("280"), limit=10
    )

    assert len(result) == 2


def test_limit_zero_returns_empty():
    contracts = [_option_at_strike("280")]

    result = _closest_strikes(
        contracts, underlying_price=Decimal("280"), limit=0
    )

    assert result == []


def test_closest_to_target_delta_picks_further_strikes_for_high_iv():
    """
    Regression test for the finding that motivated this selector:
    with DRAM (price ~56.61, IV ~95%, 37 DTE), a target delta of
    -0.20 falls on strikes noticeably below the underlying price
    (around 47-49), which price-proximity selection with a small
    limit would have missed entirely (8 closest to 56.61 covers
    roughly 53-60).
    """
    contracts = [
        _option_at_strike(str(s))
        for s in [47, 50, 53, 55, 56, 57, 58, 60]
    ]

    result = _closest_to_target_delta(
        contracts,
        underlying_price=Decimal("56.61"),
        days_to_expiration=37,
        reference_iv=Decimal("0.95"),
        target_delta=-0.20,
        limit=3,
    )

    strikes = {c.strike for c in result}

    # Strike 47 (delta ~-0.22) should be among the closest to target,
    # not excluded in favor of strikes near the price like 56-58
    # (which have much higher deltas at this IV).
    assert Decimal("47") in strikes


def test_closest_to_target_delta_picks_near_price_strikes_for_low_iv():
    """
    For a low-IV stock (ACN-like, ~47%), the target delta falls much
    closer to the underlying price - the selector should behave
    similarly to price-proximity in that case.
    """
    contracts = [
        _option_at_strike(str(s)) for s in [120, 125, 130, 135, 140]
    ]

    result = _closest_to_target_delta(
        contracts,
        underlying_price=Decimal("139.09"),
        days_to_expiration=37,
        reference_iv=Decimal("0.478"),
        target_delta=-0.20,
        limit=2,
    )

    strikes = {c.strike for c in result}

    assert strikes == {Decimal("120"), Decimal("125")}
