"""
Tests for ExpenseService.
Tests expense CRUD operations with mocked repositories and UnitOfWork.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import date
from decimal import Decimal

from app.application.expense_service import ExpenseService, ServiceResult
from app.presentation.schemas.expense_schemas import (
    GastoCreateRequest,
    GastoUpdateRequest,
)
from tests.helpers import build_expense_model, build_expense_category_model


# ==================== Create Tests ====================

@pytest.mark.asyncio
async def test_create_expense_success(mock_uow, mock_cache_service, mock_audit_service, mock_logger):
    """Test successful expense creation."""
    service = ExpenseService(
        uow=mock_uow, cache_service=mock_cache_service,
        audit_service=mock_audit_service, logger=mock_logger,
    )
    categoria = build_expense_category_model(id=1, nombre="Insumos")
    mock_uow.expense_category_repo.get_by_id.return_value = categoria
    mock_uow.expense_repo.refresh = AsyncMock(side_effect=lambda g: setattr(g, 'id', 1))

    request = GastoCreateRequest(
        categoria_gasto_id=1,
        descripcion="Compra de harina",
        monto=Decimal("5000.00"),
        fecha_pago=date.today(),
    )

    result = await service.create(request, username="admin")

    assert result.status_code == 201
    assert result.value is not None
    mock_uow.expense_repo.add.assert_called_once()
    mock_uow.commit.assert_called_once()


@pytest.mark.asyncio
async def test_create_expense_category_not_found(mock_uow, mock_cache_service, mock_logger):
    """Test creating expense with non-existent category."""
    service = ExpenseService(
        uow=mock_uow, cache_service=mock_cache_service, logger=mock_logger,
    )
    mock_uow.expense_category_repo.get_by_id.return_value = None

    request = GastoCreateRequest(
        categoria_gasto_id=999,
        descripcion="Test",
        monto=Decimal("100.00"),
        fecha_pago=date.today(),
    )

    result = await service.create(request, username="admin")

    assert result.status_code == 404
    assert "Categoría de gasto no encontrada" in result.error
    mock_uow.expense_repo.add.assert_not_called()


@pytest.mark.asyncio
async def test_create_expense_error(mock_uow, mock_cache_service, mock_logger):
    """Test expense creation with database error."""
    service = ExpenseService(
        uow=mock_uow, cache_service=mock_cache_service, logger=mock_logger,
    )
    categoria = build_expense_category_model(id=1)
    mock_uow.expense_category_repo.get_by_id.return_value = categoria
    mock_uow.expense_repo.add.side_effect = Exception("DB error")

    request = GastoCreateRequest(
        categoria_gasto_id=1,
        descripcion="Test",
        monto=Decimal("100.00"),
        fecha_pago=date.today(),
    )

    result = await service.create(request, username="admin")

    assert result.status_code == 400
    assert result.error == "DB error"


# ==================== Get By ID Tests ====================

@pytest.mark.asyncio
async def test_get_by_id_success(mock_uow, mock_cache_service, mock_logger):
    """Test getting expense by ID."""
    service = ExpenseService(
        uow=mock_uow, cache_service=mock_cache_service, logger=mock_logger,
    )
    expense = build_expense_model(id=1)
    mock_uow.expense_repo.get_by_id_with_category.return_value = expense

    result = await service.get_by_id(1)

    assert result.status_code == 200
    assert result.value.id == 1


@pytest.mark.asyncio
async def test_get_by_id_not_found(mock_uow, mock_cache_service, mock_logger):
    """Test getting non-existent expense."""
    service = ExpenseService(
        uow=mock_uow, cache_service=mock_cache_service, logger=mock_logger,
    )
    mock_uow.expense_repo.get_by_id_with_category.return_value = None

    result = await service.get_by_id(999)

    assert result.status_code == 404
    assert "Gasto no encontrado" in result.error


@pytest.mark.asyncio
async def test_get_by_id_from_cache(mock_uow, mock_cache_service, mock_logger):
    """Test getting expense from cache."""
    service = ExpenseService(
        uow=mock_uow, cache_service=mock_cache_service, logger=mock_logger,
    )
    cached_expense = build_expense_model(id=1)
    mock_cache_service.get.return_value = cached_expense

    result = await service.get_by_id(1)

    assert result.status_code == 200
    assert result.value.id == 1
    mock_uow.expense_repo.get_by_id_with_category.assert_not_called()


# ==================== List Tests ====================

@pytest.mark.asyncio
async def test_list_all_success(mock_uow, mock_cache_service, mock_logger):
    """Test listing all expenses."""
    service = ExpenseService(
        uow=mock_uow, cache_service=mock_cache_service, logger=mock_logger,
    )
    expenses = [build_expense_model(1), build_expense_model(2)]
    mock_uow.expense_repo.list.return_value = expenses

    result = await service.list_all()

    assert result.status_code == 200
    assert len(result.value) == 2


@pytest.mark.asyncio
async def test_list_by_filters(mock_uow, mock_cache_service, mock_logger):
    """Test listing expenses with filters."""
    service = ExpenseService(
        uow=mock_uow, cache_service=mock_cache_service, logger=mock_logger,
    )
    filtered = [build_expense_model(1)]
    mock_uow.expense_repo.list_by_filters.return_value = filtered
    mock_uow.expense_category_repo.get_by_id.return_value = build_expense_category_model(id=1, padre_id=None)
    mock_uow.expense_category_repo.get_by_parent_id.return_value = []

    result = await service.list_by_filters(
        fecha_desde=date(2025, 1, 1),
        fecha_hasta=date(2025, 12, 31),
        categoria_gasto_id=1,
    )

    assert result.status_code == 200


# ==================== Update Tests ====================

@pytest.mark.asyncio
async def test_update_expense_success(mock_uow, mock_cache_service, mock_audit_service, mock_logger):
    """Test successful expense update."""
    service = ExpenseService(
        uow=mock_uow, cache_service=mock_cache_service,
        audit_service=mock_audit_service, logger=mock_logger,
    )
    expense = build_expense_model(id=1, monto=5000.0)
    mock_uow.expense_repo.get_by_id.return_value = expense
    mock_uow.expense_repo.refresh = AsyncMock()

    request = GastoUpdateRequest(monto=Decimal("7500.00"))

    result = await service.update(1, request, username="admin")

    assert result.status_code == 200
    mock_uow.commit.assert_called_once()


@pytest.mark.asyncio
async def test_update_expense_not_found(mock_uow, mock_cache_service, mock_logger):
    """Test updating non-existent expense."""
    service = ExpenseService(
        uow=mock_uow, cache_service=mock_cache_service, logger=mock_logger,
    )
    mock_uow.expense_repo.get_by_id.return_value = None

    request = GastoUpdateRequest(monto=Decimal("100"))

    result = await service.update(999, request, username="admin")

    assert result.status_code == 404


@pytest.mark.asyncio
async def test_update_expense_invalid_category(mock_uow, mock_cache_service, mock_logger):
    """Test updating expense with invalid new category."""
    service = ExpenseService(
        uow=mock_uow, cache_service=mock_cache_service, logger=mock_logger,
    )
    expense = build_expense_model(id=1, categoria_gasto_id=1)
    mock_uow.expense_repo.get_by_id.return_value = expense
    mock_uow.expense_category_repo.get_by_id.return_value = None

    request = GastoUpdateRequest(categoria_gasto_id=999)

    result = await service.update(1, request, username="admin")

    assert result.status_code == 404
    assert "Categoría de gasto no encontrada" in result.error


# ==================== Delete Tests ====================

@pytest.mark.asyncio
async def test_delete_expense_success(mock_uow, mock_cache_service, mock_audit_service, mock_logger):
    """Test successful expense deletion (soft delete)."""
    service = ExpenseService(
        uow=mock_uow, cache_service=mock_cache_service,
        audit_service=mock_audit_service, logger=mock_logger,
    )
    expense = build_expense_model(id=1, activo=True)
    mock_uow.expense_repo.get_by_id.return_value = expense

    result = await service.delete(1, username="admin")

    assert result.status_code == 204
    mock_uow.commit.assert_called_once()


@pytest.mark.asyncio
async def test_delete_expense_not_found(mock_uow, mock_cache_service, mock_logger):
    """Test deleting non-existent expense."""
    service = ExpenseService(
        uow=mock_uow, cache_service=mock_cache_service, logger=mock_logger,
    )
    mock_uow.expense_repo.get_by_id.return_value = None

    result = await service.delete(999, username="admin")

    assert result.status_code == 404
    assert "Gasto no encontrado" in result.error
