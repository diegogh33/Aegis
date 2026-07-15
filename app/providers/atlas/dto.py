from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class AtlasEntry:
    """
    A single company analysis from the ATLAS research library
    (diegogh33/atlas-research), parsed from an analysis file's YAML
    frontmatter.

    `valoracion` is kept as the raw string from ATLAS ("alcista",
    "seguimiento", "posicion", ...) rather than mapped to a fixed
    enum here - the mapping to InvestmentThesis.approved/watchlist
    lives in the mapper, so ATLAS can introduce new values without
    breaking parsing.
    """

    ticker: str
    nombre: str
    valoracion: str
    resumen: str | None
    fecha: date | None
    zona_compra: str | None
    entrada_max: float | None
