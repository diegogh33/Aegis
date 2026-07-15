from __future__ import annotations

import asyncio
import math
from decimal import Decimal

from ib_async import IB, Ticker

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


class MarketDataProvider:
    """
    Retrieves real-time market data from Interactive Brokers.
    """

    def __init__(self, ib: IB) -> None:
        self.ib = ib

    async def get(self, contract) -> MarketData:

        ticker: Ticker = self.ib.reqMktData(
            contract,
            genericTickList="100",
        )

        await asyncio.sleep(2)

        greeks = ticker.modelGreeks

        bid = _decimal_or_none(ticker.bid)
        ask = _decimal_or_none(ticker.ask)
        last = _decimal_or_none(ticker.last)

        mark = None

        if bid is not None and ask is not None:
            mark = (bid + ask) / Decimal("2")

        underlying = _decimal_or_none(ticker.marketPrice())

        self.ib.cancelMktData(contract)

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
            open_interest=None,
        )

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

        ticker: Ticker = self.ib.reqMktData(contract)

        await asyncio.sleep(2)

        price = _decimal_or_none(ticker.marketPrice())

        self.ib.cancelMktData(contract)

        return price