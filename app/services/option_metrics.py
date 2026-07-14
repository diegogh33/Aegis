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

        #
        # Premium
        #

        premium = (
            option.mark
            or option.bid
            or option.last
            or Decimal("0")
        )

        #
        # Capital required (Cash Secured Put)
        #

        capital = option.strike - premium

        if capital <= 0:

            capital = Decimal("0.01")

        #
        # Days to expiration
        #

        days = max(
            1,
            (option.expiration - date.today()).days,
        )

        #
        # Return on capital
        #

        roc = premium / capital

        annualized = (
            roc
            * Decimal("365")
            / Decimal(days)
        )

        #
        # Break-even
        #

        break_even = option.strike - premium

        #
        # Downside protection
        #

        if option.underlying_price is not None:

            downside = (
                option.underlying_price
                - break_even
            ) / option.underlying_price

        else:

            downside = Decimal("0")

        return OptionMetrics(
            premium=premium.quantize(
                Decimal("0.01")
            ),
            capital_required=capital.quantize(
                Decimal("0.01")
            ),
            return_on_capital=roc.quantize(
                Decimal("0.0001")
            ),
            annualized_return=annualized.quantize(
                Decimal("0.0001")
            ),
            break_even=break_even.quantize(
                Decimal("0.01")
            ),
            downside_protection=downside.quantize(
                Decimal("0.0001")
            ),
            days_to_expiration=days,
        )