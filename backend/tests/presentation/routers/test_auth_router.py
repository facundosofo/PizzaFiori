"""
Tests para los endpoints de autenticación.
Verifica respuestas HTTP sin verificar mocks.
"""

import pytest
from httpx import AsyncClient
from unittest.mock import MagicMock, patch


# --- Tests de login ---

@pytest.mark.asyncio
async def test_login_exitoso(async_client: AsyncClient, mock_user_service):
    """Login con credenciales válidas retorna 200 y token."""
    user = MagicMock()
    user.id = 1
    user.username = "admin"
    user.email = "admin@test.com"
    user.first_name = "Admin"
    user.last_name = "Test"
    user.role = "ADMIN"
    user.created_at = "2024-01-01T00:00:00"
    user.updated_at = "2024-01-01T00:00:00"

    mock_user_service.authenticate_user.return_value.error = None
    mock_user_service.authenticate_user.return_value.value = user

    with patch(
        "app.presentation.routers.auth_router.JWTService.generate_token",
        return_value={"token": "fake.jwt.token", "expires_in": 3600, "expires_at": 9999999},
    ):
        response = await async_client.post(
            "/auth/login",
            json={"username": "admin", "password": "Password123"},
        )

    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert data["user"]["username"] == "admin"


@pytest.mark.asyncio
async def test_login_credenciales_invalidas(async_client: AsyncClient, mock_user_service):
    """Login con credenciales inválidas retorna 401."""
    mock_user_service.authenticate_user.return_value.error = "Credenciales inválidas"
    mock_user_service.authenticate_user.return_value.status_code = 401
    mock_user_service.authenticate_user.return_value.value = None

    response = await async_client.post(
        "/auth/login",
        json={"username": "wrong", "password": "wrong"},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_cuenta_bloqueada(async_client: AsyncClient, mock_user_service):
    """Login con cuenta bloqueada retorna 423."""
    mock_user_service.authenticate_user.return_value.error = "Cuenta bloqueada"
    mock_user_service.authenticate_user.return_value.status_code = 423
    mock_user_service.authenticate_user.return_value.value = None

    response = await async_client.post(
        "/auth/login",
        json={"username": "locked_user", "password": "Password123"},
    )

    assert response.status_code == 423


@pytest.mark.asyncio
async def test_login_campos_vacios(async_client: AsyncClient):
    """Login sin campos requeridos retorna 422."""
    response = await async_client.post("/auth/login", json={})

    assert response.status_code == 422


# --- Tests de reset password ---

@pytest.mark.asyncio
async def test_reset_password(async_client: AsyncClient):
    """Reset password retorna 202 (stub)."""
    response = await async_client.post(
        "/auth/reset-password",
        json={"email": "admin@test.com"},
    )

    assert response.status_code == 202
    assert "message" in response.json()


# --- Tests de logout ---

@pytest.mark.asyncio
async def test_logout(async_client: AsyncClient):
    """Logout retorna 200."""
    response = await async_client.post("/auth/logout")

    assert response.status_code == 200
    data = response.json()
    assert "message" in data
