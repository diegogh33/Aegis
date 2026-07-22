from __future__ import annotations

from dataclasses import replace
from decimal import Decimal
from unittest.mock import MagicMock

from app.cli.shared import TickerSummary, build_summary, sort_summaries
from tests.conftest import build_option


def _scored_option(score: float = 80.0, delta: float = -0.20):
    """Minimal ScoredOption mock for build_summary tests."""
    option = replace(
        build_option(delta=delta),
        underlying_price=Decimal("280"),
        strike=Decimal("250"),
        bid=Decimal("4.00"),
        ask=Decimal("4.20"),
        implied_volatility=Decimal("0.35"),
        open_interest=1500,
    )
    scored = MagicMock()
    scored.option = option
    scored.score.total = Decimal(str(score))
    return scored


def _result(contracts=None, rejected=None):
    result = MagicMock()
    result.contracts = contracts or []
    result.rejected = rejected or []
    return result


def test_build_summary_with_candidates():
    scored = _scored_option(score=82.5)
    result = _result(contracts=[scored])

    summary = build_summary("AAPL", "alcista", result)

    assert summary.ticker == "AAPL"
    assert summary.atlas_valoracion == "alcista"
    assert summary.candidates == 1
    assert summary.best_score == 82.5
    assert summary.best_strike == "250"
    assert summary.best_otm_pct == "10.7% OTM"
    assert summary.best_bid == "4.00"
    assert summary.best_delta == "-0.200"
    assert summary.top_rejection is None


def test_build_summary_no_candidates_shows_top_rejection():
    rejected_a = MagicMock()
    rejected_a.reason = "DELTA"
    rejected_b = MagicMock()
    rejected_b.reason = "DELTA"
    rejected_c = MagicMock()
    rejected_c.reason = "SPREAD"

    result = _result(rejected=[rejected_a, rejected_b, rejected_c])

    summary = build_summary("ACN", "alcista", result)

    assert summary.candidates == 0
    assert summary.best_score is None
    assert summary.top_rejection == "DELTA"


def test_build_summary_no_candidates_no_rejections():
    result = _result()

    summary = build_summary("ZTS", "alcista", result)

    assert summary.candidates == 0
    assert summary.top_rejection is None


def test_build_summary_itm_strike():
    """Strike above underlying price shows ITM% instead of OTM%."""
    scored = _scored_option()
    scored.option = replace(
        scored.option,
        underlying_price=Decimal("200"),
        strike=Decimal("250"),
    )
    result = _result(contracts=[scored])

    summary = build_summary("X", None, result)

    assert "ITM" in summary.best_otm_pct


def test_sort_summaries_candidates_before_no_candidates():
    has = TickerSummary(
        ticker="A", atlas_valoracion="alcista",
        candidates=3, best_score=75.0,
        best_strike=None, best_expiration=None,
        best_otm_pct=None, top_rejection=None,
    )
    empty = TickerSummary(
        ticker="B", atlas_valoracion="alcista",
        candidates=0, best_score=None,
        best_strike=None, best_expiration=None,
        best_otm_pct=None, top_rejection="DELTA",
    )

    result = sort_summaries([empty, has])

    assert result[0].ticker == "A"
    assert result[1].ticker == "B"


def test_sort_summaries_ordered_by_score_descending():
    low = TickerSummary(
        ticker="LOW", atlas_valoracion=None,
        candidates=2, best_score=60.0,
        best_strike=None, best_expiration=None,
        best_otm_pct=None, top_rejection=None,
    )
    high = TickerSummary(
        ticker="HIGH", atlas_valoracion=None,
        candidates=5, best_score=85.0,
        best_strike=None, best_expiration=None,
        best_otm_pct=None, top_rejection=None,
    )
    mid = TickerSummary(
        ticker="MID", atlas_valoracion=None,
        candidates=1, best_score=72.0,
        best_strike=None, best_expiration=None,
        best_otm_pct=None, top_rejection=None,
    )

    result = sort_summaries([low, high, mid])

    assert [s.ticker for s in result] == ["HIGH", "MID", "LOW"]
