from __future__ import annotations

from loguru import logger

from app.providers.atlas.client import AtlasClient
from app.providers.atlas.dto import AtlasEntry
from app.providers.atlas.mapper import AtlasMapper, UnparsableAtlasEntryError


class AtlasProvider:
    """
    Provides access to company analyses from the ATLAS research
    library (diegogh33/atlas-research).

    Filenames under analyses/ don't reliably match the ticker (e.g.
    "mc.pa.md" for ticker "MC.PA", "LOG.MC.md" for "LOG.MC",
    lowercase filenames like "hims.md" for ticker "HIMS") - so this
    builds an index keyed by the `ticker` field from each file's own
    frontmatter, rather than guessing a filename convention.

    The index is built once per AtlasProvider instance and cached in
    memory - a full analysis run may look up several tickers, and
    there's no need to re-list and re-fetch all files for each one.
    """

    def __init__(self, client: AtlasClient | None = None) -> None:

        self._client = client or AtlasClient()

        self._index: dict[str, AtlasEntry] | None = None

    async def _build_index(self) -> dict[str, AtlasEntry]:

        filenames = await self._client.list_analyses()

        index: dict[str, AtlasEntry] = {}

        for filename in filenames:

            content = await self._client.get_file_content(filename)

            try:
                entry = AtlasMapper.entry(content, source_filename=filename)
            except UnparsableAtlasEntryError as error:
                # One malformed analysis file shouldn't take down
                # lookups for every other ticker in the library.
                logger.warning(
                    "Skipping unparsable ATLAS entry: {error}",
                    error=error,
                )
                continue

            index[entry.ticker] = entry

        return index

    async def get_entry(self, ticker: str) -> AtlasEntry | None:
        """
        Returns the ATLAS entry for a ticker, or None if it hasn't
        been analyzed yet (not in the library at all).
        """

        if self._index is None:
            self._index = await self._build_index()

        return self._index.get(ticker.strip().upper())

    async def close(self) -> None:

        await self._client.close()
