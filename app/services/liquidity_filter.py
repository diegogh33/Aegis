from __future__ import annotations

from decimal import Decimal

from app.models.option_contract import OptionContract


class LiquidityFilter:
    """
    Removes illiquid option contracts.

    During development, if market data is unavailable
    (for example because the IBKR account has no market
    data subscription), the contract is kept instead of
    being discarded.
    """

    def __init__(
        self,
        minimum_bid: Decimal = Decimal("0.01"),
        minimum_volume: int = 1,
        maximum_spread_pct: Decimal = Decimal("0.20"),
    ) -> None:

        self.minimum_bid = minimum_bid
        self.minimum_volume = minimum_volume
        self.maximum_spread_pct = maximum_spread_pct

    def apply(
        self,
        contracts: list[OptionContract],
    ) -> list[OptionContract]:

        filtered: list[OptionContract] = []

        for contract in contracts:

            #
            # No market data available.
            #
            # Keep the contract during development.
            #

            if contract.bid is None or contract.ask is None:
                filtered.append(contract)
                continue

            #
            # Minimum premium
            #

            if contract.bid < self.minimum_bid:
                continue

            #
            # Volume
            #

            if (
                contract.volume is not None
                and contract.volume < self.minimum_volume
            ):
                continue

            #
            # Bid / Ask spread
            #

            spread = contract.ask - contract.bid

            if contract.ask > 0:

                spread_pct = spread / contract.ask

                if spread_pct > self.maximum_spread_pct:
                    continue

            filtered.append(contract)

        return filtered