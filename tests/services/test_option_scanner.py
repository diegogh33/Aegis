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


async def test_uses_option_own_underlying_price_when_available():
    option = build_option(delta=None)

    provider = AsyncMock()
    provider.get_put_contracts.return_value = [option]
    provider.get_underlying_price.return_value = Decimal("280.00")
    provider.get_market_data.return_value = _market_data(
        underlying_price=Decimal("281.50")
    )

    scanner = OptionScanner(provider)

    result = await scanner.scan_puts("AAPL")

    assert result[0].underlying_price == Decimal("281.50")


async def test_underlying_price_stays_none_if_both_sources_are_missing():
    option = build_option(delta=None)

    provider = AsyncMock()
    provider.get_put_contracts.return_value = [option]
    provider.get_underlying_price.return_value = None
    provider.get_market_data.return_value = _market_data(underlying_price=None)

    scanner = OptionScanner(provider)

    result = await scanner.scan_puts("AAPL")

    assert result[0].underlying_price is None
