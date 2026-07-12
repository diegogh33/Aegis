from dataclasses import dataclass


@dataclass(slots=True)
class AlphaVantageOptionDTO:
    """
    Raw option contract returned by Alpha Vantage.
    """

    symbol: str

    expiration: str

    strike: str

    option_type: str

    bid: str

    ask: str

    delta: float | None

    gamma: float | None

    theta: float | None

    vega: float | None

    implied_volatility: float | None

    open_interest: int | None

    volume: int | None