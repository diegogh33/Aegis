from __future__ import annotations

import asyncio
from collections import Counter
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from app.models.analysis_result import AnalysisResult
from app.providers.alphavantage.provider import AlphaVantageProvider
from app.providers.atlas.provider import AtlasProvider
from app.providers.ibkr.provider import IBKRProvider
from app.services.analysis_service import AnalysisService

console = Console()

# A ticker is eligible for analysis if its current price is at or
# below buy_price * (1 + PRICE_MARGIN). Confirmed with Diego:
# 10% above entrada_max is the threshold - beyond that, the stock
# isn't in or near the buy zone and there's no point scanning options.
PRICE_MARGIN = Decimal("0.10")


@dataclass
class TickerSummary:
    ticker: str
    atlas_valoracion: str | None
    candidates: int
    best_score: float | None
    best_strike: str | None
    best_expiration: str | None
    best_otm_pct: str | None
    top_rejection: str | None


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
    posicion, seguimiento), approved ones first. Tickers whose current
    price is more than 10% above their ATLAS buy-zone ceiling
    (entrada_max) are skipped automatically - no point scanning options
    for a stock that isn't near its buy zone.

    With tickers: analyzes exactly those tickers, regardless of
    whether they exist in ATLAS. Tickers without an ATLAS entry (no
    entrada_max) are always analyzed.

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

        service = AnalysisService(
            alpha_provider=alpha,
            ibkr_provider=ibkr,
            atlas_provider=atlas,
        )

        # Build the list of tickers and their ATLAS metadata.
        # buy_price_map holds entrada_max per ticker (None = no ceiling).
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

        # Price filter only applies when scanning ATLAS automatically
        # (no explicit tickers). When the user passes tickers
        # explicitly, they've already decided to analyze them.
        apply_price_filter = not bool(tickers)

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

        for i, ticker in enumerate(ticker_list, 1):

            valoracion = atlas_map.get(ticker)
            buy_price = buy_price_map.get(ticker)

            label = f"[{i}/{len(ticker_list)}] {ticker}"
            if valoracion:
                label += f" ({valoracion})"

            # Price filter: if we have a buy_price ceiling from ATLAS,
            # fetch the current stock price first (one lightweight
            # request) and skip immediately if the stock is more than
            # PRICE_MARGIN above that ceiling. This avoids burning
            # dozens of IBKR option-chain requests on tickers that
            # aren't near their buy zone.
            if apply_price_filter and buy_price is not None:

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

                if result.contracts:

                    best = result.contracts[0]
                    option = best.option

                    if (
                        option.underlying_price is not None
                        and option.underlying_price > 0
                    ):
                        diff = option.underlying_price - option.strike
                        otm_pct_val = diff / option.underlying_price * 100
                        otm_str = (
                            f"{otm_pct_val:.1f}% OTM"
                            if otm_pct_val >= 0
                            else f"{abs(otm_pct_val):.1f}% ITM"
                        )
                    else:
                        otm_str = None

                    summary = TickerSummary(
                        ticker=ticker,
                        atlas_valoracion=valoracion,
                        candidates=len(result.contracts),
                        best_score=float(best.score.total),
                        best_strike=str(option.strike),
                        best_expiration=str(option.expiration),
                        best_otm_pct=otm_str,
                        top_rejection=None,
                    )
                    console.print(
                        f"[green]{len(result.contracts)} candidate(s)[/]"
                    )

                else:

                    top_reason = None
                    if result.rejected:
                        counts = Counter(
                            r.reason for r in result.rejected
                        )
                        top_reason = counts.most_common(1)[0][0]

                    summary = TickerSummary(
                        ticker=ticker,
                        atlas_valoracion=valoracion,
                        candidates=0,
                        best_score=None,
                        best_strike=None,
                        best_expiration=None,
                        best_otm_pct=None,
                        top_rejection=top_reason,
                    )
                    console.print("[dim]no candidates[/]")

            except Exception as exc:
                summary = TickerSummary(
                    ticker=ticker,
                    atlas_valoracion=valoracion,
                    candidates=0,
                    best_score=None,
                    best_strike=None,
                    best_expiration=None,
                    best_otm_pct=None,
                    top_rejection=f"ERROR: {exc}",
                )
                console.print(f"[red]error: {exc}[/]")

            summaries.append(summary)

        # Summary table — only shows tickers that were actually analyzed
        console.print()
        console.rule("[bold]Summary[/]")
        console.print()

        if summaries:

            summary_table = Table(
                title=(
                    "Watchlist — Long-Term Candidates"
                    if long_term
                    else "Watchlist — Best PUT Candidates"
                )
            )

            summary_table.add_column("Ticker", style="bold")
            summary_table.add_column("ATLAS")
            summary_table.add_column("Candidates", justify="right")
            summary_table.add_column("Best Score", justify="right")
            summary_table.add_column("Best Strike", justify="right")
            summary_table.add_column("OTM%", justify="right")
            summary_table.add_column("Expiration")
            summary_table.add_column("Notes")

            for s in summaries:

                atlas_cell = s.atlas_valoracion or "-"

                if s.candidates > 0:
                    summary_table.add_row(
                        s.ticker,
                        atlas_cell,
                        str(s.candidates),
                        f"{s.best_score:.1f}",
                        s.best_strike or "-",
                        s.best_otm_pct or "-",
                        s.best_expiration or "-",
                        "",
                    )
                else:
                    summary_table.add_row(
                        f"[dim]{s.ticker}[/]",
                        f"[dim]{atlas_cell}[/]",
                        "[dim]0[/]",
                        "[dim]-[/]",
                        "[dim]-[/]",
                        "[dim]-[/]",
                        "[dim]-[/]",
                        f"[dim]{s.top_rejection or ''}[/]",
                    )

            console.print(summary_table)

        with_candidates = [s for s in summaries if s.candidates > 0]
        analyzed = len(summaries)

        console.print(
            f"\n[bold green]{len(with_candidates)} of {analyzed} "
            f"analyzed ticker(s) have candidates.[/]"
        )
        if skipped:
            console.print(
                f"[dim]{skipped} ticker(s) skipped — price more than "
                f"{int(PRICE_MARGIN * 100)}% above ATLAS buy zone.[/]"
            )

    finally:

        await alpha.close()
        await ibkr.disconnect()
        await atlas.close()
