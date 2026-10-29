from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from io import BytesIO
import os
from pathlib import Path
import re
import sys
import unicodedata
from typing import Sequence
from xml.sax.saxutils import escape

import structlog
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import (
    BaseDocTemplate,
    Flowable,
    Frame,
    KeepTogether,
    NextPageTemplate,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from app.application.public_catalog_service import build_public_catalog
from app.domain.models.offer import Offer
from app.domain.models.product import Product
from app.domain.models.product_category import ProductCategory
from app.domain.unit_of_work import AbstractUnitOfWork
from app.presentation.schemas.public_catalog_schemas import (
    PublicCatalogCategory,
    PublicCatalogOffer,
    PublicCatalogProduct,
    PublicCatalogResponse,
)


logger = structlog.get_logger(__name__)

MENU_THEME = {
    "background": colors.HexColor("#0D0D0D"),
    "surface": colors.HexColor("#141414"),
    "text": colors.HexColor("#F5F5F5"),
    "muted": colors.HexColor("#B6BCC6"),
    "tertiary": colors.HexColor("#9CA3AF"),
    "leader": colors.HexColor("#3A3A3A"),
    "green": colors.HexColor("#22C55E"),
    "red": colors.HexColor("#EF4444"),
    "divider": colors.HexColor("#2A2A2A"),
}
PAGE_MARGIN = 1.9 * cm
FIRST_PAGE_TOP_MARGIN = 4.1 * cm
LATER_PAGE_TOP_MARGIN = 1.9 * cm
BOTTOM_MARGIN = 1.8 * cm
PROMO_GUTTER = 1.4 * cm
PRODUCT_GUTTER = 1.6 * cm
PRICE_COLUMN_WIDTH = 59
PROMO_PRICE_COLUMN_WIDTH = 74
FONT_SERIF_BOLD = "Helvetica-Bold"
FONT_SERIF_ITALIC_BOLD = "Helvetica-BoldOblique"
FONT_SANS = "Helvetica"
FONT_SANS_BOLD = "Helvetica-Bold"


class MenuCatalogEmptyError(Exception):
    """Raised when there are no active products with a configured price."""


def _font_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "app" / "assets" / "menu-fonts"
    return Path(__file__).resolve().parents[1] / "assets" / "menu-fonts"


def _register_menu_fonts() -> tuple[str, str, str, str]:
    global FONT_SERIF_BOLD, FONT_SERIF_ITALIC_BOLD, FONT_SANS, FONT_SANS_BOLD

    fonts = {
        "MenuPlayfair-Bold": "PlayfairDisplay-Bold.ttf",
        "MenuPlayfair-BoldItalic": "PlayfairDisplay-BoldItalic.ttf",
        "MenuInter": "Inter-Regular.ttf",
        "MenuInter-Bold": "Inter-Bold.ttf",
    }
    registered_fonts = set(pdfmetrics.getRegisteredFontNames())
    font_dir = _font_dir()
    missing = [
        filename for filename in fonts.values() if not (font_dir / filename).is_file()
    ]
    if missing:
        logger.warning(
            "menu_pdf.fonts_missing",
            font_directory=str(font_dir),
            missing=missing,
        )
        FONT_SERIF_BOLD = "Helvetica-Bold"
        FONT_SERIF_ITALIC_BOLD = "Helvetica-BoldOblique"
        FONT_SANS = "Helvetica"
        FONT_SANS_BOLD = "Helvetica-Bold"
        return (
            FONT_SERIF_BOLD,
            FONT_SERIF_ITALIC_BOLD,
            FONT_SANS,
            FONT_SANS_BOLD,
        )

    for font_name, filename in fonts.items():
        if font_name not in registered_fonts:
            pdfmetrics.registerFont(TTFont(font_name, str(font_dir / filename)))

    FONT_SERIF_BOLD = "MenuPlayfair-Bold"
    FONT_SERIF_ITALIC_BOLD = "MenuPlayfair-BoldItalic"
    FONT_SANS = "MenuInter"
    FONT_SANS_BOLD = "MenuInter-Bold"
    return FONT_SERIF_BOLD, FONT_SERIF_ITALIC_BOLD, FONT_SANS, FONT_SANS_BOLD


def _format_money(value: str | Decimal) -> str:
    amount = Decimal(str(value)).quantize(Decimal("0.01"))
    formatted = f"{amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    if formatted.endswith(",00"):
        formatted = formatted[:-3]
    return f"$ {formatted}"


def _format_quantity(quantity: str | Decimal) -> str:
    amount = Decimal(str(quantity))
    if amount == amount.to_integral_value():
        return str(int(amount))
    return f"{amount:f}".rstrip("0").rstrip(".").replace(".", ",")


def _format_presentation(quantity: str | Decimal) -> str:
    amount = Decimal(str(quantity))
    if amount < Decimal("1"):
        return "Porción"
    if amount == Decimal("6"):
        return "Media docena"
    if amount == Decimal("12"):
        return "Docena"
    if amount == Decimal("1"):
        return "Unidad"
    return f"{_format_quantity(amount)} unid."


def _format_product_presentation(
    quantity: Decimal,
    portion_quantities: set[Decimal],
) -> str:
    label = _format_presentation(quantity)
    if quantity < Decimal("1") and len(portion_quantities) > 1:
        fraction_labels = {
            Decimal("0.125"): "1/8",
            Decimal("0.25"): "1/4",
            Decimal("0.5"): "1/2",
        }
        fraction = fraction_labels.get(quantity)
        if fraction:
            return f"{label} {fraction}"
    return label


def _title_case_if_uppercase(text: str) -> str:
    if not text or not any(character.islower() for character in text):
        connectors = {
            "a", "al", "con", "de", "del", "el", "en", "la", "las",
            "los", "por", "sin", "y",
        }

        def title_segment(segment: str, is_first_word: bool) -> str:
            word_index = 0

            def title_word(match: re.Match[str]) -> str:
                nonlocal word_index
                word = match.group(0)
                is_first = is_first_word and word_index == 0
                word_index += 1
                lowered = word.lower()
                if not is_first and lowered in connectors:
                    return lowered
                if len(word) <= 3 and word.isupper():
                    return word
                return lowered[0].upper() + lowered[1:]

            return re.sub(r"[^\W\d_]+", title_word, segment, flags=re.UNICODE)

        pieces = re.split(r"(\([^()]*\))", text)
        first_word = True
        normalized = []
        for piece in pieces:
            if piece.startswith("(") and piece.endswith(")"):
                normalized.append(piece)
                continue
            normalized.append(title_segment(piece, first_word))
            if re.search(r"[^\W\d_]", piece, flags=re.UNICODE):
                first_word = False
        return "".join(normalized)
    return text


def _format_offer_quantity(quantity: Decimal) -> str:
    amount = Decimal(str(quantity))
    portions = {
        Decimal("0.125"): "1 porción",
        Decimal("0.25"): "1 porción",
        Decimal("0.5"): "1 porción",
    }
    if amount in portions:
        return portions[amount]
    if amount == Decimal("6"):
        return "1/2 docena"
    if amount >= Decimal("12") and amount % Decimal("12") == 0:
        dozens = amount / Decimal("12")
        return f"{_format_quantity(dozens)} docena" + (
            "" if dozens == Decimal("1") else "s"
        )
    return _format_quantity(amount)


def _normalize_category_name(name: str) -> str:
    decomposed = unicodedata.normalize("NFKD", name.strip().casefold())
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def _hidden_category_names() -> set[str]:
    configured = os.getenv("MENU_PDF_HIDDEN_CATEGORIES", "Extras")
    return {
        normalized
        for name in configured.split(",")
        if (normalized := _normalize_category_name(name))
    }


def _without_hidden_categories(
    catalog: PublicCatalogResponse,
) -> PublicCatalogResponse:
    hidden_names = _hidden_category_names()
    hidden_ids = {
        category.id
        for category in catalog.categorias
        if _normalize_category_name(category.nombre) in hidden_names
    }
    if not hidden_ids:
        return catalog

    products = [
        product
        for product in catalog.productos
        if product.categoria_id not in hidden_ids
    ]
    visible_product_ids = {product.id for product in products}
    offers = []
    for offer in catalog.ofertas:
        items = []
        for item in offer.items:
            if item.categoria_id in hidden_ids:
                continue
            product_ids = [
                product_id
                for product_id in item.producto_ids
                if product_id in visible_product_ids
            ]
            if item.categoria_id is None and not product_ids:
                continue
            items.append(
                item.model_copy(update={"producto_ids": product_ids})
            )
        if items or not offer.items:
            offers.append(offer.model_copy(update={"items": items}))
    return catalog.model_copy(
        update={
            "categorias": [
                category
                for category in catalog.categorias
                if category.id not in hidden_ids
            ],
            "productos": products,
            "ofertas": offers,
        }
    )


def _offer_description(offer: PublicCatalogOffer, catalog: PublicCatalogResponse) -> str:
    products = {
        product.id: _title_case_if_uppercase(product.nombre)
        for product in catalog.productos
    }
    categories = {
        category.id: _title_case_if_uppercase(category.nombre)
        for category in catalog.categorias
    }
    entries = []

    for item in offer.items:
        amount = Decimal(str(item.cantidad))
        quantity_text = _format_offer_quantity(amount)
        if item.categoria_id is not None:
            category_name = categories.get(item.categoria_id)
            if not category_name:
                continue
            entries.append(
                f"{quantity_text} de {category_name.lower()} a elección"
            )
            continue

        names = [
            products[product_id]
            for product_id in item.producto_ids
            if product_id in products
        ]
        if len(names) > 1:
            entries.append(f"Elegí {_format_quantity(amount)}: {' / '.join(names)}")
        elif names and amount in (
            Decimal("0.125"),
            Decimal("0.25"),
            Decimal("0.5"),
        ):
            entries.append(f"{quantity_text} de {names[0]}")
        elif names and amount >= Decimal("12") and amount % Decimal("12") == 0:
            entries.append(f"{quantity_text} de {names[0]}")
        elif names:
            entries.append(f"{_format_quantity(amount)} × {names[0]}")

    return " · ".join(entries)


def _limited_lines(
    text: str,
    font_name: str,
    font_size: float,
    max_width: float,
    max_lines: int = 2,
) -> list[str]:
    words = text.split()
    if not words:
        return [""]

    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if pdfmetrics.stringWidth(candidate, font_name, font_size) <= max_width:
            current = candidate
            continue
        if current:
            lines.append(current)
            current = ""
        if pdfmetrics.stringWidth(word, font_name, font_size) <= max_width:
            current = word
            continue

        prefix = ""
        for char in word:
            if pdfmetrics.stringWidth(prefix + char, font_name, font_size) > max_width:
                break
            prefix += char
        if len(lines) + 1 >= max_lines:
            while prefix and pdfmetrics.stringWidth(
                prefix + "…", font_name, font_size
            ) > max_width:
                prefix = prefix[:-1]
            lines.append(prefix.rstrip() + "…")
            return lines
        lines.append(prefix)
        current = word[len(prefix):]
        if pdfmetrics.stringWidth(current, font_name, font_size) > max_width:
            while current and pdfmetrics.stringWidth(
                current + "…", font_name, font_size
            ) > max_width:
                current = current[:-1]
            lines.append(current.rstrip() + "…")
            return lines
    if current:
        lines.append(current)

    if len(lines) <= max_lines:
        return lines
    lines = lines[:max_lines]
    last = lines[-1]
    while last and pdfmetrics.stringWidth(
        last + "…", font_name, font_size
    ) > max_width:
        last = last[:-1]
    lines[-1] = last.rstrip() + "…"
    return lines


def _tracked_text(
    canvas: Canvas,
    text: str,
    font_name: str,
    font_size: float,
    center_x: float,
    baseline: float,
    color: colors.Color,
    tracking: float,
    align_right: bool = False,
) -> None:
    text_width = pdfmetrics.stringWidth(text, font_name, font_size)
    total_width = text_width + tracking * max(0, len(text) - 1)
    origin_x = center_x - total_width if align_right else center_x - total_width / 2
    text_object = canvas.beginText(origin_x, baseline)
    text_object.setFont(font_name, font_size)
    text_object.setFillColor(color)
    text_object.setCharSpace(tracking)
    text_object.textLine(text)
    canvas.drawText(text_object)


def _draw_heart(canvas: Canvas, center_x: float, center_y: float) -> None:
    heart = canvas.beginPath()
    heart.moveTo(center_x, center_y - 4)
    heart.curveTo(center_x - 2, center_y, center_x - 9, center_y + 3, center_x - 8, center_y + 8)
    heart.curveTo(center_x - 7, center_y + 14, center_x - 2, center_y + 13, center_x, center_y + 9)
    heart.curveTo(center_x + 2, center_y + 13, center_x + 7, center_y + 14, center_x + 8, center_y + 8)
    heart.curveTo(center_x + 9, center_y + 3, center_x + 2, center_y, center_x, center_y - 4)
    heart.close()
    canvas.saveState()
    canvas.clipPath(heart, stroke=0, fill=0)
    canvas.setFillColor(MENU_THEME["green"])
    canvas.rect(center_x - 9, center_y - 5, 6, 21, fill=1, stroke=0)
    canvas.setFillColor(MENU_THEME["text"])
    canvas.rect(center_x - 3, center_y - 5, 6, 21, fill=1, stroke=0)
    canvas.setFillColor(MENU_THEME["red"])
    canvas.rect(center_x + 3, center_y - 5, 6, 21, fill=1, stroke=0)
    canvas.restoreState()


def _page_chrome(canvas: Canvas, document: BaseDocTemplate) -> None:
    page_width, page_height = document.pagesize
    canvas.saveState()
    canvas.setFillColor(MENU_THEME["background"])
    canvas.rect(-1, -1, page_width + 2, page_height + 2, fill=1, stroke=0)

    if document.page == 1:
        serif_italic_bold, sans = _register_menu_fonts()[1:3]
        center_x = page_width / 2
        _tracked_text(
            canvas,
            "MENÚ",
            sans,
            15,
            center_x,
            page_height - 1.15 * cm,
            MENU_THEME["text"],
            2.2,
        )
        brand_size = 32
        brand_y = page_height - 2.25 * cm
        pizza_width = pdfmetrics.stringWidth("PIZZA", serif_italic_bold, brand_size)
        space_width = pdfmetrics.stringWidth(" ", serif_italic_bold, brand_size) + 12
        fiori_width = pdfmetrics.stringWidth("FIORI", serif_italic_bold, brand_size)
        brand_x = center_x - (pizza_width + space_width + fiori_width) / 2
        canvas.setFont(serif_italic_bold, brand_size)
        canvas.setFillColor(MENU_THEME["green"])
        canvas.drawString(brand_x, brand_y, "PIZZA")
        canvas.setFillColor(MENU_THEME["red"])
        canvas.drawString(brand_x + pizza_width + space_width, brand_y, "FIORI")

        divider_y = page_height - 3.05 * cm
        canvas.setStrokeColor(MENU_THEME["divider"])
        canvas.setLineWidth(0.5)
        canvas.line(PAGE_MARGIN, divider_y, center_x - 14, divider_y)
        canvas.line(center_x + 14, divider_y, page_width - PAGE_MARGIN, divider_y)
        _draw_heart(canvas, center_x, divider_y - 3)

    canvas.restoreState()


class _PageCountCanvas(Canvas):
    _saved_page_states: list[dict[str, object]]
    _footer_font: str

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self) -> None:
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def _draw_footer(self, page_number: int, total_pages: int) -> None:
        page_width, _ = self._pagesize
        center_x = page_width / 2
        flag_width = 36
        flag_y = 20
        self.saveState()
        self.setFillColor(MENU_THEME["green"])
        self.rect(center_x - flag_width / 2, flag_y, flag_width / 3, 2, fill=1, stroke=0)
        self.setFillColor(MENU_THEME["text"])
        self.rect(center_x - flag_width / 6, flag_y, flag_width / 3, 2, fill=1, stroke=0)
        self.setFillColor(MENU_THEME["red"])
        self.rect(center_x + flag_width / 6, flag_y, flag_width / 3, 2, fill=1, stroke=0)

        self.setFillColor(MENU_THEME["tertiary"])
        self.setFont(self._footer_font, 8.5)
        footer = (
            "Precios sujetos a confirmación por el local · "
            f" Pág. {page_number} de {total_pages}"
        )
        self.drawCentredString(center_x, 31, footer)
        self.restoreState()

    def save(self) -> None:
        total_pages = len(self._saved_page_states)
        self._footer_font = _register_menu_fonts()[2]
        for page_number, state in enumerate(self._saved_page_states, start=1):
            self.__dict__.update(state)
            self._draw_footer(page_number, total_pages)
            super().showPage()
        super().save()


