from __future__ import annotations

import asyncio
import math
from decimal import Decimal

from ib_async import IB, Ticker
from ib_async.objects import OptionComputation
from loguru import logger

from app.models.market_data import MarketData


def _decimal_or_none(value: float | None) -> Decimal | None:
    """
    Converts an IBKR tick value into a clean Decimal, or None if the
    value is missing.

    IBKR/ib_async represents "no data" in more than one way depending
    on the field: None, -1, or NaN (float('nan')). NaN in particular
    is easy to miss because `nan not in (None, -1)` is True (NaN never
    equals anything, including itself), so it slips through as if it
    were a real price - and later breaks any Decimal comparison with
    decimal.InvalidOperation.
    """

    if value is None:
        return None

    if isinstance(value, float) and math.isnan(value):
        return None

    if value == -1:
        return None

    return Decimal(str(value))


def _has_any_price(ticker: Ticker) -> bool:
    return not (
        _decimal_or_none(ticker.bid) is None
        and _decimal_or_none(ticker.ask) is None
        and _decimal_or_none(ticker.last) is None
        and _decimal_or_none(ticker.marketPrice()) is None
    )


def _to_market_data(
    ticker: Ticker,
    greeks,
) -> MarketData:
    """
    Maps an IBKR Ticker (plus a possibly-later-arrived greeks object)
    into a MarketData. Pure and side-effect free, so it's testable
    without an IB connection.
    """

    bid = _decimal_or_none(ticker.bid)
    ask = _decimal_or_none(ticker.ask)
    last = _decimal_or_none(ticker.last)

    mark = None

    if bid is not None and ask is not None:
        mark = (bid + ask) / Decimal("2")

    underlying = _decimal_or_none(ticker.marketPrice())

    return MarketData(
        underlying_price=underlying,

        bid=bid,
        ask=ask,
        last=last,
        mark=mark,

        delta=_decimal_or_none(greeks.delta) if greeks else None,
        gamma=_decimal_or_none(greeks.gamma) if greeks else None,
        theta=_decimal_or_none(greeks.theta) if greeks else None,
        vega=_decimal_or_none(greeks.vega) if greeks else None,

        implied_volatility=(
            _decimal_or_none(greeks.impliedVol) if greeks else None
        ),

        volume=(
            None
            if ticker.volume is None or math.isnan(ticker.volume)
            else ticker.volume
        ),
        open_interest=(
            None
            if ticker.openInterest is None
            or math.isnan(ticker.openInterest)
            else int(ticker.openInterest)
        ),
    )


def _select_greeks(ticker: Ticker) -> tuple[OptionComputation | None, str]:
    """
    Returns (greeks, source) - the best available Greeks object for a
    ticker, preferring modelGreeks, falling back to bidGreeks then
    askGreeks. `source` is "model", "bid", "ask", or "none".
    """

    if ticker.modelGreeks is not None:
        return ticker.modelGreeks, "model"

    if ticker.bidGreeks is not None:
        return ticker.bidGreeks, "bid"

    if ticker.askGreeks is not None:
        return ticker.askGreeks, "ask"

    return None, "none"


