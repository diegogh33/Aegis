from __future__ import annotations

from ib_async import IB


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