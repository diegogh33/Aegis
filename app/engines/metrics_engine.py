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

        dte = (option.expiration - today).days

        premium = option.mark * Decimal("100")

        premium_percentage = (
            premium / (option.strike * Decimal("100"))
        )

        annualized_return = (
            premium_percentage
            * Decimal("365")
            / Decimal(dte)
        )

        break_even = option.strike - option.mark

        distance_to_strike_pct = (
            (underlying_price - option.strike)
            / underlying_price
        )

        margin_of_safety_pct = (
            (underlying_price - break_even)
            / underlying_price
        )

        bid_ask_spread = option.ask - option.bid

        bid_ask_spread_pct = (
            bid_ask_spread / option.ask
            if option.ask > 0
            else Decimal("0")
        )

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