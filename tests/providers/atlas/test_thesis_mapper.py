from app.providers.atlas.dto import AtlasEntry
from app.providers.atlas.thesis_mapper import thesis_from_atlas_entry


def _entry(valoracion: str) -> AtlasEntry:
    return AtlasEntry(
        ticker="XYZ",
        nombre="XYZ Corp",
        valoracion=valoracion,
        resumen="Some summary.",
        fecha=None,
        zona_compra=None,
        entrada_max=None,
    )


def test_no_entry_at_all_is_not_approved():
    """
    ATLAS's own principle: first approve the company, then look for
    the best CSP. A ticker never analyzed should not be silently
    treated as approved.
    """
    thesis = thesis_from_atlas_entry(None)

    assert thesis.approved is False
    assert thesis.watchlist is False


def test_alcista_is_approved():
    thesis = thesis_from_atlas_entry(_entry("alcista"))

    assert thesis.approved is True
    assert thesis.watchlist is False


def test_posicion_is_approved():
    thesis = thesis_from_atlas_entry(_entry("posicion"))

    assert thesis.approved is True


def test_seguimiento_is_watchlist_not_approved():
    thesis = thesis_from_atlas_entry(_entry("seguimiento"))

    assert thesis.approved is False
    assert thesis.watchlist is True


def test_unknown_valoracion_defaults_to_not_approved_not_watchlist():
    """
    ATLAS's vocabulary may evolve independently of Aegis - an
    unrecognized value shouldn't raise or silently approve.
    """
    thesis = thesis_from_atlas_entry(_entry("algo_nuevo_no_previsto"))

    assert thesis.approved is False
    assert thesis.watchlist is False


def test_notes_come_from_resumen():
    thesis = thesis_from_atlas_entry(_entry("alcista"))

    assert thesis.notes == "Some summary."


def test_entrada_max_maps_to_buy_price():
    from decimal import Decimal

    entry = AtlasEntry(
        ticker="ACN",
        nombre="Accenture",
        valoracion="alcista",
        resumen=None,
        fecha=None,
        zona_compra="≤$160 · compra clara <$150",
        entrada_max=160.0,
    )

    thesis = thesis_from_atlas_entry(entry)

    assert thesis.buy_price == Decimal("160.0")
    assert thesis.zona_compra == "≤$160 · compra clara <$150"


def test_missing_entrada_max_leaves_buy_price_none():
    thesis = thesis_from_atlas_entry(_entry("alcista"))

    assert thesis.buy_price is None
    assert thesis.zona_compra is None
