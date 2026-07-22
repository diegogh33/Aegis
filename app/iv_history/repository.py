from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path


@dataclass(frozen=True)
class IVSnapshot:
    """
    A single daily IV observation for a ticker.
    """

    ticker: str
    day: date
    implied_volatility: Decimal


class IVHistoryRepository:
    """
    Local SQLite store for daily IV snapshots, used to calculate
    IV Rank once enough history has accumulated.

    Uses (ticker, day) as the natural key: recording a second snapshot
    for the same ticker on the same day overwrites the first one
    rather than creating a duplicate - by design, since Aegis records
    a snapshot every time a ticker is analyzed, and a ticker can be
    analyzed more than once per day.
    """

    def __init__(self, db_path: str) -> None:

        self._db_path = Path(db_path)

        self._db_path.parent.mkdir(parents=True, exist_ok=True)

        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._db_path)

    def _init_schema(self) -> None:

        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS iv_snapshots (
                    ticker TEXT NOT NULL,
                    day TEXT NOT NULL,
                    implied_volatility TEXT NOT NULL,
                    PRIMARY KEY (ticker, day)
                )
                """
            )

    def record(self, snapshot: IVSnapshot) -> None:

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO iv_snapshots (ticker, day, implied_volatility)
                VALUES (?, ?, ?)
                ON CONFLICT (ticker, day)
                DO UPDATE SET implied_volatility = excluded.implied_volatility
                """,
                (
                    snapshot.ticker,
                    snapshot.day.isoformat(),
                    str(snapshot.implied_volatility),
                ),
            )

    def summary_by_ticker(self) -> list[dict]:
        """
        Returns a summary row per ticker: ticker, days recorded,
        first snapshot date, last snapshot date, and latest IV.
        Ordered by days recorded descending (most progress first).
        """

        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    ticker,
                    COUNT(*) AS days,
                    MIN(day) AS first_day,
                    MAX(day) AS last_day,
                    implied_volatility AS latest_iv
                FROM iv_snapshots
                GROUP BY ticker
                ORDER BY days DESC, ticker ASC
                """
            ).fetchall()

        return [
            {
                "ticker": row[0],
                "days": row[1],
                "first_day": date.fromisoformat(row[2]),
                "last_day": date.fromisoformat(row[3]),
                "latest_iv": Decimal(row[4]),
            }
            for row in rows
        ]

    def history(
        self,
        ticker: str,
        lookback_days: int,
        today: date | None = None,
    ) -> list[IVSnapshot]:
        """
        Returns all recorded snapshots for `ticker` within the last
        `lookback_days` days (inclusive), oldest first.
        """

        if today is None:
            today = date.today()

        cutoff = today - timedelta(days=lookback_days)

        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT ticker, day, implied_volatility
                FROM iv_snapshots
                WHERE ticker = ? AND day >= ?
                ORDER BY day ASC
                """,
                (ticker, cutoff.isoformat()),
            ).fetchall()

        return [
            IVSnapshot(
                ticker=row[0],
                day=date.fromisoformat(row[1]),
                implied_volatility=Decimal(row[2]),
            )
            for row in rows
        ]
