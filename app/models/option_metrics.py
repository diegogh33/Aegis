from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class OptionMetrics:
    """
    Derived financial metrics for an option.
    """

    premium: Decimal
    capital_required: Decimal

    return_on_capital: Decimal
    annualized_return: Decimal

    break_even: Decimal
    downside_protection: Decimal

    days_to_expiration: int