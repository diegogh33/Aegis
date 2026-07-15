from __future__ import annotations

from app.engines.metrics_engine import MetricsEngine
from app.engines.option_score_engine import OptionScoreEngine
from app.models.analysis_result import AnalysisResult
from app.models.investment_candidate import InvestmentCandidate
from app.models.investment_thesis import InvestmentThesis
from app.models.rejected_contract import RejectedContract
from app.models.scored_option import ScoredOption
from app.providers.alphavantage.provider import AlphaVantageProvider
from app.providers.ibkr.provider import IBKRProvider
from app.services.option_scanner import OptionScanner
from app.strategies.cash_secured_put import CashSecuredPutStrategy


class AnalysisService:

    def __init__(
        self,
        alpha_provider: AlphaVantageProvider,
        ibkr_provider: IBKRProvider,
    ) -> None:

        self.alpha = alpha_provider
        self.ibkr = ibkr_provider

        self.scanner = OptionScanner(ibkr_provider)

        self.scorer = OptionScoreEngine()

        self.strategy = CashSecuredPutStrategy()

    async def analyze(
        self,
        ticker: str,
        exchange: str = "SMART",
        currency: str = "USD",
    ) -> AnalysisResult:

        company = await self.alpha.get_company(ticker)

        contracts = await self.scanner.scan_puts(
            ticker, exchange=exchange, currency=currency
        )

        ranked: list[ScoredOption] = []
        rejected: list[RejectedContract] = []

        for contract in contracts:

            if contract.underlying_price is None:
                rejected.append(
                    RejectedContract(
                        option=contract,
                        reason="NO_UNDERLYING_PRICE",
                        detail=(
                            "No underlying price available (from the "
                            "option itself or the stock fallback)."
                        ),
                    )
                )
                continue

            # NOTE: InvestmentThesis.approved is hardcoded to True for now.
            # There is no data source yet that populates a real investment
            # thesis (e.g. from the ATLAS research library) for a given
            # ticker, so CompanyApprovedRule would reject every candidate
            # if this defaulted to False. Once a real thesis source exists,
            # this should be replaced with an actual lookup.
            thesis = InvestmentThesis(approved=True)

            candidate = InvestmentCandidate(
                company=company,
                thesis=thesis,
                option=contract,
            )

            evaluation = self.strategy.evaluate(candidate)

            if not evaluation.passed:

                blocker = evaluation.blockers[0]

                rejected.append(
                    RejectedContract(
                        option=contract,
                        reason=blocker.rule_id,
                        detail=blocker.message,
                    )
                )
                continue

            metrics = MetricsEngine.calculate(
                option=contract,
                underlying_price=contract.underlying_price,
            )

            score = self.scorer.evaluate(
                option=contract,
                metrics=metrics,
            )

            ranked.append(
                ScoredOption(
                    option=contract,
                    metrics=metrics,
                    score=score,
                    evaluation=evaluation,
                )
            )

        ranked.sort(
            key=lambda item: item.score.total,
            reverse=True,
        )

        return AnalysisResult(
            company=company,
            contracts=ranked,
            rejected=rejected,
        )