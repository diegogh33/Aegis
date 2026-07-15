import math
from decimal import Decimal

from app.providers.ibkr.market_data import _decimal_or_none


def test_none_returns_none():
    assert _decimal_or_none(None) is None


def test_minus_one_returns_none():
    assert _decimal_or_none(-1) is None


def test_nan_returns_none():
    """
    Regression test: IBKR/ib_async represents missing ticks as NaN in
    some fields (bid/ask/last/marketPrice). `nan not in (None, -1)` is
    True because NaN never equals anything, so a naive check lets it
    through as if it were a real price. That NaN eventually reached
    Decimal comparisons in LiquidityFilter and raised
    decimal.InvalidOperation in production.
    """
    assert _decimal_or_none(math.nan) is None


def test_real_value_returns_decimal():
    result = _decimal_or_none(4.25)

    assert result == Decimal("4.25")


def test_zero_is_a_valid_value_not_missing_data():
    result = _decimal_or_none(0.0)

    assert result == Decimal("0")
