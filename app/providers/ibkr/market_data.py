from __future__ import annotations

import asyncio
from decimal import Decimal

from ib_async import IB, Ticker

from app.models.market_data import MarketData


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

        bid = (
            Decimal(str(ticker.bid))
            if ticker.bid not in (None, -1)
            else None
        )

        ask = (
            Decimal(str(ticker.ask))
            if ticker.ask not in (None, -1)
            else None
        )

        last = (
            Decimal(str(ticker.last))
            if ticker.last not in (None, -1)
            else None
        )

        mark = None

        if bid is not None and ask is not None:
            mark = (bid + ask) / Decimal("2")

        underlying = None

        market_price = ticker.marketPrice()

        if market_price not in (None, -1):
            underlying = Decimal(str(market_price))

        self.ib.cancelMktData(contract)

        return MarketData(
            underlying_price=underlying,

            bid=bid,
            ask=ask,
            last=last,
            mark=mark,

            delta=(
                Decimal(str(greeks.delta))
                if greeks and greeks.delta is not None
                else None
            ),

            gamma=(
                Decimal(str(greeks.gamma))
                if greeks and greeks.gamma is not None
                else None
            ),

            theta=(
                Decimal(str(greeks.theta))
                if greeks and greeks.theta is not None
                else None
            ),

            vega=(
                Decimal(str(greeks.vega))
                if greeks and greeks.vega is not None
                else None
            ),

            implied_volatility=(
                Decimal(str(greeks.impliedVol))
                if greeks and greeks.impliedVol is not None
                else None
            ),

            volume=ticker.volume,
            open_interest=None,
        )