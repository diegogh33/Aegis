from __future__ import annotations

import asyncio
from dataclasses import replace

from app.models.market_data import MarketData
from app.models.option_contract import OptionContract
from app.providers.ibkr.provider import IBKRProvider
from app.services.liquidity_filter import LiquidityFilter


class OptionScanner:
    """
    Retrieves, enriches and filters option contracts.
    """

    def __init__(
        self,
        provider: IBKRProvider,
    ) -> None:

        self.provider = provider
        self.liquidity_filter = LiquidityFilter()

    async def scan_puts(
        self,
        symbol: str,
    ) -> list[OptionContract]:

        contracts = await self.provider.get_put_contracts(symbol)

        # Durante el desarrollo limitamos el número
        contracts = contracts[:10]

        tasks = [
            self.provider.get_market_data(contract)
            for contract in contracts
        ]

        markets: list[MarketData] = await asyncio.gather(*tasks)

        enriched: list[OptionContract] = []

        for contract, market in zip(contracts, markets):

            enriched.append(
                replace(
                    contract,
                    bid=market.bid,
                    ask=market.ask,
                    last=market.last,
                    mark=market.mark,
                    delta=market.delta,
                    gamma=market.gamma,
                    theta=market.theta,
                    vega=market.vega,
                    implied_volatility=market.implied_volatility,
                    volume=market.volume,
                    open_interest=market.open_interest,
                )
            )

        return self.liquidity_filter.apply(enriched)