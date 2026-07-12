from __future__ import annotations

from abc import ABC, abstractmethod

from app.models.company import Company
from app.models.option_contract import OptionContract


class MarketDataProvider(ABC):
    """
    Abstract interface for every market data provider.
    """

    @abstractmethod
    async def get_company(
        self,
        ticker: str,
    ) -> Company:
        raise NotImplementedError

    @abstractmethod
    async def get_option_chain(
        self,
        ticker: str,
    ) -> list[OptionContract]:
        raise NotImplementedError