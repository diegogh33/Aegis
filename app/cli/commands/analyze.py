from __future__ import annotations

import asyncio
from collections import Counter

from rich.console import Console
from rich.table import Table

from app.providers.alphavantage.provider import AlphaVantageProvider
from app.providers.ibkr.provider import IBKRProvider
from app.services.analysis_service import AnalysisService

console = Console()


def analyze(
    ticker: str,
    exchange: str = "SMART",
    currency: str = "USD",
) -> None:
    """
    Analyzes a ticker's Cash Secured Put candidates.

    For non-US underlyings (e.g. Spanish stocks on MEFF), pass
    --currency EUR. --exchange usually stays "SMART" (IBKR's
    SmartRouting finds the right market) unless a specific routing
    is needed.
    """
    asyncio.run(_analyze(ticker, exchange=exchange, currency=currency))


async def _analyze(ticker: str, exchange: str, currency: str) -> None:

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

        result = await service.analyze(
            ticker, exchange=exchange, currency=currency
        )

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

        if result.rejected:

            reasons = Counter(item.reason for item in result.rejected)

            example_detail = {
                item.reason: item.detail for item in result.rejected
            }

            rejected_table = Table(title="Rejected Contracts")

            rejected_table.add_column("Reason")
            rejected_table.add_column("Count", justify="right")
            rejected_table.add_column("Example")

            for reason, count in reasons.most_common():
                rejected_table.add_row(
                    reason,
                    str(count),
                    example_detail[reason],
                )

            console.print()
            console.print(rejected_table)

        if not result.contracts:
            console.print(
                "\n[bold yellow]No candidates passed the Constitution "
                "or had usable market data.[/] See 'Rejected Contracts' "
                "above for why."
            )

        console.print("\n[bold green]Analysis completed[/]")

    finally:

        await alpha.close()
        await ibkr.disconnect()