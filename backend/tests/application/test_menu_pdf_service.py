import re
import shutil
import subprocess
from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.application.menu_pdf_service import (
    MenuCatalogEmptyError,
    MenuPdfService,
    _CategoryTable,
    _ProductBlock,
    _SectionHeading,
    _category_section_table,
    _category_table,
    _categories_for_menu,
    _title_case_if_uppercase,
    _offer_description,
    _format_money,
    _format_presentation,
    _category_offer_presentations,
    _common_presentations,
    _paragraph_styles,
    _register_menu_fonts,
    _without_hidden_categories,
)
from app.application.public_catalog_service import build_public_catalog


def _category(category_id: int, name: str, active: bool = True):
    return SimpleNamespace(id=category_id, nombre=name, activo=active)


def _product(product_id: int, name: str, category_id: int, active: bool = True, prices=None):
    return SimpleNamespace(
        id=product_id,
        nombre=name,
        categoria_id=category_id,
        activo=active,
        precios=prices or [],
    )


@pytest.mark.asyncio
async def test_generates_pdf_from_sellable_database_products():
    category = _category(1, "Pizzas")
    product = _product(
        10,
        "Muzzarella",
        1,
        prices=[
            SimpleNamespace(cantidad=Decimal("1"), precio=Decimal("12000")),
            SimpleNamespace(cantidad=Decimal("0.5"), precio=Decimal("6500")),
        ],
    )
    offer = SimpleNamespace(
        id=20,
        nombre="Combo",
        descripcion="Para compartir",
        precio=Decimal("15000"),
        activo=True,
        productos=[
            SimpleNamespace(
                cantidad=Decimal("1"),
                categoria_id=None,
                productos=[product],
            )
        ],
    )
    uow = SimpleNamespace(
        product_category_repo=SimpleNamespace(
            list_by_active=AsyncMock(return_value=[category])
        ),
        product_repo=SimpleNamespace(list=AsyncMock(return_value=[product])),
        offer_repo=SimpleNamespace(list=AsyncMock(return_value=[offer])),
    )

    pdf = await MenuPdfService().generate(uow)

    assert pdf.startswith(b"%PDF-")
    assert b"%%EOF" in pdf[-100:]
    uow.product_category_repo.list_by_active.assert_awaited_once_with(activo=True)
    uow.product_repo.list.assert_awaited_once_with(active=True)
    uow.offer_repo.list.assert_awaited_once_with(active=True)


@pytest.mark.asyncio
async def test_generates_paginated_menu_with_category_offers_and_spanish_names():
    category = _category(1, "EMPANADAS")
    products = [
        _product(
            product_id,
            "ÑANDÚ CON QUESO ÜBER" if product_id == 1 else f"Empanada de prueba {product_id}",
            1,
            prices=[
                SimpleNamespace(cantidad=Decimal("1"), precio=Decimal("1000"))
            ],
        )
        for product_id in range(1, 81)
    ]
    offers = [
        SimpleNamespace(
            id=offer_id,
            nombre=name,
            descripcion=None,
            precio=price,
            activo=True,
            productos=[
                SimpleNamespace(
                    cantidad=quantity,
                    categoria_id=1,
                    productos=[],
                )
            ],
        )
        for offer_id, name, quantity, price in (
            (30, "Media docena", Decimal("6"), Decimal("6000")),
            (31, "Docena", Decimal("12"), Decimal("11000")),
            (32, "Dos docenas", Decimal("24"), Decimal("20000")),
        )
    ]
    uow = SimpleNamespace(
        product_category_repo=SimpleNamespace(
            list_by_active=AsyncMock(return_value=[category])
        ),
        product_repo=SimpleNamespace(list=AsyncMock(return_value=products)),
        offer_repo=SimpleNamespace(list=AsyncMock(return_value=offers)),
    )

    pdf = await MenuPdfService().generate(uow)
    page_count = len(re.findall(rb"/Type\s*/Page\b", pdf))

    assert pdf.startswith(b"%PDF-")
    assert page_count >= 2
    assert page_count <= 3


