from __future__ import annotations

from app.models.company import Company
from app.providers.alphavantage.client import AlphaVantageClient
from app.providers.alphavantage.mapper import AlphaVantageMapper


class AlphaVantageProvider:
    """
    High level provider that exposes domain models instead of raw JSON.
    """

    def __init__(self) -> None:
        self._client = AlphaVantageClient()

    async def get_company(
        self,
        symbol: str,
    ) -> Company:
        raw = await self._client.get_company_overview(symbol)

        return AlphaVantageMapper.company(raw)

    async def close(self) -> None:
        await self._client.close()