"""
Tests for ProductCategoryService.
Tests business logic with mocked repositories and UnitOfWork.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.application.product_category_service import ProductCategoryService, ServiceResult
from app.presentation.schemas.product_category_schemas import (
    ProductoCategoriaCreateRequest,
    ProductoCategoriaUpdateRequest,
)
from tests.helpers import build_category_model


# ==================== Create Tests ====================

@pytest.mark.asyncio
async def test_create_category_success(mock_uow, mock_cache_service, mock_audit_service, mock_logger):
    """Test successful category creation."""
    service = ProductCategoryService(
        uow=mock_uow, cache_service=mock_cache_service,
        audit_service=mock_audit_service, logger=mock_logger,
    )
    request = ProductoCategoriaCreateRequest(nombre="Empanadas")

    mock_uow.product_category_repo.refresh = AsyncMock(
        side_effect=lambda cat: setattr(cat, 'id', 1)
    )

    result = await service.create(request, username="admin")

    assert result.status_code == 201
    assert result.value is not None
    assert result.error is None
    mock_uow.product_category_repo.add.assert_called_once()
    mock_uow.commit.assert_called_once()


@pytest.mark.asyncio
async def test_create_category_error(mock_uow, mock_cache_service, mock_logger):
    """Test category creation with database error."""
    service = ProductCategoryService(
        uow=mock_uow, cache_service=mock_cache_service, logger=mock_logger,
    )
    request = ProductoCategoriaCreateRequest(nombre="Test")
    mock_uow.product_category_repo.add.side_effect = Exception("Database error")

    result = await service.create(request, username="admin")

    assert result.status_code == 400
    assert result.value is None
    assert result.error == "Database error"


# ==================== Get All Tests ====================

@pytest.mark.asyncio
async def test_get_all_categories_success(mock_uow, mock_cache_service, mock_logger, multiple_categories):
    """Test getting all categories."""
    service = ProductCategoryService(
        uow=mock_uow, cache_service=mock_cache_service, logger=mock_logger,
    )
    mock_uow.product_category_repo.list.return_value = multiple_categories

    result = await service.get_all()

    assert len(result) == 3
    assert result[0].nombre == "Empanadas"
    assert result[1].nombre == "Pizzas"
    assert result[2].nombre == "Bebidas"


@pytest.mark.asyncio
async def test_get_all_categories_empty(mock_uow, mock_cache_service, mock_logger):
    """Test getting all categories when none exist."""
    service = ProductCategoryService(
        uow=mock_uow, cache_service=mock_cache_service, logger=mock_logger,
    )
    mock_uow.product_category_repo.list.return_value = []

    result = await service.get_all()

    assert len(result) == 0


@pytest.mark.asyncio
async def test_get_all_categories_filtered_by_active(mock_uow, mock_cache_service, mock_logger):
    """Test getting only active categories."""
    service = ProductCategoryService(
        uow=mock_uow, cache_service=mock_cache_service, logger=mock_logger,
    )
    active_cats = [build_category_model(1, "Empanadas")]
    mock_uow.product_category_repo.list_by_active.return_value = active_cats

    result = await service.get_all(activo=True)

    assert len(result) == 1
    mock_uow.product_category_repo.list_by_active.assert_called_once_with(True)


# ==================== Get By ID Tests ====================

@pytest.mark.asyncio
async def test_get_by_id_success(mock_uow, mock_cache_service, mock_logger, sample_category):
    """Test getting category by ID successfully."""
    service = ProductCategoryService(
        uow=mock_uow, cache_service=mock_cache_service, logger=mock_logger,
    )
    mock_uow.product_category_repo.get_by_id.return_value = sample_category

    result = await service.get_by_id(1)

    assert result.status_code == 200
    assert result.value is not None
    assert result.value.id == 1
    assert result.value.nombre == "Empanadas"
    assert result.error is None


@pytest.mark.asyncio
async def test_get_by_id_not_found(mock_uow, mock_cache_service, mock_logger):
    """Test getting category by ID when it doesn't exist."""
    service = ProductCategoryService(
        uow=mock_uow, cache_service=mock_cache_service, logger=mock_logger,
    )
    mock_uow.product_category_repo.get_by_id.return_value = None

    result = await service.get_by_id(999)

    assert result.status_code == 404
    assert result.value is None
    assert result.error == "Categoría no encontrada"


# ==================== Update Tests ====================

