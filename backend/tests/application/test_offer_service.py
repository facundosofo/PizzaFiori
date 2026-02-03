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
from tests.helpers import build_offer_model, build_product_model, build_category_model


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
    
    # Mock products exist (called twice per product: validation + relationship)
    mock_uow.product_repo.get_by_id.side_effect = [
        build_product_model(1, "Producto 1", 1),  # Validation
        build_product_model(2, "Producto 2", 1),  # Validation
        build_product_model(1, "Producto 1", 1),  # Relationship
        build_product_model(2, "Producto 2", 1),  # Relationship
    ]

    async def _add_side_effect(offer):
        offer.id = 1
        return offer

    mock_uow.offer_repo.add.side_effect = _add_side_effect
    mock_uow.offer_repo.get_by_id.return_value = build_offer_model(1, "Promo Docena", "12 empanadas surtidas", 10000.0, True)
    
    # Act
    result = await service.create(request)
    
    # Assert
    assert result.status_code == 201
    assert result.value is not None
    assert result.error is None
    
    # Verify product validation calls (2 for validation + 2 for relationships)
    assert mock_uow.product_repo.get_by_id.call_count == 4
    mock_uow.product_repo.get_by_id.assert_any_call(1)
    mock_uow.product_repo.get_by_id.assert_any_call(2)
    
    # Verify offer creation
    mock_uow.offer_repo.add.assert_called_once()
    mock_uow.commit.assert_called_once()
    mock_uow.offer_repo.get_by_id.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_create_offer_success_with_categoria_item(mock_uow, mock_logger):
    """Test successful offer creation with a categoria_id item."""
    service = OfferService(uow=mock_uow, logger=mock_logger)

    request = OfferCreateRequest(
        nombre="Promo Empanadas",
        descripcion="2 docenas empanadas",
        precio=Decimal("38000.00"),
        productos=[
            OfferItemRequest(categoria_id=1, cantidad=24),
        ],
    )

    mock_uow.category_repo.get_by_id.return_value = build_category_model(1, "Empanadas", "Empanadas artesanales")

    async def _add_side_effect(offer):
        offer.id = 2
        return offer

    mock_uow.offer_repo.add.side_effect = _add_side_effect
    mock_uow.offer_repo.get_by_id.return_value = build_offer_model(2, "Promo Empanadas", "2 docenas empanadas", 38000.0, True)

    result = await service.create(request)

    assert result.status_code == 201
    assert result.error is None
    mock_uow.category_repo.get_by_id.assert_called_once_with(1)
    mock_uow.product_repo.get_by_id.assert_not_called()
    mock_uow.offer_repo.get_by_id.assert_called_once_with(2)


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
async def test_create_offer_categoria_not_found(mock_uow, mock_logger):
    """Test creating offer with non-existent category."""
    service = OfferService(uow=mock_uow, logger=mock_logger)

    request = OfferCreateRequest(
        nombre="Promo Categoria Invalid",
        precio=Decimal("5000.00"),
        productos=[
            OfferItemRequest(categoria_id=999, cantidad=6)
        ]
    )

    mock_uow.category_repo.get_by_id.return_value = None

    result = await service.create(request)

    assert result.status_code == 404
    assert "Categoría 999 no encontrada" in result.error
    mock_uow.category_repo.get_by_id.assert_called_once_with(999)
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
    mock_uow.offer_repo.get_by_id.side_effect = [sample_offer, sample_offer]
    
    request = OfferUpdateRequest(
        nombre="Nuevo Nombre",
        precio=Decimal("12000.00")
    )
    
    # Act
    result = await service.update(1, offer_update=request)
    
    # Assert
    assert result.status_code == 200
    assert result.value is not None
    assert mock_uow.offer_repo.get_by_id.call_count == 2
    mock_uow.offer_repo.update.assert_called_once()
    mock_uow.commit.assert_called_once()


