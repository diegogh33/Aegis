from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    """
    Central application settings.

    Environment variables are loaded only once from the .env file.
    The rest of the application should access configuration through
    this object instead of calling os.getenv().
    """

    def __init__(self) -> None:
        self.alphavantage_api_key = self._get_required(
            "ALPHAVANTAGE_API_KEY"
        )

    @staticmethod
    def _get_required(name: str) -> str:
        value = os.getenv(name)

        if not value:
            raise RuntimeError(
                f"Missing required environment variable: {name}"
            )

        return value


settings = Settings()