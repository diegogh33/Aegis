from app.rules.company.company_approved_rule import CompanyApprovedRule
from app.rules.delta import DeltaRule
from app.rules.dte import DTERule
from app.rules.no_earnings import NoUpcomingEarningsRule
from app.strategies.base import Strategy


class CashSecuredPutStrategy(Strategy):
    """
    Strategy for evaluating Cash Secured PUT opportunities.
    """

    def __init__(self):
        super().__init__(
            rules=[
                CompanyApprovedRule(),
                NoUpcomingEarningsRule(),
                DTERule(),
                DeltaRule(),
            ]
        )