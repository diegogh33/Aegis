from __future__ import annotations

from ib_async import Contract, IB, Option, Stock

from app.models.market_data import MarketData
from app.models.option_contract import OptionContract
from app.providers.ibkr.mapper import IBKRMapper
from app.providers.ibkr.market_data import MarketDataProvider


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

    async def connect(self) -> None:

        await self.ib.connectAsync(
            host=self._host,
            port=self._port,
            clientId=self._client_id,
        )

        #
        # Utilizar datos retrasados cuando la API no tenga permisos
        # de tiempo real.
        #
        self.ib.reqMarketDataType(3)

    async def disconnect(self) -> None:

        if self.ib.isConnected():
            self.ib.disconnect()

    async def get_option_chain(self, symbol: str) -> dict:

        stock = Stock(symbol, "SMART", "USD")

        qualified = await self.ib.qualifyContractsAsync(stock)

        if not qualified:
            raise ValueError(f"Unable to qualify contract for {symbol}")

        stock_contract = qualified[0]

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

        return {
            "contract": stock_contract,
            "exchange": chain.exchange,
            "expirations": sorted(chain.expirations),
            "strikes": sorted(chain.strikes),
        }

    async def get_put_contracts(
        self,
        symbol: str,
    ) -> list[OptionContract]:

        chain = await self.get_option_chain(symbol)

        contracts: list[OptionContract] = []

        for expiration in chain["expirations"][:2]:

            option = Option(
                symbol=symbol,
                lastTradeDateOrContractMonth=expiration,
                strike=0,
                right="P",
                exchange=chain["exchange"],
            )

            details = await self.ib.reqContractDetailsAsync(option)

            for detail in details:

                contract = detail.contract

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