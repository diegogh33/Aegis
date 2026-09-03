from __future__ import annotations

from dataclasses import replace
from datetime import date
from decimal import Decimal

from app.strategies.pcs import PCS_MIN_OI, find_pcs_candidates
from tests.conftest import build_option


def _contract(
    strike: float,
    bid: float,
    ask: float,
    open_interest: int | None = 600,
    dte: int = 35,
):
    # Set underlying_price 25% above strike so contracts are OTM by default.
    # Tests that specifically test the ITM filter set their own underlying_price.
    underlying_price = Decimal(str(round(strike * 1.25, 2)))
    return replace(
        build_option(delta=-0.20, dte=dte),
        strike=Decimal(str(strike)),
        bid=Decimal(str(bid)),
        ask=Decimal(str(ask)),
        open_interest=open_interest,
        underlying_price=underlying_price,
    )


def test_generates_pcs_combination_from_two_contracts():
    short = _contract(strike=110, bid=3.20, ask=3.70)
    long = _contract(strike=100, bid=1.37, ask=1.77)

    candidates = find_pcs_candidates([short, long])

    assert len(candidates) == 1
    c = candidates[0]
    assert c.short.strike == Decimal("110")
    assert c.long.strike == Decimal("100")
    assert c.width == Decimal("10")
    # mid_short = (3.20 + 3.70) / 2 = 3.45
    # mid_long  = (1.37 + 1.77) / 2 = 1.57
    # credit    = 3.45 - 1.57 = 1.88
    assert abs(c.credit_mid - Decimal("1.88")) < Decimal("0.01")
    # ratio = 1.88 / 10 = 18.8% — below 25%
    assert not c.passes_credit_ratio


def test_pcs_passes_when_credit_ratio_above_25_percent():
    # SPOT real example from plan: PCS 390/370, credit ~$5.60, ancho $20 → 28%
    short = _contract(strike=390, bid=5.40, ask=5.80)
    long = _contract(strike=370, bid=0.10, ask=0.30)

    candidates = find_pcs_candidates([short, long])

    assert len(candidates) == 1
    c = candidates[0]
    assert c.passes_credit_ratio


def test_groups_by_expiration_no_cross_expiry_pairs():
    short_aug = _contract(strike=110, bid=3.20, ask=3.70, dte=35)
    long_sep = replace(
        _contract(strike=100, bid=1.37, ask=1.77, dte=65),
        expiration=date.today().replace(month=9),
    )

    candidates = find_pcs_candidates([short_aug, long_sep])

    # Different expirations — no valid pair
    assert len(candidates) == 0


def test_oi_flag_correctly_marks_low_oi_legs():
    short = _contract(strike=110, bid=3.20, ask=3.70, open_interest=50)
    long = _contract(strike=100, bid=1.37, ask=1.77, open_interest=600)

    candidates = find_pcs_candidates([short, long])

    assert len(candidates) == 1
    c = candidates[0]
    assert not c.short_oi_ok
    assert c.long_oi_ok
    assert not c.oi_ok
    assert not c.passes_all


def test_passing_spreads_sorted_before_failing():
    # Two spreads: one passes ratio, one doesn't
    contracts = [
        _contract(strike=120, bid=6.10, ask=7.00),   # high mid ~6.55
        _contract(strike=110, bid=3.20, ask=3.70),   # mid 3.45
        _contract(strike=100, bid=1.37, ask=1.77),   # mid 1.57
    ]

    candidates = find_pcs_candidates(contracts)

    # 120/110 → credit = 6.55 - 3.45 = 3.10, ratio = 31% → passes
    # 120/100 → credit = 6.55 - 1.57 = 4.98, ratio = 24.9% → just fails
    # 110/100 → credit = 3.45 - 1.57 = 1.88, ratio = 18.8% → fails
    assert candidates[0].passes_credit_ratio
    assert candidates[0].short.strike == Decimal("120")
    assert candidates[0].long.strike == Decimal("110")