def _paragraph_styles(
    serif_bold: str,
    sans: str,
    sans_bold: str,
) -> dict[str, ParagraphStyle]:
    return {
        "product_name": ParagraphStyle(
            "MenuProductName",
            fontName=sans,
            fontSize=10.5,
            leading=14.2,
            textColor=MENU_THEME["text"],
        ),
        "product_description": ParagraphStyle(
            "MenuProductDescription",
            fontName=sans,
            fontSize=9,
            leading=12.15,
            textColor=MENU_THEME["muted"],
        ),
        "product_price": ParagraphStyle(
            "MenuProductPrice",
            fontName=sans_bold,
            fontSize=10.5,
            leading=14.2,
            textColor=MENU_THEME["text"],
            alignment=TA_RIGHT,
        ),
        "category_offer_label": ParagraphStyle(
            "MenuCategoryOfferLabel",
            fontName=sans_bold,
            fontSize=9,
            leading=12.15,
            textColor=MENU_THEME["tertiary"],
            alignment=TA_CENTER,
        ),
        "category_offer_price": ParagraphStyle(
            "MenuCategoryOfferPrice",
            fontName=sans_bold,
            fontSize=10,
            leading=13.5,
            textColor=MENU_THEME["green"],
            alignment=TA_CENTER,
        ),
        "pizza_half_and_half_note": ParagraphStyle(
            "MenuPizzaHalfAndHalfNote",
            fontName="Helvetica-Oblique",
            fontSize=9,
            leading=12.15,
            textColor=MENU_THEME["muted"],
            alignment=TA_CENTER,
        ),
        "promo_label": ParagraphStyle(
            "MenuPromoLabel",
            fontName=sans_bold,
            fontSize=8,
            leading=10.8,
            textColor=MENU_THEME["tertiary"],
        ),
        "promo_name": ParagraphStyle(
            "MenuPromoName",
            fontName=serif_bold,
            fontSize=11.5,
            leading=14.4,
            textColor=MENU_THEME["text"],
        ),
        "promo_detail": ParagraphStyle(
            "MenuPromoDetail",
            fontName=sans,
            fontSize=9,
            leading=12.15,
            textColor=MENU_THEME["muted"],
            leftIndent=9,
            firstLineIndent=-9,
        ),
        "promo_price": ParagraphStyle(
            "MenuPromoPrice",
            fontName=sans_bold,
            fontSize=12,
            leading=15,
            textColor=MENU_THEME["green"],
            alignment=TA_RIGHT,
        ),
        "notice": ParagraphStyle(
            "MenuNotice",
            fontName=sans,
            fontSize=9,
            leading=12.15,
            textColor=MENU_THEME["muted"],
        ),
    }


