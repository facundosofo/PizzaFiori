"""
Tests for OfferService.
Tests business logic with mocked repositories and UnitOfWork.
"""

import pytest
from unittest.mock import AsyncMock
from decimal import Decimal

from app.application.offer_service import OfferService, ServiceResult
from app.presentation.schemas.offer_schemas import (
    OfferCreateRequest,
    OfferUpdateRequest,
    OfferItemRequest
)
from tests.helpers import build_offer_model, build_product_model


# ==================== Create Tests ====================

@pytest.mark.asyncio
async def test_create_offer_success(mock_uow, mock_logger):
    """Test successful offer creation."""
    # Arrange
    service = OfferService(uow=mock_uow, logger=mock_logger)
    
    request = OfferCreateRequest(
        nombre="Promo Docena",
        descripcion="12 empanadas surtidas",
        precio=Decimal("10000.00"),
        productos=[
            OfferItemRequest(producto_id=1, cantidad=6),
            OfferItemRequest(producto_id=2, cantidad=6)
        ]
    )
    
    # Mock products exist
    mock_uow.product_repo.get_by_id.side_effect = [
        build_product_model(1, "Producto 1", 1),
        build_product_model(2, "Producto 2", 1)
    ]
    mock_uow.offer_repo.refresh = AsyncMock()
    
    # Act
    result = await service.create(request)
    
    # Assert
    assert result.status_code == 201
    assert result.value is not None
    assert result.error is None
    
    # Verify product validation calls
    assert mock_uow.product_repo.get_by_id.call_count == 2
    mock_uow.product_repo.get_by_id.assert_any_call(1)
    mock_uow.product_repo.get_by_id.assert_any_call(2)
    
    # Verify offer creation
    mock_uow.offer_repo.add.assert_called_once()
    mock_uow.commit.assert_called_once()
    mock_uow.offer_repo.refresh.assert_called_once()


@pytest.mark.asyncio
async def test_create_offer_product_not_found(mock_uow, mock_logger):
    """Test creating offer with non-existent product."""
    # Arrange
    service = OfferService(uow=mock_uow, logger=mock_logger)
    
    request = OfferCreateRequest(
        nombre="Promo Invalid",
        precio=Decimal("5000.00"),
        productos=[
            OfferItemRequest(producto_id=999, cantidad=6)
        ]
    )
    
    # Mock product doesn't exist
    mock_uow.product_repo.get_by_id.return_value = None
    
    # Act
    result = await service.create(request)
    
    # Assert
    assert result.status_code == 404
    assert "Producto 999 no encontrado" in result.error
    
    # Verify product validation was called
    mock_uow.product_repo.get_by_id.assert_called_once_with(999)
    
    # Verify offer was not created
    mock_uow.offer_repo.add.assert_not_called()
    mock_uow.commit.assert_not_called()


@pytest.mark.asyncio
async def test_create_offer_validates_all_products(mock_uow, mock_logger):
    """Test that all products are validated before creation."""
    # Arrange
    service = OfferService(uow=mock_uow, logger=mock_logger)
    
    request = OfferCreateRequest(
        nombre="Promo Test",
        precio=Decimal("8000.00"),
        productos=[
            OfferItemRequest(producto_id=1, cantidad=3),
            OfferItemRequest(producto_id=2, cantidad=3),
            OfferItemRequest(producto_id=999, cantidad=6)  # Invalid
        ]
    )
    
    # Mock: first two exist, third doesn't
    mock_uow.product_repo.get_by_id.side_effect = [
        build_product_model(1, "Producto 1", 1),
        build_product_model(2, "Producto 2", 1),
        None  # Product 999 doesn't exist
    ]
    
    # Act
    result = await service.create(request)
    
    # Assert
    assert result.status_code == 404
    assert "Producto 999 no encontrado" in result.error
    
    # Verify all products were checked
    assert mock_uow.product_repo.get_by_id.call_count == 3


@pytest.mark.asyncio
async def test_create_offer_database_error(mock_uow, mock_logger):
    """Test offer creation with database error."""
    # Arrange
    service = OfferService(uow=mock_uow, logger=mock_logger)
    
    request = OfferCreateRequest(
        nombre="Test Offer",
        precio=Decimal("5000.00"),
        productos=[
            OfferItemRequest(producto_id=1, cantidad=6)
        ]
    )
    
    mock_uow.product_repo.get_by_id.return_value = build_product_model(1, "Test", 1)
    mock_uow.offer_repo.add.side_effect = Exception("Database error")
    
    # Act
    result = await service.create(request)
    
    # Assert
    assert result.status_code == 400
    assert result.error == "Database error"
    mock_logger.error.assert_called_once()


# ==================== Get By ID Tests ====================

@pytest.mark.asyncio
async def test_get_by_id_success(mock_uow, mock_logger, sample_offer):
    """Test getting offer by ID successfully."""
    # Arrange
    service = OfferService(uow=mock_uow, logger=mock_logger)
    mock_uow.offer_repo.get_by_id.return_value = sample_offer
    
    # Act
    result = await service.get_by_id(1)
    
    # Assert
    assert result.status_code == 200
    assert result.value is not None
    assert result.value.id == 1
    mock_uow.offer_repo.get_by_id.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_get_by_id_not_found(mock_uow, mock_logger):
    """Test getting offer by ID when it doesn't exist."""
    # Arrange
    service = OfferService(uow=mock_uow, logger=mock_logger)
    mock_uow.offer_repo.get_by_id.return_value = None
    
    # Act
    result = await service.get_by_id(999)
    
    # Assert
    assert result.status_code == 404
    assert "Oferta 999 no encontrada" in result.error
    mock_uow.offer_repo.get_by_id.assert_called_once_with(999)


