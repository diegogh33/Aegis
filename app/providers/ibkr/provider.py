from __future__ import annotations

from decimal import Decimal

from ib_async import Contract, IB, Option, Stock
from loguru import logger

from app.models.market_data import MarketData
from app.models.option_contract import OptionContract
from app.providers.ibkr.mapper import IBKRMapper
from app.providers.ibkr.market_data import MarketDataProvider


def _as_single_contract(
    qualified: Contract | list[Contract | None] | None,
) -> Contract | None:
    """
    Normalizes one element of qualifyContractsAsync()'s result list
    into a single Contract or None.

    qualifyContractsAsync(*contracts) returns one entry per input
    contract, but each entry's static type is
    `Contract | list[Contract | None] | None` - the list case exists
    in the library for ambiguous contracts that could expand into
    several matches. For a well-formed Stock/Option request, that
    never actually happens in practice, but this makes the assumption
    explicit and mypy-verifiable instead of silently trusting it.
    """

    if isinstance(qualified, Contract):
        return qualified

    if isinstance(qualified, list):
        return qualified[0] if qualified else None

    return None


class IBKRProvider:
    """
    Wrapper around the Interactive Brokers API.
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 7496,
        client_id: int = 1,
    ) -> None:

        self._host = host
        self._port = port
        self._client_id = client_id

        self.ib = IB()

        self.market_data = MarketDataProvider(self.ib)

        self._contracts: dict[int, Contract] = {}
        self._stock_contracts: dict[str, Contract] = {}

    async def connect(self) -> None:

        await self.ib.connectAsync(
            host=self._host,
            port=self._port,
            clientId=self._client_id,
        )

        #
        # La cuenta tiene suscripción de datos en tiempo real
        # (US Securities Snapshot and Futures Value Bundle +
        # US Equity and Options Add-On Streaming Bundle), así que
        # pedimos datos en vivo en vez de forzar delayed.
        #
        self.ib.reqMarketDataType(1)

    async def disconnect(self) -> None:

        if self.ib.isConnected():
            self.ib.disconnect()

    async def get_option_chain(
        self,
        symbol: str,
        exchange: str = "SMART",
        currency: str = "USD",
    ) -> dict:

        stock = Stock(symbol, exchange, currency)

        qualified = await self.ib.qualifyContractsAsync(stock)

        stock_contract = (
            _as_single_contract(qualified[0]) if qualified else None
        )

        if stock_contract is None:
            raise ValueError(f"Unable to qualify contract for {symbol}")

        self._stock_contracts[symbol] = stock_contract

        chains = await self.ib.reqSecDefOptParamsAsync(
            stock_contract.symbol,
            "",
            stock_contract.secType,
            stock_contract.conId,
        )

        if not chains:
            raise ValueError(f"No option chain found for {symbol}")

        chain = next(
            (c for c in chains if c.exchange == "SMART"),
            chains[0],
        )

        expirations = sorted(chain.expirations)

        logger.debug(
            "{symbol}: {count} expirations available on {exchange}: "
            "{expirations}",
            symbol=symbol,
            count=len(expirations),
            exchange=chain.exchange,
            expirations=", ".join(expirations),
        )

        return {
            "contract": stock_contract,
            "exchange": chain.exchange,
            "expirations": sorted(chain.expirations),
            "strikes": sorted(chain.strikes),
        }

    async def get_underlying_price(
        self,
        symbol: str,
        exchange: str = "SMART",
        currency: str = "USD",
    ) -> Decimal | None:
        """
        Returns the current market price of the underlying stock,
        independent of any option contract's own market data.

        Requires get_option_chain(symbol) to have been called first
        for this symbol (it qualifies and caches the stock contract).
        Falls back to a fresh qualification if that hasn't happened.
        """

        stock_contract = self._stock_contracts.get(symbol)

        if stock_contract is None:

            stock = Stock(symbol, exchange, currency)

            qualified = await self.ib.qualifyContractsAsync(stock)

            stock_contract = (
                _as_single_contract(qualified[0]) if qualified else None
            )

            if stock_contract is None:
                return None

            self._stock_contracts[symbol] = stock_contract

        return await self.market_data.get_stock_price(stock_contract)

    async def get_put_contracts(
        self,
        symbol: str,
        exchange: str = "SMART",
        currency: str = "USD",
    ) -> list[OptionContract]:

        chain = await self.get_option_chain(
            symbol, exchange=exchange, currency=currency
        )

        contracts: list[OptionContract] = []

        for expiration in chain["expirations"][:2]:

            option = Option(
                symbol=symbol,
                lastTradeDateOrContractMonth=expiration,
                strike=0,
                right="P",
                exchange=chain["exchange"],
                currency=currency,
            )

            details = await self.ib.reqContractDetailsAsync(option)

            for detail in details:

                contract = detail.contract

                if contract is None:
                    continue

                option_contract = IBKRMapper.option_contract(contract)

                self._contracts[
                    option_contract.con_id
                ] = contract

                contracts.append(option_contract)

        contracts.sort(
            key=lambda c: (
                c.expiration,
                c.strike,
            )
        )

        return contracts

    async def get_market_data(
        self,
        option: OptionContract,
    ) -> MarketData:

        contract = self._contracts.get(option.con_id)

        if contract is None:
            raise ValueError(
                f"Contract {option.con_id} not found."
            )

        return await self.market_data.get(contract)