from __future__ import annotations

import asyncio
from collections import Counter
from decimal import Decimal

from rich.console import Console
from rich.table import Table

from app.cli.shared import TickerSummary, build_summary, print_summary_table
from app.providers.alphavantage.provider import AlphaVantageProvider
from app.providers.atlas.provider import AtlasProvider
from app.providers.ibkr.provider import IBKRProvider
from app.services.analysis_service import AnalysisService

import typer

console = Console()


def analyze(
    tickers: list[str] = typer.Argument(
        ...,
        help="One or more tickers to analyze.",
    ),
    exchange: str = "SMART",
    currency: str = "USD",
    long_term: bool = False,
    pcs: bool = False,
    no_rules: bool = typer.Option(
        False,
        "--no-rules",
        help="Show raw option chain without applying any Constitution rules. "
             "Displays all contracts from ATM down to delta -0.10.",
    ),
    until: str | None = typer.Option(
        None,
        "--until",
        help="Limit expirations to this month (YYYY-MM format). "
             "E.g. --until 2026-11 shows only contracts expiring by Nov 2026.",
    ),
) -> None:
    """
    Analyzes one or more tickers for Cash Secured PUT candidates.

    Single ticker: shows the full detailed table (Company, candidates,
    rejected contracts).

    Multiple tickers: shows a compact summary table, one row per
    ticker, with the best candidate for each.

    --long-term switches to the opportunistic long-dated PUT strategy
    (90-365 DTE). --currency EUR for European underlyings.

    --pcs additionally shows Put Credit Spread combinations.

    --no-rules shows the raw option chain without any Constitution
    filters (delta, spread, liquidity...). Use --until YYYY-MM to
    limit the expirations shown.
    """
    asyncio.run(
        _analyze(
            tickers=tickers,
            exchange=exchange,
            currency=currency,
            long_term=long_term,
            pcs=pcs,
            no_rules=no_rules,
            until=until,
        )
    )


async def _analyze(
    tickers: list[str],
    exchange: str,
    currency: str,
    long_term: bool,
    pcs: bool = False,
    no_rules: bool = False,
    until: str | None = None,
) -> None:

    alpha = AlphaVantageProvider()
    ibkr = IBKRProvider()
    atlas = AtlasProvider()

    try:

        console.rule("[bold blue]Aegis[/]")

        if no_rules:
            console.print("[bold]Mode: raw chain — no Constitution rules[/]")
        elif long_term:
            console.print(
                "[bold]Mode: long-term opportunistic (90-365 DTE)[/]"
            )

        console.print("[bold]Connecting to IBKR...[/]")
        await ibkr.connect()
        console.print("[green]✓ Connected[/]")

        service = AnalysisService(
            alpha_provider=alpha,
            ibkr_provider=ibkr,
            atlas_provider=atlas,
        )

        if no_rules:
            if len(tickers) == 1:
                await _no_rules(
                    tickers[0], exchange, currency, long_term,
                    ibkr, until=until,
                )
            else:
                console.print(
                    "[yellow]--no-rules only supports a single ticker.[/]"
                )
        elif len(tickers) == 1:
            await _single(
                tickers[0], exchange, currency, long_term, service, pcs=pcs
            )
        else:
            await _multi(tickers, exchange, currency, long_term, service)

        console.print("\n[bold green]Analysis completed[/]")

    finally:

        await alpha.close()
        await ibkr.disconnect()
        await atlas.close()