@pytest.mark.asyncio
async def test_menu_pdf_requires_at_least_one_sellable_product():
    uow = SimpleNamespace(
        product_category_repo=SimpleNamespace(
            list_by_active=AsyncMock(return_value=[_category(1, "Pizzas")])
        ),
        product_repo=SimpleNamespace(list=AsyncMock(return_value=[])),
        offer_repo=SimpleNamespace(list=AsyncMock(return_value=[])),
    )

    with pytest.raises(MenuCatalogEmptyError, match="No hay productos activos"):
        await MenuPdfService().generate(uow)


def test_menu_pdf_formats_prices_and_presentations_for_argentine_spanish():
    assert _format_money(Decimal("12500.5")) == "$ 12.500,50"
    assert _format_money(Decimal("12000")) == "$ 12.000"
    assert _format_presentation(Decimal("0.5")) == "Porción"
    assert _format_presentation(Decimal("0.125")) == "Porción"
    assert _format_presentation(Decimal("1")) == "Unidad"
    assert _format_presentation(Decimal("6")) == "Media docena"
    assert _format_presentation(Decimal("12")) == "Docena"


def test_category_offer_presentations_include_only_single_category_offers():
    offers = [
        SimpleNamespace(
            nombre="Docena",
            precio=Decimal("12000"),
            items=[
                SimpleNamespace(
                    cantidad=Decimal("12"),
                    categoria_id=3,
                    producto_ids=[],
                )
            ],
        ),
        SimpleNamespace(
            nombre="Dos docenas",
            precio=Decimal("22000"),
            items=[
                SimpleNamespace(
                    cantidad=Decimal("24"),
                    categoria_id=3,
                    producto_ids=[],
                )
            ],
        ),
        SimpleNamespace(
            nombre="Media docena",
            precio=Decimal("6500"),
            items=[
                SimpleNamespace(
                    cantidad=Decimal("6"),
                    categoria_id=3,
                    producto_ids=[],
                )
            ],
        ),
        SimpleNamespace(
            nombre="Promo combinada",
            precio=Decimal("15000"),
            items=[
                SimpleNamespace(
                    cantidad=Decimal("24"),
                    categoria_id=3,
                    producto_ids=[],
                ),
                SimpleNamespace(
                    cantidad=Decimal("1"),
                    categoria_id=None,
                    producto_ids=[10],
                ),
            ],
        ),
        SimpleNamespace(
            nombre="Otra categoría",
            precio=Decimal("9000"),
            items=[
                SimpleNamespace(
                    cantidad=Decimal("6"),
                    categoria_id=4,
                    producto_ids=[],
                )
            ],
        ),
    ]
    table = _category_offer_presentations(
        offers,
        category_id=3,
        width=300,
        styles=_paragraph_styles("Helvetica-Bold", "Helvetica", "Helvetica-Bold"),
    )

    assert table is not None
    assert [cell.text for cell in table._cellvalues[0]] == [
        "Media docena",
        "Docena",
        "2 docenas",
    ]
    assert [cell.text for cell in table._cellvalues[1]] == [
        "$ 1.083 c/u",
        "$ 1.000 c/u",
        "$ 917 c/u",
    ]
    assert table._argW == [100, 100, 100]

    test_price_offer = SimpleNamespace(
        nombre="Media docena",
        precio=Decimal("1000"),
        items=[
            SimpleNamespace(
                cantidad=Decimal("6"),
                categoria_id=3,
                producto_ids=[],
            )
        ],
    )
    rounded_table = _category_offer_presentations(
        [test_price_offer],
        category_id=3,
        width=300,
        styles=_paragraph_styles("Helvetica-Bold", "Helvetica", "Helvetica-Bold"),
    )
    assert rounded_table is not None
    assert rounded_table._cellvalues[1][0].text == "$ 167 c/u"


def test_title_cases_only_all_uppercase_names_and_preserves_acronyms():
    assert _title_case_if_uppercase(
        "PIZZA JAMÓN Y MORRONES CON QUESO"
    ) == "Pizza Jamón y Morrones con Queso"
    assert _title_case_if_uppercase(
        "EMPANADAS DE CARNE (VEG) Y BBQ"
    ) == "Empanadas de Carne (VEG) y BBQ"
    assert _title_case_if_uppercase(
        "Pizza Jamón y Morrones"
    ) == "Pizza Jamón y Morrones"
    assert _title_case_if_uppercase("PIZZA CON ANANÁ Y ÜN") == (
        "Pizza con Ananá y ÜN"
    )


