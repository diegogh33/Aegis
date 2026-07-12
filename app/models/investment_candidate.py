from pydantic import BaseModel

from app.models.company import Company
from app.models.investment_thesis import InvestmentThesis
from app.models.option_contract import OptionContract


class InvestmentCandidate(BaseModel):
    """
    Aggregate root for evaluating an investment opportunity.

    Every business rule receives a single InvestmentCandidate instance.
    """

    company: Company
    thesis: InvestmentThesis
    option: OptionContract | None = None