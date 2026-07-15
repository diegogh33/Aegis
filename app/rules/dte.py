from datetime import date
from decimal import Decimal

from app.config.settings import Settings
from app.core.result import RuleResult
from app.core.rule_status import RuleStatus
from app.rules.base import Rule


class DTERule(Rule):
    """
    Evaluates whether the option's days-to-expiration falls within the
    Constitution's allowed range (config/constitution.yaml,
    cash_secured_put.dte).

    Unlike DeltaRule and NoUpcomingEarningsRule, this rule reads its
    thresholds from Settings instead of hardcoding them - the
    Constitution's own "Configuration First" principle. min/max can
    be overridden explicitly (e.g. for tests) without touching the
    YAML file.
    """

    id = "DTE"

    name = "Days to Expiration"

    blocker = True

    def __init__(
        self,
        min_dte: int | None = None,
        max_dte: int | None = None,
        settings: Settings | None = None,
    ):
        if min_dte is None or max_dte is None:

            settings = settings or Settings()

            dte_config = settings.get("cash_secured_put", "dte")

            if min_dte is None:
                min_dte = dte_config["min"]

            if max_dte is None:
                max_dte = dte_config["max"]

        self.min_dte = min_dte
        self.max_dte = max_dte

    def evaluate(self, candidate):

        expiration = candidate.option.expiration

        days = (expiration - date.today()).days

        if days < self.min_dte:
            return RuleResult(
                rule_id=self.id,
                status=RuleStatus.FAIL,
                score=Decimal("0"),
                message=(
                    f"{days} DTE is below the minimum of {self.min_dte}."
                ),
                blocker=True,
            )

        if days > self.max_dte:
            return RuleResult(
                rule_id=self.id,
                status=RuleStatus.FAIL,
                score=Decimal("0"),
                message=(
                    f"{days} DTE is above the maximum of {self.max_dte}."
                ),
                blocker=True,
            )

        return RuleResult(
            rule_id=self.id,
            status=RuleStatus.PASS,
            score=Decimal("10"),
            message=f"{days} DTE is within the allowed range.",
        )
