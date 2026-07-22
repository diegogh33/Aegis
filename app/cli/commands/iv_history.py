from __future__ import annotations

from datetime import date

from rich.console import Console
from rich.table import Table

from app.config.settings import Settings
from app.iv_history.repository import IVHistoryRepository

console = Console()

_MINIMUM_DAYS = 90  # matches constitution.yaml cash_secured_put.ivr.minimum_days_history


def iv_history() -> None:
    """
    Shows IV history accumulation progress per ticker.

    IVRankRule requires 90 days of daily snapshots before it starts
    blocking candidates. This command shows how many days each ticker
    has accumulated, how many remain, and the latest recorded IV.

    Snapshots are recorded automatically every time a ticker is
    analyzed with Aegis (one per day, overwriting if the same ticker
    is analyzed multiple times on the same day).
    """

    settings = Settings()

    try:
        min_days = settings.get("cash_secured_put", "ivr")["minimum_days_history"]
    except Exception:
        min_days = _MINIMUM_DAYS

    repo = IVHistoryRepository(settings.iv_history_db_path)
    rows = repo.summary_by_ticker()

    if not rows:
        console.print(
            "\n[yellow]No IV history recorded yet.[/]\n"
            "Run any analysis command to start accumulating history.\n"
            "Each ticker gets one snapshot per day of analysis.\n"
        )
        return

    table = Table(title=f"IV History — {min_days} days needed for IVRankRule to activate")

    table.add_column("Ticker", style="bold")
    table.add_column("Days", justify="right")
    table.add_column("Remaining", justify="right")
    table.add_column("Progress")
    table.add_column("First", justify="right")
    table.add_column("Last", justify="right")
    table.add_column("Latest IV", justify="right")
    table.add_column("Status")

    today = date.today()

    for row in rows:

        ticker = row["ticker"]
        days = row["days"]
        remaining = max(0, min_days - days)
        pct = min(100, int(days / min_days * 100))

        # Progress bar: 10 chars wide
        filled = pct // 10
        bar = "█" * filled + "░" * (10 - filled)

        if days >= min_days:
            status = "[bold green]✓ Active[/]"
            remaining_str = "[green]0[/]"
        elif days >= min_days * 0.75:
            status = "[yellow]Almost there[/]"
            remaining_str = str(remaining)
        else:
            status = "[dim]Accumulating[/]"
            remaining_str = str(remaining)

        # How long since the last snapshot?
        days_since = (today - row["last_day"]).days
        last_str = str(row["last_day"])
        if days_since > 7:
            last_str = f"[yellow]{last_str}[/]"

        table.add_row(
            ticker,
            str(days),
            remaining_str,
            f"{bar} {pct}%",
            str(row["first_day"]),
            last_str,
            f"{float(row['latest_iv']):.1%}",
            status,
        )

    console.print()
    console.print(table)

    active = sum(1 for r in rows if r["days"] >= min_days)
    console.print(
        f"\n[bold]{len(rows)}[/] ticker(s) tracked. "
        f"[bold green]{active}[/] with {min_days}+ days "
        f"(IVRankRule active).\n"
    )
