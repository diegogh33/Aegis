from decimal import Decimal

from app.config.settings import Settings
from app.core.result import RuleResult
from app.core.rule_status import RuleStatus
from app.rules.base import Rule


class LiquidityRule(Rule):
    """
    Evaluates whether an option contract has enough liquidity
    (volume, open interest) to be tradeable without excessive slippage.

    Reads its thresholds from constitution.yaml (cash_secured_put.
    liquidity) via Settings, following DTERule's pattern rather than
    DeltaRule/NoUpcomingEarningsRule's hardcoded defaults.

    Missing market data (volume/open_interest is None) is treated as
    PASS, not FAIL - this preserves the "keep the contract during
    development" behavior of the old LiquidityFilter service, needed
    because IBKR doesn't always return this data (see README).
    """

    id = "LIQUIDITY"

    name = "Liquidity"

    blocker = True

    def __init__(
        self,
        minimum_volume: int | None = None,
        minimum_open_interest: int | None = None,
        settings: Settings | None = None,
    ):
        if minimum_volume is None or minimum_open_interest is None:

            settings = settings or Settings()

            liquidity_config = settings.get(
                "cash_secured_put", "liquidity"
            )

            if minimum_volume is None:
                minimum_volume = liquidity_config["minimum_volume"]

            if minimum_open_interest is None:
                minimum_open_interest = liquidity_config[
                    "minimum_open_interest"
                ]

        self.minimum_volume = minimum_volume
        self.minimum_open_interest = minimum_open_interest

    def evaluate(self, candidate):

        option = candidate.option

        if option.volume is not None and option.volume < self.minimum_volume:
            return RuleResult(
                rule_id=self.id,
                status=RuleStatus.FAIL,
                score=Decimal("0"),
                message=(
                    f"Volume {option.volume} is below the minimum of "
                    f"{self.minimum_volume}."
                ),
                blocker=True,
            )

        if (
            option.open_interest is not None
            and option.open_interest < self.minimum_open_interest
        ):
            return RuleResult(
                rule_id=self.id,
                status=RuleStatus.FAIL,
                score=Decimal("0"),
                message=(
                    f"Open interest {option.open_interest} is below the "
                    f"minimum of {self.minimum_open_interest}."
                ),
                blocker=True,
            )

        return RuleResult(
            rule_id=self.id,
            status=RuleStatus.PASS,
            score=Decimal("10"),
            message="Liquidity is within acceptable limits.",
        )
