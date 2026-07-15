from __future__ import annotations

from decimal import Decimal

from app.config.settings import Settings
from app.models.option_contract import OptionContract
from app.models.option_metrics import OptionMetrics
from app.models.score_result import ScoreResult


class OptionScoreEngine:

    def __init__(self) -> None:

        settings = Settings()

        scoring = settings.get(
            "cash_secured_put",
            "scoring",
        )

        #
        # Delta
        #

        self.delta_target = Decimal(
            str(scoring["delta"]["target"])
        )

        self.delta_weight = scoring["delta"]["weight"]

        #
        # Spread
        #

        self.spread_weight = scoring["spread"]["weight"]

        #
        # Volume
        #

        self.volume_weight = scoring["volume"]["weight"]

        self.volume_norm = Decimal(
            str(scoring["volume"]["normalization"])
        )

        #
        # Annualized Return
        #

        self.annualized_weight = scoring[
            "annualized_return"
        ]["weight"]

        self.target_return = Decimal(
            str(
                scoring["annualized_return"]["target"]
            )
        )

    def evaluate(
        self,
        *,
        option: OptionContract,
        metrics: OptionMetrics,
    ) -> ScoreResult:

        delta_score = 0.0
        spread_score = 0.0
        volume_score = 0.0
        annualized_score = 0.0

        #
        # Delta
        #

        if option.delta is not None:

            distance = abs(
                abs(option.delta) - self.delta_target
            )

            delta_score = max(
                0.0,
                self.delta_weight
                - float(distance * Decimal("200")),
            )

        #
        # Spread (bid/ask, expressed as % of ask)
        #

        bid = option.bid or Decimal("0")
        ask = option.ask or Decimal("0")

        if ask > 0:

            spread_pct = (ask - bid) / ask

            spread_score = max(
                0.0,
                self.spread_weight
                - float(spread_pct * Decimal("100")),
            )

        else:

            spread_score = 0.0

        #
        # Volume
        #

        if option.volume is not None:

            volume_score = min(
                self.volume_weight,
                float(
                    Decimal(str(option.volume))
                    / self.volume_norm
                ),
            )

        #
        # Annualized Return
        #

        if metrics.annualized_return is not None:

            annualized_score = min(
                self.annualized_weight,
                float(
                    metrics.annualized_return
                    * Decimal("100")
                    / self.target_return
                    * Decimal(self.annualized_weight)
                ),
            )

        return ScoreResult(
            delta=round(delta_score, 2),
            spread=round(spread_score, 2),
            volume=round(volume_score, 2),
            premium=0.0,
            annualized_return=round(
                annualized_score,
                2,
            ),
        )