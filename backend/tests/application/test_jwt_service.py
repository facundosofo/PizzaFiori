"""
Tests for JWTService.
Tests JWT token generation, decoding, and extraction using python-jose.
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from app.application.services.jwt_service import JWTService


# Build a fake settings object for tests
def _fake_settings():
    s = MagicMock()
    s.jwt_secret = "test-secret-key-for-unit-tests"
    s.jwt_algorithm = "HS256"
    s.jwt_access_token_expire_minutes = 30
    s.jwt_token_durations = {"ADMIN": 60, "USER": 30}
    return s


# ==================== generate_token Tests ====================


@patch("app.application.services.jwt_service.settings", _fake_settings())
def test_generate_token_returns_dict():
    """Test generate_token returns dict with required keys."""
    result = JWTService.generate_token(user_id=1, username="admin", role="ADMIN")

    assert "token" in result
    assert "expires_in" in result
    assert "expires_at" in result
    assert isinstance(result["token"], str)


@patch("app.application.services.jwt_service.settings", _fake_settings())
def test_generate_token_admin_duration():
    """Test ADMIN role gets 60 min duration (from jwt_token_durations)."""
    result = JWTService.generate_token(user_id=1, username="admin", role="ADMIN")

    assert result["expires_in"] == 60 * 60  # 60 minutes in seconds


@patch("app.application.services.jwt_service.settings", _fake_settings())
def test_generate_token_user_duration():
    """Test USER role gets 30 min duration."""
    result = JWTService.generate_token(user_id=2, username="user", role="USER")

    assert result["expires_in"] == 30 * 60  # 30 minutes in seconds


@patch("app.application.services.jwt_service.settings", _fake_settings())
def test_generate_token_custom_expiration():
    """Test custom_expires_minutes overrides role duration."""
    result = JWTService.generate_token(
        user_id=1, username="admin", role="ADMIN", custom_expires_minutes=5
    )

    assert result["expires_in"] == 5 * 60  # 5 minutes in seconds


# ==================== decode_token Tests ====================


@patch("app.application.services.jwt_service.settings", _fake_settings())
def test_decode_token_valid():
    """Test decoding a valid token returns payload."""
    token_data = JWTService.generate_token(user_id=1, username="admin", role="ADMIN")
    payload = JWTService.decode_token(token_data["token"])

    assert payload["sub"] == "1"
    assert payload["username"] == "admin"
    assert payload["role"] == "ADMIN"
    assert payload["type"] == "access"
    assert "exp" in payload
    assert "iat" in payload


@patch("app.application.services.jwt_service.settings", _fake_settings())
def test_decode_token_expired():
    """Test decoding expired token raises ValueError."""
    # Generate token with very short expiration
    from jose import jwt

    fake = _fake_settings()
    payload = {
        "sub": "1",
        "username": "admin",
        "role": "ADMIN",
        "exp": int((datetime.now() - timedelta(hours=1)).timestamp()),
        "iat": int(datetime.now().timestamp()),
        "type": "access",
    }
    token = jwt.encode(payload, fake.jwt_secret, algorithm=fake.jwt_algorithm)

    with pytest.raises(ValueError, match="Invalid or expired token"):
        JWTService.decode_token(token)


@patch("app.application.services.jwt_service.settings", _fake_settings())
def test_decode_token_invalid():
    """Test decoding invalid token string raises ValueError."""
    with pytest.raises(ValueError, match="Invalid or expired token"):
        JWTService.decode_token("not.a.valid.jwt.token")


@patch("app.application.services.jwt_service.settings", _fake_settings())
def test_decode_token_wrong_secret():
    """Test decoding token signed with wrong secret raises ValueError."""
    from jose import jwt

    payload = {
        "sub": "1",
        "exp": int((datetime.now() + timedelta(hours=1)).timestamp()),
    }
    token = jwt.encode(payload, "wrong-secret", algorithm="HS256")

    with pytest.raises(ValueError, match="Invalid or expired token"):
        JWTService.decode_token(token)


# ==================== extract_bearer_token Tests ====================


def test_extract_bearer_token_valid():
    """Test extracting token from valid Bearer header."""
    token = JWTService.extract_bearer_token("Bearer abc123.xyz.def")
    assert token == "abc123.xyz.def"


def test_extract_bearer_token_none():
    """Test extracting from None returns None."""
    assert JWTService.extract_bearer_token(None) is None


def test_extract_bearer_token_empty():
    """Test extracting from empty string returns None."""
    assert JWTService.extract_bearer_token("") is None


def test_extract_bearer_token_no_bearer_prefix():
    """Test extracting without Bearer prefix returns None."""
    assert JWTService.extract_bearer_token("Basic abc123") is None


def test_extract_bearer_token_case_sensitive():
    """Test Bearer prefix is case-sensitive."""
    assert JWTService.extract_bearer_token("bearer abc123") is None
