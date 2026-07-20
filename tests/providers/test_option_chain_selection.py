from ib_async.objects import OptionChain

from app.providers.ibkr.provider import _select_option_chain


def _chain(exchange: str, trading_class: str, expirations: list[str]) -> OptionChain:
    return OptionChain(
        exchange=exchange,
        underlyingConId=1,
        tradingClass=trading_class,
        multiplier="100",
        expirations=expirations,
        strikes=[100.0, 105.0],
    )


def test_prefers_smart_chain_matching_symbol_exactly():
    """
    Regression test for the real MSFT case: reqSecDefOptParamsAsync
    returned two SMART chains - the standard "MSFT" class (many
    expirations) and a secondary "2MSFT" class (a single expiration,
    a handful of strikes) - and the code was picking whichever came
    first, sometimes the secondary one. tradingClass matching the
    symbol should always win.
    """
    standard = _chain(
        "SMART", "MSFT", ["20260724", "20260821", "20261016", "20270115"]
    )
    secondary = _chain("SMART", "2MSFT", ["20260728"])

    # Order shouldn't matter - try both orderings.
    assert _select_option_chain([secondary, standard], "MSFT") is standard
    assert _select_option_chain([standard, secondary], "MSFT") is standard


def test_falls_back_to_first_smart_chain_when_no_exact_match():
    only_secondary = _chain("SMART", "2MSFT", ["20260728"])
    non_smart = _chain("BOX", "MSFT", ["20260724"])

    result = _select_option_chain([non_smart, only_secondary], "MSFT")

    assert result is only_secondary


def test_falls_back_to_first_chain_when_no_smart_chain_at_all():
    only_non_smart = _chain("BOX", "MSFT", ["20260724"])

    result = _select_option_chain([only_non_smart], "MSFT")

    assert result is only_non_smart


def test_single_smart_chain_is_used_regardless_of_trading_class():
    """
    Most underlyings only have one SMART chain - the common case
    should be unaffected by the exact-match preference.
    """
    only_chain = _chain("SMART", "MSFT", ["20260724"])

    result = _select_option_chain([only_chain], "MSFT")

    assert result is only_chain
