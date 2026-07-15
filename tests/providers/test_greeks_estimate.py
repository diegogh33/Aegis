from decimal import Decimal

from app.providers.ibkr.greeks_estimate import estimate_put_delta


def test_acn_strikes_match_real_ibkr_deltas_within_tolerance():
    """
    Regression/calibration test: values compared directly against
    real IBKR deltas observed for ACN (underlying ~139.09, IV ~47%,
    37 DTE) during this session's diagnostics.

        strike | real IBKR delta
        120    | -0.153
        125    | -0.221
        130    | -0.306
        135    | -0.395

    Estimates should land within ~0.03 of the real value - it's an
    approximation using a single reference IV, not each strike's own
    smile-adjusted IV, so it's not expected to match exactly.
    """
    S = Decimal("139.09")
    iv = Decimal("0.478")  # roughly the ATM IV observed for this chain
    dte = 37

    cases = [
        (Decimal("120"), -0.153),
        (Decimal("125"), -0.221),
        (Decimal("130"), -0.306),
        (Decimal("135"), -0.395),
    ]

    for strike, real_delta in cases:
        estimate = estimate_put_delta(S, strike, dte, iv)
        assert abs(estimate - real_delta) < 0.03


def test_dram_high_iv_strikes_are_further_from_price_than_acn():
    """
    The finding that motivated this change: with DRAM's much higher
    IV (~95% vs ACN's ~47%), the strikes landing near a -0.20 delta
    target sit much further (in absolute price terms) from the
    underlying price than for a low-IV stock at the same DTE - so a
    fixed "N closest strikes to price" selection misses them.
    """
    S = Decimal("56.61")
    iv = Decimal("0.95")
    dte = 37

    # From the real DRAM chain: strike 47 (~17% OTM) had delta ~-0.22.
    estimate = estimate_put_delta(S, Decimal("47"), dte, iv)

    assert -0.30 < estimate < -0.15

    distance_from_price = float(S) - 47
    assert distance_from_price > 9  # far from the underlying price


def test_delta_moves_toward_zero_as_strike_moves_further_otm():
    S = Decimal("100")
    iv = Decimal("0.40")
    dte = 30

    deep_otm = estimate_put_delta(S, Decimal("70"), dte, iv)
    near_atm = estimate_put_delta(S, Decimal("95"), dte, iv)

    assert abs(deep_otm) < abs(near_atm)


def test_zero_or_negative_inputs_return_zero_instead_of_raising():
    assert estimate_put_delta(Decimal("0"), Decimal("100"), 30, Decimal("0.4")) == 0.0
    assert estimate_put_delta(Decimal("100"), Decimal("0"), 30, Decimal("0.4")) == 0.0
    assert estimate_put_delta(Decimal("100"), Decimal("100"), 30, Decimal("0")) == 0.0
