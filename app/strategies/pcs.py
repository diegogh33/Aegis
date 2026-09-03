from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.models.option_contract import OptionContract

# Minimum credit/width ratio for a PCS to be considered viable
# per Plan Operativo S2/S3: ≥25% (adapted from 33% in low-VIX regime)
PCS_MIN_CREDIT_RATIO = Decimal("0.25")

# Minimum OI for both legs of a PCS per Plan Operativo:
# S2: >500 short, S3: >500 short and long.
# Using 500 as the floor for both legs here.
PCS_MIN_OI = 500


@dataclass(frozen=True)
class PCSCandidate:
    """
    A Put Credit Spread candidate: sell the short put (higher strike),
    buy the long put (lower strike) as protection.
    """

    short: OptionContract
    long: OptionContract

    # Calculated fields
    width: Decimal
    credit_mid: Decimal        # mid_short - mid_long
    credit_ratio: Decimal      # credit_mid / width
    break_even: Decimal        # short.strike - credit_mid

    # Optional: ATLAS buy-zone ceiling for the underlying.
    # When set, short strikes above this value fail passes_buy_zone.
    buy_price: Decimal | None = None

    @property
    def passes_credit_ratio(self) -> bool:
        return self.credit_ratio >= PCS_MIN_CREDIT_RATIO

    @property
    def short_oi_ok(self) -> bool:
        oi = self.short.open_interest
        return oi is not None and oi >= PCS_MIN_OI

    @property
    def long_oi_ok(self) -> bool:
        oi = self.long.open_interest
        return oi is not None and oi >= PCS_MIN_OI

    @property
    def oi_ok(self) -> bool:
        return self.short_oi_ok and self.long_oi_ok

    @property
    def passes_buy_zone(self) -> bool:
        """
        True when the short strike is at or below the ATLAS buy-zone
        ceiling (buy_price). If no buy_price is set (ticker not in
        ATLAS or no entrada_max recorded), this is always True -
        consistent with BelowBuyZoneRule's non-blocking behavior for
        tickers without a formal ATLAS thesis.
        """
        if self.buy_price is None:
            return True
        return self.short.strike <= self.buy_price

    @property
    def passes_all(self) -> bool:
        return (
            self.passes_credit_ratio
            and self.oi_ok
            and self.passes_buy_zone
        )


def _mid(contract: OptionContract) -> Decimal | None:
    """Mid price of a contract, or None if bid/ask unavailable."""
    if contract.bid is None or contract.ask is None:
        return None
    return (contract.bid + contract.ask) / 2


def find_pcs_candidates(
    contracts: list[OptionContract],
    buy_price: Decimal | None = None,
) -> list[PCSCandidate]:
    """
    Generates all valid PCS combinations from a list of option contracts.

    Rules:
    - Both legs must be from the same expiration date.
    - Short strike > long strike (short is closer to the money).
    - Both legs must have bid/ask available (needed for credit calc).
    - Credit must be positive (long mid < short mid).
    - Results are sorted: passing spreads first (by credit_ratio desc),
      then non-passing (by credit_ratio desc).

    buy_price: optional ATLAS buy-zone ceiling (InvestmentThesis.
    buy_price). When set, spreads whose short strike exceeds this value
    are generated but marked as failing passes_buy_zone - the sort
    order keeps them below passing candidates. When None (ticker not
    in ATLAS or no entrada_max recorded), no buy-zone check is applied,
    consistent with BelowBuyZoneRule's non-blocking behavior.
    """

    # Group contracts by expiration
    by_expiration: dict = {}
    for c in contracts:
        key = c.expiration
        if key not in by_expiration:
            by_expiration[key] = []
        by_expiration[key].append(c)

    candidates: list[PCSCandidate] = []

    for expiration_contracts in by_expiration.values():

        # Sort by strike descending (short candidates first)
        sorted_contracts = sorted(
            expiration_contracts,
            key=lambda c: c.strike,
            reverse=True,
        )

        for i, short in enumerate(sorted_contracts):

            short_mid = _mid(short)
            if short_mid is None:
                continue

            # Short strike must be at or below the current underlying
            # price — an ITM short PUT means buying shares above market
            # price if assigned, which is never the intent for a PCS.
            # Confirmed with NKE: price $38.75, strike $40 was appearing
            # as a top candidate despite being ITM.
            if (
                short.underlying_price is not None
                and short.underlying_price > 0
                and short.strike > short.underlying_price
            ):
                continue

            for long in sorted_contracts[i + 1:]:

                long_mid = _mid(long)
                if long_mid is None:
                    continue

                credit = short_mid - long_mid

                if credit <= 0:
                    continue

                width = short.strike - long.strike
                if width <= 0:
                    continue

                ratio = credit / width

                candidate = PCSCandidate(
                    short=short,
                    long=long,
                    width=width,
                    credit_mid=credit,
                    credit_ratio=ratio,
                    break_even=short.strike - credit,
                    buy_price=buy_price,
                )

                candidates.append(candidate)

    # Sort: passing first by ratio desc, then non-passing by ratio desc
    return sorted(
        candidates,
        key=lambda c: (0 if c.passes_all else 1, -c.credit_ratio),
    )
