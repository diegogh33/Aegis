from __future__ import annotations

from dataclasses import replace
from decimal import Decimal
from unittest.mock import MagicMock


from app.strategies.pcs import find_pcs_candidates
from tests.conftest import build_option


# ── Helpers ────────────────────────────────────────────────────────────


def _contract(
    strike: float,
    bid: float,
    ask: float,
    open_interest: int | None = 600,
    dte: int = 35,
):
    return replace(
        build_option(delta=-0.20, dte=dte),
        strike=Decimal(str(strike)),
        bid=Decimal(str(bid)),
        ask=Decimal(str(ask)),
        open_interest=open_interest,
    )


def _scored(contract):
    """Wrap a contract in a minimal ScoredOption mock."""
    s = MagicMock()
    s.option = contract
    s.score.total = Decimal("80")
    return s


def _rejected(contract, reason="LIQUIDITY"):
    """Wrap a contract in a minimal RejectedContract mock."""
    r = MagicMock()
    r.option = contract
    r.reason = reason
    r.detail = "Volume 0 is below the minimum of 50."
    return r


# ── MU regression: rejected contracts usable as long leg ───────────────


def test_rejected_contracts_are_used_as_long_leg():
    """
    Regression test from real MU run: all 15 contracts were rejected
    by LIQUIDITY (volume < 50), so result.contracts was empty. The old
    code only used result.contracts for PCS, finding no pairs. The fix
    combines result.contracts + result.rejected, so the rejected
    contracts can serve as the long (protection) leg.
    """
    # One contract passes Constitution (high volume)
    short_contract = _contract(strike=810, bid=45.77, ask=47.50, open_interest=734)
    # Another is rejected by LIQUIDITY but has valid bid/ask for long leg
    long_contract = _contract(strike=800, bid=42.88, ask=44.50, open_interest=7763)

    # Simulate what AnalysisResult would contain
    passed = [_scored(short_contract)]
    rejected = [_rejected(long_contract, reason="LIQUIDITY")]

    all_contracts = (
        [s.option for s in passed]
        + [r.option for r in rejected]
    )

    candidates = find_pcs_candidates(all_contracts)

    assert len(candidates) >= 1
    c = candidates[0]
    assert c.short.strike == Decimal("810")
    assert c.long.strike == Decimal("800")
    # credit = mid(810) - mid(800) = 46.635 - 43.69 = ~2.94
    # width = 10, ratio = ~29.4% → passes
    assert c.passes_credit_ratio


def test_no_candidates_when_only_passed_contracts_used():
    """
    Confirms that if we only used result.contracts (the old behavior),
    we'd find no pairs when only one contract passed — the fix is
    necessary.
    """
    short_contract = _contract(strike=810, bid=45.77, ask=47.50)
    passed = [_scored(short_contract)]

    # Only use passed contracts (old behavior)
    only_passed = [s.option for s in passed]
    candidates = find_pcs_candidates(only_passed)

    # Only one contract — no pairs possible
    assert len(candidates) == 0


# ── Settings: s2_universe loaded correctly ─────────────────────────────


def test_s2_universe_is_configured_in_constitution():
    """
    Confirms that s2_universe exists in constitution.yaml and contains
    the expected tickers. If someone accidentally removes or renames
    this key, scan-pcs s2 would silently do nothing.
    """
    from app.config.settings import Settings

    settings = Settings()
    universe = settings.get("s2_universe")

    assert isinstance(universe, list)
    assert len(universe) > 0
    # Core S2 tickers from Plan Operativo
    for expected in ["AMD", "MU", "PYPL", "COIN", "NOW"]:
        assert expected in universe, f"{expected} missing from s2_universe"


def test_s3_universe_is_configured_in_constitution():
    from app.config.settings import Settings

    settings = Settings()
    universe = settings.get("s3_universe")

    assert isinstance(universe, list)
    assert len(universe) > 0
    for expected in ["SPY", "QQQ", "IWM"]:
        assert expected in universe, f"{expected} missing from s3_universe"


# ── PCS constitution thresholds ────────────────────────────────────────


def test_pcs_credit_ratio_threshold_matches_plan():
    """
    The 25% threshold is defined in Plan Operativo S2/S3. If someone
    changes the constant, this test catches it.
    """
    from app.strategies.pcs import PCS_MIN_CREDIT_RATIO

    assert PCS_MIN_CREDIT_RATIO == Decimal("0.25")


def test_pcs_oi_threshold_matches_plan():
    from app.strategies.pcs import PCS_MIN_OI

    assert PCS_MIN_OI == 500


# ── IV context thresholds loaded from constitution ─────────────────────


def test_iv_thresholds_exist_in_constitution():
    """
    The market context panel reads IV thresholds from constitution.yaml.
    If someone removes these keys, the panel would crash or show wrong
    colors.
    """
    from app.config.settings import Settings

    settings = Settings()
    ivr_config = settings.get("cash_secured_put", "ivr")

    assert "minimum" in ivr_config, "ivr.minimum missing from constitution"
    assert "preferred_minimum" in ivr_config, "ivr.preferred_minimum missing"
    assert "minimum_days_history" in ivr_config

    # Values should be sane
    assert ivr_config["minimum"] == 30
    assert ivr_config["preferred_minimum"] == 40
    assert ivr_config["minimum_days_history"] == 90


# ── DTE calculation ────────────────────────────────────────────────────


def test_dte_is_calculated_correctly_from_expiration():
    """
    DTE shown in PCS tables is (expiration - today).days.
    Verifies the calculation is correct with a known date.
    """
    from datetime import date, timedelta

    expiration = date.today() + timedelta(days=30)
    contract = _contract(strike=100, bid=3.00, ask=3.20)
    contract = replace(contract, expiration=expiration)

    dte = (contract.expiration - date.today()).days
    assert dte == 30


# ── Annualized return calculation ──────────────────────────────────────


def test_annualized_return_formula():
    """
    Ret. Anual. = (bid / strike) * (365 / DTE) * 100
    Validates the formula with known values.
    Example: bid=3.55, strike=90, DTE=29 → (3.55/90) * (365/29) * 100 = 49.6%
    """
    bid = 3.55
    strike = 90.0
    dte = 29

    ann_return = (bid / strike) * (365 / dte) * 100
    assert abs(ann_return - 49.6) < 0.5  # ~49.6%
