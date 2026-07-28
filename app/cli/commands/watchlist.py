from __future__ import annotations

import asyncio
import time
from decimal import Decimal
from typing import Optional

import typer
from rich.console import Console

from app.cli.shared import TickerSummary, build_summary, print_summary_table
from app.config.settings import Settings
from app.models.analysis_result import AnalysisResult
from app.providers.alphavantage.provider import AlphaVantageProvider
from app.providers.atlas.provider import AtlasProvider
from app.providers.ibkr.provider import IBKRProvider
from app.services.analysis_service import AnalysisService

console = Console()

# A ticker is eligible for analysis if its current price is at or
# below buy_price * (1 + PRICE_MARGIN). Confirmed with Diego:
# 10% above entrada_max is the threshold.
PRICE_MARGIN = Decimal("0.10")


def watchlist(
    tickers: Optional[list[str]] = typer.Argument(
        default=None,
        help="Tickers to analyze. If omitted, analyzes all tickers in ATLAS.",
    ),
    currency: str = "USD",
    long_term: bool = False,
) -> None:
    """
    Analyzes multiple tickers and shows a summary table.

    Without arguments: analyzes all tickers in ATLAS (alcista,
    posicion, seguimiento), approved ones first. Applies two automatic
    filters: tickers in watchlist.exclude (constitution.yaml) are
    skipped, and tickers whose price is more than 10% above their
    ATLAS buy-zone ceiling are also skipped.

    With tickers: analyzes exactly those tickers without any filters.

    Combinable with --long-term and --currency EUR.
    """
    asyncio.run(
        _watchlist(
            tickers=tickers or [],
            currency=currency,
            long_term=long_term,
        )
    )


async def _watchlist(
    tickers: list[str],
    currency: str,
    long_term: bool,
) -> None:

    alpha = AlphaVantageProvider()
    ibkr = IBKRProvider()
    atlas = AtlasProvider()

    try:

        console.rule("[bold blue]Aegis — Watchlist[/]")

        if long_term:
            console.print(
                "[bold]Mode: long-term opportunistic (90-365 DTE)[/]"
            )

        console.print("[bold]Connecting to IBKR...[/]")
        await ibkr.connect()
        console.print("[green]✓ Connected[/]\n")

        t_start = time.monotonic()

        service = AnalysisService(
            alpha_provider=alpha,
            ibkr_provider=ibkr,
            atlas_provider=atlas,
        )

        # Filters only apply to the automatic ATLAS scan.
        apply_filters = not bool(tickers)

        # Load exclude list from constitution.yaml (only for auto scan)
        excluded: set[str] = set()
        if apply_filters:
            settings = Settings()
            try:
                excluded = set(
                    t.upper()
                    for t in settings.get("watchlist", "exclude")
                )
            except Exception:
                pass  # section not present — no exclusions

        # Build the list of tickers and their ATLAS metadata.
        if tickers:
            ticker_list = [t.upper() for t in tickers]
            atlas_map: dict[str, str | None] = {}
            buy_price_map: dict[str, Decimal | None] = {}
            for t in ticker_list:
                entry = await atlas.get_entry(t)
                atlas_map[t] = entry.valoracion if entry else None
                buy_price_map[t] = (
                    Decimal(str(entry.entrada_max))
                    if entry and entry.entrada_max
                    else None
                )
        else:
            all_entries = await atlas.get_all_entries()
            ticker_list = [e.ticker for e in all_entries]
            atlas_map = {e.ticker: e.valoracion for e in all_entries}
            buy_price_map = {
                e.ticker: (
                    Decimal(str(e.entrada_max))
                    if e.entrada_max
                    else None
                )
                for e in all_entries
            }

        if not ticker_list:
            console.print(
                "[yellow]No tickers found. Add analyses to your ATLAS "
                "library or pass tickers explicitly.[/]"
            )
            return

        console.print(
            f"Checking [bold]{len(ticker_list)}[/] ticker(s)...\n"
        )

        summaries: list[TickerSummary] = []
        skipped = 0
        errors = 0

        for i, ticker in enumerate(ticker_list, 1):

            valoracion = atlas_map.get(ticker)
            buy_price = buy_price_map.get(ticker)

            label = f"[{i}/{len(ticker_list)}] {ticker}"
            if valoracion:
                label += f" ({valoracion})"

            # Exclude list filter
            if apply_filters and ticker in excluded:
                console.print(
                    f"  {label}... [dim]excluded (watchlist.exclude)[/]"
                )
                skipped += 1
                continue

            # Price filter
            if apply_filters and buy_price is not None:

                current_price = await ibkr.get_underlying_price(
                    ticker,
                    currency=currency,
                )

                if current_price is not None:
                    ceiling = buy_price * (1 + PRICE_MARGIN)
                    if current_price > ceiling:
                        pct_above = (
                            (current_price - buy_price) / buy_price * 100
                        )
                        console.print(
                            f"  {label}... "
                            f"[dim]skipped "
                            f"({current_price:.2f} is {pct_above:.1f}% "
                            f"above buy zone {buy_price:.2f})[/]"
                        )
                        skipped += 1
                        continue

            console.print(f"  {label}...", end=" ")

            try:
                result: AnalysisResult = await service.analyze(
                    ticker,
                    currency=currency,
                    long_term=long_term,
                )

                summary = build_summary(ticker, valoracion, result)
                console.print(
                    f"[green]{len(result.contracts)} candidate(s)[/]"
                    if result.contracts
                    else "[dim]no candidates[/]"
                )
                summaries.append(summary)

            except Exception as exc:
                # Errors (no option chain, can't qualify contract, etc.)
                # are shown inline but excluded from the summary table —
                # they don't represent a real analysis result.
                console.print(f"[red]error: {exc}[/]")
                errors += 1

        print_summary_table(summaries, long_term)

        elapsed = time.monotonic() - t_start
        mins, secs = divmod(int(elapsed), 60)
        elapsed_str = f"{mins}m {secs}s" if mins else f"{secs}s"

        if skipped:
            console.print(
                f"[dim]{skipped} ticker(s) skipped (excluded or above "
                f"buy zone).[/]"
            )
        if errors:
            console.print(
                f"[dim]{errors} ticker(s) errored (no options chain or "
                f"contract qualification failed — see log above).[/]"
            )
        console.print(f"[dim]Total time: {elapsed_str}[/]")

    except Exception as exc:
        from app.cli.errors import print_error
        print_error(exc)

    finally:

        await alpha.close()
        await ibkr.disconnect()
        await atlas.close()

