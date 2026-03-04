"""
Tests for UserService.
Tests user registration, authentication, password management, and account operations.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from app.application.user_service import UserService, ServiceResult
from tests.helpers import build_user_model


# ==================== Validate Password Tests ====================

class TestValidatePassword:
    """Tests for password validation rules."""

    def _make_service(self, mock_uow, mock_logger):
        return UserService(uow=mock_uow, logger=mock_logger)

    def test_password_too_short(self, mock_uow, mock_logger):
        service = self._make_service(mock_uow, mock_logger)
        is_valid, error = service.validate_password("Ab1!")
        assert is_valid is False
        assert "characters" in error

    def test_password_no_uppercase(self, mock_uow, mock_logger):
        service = self._make_service(mock_uow, mock_logger)
        is_valid, error = service.validate_password("abcdefgh1")
        assert is_valid is False
        assert "uppercase" in error

    def test_password_no_number(self, mock_uow, mock_logger):
        service = self._make_service(mock_uow, mock_logger)
        is_valid, error = service.validate_password("Abcdefghi")
        assert is_valid is False
        assert "number" in error

    def test_password_valid(self, mock_uow, mock_logger):
        service = self._make_service(mock_uow, mock_logger)
        is_valid, error = service.validate_password("Abcdefg1")
        assert is_valid is True
        assert error is None


# ==================== Register User Tests ====================

@pytest.mark.asyncio
async def test_register_user_success(mock_uow, mock_audit_service, mock_logger):
    """Test successful user registration."""
    service = UserService(uow=mock_uow, audit_service=mock_audit_service, logger=mock_logger)

    mock_uow.users.get_by_username.return_value = None
    mock_uow.users.get_by_email.return_value = None
    mock_uow.users.refresh = AsyncMock(side_effect=lambda u: setattr(u, 'id', 1))

    result = await service.register_user(
        username="newuser",
        email="new@example.com",
        password="ValidPass1",
        first_name="New",
        last_name="User",
    )

    assert result.status_code == 201
    assert result.value is not None
    mock_uow.users.add.assert_called_once()
    mock_uow.commit.assert_called_once()


@pytest.mark.asyncio
async def test_register_user_invalid_password(mock_uow, mock_logger):
    """Test registration with weak password."""
    service = UserService(uow=mock_uow, logger=mock_logger)

    result = await service.register_user(
        username="user", email="u@e.com",
        password="weak", first_name="A", last_name="B",
    )

    assert result.status_code == 422
    mock_uow.users.add.assert_not_called()


@pytest.mark.asyncio
async def test_register_user_duplicate_username(mock_uow, mock_logger):
    """Test registration with existing username."""
    service = UserService(uow=mock_uow, logger=mock_logger)
    mock_uow.users.get_by_username.return_value = build_user_model()

    result = await service.register_user(
        username="testuser", email="new@e.com",
        password="ValidPass1", first_name="A", last_name="B",
    )

    assert result.status_code == 409
    assert "Username already exists" in result.error


@pytest.mark.asyncio
async def test_register_user_duplicate_email(mock_uow, mock_logger):
    """Test registration with existing email."""
    service = UserService(uow=mock_uow, logger=mock_logger)
    mock_uow.users.get_by_username.return_value = None
    mock_uow.users.get_by_email.return_value = build_user_model()

    result = await service.register_user(
        username="newuser", email="test@example.com",
        password="ValidPass1", first_name="A", last_name="B",
    )

    assert result.status_code == 409
    assert "Email already exists" in result.error


# ==================== Authenticate User Tests ====================

@pytest.mark.asyncio
async def test_authenticate_user_success(mock_uow, mock_logger):
    """Test successful authentication."""
    service = UserService(uow=mock_uow, logger=mock_logger)
    user = build_user_model(password_hash="$2b$12$hash")

    mock_uow.users.get_by_username.return_value = user

    with patch("app.application.user_service.verify_password", return_value=True):
        result = await service.authenticate_user("testuser", "ValidPass1")

    assert result.status_code == 200
    assert result.value is not None


@pytest.mark.asyncio
async def test_authenticate_user_not_found(mock_uow, mock_logger):
    """Test authentication with non-existent user."""
    service = UserService(uow=mock_uow, logger=mock_logger)
    mock_uow.users.get_by_username.return_value = None

    result = await service.authenticate_user("ghost", "password")

    assert result.status_code == 401
    assert "Invalid credentials" in result.error


@pytest.mark.asyncio
async def test_authenticate_user_wrong_password(mock_uow, mock_logger):
    """Test authentication with wrong password."""
    service = UserService(uow=mock_uow, logger=mock_logger)
    user = build_user_model(failed_login_attempts=0)
    mock_uow.users.get_by_username.return_value = user

    with patch("app.application.user_service.verify_password", return_value=False):
        result = await service.authenticate_user("testuser", "wrong")

    assert result.status_code == 401
    assert "Invalid credentials" in result.error


@pytest.mark.asyncio
async def test_authenticate_user_locked_account(mock_uow, mock_logger):
    """Test authentication with locked account."""
    service = UserService(uow=mock_uow, logger=mock_logger)
    user = build_user_model(locked_until=datetime.now() + timedelta(minutes=30))
    mock_uow.users.get_by_username.return_value = user

    result = await service.authenticate_user("testuser", "ValidPass1")

    assert result.status_code == 423
    assert "locked" in result.error.lower()


# ==================== Get User Tests ====================

@pytest.mark.asyncio
async def test_get_user_success(mock_uow, mock_logger):
    """Test getting user by ID."""
    service = UserService(uow=mock_uow, logger=mock_logger)
    user = build_user_model(id=1)
    mock_uow.users.get_by_id.return_value = user

    result = await service.get_user(1)

    assert result.status_code == 200
    assert result.value.id == 1


@pytest.mark.asyncio
async def test_get_user_not_found(mock_uow, mock_logger):
    """Test getting non-existent user."""
    service = UserService(uow=mock_uow, logger=mock_logger)
    mock_uow.users.get_by_id.return_value = None

    result = await service.get_user(999)

    assert result.status_code == 404
    assert result.error == "User not found"


# ==================== Get All Users Tests ====================

@pytest.mark.asyncio
async def test_get_all_users_success(mock_uow, mock_logger):
    """Test getting all users."""
    service = UserService(uow=mock_uow, logger=mock_logger)
    users = [build_user_model(1, "user1"), build_user_model(2, "user2")]
    mock_uow.users.list.return_value = users

    result = await service.get_all_users()

    assert result.status_code == 200
    assert len(result.value) == 2


@pytest.mark.asyncio
async def test_get_all_users_with_role_filter(mock_uow, mock_logger):
    """Test getting users filtered by role."""
    service = UserService(uow=mock_uow, logger=mock_logger)
    admins = [build_user_model(1, "admin1", role="ADMIN")]
    mock_uow.users.list_by_role.return_value = admins

    result = await service.get_all_users(role_filter="ADMIN")

    assert result.status_code == 200
    assert len(result.value) == 1
    mock_uow.users.list_by_role.assert_called_once_with("ADMIN", skip=0, limit=100)


# ==================== Update User Tests ====================

@pytest.mark.asyncio
async def test_update_user_success(mock_uow, mock_audit_service, mock_logger):
    """Test updating user information."""
    service = UserService(uow=mock_uow, audit_service=mock_audit_service, logger=mock_logger)
    user = build_user_model(id=1)
    mock_uow.users.get_by_id.return_value = user
    mock_uow.users.refresh = AsyncMock()

    result = await service.update_user(1, {"first_name": "Updated"}, updated_by_username="admin")

    assert result.status_code == 200
    mock_uow.users.update.assert_called_once()
    mock_uow.commit.assert_called_once()


@pytest.mark.asyncio
async def test_update_user_not_found(mock_uow, mock_logger):
    """Test updating non-existent user."""
    service = UserService(uow=mock_uow, logger=mock_logger)
    mock_uow.users.get_by_id.return_value = None

    result = await service.update_user(999, {"first_name": "X"}, updated_by_username="admin")

    assert result.status_code == 404


# ==================== Change Password Tests ====================

@pytest.mark.asyncio
async def test_change_password_success(mock_uow, mock_logger):
    """Test successful password change."""
    service = UserService(uow=mock_uow, logger=mock_logger)
    user = build_user_model(id=1, password_hash="$2b$12$old")
    mock_uow.users.get_by_id.return_value = user

    with patch("app.application.user_service.verify_password", return_value=True):
        with patch("app.application.user_service.hash_password", return_value="$2b$12$new"):
            result = await service.change_password(1, "OldPass1", "NewPass1!")

    assert result.status_code == 200
    mock_uow.commit.assert_called_once()


@pytest.mark.asyncio
async def test_change_password_invalid_old(mock_uow, mock_logger):
    """Test password change with wrong current password."""
    service = UserService(uow=mock_uow, logger=mock_logger)
    user = build_user_model(id=1)
    mock_uow.users.get_by_id.return_value = user

    with patch("app.application.user_service.verify_password", return_value=False):
        result = await service.change_password(1, "wrong", "NewPass1!")

    assert result.status_code == 400
    assert "Invalid old password" in result.error


@pytest.mark.asyncio
async def test_change_password_invalid_new(mock_uow, mock_logger):
    """Test password change with weak new password."""
    service = UserService(uow=mock_uow, logger=mock_logger)

    result = await service.change_password(1, "OldPass1", "weak")

    assert result.status_code == 422


# ==================== Delete User Tests ====================

@pytest.mark.asyncio
async def test_delete_user_success(mock_uow, mock_audit_service, mock_logger):
    """Test successful user deletion."""
    service = UserService(uow=mock_uow, audit_service=mock_audit_service, logger=mock_logger)
    user = build_user_model(id=1)
    mock_uow.users.get_by_id.return_value = user

    result = await service.delete_user(1, deleted_by_username="admin")

    assert result.status_code == 204
    mock_uow.users.delete.assert_called_once_with(1)
    mock_uow.commit.assert_called_once()


@pytest.mark.asyncio
async def test_delete_user_not_found(mock_uow, mock_logger):
    """Test deleting non-existent user."""
    service = UserService(uow=mock_uow, logger=mock_logger)
    mock_uow.users.get_by_id.return_value = None

    result = await service.delete_user(999, deleted_by_username="admin")

    assert result.status_code == 404


# ==================== Unlock Account Tests ====================

@pytest.mark.asyncio
async def test_unlock_account_success(mock_uow, mock_audit_service, mock_logger):
    """Test unlocking a locked account."""
    service = UserService(uow=mock_uow, audit_service=mock_audit_service, logger=mock_logger)
    user = build_user_model(
        id=1,
        failed_login_attempts=5,
        locked_until=datetime.now() + timedelta(hours=1),
    )
    mock_uow.users.get_by_id.return_value = user

    result = await service.unlock_user_account(1, unlocked_by_username="admin")

    assert result.status_code == 200
    mock_uow.users.update.assert_called_once()
    mock_uow.commit.assert_called_once()


@pytest.mark.asyncio
async def test_unlock_account_not_found(mock_uow, mock_logger):
    """Test unlocking non-existent account."""
    service = UserService(uow=mock_uow, logger=mock_logger)
    mock_uow.users.get_by_id.return_value = None

    result = await service.unlock_user_account(999, unlocked_by_username="admin")

    assert result.status_code == 404
