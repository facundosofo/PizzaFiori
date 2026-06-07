"""
ReportService  –  Generador de reporte de ventas PDF
Diseño dark-mode según guía UX/UI PizzaFiori (Enero 2026)
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from io import BytesIO
from typing import List, Optional, Tuple

import structlog
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mticker
from matplotlib.backends.backend_agg import FigureCanvasAgg

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    Image,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from app.domain.models.expense import Expense
from app.domain.models.sale import Sale
from app.domain.unit_of_work import AbstractUnitOfWork


# ─────────────────────────────────────────────────────────────────────────────
#  Paletas de colores para modo oscuro y claro
# ─────────────────────────────────────────────────────────────────────────────
THEMES = {
    "dark": {
        "BG_MAIN":       colors.HexColor("#0d0d0d"),
        "BG_SECOND":     colors.HexColor("#1a1a1a"),
        "BG_RAISED":     colors.HexColor("#2a2a2a"),
        "TEXT_H1":       colors.HexColor("#ffffff"),
        "TEXT_BODY":     colors.HexColor("#e8e8e8"),
        "TEXT_MUTED":    colors.HexColor("#888888"),
        "GREEN_BASE":    colors.HexColor("#22c55e"),
        "GREEN_LIGHT":   colors.HexColor("#4ade80"),
        "GREEN_SUBTLE":  colors.HexColor("#0d2b17"),   # fondo filas subtotal/recargo
        "GREEN_TOTAL":   colors.HexColor("#14381f"),   # fondo fila TOTAL
        "BORDER_MAIN":   colors.HexColor("#404040"),
        "BORDER_SUB":    colors.HexColor("#2e2e2e"),
    },
    "light": {
        "BG_MAIN":       colors.HexColor("#ffffff"),
        "BG_SECOND":     colors.HexColor("#f8f9fa"),
        "BG_RAISED":     colors.HexColor("#f1f3f5"),
        "TEXT_H1":       colors.HexColor("#222222"),
        "TEXT_BODY":     colors.HexColor("#333333"),
        "TEXT_MUTED":    colors.HexColor("#888888"),
        "GREEN_BASE":    colors.HexColor("#22c55e"),
        "GREEN_LIGHT":   colors.HexColor("#16a34a"),
        "GREEN_SUBTLE":  colors.HexColor("#f0fdf4"),   # fondo filas subtotal/recargo
        "GREEN_TOTAL":   colors.HexColor("#dcfce7"),   # fondo fila TOTAL
        "BORDER_MAIN":   colors.HexColor("#cccccc"),
        "BORDER_SUB":    colors.HexColor("#e0e0e0"),
    },
}

# Variables globales para compatibilidad (por defecto dark)
BG_MAIN    = THEMES["dark"]["BG_MAIN"]
BG_SECOND  = THEMES["dark"]["BG_SECOND"]
BG_RAISED  = THEMES["dark"]["BG_RAISED"]
TEXT_H1    = THEMES["dark"]["TEXT_H1"]
TEXT_BODY  = THEMES["dark"]["TEXT_BODY"]
TEXT_MUTED = THEMES["dark"]["TEXT_MUTED"]
GREEN_BASE  = THEMES["dark"]["GREEN_BASE"]
GREEN_LIGHT = THEMES["dark"]["GREEN_LIGHT"]
BORDER_MAIN = THEMES["dark"]["BORDER_MAIN"]
BORDER_SUB  = THEMES["dark"]["BORDER_SUB"]


def get_theme_colors(mode: str = "dark"):
    """Devuelve el diccionario de colores para el modo dado ('dark' o 'light')."""
    return THEMES.get(mode, THEMES["dark"])


LOGO_PATH = r"C:\Users\Facundo\Desktop\PizzaFiori\frontend\public\logo.png"

HEADER_H = 1.4 * cm
FOOTER_H = 0.8 * cm
MARGIN   = 1.8 * cm


# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class ReportResult:
    pdf_bytes: Optional[bytes] = None
    error: Optional[str] = None
    status_code: int = 200


# ─────────────────────────────────────────────────────────────────────────────
#  Función de decoración de página (se llama ANTES del contenido Platypus)
# ─────────────────────────────────────────────────────────────────────────────
def _decorate_page_with_theme(
    canvas: rl_canvas.Canvas,
    doc: BaseDocTemplate,
    mode: str = "dark",
    report_title: str = "Reporte de Ventas",
):
    """
    onPage callback: dibuja fondo, header y footer ANTES que Platypus
    pinte el contenido, así nada queda tapado. Usa la paleta del modo.
    """
    colors_ = get_theme_colors(mode)
    canvas.saveState()
    w, h = A4

    # ── Fondo completo ────────────────────────────────────────────────────────
    canvas.setFillColor(colors_["BG_MAIN"])
    canvas.rect(0, 0, w, h, fill=1, stroke=0)

    # ── Header bar ────────────────────────────────────────────────────────────
    canvas.setFillColor(colors_["BG_SECOND"])
    canvas.rect(0, h - HEADER_H, w, HEADER_H, fill=1, stroke=0)

    # Línea verde inferior del header
    canvas.setStrokeColor(colors_["GREEN_BASE"])
    canvas.setLineWidth(1.5)
    canvas.line(0, h - HEADER_H, w, h - HEADER_H)

    # Logo o texto fallback
    logo_y     = h - HEADER_H + 0.18 * cm
    logo_h     = HEADER_H - 0.36 * cm
    logo_max_w = 4 * cm
    logo_drawn = False
    if os.path.isfile(LOGO_PATH):
        try:
            canvas.drawImage(
                LOGO_PATH, 2 * cm, logo_y,
                height=logo_h, width=logo_max_w,
                preserveAspectRatio=True, anchor="w",
                mask="auto",
            )
            logo_drawn = True
        except Exception:
            pass

    if not logo_drawn:
        canvas.setFillColor(colors_["GREEN_BASE"])
        canvas.setFont("Helvetica-Bold", 11)
        canvas.drawString(2 * cm, h - HEADER_H / 2 - 0.15 * cm, "PizzaFiori")

    # Fecha generación (derecha)
    canvas.setFillColor(colors_["TEXT_MUTED"])
    canvas.setFont("Helvetica", 7.5)
    now_str = datetime.now().strftime("%d/%m/%Y  %H:%M")
    canvas.drawRightString(w - 2 * cm, h - HEADER_H / 2 - 0.15 * cm, f"Generado: {now_str}")

    # ── Footer ─────────────────────────────────────────────────────────────────
    canvas.setFillColor(colors_["BG_SECOND"])
    canvas.rect(0, 0, w, FOOTER_H, fill=1, stroke=0)

    canvas.setStrokeColor(colors_["BORDER_MAIN"])
    canvas.setLineWidth(0.5)
    canvas.line(0, FOOTER_H, w, FOOTER_H)

    canvas.setFillColor(colors_["TEXT_MUTED"])
    canvas.setFont("Helvetica", 7)
    canvas.drawCentredString(
        w / 2,
        FOOTER_H / 2 - 0.1 * cm,
        f"PizzaFiori  •  {report_title}  •  Página {doc.page} de {doc._pagecount if hasattr(doc, '_pagecount') else '?'}",
    )

    canvas.restoreState()


# ─────────────────────────────────────────────────────────────────────────────
#  Two-pass doc para saber el total de páginas antes de pintar
# ─────────────────────────────────────────────────────────────────────────────
class TwoPassDoc(BaseDocTemplate):
    """
    Primer pass: cuenta páginas.
    Segundo pass: pinta con el total correcto en el footer.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._pagecount = 0

    def handle_pageEnd(self):
        self._pagecount = self.page
        super().handle_pageEnd()

    def build(self, flowables, **kwargs):
        from io import BytesIO as _BytesIO
        tmp = _BytesIO()
        self._pagecount = 0
        super().build(flowables, **kwargs)