async def _no_rules(
    ticker: str,
    exchange: str,
    currency: str,
    long_term: bool,
    ibkr: IBKRProvider,
    until: str | None = None,
    min_delta: float = -0.10,
) -> None:
    """
    Shows the raw option chain without any Constitution rules.
    Contracts from ATM down to min_delta (-0.10 by default),
    optionally filtered to expirations up to a given YYYY-MM.
    """
    from datetime import date as date_type

    from app.services.option_scanner import OptionScanner

    # Parse --until into a cutoff date (last day of that month)
    until_date: date_type | None = None
    if until:
        try:
            year, month = until.split("-")
            import calendar
            last_day = calendar.monthrange(int(year), int(month))[1]
            until_date = date_type(int(year), int(month), last_day)
        except ValueError:
            console.print(
                f"[red]Invalid --until format '{until}'. "
                f"Use YYYY-MM (e.g. 2026-11).[/]"
            )
            return

    # DTE window for the scan:
    # - --until specified: scan from 1 day up to until_date (in days)
    # - --long-term without --until: 90-730 days
    # - neither: 1-730 days
    from datetime import date as date_today_type
    today = date_today_type.today()

    if until_date is not None:
        max_dte = (until_date - today).days
        if max_dte <= 0:
            console.print(
                f"[red]--until {until} is in the past.[/]"
            )
            return
        dte_window = {"min": 1, "max": max_dte}
    elif long_term:
        dte_window = {"min": 90, "max": 730}
    else:
        dte_window = {"min": 1, "max": 730}

    target_delta = -0.20

    scanner = OptionScanner(ibkr)

    console.print(
        f"\nFetching raw chain for [bold]{ticker}[/]"
        + (f" until {until}" if until else "")
        + "...\n"
    )

    contracts = await scanner.scan_puts(
        ticker,
        exchange=exchange,
        currency=currency,
        dte_window=dte_window,
        target_delta=target_delta,
    )

    # Show contracts with delta between -0.50 (ATM side) and -0.10 (OTM
    # limit). This is the interesting range for selling options - deeper
    # OTM than -0.10 has very little premium, more ITM than -0.50 is
    # too risky.
    filtered = [
        c for c in contracts
        if c.delta is not None
        and -0.50 <= c.delta <= -0.10
        and c.bid is not None
        and c.bid > 0
    ]

    if not filtered:
        console.print(
            "[yellow]No contracts found with available data in this range.[/]"
        )
        return

    # Sort by bid descending — highest premium first
    filtered.sort(key=lambda c: c.bid or 0, reverse=True)

    table = Table(
        title=f"Raw PUT Chain — {ticker}"
              + (f" (until {until})" if until else "")
              + " | delta -0.50 to -0.10 | sorted by premium"
    )

    table.add_column("Bid", justify="right", style="bold")
    table.add_column("Ask", justify="right")
    table.add_column("Mid", justify="right")
    table.add_column("Strike", justify="right")
    table.add_column("Delta", justify="right")
    table.add_column("IV", justify="right")
    table.add_column("OTM%", justify="right")
    table.add_column("Open Int", justify="right")
    table.add_column("Expiration")

    for c in filtered:
        mid = (c.bid + c.ask) / 2 if c.bid and c.ask else None
        mid_str = f"${float(mid):.2f}" if mid else "-"

        if c.underlying_price and c.underlying_price > 0:
            otm_pct = (c.underlying_price - c.strike) / c.underlying_price * 100
            otm_str = (
                f"{otm_pct:.1f}% OTM"
                if otm_pct >= 0
                else f"{abs(otm_pct):.1f}% ITM"
            )
        else:
            otm_str = "-"

        table.add_row(
            f"${float(c.bid):.2f}" if c.bid else "-",
            f"${float(c.ask):.2f}" if c.ask else "-",
            mid_str,
            f"${c.strike}",
            f"{c.delta:.3f}" if c.delta else "-",
            f"{float(c.implied_volatility):.2%}" if c.implied_volatility else "-",
            otm_str,
            str(c.open_interest) if c.open_interest else "-",
            str(c.expiration),
        )

    console.print(table)
    console.print(
        f"\n[dim]{len(filtered)} contracts shown "
        f"(delta -0.50 to -0.10, sorted by premium desc).[/]"
    )


