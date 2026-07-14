from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from ib_async import Contract

from app.models.option_contract import OptionContract


class IBKRMapper:
    """
    Maps IBKR contracts into Aegis domain models.
    """

    @staticmethod
    def option_contract(contract: Contract) -> OptionContract:

        expiration = datetime.strptime(
            contract.lastTradeDateOrContractMonth,
            "%Y%m%d",
        ).date()

        return OptionContract(
            underlying=contract.symbol,
            local_symbol=contract.localSymbol,
            con_id=contract.conId,
            option_type="put" if contract.right == "P" else "call",
            expiration=expiration,
            strike=Decimal(str(contract.strike)),
            exchange=contract.exchange,
            currency=contract.currency,
            multiplier=int(contract.multiplier),

            # Underlying
            underlying_price=None,

            # Prices
            bid=None,
            ask=None,
            last=None,
            mark=None,

            # Greeks
            delta=None,
            gamma=None,
            theta=None,
            vega=None,
            implied_volatility=None,

            # Liquidity
            volume=None,
            open_interest=None,
        )