def _presentation_label(
    quantity: Decimal,
    portion_quantities: set[Decimal],
) -> str:
    return _format_product_presentation(quantity, portion_quantities)


class _PresentationHeader(Flowable):
    def __init__(
        self,
        width: float,
        presentations: set[Decimal],
    ):
        super().__init__()
        self.target_width = width
        self.presentations = sorted(presentations)
        self.height = 14

    def wrap(self, availWidth: float, _availHeight: float) -> tuple[float, float]:
        self.width = min(self.target_width, availWidth)
        return self.width, self.height

    def draw(self) -> None:
        self.canv.setFillColor(MENU_THEME["tertiary"])
        for index, quantity in enumerate(self.presentations):
            column_right = self.width - (
                len(self.presentations) - index - 1
            ) * PRICE_COLUMN_WIDTH
            _tracked_text(
                self.canv,
                _format_presentation(quantity).upper(),
                FONT_SANS_BOLD,
                8,
                column_right,
                2,
                MENU_THEME["tertiary"],
                0.8,
                align_right=True,
            )


class _ProductBlock(Flowable):
    def __init__(
        self,
        product: PublicCatalogProduct,
        width: float,
        styles: dict[str, ParagraphStyle],
        category_quantities: set[Decimal],
        common_presentations: set[Decimal] | None,
    ):
        super().__init__()
        self.product = product
        self.target_width = width
        self.styles = styles
        self.category_quantities = category_quantities
        self.common_presentations = common_presentations
        self.price_column_count = max(1, len(category_quantities))
        self.spaceAfter = 9
        self._name_paragraph: Paragraph | None = None
        self._description_paragraph: Paragraph | None = None
        self._name_width = width
        self._name_height = 0
        self._name_lines: list[str] = []
        self._description_height = 0
        self._price_cells: list[tuple[int, Paragraph, str | None]] = []
        self._labels_height = 0

    def wrap(self, availWidth: float, availHeight: float) -> tuple[float, float]:
        self.width = min(self.target_width, availWidth)
        prices = {
            Decimal(str(price.cantidad)): Decimal(str(price.precio))
            for price in self.product.precios
        }
        reserved_price_width = (
            10 if self.price_column_count >= 2 else 8
        ) + self.price_column_count * PRICE_COLUMN_WIDTH
        self._name_width = max(38, self.width - reserved_price_width)
        product_name = _title_case_if_uppercase(self.product.nombre)
        name_lines = _limited_lines(
            product_name,
            self.styles["product_name"].fontName,
            self.styles["product_name"].fontSize,
            self._name_width,
        )
        self._name_lines = name_lines
        self._name_paragraph = Paragraph(
            "<br/>".join(escape(line) for line in name_lines),
            self.styles["product_name"],
        )
        _, self._name_height = self._name_paragraph.wrap(
            self._name_width,
            availHeight,
        )

        self._price_cells = []
        portion_quantities = {
            quantity for quantity in prices if quantity < Decimal("1")
        }
        needs_hanging_labels = (
            self.common_presentations is None
            and (
                len(prices) > 1
                or any(quantity < Decimal("1") for quantity in prices)
            )
        )
        for quantity, amount in sorted(prices.items()):
            column_index = self.price_column_count - len(prices) + len(
                self._price_cells
            )
            label = (
                _presentation_label(quantity, portion_quantities)
                if needs_hanging_labels
                else None
            )
            price = Paragraph(
                escape(_format_money(amount)),
                self.styles["product_price"],
            )
            price.wrap(PRICE_COLUMN_WIDTH, availHeight)
            self._price_cells.append((column_index, price, label))
        self._labels_height = 11 if any(label for _, _, label in self._price_cells) else 0

        description = getattr(self.product, "descripcion", None)
        if description:
            self._description_paragraph = Paragraph(
                escape(_title_case_if_uppercase(str(description))),
                self.styles["product_description"],
            )
            _, self._description_height = self._description_paragraph.wrap(
                self.width,
                availHeight,
            )
        else:
            self._description_paragraph = None
            self._description_height = 0

        height = self._labels_height + max(self._name_height, 13)
        if self._description_paragraph:
            height += 2 + self._description_height
        self.height = height + self.spaceAfter
        return self.width, self.height

    def draw(self) -> None:
        description_gap = 2 if self._description_paragraph else 0
        description_block_height = description_gap + self._description_height
        name_bottom = self.spaceAfter + description_block_height
        price_bottom = name_bottom + max(
            0, self._name_height - self.styles["product_name"].leading
        )
        self._name_paragraph.drawOn(self.canv, 0, name_bottom)
        for column_index, price, label in self._price_cells:
            column_right = self.width - (
                self.price_column_count - column_index - 1
            ) * PRICE_COLUMN_WIDTH
            price.drawOn(
                self.canv,
                column_right - PRICE_COLUMN_WIDTH,
                price_bottom,
            )
            if label:
                _tracked_text(
                    self.canv,
                    label.upper(),
                    FONT_SANS,
                    8,
                    column_right,
                    price_bottom + 13,
                    MENU_THEME["tertiary"],
                    0.8,
                    align_right=True,
                )
        if len(self._name_lines) == 1 and self._price_cells:
            name_width = pdfmetrics.stringWidth(
                self._name_lines[0],
                self.styles["product_name"].fontName,
                self.styles["product_name"].fontSize,
            )
            price_left = self.width - (
                self.price_column_count * PRICE_COLUMN_WIDTH
            )
            leader_start = name_width + 3
            leader_end = price_left - 3
            if leader_end - leader_start >= 6:
                self.canv.saveState()
                self.canv.setStrokeColor(MENU_THEME["leader"])
                self.canv.setLineWidth(0.5)
                self.canv.setDash(0, 3)
                self.canv.line(
                    leader_start,
                    name_bottom + 4,
                    leader_end,
                    name_bottom + 4,
                )
                self.canv.restoreState()
        if self._description_paragraph:
            self._description_paragraph.drawOn(
                self.canv,
                0,
                self.spaceAfter,
            )


