"""
Tests para los endpoints de gastos.
Verifica respuestas HTTP sin verificar mocks.
"""

import pytest
from httpx import AsyncClient
from unittest.mock import MagicMock
from datetime import date, datetime
from decimal import Decimal


def _build_expense_mock(**kwargs):
    """Build a mock expense for router responses."""
    defaults = {
        "id": 1,
        "categoria_gasto_id": 1,
        "descripcion": "Compra harina",
        "monto": 5000.0,
        "fecha_pago": date(2024, 6, 1),
        "activo": True,
        "fecha_creacion": datetime(2024, 6, 1),
        "fecha_actualizacion": datetime(2024, 6, 1),
        "categoria_gasto": None,
    }
    defaults.update(kwargs)
    m = MagicMock()
    for k, v in defaults.items():
        setattr(m, k, v)
    return m


# --- Tests de creación ---

@pytest.mark.asyncio
async def test_create_gasto_exitoso(async_client: AsyncClient, mock_expense_service):
    """Crear gasto con datos válidos retorna 201."""
    gasto = _build_expense_mock(id=1)
    mock_expense_service.create.return_value.error = None
    mock_expense_service.create.return_value.value = gasto

    payload = {
        "categoria_gasto_id": 1,
        "descripcion": "Compra harina",
        "monto": 5000.0,
        "fecha_pago": "2024-06-01",
    }

    response = await async_client.post("/gastos", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 1


@pytest.mark.asyncio
async def test_create_gasto_categoria_no_existe(async_client: AsyncClient, mock_expense_service):
    """Crear gasto con categoría inexistente retorna 404."""
    mock_expense_service.create.return_value.error = "Categoría no encontrada"
    mock_expense_service.create.return_value.status_code = 404
    mock_expense_service.create.return_value.value = None

    payload = {
        "categoria_gasto_id": 999,
        "monto": 5000.0,
        "fecha_pago": "2024-06-01",
    }

    response = await async_client.post("/gastos", json=payload)

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_gasto_monto_invalido(async_client: AsyncClient):
    """Crear gasto con monto negativo retorna 422."""
    payload = {
        "categoria_gasto_id": 1,
        "monto": -100,
        "fecha_pago": "2024-06-01",
    }

    response = await async_client.post("/gastos", json=payload)

    assert response.status_code == 422


# --- Tests de listado ---

@pytest.mark.asyncio
async def test_list_gastos(async_client: AsyncClient, mock_expense_service):
    """GET /gastos retorna lista de gastos."""
    gastos = [_build_expense_mock(id=1), _build_expense_mock(id=2)]
    mock_expense_service.list_all.return_value.error = None
    mock_expense_service.list_all.return_value.value = gastos
    mock_expense_service.list_by_filters.return_value.error = None
    mock_expense_service.list_by_filters.return_value.value = gastos

    response = await async_client.get("/gastos")

    assert response.status_code == 200


# --- Tests de get by id ---

@pytest.mark.asyncio
async def test_get_gasto_exitoso(async_client: AsyncClient, mock_expense_service):
    """GET /gastos/{id} retorna gasto."""
    gasto = _build_expense_mock(id=1)
    mock_expense_service.get_by_id.return_value.error = None
    mock_expense_service.get_by_id.return_value.value = gasto

    response = await async_client.get("/gastos/1")

    assert response.status_code == 200
    assert response.json()["id"] == 1


@pytest.mark.asyncio
async def test_get_gasto_no_encontrado(async_client: AsyncClient, mock_expense_service):
    """GET /gastos/{id} con ID inexistente retorna 404."""
    mock_expense_service.get_by_id.return_value.error = "Gasto no encontrado"
    mock_expense_service.get_by_id.return_value.status_code = 404
    mock_expense_service.get_by_id.return_value.value = None

    response = await async_client.get("/gastos/999")

    assert response.status_code == 404


# --- Tests de actualización ---

@pytest.mark.asyncio
async def test_update_gasto_exitoso(async_client: AsyncClient, mock_expense_service):
    """PUT /gastos/{id} actualiza gasto correctamente."""
    gasto = _build_expense_mock(id=1, monto=7000.0)
    mock_expense_service.update.return_value.error = None
    mock_expense_service.update.return_value.value = gasto

    response = await async_client.put(
        "/gastos/1",
        json={"monto": 7000.0},
    )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_update_gasto_no_encontrado(async_client: AsyncClient, mock_expense_service):
    """PUT /gastos/{id} con ID inexistente retorna 404."""
    mock_expense_service.update.return_value.error = "Gasto no encontrado"
    mock_expense_service.update.return_value.status_code = 404
    mock_expense_service.update.return_value.value = None

    response = await async_client.put(
        "/gastos/999",
        json={"monto": 100.0},
    )

    assert response.status_code == 404


# --- Tests de eliminación ---

@pytest.mark.asyncio
async def test_delete_gasto_exitoso(async_client: AsyncClient, mock_expense_service):
    """DELETE /gastos/{id} elimina gasto correctamente."""
    mock_expense_service.delete.return_value.error = None
    mock_expense_service.delete.return_value.value = True

    response = await async_client.delete("/gastos/1")

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_gasto_no_encontrado(async_client: AsyncClient, mock_expense_service):
    """DELETE /gastos/{id} con ID inexistente retorna 404."""
    mock_expense_service.delete.return_value.error = "Gasto no encontrado"
    mock_expense_service.delete.return_value.status_code = 404
    mock_expense_service.delete.return_value.value = None

    response = await async_client.delete("/gastos/999")

    assert response.status_code == 404
