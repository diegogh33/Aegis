from abc import ABC
from abc import abstractmethod

from app.models.company import Company


class MarketDataProvider(ABC):

    @abstractmethod
    async def get_company(self, ticker: str) -> Company:
        ...