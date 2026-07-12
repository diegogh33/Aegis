from pathlib import Path

import yaml


class Settings:
    """
    Loads the Aegis Constitution.
    """

    def __init__(
        self,
        path: str = "config/constitution.yaml",
    ):

        self.path = Path(path)

        with self.path.open(
            "r",
            encoding="utf-8",
        ) as file:

            self.data = yaml.safe_load(file)