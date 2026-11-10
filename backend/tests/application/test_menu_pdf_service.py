import re
import shutil
import subprocess
from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import Spacer

import app.application.menu_pdf_service as menu_pdf_service
from app.application.menu_pdf_service import (
    MenuCatalogEmptyError,
    MenuPdfService,
    _CategoryTable,
    _PromoEntry,
    _PresentationHeader,
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
    _draw_leader_dots,
    _paragraph_styles,
    _register_menu_fonts,
    _promo_rows,
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


def test_menu_pdf_keeps_persisted_offer_order():
    category = _category(1, "Pizzas")
    product = _product(
        10,
        "Muzzarella",
        1,
        prices=[SimpleNamespace(cantidad=Decimal("1"), precio=Decimal("12000"))],
    )
    offers = [
        SimpleNamespace(
            id=offer_id,
            nombre=name,
            descripcion=None,
            precio=Decimal("10000"),
            activo=True,
            productos=[
                SimpleNamespace(
                    cantidad=Decimal("1"),
                    categoria_id=1,
                    productos=[],
                )
            ],
        )
        for offer_id, name in ((20, "Promo Z"), (21, "Promo A"), (22, "Promo M"))
    ]
    catalog = build_public_catalog(
        [category],
        [product],
        offers,
        image_urls={},
        published_at=datetime.now(timezone.utc),
    )
    serif_bold, _, sans, sans_bold = _register_menu_fonts()
    styles = _paragraph_styles(serif_bold, sans, sans_bold)

    rows = _promo_rows(catalog.ofertas, catalog, 500, styles)
    rendered_names = [
        cell.offer.nombre
        for row in rows
        for cell in (row._cellvalues[0][0], row._cellvalues[0][2])
        if isinstance(cell, _PromoEntry)
    ]

    assert rendered_names == ["Promo Z", "Promo A", "Promo M"]


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
async def test_current_menu_categories_fit_in_two_pages():
    category_names = [
        "Pizzas",
        "Faina",
        "Empanadas",
        "Super Milas",
        "Sandwich de Mila",
        "Papas Fritas",
        "Picada",
        "Tartas",
    ]
    categories = [
        _category(category_id, name)
        for category_id, name in enumerate(category_names, start=1)
    ]
    products = []
    product_ids_by_category = {}
    product_groups = [
        [
            "Muzzarella",
            "Napolitana",
            "Calabresa",
            "Roquefort",
            "Provolone",
            "Palmitos",
            "Ananá",
            "Anchoas",
            "Jamón y Morrones",
            "Espinaca S. Blanca",
            "Fugazza (S. Queso)",
            "Fugazetta",
            "Caprese",
            "Crudo y Rúcula",
            "Fiori",
        ],
        ["Faina"],
        [
            "Empanada de Carne",
            "Empanada de Pollo",
            "Empanada de Jamón y Queso",
            "Empanada de Humita",
            "Empanada Caprese",
            "Empanada de Verdura",
            "Empanada de Roquefort",
            "Empanada de Cebolla",
        ],
        [
            "Super Mila Napolitana",
            "Super Mila Americana",
            "Super Mila Fugazzetta",
            "Super Mila Caprese",
        ],
        ["Sandwich de Mila Completo", "Sandwich de Mila Simple"],
        ["Papas Fritas Completas", "Papas Fritas Simples"],
        ["Tequeños, Nuggets y Papas Fritas", "Tequeños"],
        ["Jamón, Queso y Huevo", "Jamón, Queso, Tomate y Huevo"],
    ]
    product_id = 1
    for category_id, names in enumerate(product_groups, start=1):
        category_product_ids = []
        for name in names:
            prices = [
                SimpleNamespace(cantidad=Decimal("1"), precio=Decimal("1000"))
            ]
            if category_id in {2, 6, 8}:
                prices.insert(
                    0,
                    SimpleNamespace(
                        cantidad=Decimal("0.5"),
                        precio=Decimal("500"),
                    ),
                )
            products.append(
                _product(product_id, name, category_id, prices=prices)
            )
            category_product_ids.append(product_id)
            product_id += 1
        product_ids_by_category[category_id] = category_product_ids

    def product_offer(
        offer_id,
        name,
        description,
        quantity,
        selected_product_ids,
    ):
        selected_products = [
            product
            for product in products
            if product.id in selected_product_ids
        ]
        return SimpleNamespace(
            id=offer_id,
            nombre=name,
            descripcion=description,
            precio=Decimal("10000"),
            activo=True,
            productos=[
                SimpleNamespace(
                    cantidad=quantity,
                    categoria_id=None,
                    productos=selected_products,
                )
            ],
        )

    offers = [
        product_offer(
            1,
            "Promo 1",
            "3 Muzzarella",
            Decimal("3"),
            [product_ids_by_category[1][0]],
        ),
        SimpleNamespace(
            id=2,
            nombre="Promo 2",
            descripcion="2 Docenas de Empanadas",
            precio=Decimal("18000"),
            activo=True,
            productos=[
                SimpleNamespace(
                    cantidad=Decimal("24"),
                    categoria_id=3,
                    productos=[],
                )
            ],
        ),
        product_offer(
            3,
            "Promo 3",
            "1 Especial + 1 Muzzarella + 6 Empanadas",
            Decimal("1"),
            [product_ids_by_category[1][1], product_ids_by_category[1][2]],
        ),
        SimpleNamespace(
            id=4,
            nombre="Promo 4",
            descripcion="1 Muzzarella + 6 Empanadas",
            precio=Decimal("12000"),
            activo=True,
            productos=[
                SimpleNamespace(
                    cantidad=Decimal("1"),
                    categoria_id=None,
                    productos=[products[0]],
                ),
                SimpleNamespace(
                    cantidad=Decimal("6"),
                    categoria_id=3,
                    productos=[],
                ),
            ],
        ),
        SimpleNamespace(
            id=5,
            nombre="Promo 5",
            descripcion="Media docena de empanadas",
            precio=Decimal("6000"),
            activo=True,
            productos=[
                SimpleNamespace(
                    cantidad=Decimal("6"),
                    categoria_id=3,
                    productos=[],
                )
            ],
        ),
        SimpleNamespace(
            id=6,
            nombre="Promo 6",
            descripcion="Una docena de empanadas",
            precio=Decimal("11000"),
            activo=True,
            productos=[
                SimpleNamespace(
                    cantidad=Decimal("12"),
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
    page_count = len(re.findall(rb"/Type\s*/Page\b", pdf))

    assert page_count == 2


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


def test_page_brand_uses_selected_png_logo(monkeypatch):
    draw_images = []
    decorative_lines = []

    class RecordingCanvas:
        def saveState(self):
            pass

        def restoreState(self):
            pass

        def setFillColor(self, _color):
            pass

        def rect(self, *_args, **_kwargs):
            pass

        def drawImage(self, *args, **kwargs):
            draw_images.append((args, kwargs))

        def setStrokeColor(self, _color):
            pass

        def setLineWidth(self, _width):
            pass

        def line(self, *_args):
            decorative_lines.append(_args)

    monkeypatch.setattr(
        menu_pdf_service,
        "ImageReader",
        lambda path: SimpleNamespace(getSize=lambda: (1600, 600), path=path),
    )
    draw_heart = Mock()
    monkeypatch.setattr(menu_pdf_service, "_draw_heart", draw_heart)

    menu_pdf_service._page_chrome(
        RecordingCanvas(),
        SimpleNamespace(page=1, pagesize=(600, 800)),
    )

    assert len(draw_images) == 1
    image, options = draw_images[0]
    assert image[0].path == str(menu_pdf_service._menu_logo_path())
    rendered_width = 1600 * (76 / 600)
    assert image[1] == pytest.approx((600 - rendered_width) / 2)
    assert image[2] == pytest.approx(800 - 3.05 * menu_pdf_service.cm + 3)
    assert options["width"] == pytest.approx(rendered_width)
    assert options["height"] == pytest.approx(76)
    assert options["mask"] == "auto"
    assert decorative_lines == []
    draw_heart.assert_not_called()


def test_only_selected_menu_logos_are_available():
    logo_dir = menu_pdf_service._menu_logo_path().parent
    filenames = {
        menu_pdf_service.MENU_LOGO_FILENAME,
        menu_pdf_service.MENU_FOOTER_LOGO_FILENAME,
    }
    assert {path.name for path in logo_dir.iterdir()} == filenames

    for filename in filenames:
        logo_path = logo_dir / filename
        assert logo_path.is_file()
        width, height = menu_pdf_service.ImageReader(str(logo_path)).getSize()
        assert width > 0
        assert height > 0


def test_footer_uses_small_pizza_logo_instead_of_italian_flag(monkeypatch):
    draw_images = []
    draw_rectangles = []
    draw_strings = []

    class RecordingCanvas:
        _pagesize = (600, 800)
        _footer_font = "footer"

        def saveState(self):
            pass

        def restoreState(self):
            pass

        def drawImage(self, *args, **kwargs):
            draw_images.append((args, kwargs))

        def rect(self, *args, **kwargs):
            draw_rectangles.append((args, kwargs))

        def setFillColor(self, _color):
            pass

        def setFont(self, *_args):
            pass

        def drawCentredString(self, *args):
            draw_strings.append(args)

    monkeypatch.setattr(
        menu_pdf_service,
        "ImageReader",
        lambda path: SimpleNamespace(getSize=lambda: (1600, 688), path=path),
    )

    menu_pdf_service._PageCountCanvas._draw_footer(RecordingCanvas(), 2, 4)

    assert len(draw_images) == 1
    image, options = draw_images[0]
    assert image[0].path == str(
        menu_pdf_service._menu_logo_path(
            menu_pdf_service.MENU_FOOTER_LOGO_FILENAME
        )
    )
    assert image[1] == pytest.approx(291)
    assert image[2] == pytest.approx(21 - (18 * 688 / 1600) / 2)
    assert options["width"] == 18
    assert options["height"] == pytest.approx(18 * 688 / 1600)
    assert options["mask"] == "auto"
    assert draw_rectangles == []
    assert draw_strings[0][2] == "Precios sujetos a confirmación por el local ·  Pág. 2 de 4"


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

    total_price_table = _category_offer_presentations(
        [test_price_offer],
        category_id=3,
        width=300,
        styles=_paragraph_styles("Helvetica-Bold", "Helvetica", "Helvetica-Bold"),
        show_total_price=True,
    )
    assert total_price_table is not None
    assert total_price_table._cellvalues[1][0].text == "$ 1.000"


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


def test_product_leader_dots_and_prices_align_with_last_name_line():
    _, _, sans, sans_bold = _register_menu_fonts()
    product = SimpleNamespace(
        nombre="EMPANADAS DE JAMÓN Y QUESO AZUL",
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

    class RecordingCanvas:
        def __init__(self):
            self.dots = []

        def saveState(self):
            pass

        def restoreState(self):
            pass

        def setFillColor(self, _color):
            pass

        def circle(self, x, y, radius, stroke=0, fill=1):
            self.dots.append((x, y, radius, stroke, fill))

    canvas = RecordingCanvas()
    name_draw = Mock()
    price_draws = [Mock(), Mock()]
    block.canv = canvas
    block._name_paragraph = SimpleNamespace(drawOn=name_draw)
    price_style = block.styles["product_price"]
    price_texts = ["$ 6.500", "$ 12.000"]
    block._price_cells = [
        (
            column,
            SimpleNamespace(
                drawOn=price_draw,
                getPlainText=lambda text=text: text,
                style=price_style,
            ),
            None,
        )
        for column, (price_draw, text) in enumerate(zip(price_draws, price_texts))
    ]

    block.draw()

    name_bottom = name_draw.call_args.args[2]
    assert all(price_draw.call_args.args[2] == name_bottom for price_draw in price_draws)
    assert canvas.dots
    expected_dot_y = (
        name_bottom
        + block.styles["product_name"].leading
        - block.styles["product_name"].fontSize
        + menu_pdf_service.LEADER_DOT_RADIUS
    )
    assert all(dot[1] == expected_dot_y and dot[2] == 1 for dot in canvas.dots)
    assert all(dot[3:] == (0, 1) for dot in canvas.dots)
    first_price_left = block.width - 59 - pdfmetrics.stringWidth(
        price_texts[0],
        price_style.fontName,
        price_style.fontSize,
    )
    assert first_price_left - canvas.dots[0][0] - 1 == pytest.approx(8)
    assert canvas.dots[-1][0] - 1 - (
        pdfmetrics.stringWidth(
            block._name_lines[-1],
            block.styles["product_name"].fontName,
            block.styles["product_name"].fontSize,
        )
    ) >= 8


def test_category_headings_and_decorative_lines_start_at_left_edge(monkeypatch):
    serif_bold, _, _, _ = _register_menu_fonts()
    heading = _SectionHeading("Promociones", 500, serif_bold)
    heading.wrap(500, 300)
    tracked_text_calls = []
    decorative_lines = []

    def record_tracked_text(
        _canvas,
        text,
        font_name,
        font_size,
        center_x,
        baseline,
        color,
        tracking,
        align_right=False,
    ):
        tracked_text_calls.append((text, center_x, tracking, align_right))

    class RecordingCanvas:
        def setStrokeColor(self, _color):
            pass

        def setLineWidth(self, _width):
            pass

        def line(self, *coordinates):
            decorative_lines.append(coordinates)

    monkeypatch.setattr(menu_pdf_service, "_tracked_text", record_tracked_text)
    heading.canv = RecordingCanvas()
    heading.draw()

    assert tracked_text_calls[0][1] == pytest.approx(
        pdfmetrics.stringWidth(
            tracked_text_calls[0][0],
            serif_bold,
            heading.font_size,
        )
        / 2
        + heading.tracking * (len(tracked_text_calls[0][0]) - 1) / 2
    )
    assert decorative_lines == [(0, 2, 500, 2)]


def test_one_column_category_spans_full_width_and_category_offer_headers_align_right():
    serif_bold, _, sans, sans_bold = _register_menu_fonts()
    styles = _paragraph_styles(serif_bold, sans, sans_bold)
    products = [
        _product(
            1,
            "Faina",
            1,
            prices=[SimpleNamespace(cantidad=Decimal("1"), precio=Decimal("1000"))],
        ),
        _product(
            2,
            "Faina con queso",
            1,
            prices=[SimpleNamespace(cantidad=Decimal("1"), precio=Decimal("1500"))],
        ),
    ]

    _, column_widths, _ = _category_table(
        products,
        500,
        styles,
        {Decimal("1")},
        None,
    )

    assert column_widths == [500]
    assert styles["pizza_half_and_half_note"].alignment == TA_LEFT

    offers = [
        SimpleNamespace(
            nombre=name,
            precio=Decimal("6000"),
            items=[
                SimpleNamespace(
                    cantidad=quantity,
                    categoria_id=1,
                    producto_ids=[],
                )
            ],
        )
        for name, quantity in (
            ("Media docena", Decimal("6")),
            ("Docena", Decimal("12")),
        )
    ]
    offer_table = menu_pdf_service._category_offer_presentations(
        offers,
        category_id=1,
        width=500,
        styles=styles,
    )

    assert offer_table is not None
    assert all(
        paragraph.style.alignment == TA_RIGHT
        for row in offer_table._cellvalues
        for paragraph in row
    )

    centered_offer_table = menu_pdf_service._category_offer_presentations(
        offers,
        category_id=1,
        width=500,
        styles=styles,
        center_columns=True,
    )
    assert centered_offer_table is not None
    assert all(
        paragraph.style.alignment == TA_CENTER
        for row in centered_offer_table._cellvalues
        for paragraph in row
    )


def test_common_presentation_header_has_space_before_first_product_row():
    serif_bold, _, sans, sans_bold = _register_menu_fonts()
    styles = _paragraph_styles(serif_bold, sans, sans_bold)
    products = [
        _product(
            product_id,
            f"Faina {product_id}",
            1,
            prices=[
                SimpleNamespace(cantidad=Decimal("0.5"), precio=Decimal("500")),
                SimpleNamespace(cantidad=Decimal("1"), precio=Decimal("1000")),
            ],
        )
        for product_id in range(1, 3)
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
        _SectionHeading("Faina", 500, serif_bold),
        None,
        None,
        rows,
        widths,
        common,
        "LEFT",
    )

    header_gap = section._cellvalues[3][0]
    assert isinstance(header_gap, Spacer)
    assert header_gap.height == 5


def test_mixed_portion_and_unit_products_share_category_headers(monkeypatch):
    serif_bold, _, sans, sans_bold = _register_menu_fonts()
    styles = _paragraph_styles(serif_bold, sans, sans_bold)
    products = [
        _product(
            1,
            "Faina con porción",
            1,
            prices=[
                SimpleNamespace(cantidad=Decimal("0.5"), precio=Decimal("500")),
                SimpleNamespace(cantidad=Decimal("1"), precio=Decimal("1000")),
            ],
        ),
        *[
            _product(
                product_id,
                f"Faina {product_id}",
                1,
                prices=[
                    SimpleNamespace(cantidad=Decimal("1"), precio=Decimal("1000"))
                ],
            )
            for product_id in range(2, 5)
        ],
    ]

    quantities, presentations = _common_presentations(products)
    rows, _, _ = _category_table(
        products,
        500,
        styles,
        quantities,
        presentations,
    )

    assert presentations == {Decimal("0.5"), Decimal("1")}
    assert isinstance(rows[0][0], _PresentationHeader)
    assert isinstance(rows[0][2], _PresentationHeader)
    assert rows[0][0].presentations == [Decimal("0.5"), Decimal("1")]
    assert rows[0][2].presentations == [Decimal("0.5"), Decimal("1")]

    header_labels = []
    header = rows[0][0]
    header.canv = SimpleNamespace(setFillColor=Mock())
    header.wrap(header.target_width, 500)
    monkeypatch.setattr(
        menu_pdf_service,
        "_tracked_text",
        lambda _canvas, text, *_args, **_kwargs: header_labels.append(text),
    )
    header.draw()
    assert header_labels == ["PORCIÓN", "UNIDAD"]

    product_blocks = [
        cell
        for row in rows[1:]
        for cell in (row[0], row[2])
        if isinstance(cell, _ProductBlock)
    ]
    for block in product_blocks:
        block.wrap(block.target_width, 500)
        assert all(label is None for _, _, label in block._price_cells)


def test_leader_dots_respect_minimum_clearance():
    class RecordingCanvas:
        def __init__(self):
            self.dots = []

        def saveState(self):
            pass

        def restoreState(self):
            pass

        def setFillColor(self, _color):
            pass

        def circle(self, x, y, radius, stroke=0, fill=1):
            self.dots.append((x, y, radius))

    canvas = RecordingCanvas()
    _draw_leader_dots(canvas, 20, 50, 7)
    assert canvas.dots
    assert canvas.dots[0][0] == 41
    assert canvas.dots[-1][0] >= 29
    assert all(dot[1:] == (8, 1) for dot in canvas.dots)


def test_leader_dots_are_omitted_when_promo_title_leaves_too_little_space():
    class RecordingCanvas:
        def __init__(self):
            self.dots = []

        def saveState(self):
            pass

        def restoreState(self):
            pass

        def setFillColor(self, _color):
            pass

        def circle(self, x, y, radius, stroke=0, fill=1):
            self.dots.append((x, y, radius))

    canvas = RecordingCanvas()
    _draw_leader_dots(canvas, 20, 28, 8)

    assert canvas.dots == []


def test_promo_leader_dots_and_price_align_with_last_title_line():
    serif_bold, _, sans, sans_bold = _register_menu_fonts()
    offer = SimpleNamespace(
        nombre="SUPER PICADA PARA COMPARTIR CON TODOS",
        descripcion="Esta descripcion no debe aparecer en el PDF",
        precio=Decimal("25000"),
        items=[],
    )
    entry = _PromoEntry(
        offer,
        SimpleNamespace(productos=[], categorias=[]),
        width=220,
        styles=_paragraph_styles(serif_bold, sans, sans_bold),
    )
    entry.wrap(220, 500)
    assert entry.title == offer.nombre
    assert " ".join(entry._title_lines) == offer.nombre
    assert len(entry._title_lines) > 1

    class RecordingCanvas:
        def __init__(self):
            self.dots = []

        def beginText(self, *_args):
            return SimpleNamespace(
                setFont=Mock(),
                setFillColor=Mock(),
                setCharSpace=Mock(),
                textLine=Mock(),
            )

        def drawText(self, _text):
            pass

        def saveState(self):
            pass

        def restoreState(self):
            pass

        def setFillColor(self, _color):
            pass

        def circle(self, x, y, radius, stroke=0, fill=1):
            self.dots.append((x, y, radius, stroke, fill))

    canvas = RecordingCanvas()
    title_draw = Mock()
    price_draw = Mock()
    entry.canv = canvas
    entry._title = SimpleNamespace(drawOn=title_draw)
    price_text = "$ 25.000"
    entry._price = SimpleNamespace(
        drawOn=price_draw,
        getPlainText=lambda: price_text,
        style=entry.styles["promo_price"],
    )

    entry.draw()

    title_baseline = title_draw.call_args.args[2]
    assert price_draw.call_args.args[2] == title_baseline
    assert price_draw.call_args.args[1] == (
        entry.width
        - menu_pdf_service.PROMO_PRICE_COLUMN_WIDTH
    )
    assert canvas.dots
    expected_dot_y = (
        title_baseline
        + entry.styles["promo_name"].leading
        - entry.styles["promo_name"].fontSize
        + menu_pdf_service.LEADER_DOT_RADIUS
    )
    assert all(dot[1] == expected_dot_y and dot[2] == 1 for dot in canvas.dots)
    expected_price_left = entry.width - pdfmetrics.stringWidth(
        price_text,
        entry._price.style.fontName,
        entry._price.style.fontSize,
    )
    assert expected_price_left - canvas.dots[0][0] - 1 == pytest.approx(8)


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
    parts = section.split(500, 220)

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
        SimpleNamespace(
            id=43,
            nombre="Media docena de empanadas",
            descripcion=None,
            precio=Decimal("6500"),
            activo=True,
            productos=[
                SimpleNamespace(
                    cantidad=Decimal("6"),
                    categoria_id=3,
                    productos=[],
                )
            ],
        ),
        SimpleNamespace(
            id=44,
            nombre="Muchas empanadas",
            descripcion=None,
            precio=Decimal("99000"),
            activo=True,
            productos=[
                SimpleNamespace(
                    cantidad=Decimal("99"),
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
        "Elegí entre Napolitana o Calabresa"
    )
    assert descriptions["Promo faina"] == "1 porción de Faina"
    assert descriptions["Docenas de empanadas"] == (
        "2 docenas de empanadas a elección"
    )
    assert descriptions["Media docena de empanadas"] == (
        "1/2 docena de empanadas a elección"
    )
    assert descriptions["Muchas empanadas"] == (
        "99 de empanadas a elección"
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