# ─────────────────────────────────────────────────────────────────────────────
#  Servicio principal
# ─────────────────────────────────────────────────────────────────────────────
class ReportService:

    def __init__(
        self,
        uow: AbstractUnitOfWork,
        logger: structlog.BoundLogger | None = None,
    ):
        self.uow    = uow
        self.logger = logger or structlog.get_logger(__name__)

    # ── Punto de entrada ─────────────────────────────────────────────────────

    async def generate_sales_report(
        self,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
        modo: str = "light",
        mostrar_resumen_periodo: bool = True,
        mostrar_resumen_dia: bool = True,
        mostrar_resumen_mes: bool = False,
        mostrar_resumen_categoria: bool = True,
        mostrar_resumen_productos: bool = True,
        mostrar_detalle_ventas: bool = True,
    ) -> ReportResult:
        try:
            self.logger.info("Generando reporte", fecha_desde=fecha_desde, fecha_hasta=fecha_hasta)

            async with self.uow as uow:
                from datetime import time, timedelta
                fecha_desde_dt = (
                    datetime.combine(fecha_desde, time.min) + timedelta(hours=6)
                    if fecha_desde
                    else None
                )
                fecha_hasta_dt = (
                    datetime.combine(fecha_hasta, time.max) + timedelta(hours=6)
                    if fecha_hasta
                    else None
                )
                sales = await uow.sale_repo.list(
                    skip=0, limit=10_000,
                    fecha_desde=fecha_desde_dt,
                    fecha_hasta=fecha_hasta_dt,
                )

            if not sales:
                return ReportResult(error="No hay ventas en el período seleccionado", status_code=404)

            total_ventas   = len(sales)
            total_ingresos = sum(s.total for s in sales)
            chart_data     = self._prepare_chart_data(sales)

            pdf_bytes = await self._create_pdf(
                sales, total_ventas, total_ingresos,
                fecha_desde, fecha_hasta, chart_data,
                modo,
                mostrar_resumen_periodo,
                mostrar_resumen_dia,
                mostrar_resumen_mes,
                mostrar_resumen_categoria,
                mostrar_resumen_productos,
                mostrar_detalle_ventas,
            )
            self.logger.info("Reporte OK", total_ventas=total_ventas)
            return ReportResult(pdf_bytes=pdf_bytes)

        except Exception as e:
            self.logger.error("Error reporte", error=str(e), exc_info=True)
            return ReportResult(error=str(e), status_code=500)

    # ── Preparación de datos ─────────────────────────────────────────────────

    def _prepare_chart_data(self, sales: List[Sale]) -> List[Tuple[datetime, Decimal]]:
        import datetime as dt_mod
        buckets: dict = {}
        for sale in sales:
            d = (sale.fecha_creacion - dt_mod.timedelta(hours=6)).date()
            buckets[d] = buckets.get(d, Decimal("0")) + sale.total
        return [
            (datetime.combine(d, datetime.min.time()), t)
            for d, t in sorted(buckets.items())
        ]

    # ── Construcción del PDF ─────────────────────────────────────────────────

    async def _create_pdf(
        self,
        sales: List[Sale],
        total_ventas: int,
        total_ingresos: Decimal,
        fecha_desde: Optional[date],
        fecha_hasta: Optional[date],
        chart_data: List[Tuple[datetime, Decimal]],
        modo: str = "dark",
        mostrar_resumen_periodo: bool = True,
        mostrar_resumen_dia: bool = True,
        mostrar_resumen_mes: bool = False,
        mostrar_resumen_categoria: bool = True,
        mostrar_resumen_productos: bool = True,
        mostrar_detalle_ventas: bool = True,
    ) -> bytes:
        buffer  = BytesIO()
        w, h    = A4
        TOP_PAD = HEADER_H + 0.5 * cm
        BOT_PAD = FOOTER_H + 0.5 * cm

        doc = BaseDocTemplate(
            buffer, pagesize=A4,
            rightMargin=MARGIN, leftMargin=MARGIN,
            topMargin=TOP_PAD, bottomMargin=BOT_PAD,
        )

        page_count_holder = [1]

        def on_page(canvas, doc):
            _decorate_page_with_theme(canvas, doc, modo)

        frame = Frame(
            MARGIN, BOT_PAD,
            w - 2 * MARGIN, h - TOP_PAD - BOT_PAD,
            id="main",
            leftPadding=0, rightPadding=0,
            topPadding=0, bottomPadding=0,
        )
        doc.addPageTemplates([
            PageTemplate(id="dark", frames=[frame], onPage=on_page)
        ])

        styles    = self._styles(modo)
        content_w = w - 2 * MARGIN
        flowables = self._build_story(
            sales, total_ventas, total_ingresos,
            fecha_desde, fecha_hasta, chart_data,
            styles, content_w, modo,
            mostrar_resumen_periodo,
            mostrar_resumen_dia,
            mostrar_resumen_mes,
            mostrar_resumen_categoria,
            mostrar_resumen_productos,
            mostrar_detalle_ventas,
        )

        # Pass 1: contar páginas
        from reportlab.platypus import SimpleDocTemplate
        count_buf = BytesIO()
        count_doc = BaseDocTemplate(
            count_buf, pagesize=A4,
            rightMargin=MARGIN, leftMargin=MARGIN,
            topMargin=TOP_PAD, bottomMargin=BOT_PAD,
        )
        count_frame = Frame(
            MARGIN, BOT_PAD,
            w - 2 * MARGIN, h - TOP_PAD - BOT_PAD,
            id="main",
            leftPadding=0, rightPadding=0,
            topPadding=0, bottomPadding=0,
        )
        count_doc.addPageTemplates([PageTemplate(id="count", frames=[count_frame])])

        flowables_count = self._build_story(
            sales, total_ventas, total_ingresos,
            fecha_desde, fecha_hasta, chart_data,
            styles, content_w, modo,
        )
        count_doc.build(flowables_count)
        page_count_holder[0] = count_doc.page
        count_buf.close()

        # Pass 2: render real con total de páginas correcto
        doc.build(flowables)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

    def _build_story(
        self,
        sales, total_ventas, total_ingresos,
        fecha_desde, fecha_hasta, chart_data,
        styles, content_w, modo: str = "dark",
        mostrar_resumen_periodo: bool = True,
        mostrar_resumen_dia: bool = True,
        mostrar_resumen_mes: bool = False,
        mostrar_resumen_categoria: bool = True,
        mostrar_resumen_productos: bool = True,
        mostrar_detalle_ventas: bool = True,
    ) -> list:
        many_rows = len(sales) > 20
        elements  = []

        # Título + período
        elements.append(Spacer(1, 0.3 * cm))
        elements.append(Paragraph("Reporte de Ventas", styles["title"]))
        elements.append(Spacer(1, 0.1 * cm))
        elements.append(Paragraph(self._format_periodo(fecha_desde, fecha_hasta), styles["subtitle"]))
        elements.append(Spacer(1, 0.35 * cm))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=GREEN_BASE, spaceAfter=0.4 * cm))

        # Calcular totales incluyendo desglose de ofertas
        total_productos = 0
        for sale in sales:
            for item in sale.items:
                if item.oferta_id and item.oferta_productos_snapshot:
                    for prod in item.oferta_productos_snapshot:
                        total_productos += prod.cantidad * item.cantidad
                else:
                    total_productos += item.cantidad

        # KPIs
        if mostrar_resumen_periodo:
            elements.append(Paragraph("Resumen del Período", styles["section"]))
            elements.append(Spacer(1, 0.15 * cm))
            elements.append(self._kpi_table(total_ventas, total_ingresos, total_productos, content_w, modo))
            elements.append(Spacer(1, 0.5 * cm))

        # Resumen por Día
        if mostrar_resumen_dia:
            elements.append(Paragraph("Resumen por Día", styles["section"]))
            elements.append(Spacer(1, 0.15 * cm))
            elements.append(self._daily_summary_table(sales, styles, content_w, modo))
            elements.append(Spacer(1, 0.5 * cm))

        # Resumen por Mes
        if mostrar_resumen_mes:
            elements.append(Paragraph("Resumen por Mes", styles["section"]))
            elements.append(Spacer(1, 0.15 * cm))
            elements.append(self._monthly_summary_table(sales, styles, content_w, modo))
            elements.append(Spacer(1, 0.5 * cm))

        """
        # Gráfico
        if len(chart_data) > 1:
            chart_h   = 4.5 * cm if many_rows else 6.5 * cm
            chart_img = self._build_chart(chart_data, compact=many_rows)
            if chart_img:
                elements.append(Image(chart_img, width=content_w, height=chart_h))
                elements.append(Spacer(1, 0.5 * cm))
        """

        # Tabla de resumen por categoría
        if mostrar_resumen_categoria:
            elements.append(Paragraph("Resumen por Categoría", styles["section"]))
            elements.append(Spacer(1, 0.25 * cm))
            elements.append(self._category_summary_table(sales, styles, content_w))
            elements.append(Spacer(1, 0.5 * cm))

        # Tabla de agrupado
        if mostrar_resumen_productos:
            elements.append(Paragraph("Resumen de Productos Vendidos", styles["section"]))
            elements.append(Spacer(1, 0.25 * cm))
            elements.append(self._grouped_items_table(sales, styles, content_w))
            elements.append(Spacer(1, 0.5 * cm))

        # Tabla de detalle
        if mostrar_detalle_ventas:
            elements.append(Paragraph("Detalle de Ventas", styles["section"]))
            elements.append(Spacer(1, 0.25 * cm))
            elements.append(self._sales_table(sales, styles, content_w))

        return elements

    # ── Estilos ───────────────────────────────────────────────────────────────

    def _styles(self, mode: str = "dark") -> dict:
        colors_ = get_theme_colors(mode)
        base = getSampleStyleSheet()

        def ps(name, **kw) -> ParagraphStyle:
            return ParagraphStyle(name, parent=base["Normal"], **kw)

        return {
            "title": ps(
                "rpt_title", fontName="Helvetica-Bold", fontSize=20,
                textColor=colors_["TEXT_H1"], leading=24,
            ),
            "subtitle": ps(
                "rpt_sub", fontName="Helvetica", fontSize=9,
                textColor=colors_["TEXT_MUTED"],
            ),
            "section": ps(
                "rpt_section", fontName="Helvetica-Bold", fontSize=10,
                textColor=colors_["TEXT_H1"] if mode == "light" else colors_["GREEN_BASE"],
                leading=13,
            ),
            "kpi_val": ps(
                "rpt_kval", fontName="Helvetica-Bold", fontSize=16,
                textColor=colors_["TEXT_H1"] if mode == "light" else colors_["GREEN_BASE"],
                alignment=TA_CENTER, leading=19,
            ),
            "kpi_lbl": ps(
                "rpt_klbl", fontName="Helvetica", fontSize=7,
                textColor=colors_["TEXT_MUTED"], alignment=TA_CENTER,
            ),
            "th": ps(
                "rpt_th", fontName="Helvetica-Bold", fontSize=7.5,
                textColor=colors_["TEXT_BODY"] if mode == "light" else colors_["GREEN_BASE"],
                alignment=TA_CENTER,
            ),
            "td": ps(
                "rpt_td", fontName="Helvetica", fontSize=7.5,
                textColor=colors_["TEXT_BODY"], alignment=TA_CENTER, leading=10,
            ),
            "td_item": ps(
                "rpt_td_item", fontName="Helvetica", fontSize=7,
                textColor=colors_["TEXT_BODY"], alignment=TA_LEFT, leading=9,
            ),
            "td_money": ps(
                "rpt_money", fontName="Helvetica-Bold", fontSize=7.5,
                textColor=colors_["GREEN_BASE"], alignment=TA_RIGHT, leading=10,
            ),
            # ── Nuevos estilos para filas de resumen en _sales_table ──────────
            "td_summary_label": ps(
                "rpt_sum_lbl", fontName="Helvetica-Bold", fontSize=7.5,
                textColor=colors_["TEXT_MUTED"], alignment=TA_RIGHT, leading=10,
            ),
            "td_summary_total": ps(
                "rpt_sum_tot", fontName="Helvetica-Bold", fontSize=8,
                textColor=colors_["GREEN_BASE"], alignment=TA_RIGHT, leading=10,
            ),
        }

    # ── KPI cards ────────────────────────────────────────────────────────────

    def _kpi_table(
        self,
        total_ventas: int,
        total_ingresos: Decimal,
        total_productos: int,
        content_w: float,
        modo: str,
    ) -> Table:
        import inspect
        caller = inspect.stack()[1].function
        s = self._styles(modo)
        colors_ = get_theme_colors(modo)

        def card(label: str, value: str) -> list:
            return [Paragraph(value, s["kpi_val"]), Paragraph(label, s["kpi_lbl"])]

        data = [[
            card("Total de Ventas",    str(total_ventas)),
            card("Productos Vendidos", str(total_productos)),
            card("Ingresos Totales",   f"${float(total_ingresos):,.2f}"),
        ]]

        cw       = content_w / 3
        t        = Table(data, colWidths=[cw, cw, cw], rowHeights=[1.4 * cm])
        bg_color = colors_["BG_RAISED"] if modo == "dark" else colors_["BG_MAIN"]
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), bg_color),
            ("LINEABOVE",     (0, 0), (0, 0),   2.5, colors_["GREEN_BASE"]),
            ("LINEABOVE",     (1, 0), (1, 0),   2.5, colors_["GREEN_BASE"]),
            ("LINEABOVE",     (2, 0), (2, 0),   2.5, colors_["GREEN_BASE"]),
            ("LINEAFTER",     (0, 0), (1, 0),   0.5, colors_["BORDER_MAIN"]),
            ("BOX",           (0, 0), (-1, -1), 1,   colors_["BORDER_MAIN"]),
            ("LEFTPADDING",   (0, 0), (-1, -1), 10),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
            ("TOPPADDING",    (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ]))
        return t

    def _category_summary_table(self, sales: List[Sale], styles: dict, content_w: float) -> Table:
        """Agrupa cantidades vendidas por categoría, desglosando ofertas."""
        from collections import defaultdict

        categories: dict = defaultdict(int)

        for sale in sales:
            for item in sale.items:
                es_oferta = item.oferta_id is not None
                if es_oferta and item.oferta_productos_snapshot:
                    for prod in item.oferta_productos_snapshot:
                        cat = prod.categoria_nombre or "Sin Categoría"
                        categories[cat] += prod.cantidad * item.cantidad
                else:
                    cat = item.item_categoria or "Sin Categoría"
                    categories[cat] += item.cantidad

        sorted_cats = sorted(categories.items(), key=lambda x: x[1], reverse=True)

        headers = [
            Paragraph("Categoría",        styles["th"]),
            Paragraph("Cantidad Vendida", styles["th"]),
        ]
        rows = [headers]

        for cat_name, cantidad in sorted_cats:
            rows.append([
                Paragraph(cat_name,    styles["td_item"]),
                Paragraph(str(cantidad), styles["td"]),
            ])

        col_widths = [content_w * r for r in (0.60, 0.40)]
        t = Table(rows, colWidths=col_widths, rowHeights=None, repeatRows=1)

        modo    = "light" if styles["title"].textColor == THEMES["light"]["TEXT_H1"] else "dark"
        colors_ = get_theme_colors(modo)
        t.setStyle(TableStyle([
            ("BACKGROUND",     (0, 0), (-1, 0),  colors_["BG_RAISED"]),
            ("LINEBELOW",      (0, 0), (-1, 0),  1.5, colors_["GREEN_BASE"]),
            ("TOPPADDING",     (0, 0), (-1, 0),  8),
            ("BOTTOMPADDING",  (0, 0), (-1, 0),  8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors_["BG_MAIN"], colors_["BG_SECOND"]]),
            ("TOPPADDING",     (0, 1), (-1, -1), 4),
            ("BOTTOMPADDING",  (0, 1), (-1, -1), 4),
            ("LINEBELOW",      (0, 1), (-1, -2), 0.3, colors_["BORDER_SUB"]),
            ("BOX",            (0, 0), (-1, -1), 1,   colors_["BORDER_MAIN"]),
            ("LINEAFTER",      (0, 0), (0, -1),  0.5, colors_["BORDER_MAIN"]),
            ("LINEAFTER",      (1, 0), (1, -1),  0.5, colors_["BORDER_MAIN"]),
            ("ALIGN",          (0, 0), (-1, -1), "CENTER"),
            ("ALIGN",          (0, 1), (0, -1),  "LEFT"),
            ("ALIGN",          (1, 1), (1, -1),  "RIGHT"),
            ("VALIGN",         (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING",    (0, 0), (-1, -1), 6),
            ("RIGHTPADDING",   (0, 0), (-1, -1), 8),
        ]))
        return t

    def _grouped_items_table(self, sales: List[Sale], styles: dict, content_w: float) -> Table:
        """Agrupa ítems vendidos por producto, desglosando los que están dentro de ofertas."""
        from collections import defaultdict

        grouped: dict = defaultdict(lambda: {"nombre": "", "categoria": "", "cantidad": 0})

        for sale in sales:
            for item in sale.items:
                es_oferta = item.oferta_id is not None
                if es_oferta and item.oferta_productos_snapshot:
                    for prod in item.oferta_productos_snapshot:
                        key = f"{prod.producto_nombre}:{prod.categoria_nombre}"
                        grouped[key]["nombre"]    = prod.producto_nombre
                        grouped[key]["categoria"] = prod.categoria_nombre or "-"
                        grouped[key]["cantidad"] += prod.cantidad * item.cantidad
                else:
                    key = f"{item.item_nombre}:{item.item_categoria}"
                    grouped[key]["nombre"]    = item.item_nombre
                    grouped[key]["categoria"] = item.item_categoria
                    grouped[key]["cantidad"] += item.cantidad

        sorted_items = sorted(grouped.items(), key=lambda x: x[1]["cantidad"], reverse=True)

        headers = [
            Paragraph("Producto",         styles["th"]),
            Paragraph("Categoría",        styles["th"]),
            Paragraph("Cantidad Vendida", styles["th"]),
        ]
        rows = [headers]

        for key, data in sorted_items:
            rows.append([
                Paragraph(data["nombre"],    styles["td_item"]),
                Paragraph(data["categoria"], styles["td"]),
                Paragraph(str(data["cantidad"]), styles["td"]),
            ])

        col_widths = [content_w * r for r in (0.45, 0.30, 0.25)]
        t = Table(rows, colWidths=col_widths, rowHeights=None, repeatRows=1)

        modo    = "light" if styles["title"].textColor == THEMES["light"]["TEXT_H1"] else "dark"
        colors_ = get_theme_colors(modo)
        t.setStyle(TableStyle([
            ("BACKGROUND",     (0, 0), (-1, 0),  colors_["BG_RAISED"]),
            ("LINEBELOW",      (0, 0), (-1, 0),  1.5, colors_["GREEN_BASE"]),
            ("TOPPADDING",     (0, 0), (-1, 0),  8),
            ("BOTTOMPADDING",  (0, 0), (-1, 0),  8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors_["BG_MAIN"], colors_["BG_SECOND"]]),
            ("TOPPADDING",     (0, 1), (-1, -1), 4),
            ("BOTTOMPADDING",  (0, 1), (-1, -1), 4),
            ("LINEBELOW",      (0, 1), (-1, -2), 0.3, colors_["BORDER_SUB"]),
            ("BOX",            (0, 0), (-1, -1), 1,   colors_["BORDER_MAIN"]),
            ("LINEAFTER",      (0, 0), (0, -1),  0.5, colors_["BORDER_MAIN"]),
            ("LINEAFTER",      (1, 0), (1, -1),  0.5, colors_["BORDER_MAIN"]),
            ("LINEAFTER",      (2, 0), (2, -1),  0.5, colors_["BORDER_MAIN"]),
            ("ALIGN",          (0, 0), (-1, -1), "CENTER"),
            ("ALIGN",          (0, 1), (0, -1),  "LEFT"),
            ("ALIGN",          (2, 1), (2, -1),  "RIGHT"),
            ("VALIGN",         (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING",    (0, 0), (-1, -1), 6),
            ("RIGHTPADDING",   (0, 0), (-1, -1), 8),
        ]))
        return t

    def _daily_summary_table(self, sales: List[Sale], styles: dict, content_w: float, modo: str) -> Table:
        from collections import defaultdict
        import datetime as dt_mod

        daily = defaultdict(lambda: {"ventas": 0, "productos": 0, "ingresos": Decimal("0")})
        for sale in sales:
            day = (sale.fecha_creacion - dt_mod.timedelta(hours=6)).date()
            daily[day]["ventas"]   += 1
            daily[day]["ingresos"] += sale.total
            for item in sale.items:
                if item.oferta_id and item.oferta_productos_snapshot:
                    for prod in item.oferta_productos_snapshot:
                        daily[day]["productos"] += prod.cantidad * item.cantidad
                else:
                    daily[day]["productos"] += item.cantidad

        sorted_days = sorted(daily.items())
        headers = [
            Paragraph("Fecha",             styles["th"]),
            Paragraph("Total de Ventas",   styles["th"]),
            Paragraph("Productos Vendidos", styles["th"]),
            Paragraph("Ingresos Totales",  styles["th"]),
        ]
        rows = [headers]
        for day, data in sorted_days:
            rows.append([
                Paragraph(day.strftime("%d/%m/%Y"),         styles["td"]),
                Paragraph(str(data["ventas"]),              styles["td"]),
                Paragraph(str(data["productos"]),           styles["td"]),
                Paragraph(f"${float(data['ingresos']):,.2f}", styles["td_money"]),
            ])

        col_widths = [content_w * r for r in (0.18, 0.22, 0.30, 0.30)]
        colors_    = get_theme_colors(modo)
        t = Table(rows, colWidths=col_widths, rowHeights=None, repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND",     (0, 0), (-1, 0),  colors_["BG_RAISED"]),
            ("LINEBELOW",      (0, 0), (-1, 0),  1.5, colors_["GREEN_BASE"]),
            ("TOPPADDING",     (0, 0), (-1, 0),  8),
            ("BOTTOMPADDING",  (0, 0), (-1, 0),  8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors_["BG_MAIN"], colors_["BG_SECOND"]]),
            ("TOPPADDING",     (0, 1), (-1, -1), 4),
            ("BOTTOMPADDING",  (0, 1), (-1, -1), 4),
            ("LINEBELOW",      (0, 1), (-1, -2), 0.3, colors_["BORDER_SUB"]),
            ("BOX",            (0, 0), (-1, -1), 1,   colors_["BORDER_MAIN"]),
            ("LINEAFTER",      (0, 0), (0, -1),  0.5, colors_["BORDER_MAIN"]),
            ("LINEAFTER",      (1, 0), (1, -1),  0.5, colors_["BORDER_MAIN"]),
            ("LINEAFTER",      (2, 0), (2, -1),  0.5, colors_["BORDER_MAIN"]),
            ("LINEAFTER",      (3, 0), (3, -1),  0.5, colors_["BORDER_MAIN"]),
            ("ALIGN",          (0, 0), (-1, -1), "CENTER"),
            ("ALIGN",          (0, 1), (0, -1),  "LEFT"),
            ("ALIGN",          (3, 1), (3, -1),  "RIGHT"),
            ("VALIGN",         (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING",    (0, 0), (-1, -1), 6),
            ("RIGHTPADDING",   (0, 0), (-1, -1), 8),
        ]))
        return t

    def _monthly_summary_table(self, sales: List[Sale], styles: dict, content_w: float, modo: str) -> Table:
        from collections import defaultdict
        import datetime as dt_mod

        MONTH_NAMES = [
            "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
            "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
        ]
        monthly = defaultdict(lambda: {"ventas": 0, "productos": 0, "ingresos": Decimal("0")})
        for sale in sales:
            m = (sale.fecha_creacion - dt_mod.timedelta(hours=6)).month
            monthly[m]["ventas"]   += 1
            monthly[m]["ingresos"] += sale.total
            for item in sale.items:
                if item.oferta_id and item.oferta_productos_snapshot:
                    for prod in item.oferta_productos_snapshot:
                        monthly[m]["productos"] += prod.cantidad * item.cantidad
                else:
                    monthly[m]["productos"] += item.cantidad

        sorted_months = sorted(monthly.keys())
        headers = [
            Paragraph("Mes",                styles["th"]),
            Paragraph("Total de Ventas",    styles["th"]),
            Paragraph("Productos Vendidos", styles["th"]),
            Paragraph("Ingresos Totales",   styles["th"]),
        ]
        rows = [headers]
        for m in sorted_months:
            data = monthly[m]
            rows.append([
                Paragraph(MONTH_NAMES[m - 1],                styles["td_item"]),
                Paragraph(str(data["ventas"]),               styles["td"]),
                Paragraph(str(data["productos"]),            styles["td"]),
                Paragraph(f"${float(data['ingresos']):,.2f}", styles["td_money"]),
            ])

        col_widths = [content_w * r for r in (0.25, 0.22, 0.28, 0.25)]
        colors_    = get_theme_colors(modo)
        t = Table(rows, colWidths=col_widths, rowHeights=None, repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND",     (0, 0), (-1, 0),  colors_["BG_RAISED"]),
            ("LINEBELOW",      (0, 0), (-1, 0),  1.5, colors_["GREEN_BASE"]),
            ("TOPPADDING",     (0, 0), (-1, 0),  8),
            ("BOTTOMPADDING",  (0, 0), (-1, 0),  8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors_["BG_MAIN"], colors_["BG_SECOND"]]),
            ("TOPPADDING",     (0, 1), (-1, -1), 4),
            ("BOTTOMPADDING",  (0, 1), (-1, -1), 4),
            ("LINEBELOW",      (0, 1), (-1, -2), 0.3, colors_["BORDER_SUB"]),
            ("BOX",            (0, 0), (-1, -1), 1,   colors_["BORDER_MAIN"]),
            ("LINEAFTER",      (0, 0), (0, -1),  0.5, colors_["BORDER_MAIN"]),
            ("LINEAFTER",      (1, 0), (1, -1),  0.5, colors_["BORDER_MAIN"]),
            ("LINEAFTER",      (2, 0), (2, -1),  0.5, colors_["BORDER_MAIN"]),
            ("ALIGN",          (0, 0), (-1, -1), "CENTER"),
            ("ALIGN",          (0, 1), (0, -1),  "LEFT"),
            ("ALIGN",          (3, 1), (3, -1),  "RIGHT"),
            ("VALIGN",         (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING",    (0, 0), (-1, -1), 6),
            ("RIGHTPADDING",   (0, 0), (-1, -1), 8),
        ]))
        return t

    # ── Tabla de ventas ──────────────────────────────────────────────────────

    def _sales_table(self, sales: List[Sale], styles: dict, content_w: float) -> Table:
        """
        Tabla de detalle de ventas.

        Cambio clave respecto a la versión anterior:
        Las filas de SUBTOTAL, RECARGO y TOTAL hacen SPAN sobre las dos últimas
        columnas ("Precio Unit." + "Total"), mostrando el label y el monto
        concatenados en una sola celda alineada a la derecha.  Esto evita el
        aspecto "desconectado" que se producía cuando el label aparecía en la
        columna "Precio Unit." y el monto en "Total" con cuatro columnas vacías
        a la izquierda.

        Colores de fondo:
          • subtotal / recargo → GREEN_SUBTLE  (verde muy suave)
          • total              → GREEN_TOTAL   (verde más marcado)
        """
        modo    = "light" if styles["title"].textColor == THEMES["light"]["TEXT_H1"] else "dark"
        colors_ = get_theme_colors(modo)

        headers = [
            Paragraph("Fecha y Hora", styles["th"]),
            Paragraph("Nº Orden",     styles["th"]),
            Paragraph("Ítem",         styles["th"]),
            Paragraph("Categoría",    styles["th"]),
            Paragraph("Cantidad",     styles["th"]),
            Paragraph("Precio Unit.", styles["th"]),
            Paragraph("Total",        styles["th"]),
        ]
        rows         = [headers]
        span_cmds    = []          # comandos SPAN acumulados
        summary_rows = []          # índices de filas subtotal / recargo
        total_rows   = []          # índices de filas TOTAL
        sale_sep_rows = []         # índices de última fila de cada venta (para separador)

        for sale in sales:
            fecha_str      = sale.fecha_creacion.strftime("%d/%m/%y %H:%M")
            sale_start_row = len(rows)
            first_row      = True

            for item in sale.items:
                es_oferta = item.oferta_id is not None

                if es_oferta and item.oferta_productos_snapshot:
                    # ── fila cabecera de oferta ───────────────────────────────
                    rows.append([
                        Paragraph(fecha_str if first_row else "",          styles["td"]),
                        Paragraph(sale.numero_orden if first_row else "",  styles["td"]),
                        Paragraph(f" {item.item_nombre}",                  styles["td_item"]),
                        Paragraph("OFERTA",                                styles["td"]),
                        Paragraph(str(item.cantidad),                      styles["td"]),
                        Paragraph(f"${float(item.precio_unitario):,.2f}",  styles["td"]),
                        Paragraph(f"${float(item.subtotal):,.2f}",         styles["td_money"]),
                    ])
                    first_row = False

                    # ── filas de desglose de la oferta ────────────────────────
                    for prod in item.oferta_productos_snapshot:
                        rows.append([
                            Paragraph("", styles["td"]),
                            Paragraph("", styles["td"]),
                            Paragraph(prod.producto_nombre,              styles["td_item"]),
                            Paragraph(prod.categoria_nombre or "-",      styles["td"]),
                            Paragraph(str(prod.cantidad * item.cantidad), styles["td"]),
                            Paragraph("", styles["td"]),
                            Paragraph("", styles["td_money"]),
                        ])

                else:
                    # ── fila de ítem regular ──────────────────────────────────
                    rows.append([
                        Paragraph(fecha_str if first_row else "",         styles["td"]),
                        Paragraph(sale.numero_orden if first_row else "", styles["td"]),
                        Paragraph(item.item_nombre,                       styles["td_item"]),
                        Paragraph(item.item_categoria,                    styles["td"]),
                        Paragraph(str(item.cantidad),                     styles["td"]),
                        Paragraph(f"${float(item.precio_unitario):,.2f}", styles["td"]),
                        Paragraph(f"${float(item.subtotal):,.2f}",        styles["td_money"]),
                    ])
                    first_row = False

            # ── fila SUBTOTAL ─────────────────────────────────────────────────
            subtotal     = sum(i.subtotal for i in sale.items)
            sub_idx      = len(rows)
            rows.append([
                Paragraph("", styles["td"]),
                Paragraph("", styles["td"]),
                Paragraph("", styles["td_item"]),
                Paragraph("", styles["td"]),
                Paragraph("", styles["td"]),
                Paragraph(
                    f"Subtotal    ${float(subtotal):,.2f}",
                    styles["td_summary_label"],
                ),
                Paragraph("", styles["td"]),   # celda absorbida por el SPAN
            ])
            span_cmds.append(("SPAN", (5, sub_idx), (6, sub_idx)))
            summary_rows.append(sub_idx)

            # ── fila RECARGO (condicional) ────────────────────────────────────
            if sale.porcentaje_recargo is not None and sale.monto_recargo is not None:
                rec_idx = len(rows)
                rows.append([
                    Paragraph("", styles["td"]),
                    Paragraph("", styles["td"]),
                    Paragraph("", styles["td_item"]),
                    Paragraph("", styles["td"]),
                    Paragraph("", styles["td"]),
                    Paragraph(
                        f"Recargo ({float(sale.porcentaje_recargo):.0f}%)    "
                        f"${float(sale.monto_recargo):,.2f}",
                        styles["td_summary_label"],
                    ),
                    Paragraph("", styles["td"]),
                ])
                span_cmds.append(("SPAN", (5, rec_idx), (6, rec_idx)))
                summary_rows.append(rec_idx)

            # ── fila TOTAL ────────────────────────────────────────────────────
            tot_idx = len(rows)
            rows.append([
                Paragraph("", styles["td"]),
                Paragraph("", styles["td"]),
                Paragraph("", styles["td_item"]),
                Paragraph("", styles["td"]),
                Paragraph("", styles["td"]),
                Paragraph(
                    f"TOTAL    ${float(sale.total):,.2f}",
                    styles["td_summary_total"],
                ),
                Paragraph("", styles["td"]),
            ])
            span_cmds.append(("SPAN", (5, tot_idx), (6, tot_idx)))
            summary_rows.append(tot_idx)
            total_rows.append(tot_idx)
            sale_sep_rows.append(tot_idx)

        # ── anchos de columna ─────────────────────────────────────────────────
        col_widths = [content_w * r for r in (0.14, 0.18, 0.22, 0.13, 0.08, 0.13, 0.12)]

        # ── estilos base ──────────────────────────────────────────────────────
        table_styles = [
            ("BACKGROUND",     (0, 0), (-1, 0),  colors_["BG_RAISED"]),
            ("LINEBELOW",      (0, 0), (-1, 0),  1.5, colors_["GREEN_BASE"]),
            ("TOPPADDING",     (0, 0), (-1, 0),  8),
            ("BOTTOMPADDING",  (0, 0), (-1, 0),  8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors_["BG_MAIN"], colors_["BG_SECOND"]]),
            ("TOPPADDING",     (0, 1), (-1, -1), 4),
            ("BOTTOMPADDING",  (0, 1), (-1, -1), 4),
            ("LINEBELOW",      (0, 1), (-1, -2), 0.3, colors_["BORDER_SUB"]),
            ("BOX",            (0, 0), (-1, -1), 1,   colors_["BORDER_MAIN"]),
            # Líneas verticales
            ("LINEAFTER",      (0, 0), (0, -1),  0.5, colors_["BORDER_MAIN"]),
            ("LINEAFTER",      (1, 0), (1, -1),  0.5, colors_["BORDER_MAIN"]),
            ("LINEAFTER",      (2, 0), (2, -1),  0.5, colors_["BORDER_MAIN"]),
            ("LINEAFTER",      (3, 0), (3, -1),  0.5, colors_["BORDER_MAIN"]),
            ("LINEAFTER",      (4, 0), (4, -1),  0.5, colors_["BORDER_MAIN"]),
            ("LINEAFTER",      (5, 0), (5, -1),  0.5, colors_["BORDER_MAIN"]),
            # Alineación general
            ("ALIGN",          (0, 0), (-1, -1), "CENTER"),
            ("ALIGN",          (2, 1), (2, -1),  "LEFT"),
            ("ALIGN",          (5, 1), (6, -1),  "RIGHT"),
            ("VALIGN",         (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING",    (0, 0), (-1, -1), 6),
            ("RIGHTPADDING",   (0, 0), (-1, -1), 8),
        ]

        # Separador grueso entre ventas
        table_styles += [
            ("LINEBELOW", (0, r), (-1, r), 1.0, colors_["BORDER_MAIN"])
            for r in sale_sep_rows
        ]

        # Añadir los comandos SPAN
        table_styles += span_cmds

        # ── estilos filas SUBTOTAL / RECARGO ──────────────────────────────────
        for r in summary_rows:
            table_styles += [
                ("BACKGROUND",    (0, r), (-1, r), colors_["GREEN_SUBTLE"]),
                ("TOPPADDING",    (0, r), (-1, r), 5),
                ("BOTTOMPADDING", (0, r), (-1, r), 5),
                # Suprimir divisor vertical dentro del SPAN (cols 5-6)
                ("LINEAFTER",     (4, r), (4, r),  0.5, colors_["BORDER_MAIN"]),
                ("LINEAFTER",     (5, r), (5, r),  0,   colors_["BG_MAIN"]),
            ]

        # ── estilos fila TOTAL ────────────────────────────────────────────────
        for r in total_rows:
            table_styles += [
                ("BACKGROUND",    (0, r), (-1, r), colors_["GREEN_TOTAL"]),
                ("LINEABOVE",     (0, r), (-1, r), 1.0, colors_["GREEN_BASE"]),
                ("LINEBELOW",     (0, r), (-1, r), 1.5, colors_["GREEN_BASE"]),
                ("TOPPADDING",    (0, r), (-1, r), 6),
                ("BOTTOMPADDING", (0, r), (-1, r), 6),
            ]

        t = Table(rows, colWidths=col_widths, rowHeights=None, repeatRows=1)
        t.setStyle(TableStyle(table_styles))
        return t

    # ── Gráfico dark ─────────────────────────────────────────────────────────

    def _build_chart(
        self,
        chart_data: List[Tuple[datetime, Decimal]],
        compact: bool = False,
    ) -> Optional[BytesIO]:
        try:
            dates  = [d for d, _ in chart_data]
            values = [float(v) for _, v in chart_data]

            fig, ax = plt.subplots(figsize=(11, 3.0 if compact else 3.8), dpi=130)
            fig.patch.set_facecolor("#1a1a1a")
            ax.set_facecolor("#0d0d0d")

            ax.fill_between(dates, values, alpha=0.18, color="#22c55e", zorder=2)
            ax.plot(
                dates, values,
                marker="o", linewidth=2, markersize=4,
                color="#22c55e",
                markerfacecolor="#0d0d0d",
                markeredgecolor="#4ade80",
                markeredgewidth=1.5,
                zorder=3,
            )

            if len(dates) <= 14 and not compact:
                for x, y in zip(dates, values):
                    ax.annotate(
                        f"${y:,.0f}", (x, y),
                        textcoords="offset points", xytext=(0, 7),
                        ha="center", fontsize=6, color="#4ade80",
                    )

            ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))

            if len(dates) <= 7:
                ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))
                ax.xaxis.set_major_locator(mdates.DayLocator())
            elif len(dates) <= 31:
                ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))
                ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(dates) // 7)))
            else:
                ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%Y"))
                ax.xaxis.set_major_locator(mdates.MonthLocator())

            plt.xticks(rotation=25, ha="right", fontsize=7, color="#888888")
            plt.yticks(fontsize=7, color="#888888")
            ax.tick_params(colors="#888888", which="both")

            for spine in ax.spines.values():
                spine.set_edgecolor("#2a2a2a")
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)

            ax.grid(True, linestyle="--", linewidth=0.4, color="#2a2a2a", zorder=1)
            ax.set_xlabel("Fecha", fontsize=7.5, color="#888888", labelpad=4)
            ax.set_ylabel("Ingresos ($)", fontsize=7.5, color="#888888", labelpad=4)

            plt.tight_layout(pad=1.0)

            buf = BytesIO()
            FigureCanvasAgg(fig).print_png(buf)
            plt.close(fig)
            buf.seek(0)
            return buf

        except Exception as e:
            self.logger.error("Error gráfico", error=str(e))
            return None

    # ── Utilidades ────────────────────────────────────────────────────────────

    def _format_periodo(self, desde: Optional[date], hasta: Optional[date]) -> str:
        if desde and hasta:
            return f"Período:  {desde.strftime('%d/%m/%Y')}  →  {hasta.strftime('%d/%m/%Y')}"
        if desde:
            return f"Desde: {desde.strftime('%d/%m/%Y')}"
        if hasta:
            return f"Hasta: {hasta.strftime('%d/%m/%Y')}"
        return "Período: Histórico completo"

    # ── Reporte de Costos ─────────────────────────────────────────────────────

    async def generate_costs_report(
        self,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
        modo: str = "light",
        mostrar_resumen_periodo: bool = True,
        mostrar_resumen_categoria: bool = True,
        mostrar_resumen_mes: bool = False,
        mostrar_detalle_costos: bool = True,
    ) -> ReportResult:
        try:
            self.logger.info("Generando reporte de costos", fecha_desde=fecha_desde, fecha_hasta=fecha_hasta)
            async with self.uow as uow:
                expenses = await uow.expense_repo.list_for_report(
                    fecha_desde=fecha_desde,
                    fecha_hasta=fecha_hasta,
                )
            if not expenses:
                return ReportResult(error="No hay costos en el período seleccionado", status_code=404)
            total_costos = sum(e.monto for e in expenses)
            cantidad     = len(expenses)
            pdf_bytes    = await self._create_costs_pdf(
                expenses, total_costos, cantidad,
                fecha_desde, fecha_hasta, modo,
                mostrar_resumen_periodo, mostrar_resumen_categoria,
                mostrar_resumen_mes, mostrar_detalle_costos,
            )
            self.logger.info("Reporte de costos OK", cantidad=cantidad)
            return ReportResult(pdf_bytes=pdf_bytes)
        except Exception as e:
            self.logger.error("Error reporte costos", error=str(e), exc_info=True)
            return ReportResult(error=str(e), status_code=500)

    async def _create_costs_pdf(
        self,
        expenses: List[Expense],
        total_costos,
        cantidad: int,
        fecha_desde: Optional[date],
        fecha_hasta: Optional[date],
        modo: str = "light",
        mostrar_resumen_periodo: bool = True,
        mostrar_resumen_categoria: bool = True,
        mostrar_resumen_mes: bool = False,
        mostrar_detalle_costos: bool = True,
    ) -> bytes:
        buffer  = BytesIO()
        w, h    = A4
        TOP_PAD = HEADER_H + 0.5 * cm
        BOT_PAD = FOOTER_H + 0.5 * cm

        def on_page(canvas, doc):
            _decorate_page_with_theme(canvas, doc, modo, report_title="Reporte de Costos")

        doc = BaseDocTemplate(
            buffer, pagesize=A4,
            rightMargin=MARGIN, leftMargin=MARGIN,
            topMargin=TOP_PAD, bottomMargin=BOT_PAD,
        )
        frame = Frame(
            MARGIN, BOT_PAD, w - 2 * MARGIN, h - TOP_PAD - BOT_PAD,
            id="main", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
        )
        doc.addPageTemplates([PageTemplate(id="costs", frames=[frame], onPage=on_page)])
        styles    = self._styles(modo)
        content_w = w - 2 * MARGIN

        # Pass 1: contar páginas
        count_buf = BytesIO()
        count_doc = BaseDocTemplate(
            count_buf, pagesize=A4,
            rightMargin=MARGIN, leftMargin=MARGIN,
            topMargin=TOP_PAD, bottomMargin=BOT_PAD,
        )
        count_frame = Frame(
            MARGIN, BOT_PAD, w - 2 * MARGIN, h - TOP_PAD - BOT_PAD,
            id="main", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
        )
        count_doc.addPageTemplates([PageTemplate(id="count", frames=[count_frame])])
        flowables_count = self._build_costs_story(
            expenses, total_costos, cantidad, fecha_desde, fecha_hasta,
            styles, content_w, modo,
        )
        count_doc.build(flowables_count)
        count_buf.close()

        # Pass 2: render real
        flowables = self._build_costs_story(
            expenses, total_costos, cantidad, fecha_desde, fecha_hasta,
            styles, content_w, modo,
            mostrar_resumen_periodo, mostrar_resumen_categoria,
            mostrar_resumen_mes, mostrar_detalle_costos,
        )
        doc.build(flowables)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

    def _build_costs_story(
        self,
        expenses: List[Expense],
        total_costos,
        cantidad: int,
        fecha_desde: Optional[date],
        fecha_hasta: Optional[date],
        styles: dict,
        content_w: float,
        modo: str = "light",
        mostrar_resumen_periodo: bool = True,
        mostrar_resumen_categoria: bool = True,
        mostrar_resumen_mes: bool = False,
        mostrar_detalle_costos: bool = True,
    ) -> list:
        elements: list = []
        elements.append(Spacer(1, 0.3 * cm))
        elements.append(Paragraph("Reporte de Costos", styles["title"]))
        elements.append(Spacer(1, 0.1 * cm))
        elements.append(Paragraph(self._format_periodo(fecha_desde, fecha_hasta), styles["subtitle"]))
        elements.append(Spacer(1, 0.35 * cm))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=GREEN_BASE, spaceAfter=0.4 * cm))

        if mostrar_resumen_periodo:
            elements.append(Paragraph("Resumen del Período", styles["section"]))
            elements.append(Spacer(1, 0.15 * cm))
            elements.append(self._costs_kpi_table(total_costos, cantidad, expenses, content_w, modo))
            elements.append(Spacer(1, 0.5 * cm))

        if mostrar_resumen_mes:
            elements.append(Paragraph("Resumen por Mes", styles["section"]))
            elements.append(Spacer(1, 0.25 * cm))
            elements.append(self._costs_month_table(expenses, styles, content_w, modo))
            elements.append(Spacer(1, 0.5 * cm))

        if mostrar_resumen_categoria:
            elements.append(Paragraph("Resumen por Categoría", styles["section"]))
            elements.append(Spacer(1, 0.25 * cm))
            elements.append(self._costs_category_table(expenses, styles, content_w, modo))
            elements.append(Spacer(1, 0.5 * cm))

        if mostrar_detalle_costos:
            elements.append(Paragraph("Detalle de Costos", styles["section"]))
            elements.append(Spacer(1, 0.25 * cm))
            elements.append(self._costs_detail_table(expenses, styles, content_w, modo))

        return elements

    def _costs_kpi_table(
        self,
        total_costos,
        cantidad: int,
        expenses: List[Expense],
        content_w: float,
        modo: str,
    ) -> Table:
        from collections import defaultdict
        s       = self._styles(modo)
        colors_ = get_theme_colors(modo)
        cat_totals: dict = defaultdict(float)
        for e in expenses:
            if e.categoria_gasto:
                cat = (
                    e.categoria_gasto.padre_categoria.nombre
                    if e.categoria_gasto.padre_categoria
                    else e.categoria_gasto.nombre
                )
            else:
                cat = "Sin Categoría"
            cat_totals[cat] += float(e.monto)
        top_cat = max(cat_totals, key=lambda k: cat_totals[k]) if cat_totals else "-"

        def card(label: str, value: str) -> list:
            return [Paragraph(value, s["kpi_val"]), Paragraph(label, s["kpi_lbl"])]

        data = [[
            card("Total de Costos", f"${float(total_costos):,.2f}"),
            card("Registros",       str(cantidad)),
            card("Mayor Categoría", top_cat),
        ]]
        cw       = content_w / 3
        t        = Table(data, colWidths=[cw, cw, cw], rowHeights=[1.4 * cm])
        bg_color = colors_["BG_RAISED"] if modo == "dark" else colors_["BG_MAIN"]
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), bg_color),
            ("LINEABOVE",     (0, 0), (0, 0),   2.5, colors_["GREEN_BASE"]),
            ("LINEABOVE",     (1, 0), (1, 0),   2.5, colors_["GREEN_BASE"]),
            ("LINEABOVE",     (2, 0), (2, 0),   2.5, colors_["GREEN_BASE"]),
            ("LINEAFTER",     (0, 0), (1, 0),   0.5, colors_["BORDER_MAIN"]),
            ("BOX",           (0, 0), (-1, -1), 1,   colors_["BORDER_MAIN"]),
            ("LEFTPADDING",   (0, 0), (-1, -1), 10),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
            ("TOPPADDING",    (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ]))
        return t

    def _costs_category_table(
        self, expenses: List[Expense], styles: dict, content_w: float, modo: str
    ) -> Table:
        from collections import defaultdict

        group_totals: dict = defaultdict(float)
        for e in expenses:
            if e.categoria_gasto:
                if e.categoria_gasto.padre_categoria:
                    parent = e.categoria_gasto.padre_categoria.nombre
                    sub    = e.categoria_gasto.nombre
                else:
                    parent = e.categoria_gasto.nombre
                    sub    = "-"
            else:
                parent = "Sin Categoría"
                sub    = "-"
            group_totals[(parent, sub)] += float(e.monto)

        total         = sum(group_totals.values()) or 1
        sorted_groups = sorted(group_totals.items(), key=lambda x: x[1], reverse=True)

        headers = [
            Paragraph("Categoría",    styles["th"]),
            Paragraph("Subcategoría", styles["th"]),
            Paragraph("Total",        styles["th"]),
            Paragraph("% del Total",  styles["th"]),
        ]
        rows = [headers]
        for (parent_name, sub_name), monto in sorted_groups:
            pct = monto / total * 100
            rows.append([
                Paragraph(parent_name,      styles["td_item"]),
                Paragraph(sub_name,         styles["td"]),
                Paragraph(f"${monto:,.2f}", styles["td_money"]),
                Paragraph(f"{pct:.1f}%",    styles["td"]),
            ])

        col_widths = [content_w * r for r in (0.35, 0.28, 0.22, 0.15)]
        colors_    = get_theme_colors(modo)
        t = Table(rows, colWidths=col_widths, rowHeights=None, repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND",     (0, 0), (-1, 0),  colors_["BG_RAISED"]),
            ("LINEBELOW",      (0, 0), (-1, 0),  1.5, colors_["GREEN_BASE"]),
            ("TOPPADDING",     (0, 0), (-1, 0),  8),
            ("BOTTOMPADDING",  (0, 0), (-1, 0),  8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors_["BG_MAIN"], colors_["BG_SECOND"]]),
            ("TOPPADDING",     (0, 1), (-1, -1), 4),
            ("BOTTOMPADDING",  (0, 1), (-1, -1), 4),
            ("LINEBELOW",      (0, 1), (-1, -2), 0.3, colors_["BORDER_SUB"]),
            ("BOX",            (0, 0), (-1, -1), 1,   colors_["BORDER_MAIN"]),
            ("LINEAFTER",      (0, 0), (0, -1),  0.5, colors_["BORDER_MAIN"]),
            ("LINEAFTER",      (1, 0), (1, -1),  0.5, colors_["BORDER_MAIN"]),
            ("LINEAFTER",      (2, 0), (2, -1),  0.5, colors_["BORDER_MAIN"]),
            ("ALIGN",          (0, 0), (-1, -1), "CENTER"),
            ("ALIGN",          (0, 1), (0, -1),  "LEFT"),
            ("ALIGN",          (1, 1), (1, -1),  "LEFT"),
            ("ALIGN",          (2, 1), (2, -1),  "RIGHT"),
            ("VALIGN",         (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING",    (0, 0), (-1, -1), 6),
            ("RIGHTPADDING",   (0, 0), (-1, -1), 8),
        ]))
        return t

    def _costs_month_table(
        self, expenses: List[Expense], styles: dict, content_w: float, modo: str
    ) -> Table:
        from collections import defaultdict

        MONTH_NAMES = [
            "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
            "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
        ]
        month_totals: dict = defaultdict(float)
        month_counts: dict = defaultdict(int)
        for e in expenses:
            m = e.fecha_pago.month
            month_totals[m] += float(e.monto)
            month_counts[m] += 1

        total         = sum(month_totals.values()) or 1
        sorted_months = sorted(month_totals.keys())

        headers = [
            Paragraph("Mes",         styles["th"]),
            Paragraph("Registros",   styles["th"]),
            Paragraph("Total",       styles["th"]),
            Paragraph("% del Total", styles["th"]),
        ]
        rows = [headers]
        for m in sorted_months:
            monto = month_totals[m]
            pct   = monto / total * 100
            rows.append([
                Paragraph(MONTH_NAMES[m - 1],   styles["td_item"]),
                Paragraph(str(month_counts[m]), styles["td"]),
                Paragraph(f"${monto:,.2f}",     styles["td_money"]),
                Paragraph(f"{pct:.1f}%",        styles["td"]),
            ])

        col_widths = [content_w * r for r in (0.35, 0.18, 0.30, 0.17)]
        colors_    = get_theme_colors(modo)
        t = Table(rows, colWidths=col_widths, rowHeights=None, repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND",     (0, 0), (-1, 0),  colors_["BG_RAISED"]),
            ("LINEBELOW",      (0, 0), (-1, 0),  1.5, colors_["GREEN_BASE"]),
            ("TOPPADDING",     (0, 0), (-1, 0),  8),
            ("BOTTOMPADDING",  (0, 0), (-1, 0),  8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors_["BG_MAIN"], colors_["BG_SECOND"]]),
            ("TOPPADDING",     (0, 1), (-1, -1), 4),
            ("BOTTOMPADDING",  (0, 1), (-1, -1), 4),
            ("LINEBELOW",      (0, 1), (-1, -2), 0.3, colors_["BORDER_SUB"]),
            ("BOX",            (0, 0), (-1, -1), 1,   colors_["BORDER_MAIN"]),
            ("LINEAFTER",      (0, 0), (0, -1),  0.5, colors_["BORDER_MAIN"]),
            ("LINEAFTER",      (1, 0), (1, -1),  0.5, colors_["BORDER_MAIN"]),
            ("LINEAFTER",      (2, 0), (2, -1),  0.5, colors_["BORDER_MAIN"]),
            ("ALIGN",          (0, 0), (-1, -1), "CENTER"),
            ("ALIGN",          (0, 1), (0, -1),  "LEFT"),
            ("ALIGN",          (1, 1), (1, -1),  "CENTER"),
            ("ALIGN",          (2, 1), (2, -1),  "RIGHT"),
            ("VALIGN",         (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING",    (0, 0), (-1, -1), 6),
            ("RIGHTPADDING",   (0, 0), (-1, -1), 8),
        ]))
        return t

    def _costs_detail_table(
        self, expenses: List[Expense], styles: dict, content_w: float, modo: str
    ) -> Table:
        headers = [
            Paragraph("Fecha",        styles["th"]),
            Paragraph("Categoría",    styles["th"]),
            Paragraph("Subcategoría", styles["th"]),
            Paragraph("Descripción",  styles["th"]),
            Paragraph("Monto",        styles["th"]),
        ]
        rows = [headers]
        for e in expenses:
            if e.categoria_gasto:
                if e.categoria_gasto.padre_categoria:
                    parent = e.categoria_gasto.padre_categoria.nombre
                    sub    = e.categoria_gasto.nombre
                else:
                    parent = e.categoria_gasto.nombre
                    sub    = "-"
            else:
                parent = "Sin Categoría"
                sub    = "-"
            desc = e.descripcion or "-"
            rows.append([
                Paragraph(e.fecha_pago.strftime("%d/%m/%Y"), styles["td"]),
                Paragraph(parent,                            styles["td"]),
                Paragraph(sub,                               styles["td"]),
                Paragraph(desc,                              styles["td_item"]),
                Paragraph(f"${float(e.monto):,.2f}",         styles["td_money"]),
            ])

        col_widths = [content_w * r for r in (0.12, 0.19, 0.19, 0.33, 0.17)]
        colors_    = get_theme_colors(modo)
        t = Table(rows, colWidths=col_widths, rowHeights=None, repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND",     (0, 0), (-1, 0),  colors_["BG_RAISED"]),
            ("LINEBELOW",      (0, 0), (-1, 0),  1.5, colors_["GREEN_BASE"]),
            ("TOPPADDING",     (0, 0), (-1, 0),  8),
            ("BOTTOMPADDING",  (0, 0), (-1, 0),  8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors_["BG_MAIN"], colors_["BG_SECOND"]]),
            ("TOPPADDING",     (0, 1), (-1, -1), 4),
            ("BOTTOMPADDING",  (0, 1), (-1, -1), 4),
            ("LINEBELOW",      (0, 1), (-1, -2), 0.3, colors_["BORDER_SUB"]),
            ("BOX",            (0, 0), (-1, -1), 1,   colors_["BORDER_MAIN"]),
            ("LINEAFTER",      (0, 0), (0, -1),  0.5, colors_["BORDER_MAIN"]),
            ("LINEAFTER",      (1, 0), (1, -1),  0.5, colors_["BORDER_MAIN"]),
            ("LINEAFTER",      (2, 0), (2, -1),  0.5, colors_["BORDER_MAIN"]),
            ("LINEAFTER",      (3, 0), (3, -1),  0.5, colors_["BORDER_MAIN"]),
            ("ALIGN",          (0, 0), (-1, -1), "CENTER"),
            ("ALIGN",          (3, 1), (3, -1),  "LEFT"),
            ("ALIGN",          (4, 1), (4, -1),  "RIGHT"),
            ("VALIGN",         (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING",    (0, 0), (-1, -1), 6),
            ("RIGHTPADDING",   (0, 0), (-1, -1), 8),
        ]))
        return t

    # ── Reporte de Balance ────────────────────────────────────────────────────

    async def generate_general_report(
        self,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
        modo: str = "light",
        mostrar_resumen_periodo: bool = True,
        mostrar_resumen_mes: bool = False,
        mostrar_resumen_categoria_ventas: bool = True,
        mostrar_resumen_productos: bool = True,
        mostrar_resumen_categoria_costos: bool = True,
    ) -> ReportResult:
        try:
            self.logger.info("Generando reporte general", fecha_desde=fecha_desde, fecha_hasta=fecha_hasta)
            async with self.uow as uow:
                from datetime import time, timedelta
                fecha_desde_dt = (
                    datetime.combine(fecha_desde, time.min) + timedelta(hours=6)
                    if fecha_desde else None
                )
                fecha_hasta_dt = (
                    datetime.combine(fecha_hasta, time.max) + timedelta(hours=6)
                    if fecha_hasta else None
                )
                sales = await uow.sale_repo.list(
                    skip=0, limit=10_000,
                    fecha_desde=fecha_desde_dt,
                    fecha_hasta=fecha_hasta_dt,
                )
                expenses = await uow.expense_repo.list_for_report(
                    fecha_desde=fecha_desde,
                    fecha_hasta=fecha_hasta,
                )
            if not sales and not expenses:
                return ReportResult(error="No hay datos en el período seleccionado", status_code=404)
            total_ingresos = sum(s.total for s in sales) if sales else Decimal("0")
            total_gastos   = sum(e.monto for e in expenses) if expenses else Decimal("0")
            resultado_neto = total_ingresos - total_gastos
            margen_neto    = float(resultado_neto / total_ingresos * 100) if total_ingresos > 0 else 0.0
            pdf_bytes = await self._create_general_pdf(
                sales, expenses,
                total_ingresos, total_gastos, resultado_neto, margen_neto,
                fecha_desde, fecha_hasta, modo,
                mostrar_resumen_periodo, mostrar_resumen_mes,
                mostrar_resumen_categoria_ventas, mostrar_resumen_productos,
                mostrar_resumen_categoria_costos,
            )
            self.logger.info("Reporte general OK")
            return ReportResult(pdf_bytes=pdf_bytes)
        except Exception as e:
            self.logger.error("Error reporte general", error=str(e), exc_info=True)
            return ReportResult(error=str(e), status_code=500)

    async def _create_general_pdf(
        self,
        sales: List[Sale],
        expenses: List[Expense],
        total_ingresos: Decimal,
        total_gastos: Decimal,
        resultado_neto: Decimal,
        margen_neto: float,
        fecha_desde: Optional[date],
        fecha_hasta: Optional[date],
        modo: str = "light",
        mostrar_resumen_periodo: bool = True,
        mostrar_resumen_mes: bool = False,
        mostrar_resumen_categoria_ventas: bool = True,
        mostrar_resumen_productos: bool = True,
        mostrar_resumen_categoria_costos: bool = True,
    ) -> bytes:
        buffer  = BytesIO()
        w, h    = A4
        TOP_PAD = HEADER_H + 0.5 * cm
        BOT_PAD = FOOTER_H + 0.5 * cm

        def on_page(canvas, doc):
            _decorate_page_with_theme(canvas, doc, modo, report_title="Reporte General")

        styles    = self._styles(modo)
        content_w = w - 2 * MARGIN

        # Pass 1: contar páginas
        count_buf = BytesIO()
        count_doc = BaseDocTemplate(
            count_buf, pagesize=A4,
            rightMargin=MARGIN, leftMargin=MARGIN,
            topMargin=TOP_PAD, bottomMargin=BOT_PAD,
        )
        count_frame = Frame(
            MARGIN, BOT_PAD, w - 2 * MARGIN, h - TOP_PAD - BOT_PAD,
            id="main", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
        )
        count_doc.addPageTemplates([PageTemplate(id="count_gen", frames=[count_frame])])
        flowables_count = self._build_general_story(
            sales, expenses,
            total_ingresos, total_gastos, resultado_neto, margen_neto,
            fecha_desde, fecha_hasta, styles, content_w, modo,
            mostrar_resumen_periodo, mostrar_resumen_mes,
            mostrar_resumen_categoria_ventas, mostrar_resumen_productos,
            mostrar_resumen_categoria_costos,
        )
        count_doc.build(flowables_count)
        total_pages = count_doc.page
        count_buf.close()

        # Pass 2: render real
        def on_page_real(canvas, doc):
            doc._pagecount = total_pages
            _decorate_page_with_theme(canvas, doc, modo, report_title="Reporte General")

        doc2 = BaseDocTemplate(
            buffer, pagesize=A4,
            rightMargin=MARGIN, leftMargin=MARGIN,
            topMargin=TOP_PAD, bottomMargin=BOT_PAD,
        )
        frame2 = Frame(
            MARGIN, BOT_PAD, w - 2 * MARGIN, h - TOP_PAD - BOT_PAD,
            id="main", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
        )
        doc2.addPageTemplates([PageTemplate(id="general2", frames=[frame2], onPage=on_page_real)])
        flowables_real = self._build_general_story(
            sales, expenses,
            total_ingresos, total_gastos, resultado_neto, margen_neto,
            fecha_desde, fecha_hasta, styles, content_w, modo,
            mostrar_resumen_periodo, mostrar_resumen_mes,
            mostrar_resumen_categoria_ventas, mostrar_resumen_productos,
            mostrar_resumen_categoria_costos,
        )
        doc2.build(flowables_real)
        buffer.seek(0)
        return buffer.read()

    def _build_general_story(
        self,
        sales: List[Sale],
        expenses: List[Expense],
        total_ingresos: Decimal,
        total_gastos: Decimal,
        resultado_neto: Decimal,
        margen_neto: float,
        fecha_desde: Optional[date],
        fecha_hasta: Optional[date],
        styles: dict,
        content_w: float,
        modo: str,
        mostrar_resumen_periodo: bool = True,
        mostrar_resumen_mes: bool = False,
        mostrar_resumen_categoria_ventas: bool = True,
        mostrar_resumen_productos: bool = True,
        mostrar_resumen_categoria_costos: bool = True,
    ) -> list:
        elements: list = []
        elements.append(Spacer(1, 0.4 * cm))
        elements.append(Paragraph("Reporte General", styles["title"]))
        elements.append(Paragraph(self._format_periodo(fecha_desde, fecha_hasta), styles["subtitle"]))
        elements.append(Spacer(1, 0.5 * cm))
        elements.append(HRFlowable(width=content_w, thickness=0.5, color=styles["section"].textColor))
        elements.append(Spacer(1, 0.4 * cm))

        if mostrar_resumen_periodo:
            elements.append(Paragraph("Resumen del período", styles["section"]))
            elements.append(Spacer(1, 0.25 * cm))
            elements.append(self._general_kpi_table(
                total_ingresos, total_gastos, resultado_neto, margen_neto, content_w, modo,
            ))
            elements.append(Spacer(1, 0.5 * cm))

        if mostrar_resumen_mes:
            elements.append(Paragraph("Resumen por mes", styles["section"]))
            elements.append(Spacer(1, 0.25 * cm))
            elements.append(self._general_month_table(sales, expenses, styles, content_w, modo))
            elements.append(Spacer(1, 0.5 * cm))

        if mostrar_resumen_categoria_ventas:
            elements.append(Paragraph("Ventas por categoría", styles["section"]))
            elements.append(Spacer(1, 0.25 * cm))
            elements.append(self._category_summary_table(sales, styles, content_w))
            elements.append(Spacer(1, 0.5 * cm))

        if mostrar_resumen_productos:
            elements.append(Paragraph("Productos vendidos", styles["section"]))
            elements.append(Spacer(1, 0.25 * cm))
            elements.append(self._grouped_items_table(sales, styles, content_w))
            elements.append(Spacer(1, 0.5 * cm))

        if mostrar_resumen_categoria_costos:
            elements.append(Paragraph("Costos por categoría", styles["section"]))
            elements.append(Spacer(1, 0.25 * cm))
            elements.append(self._costs_category_table(expenses, styles, content_w, modo))
            elements.append(Spacer(1, 0.5 * cm))

        return elements

    def _general_kpi_table(
        self,
        total_ingresos: Decimal,
        total_gastos: Decimal,
        resultado_neto: Decimal,
        margen_neto: float,
        content_w: float,
        modo: str,
    ) -> Table:
        s        = self._styles(modo)
        colors_  = get_theme_colors(modo)
        red_color    = colors.HexColor("#ef4444")
        pos_color    = colors_["GREEN_BASE"]
        neto_color   = pos_color if resultado_neto >= 0 else red_color
        margen_color = pos_color if margen_neto    >= 0 else red_color

        kpi_val_sm = ParagraphStyle(
            "rpt_kval_bal",
            parent=s["kpi_val"],
            fontSize=13,
            leading=16,
        )

        def card(label: str, value: str, val_color=None) -> list:
            base = ParagraphStyle(
                "rpt_kval_bal_col",
                parent=kpi_val_sm,
                textColor=val_color,
            ) if val_color is not None else kpi_val_sm
            return [Paragraph(value, base), Paragraph(label, s["kpi_lbl"])]

        data = [[
            card("Ingresos Totales", f"${float(total_ingresos):,.2f}"),
            card("Gastos Totales",   f"${float(total_gastos):,.2f}"),
            card("Resultado Neto",   f"${float(resultado_neto):,.2f}", neto_color),
            card("Margen Neto",      f"{margen_neto:.1f}%",           margen_color),
        ]]
        cw       = content_w / 4
        t        = Table(data, colWidths=[cw, cw, cw, cw], rowHeights=[1.4 * cm])
        bg_color = colors_["BG_RAISED"] if modo == "dark" else colors_["BG_MAIN"]
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), bg_color),
            ("LINEABOVE",     (0, 0), (0, 0),   2.5, colors_["GREEN_BASE"]),
            ("LINEABOVE",     (1, 0), (1, 0),   2.5, colors_["GREEN_BASE"]),
            ("LINEABOVE",     (2, 0), (2, 0),   2.5, colors_["GREEN_BASE"]),
            ("LINEABOVE",     (3, 0), (3, 0),   2.5, colors_["GREEN_BASE"]),
            ("LINEAFTER",     (0, 0), (2, 0),   0.5, colors_["BORDER_MAIN"]),
            ("BOX",           (0, 0), (-1, -1), 1,   colors_["BORDER_MAIN"]),
            ("LEFTPADDING",   (0, 0), (-1, -1), 8),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
            ("TOPPADDING",    (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ]))
        return t

    def _general_month_table(
        self,
        sales: List[Sale],
        expenses: List[Expense],
        styles: dict,
        content_w: float,
        modo: str,
    ) -> Table:
        from collections import defaultdict
        import datetime as dt_mod

        MONTH_NAMES = [
            "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
            "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
        ]
        monthly_sales: dict = defaultdict(lambda: Decimal("0"))
        for s in sales:
            m = (s.fecha_creacion - dt_mod.timedelta(hours=6)).month
            monthly_sales[m] += s.total
        monthly_exp: dict = defaultdict(lambda: Decimal("0"))
        for e in expenses:
            m = e.fecha_pago.month
            monthly_exp[m] += e.monto

        all_months = sorted(set(monthly_sales.keys()) | set(monthly_exp.keys()))
        colors_    = get_theme_colors(modo)
        red_color   = colors.HexColor("#ef4444")
        green_color = colors_["GREEN_BASE"]

        headers = [
            Paragraph("Mes",       styles["th"]),
            Paragraph("Ingresos",  styles["th"]),
            Paragraph("Gastos",    styles["th"]),
            Paragraph("Resultado", styles["th"]),
            Paragraph("Margen %",  styles["th"]),
        ]
        rows = [headers]
        for m in all_months:
            ingresos  = float(monthly_sales.get(m, Decimal("0")))
            gastos    = float(monthly_exp.get(m, Decimal("0")))
            resultado = ingresos - gastos
            margen    = (resultado / ingresos * 100) if ingresos > 0 else 0.0
            res_color    = green_color if resultado >= 0 else red_color
            margen_color = green_color if margen    >= 0 else red_color
            res_style = ParagraphStyle(
                "rpt_bal_res", parent=styles["td_money"], textColor=res_color, alignment=TA_RIGHT,
            )
            margen_style = ParagraphStyle(
                "rpt_bal_mg", parent=styles["td_money"], textColor=margen_color, alignment=TA_RIGHT,
            )
            rows.append([
                Paragraph(MONTH_NAMES[m - 1],  styles["td_item"]),
                Paragraph(f"${ingresos:,.2f}",  styles["td_money"]),
                Paragraph(f"${gastos:,.2f}",    styles["td_money"]),
                Paragraph(f"${resultado:,.2f}", res_style),
                Paragraph(f"{margen:.1f}%",     margen_style),
            ])

        col_widths = [content_w * r for r in (0.22, 0.21, 0.21, 0.22, 0.14)]
        t = Table(rows, colWidths=col_widths, rowHeights=None, repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND",     (0, 0), (-1, 0),  colors_["BG_RAISED"]),
            ("LINEBELOW",      (0, 0), (-1, 0),  1.5, colors_["GREEN_BASE"]),
            ("TOPPADDING",     (0, 0), (-1, 0),  8),
            ("BOTTOMPADDING",  (0, 0), (-1, 0),  8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors_["BG_MAIN"], colors_["BG_SECOND"]]),
            ("TOPPADDING",     (0, 1), (-1, -1), 4),
            ("BOTTOMPADDING",  (0, 1), (-1, -1), 4),
            ("LINEBELOW",      (0, 1), (-1, -2), 0.3, colors_["BORDER_SUB"]),
            ("BOX",            (0, 0), (-1, -1), 1,   colors_["BORDER_MAIN"]),
            ("LINEAFTER",      (0, 0), (0, -1),  0.5, colors_["BORDER_MAIN"]),
            ("LINEAFTER",      (1, 0), (1, -1),  0.5, colors_["BORDER_MAIN"]),
            ("LINEAFTER",      (2, 0), (2, -1),  0.5, colors_["BORDER_MAIN"]),
            ("LINEAFTER",      (3, 0), (3, -1),  0.5, colors_["BORDER_MAIN"]),
            ("ALIGN",          (0, 0), (-1, -1), "CENTER"),
            ("ALIGN",          (0, 1), (0, -1),  "LEFT"),
            ("ALIGN",          (1, 1), (4, -1),  "RIGHT"),
            ("VALIGN",         (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING",    (0, 0), (-1, -1), 6),
            ("RIGHTPADDING",   (0, 0), (-1, -1), 8),
        ]))
        return t