def test_itm_short_strike_is_excluded():
    """
    Regression test from real NKE case: price $38.75, but strike $40
    was appearing as a top PCS candidate despite being ITM. A short PUT
    with strike above the current price means buying shares above market
    value if assigned — never valid for a PCS.
    """
    # Short strike $40 ITM (price $38.75)
    itm_short = replace(
        _contract(strike=40, bid=2.87, ask=2.87),
        underlying_price=Decimal("38.75"),
    )
    long = replace(
        _contract(strike=35, bid=0.74, ask=0.74),
        underlying_price=Decimal("38.75"),
    )

    candidates = find_pcs_candidates([itm_short, long])

    # ITM short should produce no candidates
    assert len(candidates) == 0


def test_otm_short_strike_is_included():
    """OTM short strike (below price) should still produce candidates."""
    otm_short = replace(
        _contract(strike=36, bid=2.00, ask=2.00),
        underlying_price=Decimal("38.75"),
    )
    long = replace(
        _contract(strike=32, bid=0.50, ask=0.50),
        underlying_price=Decimal("38.75"),
    )

    candidates = find_pcs_candidates([otm_short, long])

    assert len(candidates) == 1
    assert candidates[0].short.strike == Decimal("36")
    assert PCS_MIN_OI == 500


def test_short_strike_above_buy_price_fails_buy_zone():
    """
    Regression: if the short strike is above the ATLAS buy-zone ceiling,
    being assigned would mean buying shares at a price above what Diego
    considers attractive - the spread should not pass even if
    credit/width and OI are fine.
    """
    short = _contract(strike=120, bid=6.10, ask=7.00)
    long = _contract(strike=110, bid=3.20, ask=3.70)

    # buy_price=115: short strike 120 > 115 → fails buy zone
    candidates = find_pcs_candidates(
        [short, long],
        buy_price=Decimal("115"),
    )

    assert len(candidates) == 1
    c = candidates[0]
    assert not c.passes_buy_zone
    assert not c.passes_all


def test_short_strike_at_buy_price_passes_buy_zone():
    short = _contract(strike=110, bid=3.20, ask=3.70)
    long = _contract(strike=100, bid=1.37, ask=1.77)

    candidates = find_pcs_candidates(
        [short, long],
        buy_price=Decimal("110"),
    )

    assert candidates[0].passes_buy_zone


def test_no_buy_price_always_passes_buy_zone():
    """No ATLAS entry → no buy-zone check → same behavior as before."""
    short = _contract(strike=500, bid=6.10, ask=7.00)
    long = _contract(strike=480, bid=3.20, ask=3.70)

    candidates = find_pcs_candidates([short, long], buy_price=None)

    assert candidates[0].passes_buy_zone


def test_buy_zone_failure_shown_before_other_failures_in_sort():
    """
    A spread that passes all filters (including buy_zone) should appear
    before one that only fails buy_zone.
    """
    # Passes all: credit ratio 66.3%, short 110 <= buy_price 115
    passing_short = _contract(strike=110, bid=8.00, ask=8.40)
    passing_long = _contract(strike=100, bid=1.37, ask=1.77)

    # Fails buy_zone only: short 120 > buy_price 115
    zone_short = _contract(strike=120, bid=6.10, ask=7.00)
    zone_long2 = _contract(strike=100, bid=1.37, ask=1.77)

    candidates = find_pcs_candidates(
        [passing_short, passing_long, zone_short, zone_long2],
        buy_price=Decimal("115"),
    )

    passing = [c for c in candidates if c.passes_all]
    assert len(passing) >= 1

    first_passing_idx = next(
        i for i, c in enumerate(candidates) if c.passes_all
    )
    first_failing_idx = next(
        i for i, c in enumerate(candidates) if not c.passes_all
    )
    assert first_passing_idx < first_failing_idx
