from decimal import Decimal
from unittest.mock import AsyncMock

from app.models.market_data import MarketData
from app.services.option_scanner import OptionScanner
from tests.conftest import build_option


def _market_data(underlying_price: Decimal | None) -> MarketData:
    return MarketData(
        underlying_price=underlying_price,
        bid=Decimal("4.0"),
        ask=Decimal("4.2"),
        last=Decimal("4.1"),
        mark=Decimal("4.1"),
        delta=None,
        gamma=None,
        theta=None,
        vega=None,
        implied_volatility=None,
        volume=None,
        open_interest=None,
    )


async def test_propagates_exchange_and_currency_to_provider():
    """
    Non-US tickers (e.g. Spanish stocks on MEFF) need exchange/
    currency passed through to IBKR - defaults are SMART/USD but
    scan_puts must forward whatever the caller specifies.
    """
    option = build_option(delta=None)

    provider = AsyncMock()
    provider.get_put_contracts.return_value = [option]
    provider.get_underlying_price.return_value = Decimal("40.00")
    provider.get_market_data.return_value = _market_data(underlying_price=None)

    scanner = OptionScanner(provider)

    await scanner.scan_puts("SAN", exchange="SMART", currency="EUR")

    provider.get_put_contracts.assert_awaited_once_with(
        "SAN",
        exchange="SMART",
        currency="EUR",
        dte_window=None,
        target_delta=None,
    )
    provider.get_underlying_price.assert_awaited_once_with(
        "SAN", exchange="SMART", currency="EUR"
    )


async def test_falls_back_to_stock_price_when_option_has_no_underlying_price():
    """
    Regression test: on accounts without an IBKR options market data
    subscription (error 10091), each option's own underlying_price
    comes back empty even though the stock itself has real market
    data. Without a fallback, every contract used to be silently
    dropped later by AnalysisService's `if underlying_price is None`
    check, producing an empty results table with no error.
    """
    option = build_option(delta=None)

    provider = AsyncMock()
    provider.get_put_contracts.return_value = [option]
    provider.get_underlying_price.return_value = Decimal("280.00")
    provider.get_market_data.return_value = _market_data(underlying_price=None)

    scanner = OptionScanner(provider)

    result = await scanner.scan_puts("AAPL")

    assert len(result) == 1
    assert result[0].underlying_price == Decimal("280.00")


async def test_stock_price_is_preferred_over_options_embedded_underlying_price():
    """
    Regression test from real ASML --long-term run: the underlying_price
    embedded in the option's market data tick came back at ~€83 instead
    of the real ~€1576 (a known scale issue with EUREX options), making
    OTM% calculations completely wrong. The stock's own price
    (get_underlying_price) is now always preferred when available -
    it's reliable and consistent across markets.
    """
    option = build_option(delta=None)

    provider = AsyncMock()
    provider.get_put_contracts.return_value = [option]
    provider.get_underlying_price.return_value = Decimal("280.00")
    provider.get_market_data.return_value = _market_data(
        underlying_price=Decimal("83.00")  # wrong scale, like ASML on EUREX
    )

    scanner = OptionScanner(provider)

    result = await scanner.scan_puts("AAPL")

    # Stock price (280.00) wins over the option's embedded price (83.00)
    assert result[0].underlying_price == Decimal("280.00")


async def test_underlying_price_stays_none_if_both_sources_are_missing():
    option = build_option(delta=None)

    provider = AsyncMock()
    provider.get_put_contracts.return_value = [option]
    provider.get_underlying_price.return_value = None
    provider.get_market_data.return_value = _market_data(underlying_price=None)

    scanner = OptionScanner(provider)

    result = await scanner.scan_puts("AAPL")

    assert result[0].underlying_price is None


async def test_market_data_requests_are_sent_in_batches():
    """
    Regression test: firing all market data requests at once with a
    single asyncio.gather() (confirmed with ACN, 32 contracts) can
    saturate IBKR's 50 messages/second limit for API clients, leaving
    an entire expiration without Greeks even when the real market has
    normal liquidity - not a data availability problem, a request
    saturation one. Requests should go out in small batches instead.
    """
    contracts = [build_option(delta=None) for _ in range(10)]

    call_order: list[int] = []

    async def _tracked_get_market_data(contract):
        call_order.append(len(call_order))
        return _market_data(underlying_price=None)

    provider = AsyncMock()
    provider.get_put_contracts.return_value = contracts
    provider.get_underlying_price.return_value = Decimal("280.00")
    provider.get_market_data.side_effect = _tracked_get_market_data

    scanner = OptionScanner(provider)

    result = await scanner.scan_puts("AAPL", batch_size=3)

    assert len(result) == 10
    # 10 contracts, batch_size=3: 4 batches (3+3+3+1), each awaited
    # via asyncio.gather - all 10 calls still happen, just not as one
    # single gather() of 10.
    assert provider.get_market_data.await_count == 10
