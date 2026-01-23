"""
Tests for CategoryService.
Tests business logic with mocked repositories and UnitOfWork.
"""

import pytest
from unittest.mock import AsyncMock

from app.application.category_service import CategoryService, ServiceResult
from app.domain.models.category import Category
from app.presentation.schemas.category_schemas import (
    CategoriaCreateRequest,
    CategoriaUpdateRequest
)
from tests.helpers import build_category_model


# ==================== Create Tests ====================

@pytest.mark.asyncio
async def test_create_category_success(mock_uow, mock_logger):
    """Test successful category creation."""
    # Arrange
    service = CategoryService(uow=mock_uow, logger=mock_logger)
    request = CategoriaCreateRequest(
        nombre="Empanadas",
        descripcion="Empanadas artesanales"
    )
    
    created_category = build_category_model(
        id=1,
        nombre="Empanadas",
        descripcion="Empanadas artesanales"
    )
    mock_uow.category_repo.refresh = AsyncMock(side_effect=lambda cat: setattr(cat, 'id', 1))
    
    # Act
    result = await service.create(request)
    
    # Assert
    assert result.status_code == 201
    assert result.value is not None
    assert result.error is None
    
    # Verify mock calls
    mock_uow.category_repo.add.assert_called_once()
    mock_uow.commit.assert_called_once()
    mock_uow.category_repo.refresh.assert_called_once()
    
    # Verify logger calls
    assert mock_logger.debug.call_count >= 2


@pytest.mark.asyncio
async def test_create_category_without_descripcion(mock_uow, mock_logger):
    """Test creating category without optional description."""
    # Arrange
    service = CategoryService(uow=mock_uow, logger=mock_logger)
    request = CategoriaCreateRequest(nombre="Pizzas")
    
    mock_uow.category_repo.refresh = AsyncMock()
    
    # Act
    result = await service.create(request)
    
    # Assert
    assert result.status_code == 201
    assert result.value is not None
    mock_uow.category_repo.add.assert_called_once()
    mock_uow.commit.assert_called_once()


@pytest.mark.asyncio
async def test_create_category_error(mock_uow, mock_logger):
    """Test category creation with database error."""
    # Arrange
    service = CategoryService(uow=mock_uow, logger=mock_logger)
    request = CategoriaCreateRequest(nombre="Test")
    
    mock_uow.category_repo.add.side_effect = Exception("Database error")
    
    # Act
    result = await service.create(request)
    
    # Assert
    assert result.status_code == 400
    assert result.value is None
    assert result.error == "Database error"
    
    # Verify error logging
    mock_logger.error.assert_called_once()


# ==================== Get All Tests ====================

@pytest.mark.asyncio
async def test_get_all_categories_success(mock_uow, mock_logger, multiple_categories):
    """Test getting all categories."""
    # Arrange
    service = CategoryService(uow=mock_uow, logger=mock_logger)
    mock_uow.category_repo.list.return_value = multiple_categories
    
    # Act
    result = await service.get_all()
    
    # Assert
    assert len(result) == 3
    assert result[0].nombre == "Empanadas"
    assert result[1].nombre == "Pizzas"
    assert result[2].nombre == "Bebidas"
    
    # Verify mock call
    mock_uow.category_repo.list.assert_called_once()


@pytest.mark.asyncio
async def test_get_all_categories_empty(mock_uow, mock_logger):
    """Test getting all categories when none exist."""
    # Arrange
    service = CategoryService(uow=mock_uow, logger=mock_logger)
    mock_uow.category_repo.list.return_value = []
    
    # Act
    result = await service.get_all()
    
    # Assert
    assert len(result) == 0
    mock_uow.category_repo.list.assert_called_once()


# ==================== Get By ID Tests ====================

@pytest.mark.asyncio
async def test_get_by_id_success(mock_uow, mock_logger, sample_category):
    """Test getting category by ID successfully."""
    # Arrange
    service = CategoryService(uow=mock_uow, logger=mock_logger)
    mock_uow.category_repo.get_by_id.return_value = sample_category
    
    # Act
    result = await service.get_by_id(1)
    
    # Assert
    assert result.status_code == 200
    assert result.value is not None
    assert result.value.id == 1
    assert result.value.nombre == "Empanadas"
    assert result.error is None
    
    # Verify mock call
    mock_uow.category_repo.get_by_id.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_get_by_id_not_found(mock_uow, mock_logger):
    """Test getting category by ID when it doesn't exist."""
    # Arrange
    service = CategoryService(uow=mock_uow, logger=mock_logger)
    mock_uow.category_repo.get_by_id.return_value = None
    
    # Act
    result = await service.get_by_id(999)
    
    # Assert
    assert result.status_code == 404
    assert result.value is None
    assert result.error == "Categoría no encontrada"
    
    # Verify mock call
    mock_uow.category_repo.get_by_id.assert_called_once_with(999)


