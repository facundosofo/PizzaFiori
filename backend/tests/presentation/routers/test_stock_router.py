"""
Tests para los endpoints de stock.
Verifica respuestas HTTP sin verificar mocks.
"""

import pytest
from httpx import AsyncClient
from unittest.mock import MagicMock
from datetime import datetime


# --- Tests de get all stocks ---

@pytest.mark.asyncio
async def test_get_all_stocks(async_client: AsyncClient, mock_stock_service):
    """GET /stock retorna lista de stock."""
    stocks = [
        {"categoria_id": 1, "categoria_nombre": "Pizza", "cantidad": 50,
         "umbral_amarillo": 10, "umbral_rojo": 5, "estado": "ok"},
        {"categoria_id": 2, "categoria_nombre": "Empanada", "cantidad": 0,
         "umbral_amarillo": None, "umbral_rojo": None, "estado": "sin_stock"},
    ]
    mock_stock_service.get_all_stocks.return_value.error = None
    mock_stock_service.get_all_stocks.return_value.value = stocks

    response = await async_client.get("/stock")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_get_all_stocks_error(async_client: AsyncClient, mock_stock_service):
    """GET /stock con error retorna 500."""
    mock_stock_service.get_all_stocks.return_value.error = "Error interno"
    mock_stock_service.get_all_stocks.return_value.status_code = 500
    mock_stock_service.get_all_stocks.return_value.value = None

    response = await async_client.get("/stock")

    assert response.status_code == 500


# --- Tests de add stock ---

@pytest.mark.asyncio
async def test_add_stock_exitoso(async_client: AsyncClient, mock_stock_service):
    """POST /stock/{id}/agregar agrega stock."""
    result_value = {
        "categoria_id": 1, "categoria_nombre": "Pizza",
        "cantidad": 60, "umbral_amarillo": 10, "umbral_rojo": 5, "estado": "ok",
    }
    mock_stock_service.add_stock.return_value.error = None
    mock_stock_service.add_stock.return_value.value = result_value

    response = await async_client.post(
        "/stock/1/agregar",
        json={"cantidad": 10},
    )

    assert response.status_code == 200
    assert response.json()["cantidad"] == 60


@pytest.mark.asyncio
async def test_add_stock_zero(async_client: AsyncClient):
    """POST /stock/{id}/agregar con cantidad 0 retorna 422 (validation)."""
    response = await async_client.post(
        "/stock/1/agregar",
        json={"cantidad": 0},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_add_stock_category_not_found(async_client: AsyncClient, mock_stock_service):
    """POST /stock/{id}/agregar con categoría inexistente retorna 404."""
    mock_stock_service.add_stock.return_value.error = "Categoría no encontrada"
    mock_stock_service.add_stock.return_value.status_code = 404
    mock_stock_service.add_stock.return_value.value = None

    response = await async_client.post(
        "/stock/999/agregar",
        json={"cantidad": 5},
    )

    assert response.status_code == 404


# --- Tests de configure alerts ---

@pytest.mark.asyncio
async def test_configure_alerts_exitoso(async_client: AsyncClient, mock_stock_service):
    """PUT /stock/{id}/alertas configura umbrales."""
    result_value = {
        "categoria_id": 1, "categoria_nombre": "Pizza",
        "cantidad": 50, "umbral_amarillo": 15, "umbral_rojo": 5, "estado": "ok",
    }
    mock_stock_service.configure_alerts.return_value.error = None
    mock_stock_service.configure_alerts.return_value.value = result_value

    response = await async_client.put(
        "/stock/1/alertas",
        json={"umbral_amarillo": 15, "umbral_rojo": 5},
    )

    assert response.status_code == 200
    assert response.json()["umbral_amarillo"] == 15


@pytest.mark.asyncio
async def test_configure_alerts_not_found(async_client: AsyncClient, mock_stock_service):
    """PUT /stock/{id}/alertas con categoría inexistente retorna 404."""
    mock_stock_service.configure_alerts.return_value.error = "Categoría no encontrada"
    mock_stock_service.configure_alerts.return_value.status_code = 404
    mock_stock_service.configure_alerts.return_value.value = None

    response = await async_client.put(
        "/stock/999/alertas",
        json={"umbral_amarillo": 10, "umbral_rojo": 5},
    )

    assert response.status_code == 404


# --- Tests de get movements ---

@pytest.mark.asyncio
async def test_get_movements(async_client: AsyncClient, mock_stock_service):
    """GET /stock/{id}/movimientos retorna historial."""
    movements = [
        {"id": 1, "timestamp": "2024-01-01T00:00:00", "username": "admin",
         "action": "UPDATE", "changes": {"tipo": "INGRESO", "cantidad": 10}},
    ]
    mock_stock_service.get_movements.return_value.error = None
    mock_stock_service.get_movements.return_value.value = movements

    response = await async_client.get("/stock/1/movimientos")

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_movements_empty(async_client: AsyncClient, mock_stock_service):
    """GET /stock/{id}/movimientos sin movimientos retorna lista vacía."""
    mock_stock_service.get_movements.return_value.error = None
    mock_stock_service.get_movements.return_value.value = []

    response = await async_client.get("/stock/1/movimientos")

    assert response.status_code == 200
    assert response.json() == []
