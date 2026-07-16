from datetime import date, timedelta
from decimal import Decimal

from app.iv_history.rank import calculate_iv_rank
from app.iv_history.repository import IVSnapshot


def _history(*ivs: str, days: int = 90) -> list[IVSnapshot]:
    today = date.today()
    return [
        IVSnapshot(
            ticker="AAPL",
            day=today - timedelta(days=days - i),
            implied_volatility=Decimal(iv),
        )
        for i, iv in enumerate(ivs)
    ]


def test_not_enough_history_returns_none_rank():
    history = _history("30", "40", "50")  # only 3 days

    result = calculate_iv_rank(
        Decimal("45"), history, minimum_days_required=90
    )

    assert result.rank is None
    assert result.has_enough_history is False
    assert result.days_of_history == 3


def test_calculates_rank_at_the_midpoint():
    # 90 days of history spanning IV 20 to IV 60 - current IV of 40
    # (the midpoint) should rank at 50.
    history = [
        IVSnapshot(
            ticker="AAPL",
            day=date.today() - timedelta(days=90 - i),
            implied_volatility=Decimal("20") if i == 0 else Decimal("60")
            if i == 1
            else Decimal("40"),
        )
        for i in range(90)
    ]

    result = calculate_iv_rank(
        Decimal("40"), history, minimum_days_required=90
    )

    assert result.rank == Decimal("50")
    assert result.has_enough_history is True


def test_current_iv_at_historical_max_ranks_100():
    history = [
        IVSnapshot(
            ticker="AAPL",
            day=date.today() - timedelta(days=90 - i),
            implied_volatility=Decimal("20") if i % 2 == 0 else Decimal("80"),
        )
        for i in range(90)
    ]

    result = calculate_iv_rank(
        Decimal("80"), history, minimum_days_required=90
    )

    assert result.rank == Decimal("100")


def test_current_iv_at_historical_min_ranks_0():
    history = [
        IVSnapshot(
            ticker="AAPL",
            day=date.today() - timedelta(days=90 - i),
            implied_volatility=Decimal("20") if i % 2 == 0 else Decimal("80"),
        )
        for i in range(90)
    ]

    result = calculate_iv_rank(
        Decimal("20"), history, minimum_days_required=90
    )

    assert result.rank == Decimal("0")


def test_flat_history_returns_none_rank_instead_of_dividing_by_zero():
    """
    If every recorded IV in the window is identical, max == min and
    the rank ratio is undefined - should return None (not enough
    signal), not raise or return a misleading 0/100.
    """
    history = [
        IVSnapshot(
            ticker="AAPL",
            day=date.today() - timedelta(days=90 - i),
            implied_volatility=Decimal("40"),
        )
        for i in range(90)
    ]

    result = calculate_iv_rank(
        Decimal("40"), history, minimum_days_required=90
    )

    assert result.rank is None


def test_current_iv_outside_historical_range_is_clamped():
    history = [
        IVSnapshot(
            ticker="AAPL",
            day=date.today() - timedelta(days=90 - i),
            implied_volatility=Decimal("20") if i % 2 == 0 else Decimal("80"),
        )
        for i in range(90)
    ]

    # Current IV higher than anything in the recorded history.
    result = calculate_iv_rank(
        Decimal("200"), history, minimum_days_required=90
    )

    assert result.rank == Decimal("100")