class MarketDataProvider:
    """
    Retrieves market data from Interactive Brokers.

    Requests real-time data first (market data type 1). Some markets
    (confirmed with MEFFRV/Spanish options) return IBKR error 354 -
    "Requested market data is not subscribed. Delayed market data is
    available." - when the account has a real-time subscription for
    some markets (e.g. US) but not others. Rather than fixing the
    market data type once for the whole connection (which would mean
    choosing between losing real-time data where it IS available, or
    losing delayed fallback where it ISN'T), this retries with delayed
    data (type 3) only when the first attempt comes back empty, then
    restores live mode (type 1) afterward - reqMarketDataType is
    connection-wide, not per-request, so this has to be done carefully
    to avoid leaving later requests for genuinely real-time-subscribed
    contracts stuck on delayed data.
    """

    def __init__(self, ib: IB) -> None:
        self.ib = ib

    async def _request_ticker(
        self,
        contract,
        genericTickList: str = "",
    ) -> Ticker:
        """
        Requests a ticker, waits for it to populate, and retries once
        with delayed data if nothing came back on real-time.
        """

        ticker: Ticker = self.ib.reqMktData(
            contract,
            genericTickList=genericTickList,
        )

        await asyncio.sleep(2)

        if _has_any_price(ticker):
            return ticker

        self.ib.cancelMktData(contract)

        logger.debug(
            "{symbol}: no real-time data, retrying with delayed data.",
            symbol=getattr(contract, "localSymbol", contract),
        )

        self.ib.reqMarketDataType(3)

        ticker = self.ib.reqMktData(
            contract,
            genericTickList=genericTickList,
        )

        await asyncio.sleep(2)

        # Restore live mode so later requests for contracts that DO
        # have a real-time subscription aren't stuck on delayed data.
        self.ib.reqMarketDataType(1)

        return ticker

    async def get(self, contract) -> MarketData:

        ticker = await self._request_ticker(contract, genericTickList="100,101")

        greeks = ticker.modelGreeks

        # modelGreeks (delta, gamma, theta, vega, IV) typically takes
        # longer to populate than raw bid/ask/last, since it comes
        # from IBKR's own model computation rather than a raw tick.
        # _request_ticker() already confirmed there's a usable price
        # by this point, so a short poll here is specifically for the
        # Greeks catching up, not a full retry of the price fetch.
        if _has_any_price(ticker) and greeks is None:

            for _ in range(6):

                await asyncio.sleep(0.5)

                greeks = ticker.modelGreeks

                if greeks is not None:
                    break

        greeks_source = "model"

        # For less liquid strikes, IBKR's model computation may never
        # converge even with a price available - modelGreeks stays
        # None indefinitely, not just slow to arrive. bidGreeks/
        # askGreeks are computed directly from the quoted bid/ask
        # price rather than the model's own "fair" price, so they can
        # differ slightly (especially with a wide spread), but a
        # slightly-approximate delta is more useful than none at all
        # for a strike that otherwise has real quotes.
        if greeks is None:
            greeks, greeks_source = _select_greeks(ticker)

        # openInterest updates once at session start rather than
        # tick-by-tick, so it can take longer than the 2-second wait
        # in _request_ticker to arrive - poll briefly if it's missing
        # despite having a valid price.
        if _has_any_price(ticker) and math.isnan(ticker.openInterest):

            for _ in range(4):

                await asyncio.sleep(0.5)

                if not math.isnan(ticker.openInterest):
                    break

        if not _has_any_price(ticker):
            logger.debug(
                "No market data for {symbol} (marketDataType={type}), "
                "even after retrying with delayed data. This is "
                "expected outside market hours, or if the contract has "
                "no recent trading activity.",
                symbol=getattr(contract, "localSymbol", contract),
                type=ticker.marketDataType,
            )
        elif greeks is None:
            logger.debug(
                "{symbol}: price available but no Greeks (model, bid, "
                "or ask) after polling for up to 3 extra seconds.",
                symbol=getattr(contract, "localSymbol", contract),
            )
        elif greeks_source != "model":
            logger.debug(
                "{symbol}: modelGreeks never converged, using {source} "
                "Greeks instead (derived from the quoted {source} "
                "price, may differ slightly from the model's).",
                symbol=getattr(contract, "localSymbol", contract),
                source=greeks_source,
            )

        self.ib.cancelMktData(contract)

        return _to_market_data(ticker, greeks)

    async def get_stock_price(self, contract) -> Decimal | None:
        """
        Fetches the current market price for the underlying (stock)
        contract itself, independent of any option's market data.

        This exists because option contracts on accounts without an
        options market data subscription (IBKR error 10091) never
        receive a usable underlying_price via their own ticker - but
        the stock itself usually has real market data available. This
        lets AnalysisService price contracts even when their own
        underlying_price came back empty.
        """

        ticker = await self._request_ticker(contract)

        price = _decimal_or_none(ticker.marketPrice())

        if price is None:
            logger.debug(
                "No underlying price for {symbol} (marketDataType={type}), "
                "even after retrying with delayed data.",
                symbol=getattr(contract, "localSymbol", contract),
                type=ticker.marketDataType,
            )

        self.ib.cancelMktData(contract)

        return price