from __future__ import annotations

from abc import ABC, abstractmethod

from app.models.option_contract import OptionContract


class Selector(ABC):
    """
    Base class for every selector.
    """

    @abstractmethod
    def select(
        self,
        contracts: list[OptionContract],
    ) -> list[OptionContract]:
        raise NotImplementedError