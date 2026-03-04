"""
Tests para los endpoints de categorías de gastos.
Verifica respuestas HTTP sin verificar mocks.
"""

import pytest
from httpx import AsyncClient
from unittest.mock import MagicMock
from datetime import datetime


def _build_expense_cat_mock(**kwargs):
    """Build a mock expense category for router responses."""
    defaults = {
        "id": 1,
        "nombre": "Insumos",
        "padre_id": None,
        "activo": True,
        "fecha_creacion": datetime(2024, 1, 1),
        "fecha_actualizacion": datetime(2024, 1, 1),
        "subcategorias": [],
    }
    defaults.update(kwargs)
    m = MagicMock()
    for k, v in defaults.items():
        setattr(m, k, v)
    return m


# --- Tests de creación ---

@pytest.mark.asyncio
async def test_create_categoria_exitoso(async_client: AsyncClient, mock_expense_category_service):
    """Crear categoría con datos válidos retorna 201."""
    cat = _build_expense_cat_mock(id=1, nombre="Insumos")
    mock_expense_category_service.create.return_value.error = None
    mock_expense_category_service.create.return_value.value = cat

    response = await async_client.post(
        "/gastos-categorias",
        json={"nombre": "Insumos"},
    )

    assert response.status_code == 201
    assert response.json()["nombre"] == "Insumos"


@pytest.mark.asyncio
async def test_create_categoria_con_padre(async_client: AsyncClient, mock_expense_category_service):
    """Crear subcategoría con padre válido retorna 201."""
    cat = _build_expense_cat_mock(id=2, nombre="Harina", padre_id=1)
    mock_expense_category_service.create.return_value.error = None
    mock_expense_category_service.create.return_value.value = cat

    response = await async_client.post(
        "/gastos-categorias",
        json={"nombre": "Harina", "padre_id": 1},
    )

    assert response.status_code == 201


@pytest.mark.asyncio
async def test_create_categoria_padre_invalido(async_client: AsyncClient, mock_expense_category_service):
    """Crear subcategoría con padre inexistente retorna 404."""
    mock_expense_category_service.create.return_value.error = "Categoría padre no encontrada"
    mock_expense_category_service.create.return_value.status_code = 404
    mock_expense_category_service.create.return_value.value = None

    response = await async_client.post(
        "/gastos-categorias",
        json={"nombre": "Sub", "padre_id": 999},
    )

    assert response.status_code == 404


# --- Tests de listado ---

@pytest.mark.asyncio
async def test_list_categorias(async_client: AsyncClient, mock_expense_category_service):
    """GET /gastos-categorias retorna lista."""
    cats = [
        _build_expense_cat_mock(id=1, nombre="Insumos"),
        _build_expense_cat_mock(id=2, nombre="Servicios"),
    ]
    mock_expense_category_service.list_all.return_value.error = None
    mock_expense_category_service.list_all.return_value.value = cats

    response = await async_client.get("/gastos-categorias")

    assert response.status_code == 200
    assert len(response.json()) == 2


@pytest.mark.asyncio
async def test_list_categorias_by_parent(async_client: AsyncClient, mock_expense_category_service):
    """GET /gastos-categorias?padre_id=1 retorna subcategorías."""
    cats = [_build_expense_cat_mock(id=2, nombre="Harina", padre_id=1)]
    mock_expense_category_service.list_by_parent.return_value.error = None
    mock_expense_category_service.list_by_parent.return_value.value = cats

    response = await async_client.get("/gastos-categorias?padre_id=1")

    assert response.status_code == 200


# --- Tests de get by id ---

@pytest.mark.asyncio
async def test_get_categoria(async_client: AsyncClient, mock_expense_category_service):
    """GET /gastos-categorias/{id} retorna categoría."""
    cat = _build_expense_cat_mock(id=1)
    mock_expense_category_service.get_by_id.return_value.error = None
    mock_expense_category_service.get_by_id.return_value.value = cat

    response = await async_client.get("/gastos-categorias/1")

    assert response.status_code == 200
    assert response.json()["id"] == 1


@pytest.mark.asyncio
async def test_get_categoria_not_found(async_client: AsyncClient, mock_expense_category_service):
    """GET /gastos-categorias/{id} inexistente retorna 404."""
    mock_expense_category_service.get_by_id.return_value.error = "Categoría de gasto no encontrada"
    mock_expense_category_service.get_by_id.return_value.status_code = 404
    mock_expense_category_service.get_by_id.return_value.value = None

    response = await async_client.get("/gastos-categorias/999")

    assert response.status_code == 404


# --- Tests de actualización ---

@pytest.mark.asyncio
async def test_update_categoria(async_client: AsyncClient, mock_expense_category_service):
    """PUT /gastos-categorias/{id} actualiza categoría."""
    cat = _build_expense_cat_mock(id=1, nombre="Insumos Actualizados")
    mock_expense_category_service.update.return_value.error = None
    mock_expense_category_service.update.return_value.value = cat

    response = await async_client.put(
        "/gastos-categorias/1",
        json={"nombre": "Insumos Actualizados"},
    )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_update_categoria_not_found(async_client: AsyncClient, mock_expense_category_service):
    """PUT /gastos-categorias/{id} inexistente retorna 404."""
    mock_expense_category_service.update.return_value.error = "Categoría de gasto no encontrada"
    mock_expense_category_service.update.return_value.status_code = 404
    mock_expense_category_service.update.return_value.value = None

    response = await async_client.put(
        "/gastos-categorias/999",
        json={"nombre": "Test"},
    )

    assert response.status_code == 404


# --- Tests de desactivar ---

@pytest.mark.asyncio
async def test_deactivate_categoria(async_client: AsyncClient, mock_expense_category_service):
    """PATCH /gastos-categorias/{id}/desactivar desactiva categoría."""
    cat = _build_expense_cat_mock(id=1, activo=False)
    mock_expense_category_service.delete.return_value.error = None
    mock_expense_category_service.delete.return_value.value = cat
    mock_expense_category_service.delete.return_value.status_code = 204

    response = await async_client.patch("/gastos-categorias/1/desactivar")

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_deactivate_categoria_not_found(async_client: AsyncClient, mock_expense_category_service):
    """PATCH /gastos-categorias/{id}/desactivar inexistente retorna 404."""
    mock_expense_category_service.delete.return_value.error = "Categoría de gasto no encontrada"
    mock_expense_category_service.delete.return_value.status_code = 404
    mock_expense_category_service.delete.return_value.value = None

    response = await async_client.patch("/gastos-categorias/999/desactivar")

    assert response.status_code == 404
