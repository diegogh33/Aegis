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

        ticker: Ticker = self.ib.reqMktData(contract)

        # Esperamos a que lleguen los primeros ticks
        await asyncio.sleep(2)

        bid = (
            Decimal(str(ticker.bid))
            if ticker.bid is not None and ticker.bid > 0
            else None
        )

        ask = (
            Decimal(str(ticker.ask))
            if ticker.ask is not None and ticker.ask > 0
            else None
        )

        last = (
            Decimal(str(ticker.last))
            if ticker.last is not None and ticker.last > 0
            else None
        )

        self.ib.cancelMktData(contract)

        return MarketData(
            bid=bid,
            ask=ask,
            last=last,
            mark=None,
            delta=None,
            gamma=None,
            theta=None,
            vega=None,
            implied_volatility=None,
            volume=ticker.volume,
            open_interest=None,
        )