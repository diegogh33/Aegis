from __future__ import annotations

from datetime import date
from statistics import median

from app.engines.metrics_engine import MetricsEngine
from app.engines.option_score_engine import OptionScoreEngine
from app.iv_history.repository import IVHistoryRepository, IVSnapshot
from app.models.analysis_result import AnalysisResult
from app.models.company import Company
from app.models.investment_candidate import InvestmentCandidate
from app.models.rejected_contract import RejectedContract
from app.models.scored_option import ScoredOption
from app.providers.alphavantage.client import AlphaVantageUnavailableError
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
        iv_history_repository: IVHistoryRepository | None = None,
    ) -> None:

        self.alpha = alpha_provider
        self.ibkr = ibkr_provider
        self.atlas = atlas_provider or AtlasProvider()

        self.scanner = OptionScanner(ibkr_provider)

        self.scorer = OptionScoreEngine()

        if iv_history_repository is None:
            from app.config.settings import Settings

            iv_history_repository = IVHistoryRepository(
                Settings().iv_history_db_path
            )

        self.iv_history = iv_history_repository

        self.strategy = CashSecuredPutStrategy(
            iv_history_repository=self.iv_history
        )

    async def analyze(
        self,
        ticker: str,
        exchange: str = "SMART",
        currency: str = "USD",
    ) -> AnalysisResult:

        company_known = True
        company_error: str | None = None

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
            company_error = (
                f"Alpha Vantage doesn't recognize '{ticker}' - no "
                f"fundamental data available. For non-US tickers this "
                f"often means a market suffix is needed (e.g. 'ITX.MC')."
            )
        except AlphaVantageUnavailableError as error:
            # The API itself is unavailable right now (most commonly
            # a rate limit, e.g. the free tier's 25 requests/day cap)
            # rather than the ticker being unrecognized. Same
            # fallback as above: fundamental data is unavailable, but
            # options analysis doesn't depend on it.
            company = Company.unknown(ticker)
            company_known = False
            company_error = f"Alpha Vantage is unavailable: {error}"

        # The investment thesis only depends on the ticker, not on
        # any individual contract, so it's looked up once per
        # analysis rather than once per contract.
        atlas_entry = await self.atlas.get_entry(ticker)
        thesis = thesis_from_atlas_entry(atlas_entry)

        contracts = await self.scanner.scan_puts(
            ticker, exchange=exchange, currency=currency
        )

        # Se guarda un snapshot diario de IV para el histórico de
        # IVRankRule. Se usa la mediana entre los contratos con IV
        # disponible (más robusto que depender de un único strike,
        # que puede no tener Greeks calculables - ver limitaciones de
        # datos de IBKR ya documentadas). (ticker, día) es la clave
        # natural: analizar el mismo ticker varias veces el mismo día
        # sobreescribe el snapshot de hoy, no lo duplica.
        available_ivs = [
            contract.implied_volatility
            for contract in contracts
            if contract.implied_volatility is not None
        ]

        if available_ivs:

            self.iv_history.record(
                IVSnapshot(
                    ticker=ticker,
                    day=date.today(),
                    implied_volatility=median(available_ivs),
                )
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
            company_error=company_error,
        )