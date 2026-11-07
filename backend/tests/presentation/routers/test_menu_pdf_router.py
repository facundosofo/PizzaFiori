from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.infrastructure.unit_of_work import get_uow
from app.main import app


def _menu_uow(products):
    category = SimpleNamespace(id=1, nombre="Pizzas", activo=True)
    return SimpleNamespace(
        product_category_repo=SimpleNamespace(
            list_by_active=AsyncMock(return_value=[category])
        ),
        product_repo=SimpleNamespace(list=AsyncMock(return_value=products)),
        offer_repo=SimpleNamespace(list=AsyncMock(return_value=[])),
    )


@pytest.mark.asyncio
async def test_download_menu_pdf_returns_generated_attachment(async_client, monkeypatch):
    product = SimpleNamespace(
        id=1,
        nombre="Muzzarella",
        categoria_id=1,
        activo=True,
        precios=[
            SimpleNamespace(cantidad=Decimal("1"), precio=Decimal("12000")),
        ],
    )
    unit = _menu_uow([product])

    async def override_get_uow():
        yield unit

    monkeypatch.setitem(
        app.dependency_overrides,
        get_uow,
        override_get_uow,
    )

    response = await async_client.get("/config/menu/pdf")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.headers["content-disposition"] == (
        'attachment; filename="menu-pizza-fiori.pdf"'
    )
    assert response.content.startswith(b"%PDF-")


@pytest.mark.asyncio
async def test_download_menu_pdf_returns_not_found_without_sellable_products(
    async_client, monkeypatch
):
    unit = _menu_uow([])

    async def override_get_uow():
        yield unit

    monkeypatch.setitem(
        app.dependency_overrides,
        get_uow,
        override_get_uow,
    )

    response = await async_client.get("/config/menu/pdf")

    assert response.status_code == 404
    assert "No hay productos activos" in response.json()["detail"]
