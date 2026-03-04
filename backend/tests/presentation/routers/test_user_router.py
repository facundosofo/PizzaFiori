"""
Tests para los endpoints de usuarios.
Verifica respuestas HTTP sin verificar mocks.
"""

import pytest
from httpx import AsyncClient
from unittest.mock import MagicMock
from datetime import datetime


def _build_user_mock(**kwargs):
    """Build a mock user for router responses."""
    defaults = {
        "id": 1, "username": "testuser", "email": "test@test.com",
        "first_name": "Test", "last_name": "User", "role": "USER",
        "created_at": datetime(2024, 1, 1), "updated_at": datetime(2024, 1, 1),
        "failed_login_attempts": 0, "locked_until": None,
    }
    defaults.update(kwargs)
    user = MagicMock()
    for k, v in defaults.items():
        setattr(user, k, v)
    return user


# --- Tests de registro ---

@pytest.mark.asyncio
async def test_register_user_exitoso(async_client: AsyncClient, mock_user_service):
    """Registrar usuario con datos válidos retorna 201."""
    user = _build_user_mock(id=2, username="newuser")
    mock_user_service.register_user.return_value.error = None
    mock_user_service.register_user.return_value.value = user

    payload = {
        "username": "newuser",
        "email": "new@test.com",
        "password": "Password1",
        "first_name": "New",
        "last_name": "User",
    }

    response = await async_client.post("/users", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["user"]["username"] == "newuser"


@pytest.mark.asyncio
async def test_register_user_duplicado(async_client: AsyncClient, mock_user_service):
    """Registrar usuario duplicado retorna 409."""
    mock_user_service.register_user.return_value.error = "Username ya existe"
    mock_user_service.register_user.return_value.status_code = 409
    mock_user_service.register_user.return_value.value = None

    payload = {
        "username": "admin",
        "email": "admin@test.com",
        "password": "Password1",
        "first_name": "A",
        "last_name": "B",
    }

    response = await async_client.post("/users", json=payload)

    assert response.status_code == 409


# --- Tests de me ---

@pytest.mark.asyncio
async def test_get_me(async_client: AsyncClient, mock_user_service):
    """GET /users/me retorna datos del usuario actual."""
    user = _build_user_mock(id=1, username="admin_test", role="ADMIN")
    mock_user_service.get_user.return_value.error = None
    mock_user_service.get_user.return_value.value = user

    response = await async_client.get("/users/me")

    assert response.status_code == 200
    data = response.json()
    assert "username" in data


# --- Tests de change password ---

@pytest.mark.asyncio
async def test_change_password_exitoso(async_client: AsyncClient, mock_user_service):
    """Cambiar contraseña con datos válidos retorna 200."""
    mock_user_service.change_password.return_value.error = None
    mock_user_service.change_password.return_value.value = True

    payload = {
        "old_password": "OldPass123",
        "new_password": "NewPass123",
    }

    response = await async_client.post("/users/me/change-password", json=payload)

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_change_password_old_incorrecta(async_client: AsyncClient, mock_user_service):
    """Cambiar contraseña con password vieja incorrecta retorna 400."""
    mock_user_service.change_password.return_value.error = "Contraseña actual incorrecta"
    mock_user_service.change_password.return_value.status_code = 400
    mock_user_service.change_password.return_value.value = None

    payload = {
        "old_password": "WrongPass1",
        "new_password": "NewPass123",
    }

    response = await async_client.post("/users/me/change-password", json=payload)

    assert response.status_code == 400


# --- Tests de list users (admin) ---

@pytest.mark.asyncio
async def test_list_users(async_client: AsyncClient, mock_user_service):
    """GET /users retorna lista de usuarios."""
    users = [_build_user_mock(id=1), _build_user_mock(id=2, username="user2")]
    mock_user_service.get_all_users.return_value.error = None
    mock_user_service.get_all_users.return_value.value = users

    response = await async_client.get("/users")

    assert response.status_code == 200


# --- Tests de get user details ---

@pytest.mark.asyncio
async def test_get_user_details(async_client: AsyncClient, mock_user_service):
    """GET /users/{id} retorna detalles del usuario."""
    user = _build_user_mock(id=5, username="detailuser")
    mock_user_service.get_user.return_value.error = None
    mock_user_service.get_user.return_value.value = user

    response = await async_client.get("/users/5")

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_user_not_found(async_client: AsyncClient, mock_user_service):
    """GET /users/{id} con ID inexistente retorna 404."""
    mock_user_service.get_user.return_value.error = "Usuario no encontrado"
    mock_user_service.get_user.return_value.status_code = 404
    mock_user_service.get_user.return_value.value = None

    response = await async_client.get("/users/999")

    assert response.status_code == 404


# --- Tests de update user ---

@pytest.mark.asyncio
async def test_update_user(async_client: AsyncClient, mock_user_service):
    """PUT /users/{id} actualiza usuario correctamente."""
    user = _build_user_mock(id=5, first_name="Updated")
    mock_user_service.update_user.return_value.error = None
    mock_user_service.update_user.return_value.value = user

    response = await async_client.put(
        "/users/5",
        json={"first_name": "Updated"},
    )

    assert response.status_code == 200


# --- Tests de delete user ---

@pytest.mark.asyncio
async def test_delete_user(async_client: AsyncClient, mock_user_service):
    """DELETE /users/{id} elimina usuario correctamente."""
    mock_user_service.delete_user.return_value.error = None
    mock_user_service.delete_user.return_value.value = True

    response = await async_client.delete("/users/5")

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_user_not_found(async_client: AsyncClient, mock_user_service):
    """DELETE /users/{id} con ID inexistente retorna 404."""
    mock_user_service.delete_user.return_value.error = "Usuario no encontrado"
    mock_user_service.delete_user.return_value.status_code = 404
    mock_user_service.delete_user.return_value.value = None

    response = await async_client.delete("/users/999")

    assert response.status_code == 404


# --- Tests de unlock ---

@pytest.mark.asyncio
async def test_unlock_user(async_client: AsyncClient, mock_user_service):
    """POST /users/{id}/unlock desbloquea usuario."""
    user = _build_user_mock(id=5, failed_login_attempts=0, locked_until=None)
    mock_user_service.unlock_user_account.return_value.error = None
    mock_user_service.unlock_user_account.return_value.value = user

    response = await async_client.post("/users/5/unlock")

    assert response.status_code == 200
