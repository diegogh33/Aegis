from __future__ import annotations

from app.cli.errors import _extract_ticker, _is_connection_error


def test_is_connection_error_detects_refused():
    assert _is_connection_error(ConnectionRefusedError("Connection refused"))


def test_is_connection_error_detects_timeout():
    assert _is_connection_error(TimeoutError("timed out"))


def test_is_connection_error_false_for_generic():
    assert not _is_connection_error(ValueError("something else"))


def test_extract_ticker_from_ibkr_message():
    msg = "Unable to qualify contract for NESN"
    assert _extract_ticker(msg) == "NESN"


def test_extract_ticker_returns_none_when_not_found():
    msg = "Something went wrong"
    assert _extract_ticker(msg) is None


def test_extract_ticker_handles_dotted_symbol():
    msg = "No option chain found for MC.PA"
    assert _extract_ticker(msg) == "MC.PA"
