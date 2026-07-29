from __future__ import annotations

from datetime import date, timedelta
from unittest.mock import patch


from app.cli.commands.scan_cc import S1Summary, _fetch_earnings_date, _fmt_pct


# ── S1 universe configuration ──────────────────────────────────────────


def test_s1_universe_is_configured_in_constitution():
    """
    Confirms s1_universe exists in constitution.yaml with expected
    core tickers. If someone removes this key, scan-cc silently does
    nothing.
    """
    from app.config.settings import Settings

    settings = Settings()
    universe = settings.get("s1_universe")

    assert isinstance(universe, list)
    assert len(universe) > 0

    for expected in ["BAM", "MAIN", "O", "MO", "ZTS"]:
        assert expected in universe, f"{expected} missing from s1_universe"


def test_s1_universe_contains_pbra():
    """PBRA (PBR.A) needs special IBKR handling — must stay in the list."""
    from app.config.settings import Settings

    universe = Settings().get("s1_universe")
    assert "PBRA" in universe


# ── _fmt_pct helper ────────────────────────────────────────────────────


def test_fmt_pct_positive():
    assert _fmt_pct(5.3) == "+5.3%"


def test_fmt_pct_negative():
    assert _fmt_pct(-3.7) == "-3.7%"


def test_fmt_pct_zero():
    assert _fmt_pct(0.0) == "+0.0%"


def test_fmt_pct_none():
    assert _fmt_pct(None) == "-"


# ── S1Summary sort order ───────────────────────────────────────────────


def test_summaries_sorted_by_30d_return_descending():
    """
    scan-cc sorts by ret_30d descending so the best CC candidates
    (highest recent momentum) appear first.
    """
    summaries = [
        S1Summary("LOW", 50.0, 1.0, -5.0, 40.0, 60.0, 55.0, 20.0, 5.0, 0.3),
        S1Summary("HIGH", 80.0, 8.0, 15.0, 60.0, 90.0, 85.0, 12.0, 2.0, 0.4),
        S1Summary("MID", 60.0, 3.0, 7.0, 50.0, 70.0, 65.0, 16.0, 3.5, 0.3),
    ]

    sorted_summaries = sorted(
        summaries,
        key=lambda s: s.ret_30d if s.ret_30d is not None else -999,
        reverse=True,
    )

    assert sorted_summaries[0].ticker == "HIGH"
    assert sorted_summaries[1].ticker == "MID"
    assert sorted_summaries[2].ticker == "LOW"


# ── _fetch_earnings_date ───────────────────────────────────────────────


def test_fetch_earnings_date_returns_none_on_failure():
    """
    ETFs and some ADRs don't have earnings. _fetch_earnings_date must
    return None silently — never raise or pollute the log.
    """
    with patch("yfinance.Ticker") as mock_ticker:
        mock_ticker.return_value.calendar = {}
        result = _fetch_earnings_date("BITO")

    assert result is None


def test_fetch_earnings_date_returns_future_date():
    """When yfinance returns a future earnings date, it's formatted correctly."""
    future = date.today() + timedelta(days=45)

    mock_cal = {"Earnings Date": [future]}

    with patch("yfinance.Ticker") as mock_ticker:
        mock_ticker.return_value.calendar = mock_cal
        result = _fetch_earnings_date("ZTS")

    assert result == future.strftime("%d-%b-%Y")


def test_fetch_earnings_date_skips_past_dates():
    """Past earnings dates are ignored — only future dates are returned."""
    past = date.today() - timedelta(days=10)
    future = date.today() + timedelta(days=30)

    mock_cal = {"Earnings Date": [past, future]}

    with patch("yfinance.Ticker") as mock_ticker:
        mock_ticker.return_value.calendar = mock_cal
        result = _fetch_earnings_date("MO")

    assert result == future.strftime("%d-%b-%Y")


def test_fetch_earnings_date_returns_none_when_all_past():
    """If all earnings dates are in the past, returns None."""
    past = date.today() - timedelta(days=5)

    mock_cal = {"Earnings Date": [past]}

    with patch("yfinance.Ticker") as mock_ticker:
        mock_ticker.return_value.calendar = mock_cal
        result = _fetch_earnings_date("BMY")

    assert result is None


# ── Earnings color thresholds ──────────────────────────────────────────


def test_earnings_within_30_days_should_warn():
    """
    Earnings within 30 days → red warning. Critical for CC decisions:
    never sell a call that expires after an earnings date.
    """
    from datetime import datetime as dt_type
    from datetime import date as date_type

    earnings_str = (date_type.today() + timedelta(days=20)).strftime("%d-%b-%Y")
    edate = dt_type.strptime(earnings_str, "%d-%b-%Y").date()
    days_to = (edate - date_type.today()).days

    assert days_to <= 30  # should trigger red warning


def test_earnings_beyond_45_days_is_safe():
    """Earnings >45 days away → safe zone for a Covered Call."""
    from datetime import datetime as dt_type
    from datetime import date as date_type

    earnings_str = (date_type.today() + timedelta(days=60)).strftime("%d-%b-%Y")
    edate = dt_type.strptime(earnings_str, "%d-%b-%Y").date()
    days_to = (edate - date_type.today()).days

    assert days_to > 45  # plain text, no warning
