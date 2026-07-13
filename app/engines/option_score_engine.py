from __future__ import annotations

from decimal import Decimal

from app.config.settings import Settings
from app.models.option_contract import OptionContract
from app.models.score_result import ScoreResult


class OptionScoreEngine:

    def __init__(self) -> None:

        settings = Settings()

        scoring = settings.get(
            "cash_secured_put",
            "scoring",
        )

        self.delta_target = Decimal(
            str(scoring["delta"]["target"])
        )

        self.delta_weight = scoring["delta"]["weight"]
        self.spread_weight = scoring["spread"]["weight"]
        self.volume_weight = scoring["volume"]["weight"]
        self.volume_norm = scoring["volume"]["normalization"]
        self.premium_weight = scoring["premium"]["weight"]

    def evaluate(
        self,
        option: OptionContract,
    ) -> ScoreResult:

        delta_score = 0.0
        spread_score = 0.0
        volume_score = 0.0
        premium_score = 0.0

        if option.delta is not None:

            distance = abs(
                abs(option.delta) - self.delta_target
            )

            delta_score = max(
                0,
                self.delta_weight - float(distance * Decimal("200")),
            )

        if (
            option.bid is not None
            and option.ask is not None
            and option.ask > 0
        ):

            spread = (option.ask - option.bid) / option.ask

            spread_score = max(
                0,
                self.spread_weight - float(spread * Decimal("100")),
            )

        if option.volume is not None:

            volume_score = min(
                self.volume_weight,
                option.volume / self.volume_norm,
            )

        if option.bid is not None:

            premium_score = min(
                self.premium_weight,
                float(option.bid),
            )

        return ScoreResult(
            delta=round(delta_score, 2),
            spread=round(spread_score, 2),
            volume=round(volume_score, 2),
            premium=round(premium_score, 2),
        )