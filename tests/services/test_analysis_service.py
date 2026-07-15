from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from app.providers.alphavantage.mapper import UnknownCompanyError
from app.services.analysis_service import AnalysisService
from tests.conftest import build_company, build_option


@pytest.mark.asyncio
async def test_analyze_scores_and_ranks_eligible_contracts():
    company = build_company(next_earnings=None)

    # Both inside DeltaRule's pass/warning range, so both survive the
    # Constitution, but score differently - closer to target delta
    # scores higher.
    good_option = build_option(delta=-0.20)
    warning_option = build_option(delta=-0.28)

    alpha = AsyncMock()
    alpha.get_company.return_value = company

    ibkr = AsyncMock()

    service = AnalysisService(alpha_provider=alpha, ibkr_provider=ibkr)
    service.scanner.scan_puts = AsyncMock(
        return_value=[good_option, warning_option]
    )

    result = await service.analyze("SAP")

    assert result.company == company
    assert len(result.contracts) == 2
    assert result.contracts[0].score.total >= result.contracts[1].score.total


@pytest.mark.asyncio
async def test_analyze_rejects_contracts_with_delta_out_of_range():
    company = build_company(next_earnings=None)

    good_option = build_option(delta=-0.20)
    bad_delta_option = build_option(delta=-0.45)

    alpha = AsyncMock()
    alpha.get_company.return_value = company

    ibkr = AsyncMock()

    service = AnalysisService(alpha_provider=alpha, ibkr_provider=ibkr)
    service.scanner.scan_puts = AsyncMock(
        return_value=[good_option, bad_delta_option]
    )

    result = await service.analyze("SAP")

    # bad_delta_option (-0.45) is outside DeltaRule's full range and
    # gets rejected by the Constitution before ever reaching scoring.
    assert len(result.contracts) == 1
    assert result.contracts[0].option.delta == Decimal("-0.20")

    assert len(result.rejected) == 1
    assert result.rejected[0].reason == "DELTA"
    assert result.rejected[0].option.delta == Decimal("-0.45")


@pytest.mark.asyncio
async def test_analyze_rejects_contracts_with_upcoming_earnings():
    from datetime import date, timedelta

    company = build_company(next_earnings=date.today() + timedelta(days=3))

    option = build_option(delta=-0.20)

    alpha = AsyncMock()
    alpha.get_company.return_value = company

    ibkr = AsyncMock()

    service = AnalysisService(alpha_provider=alpha, ibkr_provider=ibkr)
    service.scanner.scan_puts = AsyncMock(return_value=[option])

    result = await service.analyze("SAP")

    # Earnings in 3 days is inside the default minimum_days window,
    # so the only candidate should be filtered out by the Constitution.
    assert result.contracts == []
    assert len(result.rejected) == 1
    assert result.rejected[0].reason == "NO_EARNINGS"


@pytest.mark.asyncio
async def test_analyze_tracks_contracts_without_underlying_price_as_rejected():
    from dataclasses import replace

    company = build_company(next_earnings=None)

    option = replace(build_option(delta=-0.20), underlying_price=None)

    alpha = AsyncMock()
    alpha.get_company.return_value = company

    ibkr = AsyncMock()

    service = AnalysisService(alpha_provider=alpha, ibkr_provider=ibkr)
    service.scanner.scan_puts = AsyncMock(return_value=[option])

    result = await service.analyze("SAP")

    assert result.contracts == []
    assert len(result.rejected) == 1
    assert result.rejected[0].reason == "NO_UNDERLYING_PRICE"


@pytest.mark.asyncio
async def test_analyze_continues_with_options_when_company_is_unknown():
    """
    Regression test: Alpha Vantage not recognizing a ticker (common
    for non-US symbols without a market suffix, e.g. "ITX") used to
    crash the whole run with a bare KeyError before this reached
    AnalysisService at all. Options analysis is entirely independent
    (IBKR-only), so it should still complete with a placeholder
    Company and company_known=False, instead of failing everything.
    """
    option = build_option(delta=-0.20)

    alpha = AsyncMock()
    alpha.get_company.side_effect = UnknownCompanyError("not found")

    ibkr = AsyncMock()

    service = AnalysisService(alpha_provider=alpha, ibkr_provider=ibkr)
    service.scanner.scan_puts = AsyncMock(return_value=[option])

    result = await service.analyze("ITX", currency="EUR")

    assert result.company_known is False
    assert result.company.symbol == "ITX"
    assert len(result.contracts) == 1
