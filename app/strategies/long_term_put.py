from app.iv_history.repository import IVHistoryRepository
from app.rules.below_buy_zone import BelowBuyZoneRule
from app.rules.company.company_approved_rule import CompanyApprovedRule
from app.rules.delta import DeltaRule
from app.rules.dte import DTERule
from app.rules.ivr import IVRankRule
from app.rules.liquidity import LiquidityRule
from app.rules.no_earnings import NoUpcomingEarningsRule
from app.rules.spread import SpreadRule
from app.strategies.base import Strategy


class LongTermPutStrategy(Strategy):
    """
    Opportunistic strategy for selling long-dated PUTs on high-
    conviction price dips - distinct from the recurring
    CashSecuredPutStrategy, activated manually via --long-term.

    Example that motivated this: ACN dropped to ~$135 in a way Diego
    judged as overreaction; sold a $120 strike PUT expiring in
    November (~130+ DTE) for an $8.80 premium - either the stock
    doesn't fall further and the premium is kept, or it does and
    shares are bought at $120, a price already considered attractive.

    Reuses DTERule/DeltaRule/IVRankRule (all parametrized by
    constitution.yaml section rather than duplicated) with
    long_term_put's own wider DTE window (90-365 days) and lower/more
    conservative delta range (-0.10/-0.30). IVRankRule is
    informational only here (can_block=False) - a 90-365 day horizon
    means today's IV Rank is far less decisive than for the ~30-45
    day recurring strategy. New BelowBuyZoneRule checks the strike
    against Diego's own ATLAS buy-zone ceiling when known.
    """

    def __init__(
        self,
        iv_history_repository: IVHistoryRepository | None = None,
    ):
        super().__init__(
            rules=[
                CompanyApprovedRule(),
                NoUpcomingEarningsRule(),
                DTERule(config_section="long_term_put"),
                DeltaRule(config_section="long_term_put"),
                LiquidityRule(config_section="long_term_put"),
                SpreadRule(config_section="long_term_put"),
                BelowBuyZoneRule(),
                IVRankRule(
                    repository=iv_history_repository,
                    can_block=False,
                ),
            ]
        )
