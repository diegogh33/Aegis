from __future__ import annotations

import asyncio
from decimal import Decimal

import typer
from rich.console import Console
from rich.table import Table

from app.config.settings import Settings
from app.providers.alphavantage.provider import AlphaVantageProvider
from app.providers.atlas.provider import AtlasProvider
from app.providers.ibkr.provider import IBKRProvider
from app.services.analysis_service import AnalysisService
from app.strategies.pcs import PCSCandidate, find_pcs_candidates

console = Console()


def scan_pcs(
    sleeve: str = typer.Argument(
        ...,
        help="Universe to scan: 's2' or 's3'.",
    ),
    currency: str = "USD",
    long_term: bool = False,
) -> None:
    """
    Scans the S2 or S3 universe for Put Credit Spread opportunities.

    Analyzes all tickers in the specified universe (from
    constitution.yaml s2_universe / s3_universe), finds all valid PCS
    combinations for each, and shows only the ones that pass all
    filters (credit/width ≥ 25%, OI ≥ 500 on both legs).

    Results are sorted by credit/width ratio descending — best
    opportunities first.

    Examples:
      uv run python -m app.main scan-pcs s2
      uv run python -m app.main scan-pcs s3
      uv run python -m app.main scan-pcs s2 --long-term
    """
    sleeve_key = sleeve.lower()
    if sleeve_key not in ("s2", "s3"):
        console.print(f"[red]Unknown sleeve '{sleeve}'. Use 's2' or 's3'.[/]")
        raise typer.Exit(1)

    asyncio.run(
        _scan_pcs(
            sleeve_key=sleeve_key,
            currency=currency,
            long_term=long_term,
        )
    )


async def _scan_pcs(
    sleeve_key: str,
    currency: str,
    long_term: bool,
) -> None:

    settings = Settings()

    try:
        universe_key = f"{sleeve_key}_universe"
        ticker_list: list[str] = settings.get(universe_key)
    except Exception:
        console.print(
            f"[red]{universe_key} not found in constitution.yaml.[/]"
        )
        return

    if not ticker_list:
        console.print(f"[yellow]{universe_key} is empty.[/]")
        return

    alpha = AlphaVantageProvider()
    ibkr = IBKRProvider()
    atlas = AtlasProvider()

    try:

        sleeve_label = sleeve_key.upper()
        console.rule(f"[bold blue]Aegis — Scan PCS {sleeve_label}[/]")

        if long_term:
            console.print("[bold]Mode: long-term (90-365 DTE)[/]")

        console.print("[bold]Connecting to IBKR...[/]")
        await ibkr.connect()
        console.print("[green]✓ Connected[/]\n")

        service = AnalysisService(
            alpha_provider=alpha,
            ibkr_provider=ibkr,
            atlas_provider=atlas,
        )

        console.print(
            f"Scanning [bold]{len(ticker_list)}[/] ticker(s) "
            f"from {sleeve_label} universe...\n"
        )

        # Collect all passing PCS candidates across all tickers
        all_passing: list[tuple[str, PCSCandidate]] = []
        all_watch: list[tuple[str, PCSCandidate]] = []
        errors: list[str] = []

        for i, ticker in enumerate(ticker_list, 1):

            console.print(
                f"  [{i}/{len(ticker_list)}] {ticker}...", end=" "
            )

            try:
                result = await service.analyze(
                    ticker,
                    currency=currency,
                    long_term=long_term,
                )

                contracts = (
                    [s.option for s in result.contracts]
                    + [r.option for r in result.rejected]
                )
                candidates = find_pcs_candidates(
                    contracts,
                    buy_price=result.thesis.buy_price,
                )

                passing = [c for c in candidates if c.passes_all]
                watch = [
                    c for c in candidates
                    if c.passes_credit_ratio and not c.oi_ok
                ]

                all_passing.extend((ticker, c) for c in passing)
                all_watch.extend((ticker, c) for c in watch)

                if passing:
                    console.print(
                        f"[green]{len(passing)} PCS candidate(s) ✅[/]"
                    )
                elif watch:
                    console.print(
                        f"[yellow]{len(watch)} watch (OI bajo)[/]"
                    )
                else:
                    console.print("[dim]no candidates[/]")

            except Exception as exc:
                console.print(f"[red]error: {exc}[/]")
                errors.append(f"{ticker}: {exc}")

        # Sort all passing by credit ratio descending
        all_passing.sort(key=lambda x: -x[1].credit_ratio)
        all_watch.sort(key=lambda x: -x[1].credit_ratio)

        console.print()
        console.rule("[bold]Results[/]")

        if all_passing:
            # Group passing candidates by ticker and show context per ticker
            from app.cli.shared import print_market_context
            from app.iv_history.repository import IVHistoryRepository

            settings_ctx = Settings()
            repo = IVHistoryRepository(settings_ctx.iv_history_db_path)
            iv_summaries = repo.summary_by_ticker()
            iv_min_days = settings_ctx.get(
                "cash_secured_put", "ivr"
            )["minimum_days_history"]

            seen_tickers: set[str] = set()
            for t, c in all_passing:
                if t not in seen_tickers:
                    seen_tickers.add(t)
                    iv_entry = next(
                        (s for s in iv_summaries if s["ticker"] == t), None
                    )
                    print_market_context(
                        ticker=t,
                        underlying_price=c.short.underlying_price,
                        current_iv=c.short.implied_volatility,
                        iv_days=iv_entry["days"] if iv_entry else 0,
                        iv_min_days=iv_min_days,
                    )

            console.print()
            _render_results_table(
                all_passing,
                title=f"✅ PCS {sleeve_label} — Passing Candidates",
            )
        else:
            console.print(
                "[bold yellow]No PCS candidates passed all filters "
                "in the current market conditions.[/]\n"
            )

        if all_watch:
            console.print()
            _render_results_table(
                all_watch,
                title=f"⚠ PCS {sleeve_label} — Ratio OK but OI below 500",
                dim=True,
            )

        console.print(
            f"\n[bold green]{len(all_passing)}[/] passing PCS candidate(s) "
            f"across [bold]{len(ticker_list) - len(errors)}[/] analyzed ticker(s)."
        )
        if errors:
            console.print(
                f"[dim]{len(errors)} ticker(s) errored — see log above.[/]"
            )

    except Exception as exc:
        from app.cli.errors import print_error
        print_error(exc)

    finally:
        await alpha.close()
        await ibkr.disconnect()
        await atlas.close()


