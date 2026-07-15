from __future__ import annotations

from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from app.models.option_contract import OptionContract
from app.models.option_metrics import OptionMetrics


class MetricsEngine:
    """
    Calculates derived metrics for an option contract.

    This class contains no business rules.
    It only performs mathematical calculations.
    """

    @staticmethod
    def calculate(
        *,
        option: OptionContract,
        underlying_price: Decimal,
        today: date | None = None,
    ) -> OptionMetrics:

        if today is None:
            today = date.today()

        dte = max(
            1,
            (option.expiration - today).days,
        )

        #
        # Premium
        #

        mark = option.mark or Decimal("0")

        premium = mark * Decimal(option.multiplier)

        #
        # Capital required (cash secured: strike * multiplier)
        #

        capital_required = option.strike * Decimal(option.multiplier)

        #
        # Return on capital / annualized return
        #

        if capital_required > 0:

            return_on_capital = premium / capital_required

        else:

            return_on_capital = Decimal("0")

        annualized_return = (
            return_on_capital
            * Decimal("365")
            / Decimal(dte)
        )

        #
        # Break-even and downside protection
        #

        break_even = option.strike - mark

        if underlying_price > 0:

            downside_protection = (
                (underlying_price - break_even)
                / underlying_price
            )

        else:

            downside_protection = Decimal("0")

        return OptionMetrics(
            premium=premium.quantize(
                Decimal("0.01"),
                rounding=ROUND_HALF_UP,
            ),
            capital_required=capital_required.quantize(
                Decimal("0.01"),
                rounding=ROUND_HALF_UP,
            ),
            return_on_capital=return_on_capital,
            annualized_return=annualized_return,
            break_even=break_even,
            downside_protection=downside_protection,
            days_to_expiration=dte,
        )