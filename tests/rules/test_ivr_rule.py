from datetime import date, timedelta
from decimal import Decimal

from app.core.rule_status import RuleStatus
from app.iv_history.repository import IVHistoryRepository, IVSnapshot
from app.rules.ivr import IVRankRule
from tests.conftest import build_candidate


def _repository_with_history(
    tmp_path,
    ticker: str,
    ivs: list[str],
    days: int = 90,
) -> IVHistoryRepository:
    repo = IVHistoryRepository(str(tmp_path / "iv.db"))

    for i, iv in enumerate(ivs):
        repo.record(
            IVSnapshot(
                ticker=ticker,
                day=date.today() - timedelta(days=days - i),
                implied_volatility=Decimal(iv),
            )
        )

    return repo


def test_missing_implied_volatility_warns_but_does_not_block(tmp_path):
    repo = IVHistoryRepository(str(tmp_path / "iv.db"))

    candidate = build_candidate(delta=-0.20)  # no implied_volatility set

    rule = IVRankRule(repository=repo)
    result = rule.evaluate(candidate)

    assert result.status is RuleStatus.WARNING
    assert result.blocker is False


def test_insufficient_history_warns_but_does_not_block(tmp_path):
    repo = _repository_with_history(
        tmp_path, "SAP", ["30", "40", "50"]
    )  # only 3 days

    candidate = build_candidate(delta=-0.20, implied_volatility="0.45")

    rule = IVRankRule(
        minimum=Decimal("30"),
        preferred_minimum=Decimal("40"),
        lookback_days=365,
        minimum_days_history=90,
        repository=repo,
    )
    result = rule.evaluate(candidate)

    assert result.status is RuleStatus.WARNING
    assert result.blocker is False
    assert "history" in result.message.lower()


def test_high_iv_rank_passes(tmp_path):
    # 90 days of history split between low (20%) and high (60%) IV -
    # current IV near the high end should rank well above the
    # preferred minimum.
    ivs = ["0.20" if i % 2 == 0 else "0.60" for i in range(90)]
    repo = _repository_with_history(tmp_path, "SAP", ivs)

    candidate = build_candidate(delta=-0.20, implied_volatility="0.60")

    rule = IVRankRule(
        minimum=Decimal("30"),
        preferred_minimum=Decimal("40"),
        lookback_days=365,
        minimum_days_history=90,
        repository=repo,
    )
    result = rule.evaluate(candidate)

    assert result.status is RuleStatus.PASS
    assert result.blocker is False


def test_moderate_iv_rank_warns_but_does_not_block(tmp_path):
    ivs = ["0.20" if i % 2 == 0 else "0.60" for i in range(90)]
    repo = _repository_with_history(tmp_path, "SAP", ivs)

    # IV Rank right around 35: above minimum (30) but below preferred
    # minimum (40).
    candidate = build_candidate(delta=-0.20, implied_volatility="0.34")

    rule = IVRankRule(
        minimum=Decimal("30"),
        preferred_minimum=Decimal("40"),
        lookback_days=365,
        minimum_days_history=90,
        repository=repo,
    )
    result = rule.evaluate(candidate)

    assert result.status is RuleStatus.WARNING
    assert result.blocker is False


def test_low_iv_rank_fails_and_blocks(tmp_path):
    ivs = ["0.20" if i % 2 == 0 else "0.60" for i in range(90)]
    repo = _repository_with_history(tmp_path, "SAP", ivs)

    candidate = build_candidate(delta=-0.20, implied_volatility="0.21")

    rule = IVRankRule(
        minimum=Decimal("30"),
        preferred_minimum=Decimal("40"),
        lookback_days=365,
        minimum_days_history=90,
        repository=repo,
    )
    result = rule.evaluate(candidate)

    assert result.status is RuleStatus.FAIL
    assert result.blocker is True


def test_reads_thresholds_from_constitution_yaml_by_default(tmp_path):
    repo = IVHistoryRepository(str(tmp_path / "iv.db"))

    rule = IVRankRule(repository=repo)

    assert rule.minimum == Decimal("30")
    assert rule.preferred_minimum == Decimal("40")
    assert rule.lookback_days == 365
    assert rule.minimum_days_history == 90