def _render_results_table(
    results: list[tuple[str, PCSCandidate]],
    title: str,
    dim: bool = False,
) -> None:

    table = Table(title=title)

    table.add_column("Ticker", style="bold")
    table.add_column("Short", justify="right")
    table.add_column("Long", justify="right")
    table.add_column("Exp")
    table.add_column("DTE", justify="right")
    table.add_column("Ancho", justify="right")
    table.add_column("Mid Short", justify="right")
    table.add_column("Mid Long", justify="right")
    table.add_column("Crédito", justify="right")
    table.add_column("Cr/Ancho", justify="right")
    table.add_column("Break-even", justify="right")
    table.add_column("Caída %", justify="right")
    table.add_column("Δ Short", justify="right")
    table.add_column("OI Short", justify="right")
    table.add_column("OI Long", justify="right")

    for ticker, c in results:

        from app.strategies.pcs import _mid

        mid_short = _mid(c.short) or Decimal("0")
        mid_long = _mid(c.long) or Decimal("0")

        oi_short = (
            str(c.short.open_interest)
            if c.short.open_interest is not None else "-"
        )
        oi_long = (
            str(c.long.open_interest)
            if c.long.open_interest is not None else "-"
        )

        ratio_str = f"{c.credit_ratio:.1%}"
        if not dim:
            ratio_str = f"[green]{ratio_str}[/]"

        if dim:
            oi_short = f"[yellow]{oi_short}[/]" if not c.short_oi_ok else oi_short
            oi_long = f"[yellow]{oi_long}[/]" if not c.long_oi_ok else oi_long

        delta_str = (
            f"{c.short.delta:.3f}"
            if c.short.delta is not None else "-"
        )

        underlying = c.short.underlying_price
        if underlying and underlying > 0:
            drop_pct = (underlying - c.break_even) / underlying * 100
            drop_str = f"{drop_pct:.1f}%"
        else:
            drop_str = "-"

        from datetime import date as date_type
        dte = (c.short.expiration - date_type.today()).days

        table.add_row(
            ticker,
            f"${c.short.strike}",
            f"${c.long.strike}",
            str(c.short.expiration),
            str(dte),
            f"${c.width:.0f}",
            f"${float(mid_short):.2f}",
            f"${float(mid_long):.2f}",
            f"${c.credit_mid:.2f}",
            ratio_str,
            f"${c.break_even:.2f}",
            drop_str,
            delta_str,
            oi_short,
            oi_long,
        )

    console.print(table)
