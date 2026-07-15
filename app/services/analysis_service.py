from __future__ import annotations

from app.engines.metrics_engine import MetricsEngine
from app.engines.option_score_engine import OptionScoreEngine
from app.models.analysis_result import AnalysisResult
from app.models.company import Company
from app.models.investment_candidate import InvestmentCandidate
from app.models.rejected_contract import RejectedContract
from app.models.scored_option import ScoredOption
from app.providers.alphavantage.mapper import UnknownCompanyError
from app.providers.alphavantage.provider import AlphaVantageProvider
from app.providers.atlas.provider import AtlasProvider
from app.providers.atlas.thesis_mapper import thesis_from_atlas_entry
from app.providers.ibkr.provider import IBKRProvider
from app.services.option_scanner import OptionScanner
from app.strategies.cash_secured_put import CashSecuredPutStrategy


class AnalysisService:

    def __init__(
        self,
        alpha_provider: AlphaVantageProvider,
        ibkr_provider: IBKRProvider,
        atlas_provider: AtlasProvider | None = None,
    ) -> None:

        self.alpha = alpha_provider
        self.ibkr = ibkr_provider
        self.atlas = atlas_provider or AtlasProvider()

        self.scanner = OptionScanner(ibkr_provider)

        self.scorer = OptionScoreEngine()

        self.strategy = CashSecuredPutStrategy()

    async def analyze(
        self,
        ticker: str,
        exchange: str = "SMART",
        currency: str = "USD",
    ) -> AnalysisResult:

        company_known = True

        try:
            company = await self.alpha.get_company(ticker)
        except UnknownCompanyError:
            # Alpha Vantage doesn't recognize this ticker (common for
            # non-US symbols without the right market suffix, e.g.
            # "ITX" instead of "ITX.MC"). This only affects fundamental
            # data display - the options analysis itself is entirely
            # independent (IBKR), so it still makes sense to continue
            # rather than fail the whole run.
            company = Company.unknown(ticker)
            company_known = False

        # The investment thesis only depends on the ticker, not on
        # any individual contract, so it's looked up once per
        # analysis rather than once per contract.
        atlas_entry = await self.atlas.get_entry(ticker)
        thesis = thesis_from_atlas_entry(atlas_entry)

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
            thesis=thesis,
            contracts=ranked,
            rejected=rejected,
            company_known=company_known,
        )