class _SectionHeading(Flowable):
    def __init__(
        self,
        title: str,
        width: float,
        serif_bold: str,
    ):
        super().__init__()
        self.title = title.upper()
        self.target_width = width
        self.font_name = serif_bold
        self.tracking = 1.5
        self.font_size = 17.5
        self.continuation = False
        self.lines: list[str] = []

    def wrap(self, availWidth: float, _availHeight: float) -> tuple[float, float]:
        self.width = min(self.target_width, availWidth)
        self.lines = _limited_lines(
            self.title,
            self.font_name,
            self.font_size,
            self.width - 12,
        )
        title_height = len(self.lines) * 23
        self.height = title_height + 12
        return self.width, self.height

    def draw(self) -> None:
        baseline = self.height - 18
        for line in self.lines:
            _tracked_text(
                self.canv,
                line,
                self.font_name,
                self.font_size,
                self.width / 2,
                baseline,
                (
                    MENU_THEME["tertiary"]
                    if self.continuation
                    else MENU_THEME["text"]
                ),
                self.tracking,
            )
            baseline -= 23

        self.canv.setStrokeColor(MENU_THEME["green"])
        self.canv.setLineWidth(1)
        self.canv.line(
            (self.width - 36) / 2,
            2,
            (self.width + 36) / 2,
            2,
        )

    def as_continuation(self) -> _SectionHeading:
        heading = _SectionHeading(
            self.title,
            self.target_width,
            self.font_name,
        )
        heading.title = f"{self.title} (CONT.)"
        heading.continuation = True
        return heading


