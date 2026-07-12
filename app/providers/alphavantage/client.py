from __future__ import annotations

import httpx


class AlphaVantageClient:
    """
    Thin HTTP client responsible for communicating with
    Alpha Vantage.
    """

    BASE_URL = "https://www.alphavantage.co/query"

    def __init__(
        self,
        api_key: str,
    ):

        self.api_key = api_key

        self.client = httpx.AsyncClient(
            timeout=30,
        )

    async def get(
        self,
        **params,
    ):

        params["apikey"] = self.api_key

        response = await self.client.get(
            self.BASE_URL,
            params=params,
        )

        response.raise_for_status()

        return response.json()