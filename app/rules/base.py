from abc import ABC
from abc import abstractmethod

from app.core.result import RuleResult


class Rule(ABC):

    id: str

    name: str

    weight: float = 1.0

    blocker: bool = False

    @abstractmethod
    def evaluate(self, candidate) -> RuleResult:
        ...