from __future__ import annotations

from typing import Any

import httpx

from app.config.settings import settings
from app.providers.alphavantage.endpoints import OVERVIEW


class AlphaVantageUnavailableError(Exception):
    """
    Raised when Alpha Vantage's API itself signals a problem not
    specific to the requested ticker - most commonly a rate limit
    ("Information" field, e.g. the free tier's 25 requests/day cap),
    but also covers other explicit "Error Message" responses. Distinct
    from UnknownCompanyError (mapper.py), which means the ticker
    itself isn't recognized rather than the API being unavailable -
    callers may want to handle "try again later" differently from
    "this ticker needs a different symbol format".
    """


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
            raise AlphaVantageUnavailableError(data["Information"])

        if "Error Message" in data:
            raise AlphaVantageUnavailableError(data["Error Message"])

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