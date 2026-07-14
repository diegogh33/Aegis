from __future__ import annotations

from datetime import date
from decimal import Decimal

from app.models.option_contract import OptionContract
from app.models.option_metrics import OptionMetrics


class OptionMetricsService:
    """
    Calculates financial metrics for an option contract.
    """

    def calculate(
        self,
        option: OptionContract,
    ) -> OptionMetrics:

        premium = option.bid or Decimal("0")

        capital = option.strike - premium

        if capital <= 0:
            capital = Decimal("0.01")

        days = max(
            1,
            (option.expiration - date.today()).days,
        )

        roc = premium / capital

        annualized = roc * Decimal("365") / Decimal(days)

        break_even = option.strike - premium

        if option.underlying_price is not None:

            downside = (
                (option.underlying_price - break_even)
                / option.underlying_price
            )

        else:

            downside = Decimal("0")

        return OptionMetrics(
            premium=premium,
            capital_required=capital,
            return_on_capital=roc,
            annualized_return=annualized,
            break_even=break_even,
            downside_protection=downside,
            days_to_expiration=days,
        )