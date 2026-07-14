from ib_async import IB, Stock
import asyncio

async def main():
    ib = IB()

    await ib.connectAsync("127.0.0.1", 7496, clientId=999)

    # Fuerza datos retrasados
    ib.reqMarketDataType(3)

    stock = Stock("AAPL", "SMART", "USD")
    await ib.qualifyContractsAsync(stock)

    ticker = ib.reqMktData(stock)

    await asyncio.sleep(5)

    print("MarketDataType:", ticker.marketDataType)
    print("Bid:", ticker.bid)
    print("Ask:", ticker.ask)
    print("Last:", ticker.last)
    print("Market:", ticker.marketPrice())

    ib.disconnect()

asyncio.run(main())