import asyncio

from app.providers.alphavantage.client import AlphaVantageClient


async def main():
    client = AlphaVantageClient()

    try:
        company = await client.get_company_overview("SAP")

        print(company["Name"])
        print(company["Symbol"])
        print(company["Currency"])
        print(company["MarketCapitalization"])

    finally:
        await client.close()


asyncio.run(main())

async def get_option_chain(self, symbol: str) -> dict:
    return await self._request(
        function="HISTORICAL_OPTIONS",
        symbol=symbol,
    )