async def _single(
    ticker: str,
    exchange: str,
    currency: str,
    long_term: bool,
    service: AnalysisService,
    pcs: bool = False,
) -> None:

    result = await service.analyze(
        ticker, exchange=exchange, currency=currency, long_term=long_term
    )

    company = result.company
    thesis = result.thesis

    if result.company_known:

        company_table = Table(title="Company")
        company_table.add_column("Field")
        company_table.add_column("Value")
        company_table.add_row("Name", company.name)
        company_table.add_row("Ticker", company.symbol)
        company_table.add_row("Exchange", company.exchange)
        company_table.add_row("Sector", company.sector)
        company_table.add_row("Industry", company.industry)
        company_table.add_row("Market Cap", f"{company.market_cap:,}")
        if thesis.buy_price is not None:
            company_table.add_row("Max Entry", f"${thesis.buy_price:,.2f}")
        if thesis.zona_compra is not None:
            company_table.add_row("Buy Zone", thesis.zona_compra)

        console.print()
        console.print(company_table)

    else:

        console.print(
            f"\n[bold yellow]⚠ {result.company_error}[/] "
            f"Continuing with the options analysis, which doesn't "
            f"depend on this."
        )

    if thesis.watchlist:
        console.print(
            f"\n[bold yellow]⚠ '{ticker}' is on the ATLAS watchlist "
            f"(seguimiento) - not yet an approved investment.[/] "
            f"Candidates below are shown, but scored lower and "
            f"capped below STRONG_BUY/BUY."
        )
    elif not thesis.approved:
        console.print(
            f"\n[bold yellow]⚠ '{ticker}' has not been analyzed in "
            f"ATLAS yet.[/] Candidates below are shown, but scored "
            f"lower and capped below STRONG_BUY/BUY until it has a "
            f"recorded investment thesis."
        )

    options = Table(
        title=(
            "Best Long-Term PUT Candidates"
            if long_term
            else "Best PUT Candidates"
        )
    )

    options.add_column("Score", justify="right")
    options.add_column("Strike", justify="right")
    options.add_column("OTM%", justify="right")
    options.add_column("vs Buy Zone", justify="right")
    options.add_column("Expiration")
    options.add_column("Bid", justify="right")
    options.add_column("Ask", justify="right")
    options.add_column("Delta", justify="right")
    options.add_column("IV", justify="right")
    options.add_column("Open Int", justify="right")
    options.add_column("Recommendation")

    for scored in result.contracts:

        option = scored.option
        score = scored.score

        if option.underlying_price is not None and option.underlying_price > 0:
            diff = option.underlying_price - option.strike
            otm_pct = diff / option.underlying_price * 100
            otm_str = (
                f"{otm_pct:.1f}% OTM"
                if otm_pct >= 0
                else f"{abs(otm_pct):.1f}% ITM"
            )
        else:
            otm_str = "-"

        if thesis.buy_price is not None and thesis.buy_price > 0:
            vs_pct = (
                (thesis.buy_price - option.strike) / thesis.buy_price * 100
            )
            vs_str = (
                f"{vs_pct:.1f}% below"
                if vs_pct >= 0
                else f"[bold red]{abs(vs_pct):.1f}% above[/]"
            )
        else:
            vs_str = "-"

        options.add_row(
            f"{score.total:.1f}",
            str(option.strike),
            otm_str,
            vs_str,
            str(option.expiration),
            "-" if option.bid is None else f"{option.bid:.2f}",
            "-" if option.ask is None else f"{option.ask:.2f}",
            "-" if option.delta is None else f"{option.delta:.3f}",
            "-" if option.implied_volatility is None else f"{option.implied_volatility:.2%}",
            "-" if option.open_interest is None else str(option.open_interest),
            scored.evaluation.recommendation.value,
        )

    console.print()
    console.print(options)

    if result.rejected:

        reasons = Counter(item.reason for item in result.rejected)
        example_detail = {item.reason: item.detail for item in result.rejected}

        rejected_table = Table(title="Rejected Contracts")
        rejected_table.add_column("Reason")
        rejected_table.add_column("Count", justify="right")
        rejected_table.add_column("Example")

        for reason, count in reasons.most_common():
            rejected_table.add_row(reason, str(count), example_detail[reason])

        console.print()
        console.print(rejected_table)

    if not result.contracts:
        console.print(
            "\n[bold yellow]No candidates passed the Constitution "
            "or had usable market data.[/] See 'Rejected Contracts' "
            "above for why."
        )

    if pcs:
        _render_pcs_table(result, ticker)