@pytest.mark.asyncio
async def test_update_category_success(mock_uow, mock_cache_service, mock_audit_service, mock_logger, sample_category):
    """Test updating category successfully."""
    service = ProductCategoryService(
        uow=mock_uow, cache_service=mock_cache_service,
        audit_service=mock_audit_service, logger=mock_logger,
    )
    mock_uow.product_category_repo.get_by_id.return_value = sample_category
    mock_uow.product_category_repo.refresh = AsyncMock()

    request = ProductoCategoriaUpdateRequest(
        nombre="Empanadas Premium",
    )

    result = await service.update(1, request, username="admin")

    assert result.status_code == 200
    assert result.value is not None
    assert result.error is None
    mock_uow.commit.assert_called_once()


@pytest.mark.asyncio
async def test_update_category_not_found(mock_uow, mock_cache_service, mock_logger):
    """Test updating category that doesn't exist."""
    service = ProductCategoryService(
        uow=mock_uow, cache_service=mock_cache_service, logger=mock_logger,
    )
    mock_uow.product_category_repo.get_by_id.return_value = None
    request = ProductoCategoriaUpdateRequest(nombre="Test")

    result = await service.update(999, request, username="admin")

    assert result.status_code == 404
    assert result.value is None
    assert result.error == "Categoría no encontrada"
    mock_uow.commit.assert_not_called()


@pytest.mark.asyncio
async def test_update_category_error(mock_uow, mock_cache_service, mock_logger, sample_category):
    """Test update category with database error."""
    service = ProductCategoryService(
        uow=mock_uow, cache_service=mock_cache_service, logger=mock_logger,
    )
    mock_uow.product_category_repo.get_by_id.return_value = sample_category
    mock_uow.commit.side_effect = Exception("Database error")
    request = ProductoCategoriaUpdateRequest(nombre="Test")

    result = await service.update(1, request, username="admin")

    assert result.status_code == 400
    assert result.value is None
    assert result.error == "Database error"


# ==================== Deactivate Tests ====================

@pytest.mark.asyncio
async def test_deactivate_category_success(mock_uow, mock_cache_service, mock_audit_service, mock_logger, sample_category):
    """Test deactivating category successfully (cascade)."""
    service = ProductCategoryService(
        uow=mock_uow, cache_service=mock_cache_service,
        audit_service=mock_audit_service, logger=mock_logger,
    )
    sample_category.activo = True
    mock_uow.product_category_repo.get_by_id.return_value = sample_category
    mock_uow.product_repo.list.return_value = []
    mock_uow.product_category_repo.refresh = AsyncMock()

    result = await service.deactivate(1, username="admin")

    assert result.status_code == 200
    assert result.error is None
    mock_uow.commit.assert_called_once()


@pytest.mark.asyncio
async def test_deactivate_category_not_found(mock_uow, mock_cache_service, mock_logger):
    """Test deactivating category that doesn't exist."""
    service = ProductCategoryService(
        uow=mock_uow, cache_service=mock_cache_service, logger=mock_logger,
    )
    mock_uow.product_category_repo.get_by_id.return_value = None

    result = await service.deactivate(999, username="admin")

    assert result.status_code == 404
    assert result.error == "Categoría no encontrada"
    mock_uow.commit.assert_not_called()


@pytest.mark.asyncio
async def test_deactivate_category_with_products(mock_uow, mock_cache_service, mock_audit_service, mock_logger, sample_category):
    """Test deactivating category cascades to products and offers."""
    service = ProductCategoryService(
        uow=mock_uow, cache_service=mock_cache_service,
        audit_service=mock_audit_service, logger=mock_logger,
    )
    sample_category.activo = True
    mock_uow.product_category_repo.get_by_id.return_value = sample_category

    product1 = MagicMock(id=1, activo=True)
    product2 = MagicMock(id=2, activo=True)
    mock_uow.product_repo.list.return_value = [product1, product2]
    mock_uow.offer_repo.get_by_products.return_value = [MagicMock(id=10)]
    mock_uow.offer_repo.deactivate_by_products = AsyncMock()
    mock_uow.product_category_repo.refresh = AsyncMock()

    result = await service.deactivate(1, username="admin")

    assert result.status_code == 200
    assert product1.activo is False
    assert product2.activo is False
    mock_uow.offer_repo.deactivate_by_products.assert_called_once_with([1, 2])
    mock_uow.commit.assert_called_once()


@pytest.mark.asyncio
async def test_deactivate_category_error(mock_uow, mock_cache_service, mock_logger, sample_category):
    """Test deactivate category with database error."""
    service = ProductCategoryService(
        uow=mock_uow, cache_service=mock_cache_service, logger=mock_logger,
    )
    mock_uow.product_category_repo.get_by_id.return_value = sample_category
    mock_uow.product_repo.list.side_effect = Exception("Database constraint error")

    result = await service.deactivate(1, username="admin")

    assert result.status_code == 400
    assert result.error == "Database constraint error"
