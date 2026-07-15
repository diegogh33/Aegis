from unittest.mock import AsyncMock

import pytest

from app.providers.atlas.provider import AtlasProvider

ACN_CONTENT = """---
ticker: ACN
nombre: Accenture plc
valoracion: alcista
---
"""

ARE_CONTENT = """---
ticker: "ARE"
nombre: Alexandria Real Estate Equities
valoracion: posicion
---
"""

BROKEN_CONTENT = "# No frontmatter here at all"


@pytest.mark.asyncio
async def test_finds_entry_by_ticker_regardless_of_filename():
    """
    Real ATLAS filenames don't reliably match the ticker in the
    frontmatter (e.g. "are.md" for ticker "ARE", "mc.pa.md" for
    "MC.PA") - the index must be built from the frontmatter's own
    `ticker` field, not guessed from the filename.
    """
    client = AsyncMock()
    client.list_analyses.return_value = ["ACN.md", "are.md"]
    client.get_file_content.side_effect = lambda filename: {
        "ACN.md": ACN_CONTENT,
        "are.md": ARE_CONTENT,
    }[filename]

    provider = AtlasProvider(client=client)

    entry = await provider.get_entry("ARE")

    assert entry is not None
    assert entry.nombre == "Alexandria Real Estate Equities"


@pytest.mark.asyncio
async def test_ticker_lookup_is_case_insensitive():
    client = AsyncMock()
    client.list_analyses.return_value = ["ACN.md"]
    client.get_file_content.return_value = ACN_CONTENT

    provider = AtlasProvider(client=client)

    entry = await provider.get_entry("acn")

    assert entry is not None
    assert entry.ticker == "ACN"


@pytest.mark.asyncio
async def test_unknown_ticker_returns_none():
    client = AsyncMock()
    client.list_analyses.return_value = ["ACN.md"]
    client.get_file_content.return_value = ACN_CONTENT

    provider = AtlasProvider(client=client)

    entry = await provider.get_entry("NOTINATLAS")

    assert entry is None


@pytest.mark.asyncio
async def test_index_is_built_only_once_across_multiple_lookups():
    """
    A single analysis run may look up several tickers - list_analyses
    and get_file_content shouldn't be called again for each one.
    """
    client = AsyncMock()
    client.list_analyses.return_value = ["ACN.md"]
    client.get_file_content.return_value = ACN_CONTENT

    provider = AtlasProvider(client=client)

    await provider.get_entry("ACN")
    await provider.get_entry("ACN")
    await provider.get_entry("SOMETHING_ELSE")

    client.list_analyses.assert_awaited_once()
    client.get_file_content.assert_awaited_once()


@pytest.mark.asyncio
async def test_one_broken_entry_does_not_break_the_whole_index():
    """
    A single malformed analysis file (missing frontmatter, bad YAML)
    shouldn't prevent lookups for every other ticker in the library.
    """
    client = AsyncMock()
    client.list_analyses.return_value = ["ACN.md", "broken.md"]
    client.get_file_content.side_effect = lambda filename: {
        "ACN.md": ACN_CONTENT,
        "broken.md": BROKEN_CONTENT,
    }[filename]

    provider = AtlasProvider(client=client)

    entry = await provider.get_entry("ACN")

    assert entry is not None
    assert entry.ticker == "ACN"
