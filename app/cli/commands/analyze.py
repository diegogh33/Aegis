from __future__ import annotations

import asyncio
from datetime import date, timedelta
from decimal import Decimal

from rich.console import Console

from app.engines.hard_filter_engine import HardFilterEngine
from app.models.option_contract import OptionContract
from app.providers.alphavantage.provider import AlphaVantageProvider
from app.providers.ibkr.provider import IBKRProvider

console = Console()


def analyze(ticker: str) -> None:
    asyncio.run(_analyze(ticker))


async def _analyze(ticker: str) -> None:

    alpha_provider = AlphaVantageProvider()
    ibkr_provider = IBKRProvider()

    try:
        console.rule("[bold blue]Aegis[/]")

        console.print("[bold]Connecting to IBKR...[/]")

        await ibkr_provider.connect()

        console.print("[green]✓ Connected to IBKR[/]")

        company = await alpha_provider.get_company(ticker)

        option = OptionContract(
            underlying=company.symbol,
            option_type="put",
            expiration=date.today() + timedelta(days=30),
            strike=Decimal("0"),
            bid=Decimal("0"),
            ask=Decimal("0"),
            last=None,
            mark=Decimal("0"),
            delta=None,
            gamma=None,
            theta=None,
            vega=None,
            implied_volatility=None,
            volume=0,
            open_interest=0,
        )

        engine = HardFilterEngine()

        results = engine.evaluate(
            company=company,
            option=option,
        )

        console.print()
        console.print("[bold]Company[/]")
        console.print(f"Name       : {company.name}")
        console.print(f"Ticker     : {company.symbol}")
        console.print(f"Exchange   : {company.exchange}")
        console.print(f"Sector     : {company.sector}")
        console.print(f"Industry   : {company.industry}")
        console.print(f"Market Cap : {company.market_cap:,}")

        console.print()
        console.print("[bold]Hard Filters[/]")

        for result in results:
            icon = "✅" if result.status.value == "passed" else "❌"
            console.print(f"{icon} {result.name}")

        console.print()
        console.print("[bold green]Analysis completed[/]")

    finally:
        await alpha_provider.close()
        await ibkr_provider.disconnect()