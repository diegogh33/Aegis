from __future__ import annotations

from dataclasses import dataclass

from app.models.option_contract import OptionContract


@dataclass(frozen=True)
class RejectedContract:
    """
    An option contract that was excluded from the ranked results,
    together with why.

    `reason` is a short, stable machine-readable code (e.g.
    "NO_UNDERLYING_PRICE", or a Rule.id like "DELTA"/"DTE") so callers
    can group/count rejections without parsing free text. `detail` is
    the human-readable message for display.
    """

    option: OptionContract
    reason: str
    detail: str