class _CategoryTable(Table):
    def split(self, availWidth: float, availHeight: float) -> list[Table]:
        parts = super().split(availWidth, availHeight)
        if len(parts) <= 1:
            return parts

        def cell_flowables(cell: object) -> list[object]:
            if isinstance(cell, (tuple, list)):
                return [
                    flowable
                    for child in cell
                    for flowable in cell_flowables(child)
                ]
            return [cell]

        def product_count(table: Table) -> int:
            return sum(
                isinstance(flowable, _ProductBlock)
                for row in table._cellvalues
                for cell in row
                for flowable in cell_flowables(cell)
            )

        total_products = product_count(self)
        if total_products >= 7:
            first_count = product_count(parts[0])
            if (
                first_count < 3
                and availHeight
                < A4[1] - FIRST_PAGE_TOP_MARGIN - BOTTOM_MARGIN
            ):
                return []

            if product_count(parts[-1]) < 3:
                header_rows = int(self.repeatRows)
                for row_index in range(
                    len(parts[0]._rowHeights) - 1,
                    header_rows - 1,
                    -1,
                ):
                    row_height = parts[0]._rowHeights[row_index]
                    candidate = super().split(
                        availWidth,
                        max(1, availHeight - row_height),
                    )
                    if (
                        len(candidate) > 1
                        and product_count(candidate[0]) >= 3
                        and all(product_count(part) >= 3 for part in candidate)
                    ):
                        parts = candidate
                        break

        for part in parts[1:]:
            heading_cell = part._cellvalues[0][0]
            heading_flowables = cell_flowables(heading_cell)
            heading = heading_flowables[0] if heading_flowables else None
            if isinstance(heading, _SectionHeading):
                continuation = heading.as_continuation()
                part._cellvalues[0] = list(part._cellvalues[0])
                part._cellvalues[0][0] = (
                    (continuation,)
                    if isinstance(heading_cell, tuple)
                    else continuation
                )
        return parts