def _render_pcs_table(result, ticker: str) -> None:
    """Renders the PCS candidates table below the main candidates table."""
    from app.cli.shared import print_market_context
    from app.config.settings import Settings
    from app.iv_history.repository import IVHistoryRepository
    from app.strategies.pcs import PCS_MIN_OI, _mid, find_pcs_candidates

    all_contracts = (
        [s.option for s in result.contracts]
        + [r.option for r in result.rejected]
    )

    if not all_contracts:
        console.print(
            "\n[bold yellow]No contracts with market data available "
            "for PCS analysis.[/]"
        )
        return

    candidates = find_pcs_candidates(
        all_contracts,
        buy_price=result.thesis.buy_price,
    )

    if not candidates:
        console.print(
            "\n[dim]No PCS combinations found with positive credit "
            "and available bid/ask data.[/]"
        )
        return

    # ── Market context panel ───────────────────────────────────────────
    # Get price and IV from the best contract we have
    sample = all_contracts[0]
    underlying_price = sample.underlying_price
    current_iv = sample.implied_volatility

    # IVR progress from local history
    settings = Settings()
    repo = IVHistoryRepository(settings.iv_history_db_path)
    summaries = repo.summary_by_ticker()
    iv_entry = next((s for s in summaries if s["ticker"] == ticker), None)
    iv_days = iv_entry["days"] if iv_entry else 0
    iv_min_days = settings.get("cash_secured_put", "ivr")["minimum_days_history"]

    print_market_context(
        ticker=ticker,
        underlying_price=underlying_price,
        current_iv=current_iv,
        iv_days=iv_days,
        iv_min_days=iv_min_days,
    )

    passing = [c for c in candidates if c.passes_all]

    def _pcs_row(c, rank: int | None = None):
        """Build a table row for a PCS candidate."""
        mid_short = _mid(c.short) or Decimal("0")
        mid_long = _mid(c.long) or Decimal("0")

        oi_short_str = (
            str(c.short.open_interest)
            if c.short.open_interest is not None else "-"
        )
        oi_long_str = (
            str(c.long.open_interest)
            if c.long.open_interest is not None else "-"
        )

        ratio_str = f"[green]{c.credit_ratio:.1%}[/]" if c.passes_credit_ratio else f"[red]{c.credit_ratio:.1%}[/]"

        oi_short_disp = oi_short_str if c.short_oi_ok else f"[red]{oi_short_str}[/]"
        oi_long_disp = oi_long_str if c.long_oi_ok else f"[red]{oi_long_str}[/]"

        # Delta of the short leg (from the option if available)
        delta_str = (
            f"{c.short.delta:.3f}"
            if c.short.delta is not None else "-"
        )

        # % the underlying must fall to reach break-even
        underlying = c.short.underlying_price
        if underlying and underlying > 0:
            drop_pct = (underlying - c.break_even) / underlying * 100
            drop_str = f"{drop_pct:.1f}%"
        else:
            drop_str = "-"

        if c.passes_all:
            status = "[bold green]✅ PASA[/]"
        elif not c.passes_buy_zone:
            status = "[red]❌ Zona compra[/]"
        elif c.passes_credit_ratio and not c.oi_ok:
            status = "[yellow]⚠ OI bajo[/]"
        elif not c.passes_credit_ratio and c.oi_ok:
            status = "[red]❌ Cr/ancho[/]"
        else:
            status = "[red]❌[/]"

        label = f"[bold cyan]#{rank}[/]" if rank else ""

        return (
            label,
            f"${c.short.strike}",
            f"${c.long.strike}",
            str(c.short.expiration),
            f"${c.width:.0f}",
            f"${float(mid_short):.2f}",
            f"${float(mid_long):.2f}",
            f"${c.credit_mid:.2f}",
            ratio_str,
            f"${c.break_even:.2f}",
            drop_str,
            delta_str,
            oi_short_disp,
            oi_long_disp,
            status,
        )

    def _make_table(title: str) -> Table:
        t = Table(title=title)
        t.add_column("#", justify="center", width=3)
        t.add_column("Short", justify="right", style="bold")
        t.add_column("Long", justify="right")
        t.add_column("Exp")
        t.add_column("Ancho", justify="right")
        t.add_column("Mid Short", justify="right")
        t.add_column("Mid Long", justify="right")
        t.add_column("Crédito", justify="right")
        t.add_column("Cr/Ancho", justify="right")
        t.add_column("Break-even", justify="right")
        t.add_column("Caída %", justify="right")
        t.add_column("Δ Short", justify="right")
        t.add_column("OI Short", justify="right")
        t.add_column("OI Long", justify="right")
        t.add_column("✓")
        return t

    console.print()

    # ── Top 3 PASA — highlighted section ──────────────────────────────
    if passing:
        top3 = passing[:3]
        top_table = _make_table(
            f"🏆 Top Candidatos PCS — {ticker} "
            f"(mejores {len(top3)} de {len(passing)} que pasan)"
        )
        for i, c in enumerate(top3, 1):
            top_table.add_row(*_pcs_row(c, rank=i))
        console.print(top_table)
        console.print()

    # ── Full table ─────────────────────────────────────────────────────
    full_table = _make_table(
        f"PCS Candidates — {ticker} "
        f"(crédito/ancho ≥25%, OI ≥{PCS_MIN_OI} ambas patas)"
    )
    for c in candidates:
        rank = (passing.index(c) + 1) if c in passing[:3] else None
        full_table.add_row(*_pcs_row(c, rank=rank))

    console.print(full_table)
    console.print(
        f"\n[bold green]{len(passing)}[/] of [bold]{len(candidates)}[/] "
        f"PCS combinations pass all filters."
    )


async def _multi(
    tickers: list[str],
    exchange: str,
    currency: str,
    long_term: bool,
    service: AnalysisService,
) -> None:

    console.print(f"\nAnalyzing [bold]{len(tickers)}[/] ticker(s)...\n")

    summaries: list[TickerSummary] = []

    for i, ticker in enumerate(tickers, 1):

        console.print(f"  [{i}/{len(tickers)}] {ticker}...", end=" ")

        try:
            result = await service.analyze(
                ticker, exchange=exchange, currency=currency, long_term=long_term
            )
            thesis = result.thesis
            atlas_val = (
                "alcista" if thesis.approved
                else "seguimiento" if thesis.watchlist
                else None
            )
            summary = build_summary(ticker, atlas_val, result)
            console.print(
                f"[green]{summary.candidates} candidate(s)[/]"
                if summary.candidates > 0
                else "[dim]no candidates[/]"
            )
        except Exception as exc:
            summary = TickerSummary(
                ticker=ticker,
                atlas_valoracion=None,
                candidates=0,
                best_score=None,
                best_strike=None,
                best_expiration=None,
                best_otm_pct=None,
                top_rejection=f"ERROR: {exc}",
            )
            console.print(f"[red]error: {exc}[/]")

        summaries.append(summary)

    print_summary_table(summaries, long_term)
