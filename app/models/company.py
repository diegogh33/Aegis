from pydantic import BaseModel, Field


class Company(BaseModel):
    ticker: str = Field(..., description="Ticker de la empresa")
    name: str | None = None

    sector: str | None = None
    industry: str | None = None

    currency: str | None = None

    market_cap: float | None = None

    intrinsic_value: float | None = None

    watchlist: bool = False

    quality_score: float | None = None