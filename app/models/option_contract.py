from datetime import date

from pydantic import BaseModel


class OptionContract(BaseModel):

    ticker: str

    expiration: date

    strike: float

    option_type: str

    bid: float

    ask: float

    last: float | None = None

    delta: float | None = None

    gamma: float | None = None

    theta: float | None = None

    vega: float | None = None

    implied_volatility: float | None = None

    open_interest: int | None = None

    volume: int | None = None