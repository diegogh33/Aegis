from decimal import Decimal

from app.config.settings import Settings
from app.core.result import RuleResult
from app.core.rule_status import RuleStatus
from app.rules.base import Rule


class SpreadRule(Rule):
    """
    Evaluates whether an option contract's bid/ask spread is tight
    enough to be tradeable without excessive slippage.

    Reads its threshold from constitution.yaml (<config_section>.
    spread.maximum_percent) via Settings. config_section defaults to
    "cash_secured_put"; the long-term strategy uses config_section=
    "long_term_put" to allow wider spreads (long-dated options
    structurally have wider spreads than short-dated ones).

    Missing market data (bid or ask is None) is treated as PASS, not
    FAIL - same "keep the contract during development" behavior as
    LiquidityRule, needed because IBKR doesn't always return this
    data (see README).
    """

    id = "SPREAD"

    name = "Bid/Ask Spread"

    blocker = True

    def __init__(
        self,
        maximum_percent: Decimal | None = None,
        settings: Settings | None = None,
        config_section: str = "cash_secured_put",
    ):
        if maximum_percent is None:

            settings = settings or Settings()

            spread_config = settings.get(config_section, "spread")

            maximum_percent = Decimal(
                str(spread_config["maximum_percent"])
            )

        self.maximum_percent = maximum_percent

    def evaluate(self, candidate):

        option = candidate.option

        if option.bid is None or option.ask is None:
            return RuleResult(
                rule_id=self.id,
                status=RuleStatus.PASS,
                score=Decimal("10"),
                message="No bid/ask data available.",
            )

        if option.ask <= 0:
            return RuleResult(
                rule_id=self.id,
                status=RuleStatus.PASS,
                score=Decimal("10"),
                message="Ask price is zero or negative; cannot evaluate "
                "spread.",
            )

        spread_pct = (
            (option.ask - option.bid) / option.ask * Decimal("100")
        )

        if spread_pct > self.maximum_percent:
            return RuleResult(
                rule_id=self.id,
                status=RuleStatus.FAIL,
                score=Decimal("0"),
                message=(
                    f"Spread {spread_pct:.1f}% exceeds the maximum of "
                    f"{self.maximum_percent}%."
                ),
                blocker=True,
            )

        return RuleResult(
            rule_id=self.id,
            status=RuleStatus.PASS,
            score=Decimal("10"),
            message=f"Spread {spread_pct:.1f}% is within the allowed limit.",
        )
