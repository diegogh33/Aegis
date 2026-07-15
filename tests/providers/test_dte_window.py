from datetime import date, timedelta

from app.providers.ibkr.provider import _within_dte_window


def test_expiration_inside_window_returns_true():
    today = date(2026, 7, 15)
    expiration = (today + timedelta(days=37)).strftime("%Y%m%d")

    assert _within_dte_window(
        expiration, min_dte=20, max_dte=60, today=today
    )


def test_expiration_below_minimum_returns_false():
    today = date(2026, 7, 15)
    expiration = (today + timedelta(days=2)).strftime("%Y%m%d")

    assert not _within_dte_window(
        expiration, min_dte=20, max_dte=60, today=today
    )


def test_expiration_above_maximum_returns_false():
    today = date(2026, 7, 15)
    expiration = (today + timedelta(days=120)).strftime("%Y%m%d")

    assert not _within_dte_window(
        expiration, min_dte=20, max_dte=60, today=today
    )


def test_expiration_at_exact_boundaries_returns_true():
    today = date(2026, 7, 15)

    min_expiration = (today + timedelta(days=20)).strftime("%Y%m%d")
    max_expiration = (today + timedelta(days=60)).strftime("%Y%m%d")

    assert _within_dte_window(
        min_expiration, min_dte=20, max_dte=60, today=today
    )
    assert _within_dte_window(
        max_expiration, min_dte=20, max_dte=60, today=today
    )


def test_san_chain_scenario_from_real_run():
    """
    Regression test based on the real EUREX chain fetched for SAN on
    2026-07-15: 19 expirations, most either very near-term (2-9 days)
    or years out. Only a handful fall in a 20-60 day scan window -
    this confirms the filter picks the right ones instead of the old
    [:2] behavior, which only ever looked at the two nearest (2 and 9
    days), both far too short for the Constitution's 30-45 DTE range.
    """
    today = date(2026, 7, 15)

    expirations = [
        "20260717",  # 2 days - too short
        "20260724",  # 9 days - too short
        "20260731",  # 16 days - too short
        "20260807",  # 23 days - in window
        "20260814",  # 30 days - in window
        "20260821",  # 37 days - in window
        "20260918",  # 65 days - too long
        "20261218",  # far out
    ]

    within_window = [
        e
        for e in expirations
        if _within_dte_window(e, min_dte=20, max_dte=60, today=today)
    ]

    assert within_window == ["20260807", "20260814", "20260821"]
