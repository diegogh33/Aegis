from __future__ import annotations

from app.engines.option_score_engine import OptionScoreEngine
from app.models.analysis_result import AnalysisResult
from app.models.scored_option import ScoredOption
from app.providers.alphavantage.provider import AlphaVantageProvider
from app.providers.ibkr.provider import IBKRProvider
from app.services.option_scanner import OptionScanner


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

    async def analyze(
        self,
        ticker: str,
    ) -> AnalysisResult:

        company = await self.alpha.get_company(ticker)

        contracts = await self.scanner.scan_puts(ticker)

        ranked = sorted(
            [
                ScoredOption(
                    option=contract,
                    score=self.scorer.evaluate(contract),
                )
                for contract in contracts
            ],
            key=lambda item: item.score.total,
            reverse=True,
        )

        return AnalysisResult(
            company=company,
            contracts=ranked,
        )