# ==================== Update Tests ====================

@pytest.mark.asyncio
async def test_update_category_success(mock_uow, mock_logger, sample_category):
    """Test updating category successfully."""
    # Arrange
    service = CategoryService(uow=mock_uow, logger=mock_logger)
    mock_uow.category_repo.get_by_id.return_value = sample_category
    mock_uow.category_repo.refresh = AsyncMock()
    
    request = CategoriaUpdateRequest(
        nombre="Empanadas Premium",
        descripcion="Nueva descripción"
    )
    
    # Act
    result = await service.update(1, request)
    
    # Assert
    assert result.status_code == 200
    assert result.value is not None
    assert result.error is None
    
    # Verify mock calls
    mock_uow.category_repo.get_by_id.assert_called_once_with(1)
    mock_uow.commit.assert_called_once()
    mock_uow.category_repo.refresh.assert_called_once()


@pytest.mark.asyncio
async def test_update_category_partial(mock_uow, mock_logger, sample_category):
    """Test partial update of category (only nombre)."""
    # Arrange
    service = CategoryService(uow=mock_uow, logger=mock_logger)
    mock_uow.category_repo.get_by_id.return_value = sample_category
    mock_uow.category_repo.refresh = AsyncMock()
    
    request = CategoriaUpdateRequest(nombre="Nuevo Nombre")
    
    # Act
    result = await service.update(1, request)
    
    # Assert
    assert result.status_code == 200
    assert result.value is not None
    mock_uow.commit.assert_called_once()


@pytest.mark.asyncio
async def test_update_category_not_found(mock_uow, mock_logger):
    """Test updating category that doesn't exist."""
    # Arrange
    service = CategoryService(uow=mock_uow, logger=mock_logger)
    mock_uow.category_repo.get_by_id.return_value = None
    
    request = CategoriaUpdateRequest(nombre="Test")
    
    # Act
    result = await service.update(999, request)
    
    # Assert
    assert result.status_code == 404
    assert result.value is None
    assert result.error == "Categoría no encontrada"
    
    # Verify get was called but not commit
    mock_uow.category_repo.get_by_id.assert_called_once_with(999)
    mock_uow.commit.assert_not_called()


@pytest.mark.asyncio
async def test_update_category_error(mock_uow, mock_logger, sample_category):
    """Test update category with database error."""
    # Arrange
    service = CategoryService(uow=mock_uow, logger=mock_logger)
    mock_uow.category_repo.get_by_id.return_value = sample_category
    mock_uow.commit.side_effect = Exception("Database error")
    
    request = CategoriaUpdateRequest(nombre="Test")
    
    # Act
    result = await service.update(1, request)
    
    # Assert
    assert result.status_code == 400
    assert result.value is None
    assert result.error == "Database error"


# ==================== Delete Tests ====================

@pytest.mark.asyncio
async def test_delete_category_success(mock_uow, mock_logger, sample_category):
    """Test deleting category successfully."""
    # Arrange
    service = CategoryService(uow=mock_uow, logger=mock_logger)
    mock_uow.category_repo.get_by_id.return_value = sample_category
    
    # Act
    result = await service.delete(1)
    
    # Assert
    assert result.status_code == 200
    assert result.error is None
    
    # Verify mock calls
    mock_uow.category_repo.get_by_id.assert_called_once_with(1)
    mock_uow.category_repo.delete.assert_called_once_with(sample_category)
    mock_uow.commit.assert_called_once()


@pytest.mark.asyncio
async def test_delete_category_not_found(mock_uow, mock_logger):
    """Test deleting category that doesn't exist."""
    # Arrange
    service = CategoryService(uow=mock_uow, logger=mock_logger)
    mock_uow.category_repo.get_by_id.return_value = None
    
    # Act
    result = await service.delete(999)
    
    # Assert
    assert result.status_code == 404
    assert result.error == "Categoría no encontrada"
    
    # Verify get was called but not delete or commit
    mock_uow.category_repo.get_by_id.assert_called_once_with(999)
    mock_uow.category_repo.delete.assert_not_called()
    mock_uow.commit.assert_not_called()


@pytest.mark.asyncio
async def test_delete_category_error(mock_uow, mock_logger, sample_category):
    """Test delete category with database error."""
    # Arrange
    service = CategoryService(uow=mock_uow, logger=mock_logger)
    mock_uow.category_repo.get_by_id.return_value = sample_category
    mock_uow.category_repo.delete.side_effect = Exception("Database constraint error")
    
    # Act
    result = await service.delete(1)
    
    # Assert
    assert result.status_code == 400
    assert result.error == "Database constraint error"
