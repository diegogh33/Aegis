from __future__ import annotations

from decimal import Decimal

from app.models.company import Company


class AlphaVantageMapper:
    """
    Converts Alpha Vantage JSON responses into domain models.
    """

    @staticmethod
    def company(data: dict) -> Company:
        def decimal_or_none(value: str | None) -> Decimal | None:
            if not value or value == "None":
                return None

            return Decimal(value)

        return Company(
            symbol=data["Symbol"],
            name=data["Name"],
            currency=data["Currency"],
            exchange=data["Exchange"],
            sector=data["Sector"],
            industry=data["Industry"],
            country=data["Country"],
            market_cap=int(data["MarketCapitalization"]),
            pe_ratio=decimal_or_none(data.get("PERatio")),
            eps=decimal_or_none(data.get("EPS")),
            dividend_yield=decimal_or_none(data.get("DividendYield")),
            description=data["Description"],
        )