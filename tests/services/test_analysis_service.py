from unittest.mock import AsyncMock

import pytest

from app.services.analysis_service import AnalysisService
from tests.conftest import build_company, build_option


@pytest.mark.asyncio
async def test_analyze_scores_and_ranks_eligible_contracts():
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

    assert result.company == company
    # Both survive the Constitution (no earnings data, thesis hardcoded
    # as approved), but they should be scored and ranked - the option
    # closer to the target delta should score higher.
    assert len(result.contracts) == 2
    assert result.contracts[0].score.total >= result.contracts[1].score.total


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


@pytest.mark.asyncio
async def test_analyze_skips_contracts_without_underlying_price():
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