def test_menu_fonts_support_spanish_characters():
    _, _, sans, sans_bold = _register_menu_fonts()
    from reportlab.pdfbase import pdfmetrics

    sample = "Ñandú, Jamón, Ü, ¿Sí? ¡Sí!"
    assert pdfmetrics.stringWidth(sample, sans, 10) > 0
    assert pdfmetrics.stringWidth(sample, sans_bold, 10) > 0
    for font_name in (sans, sans_bold):
        face = pdfmetrics.getFont(font_name).face
        assert all(ord(character) in face.charToGlyph for character in sample)


def test_long_product_name_wraps_before_price_columns():
    _, _, sans, sans_bold = _register_menu_fonts()
    product = SimpleNamespace(
        nombre="EMPANADAS DE JAMÓN Y MORRONES CON QUESO AZUL",
        precios=[
            SimpleNamespace(cantidad=Decimal("0.5"), precio=Decimal("6500")),
            SimpleNamespace(cantidad=Decimal("1"), precio=Decimal("12000")),
        ],
    )
    block = _ProductBlock(
        product,
        width=260,
        styles=_paragraph_styles("MenuPlayfair-Bold", sans, sans_bold),
        category_quantities={Decimal("0.5"), Decimal("1")},
        common_presentations=None,
    )

    block.wrap(260, 500)

    assert len(block._name_lines) > 1
    assert block._name_width + 118 <= block.width
    assert "Empanadas" in block._name_lines[0]


def test_category_split_repeats_continuation_heading_and_keeps_three_items():
    serif_bold, _, sans, sans_bold = _register_menu_fonts()
    styles = _paragraph_styles(serif_bold, sans, sans_bold)
    products = [
        SimpleNamespace(
            id=product_id,
            nombre=f"Empanada de prueba {product_id}",
            precios=[SimpleNamespace(cantidad=Decimal("1"), precio=Decimal("1000"))],
        )
        for product_id in range(1, 21)
    ]
    quantities, common = _common_presentations(products)
    rows, widths, _ = _category_table(
        products,
        500,
        styles,
        quantities,
        common,
    )
    section = _category_section_table(
        _SectionHeading("Empanadas", 500, serif_bold),
        None,
        None,
        rows,
        widths,
        common,
        "LEFT",
    )

    section.wrap(500, 700)
    parts = section.split(500, 250)

    assert len(parts) > 1
    assert isinstance(parts[1], _CategoryTable)
    first_heading = parts[0]._cellvalues[0][0][0]
    assert isinstance(first_heading, _SectionHeading)
    assert first_heading.title == "EMPANADAS"
    assert not first_heading.continuation

    continuation_heading = parts[1]._cellvalues[0][0][0]
    assert isinstance(continuation_heading, _SectionHeading)
    assert continuation_heading.title == "EMPANADAS (CONT.)"
    assert continuation_heading.continuation

    def product_count(table):
        return sum(
            isinstance(flowable, _ProductBlock)
            for row in table._cellvalues
            for cell in row
            for flowable in (
                cell if isinstance(cell, (tuple, list)) else (cell,)
            )
        )

    assert product_count(parts[0]) >= 3
    assert sum(product_count(part) for part in parts) == len(products)


def test_category_reorder_is_opt_in_and_keeps_pizzas_before_short_categories(
    monkeypatch,
):
    catalog = SimpleNamespace(
        categorias=[
            SimpleNamespace(id=1, nombre="Pizzas"),
            SimpleNamespace(id=2, nombre="Empanadas"),
            SimpleNamespace(id=3, nombre="Bebidas"),
        ],
        productos=[
            SimpleNamespace(categoria_id=2) for _ in range(8)
        ] + [SimpleNamespace(categoria_id=3)],
    )

    monkeypatch.delenv("MENU_PDF_REORDER_TO_FILL", raising=False)
    assert [category.id for category in _categories_for_menu(catalog)] == [1, 2, 3]

    monkeypatch.setenv("MENU_PDF_REORDER_TO_FILL", "true")
    assert [category.id for category in _categories_for_menu(catalog)] == [1, 3, 2]


