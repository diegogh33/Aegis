from decimal import Decimal

from app.core.result import RuleResult
from app.core.rule_status import RuleStatus
from app.rules.base import Rule


class BelowBuyZoneRule(Rule):
    """
    For the long-term opportunistic strategy: checks whether the
    strike sits at or below the ceiling price Diego considers worth
    entering the stock at (InvestmentThesis.buy_price, mapped from
    ATLAS's entrada_max field).

    Selling a long-dated PUT with a strike above that ceiling would
    mean being assigned shares at a price Diego himself doesn't
    consider attractive - the whole point of this strategy is "if
    assigned, I'm happy to own it at this price".

    When buy_price isn't known (ticker never analyzed in ATLAS, or
    analyzed without an entrada_max), this doesn't block - it surfaces
    the strike's discount to the current underlying price instead, so
    Diego can judge it himself with that context rather than the
    strategy being unavailable just because a formal ATLAS entry
    doesn't exist yet.
    """

    id = "BELOW_BUY_ZONE"

    name = "Below Buy Zone"

    blocker = True

    def evaluate(self, candidate):

        option = candidate.option
        buy_price = candidate.thesis.buy_price

        strike = option.strike
        underlying_price = option.underlying_price

        discount_pct = None

        if underlying_price is not None and underlying_price > 0:
            discount_pct = (
                (underlying_price - strike) / underlying_price * Decimal("100")
            )

        if buy_price is None:

            detail = (
                f"strike is {discount_pct:.1f}% below the current price"
                if discount_pct is not None
                else "current price unavailable to compare"
            )

            return RuleResult(
                rule_id=self.id,
                status=RuleStatus.WARNING,
                score=Decimal("5"),
                message=(
                    f"No ATLAS buy-zone ceiling on record for this "
                    f"company - {detail}. Judge for yourself."
                ),
            )

        if strike <= buy_price:
            return RuleResult(
                rule_id=self.id,
                status=RuleStatus.PASS,
                score=Decimal("10"),
                message=(
                    f"Strike {strike} is at or below the ATLAS buy-zone "
                    f"ceiling of {buy_price}."
                ),
            )

        return RuleResult(
            rule_id=self.id,
            status=RuleStatus.FAIL,
            score=Decimal("0"),
            message=(
                f"Strike {strike} is above the ATLAS buy-zone ceiling "
                f"of {buy_price} - assignment would mean paying more "
                f"than considered attractive."
            ),
            blocker=True,
        )
