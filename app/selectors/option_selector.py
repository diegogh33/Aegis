from __future__ import annotations

from app.models.option_contract import OptionContract
from app.selectors.base import Selector


class OptionSelector(Selector):
    """
    Selects the best option contracts from an option chain.

    NOTE:
    This is an initial implementation. The scoring algorithm will
    evolve over time as more business rules are incorporated.
    """

    def select(
        self,
        contracts: list[OptionContract],
    ) -> list[OptionContract]:

        valid_contracts = [
            contract
            for contract in contracts
            if self._is_valid(contract)
        ]

        return sorted(
            valid_contracts,
            key=self._score,
            reverse=True,
        )

    def _is_valid(
        self,
        contract: OptionContract,
    ) -> bool:

        return (
            contract.delta is not None
            and contract.open_interest is not None
            and contract.bid > 0
        )

    def _score(
        self,
        contract: OptionContract,
    ) -> float:
        """
        Temporary scoring algorithm.
        """

        score = 0.0

        # Prefer deltas close to -0.20
        score += max(
            0,
            1 - abs(contract.delta + 0.20),
        ) * 40

        # Liquidity
        score += min(
            contract.open_interest / 1000,
            1,
        ) * 30

        # Premium
        score += float(contract.bid) * 5

        return score