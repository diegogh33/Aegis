from __future__ import annotations

from typing import Any

import httpx

from app.config.settings import settings
from app.providers.alphavantage.endpoints import OVERVIEW


class AlphaVantageClient:
    """
    Minimal Alpha Vantage HTTP client.

    Responsible only for communicating with the Alpha Vantage API.
    No business logic should live here.
    """

    BASE_URL = "https://www.alphavantage.co/query"

    def __init__(self) -> None:

        self._client = httpx.AsyncClient(
            timeout=30,
        )

    async def _request(
        self,
        **params: Any,
    ) -> dict[str, Any]:

        params["apikey"] = settings.alpha_vantage_api_key

        response = await self._client.get(
            self.BASE_URL,
            params=params,
        )

        response.raise_for_status()

        data = response.json()

        if "Information" in data:
            raise RuntimeError(data["Information"])

        if "Error Message" in data:
            raise RuntimeError(data["Error Message"])

        return data

    async def get_company_overview(
        self,
        symbol: str,
    ) -> dict[str, Any]:

        return await self._request(
            function=OVERVIEW,
            symbol=symbol,
        )

    async def close(self) -> None:

        await self._client.aclose()