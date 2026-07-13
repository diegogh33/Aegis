import asyncio

from app.providers.alphavantage.provider import AlphaVantageProvider


async def main():
    provider = AlphaVantageProvider()

    try:
        company = await provider.get_company("SAP")

        print(company)
        print()
        print(company.name)
        print(company.market_cap)
        print(company.pe_ratio)

    finally:
        await provider.close()


asyncio.run(main())