@pytest.mark.asyncio
async def test_update_offer_with_products(mock_uow, mock_logger, sample_offer):
    """Test updating offer products calls replace_items."""
    # Arrange
    service = OfferService(uow=mock_uow, logger=mock_logger)
    mock_uow.offer_repo.get_by_id.side_effect = [sample_offer, sample_offer]
    
    # Import to check isinstance
    from app.infrastructure.repositories.offer_repository import SqlAlchemyOfferRepository
    mock_uow.offer_repo.__class__ = SqlAlchemyOfferRepository
    mock_uow.offer_repo.replace_items = AsyncMock()
    
    request = OfferUpdateRequest(
        productos=[
            OfferItemRequest(producto_id=3, cantidad=12)
        ]
    )
    
    # Mock product exists (called twice: validation + relationship)
    mock_uow.product_repo.get_by_id.side_effect = [
        build_product_model(3, "Producto 3", 1),  # Validation
        build_product_model(3, "Producto 3", 1),  # Relationship
    ]
    
    # Act
    result = await service.update(1, offer_update=request)
    
    # Assert
    assert result.status_code == 200
    
    # Verify product validation (called twice)
    assert mock_uow.product_repo.get_by_id.call_count == 2
    
    # Verify replace_items was called
    mock_uow.offer_repo.replace_items.assert_called_once()
    mock_uow.offer_repo.update.assert_called_once()


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
async def test_update_offer_categoria_not_found(mock_uow, mock_logger, sample_offer):
    """Test updating offer with non-existent category."""
    service = OfferService(uow=mock_uow, logger=mock_logger)
    mock_uow.offer_repo.get_by_id.return_value = sample_offer

    request = OfferUpdateRequest(
        productos=[
            OfferItemRequest(categoria_id=999, cantidad=6)
        ]
    )

    mock_uow.category_repo.get_by_id.return_value = None

    result = await service.update(1, offer_update=request)

    assert result.status_code == 404
    assert "Categoría 999 no encontrada" in result.error
    mock_uow.offer_repo.update.assert_not_called()


@pytest.mark.asyncio
async def test_update_offer_with_categoria_item(mock_uow, mock_logger, sample_offer):
    """Test updating offer items with categoria_id validates category and updates offer."""
    service = OfferService(uow=mock_uow, logger=mock_logger)
    mock_uow.offer_repo.get_by_id.side_effect = [sample_offer, sample_offer]

    request = OfferUpdateRequest(
        productos=[
            OfferItemRequest(categoria_id=1, cantidad=24)
        ]
    )

    mock_uow.category_repo.get_by_id.return_value = build_category_model(1, "Empanadas", "Empanadas artesanales")

    result = await service.update(1, offer_update=request)

    assert result.status_code == 200
    mock_uow.category_repo.get_by_id.assert_called_once_with(1)
    mock_uow.offer_repo.update.assert_called_once()
    mock_uow.commit.assert_called_once()


@pytest.mark.asyncio
async def test_update_offer_deactivate(mock_uow, mock_logger, sample_offer):
    """Test deactivating offer."""
    # Arrange
    service = OfferService(uow=mock_uow, logger=mock_logger)
    mock_uow.offer_repo.get_by_id.side_effect = [sample_offer, sample_offer]
    
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


# ==================== Duplicate Validation Tests ====================

@pytest.mark.asyncio
async def test_create_offer_duplicate_producto_items(mock_uow, mock_logger):
    """Test creating offer with duplicate producto items fails at schema validation."""
    service = OfferService(uow=mock_uow, logger=mock_logger)
    
    # Assert that creating request with duplicates raises ValidationError
    with pytest.raises(Exception) as exc_info:
        request = OfferCreateRequest(
            nombre="Promo Duplicada",
            descripcion="Con items duplicados",
            precio=Decimal("10000.00"),
            productos=[
                OfferItemRequest(producto_id=1, cantidad=6),
                OfferItemRequest(producto_id=1, cantidad=12),  # Duplicado (mismo producto, diferente cantidad)
            ]
        )
    
    # Verify it's a validation error with correct message
    assert "Item duplicado" in str(exc_info.value)
    assert "producto 1" in str(exc_info.value)


@pytest.mark.asyncio
async def test_create_offer_duplicate_categoria_items(mock_uow, mock_logger):
    """Test creating offer with duplicate categoria items fails at schema validation."""
    service = OfferService(uow=mock_uow, logger=mock_logger)
    
    with pytest.raises(Exception) as exc_info:
        request = OfferCreateRequest(
            nombre="Promo Duplicada Categoria",
            precio=Decimal("10000.00"),
            productos=[
                OfferItemRequest(categoria_id=1, cantidad=6),
                OfferItemRequest(categoria_id=1, cantidad=12),  # Duplicado (misma categoría, diferente cantidad)
            ]
        )
    
    assert "Item duplicado" in str(exc_info.value)
    assert "categoría 1" in str(exc_info.value)


