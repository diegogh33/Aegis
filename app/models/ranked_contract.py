from pydantic import BaseModel

from app.models.option_contract import OptionContract


class RankedContract(BaseModel):
    """
    Represents an evaluated option contract.
    """

    contract: OptionContract

    score: float

    reasons: list[str]