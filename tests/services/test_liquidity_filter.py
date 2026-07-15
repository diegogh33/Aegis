from dataclasses import replace
from decimal import Decimal

from app.services.liquidity_filter import LiquidityFilter
from tests.conftest import build_option


def test_contract_without_bid_ask_is_kept():
    """
    When market data is unavailable (bid/ask are None, as they should
    be after MarketDataProvider normalizes NaN/-1 to None), the
    contract is kept rather than discarded - this is the documented
    development-time behavior.
    """
    option = replace(build_option(), bid=None, ask=None)

    result = LiquidityFilter().apply([option])

    assert result == [option]


def test_contract_below_minimum_bid_is_dropped():
    option = replace(build_option(), bid=Decimal("0.00"), ask=Decimal("0.05"))

    result = LiquidityFilter(minimum_bid=Decimal("0.01")).apply([option])

    assert result == []


def test_contract_with_wide_spread_is_dropped():
    option = replace(build_option(), bid=Decimal("1.0"), ask=Decimal("5.0"))

    result = LiquidityFilter(maximum_spread_pct=Decimal("0.20")).apply(
        [option]
    )

    assert result == []


def test_contract_with_good_liquidity_is_kept():
    option = replace(
        build_option(),
        bid=Decimal("4.0"),
        ask=Decimal("4.1"),
        volume=100,
    )

    result = LiquidityFilter().apply([option])

    assert result == [option]
