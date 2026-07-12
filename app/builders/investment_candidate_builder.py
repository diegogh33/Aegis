from app.models.company import Company
from app.models.investment_candidate import InvestmentCandidate
from app.models.investment_thesis import InvestmentThesis
from app.models.option_contract import OptionContract


class InvestmentCandidateBuilder:
    """
    Builds an InvestmentCandidate from the available data sources.
    """

    def build(
        self,
        company: Company,
        thesis: InvestmentThesis,
        option: OptionContract | None = None,
    ) -> InvestmentCandidate:

        return InvestmentCandidate(
            company=company,
            thesis=thesis,
            option=option,
        )