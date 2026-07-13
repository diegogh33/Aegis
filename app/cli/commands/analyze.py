from __future__ import annotations

import asyncio
from datetime import date, timedelta
from decimal import Decimal

from rich.console import Console
from rich.table import Table

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

        option_chain = await ibkr_provider.get_option_chain(ticker)

        console.print()

        table = Table(title="Option Chain")

        table.add_column("Exchange")
        table.add_column("Expirations", justify="right")
        table.add_column("Strikes", justify="right")

        table.add_row(
            option_chain["exchange"],
            str(len(option_chain["expirations"])),
            str(len(option_chain["strikes"])),
        )

        console.print(table)

        put_contracts = await ibkr_provider.get_put_contracts(ticker)

        console.print(
            f"\nFound [bold]{len(put_contracts)}[/] PUT contracts."
        )

        if put_contracts:

            first = put_contracts[0]

            market = await ibkr_provider.get_market_data(first)

            table = Table(title="First PUT Contract")

            table.add_column("Field")
            table.add_column("Value")

            table.add_row("Local Symbol", first.local_symbol)
            table.add_row("Expiration", str(first.expiration))
            table.add_row("Strike", str(first.strike))
            table.add_row("Type", first.option_type.upper())

            table.add_row(
                "Bid",
                "-" if market.bid is None else str(market.bid),
            )

            table.add_row(
                "Ask",
                "-" if market.ask is None else str(market.ask),
            )

            table.add_row(
                "Last",
                "-" if market.last is None else str(market.last),
            )

            table.add_row(
                "Volume",
                "-" if market.volume is None else str(market.volume),
            )

            console.print()
            console.print(table)

        company = await alpha_provider.get_company(ticker)

        option = OptionContract(
            underlying=company.symbol,
            local_symbol="",
            con_id=0,
            option_type="put",
            expiration=date.today() + timedelta(days=30),
            strike=Decimal("0"),
            exchange="SMART",
            currency="USD",
            multiplier=100,
            bid=None,
            ask=None,
            last=None,
            mark=None,
            delta=None,
            gamma=None,
            theta=None,
            vega=None,
            implied_volatility=None,
            volume=None,
            open_interest=None,
        )

        engine = HardFilterEngine()

        results = engine.evaluate(
            company=company,
            option=option,
        )

        company_table = Table(title="Company")

        company_table.add_column("Field")
        company_table.add_column("Value")

        company_table.add_row("Name", company.name)
        company_table.add_row("Ticker", company.symbol)
        company_table.add_row("Exchange", company.exchange)
        company_table.add_row("Sector", company.sector)
        company_table.add_row("Industry", company.industry)
        company_table.add_row("Market Cap", f"{company.market_cap:,}")

        console.print()
        console.print(company_table)

        filters = Table(title="Hard Filters")

        filters.add_column("Status")
        filters.add_column("Filter")

        for result in results:

            icon = "✅" if result.status.value == "passed" else "❌"

            filters.add_row(
                icon,
                result.name,
            )

        console.print()
        console.print(filters)

        console.print("\n[bold green]Analysis completed[/]")

    finally:

        await alpha_provider.close()
        await ibkr_provider.disconnect()