# ─────────────────────────────────────────────────────────────────────────────
#  Helper de decoración (fuera de la clase para evitar self en callback)
# ─────────────────────────────────────────────────────────────────────────────
def _decorate_page_with_total(canvas: rl_canvas.Canvas, doc, total_pages: int):
    """Dibuja fondo + header + footer. Llamado por onPage ANTES del contenido."""
    canvas.saveState()
    w, h = A4

    # Fondo
    canvas.setFillColor(BG_MAIN)
    canvas.rect(0, 0, w, h, fill=1, stroke=0)

    # Header
    canvas.setFillColor(BG_SECOND)
    canvas.rect(0, h - HEADER_H, w, HEADER_H, fill=1, stroke=0)
    canvas.setStrokeColor(GREEN_BASE)
    canvas.setLineWidth(1.5)
    canvas.line(0, h - HEADER_H, w, h - HEADER_H)

    # Logo
    logo_y     = h - HEADER_H + 0.18 * cm
    logo_h_px  = HEADER_H - 0.36 * cm
    logo_max_w = 4 * cm
    logo_drawn = False
    if os.path.isfile(LOGO_PATH):
        try:
            canvas.drawImage(
                LOGO_PATH, 2 * cm, logo_y,
                height=logo_h_px, width=logo_max_w,
                preserveAspectRatio=True, anchor="w",
                mask="auto",
            )
            logo_drawn = True
        except Exception:
            pass
    if not logo_drawn:
        canvas.setFillColor(GREEN_BASE)
        canvas.setFont("Helvetica-Bold", 11)
        canvas.drawString(2 * cm, h - HEADER_H / 2 - 0.15 * cm, "PizzaFiori")

    # Fecha
    canvas.setFillColor(TEXT_MUTED)
    canvas.setFont("Helvetica", 7.5)
    canvas.drawRightString(
        w - 2 * cm,
        h - HEADER_H / 2 - 0.15 * cm,
        f"Generado: {datetime.now().strftime('%d/%m/%Y  %H:%M')}",
    )

    # Footer
    canvas.setFillColor(BG_SECOND)
    canvas.rect(0, 0, w, FOOTER_H, fill=1, stroke=0)
    canvas.setStrokeColor(BORDER_MAIN)
    canvas.setLineWidth(0.5)
    canvas.line(0, FOOTER_H, w, FOOTER_H)
    canvas.setFillColor(TEXT_MUTED)
    canvas.setFont("Helvetica", 7)
    canvas.drawCentredString(
        w / 2,
        FOOTER_H / 2 - 0.1 * cm,
        f"PizzaFiori  •  Reporte de Ventas  •  Página {doc.page} de {total_pages}",
    )

    canvas.restoreState()