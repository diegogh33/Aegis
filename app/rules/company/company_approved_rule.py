from __future__ import annotations

from decimal import Decimal

from app.core.result import RuleResult
from app.core.rule_status import RuleStatus
from app.rules.base import Rule


class CompanyApprovedRule(Rule):
    """
    Checks whether the company belongs to the approved investment
    universe (ATLAS).

    Non-blocking by design: a company that hasn't been analyzed yet,
    or is only on the watchlist ("seguimiento"), still surfaces as a
    candidate - just with a reduced score and a visible WARNING/FAIL
    status - instead of being hidden from the results entirely. The
    previous blocking behavior meant tickers with no ATLAS entry at
    all (e.g. never analyzed) produced an empty results table with no
    way to see what the market itself looked like, which wasn't
    useful when the point was to explore a new idea.

    Approval is driven by InvestmentThesis.approved/watchlist, which
    reflect ATLAS's own verdict for the company.
    """

    id = "COMPANY_APPROVED"

    name = "Company approved"

    blocker = False

    def evaluate(self, candidate):

        thesis = candidate.thesis

        if thesis.approved:
            return RuleResult(
                rule_id=self.id,
                status=RuleStatus.PASS,
                score=Decimal("10"),
                message="Company belongs to the approved investment universe.",
            )

        if thesis.watchlist:
            return RuleResult(
                rule_id=self.id,
                status=RuleStatus.WARNING,
                score=Decimal("4"),
                message=(
                    "Company is on the ATLAS watchlist (seguimiento) - "
                    "not yet an approved investment."
                ),
            )

        return RuleResult(
            rule_id=self.id,
            status=RuleStatus.FAIL,
            score=Decimal("0"),
            message=(
                "Company has not been analyzed in ATLAS yet - "
                "no investment thesis on record."
            ),
        )
