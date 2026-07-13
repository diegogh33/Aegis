from __future__ import annotations

from decimal import Decimal

from app.models.option_contract import OptionContract


class LiquidityFilter:
    """
    Removes illiquid option contracts.
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

            if contract.bid is None or contract.ask is None:
                continue

            if contract.bid < self.minimum_bid:
                continue

            if contract.volume is None:
                continue

            if contract.volume < self.minimum_volume:
                continue

            spread = contract.ask - contract.bid

            if contract.ask > 0:

                spread_pct = spread / contract.ask

                if spread_pct > self.maximum_spread_pct:
                    continue

            filtered.append(contract)

        return filtered