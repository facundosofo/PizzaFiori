"""
Tests for the Health Check endpoint (GET /health).
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check_healthy(async_client: AsyncClient):
    """GET /health should return 200 with status healthy and database connected."""
    # Mock engine.connect() to simulate a successful DB connection
    mock_conn = AsyncMock()
    mock_conn.execute = AsyncMock(return_value=None)

    mock_connect = AsyncMock()
    mock_connect.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_connect.__aexit__ = AsyncMock(return_value=False)

    with patch("app.presentation.routers.health_router.engine") as mock_engine:
        mock_engine.connect.return_value = mock_connect
        response = await async_client.get("/health/")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"


@pytest.mark.asyncio
async def test_health_check_database_unreachable(async_client: AsyncClient):
    """GET /health should return 503 with database unreachable when DB is down."""
    mock_connect = AsyncMock()
    mock_connect.__aenter__ = AsyncMock(side_effect=Exception("Connection refused"))

    with patch("app.presentation.routers.health_router.engine") as mock_engine:
        mock_engine.connect.return_value = mock_connect
        response = await async_client.get("/health/")

    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "unhealthy"
    assert data["database"] == "unreachable"
