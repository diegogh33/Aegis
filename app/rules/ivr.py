from __future__ import annotations

from decimal import Decimal

from app.config.settings import Settings
from app.core.result import RuleResult
from app.core.rule_status import RuleStatus
from app.iv_history.rank import calculate_iv_rank
from app.iv_history.repository import IVHistoryRepository
from app.rules.base import Rule


class IVRankRule(Rule):
    """
    Evaluates whether the option's current implied volatility is high
    enough (relative to its own recent history) to be worth selling
    premium on - Diego's real trading system's own thresholds
    (Sistema_Venta_Prima.md): IVR >= 30 acceptable, preferably >= 40.

    IV Rank requires historical daily IV snapshots, which none of the
    data providers give reliably - Aegis builds its own history over
    time (see app/iv_history/), recording a snapshot on every
    analysis. Until minimum_days_history days of history have
    accumulated for a ticker, this rule can't evaluate meaningfully
    and passes without blocking (score 5, a neutral middle value -
    not the 10 a real PASS would score, since this isn't a confirmed
    PASS, just an unevaluated case) rather than failing candidates
    over a data gap that will resolve itself over time.

    Reads its thresholds from constitution.yaml
    (cash_secured_put.ivr) via Settings by default, following
    DTERule's pattern.
    """

    id = "IVR"

    name = "IV Rank"

    blocker = True

    def __init__(
        self,
        minimum: Decimal | None = None,
        preferred_minimum: Decimal | None = None,
        lookback_days: int | None = None,
        minimum_days_history: int | None = None,
        settings: Settings | None = None,
        repository: IVHistoryRepository | None = None,
        config_section: str = "cash_secured_put",
        can_block: bool = True,
    ):
        if (
            minimum is None
            or preferred_minimum is None
            or lookback_days is None
            or minimum_days_history is None
        ):

            settings = settings or Settings()

            ivr_config = settings.get(config_section, "ivr")

            if minimum is None:
                minimum = Decimal(str(ivr_config["minimum"]))

            if preferred_minimum is None:
                preferred_minimum = Decimal(
                    str(ivr_config["preferred_minimum"])
                )

            if lookback_days is None:
                lookback_days = ivr_config["lookback_days"]

            if minimum_days_history is None:
                minimum_days_history = ivr_config["minimum_days_history"]

        self.minimum = minimum
        self.preferred_minimum = preferred_minimum
        self.lookback_days = lookback_days
        self.minimum_days_history = minimum_days_history
        self.can_block = can_block

        if repository is None:
            settings = settings or Settings()
            repository = IVHistoryRepository(settings.iv_history_db_path)

        self.repository = repository

    def evaluate(self, candidate):

        current_iv = candidate.option.implied_volatility

        if current_iv is None:
            return RuleResult(
                rule_id=self.id,
                status=RuleStatus.WARNING,
                score=Decimal("5"),
                message="No implied volatility available to rank.",
            )

        ticker = candidate.company.symbol

        history = self.repository.history(
            ticker,
            lookback_days=self.lookback_days,
        )

        # current_iv and the values already stored in `history` are
        # both expressed as fractions (e.g. 0.47 for 47%, as IBKR
        # provides it) - calculate_iv_rank does its own internal
        # *100 normalization to produce a 0-100 rank, comparable
        # against the Constitution's minimum/preferred_minimum
        # (e.g. 30, 40). Multiplying current_iv by 100 here before
        # calling calculate_iv_rank would compare a percentage
        # against fractions still in `history`, producing a
        # meaningless result.
        result = calculate_iv_rank(
            current_iv,
            history,
            minimum_days_required=self.minimum_days_history,
        )

        if not result.has_enough_history or result.rank is None:
            return RuleResult(
                rule_id=self.id,
                status=RuleStatus.WARNING,
                score=Decimal("5"),
                message=(
                    f"Not enough IV history yet to rank "
                    f"({result.days_of_history}/"
                    f"{result.minimum_days_required} days) - "
                    f"passing without blocking."
                ),
            )

        rank = result.rank

        if rank >= self.preferred_minimum:
            return RuleResult(
                rule_id=self.id,
                status=RuleStatus.PASS,
                score=Decimal("10"),
                message=f"IV Rank {rank:.1f} is at or above the preferred minimum of {self.preferred_minimum}.",
            )

        if rank >= self.minimum:
            return RuleResult(
                rule_id=self.id,
                status=RuleStatus.WARNING,
                score=Decimal("6"),
                message=f"IV Rank {rank:.1f} is acceptable but below the preferred minimum of {self.preferred_minimum}.",
            )

        return RuleResult(
            rule_id=self.id,
            status=RuleStatus.FAIL,
            score=Decimal("0"),
            message=f"IV Rank {rank:.1f} is below the minimum of {self.minimum}.",
            blocker=self.can_block,
        )
