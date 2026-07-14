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

        premium = mark * Decimal("100")

        premium_percentage = (
            premium / (option.strike * Decimal("100"))
        )

        annualized_return = (
            premium_percentage
            * Decimal("365")
            / Decimal(dte)
        )

        #
        # Break-even
        #

        break_even = option.strike - mark

        #
        # Distance to strike
        #

        if underlying_price > 0:

            distance_to_strike_pct = (
                (underlying_price - option.strike)
                / underlying_price
            )

            margin_of_safety_pct = (
                (underlying_price - break_even)
                / underlying_price
            )

        else:

            distance_to_strike_pct = Decimal("0")
            margin_of_safety_pct = Decimal("0")

        #
        # Spread
        #

        bid = option.bid or Decimal("0")
        ask = option.ask or Decimal("0")

        bid_ask_spread = ask - bid

        if ask > 0:

            bid_ask_spread_pct = (
                bid_ask_spread / ask
            )

        else:

            bid_ask_spread_pct = Decimal("0")

        #
        # Liquidity
        #

        liquidity_score = Decimal("0")

        return OptionMetrics(
            premium=premium.quantize(
                Decimal("0.01"),
                rounding=ROUND_HALF_UP,
            ),
            premium_percentage=premium_percentage,
            annualized_return=annualized_return,
            return_on_cash=annualized_return,
            break_even=break_even,
            distance_to_strike_pct=distance_to_strike_pct,
            margin_of_safety_pct=margin_of_safety_pct,
            bid_ask_spread=bid_ask_spread,
            bid_ask_spread_pct=bid_ask_spread_pct,
            liquidity_score=liquidity_score,
            implied_volatility=option.implied_volatility,
            days_to_expiration=dte,
        )