class _PromoEntry(Flowable):
    def __init__(
        self,
        offer: PublicCatalogOffer,
        catalog: PublicCatalogResponse,
        width: float,
        styles: dict[str, ParagraphStyle],
    ):
        super().__init__()
        self.offer = offer
        self.catalog = catalog
        self.target_width = width
        self.styles = styles
        self._component_paragraphs: list[tuple[Paragraph, float]] = []
        self._title: Paragraph | None = None
        self._title_height = 0
        self._detail_paragraph: Paragraph | None = None
        self._detail_height = 0
        self._price: Paragraph | None = None
        self.label, self.title, self.description = self._copy()

    def _copy(self) -> tuple[str, str, str | None]:
        name = self.offer.nombre.strip()
        description = (self.offer.descripcion or "").strip()
        display_name = _title_case_if_uppercase(name)
        display_description = _title_case_if_uppercase(description)
        starts_with_promo = (
            re.match(r"^promo(?:\s|$)", name, re.IGNORECASE) is not None
        )
        if starts_with_promo:
            suffix = re.sub(r"^(?:promo\s*)+", "", name, flags=re.IGNORECASE).strip()
            numbered = re.fullmatch(r"\d+", suffix)
            label = f"PROMO {suffix}".upper() if numbered else "PROMO"
            title = (
                display_description
                if description and description.casefold() != name.casefold()
                else _title_case_if_uppercase(suffix)
                if numbered is None and suffix
                else None
            )
            detail = None
        else:
            label = "PROMO"
            title = display_name
            detail = (
                display_description
                if description.casefold() != name.casefold()
                else None
            )
        return label, title, detail

    def wrap(self, availWidth: float, availHeight: float) -> tuple[float, float]:
        self.width = min(self.target_width, availWidth)
        title_width = max(40, self.width - PROMO_PRICE_COLUMN_WIDTH - 8)
        if self.title:
            title_lines = _limited_lines(
                self.title,
                self.styles["promo_name"].fontName,
                self.styles["promo_name"].fontSize,
                title_width,
                max_lines=2,
            )
            self._title = Paragraph(
                "<br/>".join(
                    escape(_title_case_if_uppercase(line)) for line in title_lines
                ),
                self.styles["promo_name"],
            )
            _, self._title_height = self._title.wrap(title_width, availHeight)
        else:
            self._title = None
            self._title_height = 0
        self._price = Paragraph(
            escape(_format_money(self.offer.precio)),
            self.styles["promo_price"],
        )
        _, price_height = self._price.wrap(
            PROMO_PRICE_COLUMN_WIDTH,
            availHeight,
        )
        if self.description:
            self._detail_paragraph = Paragraph(
                f"&#8226;&nbsp; {escape(_title_case_if_uppercase(self.description))}",
                self.styles["promo_detail"],
            )
            _, self._detail_height = self._detail_paragraph.wrap(
                self.width - 8,
                availHeight,
            )
        else:
            self._detail_paragraph = None
            self._detail_height = 0
        components = _offer_description(self.offer, self.catalog)
        self._component_paragraphs = []
        if components:
            for component in components.split(" · "):
                bullet = Paragraph(
                    f"&#8226;&nbsp; {escape(_title_case_if_uppercase(component))}",
                    self.styles["promo_detail"],
                )
                _, bullet_height = bullet.wrap(self.width - 8, availHeight)
                self._component_paragraphs.append((bullet, bullet_height))

        self.height = (
            11
            + 3
            + max(self._title_height, price_height)
            + (self._detail_height + 2 if self._detail_paragraph else 0)
            + sum(height + 1 for _, height in self._component_paragraphs)
        )
        return self.width, self.height

    def split(self, _availWidth: float, _availHeight: float) -> list[Flowable]:
        return []

    def draw(self) -> None:
        label = self.canv.beginText(0, self.height - 8)
        label.setFont(FONT_SANS_BOLD, 8)
        label.setFillColor(MENU_THEME["tertiary"])
        label.setCharSpace(0.8)
        label.textLine(self.label)
        self.canv.drawText(label)
        y = self.height - 13
        if self._title:
            self._title.drawOn(self.canv, 0, y - self._title_height)
        self._price.drawOn(
            self.canv,
            self.width - PROMO_PRICE_COLUMN_WIDTH,
            y - 16,
        )
        y -= max(self._title_height, 17) + 2
        if self._detail_paragraph:
            y -= self._detail_height
            self._detail_paragraph.drawOn(self.canv, 0, y)
            y -= 2
        for paragraph, height in self._component_paragraphs:
            y -= height
            paragraph.drawOn(self.canv, 0, y)
            y -= 1


class _Notice(Flowable):
    def __init__(self, text: str, width: float, style: ParagraphStyle):
        super().__init__()
        self.text = text
        self.target_width = width
        self.style = style
        self.padding = 9
        self.paragraph: Paragraph | None = None

    def wrap(self, availWidth: float, availHeight: float) -> tuple[float, float]:
        self.width = min(self.target_width, availWidth)
        self.paragraph = Paragraph(escape(self.text), self.style)
        _, paragraph_height = self.paragraph.wrap(
            self.width - 2 * self.padding,
            availHeight,
        )
        self.height = paragraph_height + 2 * self.padding
        return self.width, self.height

    def draw(self) -> None:
        self.canv.setStrokeColor(MENU_THEME["divider"])
        self.canv.setLineWidth(0.6)
        self.canv.roundRect(
            0,
            0,
            self.width,
            self.height,
            5,
            fill=0,
            stroke=1,
        )
        self.paragraph.drawOn(
            self.canv,
            self.padding,
            self.padding,
        )


def _common_presentations(
    products: Sequence[PublicCatalogProduct],
) -> tuple[set[Decimal], set[Decimal] | None]:
    sets = [
        {Decimal(str(price.cantidad)) for price in product.precios}
        for product in products
    ]
    category_quantities = set().union(*sets) if sets else set()
    common = sets[0] if sets and len(sets[0]) == 2 and all(
        presentation_set == sets[0] for presentation_set in sets
    ) else None
    return category_quantities, common


