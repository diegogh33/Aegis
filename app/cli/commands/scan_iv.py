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

        if results:
            from loguru import logger
            item0 = results[0]
            logger.debug(
                "Scanner returned {n} results. First item symbol={sym}",
                n=len(results),
                sym=(item0.contractDetails.contract.symbol  # type: ignore[union-attr]
                     if item0.contractDetails and item0.contractDetails.contract
                     else "?"),
            )

        # Collect tickers and contracts from scanner
        from ib_async import Contract as IBContract
        scanner_items: list[IBContract] = []
        for item in results:
            cd = item.contractDetails
            if cd and cd.contract and cd.contract.symbol:
                scanner_items.append(cd.contract)  # type: ignore[arg-type]

        if not scanner_items:
            console.print("[yellow]Scanner returned no valid contracts.[/]")
            return

        console.print(
            f"Fetching price and IV for {len(scanner_items)} tickers...\n"
        )

        # Fetch price and IV for each ticker via market data
        from ib_async import Stock
        import math

        rows: list[tuple[str, float | None, float | None]] = []
        for contract in scanner_items[:top]:
            ticker_sym = contract.symbol
            try:
                stock = Stock(ticker_sym, "SMART", "USD")
                qualified_list = await ibkr.ib.qualifyContractsAsync(stock)
                if not qualified_list or qualified_list[0] is None:
                    rows.append((ticker_sym, None, None))
                    continue

                q = qualified_list[0]
                ibkr.ib.reqMktData(q, "106", False, False)  # type: ignore[arg-type]
                await asyncio.sleep(2)
                t = ibkr.ib.ticker(q)  # type: ignore[arg-type]

                price: float | None = None
                iv: float | None = None

                if t:
                    bid = t.bid
                    ask = t.ask
                    if bid and ask and not math.isnan(bid) and not math.isnan(ask) and bid > 0:
                        price = (bid + ask) / 2
                    elif t.last and not math.isnan(t.last):
                        price = t.last

                    if t.impliedVolatility and not math.isnan(t.impliedVolatility):
                        iv = t.impliedVolatility * 100

                ibkr.ib.cancelMktData(q)  # type: ignore[arg-type]
                rows.append((ticker_sym, price, iv))

            except Exception:
                rows.append((ticker_sym, None, None))

        # Sort by IV descending
        rows.sort(key=lambda r: r[2] if r[2] is not None else -1, reverse=True)

        table = Table(
            title=f"High IV Stocks — US Market "
                  f"(top {len(rows)}, sorted by IV desc)"
        )

        table.add_column("#", justify="right", width=3)
        table.add_column("Ticker", style="bold")
        table.add_column("Precio", justify="right")
        table.add_column("IV", justify="right")

        for i, (ticker_sym, price, iv) in enumerate(rows, 1):
            price_str = f"${price:.2f}" if price else "—"
            iv_str = f"{iv:.1f}%" if iv else "—"

            if iv and iv >= 80:
                iv_str = f"[bold green]{iv_str}[/]"
            elif iv and iv >= 50:
                iv_str = f"[green]{iv_str}[/]"
            elif iv and iv >= 30:
                iv_str = f"[yellow]{iv_str}[/]"

            table.add_row(str(i), ticker_sym, price_str, iv_str)

        console.print(table)
        console.print(
            "\n[dim]Verde intenso: IV ≥80% (excelente para venta de primas). "
            "Verde: IV ≥50%. Amarillo: IV ≥30%.[/]"
        )
        console.print(
            "[dim]Ejecuta [bold]uv run python -m app.main TICKER --pcs[/] "
            "para análisis PCS completo de cualquier candidato.[/]"
        )

    except Exception as exc:
        from app.cli.errors import print_error
        print_error(exc)

    finally:
        await ibkr.disconnect()
