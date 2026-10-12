import asyncio
from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

import app.application.report_service as report_service_module
from app.application.report_service import ReportService


class DummyUoW:
    def __init__(self, sales, products=None, expenses=None):
        self.sale_repo = MagicMock()
        self.product_repo = MagicMock()
        self.expense_repo = MagicMock()
        self.sale_list_kwargs = None
        self.product_ids_requested = None
        self.expenses = expenses or []

        async def list_sales(*args, **kwargs):
            self.sale_list_kwargs = kwargs
            return sales

        async def get_by_ids(ids):
            self.product_ids_requested = ids
            return products or []

        async def list_expenses_for_report(*args, **kwargs):
            return self.expenses

        self.sale_repo.list = list_sales
        self.product_repo.get_by_ids = get_by_ids
        self.expense_repo.list_for_report = list_expenses_for_report

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


@pytest.mark.asyncio
async def test_generate_sales_report_smoke():
    # Build a minimal sale + item snapshot
    sale = MagicMock()
    sale.fecha_creacion = datetime.now()
    sale.numero_orden = "1"
    sale.total = Decimal("100.00")
    sale.porcentaje_recargo = None
    sale.monto_recargo = None

    item = MagicMock()
    item.oferta_id = None
    item.oferta_productos_snapshot = []
    item.cantidad = Decimal("1")
    item.precio_unitario = Decimal("100.00")
    item.subtotal = Decimal("100.00")
    item.item_categoria = "Empanadas"
    item.item_nombre = "Empanada de Carne"
    item.precio_cantidad = None
    item.producto_id = None

    sale.items = [item]

    uow = DummyUoW([sale], products=[])
    service = ReportService(uow)
    build_story = MagicMock(wraps=service._build_story)
    service._build_story = build_story

    result = await service.generate_sales_report()

    assert result.error is None, f"Report generation failed: {result.error}"
    assert result.pdf_bytes.startswith(b"%PDF")
    build_story.assert_called_once()


@pytest.mark.asyncio
async def test_generate_sales_report_skips_items_when_no_item_sections_are_selected():
    sale = SimpleNamespace(
        fecha_creacion=datetime.now(),
        total=Decimal("100.00"),
    )

    uow = DummyUoW([sale])
    service = ReportService(uow)

    result = await service.generate_sales_report(
        mostrar_resumen_periodo=False,
        mostrar_resumen_dia=False,
        mostrar_resumen_mes=False,
        mostrar_resumen_categoria=False,
        mostrar_resumen_productos=False,
        mostrar_detalle_ventas=False,
    )

    assert result.error is None, f"Report generation failed: {result.error}"
    assert result.pdf_bytes is not None
    assert uow.sale_list_kwargs["include_items"] is False
    assert uow.product_ids_requested is None


@pytest.mark.asyncio
async def test_generate_costs_report_smoke():
    expense = SimpleNamespace(monto=Decimal("25.00"))
    service = ReportService(DummyUoW([], expenses=[expense]))

    result = await service.generate_costs_report(
        mostrar_resumen_periodo=False,
        mostrar_resumen_categoria=False,
        mostrar_resumen_mes=False,
        mostrar_detalle_costos=False,
    )

    assert result.error is None, f"Report generation failed: {result.error}"
    assert result.pdf_bytes.startswith(b"%PDF")


@pytest.mark.asyncio
async def test_generate_general_report_without_sales_item_sections_smoke():
    expense = SimpleNamespace(monto=Decimal("25.00"))
    uow = DummyUoW([], expenses=[expense])
    service = ReportService(uow)

    result = await service.generate_general_report(
        mostrar_resumen_periodo=False,
        mostrar_resumen_mes=False,
        mostrar_resumen_categoria_ventas=False,
        mostrar_resumen_productos=False,
        mostrar_resumen_categoria_costos=False,
    )

    assert result.error is None, f"Report generation failed: {result.error}"
    assert result.pdf_bytes.startswith(b"%PDF")
    assert uow.sale_list_kwargs["include_items"] is False


@pytest.mark.asyncio
async def test_generate_sales_report_numbers_all_pages_in_single_render(monkeypatch):
    sales = []
    for sale_number in range(70):
        item = SimpleNamespace(
            oferta_id=None,
            oferta_productos_snapshot=[],
            cantidad=Decimal("1"),
            precio_unitario=Decimal("100.00"),
            subtotal=Decimal("100.00"),
            item_categoria="Empanadas",
            item_nombre="Empanada de Carne",
            precio_cantidad=None,
            producto_id=None,
        )
        sales.append(SimpleNamespace(
            fecha_creacion=datetime.now(),
            numero_orden=str(sale_number),
            total=Decimal("100.00"),
            porcentaje_recargo=None,
            monto_recargo=None,
            items=[item],
        ))

    original_draw_footer = report_service_module._draw_page_footer
    page_numbers = []

    def record_page_footer(canvas, mode, title, page_number, total_pages):
        page_numbers.append((page_number, total_pages))
        original_draw_footer(canvas, mode, title, page_number, total_pages)

    monkeypatch.setattr(report_service_module, "_draw_page_footer", record_page_footer)
    result = await ReportService(DummyUoW(sales)).generate_sales_report()

    assert result.error is None, f"Report generation failed: {result.error}"
    assert len(page_numbers) > 1
    total_pages = len(page_numbers)
    assert page_numbers == [
        (page_number, total_pages)
        for page_number in range(1, total_pages + 1)
    ]
