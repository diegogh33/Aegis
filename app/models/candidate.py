from pydantic import BaseModel

from app.models.company import Company
from app.models.option_contract import OptionContract


class Candidate(BaseModel):

    company: Company

    contract: OptionContract