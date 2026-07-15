from __future__ import annotations

import asyncio

from rich.console import Console
from rich.table import Table

from app.providers.alphavantage.provider import AlphaVantageProvider
from app.providers.ibkr.provider import IBKRProvider
from app.services.analysis_service import AnalysisService

console = Console()


def analyze(ticker: str) -> None:
    asyncio.run(_analyze(ticker))


async def _analyze(ticker: str) -> None:

    alpha = AlphaVantageProvider()
    ibkr = IBKRProvider()

    try:

        console.rule("[bold blue]Aegis[/]")

        console.print("[bold]Connecting to IBKR...[/]")

        await ibkr.connect()

        console.print("[green]✓ Connected[/]")

        service = AnalysisService(
            alpha_provider=alpha,
            ibkr_provider=ibkr,
        )

        result = await service.analyze(ticker)

        company = result.company

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

        options = Table(title="Best PUT Candidates")

        options.add_column("Score", justify="right")
        options.add_column("Strike", justify="right")
        options.add_column("Expiration")
        options.add_column("Bid", justify="right")
        options.add_column("Ask", justify="right")
        options.add_column("Delta", justify="right")
        options.add_column("IV", justify="right")
        options.add_column("Volume", justify="right")
        options.add_column("Recommendation")

        for scored in result.contracts:

            option = scored.option
            score = scored.score

            options.add_row(
                f"{score.total:.1f}",
                str(option.strike),
                str(option.expiration),
                "-" if option.bid is None else f"{option.bid:.2f}",
                "-" if option.ask is None else f"{option.ask:.2f}",
                "-" if option.delta is None else f"{option.delta:.3f}",
                "-" if option.implied_volatility is None else f"{option.implied_volatility:.2%}",
                "-" if option.volume is None else str(int(option.volume)),
                scored.evaluation.recommendation.value,
            )

        console.print()
        console.print(options)

        console.print("\n[bold green]Analysis completed[/]")

    finally:

        await alpha.close()
        await ibkr.disconnect()