@pytest.mark.asyncio
async def test_generates_pdf_with_variable_presentations_and_natural_promo_details():
    categories = [
        _category(1, "Faina"),
        _category(2, "Pizzas"),
        _category(3, "Empanadas"),
    ]
    faina = _product(
        10,
        "Faina",
        1,
        prices=[
            SimpleNamespace(cantidad=Decimal("0.125"), precio=Decimal("1500")),
            SimpleNamespace(cantidad=Decimal("1"), precio=Decimal("9000")),
        ],
    )
    faina_porcion_unidad = _product(
        11,
        "Faina para compartir",
        1,
        prices=[
            SimpleNamespace(cantidad=Decimal("1"), precio=Decimal("9500")),
        ],
    )
    napolitana = _product(
        20,
        "Napolitana",
        2,
        prices=[SimpleNamespace(cantidad=Decimal("1"), precio=Decimal("18000"))],
    )
    calabresa = _product(
        21,
        "Calabresa",
        2,
        prices=[SimpleNamespace(cantidad=Decimal("1"), precio=Decimal("19000"))],
    )
    empanada = _product(
        30,
        "Carne",
        3,
        prices=[SimpleNamespace(cantidad=Decimal("1"), precio=Decimal("1200"))],
    )
    products = [faina, faina_porcion_unidad, napolitana, calabresa, empanada]
    offers = [
        SimpleNamespace(
            id=40,
            nombre="Pizza a elección",
            descripcion=None,
            precio=Decimal("18000"),
            activo=True,
            productos=[
                SimpleNamespace(
                    cantidad=Decimal("1"),
                    categoria_id=None,
                    productos=[napolitana, calabresa],
                )
            ],
        ),
        SimpleNamespace(
            id=41,
            nombre="Promo faina",
            descripcion=None,
            precio=Decimal("1500"),
            activo=True,
            productos=[
                SimpleNamespace(
                    cantidad=Decimal("0.125"),
                    categoria_id=None,
                    productos=[faina],
                )
            ],
        ),
        SimpleNamespace(
            id=42,
            nombre="Docenas de empanadas",
            descripcion=None,
            precio=Decimal("24000"),
            activo=True,
            productos=[
                SimpleNamespace(
                    cantidad=Decimal("24"),
                    categoria_id=3,
                    productos=[],
                )
            ],
        ),
    ]
    uow = SimpleNamespace(
        product_category_repo=SimpleNamespace(
            list_by_active=AsyncMock(return_value=categories)
        ),
        product_repo=SimpleNamespace(list=AsyncMock(return_value=products)),
        offer_repo=SimpleNamespace(list=AsyncMock(return_value=offers)),
    )

    pdf = await MenuPdfService().generate(uow)
    catalog = build_public_catalog(
        categories,
        products,
        offers,
        image_urls={},
        published_at=datetime.now(timezone.utc),
    )
    descriptions = {
        offer.nombre: _offer_description(offer, catalog)
        for offer in catalog.ofertas
    }

    assert pdf.startswith(b"%PDF-")
    assert b"%%EOF" in pdf[-100:]
    assert descriptions["Pizza a elección"] == (
        "Elegí 1: Napolitana / Calabresa"
    )
    assert descriptions["Promo faina"] == "1 porción de Faina"
    assert descriptions["Docenas de empanadas"] == (
        "2 docenas de empanadas a elección"
    )


