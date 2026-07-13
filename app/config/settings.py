from __future__ import annotations

import os
from pathlib import Path

import yaml
from dotenv import load_dotenv


load_dotenv()


class Settings:
    """
    Central application configuration.
    """

    def __init__(
        self,
        constitution_path: str = "config/constitution.yaml",
    ) -> None:

        # ------------------------------------------------------------------
        # Constitution
        # ------------------------------------------------------------------

        self.constitution_path = Path(constitution_path)

        with self.constitution_path.open(
            "r",
            encoding="utf-8",
        ) as file:

            self.constitution = yaml.safe_load(file)

        # ------------------------------------------------------------------
        # Alpha Vantage
        # ------------------------------------------------------------------

        self.alpha_vantage_api_key = os.getenv(
            "ALPHA_VANTAGE_API_KEY",
            "",
        )

        # ------------------------------------------------------------------
        # Interactive Brokers
        # ------------------------------------------------------------------

        self.ibkr_host = os.getenv(
            "IBKR_HOST",
            "127.0.0.1",
        )

        self.ibkr_port = int(
            os.getenv(
                "IBKR_PORT",
                "7496",
            )
        )

        self.ibkr_client_id = int(
            os.getenv(
                "IBKR_CLIENT_ID",
                "1",
            )
        )


settings = Settings()