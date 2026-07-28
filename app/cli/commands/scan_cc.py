from __future__ import annotations

import asyncio
from dataclasses import dataclass

from rich.console import Console
from rich.table import Table

from app.config.settings import Settings
from app.providers.ibkr.provider import IBKRProvider

console = Console()


@dataclass
class S1Summary:
    ticker: str
    price: float
    ret_15d: float | None       # % return last 15 days
    ret_30d: float | None       # % return last 30 days
    high_52w: float | None      # 52-week high
    low_52w: float | None       # 52-week low
    high_30d: float | None      # 30-day high
    pct_to_52w_high: float | None   # % to reach 52w high
    pct_from_30d_high: float | None  # % below 30d high (0 = at high)
    iv: float | None            # current IV


def scan_cc(
    currency: str = "USD",
) -> None:
    """
    Scans the S1 universe (cartera) for Covered Call opportunities.

    Shows a table with price momentum (15d, 30d returns), 52-week
    range, distance to annual high, distance to 30-day high, and
    current IV — the key metrics for deciding whether to sell a
    Covered Call on a position.

    Sorted by 30-day return descending: stocks that have risen the
    most recently are the best Covered Call candidates (higher
    premiums, more cushion if called away).

    Data comes from IBKR historical data (no Alpha Vantage quota used).
    """
    asyncio.run(_scan_cc(currency=currency))


async def _scan_cc(currency: str) -> None:

    settings = Settings()

    try:
        universe: list[str] = settings.get("s1_universe")
    except Exception:
        console.print("[red]s1_universe not found in constitution.yaml.[/]")
        return

    if not universe:
        console.print("[yellow]s1_universe is empty.[/]")
        return

    ibkr = IBKRProvider()

    try:

        console.rule("[bold blue]Aegis — Scan Covered Calls S1[/]")
        console.print("[bold]Connecting to IBKR...[/]")
        await ibkr.connect()
        console.print("[green]✓ Connected[/]\n")

        console.print(
            f"Fetching data for [bold]{len(universe)}[/] ticker(s)...\n"
        )

        summaries: list[S1Summary] = []
        errors: list[str] = []

        for i, ticker in enumerate(universe, 1):

            console.print(f"  [{i}/{len(universe)}] {ticker}...", end=" ")

            try:
                summary = await _fetch_summary(ibkr, ticker, currency)
                summaries.append(summary)
                console.print(
                    f"[green]${summary.price:.2f}[/] "
                    f"({_fmt_pct(summary.ret_30d)} 30d)"
                )
            except Exception as exc:
                console.print(f"[red]error: {exc}[/]")
                errors.append(ticker)

        if not summaries:
            console.print("[yellow]No data retrieved.[/]")
            return

        # Sort by 30d return descending (best CC candidates first)
        # Tickers with no 30d data go to the bottom
        summaries.sort(
            key=lambda s: s.ret_30d if s.ret_30d is not None else -999,
            reverse=True,
        )

        _render_table(summaries)

        if errors:
            console.print(
                f"\n[dim]{len(errors)} ticker(s) failed: "
                f"{', '.join(errors)}[/]"
            )

    except Exception as exc:
        from app.cli.errors import print_error
        print_error(exc)

    finally:
        await ibkr.disconnect()


async def _fetch_summary(
    ibkr: IBKRProvider,
    ticker: str,
    currency: str,
) -> S1Summary:
    """Fetches historical price data from IBKR and computes the metrics."""

    from ib_async import Contract, Stock

    stock = Stock(ticker, "SMART", currency)
    qualified = await ibkr.ib.qualifyContractsAsync(stock)
    if not qualified:
        raise ValueError(f"Cannot qualify {ticker}")

    contract: Contract = qualified[0]  # type: ignore[assignment]

    # Fetch 1 year of daily bars (covers 52w high/low + 30d + 15d)
    bars = await ibkr.ib.reqHistoricalDataAsync(
        contract,  # type: ignore[arg-type]
        endDateTime="",
        durationStr="1 Y",
        barSizeSetting="1 day",
        whatToShow="TRADES",
        useRTH=True,
        formatDate=1,
    )

    if not bars:
        raise ValueError(f"No historical data for {ticker}")

    # Current price = last close
    price = bars[-1].close

    # 52-week high/low
    high_52w = max(b.high for b in bars)
    low_52w = min(b.low for b in bars)

    # 30-day bars
    bars_30d = bars[-30:] if len(bars) >= 30 else bars
    high_30d = max(b.high for b in bars_30d)
    price_30d_ago = bars_30d[0].close

    # 15-day bars
    bars_15d = bars[-15:] if len(bars) >= 15 else bars
    price_15d_ago = bars_15d[0].close

    ret_30d = (price - price_30d_ago) / price_30d_ago * 100
    ret_15d = (price - price_15d_ago) / price_15d_ago * 100

    pct_to_52w_high = (high_52w - price) / price * 100
    pct_from_30d_high = (high_30d - price) / price * 100

    # Current IV from market data ticker (optional — stock IV is less
    # reliable than option IV, but gives a useful ballpark)
    iv: float | None = None
    try:
        import math
        ibkr.ib.reqMktData(contract, "104", False, False)  # type: ignore[arg-type]
        await asyncio.sleep(2)
        t = ibkr.ib.ticker(contract)  # type: ignore[arg-type]
        if t and t.impliedVolatility and not math.isnan(t.impliedVolatility):
            iv = t.impliedVolatility * 100
        ibkr.ib.cancelMktData(contract)  # type: ignore[arg-type]
    except Exception:
        pass  # IV is optional

    return S1Summary(
        ticker=ticker,
        price=price,
        ret_15d=ret_15d,
        ret_30d=ret_30d,
        high_52w=high_52w,
        low_52w=low_52w,
        high_30d=high_30d,
        pct_to_52w_high=pct_to_52w_high,
        pct_from_30d_high=pct_from_30d_high,
        iv=iv,
    )


