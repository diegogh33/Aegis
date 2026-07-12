from app.rules.no_earnings import NoUpcomingEarningsRule
from app.strategies.base import Strategy


class CashSecuredPutStrategy(Strategy):
    """
    Strategy for evaluating Cash Secured PUT opportunities.
    """

    def __init__(self):
        super().__init__(
            rules=[
                NoUpcomingEarningsRule(),
            ]
        )