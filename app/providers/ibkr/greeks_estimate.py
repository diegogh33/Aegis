from __future__ import annotations

import math
from decimal import Decimal
from statistics import NormalDist

_NORMAL = NormalDist()

# Used only as a rough estimate for strike selection - not a
# substitute for the real risk-free rate anywhere else in the
# project. Low sensitivity for short-dated options.
_ASSUMED_RISK_FREE_RATE = 0.04


def estimate_put_delta(
    underlying_price: Decimal,
    strike: Decimal,
    days_to_expiration: int,
    implied_volatility: Decimal,
) -> float:
    """
    Estimates a European put's delta using the Black-Scholes formula.

    This exists to pick which strikes are worth requesting real
    market data for (see IBKRProvider.get_put_contracts), before
    IBKR's own Greeks are available - a chicken-and-egg problem,
    since the real delta only comes back after requesting the
    contract's market data in the first place. It uses a single
    reference IV (typically the ATM strike's) rather than each
    strike's own smile-adjusted IV, so it's an approximation for
    strike selection, not a substitute for the real delta used
    everywhere else (DeltaRule, scoring) once market data arrives.

    Confirmed against real IBKR deltas during development: within
    ~0.02-0.03 of the real value for ACN and DRAM options using each
    underlying's own ATM IV.
    """

    S = float(underlying_price)
    K = float(strike)
    T = max(days_to_expiration, 1) / 365
    sigma = float(implied_volatility)

    if sigma <= 0 or S <= 0 or K <= 0:
        return 0.0

    d1 = (
        math.log(S / K) + (_ASSUMED_RISK_FREE_RATE + sigma**2 / 2) * T
    ) / (sigma * math.sqrt(T))

    return _NORMAL.cdf(d1) - 1