def _render_table(summaries: list[S1Summary]) -> None:

    console.print()
    console.rule("[bold]S1 — Covered Call Opportunities[/]")
    console.print()

    table = Table(
        title="S1 Universe — sorted by 30d return ↓ (best CC candidates first)"
    )

    table.add_column("Ticker", style="bold")
    table.add_column("Precio", justify="right")
    table.add_column("15d %", justify="right")
    table.add_column("30d %", justify="right")
    table.add_column("Mín 52w", justify="right")
    table.add_column("Máx 52w", justify="right")
    table.add_column("% al Máx 52w", justify="right")
    table.add_column("Máx 30d", justify="right")
    table.add_column("% vs Máx 30d", justify="right")
    table.add_column("IV", justify="right")
    table.add_column("Earnings")

    for s in summaries:

        # Color for 30d return
        ret30_str = _fmt_pct(s.ret_30d)
        if s.ret_30d is not None:
            if s.ret_30d >= 10:
                ret30_str = f"[bold green]{ret30_str}[/]"
            elif s.ret_30d >= 5:
                ret30_str = f"[green]{ret30_str}[/]"
            elif s.ret_30d < 0:
                ret30_str = f"[red]{ret30_str}[/]"

        ret15_str = _fmt_pct(s.ret_15d)
        if s.ret_15d is not None:
            if s.ret_15d >= 5:
                ret15_str = f"[green]{ret15_str}[/]"
            elif s.ret_15d < 0:
                ret15_str = f"[red]{ret15_str}[/]"

        # Distance to 52w high — green if close (<5%), red if far (>30%)
        to_high_str = _fmt_pct(s.pct_to_52w_high)
        if s.pct_to_52w_high is not None:
            if s.pct_to_52w_high <= 5:
                to_high_str = f"[bold green]{to_high_str}[/]"
            elif s.pct_to_52w_high <= 15:
                to_high_str = f"[green]{to_high_str}[/]"
            elif s.pct_to_52w_high >= 30:
                to_high_str = f"[red]{to_high_str}[/]"

        # Distance from 30d high — near 0 means at the high (good for CC)
        from_30d_str = _fmt_pct(s.pct_from_30d_high)
        if s.pct_from_30d_high is not None:
            if s.pct_from_30d_high <= 2:
                from_30d_str = f"[bold green]{from_30d_str}[/]"
            elif s.pct_from_30d_high <= 5:
                from_30d_str = f"[green]{from_30d_str}[/]"

        iv_str = f"{s.iv:.1f}%" if s.iv is not None else "-"

        earnings_url = f"https://finance.yahoo.com/quote/{s.ticker}/"
        earnings_str = f"[link={earnings_url}]Yahoo →[/link]"

        table.add_row(
            s.ticker,
            f"${s.price:.2f}",
            ret15_str,
            ret30_str,
            f"${s.low_52w:.2f}" if s.low_52w else "-",
            f"${s.high_52w:.2f}" if s.high_52w else "-",
            to_high_str,
            f"${s.high_30d:.2f}" if s.high_30d else "-",
            from_30d_str,
            iv_str,
            earnings_str,
        )

    console.print(table)
    console.print(
        "\n[dim]Verde intenso: señal fuerte (30d ≥10%, cerca de máximos). "
        "Verde: señal positiva. Rojo: caída reciente.[/]"
    )


def _fmt_pct(val: float | None) -> str:
    if val is None:
        return "-"
    sign = "+" if val >= 0 else ""
    return f"{sign}{val:.1f}%"
