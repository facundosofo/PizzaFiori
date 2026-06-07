"""
Tests para los endpoints de auditoría.
Verifica respuestas HTTP sin verificar mocks.
"""

import pytest
from httpx import AsyncClient
from unittest.mock import MagicMock
from datetime import datetime


def _build_audit_log_mock(**kwargs):
    """Build a mock audit log for router responses."""
    defaults = {
        "id": 1,
        "timestamp": datetime(2024, 6, 1, 10, 0, 0),
        "username": "admin",
        "entity_type": "Product",
        "entity_id": 1,
        "action": "CREATE",
        "changes": {"new": {"id": 1, "nombre": "Pizza"}},
    }
    defaults.update(kwargs)
    m = MagicMock()
    for k, v in defaults.items():
        setattr(m, k, v)
    return m


# --- Tests de search audit logs ---

@pytest.mark.asyncio
async def test_search_audit_logs(async_client: AsyncClient, mock_audit_service):
    """GET /audit/search retorna registros de auditoría."""
    logs = [
        _build_audit_log_mock(id=1, action="CREATE"),
        _build_audit_log_mock(id=2, action="UPDATE"),
    ]
    mock_audit_service.get_by_date_range.return_value.error = None
    mock_audit_service.get_by_date_range.return_value.value = {
        "total": 2,
        "records": logs,
    }

    response = await async_client.get(
        "/audit/search",
        params={
            "start_date": "2024-01-01T00:00:00",
            "end_date": "2024-12-31T23:59:59",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["records"]) == 2


@pytest.mark.asyncio
async def test_search_audit_logs_with_filters(async_client: AsyncClient, mock_audit_service):
    """GET /audit/search con filtros retorna registros filtrados."""
    logs = [_build_audit_log_mock(id=1, entity_type="Product", action="CREATE")]
    mock_audit_service.get_by_date_range.return_value.error = None
    mock_audit_service.get_by_date_range.return_value.value = {
        "total": 1,
        "records": logs,
    }

    response = await async_client.get(
        "/audit/search",
        params={
            "start_date": "2024-01-01T00:00:00",
            "end_date": "2024-12-31T23:59:59",
            "entity_type": "Product",
            "username": "admin",
            "action": "CREATE",
            "limit": 50,
            "offset": 0,
        },
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1


@pytest.mark.asyncio
async def test_search_audit_logs_defaults(async_client: AsyncClient, mock_audit_service):
    """GET /audit/search sin fechas usa últimos 7 días por defecto."""
    mock_audit_service.get_by_date_range.return_value.error = None
    mock_audit_service.get_by_date_range.return_value.value = {
        "total": 0,
        "records": [],
    }

    response = await async_client.get("/audit/search")

    assert response.status_code == 200
    assert response.json()["total"] == 0


@pytest.mark.asyncio
async def test_search_audit_logs_invalid_dates(async_client: AsyncClient, mock_audit_service):
    """GET /audit/search con start > end retorna 400."""
    response = await async_client.get(
        "/audit/search",
        params={
            "start_date": "2024-12-31T23:59:59",
            "end_date": "2024-01-01T00:00:00",
        },
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_search_audit_logs_error(async_client: AsyncClient, mock_audit_service):
    """GET /audit/search con error retorna 500."""
    mock_audit_service.get_by_date_range.return_value.error = "Error interno"
    mock_audit_service.get_by_date_range.return_value.status_code = 500
    mock_audit_service.get_by_date_range.return_value.value = None

    response = await async_client.get("/audit/search")

    assert response.status_code == 500
