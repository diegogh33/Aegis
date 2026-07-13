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

    @staticmethod
    def _decimal(value) -> Decimal | None:

        if value is None:
            return None

        try:

            value = float(value)

            if value <= 0:
                return None

            return Decimal(str(value))

        except Exception:
            return None

    async def get(self, contract) -> MarketData:

        ticker: Ticker = self.ib.reqMktData(contract)

        # Esperamos a que IBKR complete la información
        await asyncio.sleep(2)

        greeks = ticker.modelGreeks

        bid = self._decimal(ticker.bid)
        ask = self._decimal(ticker.ask)
        last = self._decimal(ticker.last)

        if bid is not None and ask is not None:
            mark = (bid + ask) / Decimal("2")
        else:
            mark = None

        delta = (
            Decimal(str(greeks.delta))
            if greeks and greeks.delta is not None
            else None
        )

        gamma = (
            Decimal(str(greeks.gamma))
            if greeks and greeks.gamma is not None
            else None
        )

        theta = (
            Decimal(str(greeks.theta))
            if greeks and greeks.theta is not None
            else None
        )

        vega = (
            Decimal(str(greeks.vega))
            if greeks and greeks.vega is not None
            else None
        )

        implied_volatility = (
            Decimal(str(greeks.impliedVol))
            if greeks and greeks.impliedVol is not None
            else None
        )

        self.ib.cancelMktData(contract)

        return MarketData(
            bid=bid,
            ask=ask,
            last=last,
            mark=mark,
            delta=delta,
            gamma=gamma,
            theta=theta,
            vega=vega,
            implied_volatility=implied_volatility,
            volume=ticker.volume,
            open_interest=None,
        )