@pytest.mark.asyncio
async def test_create_offer_duplicate_opciones_items(mock_uow, mock_logger):
    """Test creating offer with duplicate producto_opciones items fails at schema validation."""
    service = OfferService(uow=mock_uow, logger=mock_logger)
    
    with pytest.raises(Exception) as exc_info:
        request = OfferCreateRequest(
            nombre="Promo Opciones Duplicadas",
            precio=Decimal("10000.00"),
            productos=[
                OfferItemRequest(producto_opciones=[1, 2, 3], cantidad=1),
                OfferItemRequest(producto_opciones=[3, 1, 2], cantidad=2),  # Duplicado (mismas opciones, diferente cantidad y orden)
            ]
        )
    
    assert "Item duplicado" in str(exc_info.value)
    assert "opciones múltiples" in str(exc_info.value)


@pytest.mark.asyncio
async def test_update_offer_duplicate_items(mock_uow, mock_logger, sample_offer):
    """Test updating offer with duplicate items fails at schema validation."""
    service = OfferService(uow=mock_uow, logger=mock_logger)
    
    mock_uow.offer_repo.get_by_id.return_value = sample_offer
    
    # Assert that creating request with duplicates raises ValidationError
    with pytest.raises(Exception) as exc_info:
        request = OfferUpdateRequest(
            productos=[
                OfferItemRequest(producto_id=2, cantidad=6),
                OfferItemRequest(producto_id=2, cantidad=10),  # Duplicado (mismo producto, diferente cantidad)
            ]
        )
    
    assert "Item duplicado" in str(exc_info.value)
    assert "producto 2" in str(exc_info.value)


@pytest.mark.asyncio
async def test_schema_allows_same_item_different_cantidad():
    """Test that schema rejects same producto/categoria even with different cantidad."""
    # Should raise ValidationError
    with pytest.raises(Exception) as exc_info:
        request = OfferCreateRequest(
            nombre="Test",
            precio=Decimal("10000.00"),
            productos=[
                OfferItemRequest(producto_id=1, cantidad=5),
                OfferItemRequest(producto_id=1, cantidad=10),  # Diferente cantidad pero duplicado
            ]
        )
    assert "Item duplicado" in str(exc_info.value)


@pytest.mark.asyncio
async def test_schema_detects_duplicate_with_same_cantidad():
    """Test that schema detects duplicate when producto_id AND cantidad match."""
    with pytest.raises(Exception) as exc_info:
        request = OfferCreateRequest(
            nombre="Test",
            precio=Decimal("10000.00"),
            productos=[
                OfferItemRequest(categoria_id=1, cantidad=10),
                OfferItemRequest(categoria_id=1, cantidad=10),  # Mismo categoria_id Y cantidad
            ]
        )
    assert "Item duplicado" in str(exc_info.value)


# ==================== Deactivate by Product Tests ====================

@pytest.mark.asyncio
async def test_deactivate_by_product_success(mock_uow, mock_logger):
    """Test successfully deactivating offers when product is deactivated."""
    service = OfferService(uow=mock_uow, logger=mock_logger)
    
    # Mock repository returns IDs of deactivated offers
    mock_uow.offer_repo.deactivate_by_product.return_value = [1, 3, 5]
    
    # Act
    result = await service.deactivate_by_product(producto_id=10)
    
    # Assert
    assert result == [1, 3, 5]
    mock_uow.offer_repo.deactivate_by_product.assert_called_once_with(10)
    mock_uow.commit.assert_called_once()


@pytest.mark.asyncio
async def test_deactivate_by_product_no_offers(mock_uow, mock_logger):
    """Test deactivating product that has no offers."""
    service = OfferService(uow=mock_uow, logger=mock_logger)
    
    # Mock repository returns empty list
    mock_uow.offer_repo.deactivate_by_product.return_value = []
    
    # Act
    result = await service.deactivate_by_product(producto_id=10)
    
    # Assert
    assert result == []
    mock_uow.offer_repo.deactivate_by_product.assert_called_once_with(10)
    mock_uow.commit.assert_called_once()


@pytest.mark.asyncio
async def test_deactivate_by_product_error(mock_uow, mock_logger):
    """Test error handling when deactivating offers by product."""
    service = OfferService(uow=mock_uow, logger=mock_logger)
    
    # Mock repository raises exception
    mock_uow.offer_repo.deactivate_by_product.side_effect = Exception("Database error")
    
    # Act
    result = await service.deactivate_by_product(producto_id=10)
    
    # Assert - Should return empty list on error
    assert result == []
    mock_uow.commit.assert_not_called()

