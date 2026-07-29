from __future__ import annotations

import asyncio

import typer
from rich.console import Console
from rich.table import Table

from app.providers.ibkr.provider import IBKRProvider

console = Console()


def scan_iv(
    top: int = typer.Option(
        25,
        "--top",
        help="Number of results to return (default: 25, max: 50).",
    ),
    min_price: float = typer.Option(
        10.0,
        "--min-price",
        help="Minimum stock price filter (default: $10).",
    ),
    min_opt_volume: int = typer.Option(
        500,
        "--min-opt-volume",
        help="Minimum daily option volume (default: 500).",
    ),
) -> None:
    """
    Scans the entire US market for stocks with the highest implied
    volatility — ideal for identifying new PUT selling opportunities
    beyond the configured S2 universe.

    Uses IBKR's built-in market scanner (HIGH_OPT_IMP_VOLAT) which
    covers all US-listed stocks and ETFs in real time. No predefined
    list needed — the market itself is the universe.

    Results are sorted by IV descending. Use --min-price and
    --min-opt-volume to filter out illiquid or cheap stocks.
    """
    asyncio.run(
        _scan_iv(
            top=min(top, 50),
            min_price=min_price,
            min_opt_volume=min_opt_volume,
        )
    )


async def _scan_iv(
    top: int,
    min_price: float,
    min_opt_volume: int,
) -> None:

    from ib_async import ScannerSubscription

    ibkr = IBKRProvider()

    try:

        console.rule("[bold blue]Aegis — IV Scanner[/]")
        console.print(
            f"Scanning US market for highest IV stocks "
            f"(min price ${min_price:.0f}, "
            f"min opt volume {min_opt_volume:,})...\n"
        )
        console.print("[bold]Connecting to IBKR...[/]")
        await ibkr.connect()
        console.print("[green]✓ Connected[/]\n")

        from ib_async import TagValue

        sub = ScannerSubscription(
            instrument="STK",
            locationCode="STK.US.MAJOR",
            scanCode="HIGH_OPT_IMP_VOLAT",
            abovePrice=min_price,
            numberOfRows=top,
        )

        # Additional filter tags for option volume minimum
        filter_options = [
            TagValue("optVolumeAbove", str(min_opt_volume)),
        ]

        results = await ibkr.ib.reqScannerDataAsync(
            sub,
            scannerSubscriptionFilterOptions=filter_options,
        )

        if not results:
            console.print(
                "[yellow]No results from scanner. "
                "Try relaxing the filters.[/]"
            )
            return

        console.print(
            f"[green]Found {len(results)} candidates.[/]\n"
        )

        table = Table(
            title=f"High IV Stocks — US Market "
                  f"(top {len(results)}, sorted by IV desc)"
        )

        table.add_column("#", justify="right", width=3)
        table.add_column("Ticker", style="bold")
        table.add_column("Company")
        table.add_column("Precio", justify="right")
        table.add_column("IV", justify="right")
        table.add_column("Distance", justify="right")

        if results:
            # Log the first item's structure for diagnosis
            item0 = results[0]
            from loguru import logger
            logger.debug(
                "ScanData fields: rank={rank}, distance={dist}, "
                "benchmark={bench}, projection={proj}, "
                "contractDetails type={cd_type}, "
                "contractDetails={cd}",
                rank=item0.rank,
                dist=item0.distance,
                bench=item0.benchmark,
                proj=item0.projection,
                cd_type=type(item0.contractDetails).__name__,
                cd=item0.contractDetails,
            )

        for i, item in enumerate(results, 1):
            cd = item.contractDetails
            contract = cd.contract if cd else None
            ticker = contract.symbol if contract else "—"
            company = cd.longName[:35] if (cd and cd.longName) else "—"

            # distance is the IV rank metric from IBKR scanner
            # benchmark is the actual IV value when available
            iv_str = f"{float(item.benchmark):.1f}%" if item.benchmark else "—"
            dist_str = f"{float(item.distance):.1f}" if item.distance else "—"

            table.add_row(
                str(i),
                ticker,
                company,
                "—",   # real-time price requires a separate mkt data request
                iv_str,
                dist_str,
            )

        console.print(table)
        console.print(
            "\n[dim]'IV': implied volatility reported by the scanner. "
            "'Distance': IBKR's IV rank metric (higher = more elevated "
            "vs historical norm).[/]"
        )
        console.print(
            "[dim]Run [bold]uv run python -m app.main TICKER --pcs[/] "
            "on any of these for a full PCS analysis.[/]"
        )

    except Exception as exc:
        from app.cli.errors import print_error
        print_error(exc)

    finally:
        await ibkr.disconnect()
