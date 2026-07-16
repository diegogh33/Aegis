from __future__ import annotations

from decimal import Decimal

from app.models.investment_thesis import InvestmentThesis
from app.providers.atlas.dto import AtlasEntry

# ATLAS's `valoracion` values observed in diegogh33/atlas-research
# (not an exhaustive contract - new values default to "not approved,
# not watchlist" below rather than raising, since ATLAS's vocabulary
# may evolve independently of Aegis).
_APPROVED_VALORACIONES = {"alcista", "posicion"}
_WATCHLIST_VALORACIONES = {"seguimiento"}


def thesis_from_atlas_entry(entry: AtlasEntry | None) -> InvestmentThesis:
    """
    Builds an InvestmentThesis from an ATLAS entry.

    A ticker with no ATLAS entry at all (never analyzed) is treated
    as not approved - ATLAS's own principle is "first approve the
    company, then look for the best CSP", so the absence of an
    analysis is itself a signal, not a gap to silently default around.

    "alcista" (bullish verdict, e.g. INVERTIR-equivalent) and
    "posicion" (already holding a position there, e.g. ARE) both map
    to approved=True. "seguimiento" (watching, not yet convinced -
    ATLAS's own SEGUIMIENTO verdict) maps to approved=False,
    watchlist=True: the Constitution should be more cautious about
    companies still under observation than ones with a confirmed
    investment thesis.

    entrada_max maps to buy_price - used by BelowBuyZoneRule (long
    term strategy) to check whether a strike sits below Diego's own
    "worth entering" ceiling for the stock.
    """

    if entry is None:
        return InvestmentThesis(approved=False)

    return InvestmentThesis(
        approved=entry.valoracion in _APPROVED_VALORACIONES,
        watchlist=entry.valoracion in _WATCHLIST_VALORACIONES,
        notes=entry.resumen,
        buy_price=(
            Decimal(str(entry.entrada_max))
            if entry.entrada_max is not None
            else None
        ),
    )