def _category_table(
    products: Sequence[PublicCatalogProduct],
    content_width: float,
    styles: dict[str, ParagraphStyle],
    category_quantities: set[Decimal],
    common_presentations: set[Decimal] | None,
) -> tuple[list[list[object]], list[float], int]:
    if len(products) <= 3:
        column_width = content_width * 0.7
        data: list[list[object]] = []
        if common_presentations:
            data.append(
                [
                    _PresentationHeader(
                        column_width,
                        common_presentations,
                    )
                ]
            )
        data.extend(
            [
                _ProductBlock(
                    product,
                    column_width,
                    styles,
                    category_quantities,
                    common_presentations,
                )
            ]
            for product in products
        )
        return data, [column_width], len(data)

    gutter = PRODUCT_GUTTER
    column_width = (content_width - gutter) / 2
    left_count = (len(products) + 1) // 2
    right_count = len(products) - left_count
    rows = []
    if common_presentations:
        header = _PresentationHeader(
            column_width,
            common_presentations,
        )
        rows.append(
            [
                header,
                "",
                _PresentationHeader(column_width, common_presentations),
            ]
        )
    for row_index in range(max(left_count, right_count)):
        left = (
            _ProductBlock(
                products[row_index],
                column_width,
                styles,
                category_quantities,
                common_presentations,
            )
            if row_index < left_count
            else ""
        )
        right_index = left_count + row_index
        right = (
            _ProductBlock(
                products[right_index],
                column_width,
                styles,
                category_quantities,
                common_presentations,
            )
            if row_index < right_count
            else ""
        )
        rows.append([left, "", right])
    initial_rows = min(len(rows), 3 if common_presentations else 2)
    return rows, [column_width, gutter, column_width], initial_rows


def _category_offer_presentations(
    offers: Sequence[PublicCatalogOffer],
    category_id: int,
    width: float,
    styles: dict[str, ParagraphStyle],
) -> Table | None:
    category_offers = [
        offer
        for offer in offers
        if len(offer.items) == 1
        and offer.items[0].categoria_id == category_id
        and not offer.items[0].producto_ids
    ]
    if not category_offers:
        return None

    category_offers.sort(
        key=lambda offer: (
            Decimal(str(offer.items[0].cantidad)),
            offer.nombre.casefold(),
        )
    )
    cell_width = width / len(category_offers)
    labels = []
    prices = []
    for offer in category_offers:
        quantity = Decimal(str(offer.items[0].cantidad))
        unit_price = (
            Decimal(str(offer.precio)) / quantity
        ).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        if quantity == Decimal("6"):
            label = "Media docena"
        elif quantity >= Decimal("12") and quantity % Decimal("12") == 0:
            dozens = quantity / Decimal("12")
            label = (
                "Docena"
                if dozens == Decimal("1")
                else f"{_format_quantity(dozens)} docenas"
            )
        else:
            label = _format_presentation(quantity)
        labels.append(Paragraph(escape(label), styles["category_offer_label"]))
        prices.append(
            Paragraph(
                escape(f"{_format_money(unit_price)} c/u"),
                styles["category_offer_price"],
            )
        )

    table = Table(
        [labels, prices],
        colWidths=[cell_width] * len(category_offers),
        hAlign="LEFT",
    )
    table.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                ("TOPPADDING", (0, 0), (-1, 0), 0),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 2),
                ("TOPPADDING", (0, 1), (-1, 1), 0),
                ("BOTTOMPADDING", (0, 1), (-1, 1), 5),
            ]
        )
    )
    return table


def _product_table(
    rows: list[list[object]],
    column_widths: list[float],
    h_align: str,
) -> Table:
    table = Table(rows, colWidths=column_widths, hAlign=h_align)
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    return table


def _category_section_table(
    heading: _SectionHeading,
    category_offer_table: Table | None,
    pizza_note: Paragraph | None,
    product_rows: list[list[object]],
    column_widths: list[float],
    common_presentations: set[Decimal] | None,
    h_align: str,
) -> _CategoryTable:
    column_count = len(column_widths)
    rows: list[list[object]] = []
    span_rows: list[int] = []

    def append_spanning_row(content: Flowable | Table) -> None:
        row_index = len(rows)
        rows.append([content, *("" for _ in range(column_count - 1))])
        if column_count > 1:
            span_rows.append(row_index)

    append_spanning_row(heading)
    repeat_rows = 1
    if category_offer_table is not None:
        append_spanning_row(category_offer_table)
        repeat_rows += 1

    if pizza_note is not None:
        append_spanning_row(pizza_note)
        append_spanning_row(Spacer(1, 6))
        repeat_rows += 2
    elif category_offer_table is not None:
        append_spanning_row(Spacer(1, 12))
        repeat_rows += 1
    else:
        append_spanning_row(Spacer(1, 12))
        repeat_rows += 1

    if common_presentations and product_rows:
        rows.append(product_rows.pop(0))
        repeat_rows += 1
    rows.extend(product_rows)

    table = _CategoryTable(
        rows,
        colWidths=column_widths,
        hAlign=h_align,
        repeatRows=repeat_rows,
        splitByRow=1,
    )
    style_commands: list[tuple] = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]
    style_commands.extend(
        ("SPAN", (0, row_index), (-1, row_index))
        for row_index in span_rows
    )
    table.setStyle(TableStyle(style_commands))
    return table


def _promo_rows(
    offers: Sequence[PublicCatalogOffer],
    catalog: PublicCatalogResponse,
    width: float,
    styles: dict[str, ParagraphStyle],
) -> list[Table]:
    gutter = PROMO_GUTTER
    entry_width = (width - gutter) / 2
    ordered_offers = sorted(offers, key=lambda offer: offer.nombre.casefold())
    rows = []
    for index in range(0, len(ordered_offers), 2):
        left = _PromoEntry(
            ordered_offers[index],
            catalog,
            entry_width,
            styles,
        )
        if index + 1 < len(ordered_offers):
            right = _PromoEntry(
                ordered_offers[index + 1],
                catalog,
                entry_width,
                styles,
            )
            row = Table(
                [[left, "", right]],
                colWidths=[entry_width, gutter, entry_width],
                hAlign="LEFT",
            )
        else:
            row = Table(
                [[left, "", ""]],
                colWidths=[entry_width, gutter, entry_width],
                hAlign="LEFT",
            )
        row.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ]
            )
        )
        rows.append(row)
    return rows


