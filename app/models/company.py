from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field

from app.core.types import Money


class Company(BaseModel):
    """
    Represents objective information about a company.

    This model must never contain subjective investment decisions
    or strategy-specific information.
    """

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------

    ticker: str = Field(..., description="Company ticker symbol")
    name: str | None = None

    # ------------------------------------------------------------------
    # Classification
    # ------------------------------------------------------------------

    sector: str | None = None
    industry: str | None = None

    # ------------------------------------------------------------------
    # Market data
    # ------------------------------------------------------------------

    currency: str = "USD"

    current_price: Money | None = None

    market_cap: Money | None = None

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    next_earnings: date | None = None