from __future__ import annotations

from pathlib import Path

import yaml


class Settings:
    """
    Loads the Aegis Constitution.
    """

    def __init__(
        self,
        path: str = "config/constitution.yaml",
    ) -> None:

        with Path(path).open(
            "r",
            encoding="utf-8",
        ) as file:

            self.data = yaml.safe_load(file)

    def get(
        self,
        *keys,
        default=None,
    ):

        value = self.data

        for key in keys:

            if not isinstance(value, dict):
                return default

            value = value.get(key)

            if value is None:
                return default

        return value