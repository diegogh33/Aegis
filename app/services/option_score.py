from __future__ import annotations

from decimal import Decimal

from app.config.settings import Settings
from app.models.option_contract import OptionContract


class OptionScore:

    def __init__(self) -> None:

        settings = Settings()

        self.delta_target = Decimal(
            str(
                settings.get(
                    "option_scoring",
                    "delta",
                    "target",
                )
            )
        )

        self.delta_weight = settings.get(
            "option_scoring",
            "delta",
            "weight",
        )

        self.spread_weight = settings.get(
            "option_scoring",
            "spread",
            "weight",
        )

        self.volume_weight = settings.get(
            "option_scoring",
            "volume",
            "weight",
        )

        self.volume_norm = settings.get(
            "option_scoring",
            "volume",
            "normalization",
        )

        self.premium_weight = settings.get(
            "option_scoring",
            "premium",
            "weight",
        )

    def score(
        self,
        option: OptionContract,
    ) -> float:

        score = 0.0

        if option.delta is not None:

            distance = abs(
                abs(option.delta) - self.delta_target
            )

            score += max(
                0,
                self.delta_weight - float(distance * Decimal("200")),
            )

        if (
            option.bid is not None
            and option.ask is not None
            and option.ask > 0
        ):

            spread = (option.ask - option.bid) / option.ask

            score += max(
                0,
                self.spread_weight - float(spread * Decimal("100")),
            )

        if option.volume is not None:

            score += min(
                self.volume_weight,
                option.volume / self.volume_norm,
            )

        if option.bid is not None:

            score += min(
                self.premium_weight,
                float(option.bid),
            )

        return round(score, 2)