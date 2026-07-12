from datetime import date
from decimal import Decimal

from app.models.option_contract import OptionContract
from app.providers.alphavantage.dto import AlphaVantageOptionDTO


class AlphaVantageMapper:
    """
    Maps Alpha Vantage DTOs into domain models.
    """

    @staticmethod
    def to_option_contract(
        dto: AlphaVantageOptionDTO,
    ) -> OptionContract:

        return OptionContract(
            ticker=dto.symbol,
            expiration=date.fromisoformat(dto.expiration),
            strike=Decimal(dto.strike),
            option_type=dto.option_type,
            bid=Decimal(dto.bid),
            ask=Decimal(dto.ask),
            delta=dto.delta,
            gamma=dto.gamma,
            theta=dto.theta,
            vega=dto.vega,
            implied_volatility=dto.implied_volatility,
            open_interest=dto.open_interest,
            volume=dto.volume,
        )