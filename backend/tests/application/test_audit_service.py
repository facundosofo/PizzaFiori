"""
Tests for AuditService.
Tests audit logging operations with mocked repositories and UnitOfWork.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.application.audit_service import AuditService, AuditServiceResult
from tests.helpers import build_audit_log_model


# ==================== log_creation Tests ====================


@pytest.mark.asyncio
async def test_log_creation_success(mock_uow, mock_logger):
    """Test logging entity creation."""
    service = AuditService(uow=mock_uow, logger=mock_logger)

    entity = MagicMock(id=1)
    audit_log = build_audit_log_model(action="CREATE", entity_type="Product")
    mock_uow.audit_repo.log_action.return_value = audit_log

    with patch("app.application.audit_service.entity_to_snapshot", return_value={"id": 1, "nombre": "Pizza"}):
        result = await service.log_creation(
            username="admin", entity_type="Product", entity=entity
        )

    assert result.status_code == 201
    assert result.value == audit_log
    mock_uow.audit_repo.log_action.assert_called_once()
    mock_uow.commit.assert_called_once()


@pytest.mark.asyncio
async def test_log_creation_sale_type(mock_uow, mock_logger):
    """Test creation logging uses sale_to_snapshot for Sale entities."""
    service = AuditService(uow=mock_uow, logger=mock_logger)

    entity = MagicMock(id=10)
    audit_log = build_audit_log_model(action="CREATE", entity_type="Sale")
    mock_uow.audit_repo.log_action.return_value = audit_log

    with patch("app.application.audit_service.sale_to_snapshot", return_value={"id": 10}) as mock_sale_snap:
        result = await service.log_creation(
            username="admin", entity_type="Sale", entity=entity
        )

    mock_sale_snap.assert_called_once_with(entity)
    assert result.status_code == 201


@pytest.mark.asyncio
async def test_log_creation_entity_without_id(mock_uow, mock_logger):
    """Test creation logging fails when entity has no ID."""
    service = AuditService(uow=mock_uow, logger=mock_logger)

    entity = MagicMock(spec=[])  # no `id` attribute

    with patch("app.application.audit_service.entity_to_snapshot", return_value={}):
        result = await service.log_creation(
            username="admin", entity_type="Product", entity=entity
        )

    assert result.status_code == 400
    assert "ID" in result.error


@pytest.mark.asyncio
async def test_log_creation_error(mock_uow, mock_logger):
    """Test creation logging handles exceptions."""
    service = AuditService(uow=mock_uow, logger=mock_logger)

    entity = MagicMock(id=1)
    mock_uow.audit_repo.log_action.side_effect = Exception("DB error")

    with patch("app.application.audit_service.entity_to_snapshot", return_value={"id": 1}):
        result = await service.log_creation(
            username="admin", entity_type="Product", entity=entity
        )

    assert result.status_code == 500
    assert "Error" in result.error


# ==================== log_update Tests ====================


@pytest.mark.asyncio
async def test_log_update_success(mock_uow, mock_logger):
    """Test logging entity update with changes."""
    service = AuditService(uow=mock_uow, logger=mock_logger)

    old_entity = MagicMock(id=1)
    new_entity = MagicMock(id=1)
    diff = {"nombre": {"old": "Pizza", "new": "Pizza Deluxe"}}
    audit_log = build_audit_log_model(action="UPDATE", changes=diff)
    mock_uow.audit_repo.log_action.return_value = audit_log

    with patch("app.application.audit_service.compute_entity_diff", return_value=diff):
        result = await service.log_update(
            username="admin",
            entity_type="Product",
            old_entity=old_entity,
            new_entity=new_entity,
        )

    assert result.status_code == 201
    assert result.value == audit_log
    mock_uow.commit.assert_called_once()


@pytest.mark.asyncio
async def test_log_update_no_changes(mock_uow, mock_logger):
    """Test logging update with no actual changes returns early."""
    service = AuditService(uow=mock_uow, logger=mock_logger)

    old_entity = MagicMock(id=1)
    new_entity = MagicMock(id=1)

    with patch("app.application.audit_service.compute_entity_diff", return_value={}):
        result = await service.log_update(
            username="admin",
            entity_type="Product",
            old_entity=old_entity,
            new_entity=new_entity,
        )

    assert result.status_code == 200
    assert result.value is None
    mock_uow.audit_repo.log_action.assert_not_called()


@pytest.mark.asyncio
async def test_log_update_sale_uses_sale_diff(mock_uow, mock_logger):
    """Test update logging uses compute_sale_diff for Sale entities."""
    service = AuditService(uow=mock_uow, logger=mock_logger)

    old_sale = MagicMock(id=5)
    new_sale = MagicMock(id=5)
    diff = {"total": {"old": 100, "new": 200}}
    audit_log = build_audit_log_model(action="UPDATE", entity_type="Sale")
    mock_uow.audit_repo.log_action.return_value = audit_log

    with patch("app.application.audit_service.compute_sale_diff", return_value=diff) as mock_sale_diff:
        result = await service.log_update(
            username="admin",
            entity_type="Sale",
            old_entity=old_sale,
            new_entity=new_sale,
        )

    mock_sale_diff.assert_called_once_with(old_sale, new_sale)
    assert result.status_code == 201


@pytest.mark.asyncio
async def test_log_update_entity_without_id(mock_uow, mock_logger):
    """Test update logging fails when entity has no ID."""
    service = AuditService(uow=mock_uow, logger=mock_logger)

    old_entity = MagicMock(id=1)
    new_entity = MagicMock(spec=[])  # no `id` attribute

    with patch("app.application.audit_service.compute_entity_diff", return_value={"x": {"old": 1, "new": 2}}):
        result = await service.log_update(
            username="admin",
            entity_type="Product",
            old_entity=old_entity,
            new_entity=new_entity,
        )

    assert result.status_code == 400


# ==================== log_deletion Tests ====================


@pytest.mark.asyncio
async def test_log_deletion_success(mock_uow, mock_logger):
    """Test logging entity deletion."""
    service = AuditService(uow=mock_uow, logger=mock_logger)

    entity = MagicMock(id=1)
    audit_log = build_audit_log_model(action="DELETE")
    mock_uow.audit_repo.log_action.return_value = audit_log

    with patch("app.application.audit_service.entity_to_snapshot", return_value={"id": 1, "nombre": "Pizza"}):
        result = await service.log_deletion(
            username="admin", entity_type="Product", entity=entity
        )

    assert result.status_code == 201
    assert result.value == audit_log
    # Verify changes contain "old" key
    call_kwargs = mock_uow.audit_repo.log_action.call_args[1]
    assert "old" in call_kwargs["changes"]


@pytest.mark.asyncio
async def test_log_deletion_sale_type(mock_uow, mock_logger):
    """Test deletion logging uses sale_to_snapshot for Sale entities."""
    service = AuditService(uow=mock_uow, logger=mock_logger)

    entity = MagicMock(id=10)
    audit_log = build_audit_log_model(action="DELETE", entity_type="Sale")
    mock_uow.audit_repo.log_action.return_value = audit_log

    with patch("app.application.audit_service.sale_to_snapshot", return_value={"id": 10}) as mock_snap:
        result = await service.log_deletion(
            username="admin", entity_type="Sale", entity=entity
        )

    mock_snap.assert_called_once_with(entity)
    assert result.status_code == 201


# ==================== get_by_date_range Tests ====================


@pytest.mark.asyncio
async def test_get_by_date_range_success(mock_uow, mock_logger):
    """Test getting audit logs by date range."""
    service = AuditService(uow=mock_uow, logger=mock_logger)

    logs = [
        build_audit_log_model(id=1, action="CREATE"),
        build_audit_log_model(id=2, action="UPDATE"),
    ]
    mock_uow.audit_repo.count.return_value = 2
    mock_uow.audit_repo.get_by_date_range.return_value = logs

    start = datetime(2024, 1, 1)
    end = datetime(2024, 12, 31)

    result = await service.get_by_date_range(start_date=start, end_date=end)

    assert result.status_code == 200
    assert result.value["total"] == 2
    assert len(result.value["records"]) == 2


@pytest.mark.asyncio
async def test_get_by_date_range_with_filters(mock_uow, mock_logger):
    """Test getting audit logs with entity_type and username filters."""
    service = AuditService(uow=mock_uow, logger=mock_logger)

    logs = [build_audit_log_model(id=1, entity_type="Product", action="CREATE")]
    mock_uow.audit_repo.count.return_value = 1
    mock_uow.audit_repo.get_by_date_range.return_value = logs

    start = datetime(2024, 1, 1)
    end = datetime(2024, 12, 31)

    result = await service.get_by_date_range(
        start_date=start,
        end_date=end,
        entity_type="Product",
        username="admin",
        action="CREATE",
        limit=50,
        offset=10,
    )

    assert result.status_code == 200
    mock_uow.audit_repo.get_by_date_range.assert_called_once_with(
        start_date=start,
        end_date=end,
        entity_type="Product",
        username="admin",
        action="CREATE",
        limit=50,
        offset=10,
    )


@pytest.mark.asyncio
async def test_get_by_date_range_empty(mock_uow, mock_logger):
    """Test getting audit logs when none exist."""
    service = AuditService(uow=mock_uow, logger=mock_logger)
    mock_uow.audit_repo.count.return_value = 0
    mock_uow.audit_repo.get_by_date_range.return_value = []

    result = await service.get_by_date_range(
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 12, 31),
    )

    assert result.status_code == 200
    assert result.value["total"] == 0
    assert result.value["records"] == []


@pytest.mark.asyncio
async def test_get_by_date_range_error(mock_uow, mock_logger):
    """Test error handling in date range query."""
    service = AuditService(uow=mock_uow, logger=mock_logger)
    mock_uow.audit_repo.count.side_effect = Exception("DB error")

    result = await service.get_by_date_range(
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 12, 31),
    )

    assert result.status_code == 500
    assert "Error" in result.error
