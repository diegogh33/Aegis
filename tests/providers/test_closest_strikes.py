from dataclasses import replace
from decimal import Decimal

from app.providers.ibkr.provider import _closest_strikes
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
