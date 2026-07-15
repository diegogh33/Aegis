import math
from decimal import Decimal

from ib_async import Ticker
from ib_async.objects import OptionComputation

from app.providers.ibkr.market_data import (
    _decimal_or_none,
    _has_any_price,
    _select_greeks,
    _to_market_data,
)


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


def test_ticker_with_no_data_has_no_price():
    """
    A freshly-requested Ticker before any tick has arrived, or one for
    a contract with no subscription and no delayed data either, has
    all price fields as NaN by default.
    """
    ticker = Ticker()

    assert not _has_any_price(ticker)


def test_ticker_with_last_has_a_price():
    ticker = Ticker()
    ticker.last = 4.10

    assert _has_any_price(ticker)


def test_ticker_with_bid_ask_has_a_price():
    ticker = Ticker()
    ticker.bid = 4.0
    ticker.ask = 4.2
    ticker.last = 4.1

    assert _has_any_price(ticker)


def test_maps_open_interest_from_ticker():
    """
    Regression test: open_interest was hardcoded to None in the
    MarketData built by get(), even though the model and
    LiquidityRule both support checking it - meaning half of
    LiquidityRule (the open interest check) could never actually
    trigger. ticker.openInterest is populated as part of the standard
    option computation ticks, same as the Greeks, with no special
    genericTickList needed.
    """
    ticker = Ticker()
    ticker.openInterest = 750.0

    market_data = _to_market_data(ticker, greeks=None)

    assert market_data.open_interest == 750


def test_open_interest_nan_maps_to_none():
    ticker = Ticker()
    # openInterest defaults to NaN on a fresh Ticker.

    market_data = _to_market_data(ticker, greeks=None)

    assert market_data.open_interest is None


def test_maps_bid_ask_mark_correctly():
    ticker = Ticker()
    ticker.bid = 4.0
    ticker.ask = 4.2

    market_data = _to_market_data(ticker, greeks=None)

    assert market_data.bid == Decimal("4.0")
    assert market_data.ask == Decimal("4.2")
    assert market_data.mark == Decimal("4.1")


def test_select_greeks_prefers_model_when_available():
    ticker = Ticker()
    ticker.modelGreeks = OptionComputation(tickAttrib=0, delta=-0.20)
    ticker.bidGreeks = OptionComputation(tickAttrib=0, delta=-0.25)

    greeks, source = _select_greeks(ticker)

    assert source == "model"
    assert greeks.delta == -0.20


def test_select_greeks_falls_back_to_bid_when_model_missing():
    """
    Regression test: less liquid strikes (confirmed with ACN, ~14%
    OTM) can leave modelGreeks as None indefinitely, even with a real
    price available and after polling. bidGreeks/askGreeks are
    computed directly from the quoted price rather than the model's
    own "fair" price, so they're a reasonable fallback rather than
    leaving delta empty.
    """
    ticker = Ticker()
    ticker.bidGreeks = OptionComputation(tickAttrib=0, delta=-0.18)

    greeks, source = _select_greeks(ticker)

    assert source == "bid"
    assert greeks.delta == -0.18


def test_select_greeks_falls_back_to_ask_when_model_and_bid_missing():
    ticker = Ticker()
    ticker.askGreeks = OptionComputation(tickAttrib=0, delta=-0.15)

    greeks, source = _select_greeks(ticker)

    assert source == "ask"
    assert greeks.delta == -0.15


def test_select_greeks_returns_none_when_nothing_available():
    ticker = Ticker()

    greeks, source = _select_greeks(ticker)

    assert greeks is None
    assert source == "none"
