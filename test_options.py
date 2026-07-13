import asyncio
import json

from app.providers.alphavantage.client import AlphaVantageClient


async def main():
    client = AlphaVantageClient()

    try:
        data = await client.get_option_chain("SAP")

        print(json.dumps(data, indent=2)[:5000])

    finally:
        await client.close()


asyncio.run(main())