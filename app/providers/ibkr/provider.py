from __future__ import annotations

from ib_async import IB, Stock


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

    async def connect(self) -> None:
        await self.ib.connectAsync(
            host=self._host,
            port=self._port,
            clientId=self._client_id,
        )

    async def disconnect(self) -> None:
        if self.ib.isConnected():
            self.ib.disconnect()

    async def get_option_chain(self, symbol: str) -> dict:

        # Contrato de la acción
        stock = Stock(symbol, "SMART", "USD")

        qualified = await self.ib.qualifyContractsAsync(stock)

        if not qualified:
            raise ValueError(f"Unable to qualify contract for {symbol}")

        contract = qualified[0]

        # Obtener parámetros de la cadena de opciones
        chains = await self.ib.reqSecDefOptParamsAsync(
            contract.symbol,
            "",
            contract.secType,
            contract.conId,
        )

        if not chains:
            raise ValueError(f"No option chain found for {symbol}")

        # Preferimos SMART si existe
        chain = next(
            (c for c in chains if c.exchange == "SMART"),
            chains[0],
        )

        return {
            "exchange": chain.exchange,
            "expirations": sorted(chain.expirations),
            "strikes": sorted(chain.strikes),
        }