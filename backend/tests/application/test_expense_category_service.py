"""
Tests for ExpenseCategoryService.
Tests expense category CRUD operations with mocked repositories and UnitOfWork.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.application.expense_category_service import ExpenseCategoryService, ServiceResult
from app.presentation.schemas.expense_category_schemas import (
    GastoCategoriaCreateRequest,
    GastoCategoriaUpdateRequest,
)
from tests.helpers import build_expense_category_model


# ==================== Create Tests ====================

@pytest.mark.asyncio
async def test_create_category_success(mock_uow, mock_cache_service, mock_audit_service, mock_logger):
    """Test successful expense category creation."""
    service = ExpenseCategoryService(
        uow=mock_uow, cache_service=mock_cache_service,
        audit_service=mock_audit_service, logger=mock_logger,
    )
    mock_uow.expense_category_repo.refresh = AsyncMock(
        side_effect=lambda c: setattr(c, 'id', 1)
    )

    request = GastoCategoriaCreateRequest(nombre="Insumos")

    result = await service.create(request, username="admin")

    assert result.status_code == 201
    assert result.value is not None
    mock_uow.expense_category_repo.add.assert_called_once()
    mock_uow.commit.assert_called_once()


@pytest.mark.asyncio
async def test_create_category_with_parent(mock_uow, mock_cache_service, mock_audit_service, mock_logger):
    """Test creating subcategory with valid parent."""
    service = ExpenseCategoryService(
        uow=mock_uow, cache_service=mock_cache_service,
        audit_service=mock_audit_service, logger=mock_logger,
    )
    parent = build_expense_category_model(id=1, nombre="Insumos")
    mock_uow.expense_category_repo.get_by_id.return_value = parent
    mock_uow.expense_category_repo.refresh = AsyncMock(
        side_effect=lambda c: setattr(c, 'id', 2)
    )

    request = GastoCategoriaCreateRequest(nombre="Harina", padre_id=1)

    result = await service.create(request, username="admin")

    assert result.status_code == 201


@pytest.mark.asyncio
async def test_create_category_invalid_parent(mock_uow, mock_cache_service, mock_logger):
    """Test creating subcategory with non-existent parent."""
    service = ExpenseCategoryService(
        uow=mock_uow, cache_service=mock_cache_service, logger=mock_logger,
    )
    mock_uow.expense_category_repo.get_by_id.return_value = None

    request = GastoCategoriaCreateRequest(nombre="Sub", padre_id=999)

    result = await service.create(request, username="admin")

    assert result.status_code == 404
    assert "Categoría padre no encontrada" in result.error


@pytest.mark.asyncio
async def test_create_category_error(mock_uow, mock_cache_service, mock_logger):
    """Test creation with database error."""
    service = ExpenseCategoryService(
        uow=mock_uow, cache_service=mock_cache_service, logger=mock_logger,
    )
    mock_uow.expense_category_repo.add.side_effect = Exception("DB error")

    request = GastoCategoriaCreateRequest(nombre="Test")

    result = await service.create(request, username="admin")

    assert result.status_code == 400


# ==================== Get By ID Tests ====================

@pytest.mark.asyncio
async def test_get_by_id_success(mock_uow, mock_cache_service, mock_logger):
    """Test getting expense category by ID."""
    service = ExpenseCategoryService(
        uow=mock_uow, cache_service=mock_cache_service, logger=mock_logger,
    )
    cat = build_expense_category_model(id=1, nombre="Insumos")
    mock_uow.expense_category_repo.get_by_id_with_subcategories.return_value = cat

    result = await service.get_by_id(1)

    assert result.status_code == 200
    assert result.value.id == 1


@pytest.mark.asyncio
async def test_get_by_id_not_found(mock_uow, mock_cache_service, mock_logger):
    """Test getting non-existent expense category."""
    service = ExpenseCategoryService(
        uow=mock_uow, cache_service=mock_cache_service, logger=mock_logger,
    )
    mock_uow.expense_category_repo.get_by_id_with_subcategories.return_value = None

    result = await service.get_by_id(999)

    assert result.status_code == 404
    assert "Categoría de gasto no encontrada" in result.error


# ==================== List Tests ====================

@pytest.mark.asyncio
async def test_list_all_success(mock_uow, mock_cache_service, mock_logger):
    """Test listing all expense categories."""
    service = ExpenseCategoryService(
        uow=mock_uow, cache_service=mock_cache_service, logger=mock_logger,
    )
    cats = [
        build_expense_category_model(1, "Insumos"),
        build_expense_category_model(2, "Servicios"),
    ]
    mock_uow.expense_category_repo.list_by_active.return_value = cats

    result = await service.list_all()

    assert result.status_code == 200
    assert len(result.value) == 2


@pytest.mark.asyncio
async def test_list_by_parent(mock_uow, mock_cache_service, mock_logger):
    """Test listing expense categories by parent."""
    service = ExpenseCategoryService(
        uow=mock_uow, cache_service=mock_cache_service, logger=mock_logger,
    )
    subcats = [build_expense_category_model(2, "Harina", padre_id=1)]
    mock_uow.expense_category_repo.get_by_parent_id.return_value = subcats

    result = await service.list_by_parent(parent_id=1)

    assert result.status_code == 200
    assert len(result.value) == 1


# ==================== Update Tests ====================

@pytest.mark.asyncio
async def test_update_category_success(mock_uow, mock_cache_service, mock_audit_service, mock_logger):
    """Test successful expense category update."""
    service = ExpenseCategoryService(
        uow=mock_uow, cache_service=mock_cache_service,
        audit_service=mock_audit_service, logger=mock_logger,
    )
    cat = build_expense_category_model(id=1, nombre="Insumos")
    mock_uow.expense_category_repo.get_by_id.return_value = cat
    mock_uow.expense_category_repo.refresh = AsyncMock()

    request = GastoCategoriaUpdateRequest(nombre="Insumos Actualizados")

    result = await service.update(1, request, username="admin")

    assert result.status_code == 200
    mock_uow.commit.assert_called_once()


@pytest.mark.asyncio
async def test_update_category_not_found(mock_uow, mock_cache_service, mock_logger):
    """Test updating non-existent expense category."""
    service = ExpenseCategoryService(
        uow=mock_uow, cache_service=mock_cache_service, logger=mock_logger,
    )
    mock_uow.expense_category_repo.get_by_id.return_value = None

    request = GastoCategoriaUpdateRequest(nombre="Test")

    result = await service.update(999, request, username="admin")

    assert result.status_code == 404


@pytest.mark.asyncio
async def test_update_category_invalid_parent(mock_uow, mock_cache_service, mock_logger):
    """Test updating category with invalid new parent."""
    service = ExpenseCategoryService(
        uow=mock_uow, cache_service=mock_cache_service, logger=mock_logger,
    )
    cat = build_expense_category_model(id=2, nombre="Sub", padre_id=1)
    mock_uow.expense_category_repo.get_by_id.side_effect = [cat, None]

    request = GastoCategoriaUpdateRequest(padre_id=999)

    result = await service.update(2, request, username="admin")

    assert result.status_code == 404
    assert "Categoría padre no encontrada" in result.error


# ==================== Delete Tests ====================

@pytest.mark.asyncio
async def test_delete_category_success(mock_uow, mock_cache_service, mock_audit_service, mock_logger):
    """Test successful expense category deletion (soft delete)."""
    service = ExpenseCategoryService(
        uow=mock_uow, cache_service=mock_cache_service,
        audit_service=mock_audit_service, logger=mock_logger,
    )
    cat = build_expense_category_model(id=1, activo=True)
    mock_uow.expense_category_repo.get_by_id.return_value = cat

    result = await service.delete(1, username="admin")

    assert result.status_code == 204
    mock_uow.commit.assert_called_once()


@pytest.mark.asyncio
async def test_delete_category_not_found(mock_uow, mock_cache_service, mock_logger):
    """Test deleting non-existent expense category."""
    service = ExpenseCategoryService(
        uow=mock_uow, cache_service=mock_cache_service, logger=mock_logger,
    )
    mock_uow.expense_category_repo.get_by_id.return_value = None

    result = await service.delete(999, username="admin")

    assert result.status_code == 404
    assert "Categoría de gasto no encontrada" in result.error