def _page_frame(
    width: float,
    height: float,
    top_margin: float,
    identifier: str,
) -> Frame:
    return Frame(
        PAGE_MARGIN,
        BOTTOM_MARGIN,
        width - 2 * PAGE_MARGIN,
        height - top_margin - BOTTOM_MARGIN,
        id=identifier,
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0,
    )


def _categories_for_menu(
    catalog: PublicCatalogResponse,
) -> list[PublicCatalogCategory]:
    categories = list(catalog.categorias)
    if os.getenv("MENU_PDF_REORDER_TO_FILL", "false").strip().casefold() != "true":
        return categories

    products_by_category: dict[int, int] = {}
    for product in catalog.productos:
        products_by_category[product.categoria_id] = (
            products_by_category.get(product.categoria_id, 0) + 1
        )
    pizza_index = next(
        (
            index
            for index, category in enumerate(categories)
            if _normalize_category_name(category.nombre) == "pizzas"
        ),
        None,
    )
    if pizza_index is None:
        return categories

    fixed_categories = categories[: pizza_index + 1]
    remaining_categories = categories[pizza_index + 1 :]
    remaining_categories.sort(
        key=lambda category: (
            products_by_category.get(category.id, 0) > 3,
            products_by_category.get(category.id, 0),
        )
    )
    return fixed_categories + remaining_categories


def _render_menu_pdf(catalog: PublicCatalogResponse) -> bytes:
    catalog = _without_hidden_categories(catalog)
    serif_bold, _, sans, sans_bold = _register_menu_fonts()
    styles = _paragraph_styles(serif_bold, sans, sans_bold)
    stream = BytesIO()
    document = BaseDocTemplate(
        stream,
        pagesize=A4,
        leftMargin=PAGE_MARGIN,
        rightMargin=PAGE_MARGIN,
        topMargin=FIRST_PAGE_TOP_MARGIN,
        bottomMargin=BOTTOM_MARGIN,
        title="Menú digital · Pizza Fiori",
        author="Pizza Fiori",
        pageCompression=1,
    )
    page_width, page_height = A4
    document.addPageTemplates(
        [
            PageTemplate(
                id="first",
                frames=[
                    _page_frame(
                        page_width,
                        page_height,
                        FIRST_PAGE_TOP_MARGIN,
                        "first_frame",
                    )
                ],
                onPage=_page_chrome,
            ),
            PageTemplate(
                id="later",
                frames=[
                    _page_frame(
                        page_width,
                        page_height,
                        LATER_PAGE_TOP_MARGIN,
                        "later_frame",
                    )
                ],
                onPage=_page_chrome,
            ),
        ]
    )

    content_width = page_width - 2 * PAGE_MARGIN
    story = [NextPageTemplate("later")]
    if catalog.ofertas:
        promo_heading = _SectionHeading("Promociones", content_width, serif_bold)
        promo_rows = _promo_rows(catalog.ofertas, catalog, content_width, styles)
        if promo_rows:
            story.append(
                KeepTogether([promo_heading, Spacer(1, 12), *promo_rows])
            )
            if catalog.categorias:
                story.append(Spacer(1, 27))

    visible_categories = [
        category
        for category in _categories_for_menu(catalog)
        if any(product.categoria_id == category.id for product in catalog.productos)
    ]
    for category_index, category in enumerate(visible_categories):
        category_products = [
            product
            for product in catalog.productos
            if product.categoria_id == category.id
        ]
        if not category_products:
            continue
        category_quantities, common_presentations = _common_presentations(
            category_products
        )
        category_heading = _SectionHeading(
            category.nombre,
            content_width,
            serif_bold,
        )
        rows, column_widths, _ = _category_table(
            category_products,
            content_width,
            styles,
            category_quantities,
            common_presentations,
        )
        h_align = "CENTER" if len(category_products) <= 3 else "LEFT"
        category_offer_width = (
            content_width * 0.7 if len(category_products) <= 3 else content_width
        )
        category_offer_table = _category_offer_presentations(
            catalog.ofertas,
            category.id,
            category_offer_width,
            styles,
        )
        pizza_note = (
            Paragraph(
                escape(
                    "Pizzas mitad y mitad: se abona el precio de la variedad más cara."
                ),
                styles["pizza_half_and_half_note"],
            )
            if _normalize_category_name(category.nombre) == "pizzas"
            else None
        )
        category_table = _category_section_table(
            category_heading,
            category_offer_table,
            pizza_note,
            rows,
            column_widths,
            common_presentations,
            h_align,
        )
        story.append(KeepTogether([category_table]))
        if category_index < len(visible_categories) - 1:
            story.append(Spacer(1, 27))

    document.build(story, canvasmaker=_PageCountCanvas)

    page_count = document.page
    if page_count > 3:
        logger.warning(
            "menu_pdf.exceeds_three_pages",
            page_count=page_count,
        )
    logger.info(
        "menu_pdf.generated",
        pages=page_count,
        categories=len(catalog.categorias),
        products=len(catalog.productos),
        offers=len(catalog.ofertas),
    )
    return stream.getvalue()


class MenuPdfService:
    async def generate(self, uow: AbstractUnitOfWork) -> bytes:
        categories: Sequence[ProductCategory] = (
            await uow.product_category_repo.list_by_active(activo=True)
        )
        products: Sequence[Product] = await uow.product_repo.list(active=True)
        offers: Sequence[Offer] = await uow.offer_repo.list(active=True)
        catalog = build_public_catalog(
            categories,
            products,
            offers,
            image_urls={},
            published_at=datetime.now(timezone.utc),
        )
        if not catalog.productos:
            raise MenuCatalogEmptyError(
                "No hay productos activos con precios para generar el menú."
            )
        return await asyncio.to_thread(_render_menu_pdf, catalog)
