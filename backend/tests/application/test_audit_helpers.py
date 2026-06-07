"""
Tests for audit helper functions.
Tests diff computation, snapshot generation, and value normalization.
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
from decimal import Decimal

from app.application.utils.audit_helpers import (
    _normalize_value,
    SENSITIVE_FIELDS,
)


# ==================== _normalize_value Tests ====================


def test_normalize_none():
    assert _normalize_value(None) is None


def test_normalize_string():
    assert _normalize_value("hello") == "hello"


def test_normalize_int():
    assert _normalize_value(42) == 42


def test_normalize_float():
    assert _normalize_value(3.14) == 3.14


def test_normalize_bool():
    assert _normalize_value(True) is True


def test_normalize_datetime():
    dt = datetime(2024, 6, 15, 10, 30, 0)
    assert _normalize_value(dt) == "2024-06-15T10:30:00"


def test_normalize_decimal():
    d = Decimal("123.45")
    assert _normalize_value(d) == 123.45
    assert isinstance(_normalize_value(d), float)


def test_normalize_other_type():
    """Non-primitive types get str()."""
    result = _normalize_value([1, 2, 3])
    assert result == "[1, 2, 3]"


# ==================== SENSITIVE_FIELDS Tests ====================


def test_sensitive_fields_contains_password():
    assert "password_hash" in SENSITIVE_FIELDS
    assert "password" in SENSITIVE_FIELDS


def test_sensitive_fields_contains_tokens():
    assert "token" in SENSITIVE_FIELDS
    assert "refresh_token" in SENSITIVE_FIELDS


def test_sensitive_fields_contains_keys():
    assert "api_key" in SENSITIVE_FIELDS
    assert "secret_key" in SENSITIVE_FIELDS


# ==================== compute_entity_diff Tests ====================


def _make_entity_with_mapper(fields: dict):
    """Create a mock entity with a SQLAlchemy-like mapper."""
    entity = MagicMock()
    for k, v in fields.items():
        setattr(entity, k, v)

    # Mock SQLAlchemy columns
    columns = []
    for name in fields:
        col = MagicMock()
        col.name = name
        columns.append(col)

    entity.__class__ = type("FakeEntity", (), {})
    return entity, columns


def test_compute_entity_diff_detects_changes():
    """Test diff detects changed fields."""
    old_fields = {"id": 1, "nombre": "Pizza", "precio": 100}
    new_fields = {"id": 1, "nombre": "Pizza Deluxe", "precio": 150}
    old_entity, columns = _make_entity_with_mapper(old_fields)
    new_entity, _ = _make_entity_with_mapper(new_fields)

    mock_mapper = MagicMock()
    mock_mapper.columns = columns

    with patch("app.application.utils.audit_helpers.inspect", return_value=mock_mapper):
        from app.application.utils.audit_helpers import compute_entity_diff
        diff = compute_entity_diff(old_entity, new_entity)

    assert "nombre" in diff
    assert diff["nombre"]["old"] == "Pizza"
    assert diff["nombre"]["new"] == "Pizza Deluxe"
    assert "precio" in diff
    # id should not be in diff because it didn't change
    assert "id" not in diff


def test_compute_entity_diff_no_changes():
    """Test diff returns empty dict when nothing changed."""
    fields = {"id": 1, "nombre": "Pizza"}
    old_entity, columns = _make_entity_with_mapper(fields)
    new_entity, _ = _make_entity_with_mapper(fields)

    mock_mapper = MagicMock()
    mock_mapper.columns = columns

    with patch("app.application.utils.audit_helpers.inspect", return_value=mock_mapper):
        from app.application.utils.audit_helpers import compute_entity_diff
        diff = compute_entity_diff(old_entity, new_entity)

    assert diff == {}


def test_compute_entity_diff_excludes_timestamps():
    """Test diff excludes timestamp fields by default."""
    old_fields = {"id": 1, "nombre": "A", "fecha_actualizacion": datetime(2024, 1, 1), "fecha_creacion": datetime(2024, 1, 1)}
    new_fields = {"id": 1, "nombre": "A", "fecha_actualizacion": datetime(2024, 6, 1), "fecha_creacion": datetime(2024, 1, 1)}
    old_entity, columns = _make_entity_with_mapper(old_fields)
    new_entity, _ = _make_entity_with_mapper(new_fields)

    mock_mapper = MagicMock()
    mock_mapper.columns = columns

    with patch("app.application.utils.audit_helpers.inspect", return_value=mock_mapper):
        from app.application.utils.audit_helpers import compute_entity_diff
        diff = compute_entity_diff(old_entity, new_entity)

    assert "fecha_actualizacion" not in diff
    assert "fecha_creacion" not in diff


def test_compute_entity_diff_excludes_sensitive():
    """Test diff excludes password_hash and other sensitive fields."""
    old_fields = {"id": 1, "password_hash": "abc123"}
    new_fields = {"id": 1, "password_hash": "xyz789"}
    old_entity, columns = _make_entity_with_mapper(old_fields)
    new_entity, _ = _make_entity_with_mapper(new_fields)

    mock_mapper = MagicMock()
    mock_mapper.columns = columns

    with patch("app.application.utils.audit_helpers.inspect", return_value=mock_mapper):
        from app.application.utils.audit_helpers import compute_entity_diff
        diff = compute_entity_diff(old_entity, new_entity)

    assert "password_hash" not in diff


# ==================== entity_to_snapshot Tests ====================


def test_entity_to_snapshot():
    """Test snapshot captures all non-excluded fields."""
    fields = {"id": 1, "nombre": "Pizza", "activo": True}
    entity, columns = _make_entity_with_mapper(fields)

    mock_mapper = MagicMock()
    mock_mapper.columns = columns

    with patch("app.application.utils.audit_helpers.inspect", return_value=mock_mapper):
        from app.application.utils.audit_helpers import entity_to_snapshot
        snapshot = entity_to_snapshot(entity)

    assert snapshot["id"] == 1
    assert snapshot["nombre"] == "Pizza"
    assert snapshot["activo"] is True


def test_entity_to_snapshot_excludes_sensitive():
    """Test snapshot excludes sensitive fields."""
    fields = {"id": 1, "password_hash": "secret"}
    entity, columns = _make_entity_with_mapper(fields)

    mock_mapper = MagicMock()
    mock_mapper.columns = columns

    with patch("app.application.utils.audit_helpers.inspect", return_value=mock_mapper):
        from app.application.utils.audit_helpers import entity_to_snapshot
        snapshot = entity_to_snapshot(entity)

    assert "password_hash" not in snapshot
