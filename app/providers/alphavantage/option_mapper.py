from __future__ import annotations

from datetime import date
from decimal import Decimal

from app.models.option_contract import OptionContract


class AlphaVantageOptionMapper:
    """
    Converts Alpha Vantage option JSON into domain models.
    """

    @staticmethod
    def map(contract: dict) -> OptionContract:

        def dec(value):
            if value in ("", None, "None"):
                return None

            return Decimal(str(value))

        return OptionContract(
            symbol=contract["symbol"],
            option_type=contract["type"],
            expiration=date.fromisoformat(contract["expiration"]),
            strike=Decimal(contract["strike"]),
            bid=Decimal(contract["bid"]),
            ask=Decimal(contract["ask"]),
            last=dec(contract.get("last")),
            mark=(Decimal(contract["bid"]) + Decimal(contract["ask"])) / 2,
            volume=int(contract.get("volume", 0)),
            open_interest=int(contract.get("open_interest", 0)),
            implied_volatility=dec(contract.get("implied_volatility")),
            delta=dec(contract.get("delta")),
            gamma=dec(contract.get("gamma")),
            theta=dec(contract.get("theta")),
            vega=dec(contract.get("vega")),
        )