@pytest.mark.asyncio
async def test_editorial_layout_handles_mixed_presentations_and_stays_within_three_pages(
    monkeypatch,
):
    monkeypatch.setenv("MENU_PDF_HIDDEN_CATEGORIES", " Extras , CÁFES ")
    categories = [
        _category(1, "Pizzas"),
        _category(2, "Pizzas y Faina"),
        _category(3, "Papas Fritas"),
        _category(4, "Tartas"),
        _category(5, "Extras"),
        _category(6, "Cafés"),
    ]

    def product(product_id, name, category_id, quantities):
        return _product(
            product_id,
            name,
            category_id,
            prices=[
                SimpleNamespace(cantidad=quantity, precio=price)
                for quantity, price in quantities
            ],
        )

    unit_price = [(Decimal("1"), Decimal("18000"))]
    products = [
        product(1, "Muzzarella", 1, unit_price),
        product(2, "Napolitana", 1, unit_price),
        product(3, "Calabresa", 1, unit_price),
        product(4, "Cuatro quesos con cebolla caramelizada", 1, unit_price),
        product(5, "Muzzarella", 2, unit_price),
        product(6, "Napolitana", 2, unit_price),
        product(7, "Calabresa", 2, unit_price),
        product(
            8,
            "Faina para compartir",
            2,
            [
                (Decimal("0.125"), Decimal("1500")),
                (Decimal("1"), Decimal("9000")),
            ],
        ),
    ]
    shared_prices = [
        (Decimal("0.5"), Decimal("4000")),
        (Decimal("1"), Decimal("7500")),
    ]
    products.extend(
        product(product_id, f"Papas fritas {product_id}", 3, shared_prices)
        for product_id in range(9, 13)
    )
    tart_prices = [
        (Decimal("0.25"), Decimal("6000")),
        (Decimal("1"), Decimal("22000")),
    ]
    products.extend(
        [
            product(13, "Tarta de verdura", 4, tart_prices),
            product(14, "Tarta de jamón y queso", 4, tart_prices),
            product(15, "Café de prueba", 6, unit_price),
            product(16, "Extra de prueba", 5, unit_price),
            product(
                17,
                "Faina disponible solo por porción",
                1,
                [(Decimal("0.125"), Decimal("1800"))],
            ),
        ]
    )
    offers = [
        SimpleNamespace(
            id=30,
            nombre="Pizza a elección",
            descripcion=None,
            precio=Decimal("18000"),
            activo=True,
            productos=[
                SimpleNamespace(
                    cantidad=Decimal("1"),
                    categoria_id=None,
                    productos=[products[0], products[1]],
                )
            ],
        ),
        SimpleNamespace(
            id=31,
            nombre="PROMO PROMO 1",
            descripcion="Faina para compartir",
            precio=Decimal("1500"),
            activo=True,
            productos=[
                SimpleNamespace(
                    cantidad=Decimal("0.125"),
                    categoria_id=None,
                    productos=[products[7]],
                )
            ],
        ),
        SimpleNamespace(
            id=32,
            nombre="Promo familiar muy especial para compartir",
            descripcion="Una promoción con un nombre largo para probar el ajuste",
            precio=Decimal("32000"),
            activo=True,
            productos=[
                SimpleNamespace(
                    cantidad=Decimal("24"),
                    categoria_id=3,
                    productos=[],
                )
            ],
        ),
        SimpleNamespace(
            id=33,
            nombre="Promo de Extra de prueba",
            descripcion="Extra de prueba",
            precio=Decimal("1000"),
            activo=True,
            productos=[
                SimpleNamespace(
                    cantidad=Decimal("1"),
                    categoria_id=5,
                    productos=[],
                )
            ],
        ),
    ]
    uow = SimpleNamespace(
        product_category_repo=SimpleNamespace(
            list_by_active=AsyncMock(return_value=categories)
        ),
        product_repo=SimpleNamespace(list=AsyncMock(return_value=products)),
        offer_repo=SimpleNamespace(list=AsyncMock(return_value=offers)),
    )

    pdf = await MenuPdfService().generate(uow)
    catalog = build_public_catalog(
        categories,
        products,
        offers,
        image_urls={},
        published_at=datetime.now(timezone.utc),
    )
    visible_catalog = _without_hidden_categories(catalog)
    page_count = len(re.findall(rb"/Type\s*/Page\b", pdf))

    assert pdf.startswith(b"%PDF-")
    assert 1 <= page_count <= 3
    assert {category.nombre for category in visible_catalog.categorias} == {
        "Pizzas",
        "Pizzas y Faina",
        "Papas Fritas",
        "Tartas",
    }
    assert "Café de prueba" not in {
        product.nombre for product in visible_catalog.productos
    }
    assert "Extra de prueba" not in {
        product.nombre for product in visible_catalog.productos
    }
    assert "Promo de Extra de prueba" not in {
        offer.nombre for offer in visible_catalog.ofertas
    }
    pdftotext = shutil.which("pdftotext")
    if pdftotext:
        extracted = subprocess.run(
            [pdftotext, "-", "-"],
            input=pdf,
            check=True,
            capture_output=True,
        ).stdout.decode("utf-8", errors="replace")
        assert "Extras" not in extracted
        assert "Extra de prueba" not in extracted
        assert "Café de prueba" not in extracted
        assert "Promo de Extra de prueba" not in extracted
        assert (
            "Pizzas mitad y mitad: se abona el precio de la variedad más cara."
            in extracted
        )
        assert extracted.count("Pizzas mitad y mitad:") == 1
