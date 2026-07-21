from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from rich.console import Console
from rich.table import Table

console = Console()


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
    best_bid: str | None = None
    best_ask: str | None = None
    best_delta: str | None = None
    best_iv: str | None = None
    best_open_interest: str | None = None


def build_summary(ticker: str, atlas_valoracion: str | None, result) -> TickerSummary:
    """Builds a TickerSummary from an AnalysisResult."""

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

        return TickerSummary(
            ticker=ticker,
            atlas_valoracion=atlas_valoracion,
            candidates=len(result.contracts),
            best_score=float(best.score.total),
            best_strike=str(option.strike),
            best_expiration=str(option.expiration),
            best_otm_pct=otm_str,
            top_rejection=None,
            best_bid=f"{option.bid:.2f}" if option.bid is not None else "-",
            best_ask=f"{option.ask:.2f}" if option.ask is not None else "-",
            best_delta=f"{option.delta:.3f}" if option.delta is not None else "-",
            best_iv=f"{option.implied_volatility:.2%}" if option.implied_volatility is not None else "-",
            best_open_interest=str(option.open_interest) if option.open_interest is not None else "-",
        )

    top_reason = None
    if result.rejected:
        counts = Counter(r.reason for r in result.rejected)
        top_reason = counts.most_common(1)[0][0]

    return TickerSummary(
        ticker=ticker,
        atlas_valoracion=atlas_valoracion,
        candidates=0,
        best_score=None,
        best_strike=None,
        best_expiration=None,
        best_otm_pct=None,
        top_rejection=top_reason,
    )


def print_summary_table(summaries: list[TickerSummary], long_term: bool) -> None:
    """Renders the summary table used by both analyze (multi) and watchlist."""

    console.print()
    console.rule("[bold]Summary[/]")
    console.print()

    # Sort: tickers with candidates first (by score desc), then no-candidates
    sorted_summaries = sorted(
        summaries,
        key=lambda s: (
            0 if s.candidates > 0 else 1,
            -(s.best_score or 0),
        ),
    )

    summary_table = Table(
        title=(
            "Long-Term PUT Candidates"
            if long_term
            else "Best PUT Candidates"
        )
    )

    summary_table.add_column("Ticker", style="bold")
    summary_table.add_column("ATLAS")
    summary_table.add_column("Cands", justify="right")
    summary_table.add_column("Score", justify="right")
    summary_table.add_column("Strike", justify="right")
    summary_table.add_column("OTM%", justify="right")
    summary_table.add_column("Bid", justify="right")
    summary_table.add_column("Ask", justify="right")
    summary_table.add_column("Delta", justify="right")
    summary_table.add_column("IV", justify="right")
    summary_table.add_column("Open Int", justify="right")
    summary_table.add_column("Expiration")
    summary_table.add_column("Notes")

    for s in sorted_summaries:

        atlas_cell = s.atlas_valoracion or "-"

        if s.candidates > 0:
            summary_table.add_row(
                s.ticker,
                atlas_cell,
                str(s.candidates),
                f"{s.best_score:.1f}",
                s.best_strike or "-",
                s.best_otm_pct or "-",
                s.best_bid or "-",
                s.best_ask or "-",
                s.best_delta or "-",
                s.best_iv or "-",
                s.best_open_interest or "-",
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
                "[dim]-[/]",
                "[dim]-[/]",
                "[dim]-[/]",
                "[dim]-[/]",
                "[dim]-[/]",
                f"[dim]{s.top_rejection or ''}[/]",
            )

    console.print(summary_table)

    with_candidates = [s for s in summaries if s.candidates > 0]
    console.print(
        f"\n[bold green]{len(with_candidates)} of {len(summaries)} "
        f"ticker(s) have candidates.[/]"
    )
