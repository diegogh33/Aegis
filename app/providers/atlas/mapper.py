from __future__ import annotations

from datetime import date, datetime

import yaml

from app.providers.atlas.dto import AtlasEntry


class UnparsableAtlasEntryError(Exception):
    """
    Raised when an ATLAS analysis file doesn't have a well-formed
    YAML frontmatter block, or is missing required fields (ticker,
    nombre, valoracion).
    """


class AtlasMapper:
    """
    Parses ATLAS analysis files (Markdown with a YAML frontmatter
    block delimited by --- lines) into AtlasEntry objects.
    """

    @staticmethod
    def entry(content: str, source_filename: str) -> AtlasEntry:

        parts = content.split("---", 2)

        if len(parts) < 3:
            raise UnparsableAtlasEntryError(
                f"{source_filename}: no YAML frontmatter block found "
                "(expected content delimited by '---' lines)."
            )

        try:
            data = yaml.safe_load(parts[1])
        except yaml.YAMLError as error:
            raise UnparsableAtlasEntryError(
                f"{source_filename}: invalid YAML frontmatter: {error}"
            ) from error

        if not isinstance(data, dict):
            raise UnparsableAtlasEntryError(
                f"{source_filename}: frontmatter did not parse into "
                "a mapping."
            )

        missing = [
            key
            for key in ("ticker", "nombre", "valoracion")
            if key not in data
        ]

        if missing:
            raise UnparsableAtlasEntryError(
                f"{source_filename}: missing required frontmatter "
                f"field(s): {', '.join(missing)}."
            )

        fecha = data.get("fecha")

        parsed_fecha: date | None = None

        if isinstance(fecha, date):
            parsed_fecha = fecha
        elif isinstance(fecha, str) and fecha:
            parsed_fecha = datetime.strptime(fecha, "%Y-%m-%d").date()

        entrada_max = data.get("entrada_max")

        return AtlasEntry(
            ticker=str(data["ticker"]).strip().upper(),
            nombre=str(data["nombre"]).strip(),
            valoracion=str(data["valoracion"]).strip().lower(),
            resumen=data.get("resumen"),
            fecha=parsed_fecha,
            zona_compra=(
                str(data["zona_compra"])
                if data.get("zona_compra") is not None
                else None
            ),
            entrada_max=(
                float(entrada_max) if entrada_max is not None else None
            ),
        )
