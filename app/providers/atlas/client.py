from __future__ import annotations

import base64

import httpx

from app.config.settings import settings


class AtlasClient:
    """
    Minimal GitHub API client for reading files from the ATLAS
    research repository (diegogh33/atlas-research by default,
    configurable via ATLAS_REPO).

    Responsible only for communicating with the GitHub API. No
    business logic (frontmatter parsing, ticker matching) lives here.
    """

    BASE_URL = "https://api.github.com"

    def __init__(self) -> None:

        headers = {"Accept": "application/vnd.github+json"}

        if settings.github_token:
            headers["Authorization"] = f"token {settings.github_token}"

        self._client = httpx.AsyncClient(
            timeout=30,
            headers=headers,
        )

        self._repo = settings.atlas_repo

    async def list_analyses(self) -> list[str]:
        """
        Returns the filenames (e.g. "ACN.md") under the repo's
        analyses/ directory.
        """

        response = await self._client.get(
            f"{self.BASE_URL}/repos/{self._repo}/contents/analyses",
        )

        response.raise_for_status()

        data = response.json()

        if not isinstance(data, list):
            raise RuntimeError(
                f"Unexpected response listing ATLAS analyses: {data}"
            )

        return [
            item["name"]
            for item in data
            if item.get("type") == "file"
            and item.get("name", "").endswith(".md")
        ]

    async def get_file_content(self, filename: str) -> str:
        """
        Returns the raw text content of a single file under
        analyses/.
        """

        response = await self._client.get(
            f"{self.BASE_URL}/repos/{self._repo}/contents/analyses/"
            f"{filename}",
        )

        response.raise_for_status()

        data = response.json()

        return base64.b64decode(data["content"]).decode("utf-8")

    async def close(self) -> None:

        await self._client.aclose()
