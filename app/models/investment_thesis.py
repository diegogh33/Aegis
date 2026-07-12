from __future__ import annotations

from enum import Enum

from pydantic import BaseModel

from app.core.types import Money, Score


class Conviction(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class InvestmentThesis(BaseModel):
    """
    Represents our investment opinion about a company.

    Unlike Company, this model is subjective and may evolve over time.
    """

    fair_value: Money | None = None

    buy_price: Money | None = None

    quality_score: Score | None = None

    approved: bool = False

    watchlist: bool = False

    conviction: Conviction = Conviction.MEDIUM

    notes: str | None = None