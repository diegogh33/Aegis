from __future__ import annotations

import asyncio
from dataclasses import replace

from app.models.market_data import MarketData
from app.models.option_contract import OptionContract
from app.providers.ibkr.provider import IBKRProvider


class OptionScanner:
    """
    Retrieves and enriches option contracts with market data.

    Liquidity and spread filtering used to happen here
    (LiquidityFilter), but that duplicated - with different,
    hardcoded thresholds - what LiquidityRule/SpreadRule now do as
    part of the Constitution (see CashSecuredPutStrategy). Filtering
    now happens once, in one place, reading constitution.yaml.
    """

    def __init__(
        self,
        provider: IBKRProvider,
    ) -> None:

        self.provider = provider

    async def scan_puts(
        self,
        symbol: str,
    ) -> list[OptionContract]:

        contracts = await self.provider.get_put_contracts(symbol)

        # Durante el desarrollo limitamos el número
        contracts = contracts[:10]

        # El precio del subyacente se pide una sola vez por escaneo.
        # Esto existe porque, cuando la cuenta de IBKR no tiene
        # suscripción de datos de opciones (error 10091), el
        # underlying_price de cada opción individual llega vacío,
        # pero el precio de la propia acción normalmente sí está
        # disponible.
        fallback_underlying_price = await self.provider.get_underlying_price(
            symbol
        )

        tasks = [
            self.provider.get_market_data(contract)
            for contract in contracts
        ]

        markets: list[MarketData] = await asyncio.gather(*tasks)

        enriched: list[OptionContract] = []

        for contract, market in zip(contracts, markets):

            underlying_price = (
                market.underlying_price
                if market.underlying_price is not None
                else fallback_underlying_price
            )

            enriched.append(
                replace(
                    contract,

                    # Underlying
                    underlying_price=underlying_price,

                    # Prices
                    bid=market.bid,
                    ask=market.ask,
                    last=market.last,
                    mark=market.mark,

                    # Greeks
                    delta=market.delta,
                    gamma=market.gamma,
                    theta=market.theta,
                    vega=market.vega,
                    implied_volatility=market.implied_volatility,

                    # Liquidity
                    volume=market.volume,
                    open_interest=market.open_interest,
                )
            )

        return enriched