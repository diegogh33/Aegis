from __future__ import annotations

import asyncio
from dataclasses import replace

from loguru import logger

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
        exchange: str = "SMART",
        currency: str = "USD",
        batch_size: int = 6,
        dte_window: dict | None = None,
        target_delta: float | None = None,
    ) -> list[OptionContract]:

        contracts = await self.provider.get_put_contracts(
            symbol,
            exchange=exchange,
            currency=currency,
            dte_window=dte_window,
            target_delta=target_delta,
        )

        # El precio del subyacente se pide una sola vez por escaneo.
        # Esto existe porque, cuando la cuenta de IBKR no tiene
        # suscripción de datos de opciones (error 10091), el
        # underlying_price de cada opción individual llega vacío,
        # pero el precio de la propia acción normalmente sí está
        # disponible.
        fallback_underlying_price = await self.provider.get_underlying_price(
            symbol, exchange=exchange, currency=currency
        )

        # Se piden en lotes pequeños en vez de todos a la vez.
        # Confirmado con ACN (32 contratos): pedirlos todos con
        # asyncio.gather() puede saturar el límite de IBKR de 50
        # mensajes/segundo, dejando un vencimiento entero sin Greeks
        # aunque el mercado real tenga liquidez normal - no era falta
        # de datos, era la propia petición saturando la conexión.
        markets: list[MarketData] = []

        for i in range(0, len(contracts), batch_size):

            batch = contracts[i : i + batch_size]

            tasks = [
                self.provider.get_market_data(contract)
                for contract in batch
            ]

            markets.extend(await asyncio.gather(*tasks))

        enriched: list[OptionContract] = []

        for contract, market in zip(contracts, markets):

            underlying_price = (
                market.underlying_price
                if market.underlying_price is not None
                else fallback_underlying_price
            )

            enriched_contract = replace(
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

            logger.debug(
                "{symbol} {expiration} strike={strike}: delta={delta}, "
                "iv={iv}, bid={bid}, ask={ask}",
                symbol=symbol,
                expiration=enriched_contract.expiration,
                strike=enriched_contract.strike,
                delta=enriched_contract.delta,
                iv=enriched_contract.implied_volatility,
                bid=enriched_contract.bid,
                ask=enriched_contract.ask,
            )

            enriched.append(enriched_contract)

        return enriched