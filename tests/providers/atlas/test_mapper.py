import pytest

from app.providers.atlas.mapper import AtlasMapper, UnparsableAtlasEntryError

REAL_ACN_CONTENT = """---
ticker: ACN
nombre: Accenture plc
tipo: accion
valoracion: alcista
resumen: "Accenture es la mayor firma de servicios profesionales."
tags: [technology, it-consulting, dividend-growth]
fecha: 2026-07-06
zona_compra: "≤$160 · acumulación óptima $110–$150"
entrada_max: 160
---

# Accenture plc (ACN) — Tesis de Inversión Institucional
"""

REAL_ARE_CONTENT = """---
nombre: Alexandria Real Estate Equities
tipo: opciones
valoracion: posicion
ticker: "ARE"
---

# Alexandria Real Estate
"""


def test_parses_real_acn_frontmatter():
    entry = AtlasMapper.entry(REAL_ACN_CONTENT, source_filename="ACN.md")

    assert entry.ticker == "ACN"
    assert entry.nombre == "Accenture plc"
    assert entry.valoracion == "alcista"
    assert entry.entrada_max == 160.0
    assert entry.fecha is not None
    assert entry.fecha.isoformat() == "2026-07-06"


def test_parses_quoted_ticker_and_field_order_does_not_matter():
    """
    Regression guard: real ATLAS files don't always list fields in
    the same order, and some values (like ticker for ARE) are quoted
    in the YAML while others aren't. Both should parse the same way.
    """
    entry = AtlasMapper.entry(REAL_ARE_CONTENT, source_filename="are.md")

    assert entry.ticker == "ARE"
    assert entry.valoracion == "posicion"


def test_ticker_is_normalized_to_uppercase():
    content = """---
ticker: mc.pa
nombre: LVMH
valoracion: seguimiento
---
"""
    entry = AtlasMapper.entry(content, source_filename="mc.pa.md")

    assert entry.ticker == "MC.PA"


def test_missing_frontmatter_raises():
    with pytest.raises(UnparsableAtlasEntryError):
        AtlasMapper.entry(
            "# Just a heading, no frontmatter", source_filename="broken.md"
        )


def test_missing_required_field_raises():
    content = """---
nombre: Some Company
valoracion: alcista
---
"""
    # Missing `ticker`.
    with pytest.raises(UnparsableAtlasEntryError):
        AtlasMapper.entry(content, source_filename="broken.md")


def test_missing_optional_fields_default_to_none():
    content = """---
ticker: XYZ
nombre: XYZ Corp
valoracion: seguimiento
---
"""
    entry = AtlasMapper.entry(content, source_filename="xyz.md")

    assert entry.resumen is None
    assert entry.fecha is None
    assert entry.zona_compra is None
    assert entry.entrada_max is None
