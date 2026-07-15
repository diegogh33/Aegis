import pytest

from app.providers.alphavantage.mapper import (
    AlphaVantageMapper,
    UnknownCompanyError,
)


def test_empty_response_raises_unknown_company_error():
    """
    Regression test: Alpha Vantage returns an empty JSON object ({})
    for unrecognized tickers (e.g. "ITX" without the ".MC" suffix),
    rather than an explicit error field. The mapper used to access
    data["Symbol"] directly and blow up with a bare KeyError, which
    crashed the whole CLI run - including the options analysis, which
    doesn't depend on this data at all.
    """
    with pytest.raises(UnknownCompanyError):
        AlphaVantageMapper.company({})


def test_response_missing_name_raises_unknown_company_error():
    with pytest.raises(UnknownCompanyError):
        AlphaVantageMapper.company({"Symbol": "AAPL"})


def test_valid_response_maps_correctly():
    data = {
        "Symbol": "AAPL",
        "Name": "Apple Inc",
        "Currency": "USD",
        "Exchange": "NASDAQ",
        "Sector": "TECHNOLOGY",
        "Industry": "CONSUMER ELECTRONICS",
        "Country": "USA",
        "Description": "Apple designs and sells consumer electronics.",
        "MarketCapitalization": "3000000000000",
        "PERatio": "30.5",
        "EPS": "6.5",
    }

    company = AlphaVantageMapper.company(data)

    assert company.symbol == "AAPL"
    assert company.name == "Apple Inc"
    assert company.market_cap == 3_000_000_000_000
    assert company.pe_ratio is not None
    assert company.eps is not None


def test_missing_optional_fields_default_safely():
    data = {
        "Symbol": "AAPL",
        "Name": "Apple Inc",
    }

    company = AlphaVantageMapper.company(data)

    assert company.symbol == "AAPL"
    assert company.currency == "N/A"
    assert company.market_cap == 0
    assert company.pe_ratio is None
