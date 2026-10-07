import asyncio
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from app.application.report_service import ReportService


class DummyUoW:
    def __init__(self, sales, products=None):
        self.sale_repo = MagicMock()
        self.product_repo = MagicMock()
        async def list_sales(*args, **kwargs):
            return sales
        async def get_by_ids(ids):
            return products or []
        self.sale_repo.list = list_sales
        self.product_repo.get_by_ids = get_by_ids

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

    result = await service.generate_sales_report()

    assert result.error is None, f"Report generation failed: {result.error}"
    assert result.pdf_bytes is not None
