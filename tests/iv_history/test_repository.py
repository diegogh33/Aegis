from datetime import date, timedelta
from decimal import Decimal

from app.iv_history.repository import IVHistoryRepository, IVSnapshot


def test_records_and_retrieves_a_snapshot(tmp_path):
    repo = IVHistoryRepository(str(tmp_path / "iv.db"))

    repo.record(
        IVSnapshot(
            ticker="AAPL",
            day=date(2026, 7, 1),
            implied_volatility=Decimal("0.45"),
        )
    )

    history = repo.history("AAPL", lookback_days=30, today=date(2026, 7, 15))

    assert len(history) == 1
    assert history[0].implied_volatility == Decimal("0.45")


def test_recording_same_ticker_same_day_overwrites_not_duplicates(tmp_path):
    """
    (ticker, day) is the natural key by design: Aegis records a
    snapshot on every analysis, and a ticker can be analyzed more
    than once per day.
    """
    repo = IVHistoryRepository(str(tmp_path / "iv.db"))

    day = date(2026, 7, 1)

    repo.record(
        IVSnapshot(ticker="AAPL", day=day, implied_volatility=Decimal("0.40"))
    )
    repo.record(
        IVSnapshot(ticker="AAPL", day=day, implied_volatility=Decimal("0.50"))
    )

    history = repo.history("AAPL", lookback_days=30, today=day)

    assert len(history) == 1
    assert history[0].implied_volatility == Decimal("0.50")


def test_history_excludes_snapshots_outside_lookback_window(tmp_path):
    repo = IVHistoryRepository(str(tmp_path / "iv.db"))

    today = date(2026, 7, 15)

    repo.record(
        IVSnapshot(
            ticker="AAPL",
            day=today - timedelta(days=10),
            implied_volatility=Decimal("0.40"),
        )
    )
    repo.record(
        IVSnapshot(
            ticker="AAPL",
            day=today - timedelta(days=400),
            implied_volatility=Decimal("0.99"),
        )
    )

    history = repo.history("AAPL", lookback_days=365, today=today)

    assert len(history) == 1
    assert history[0].implied_volatility == Decimal("0.40")


def test_history_is_isolated_per_ticker(tmp_path):
    repo = IVHistoryRepository(str(tmp_path / "iv.db"))

    day = date(2026, 7, 1)

    repo.record(
        IVSnapshot(ticker="AAPL", day=day, implied_volatility=Decimal("0.40"))
    )
    repo.record(
        IVSnapshot(ticker="MSFT", day=day, implied_volatility=Decimal("0.30"))
    )

    aapl_history = repo.history("AAPL", lookback_days=30, today=day)

    assert len(aapl_history) == 1
    assert aapl_history[0].ticker == "AAPL"


def test_history_returns_oldest_first(tmp_path):
    repo = IVHistoryRepository(str(tmp_path / "iv.db"))

    today = date(2026, 7, 15)

    repo.record(
        IVSnapshot(
            ticker="AAPL",
            day=today - timedelta(days=2),
            implied_volatility=Decimal("0.40"),
        )
    )
    repo.record(
        IVSnapshot(
            ticker="AAPL",
            day=today - timedelta(days=5),
            implied_volatility=Decimal("0.35"),
        )
    )

    history = repo.history("AAPL", lookback_days=30, today=today)

    assert [s.day for s in history] == sorted(s.day for s in history)


def test_summary_by_ticker_returns_counts_and_dates(tmp_path):
    repo = IVHistoryRepository(str(tmp_path / "iv.db"))

    today = date(2026, 7, 15)

    for i in range(5):
        repo.record(
            IVSnapshot(
                ticker="AAPL",
                day=today - timedelta(days=i),
                implied_volatility=Decimal("0.30"),
            )
        )
    repo.record(
        IVSnapshot(
            ticker="ACN",
            day=today,
            implied_volatility=Decimal("0.47"),
        )
    )

    summaries = repo.summary_by_ticker()

    assert len(summaries) == 2
    # AAPL has more days, should be first
    assert summaries[0]["ticker"] == "AAPL"
    assert summaries[0]["days"] == 5
    assert summaries[0]["first_day"] == today - timedelta(days=4)
    assert summaries[0]["last_day"] == today
    assert summaries[1]["ticker"] == "ACN"
    assert summaries[1]["days"] == 1