# ==================== Get All Tests ====================

@pytest.mark.asyncio
async def test_get_all_offers(mock_uow, mock_logger):
    """Test getting all offers."""
    # Arrange
    service = OfferService(uow=mock_uow, logger=mock_logger)
    offers = [
        build_offer_model(1, "Promo 1", None, 10000.0, True),
        build_offer_model(2, "Promo 2", None, 8000.0, True)
    ]
    mock_uow.offer_repo.list.return_value = offers
    
    # Act
    result = await service.get_all()
    
    # Assert
    assert len(result) == 2
    mock_uow.offer_repo.list.assert_called_once_with(active=None)


@pytest.mark.asyncio
async def test_get_all_offers_active_filter(mock_uow, mock_logger):
    """Test getting only active offers."""
    # Arrange
    service = OfferService(uow=mock_uow, logger=mock_logger)
    active_offers = [build_offer_model(1, "Active", None, 5000.0, True)]
    mock_uow.offer_repo.list.return_value = active_offers
    
    # Act
    result = await service.get_all(active=True)
    
    # Assert
    assert len(result) == 1
    assert result[0].activo == True
    mock_uow.offer_repo.list.assert_called_once_with(active=True)


@pytest.mark.asyncio
async def test_get_all_offers_error(mock_uow, mock_logger):
    """Test getting offers with database error returns empty list."""
    # Arrange
    service = OfferService(uow=mock_uow, logger=mock_logger)
    mock_uow.offer_repo.list.side_effect = Exception("Database error")
    
    # Act
    result = await service.get_all()
    
    # Assert
    assert result == []
    mock_logger.error.assert_called_once()


# ==================== Update Tests ====================

@pytest.mark.asyncio
async def test_update_offer_basic_fields(mock_uow, mock_logger, sample_offer):
    """Test updating basic offer fields."""
    # Arrange
    service = OfferService(uow=mock_uow, logger=mock_logger)
    mock_uow.offer_repo.get_by_id.return_value = sample_offer
    mock_uow.offer_repo.refresh = AsyncMock()
    
    request = OfferUpdateRequest(
        nombre="Nuevo Nombre",
        precio=Decimal("12000.00")
    )
    
    # Act
    result = await service.update(1, offer_update=request)
    
    # Assert
    assert result.status_code == 200
    assert result.value is not None
    mock_uow.offer_repo.get_by_id.assert_called_once_with(1)
    mock_uow.offer_repo.update.assert_called_once()
    mock_uow.commit.assert_called_once()


@pytest.mark.asyncio
async def test_update_offer_with_products(mock_uow, mock_logger, sample_offer):
    """Test updating offer products calls replace_items."""
    # Arrange
    service = OfferService(uow=mock_uow, logger=mock_logger)
    mock_uow.offer_repo.get_by_id.return_value = sample_offer
    mock_uow.offer_repo.refresh = AsyncMock()
    
    # Import to check isinstance
    from app.infrastructure.repositories.offer_repository import SqlAlchemyOfferRepository
    mock_uow.offer_repo.__class__ = SqlAlchemyOfferRepository
    mock_uow.offer_repo.replace_items = AsyncMock()
    
    request = OfferUpdateRequest(
        productos=[
            OfferItemRequest(producto_id=3, cantidad=12)
        ]
    )
    
    # Mock product exists
    mock_uow.product_repo.get_by_id.return_value = build_product_model(3, "Producto 3", 1)
    
    # Act
    result = await service.update(1, offer_update=request)
    
    # Assert
    assert result.status_code == 200
    
    # Verify product validation
    mock_uow.product_repo.get_by_id.assert_called_once_with(3)
    
    # Verify replace_items was called
    mock_uow.offer_repo.replace_items.assert_called_once()


@pytest.mark.asyncio
async def test_update_offer_product_not_found(mock_uow, mock_logger, sample_offer):
    """Test updating offer with non-existent product."""
    # Arrange
    service = OfferService(uow=mock_uow, logger=mock_logger)
    mock_uow.offer_repo.get_by_id.return_value = sample_offer
    
    request = OfferUpdateRequest(
        productos=[
            OfferItemRequest(producto_id=999, cantidad=6)
        ]
    )
    
    mock_uow.product_repo.get_by_id.return_value = None
    
    # Act
    result = await service.update(1, offer_update=request)
    
    # Assert
    assert result.status_code == 404
    assert "Producto 999 no encontrado" in result.error
    mock_uow.offer_repo.update.assert_not_called()


@pytest.mark.asyncio
async def test_update_offer_deactivate(mock_uow, mock_logger, sample_offer):
    """Test deactivating offer."""
    # Arrange
    service = OfferService(uow=mock_uow, logger=mock_logger)
    mock_uow.offer_repo.get_by_id.return_value = sample_offer
    mock_uow.offer_repo.refresh = AsyncMock()
    
    request = OfferUpdateRequest()
    
    # Act
    result = await service.update(1, offer_update=request, active=False)
    
    # Assert
    assert result.status_code == 200
    mock_uow.offer_repo.update.assert_called_once()
    mock_uow.commit.assert_called_once()


@pytest.mark.asyncio
async def test_update_offer_not_found(mock_uow, mock_logger):
    """Test updating offer that doesn't exist."""
    # Arrange
    service = OfferService(uow=mock_uow, logger=mock_logger)
    mock_uow.offer_repo.get_by_id.return_value = None
    
    request = OfferUpdateRequest(nombre="Test")
    
    # Act
    result = await service.update(999, offer_update=request)
    
    # Assert
    assert result.status_code == 404
    assert "Oferta 999 no encontrada" in result.error
    mock_uow.offer_repo.update.assert_not_called()
