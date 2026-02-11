"""
Tests for SaleService.
Tests business logic including tiered pricing algorithm with mocked repositories.
"""

import pytest
from unittest.mock import AsyncMock
from decimal import Decimal

from app.application.sale_service import SaleService, ServiceResult
from app.presentation.schemas.sale_schemas import (
    SaleCreateRequest,
    SaleItemRequest
)
from tests.helpers import (
    build_product_model,
    build_product_price_model,
    build_offer_model,
    build_offer_item_model,
    build_category_model,
    build_sale_model
)


# ==================== Tiered Pricing Tests (_get_product_price) ====================

def test_get_product_price_exact_match():
    """Test pricing when quantity exactly matches a tier."""
    # Arrange
    service = SaleService(uow=AsyncMock(), logger=AsyncMock())
    
    product = build_product_model(
        id=1,
        nombre="Empanada",
        categoria_id=1,
        precios=[
            build_product_price_model(1, 1, 1, 1200.0),
            build_product_price_model(2, 1, 6, 6000.0),
            build_product_price_model(3, 1, 12, 10800.0)
        ]
    )
    
    # Act - buying exactly 6
    result = service._get_product_price(product, 6)
    
    # Assert - should be 6000 / 6 = 1000 per unit
    assert result == Decimal("1000.00")


def test_get_product_price_unit_price():
    """Test pricing for single unit."""
    # Arrange
    service = SaleService(uow=AsyncMock(), logger=AsyncMock())
    
    product = build_product_model(
        id=1,
        nombre="Empanada",
        categoria_id=1,
        precios=[
            build_product_price_model(1, 1, 1, 1200.0),
            build_product_price_model(2, 1, 6, 6000.0)
        ]
    )
    
    # Act - buying 1
    result = service._get_product_price(product, 1)
    
    # Assert - should be 1200 / 1 = 1200 per unit
    assert result == Decimal("1200.00")


def test_get_product_price_mixed_range_7_units():
    """Test pricing with quantity in between tiers (7 units)."""
    # Arrange
    service = SaleService(uow=AsyncMock(), logger=AsyncMock())
    
    product = build_product_model(
        id=1,
        nombre="Empanada",
        categoria_id=1,
        precios=[
            build_product_price_model(1, 1, 1, 1200.0),
            build_product_price_model(2, 1, 6, 6000.0),
            build_product_price_model(3, 1, 12, 10800.0)
        ]
    )
    
    # Act - buying 7 (6 + 1)
    result = service._get_product_price(product, 7)
    
    # Assert - should be (6000 + 1200) / 7 = 1028.57 per unit
    expected = (Decimal("6000") + Decimal("1200")) / Decimal("7")
    assert abs(result - expected) < Decimal("0.01")


def test_get_product_price_mixed_range_15_units():
    """Test pricing with multiple tiers (15 units)."""
    # Arrange
    service = SaleService(uow=AsyncMock(), logger=AsyncMock())
    
    product = build_product_model(
        id=1,
        nombre="Empanada",
        categoria_id=1,
        precios=[
            build_product_price_model(1, 1, 1, 1200.0),
            build_product_price_model(2, 1, 6, 6000.0),
            build_product_price_model(3, 1, 12, 10800.0)
        ]
    )
    
    # Act - buying 15 (12 + 3)
    # 12 at 10800, remaining 3 at unit price (1200 each)
    result = service._get_product_price(product, 15)
    
    # Assert - should be (10800 + 3*1200) / 15 = 960 per unit
    expected = (Decimal("10800") + Decimal("3600")) / Decimal("15")
    assert result == expected


def test_get_product_price_large_quantity():
    """Test pricing with large quantity (26 units)."""
    # Arrange
    service = SaleService(uow=AsyncMock(), logger=AsyncMock())
    
    product = build_product_model(
        id=1,
        nombre="Empanada",
        categoria_id=1,
        precios=[
            build_product_price_model(1, 1, 1, 1200.0),
            build_product_price_model(2, 1, 6, 6000.0),
            build_product_price_model(3, 1, 12, 10800.0)
        ]
    )
    
    # Act - buying 26 (12*2 + 2)
    # Two full 12s (21600) + 2 units at 1200 each (2400)
    result = service._get_product_price(product, 26)
    
    # Assert - should be (10800*2 + 2*1200) / 26
    expected = (Decimal("21600") + Decimal("2400")) / Decimal("26")
    assert result == expected


def test_get_product_price_inactive_product():
    """Test that inactive product returns None."""
    # Arrange
    service = SaleService(uow=AsyncMock(), logger=AsyncMock())
    
    product = build_product_model(
        id=1,
        nombre="Inactive",
        categoria_id=1,
        activo=False,
        precios=[build_product_price_model(1, 1, 1, 1200.0)]
    )
    
    # Act
    result = service._get_product_price(product, 5)
    
    # Assert
    assert result is None


def test_get_product_price_no_prices():
    """Test that product without prices returns None."""
    # Arrange
    service = SaleService(uow=AsyncMock(), logger=AsyncMock())
    
    product = build_product_model(
        id=1,
        nombre="No Prices",
        categoria_id=1,
        precios=[]
    )
    
    # Act
    result = service._get_product_price(product, 5)
    
    # Assert
    assert result is None


# ==================== Offer Price Tests ====================

def test_get_offer_price_active():
    """Test getting price for active offer."""
    # Arrange
    service = SaleService(uow=AsyncMock(), logger=AsyncMock())
    
    offer = build_offer_model(
        id=1,
        nombre="Promo Docena",
        precio=10000.0,
        activo=True
    )
    
    # Act
    result = service._get_offer_price(offer)
    
    # Assert
    assert result == Decimal("10000.00")


def test_get_offer_price_inactive():
    """Test that inactive offer returns None."""
    # Arrange
    service = SaleService(uow=AsyncMock(), logger=AsyncMock())
    
    offer = build_offer_model(
        id=1,
        nombre="Promo Inactiva",
        precio=8000.0,
        activo=False
    )
    
    # Act
    result = service._get_offer_price(offer)
    
    # Assert
    assert result is None


# ==================== Create Sale Tests ====================

@pytest.mark.asyncio
async def test_create_sale_with_products(mock_uow, mock_logger):
    """Test creating sale with product items."""
    # Arrange
    service = SaleService(uow=mock_uow, logger=mock_logger)
    
    request = SaleCreateRequest(
        items=[
            SaleItemRequest(producto_id=1, cantidad=6)
        ]
    )
    
    # Mock product with pricing
    product = build_product_model(
        id=1,
        nombre="Empanada",
        categoria_id=1,
        precios=[
            build_product_price_model(1, 1, 1, 1200.0),
            build_product_price_model(2, 1, 6, 6000.0)
        ]
    )
    product.categoria = build_category_model(id=1, nombre="Empanadas")
    mock_uow.product_repo.get_by_id.return_value = product
    mock_uow.sale_repo.refresh = AsyncMock()
    
    # Act
    result = await service.create(request)
    
    # Assert
    assert result.status_code == 201
    assert result.value is not None
    
    # Verify product was validated
    mock_uow.product_repo.get_by_id.assert_called_once_with(1)
    
    # Verify sale was created
    mock_uow.sale_repo.add.assert_called_once()
    mock_uow.commit.assert_called_once()


@pytest.mark.asyncio
async def test_create_sale_with_offers(mock_uow, mock_logger):
    """Test creating sale with offer items."""
    # Arrange
    service = SaleService(uow=mock_uow, logger=mock_logger)
    
    # Mock product for productos_seleccionados
    prod1 = build_product_model(id=10, nombre="Empanada", sku="EMP-001", categoria_id=1)
    prod1.categoria = build_category_model(id=1, nombre="Empanadas")
    
    # Mock offer
    offer = build_offer_model(
        id=1,
        nombre="Promo Docena",
        precio=10000.0,
        activo=True,
        productos=[
            build_offer_item_model(id=1, oferta_id=1, cantidad=12, productos=[prod1])
        ]
    )
    
    request = SaleCreateRequest(
        items=[
            SaleItemRequest(
                oferta_id=1,
                cantidad=2,
                productos_seleccionados=[{"producto_id": 10, "cantidad": 12}]
            )
        ]
    )
    
    mock_uow.offer_repo.get_by_id.return_value = offer
    mock_uow.product_repo.get_by_id.return_value = prod1
    mock_uow.sale_repo.refresh = AsyncMock()
    
    # Act
    result = await service.create(request)
    
    # Assert
    assert result.status_code == 201
    assert result.value is not None
    
    # Verify offer was validated
    mock_uow.offer_repo.get_by_id.assert_called_once_with(1)
    mock_uow.sale_repo.add.assert_called_once()


@pytest.mark.asyncio
async def test_create_sale_mixed_items(mock_uow, mock_logger):
    """Test creating sale with both products and offers."""
    # Arrange
    service = SaleService(uow=mock_uow, logger=mock_logger)
    
    # Mock products
    product = build_product_model(
        id=1,
        precios=[build_product_price_model(1, 1, 6, 6000.0)]
    )
    product.categoria = build_category_model(id=1, nombre="Empanadas")
    
    prod_oferta = build_product_model(id=2, nombre="Pizza", sku="PIZZ-001", categoria_id=1)
    prod_oferta.categoria = build_category_model(id=1, nombre="Pizzas")
    
    offer = build_offer_model(
        id=1, 
        precio=10000.0,
        productos=[
            build_offer_item_model(id=1, oferta_id=1, cantidad=1, productos=[prod_oferta])
        ]
    )
    
    request = SaleCreateRequest(
        items=[
            SaleItemRequest(producto_id=1, cantidad=6),
            SaleItemRequest(
                oferta_id=1,
                cantidad=1,
                productos_seleccionados=[{"producto_id": 2, "cantidad": 1}]
            )
        ]
    )
    
    async def mock_get_product(id):
        return product if id == 1 else prod_oferta
    
    mock_uow.product_repo.get_by_id = AsyncMock(side_effect=mock_get_product)
    mock_uow.offer_repo.get_by_id.return_value = offer
    mock_uow.sale_repo.refresh = AsyncMock()
    
    # Act
    result = await service.create(request)
    
    # Assert
    assert result.status_code == 201
    assert mock_uow.product_repo.get_by_id.call_count == 2
    mock_uow.offer_repo.get_by_id.assert_called_once()


@pytest.mark.asyncio
async def test_create_sale_product_not_found(mock_uow, mock_logger):
    """Test creating sale with non-existent product."""
    # Arrange
    service = SaleService(uow=mock_uow, logger=mock_logger)
    
    request = SaleCreateRequest(
        items=[
            SaleItemRequest(producto_id=999, cantidad=6)
        ]
    )
    
    mock_uow.product_repo.get_by_id.return_value = None
    
    # Act
    result = await service.create(request)
    
    # Assert
    assert result.status_code == 404
    assert "Producto 999 no encontrado" in result.error
    mock_uow.sale_repo.add.assert_not_called()


@pytest.mark.asyncio
async def test_create_sale_offer_not_found(mock_uow, mock_logger):
    """Test creating sale with non-existent offer."""
    # Arrange
    service = SaleService(uow=mock_uow, logger=mock_logger)
    
    request = SaleCreateRequest(
        items=[
            SaleItemRequest(
                oferta_id=999,
                cantidad=1,
                productos_seleccionados=[{"producto_id": 1, "cantidad": 1}]
            )
        ]
    )
    
    mock_uow.offer_repo.get_by_id.return_value = None
    
    # Act
    result = await service.create(request)
    
    # Assert
    assert result.status_code == 404
    assert "Oferta 999 no encontrada" in result.error
    mock_uow.sale_repo.add.assert_not_called()


@pytest.mark.asyncio
async def test_create_sale_inactive_product(mock_uow, mock_logger):
    """Test creating sale with inactive product."""
    # Arrange
    service = SaleService(uow=mock_uow, logger=mock_logger)
    
    request = SaleCreateRequest(
        items=[
            SaleItemRequest(producto_id=1, cantidad=6)
        ]
    )
    
    # Mock inactive product
    product = build_product_model(id=1, activo=False)
    mock_uow.product_repo.get_by_id.return_value = product
    
    # Act
    result = await service.create(request)
    
    # Assert
    assert result.status_code == 400
    assert "No se pudo obtener el precio" in result.error


# ==================== Get By ID Tests ====================

@pytest.mark.asyncio
async def test_get_sale_by_id_success(mock_uow, mock_logger, sample_sale):
    """Test getting sale by ID successfully."""
    # Arrange
    service = SaleService(uow=mock_uow, logger=mock_logger)
    mock_uow.sale_repo.get_by_id.return_value = sample_sale
    
    # Act
    result = await service.get_by_id(1)
    
    # Assert
    assert result.status_code == 200
    assert result.value is not None
    assert result.value.id == 1
    mock_uow.sale_repo.get_by_id.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_get_sale_by_id_not_found(mock_uow, mock_logger):
    """Test getting sale by ID when it doesn't exist."""
    # Arrange
    service = SaleService(uow=mock_uow, logger=mock_logger)
    mock_uow.sale_repo.get_by_id.return_value = None
    
    # Act
    result = await service.get_by_id(999)
    
    # Assert
    assert result.status_code == 404
    assert "Venta 999 no encontrada" in result.error
    mock_uow.sale_repo.get_by_id.assert_called_once_with(999)


# ==================== Get All Tests ====================

@pytest.mark.asyncio
async def test_get_all_sales(mock_uow, mock_logger):
    """Test getting all sales with pagination."""
    # Arrange
    service = SaleService(uow=mock_uow, logger=mock_logger)
    sales = [
        build_sale_model(1, "ORD-001", 6000.0),
        build_sale_model(2, "ORD-002", 12000.0)
    ]
    mock_uow.sale_repo.list.return_value = sales
    
    # Act
    result = await service.get_all(skip=0, limit=100)
    
    # Assert
    assert len(result) == 2
    mock_uow.sale_repo.list.assert_called_once_with(skip=0, limit=100, fecha_desde=None, fecha_hasta=None)


@pytest.mark.asyncio
async def test_get_all_sales_with_pagination(mock_uow, mock_logger):
    """Test getting sales with custom pagination."""
    # Arrange
    service = SaleService(uow=mock_uow, logger=mock_logger)
    mock_uow.sale_repo.list.return_value = []
    
    # Act
    result = await service.get_all(skip=10, limit=5)
    
    # Assert
    mock_uow.sale_repo.list.assert_called_once_with(skip=10, limit=5, fecha_desde=None, fecha_hasta=None)


@pytest.mark.asyncio
async def test_get_all_sales_error(mock_uow, mock_logger):
    """Test getting sales with database error returns empty list."""
    # Arrange
    service = SaleService(uow=mock_uow, logger=mock_logger)
    mock_uow.sale_repo.list.side_effect = Exception("Database error")
    
    # Act
    result = await service.get_all()
    
    # Assert
    assert result == []
    mock_logger.error.assert_called_once()


# ==================== Update Sale Tests ====================

@pytest.mark.asyncio
async def test_update_sale_with_products(mock_uow, mock_logger, sample_sale):
    """Test updating sale with product items."""
    # Arrange
    service = SaleService(uow=mock_uow, logger=mock_logger)
    
    from app.presentation.schemas.sale_schemas import SaleUpdateRequest
    
    request = SaleUpdateRequest(
        items=[
            SaleItemRequest(producto_id=1, cantidad=12, precio_unitario=Decimal("900.00"))
        ]
    )
    
    # Mock existing sale
    mock_uow.sale_repo.get_by_id.return_value = sample_sale
    
    # Mock product with category
    category = build_category_model(id=1, nombre="Empanadas")
    product = build_product_model(
        id=1,
        nombre="Empanada Actualizada",
        sku="EMPA-ACT-001",
        categoria_id=1
    )
    product.categoria = category
    mock_uow.product_repo.get_by_id.return_value = product
    mock_uow.sale_repo.refresh = AsyncMock()
    
    # Act
    result = await service.update(1, request)
    
    # Assert
    assert result.status_code == 200
    assert result.value is not None
    
    # Verify sale was updated
    mock_uow.sale_repo.update.assert_called_once()
    mock_uow.commit.assert_called_once()
    
    # Verify product snapshot was captured
    updated_sale = sample_sale
    # numero_orden no puede ser editado - debe mantenerse igual
    assert updated_sale.numero_orden == "ORD-001"
    assert len(updated_sale.items) == 1
    assert updated_sale.items[0].item_nombre == "Empanada Actualizada"
    assert updated_sale.items[0].producto_sku == "EMPA-ACT-001"
    assert updated_sale.items[0].item_categoria == "Empanadas"


@pytest.mark.asyncio
async def test_update_sale_with_offers_no_validation(mock_uow, mock_logger, sample_sale):
    """Test updating sale with offers does NOT validate products against current offer requirements.
    
    This is important because sales are historical records. If the offer changed after
    the sale was created, we should still allow updating the sale without validating
    against the new offer requirements.
    """
    # Arrange
    service = SaleService(uow=mock_uow, logger=mock_logger)
    
    from app.presentation.schemas.sale_schemas import SaleUpdateRequest, SelectedProduct
    
    request = SaleUpdateRequest(
        items=[
            SaleItemRequest(
                oferta_id=1,
                cantidad=2,
                precio_unitario=Decimal("8000.00"),
                productos_seleccionados=[SelectedProduct(producto_id=10, cantidad=6)]
            )
        ]
    )
    
    # Mock existing sale
    mock_uow.sale_repo.get_by_id.return_value = sample_sale
    
    # Mock current offer (could have different requirements than when sale was created)
    cat1 = build_category_model(id=1, nombre="Empanadas")
    prod1 = build_product_model(id=10, nombre="Empanada Carne", sku="EMPA-CARN-001", categoria_id=1)
    prod1.categoria = cat1
    
    # Current offer now requires 12 empanadas (changed from original 6)
    oferta_actual = build_offer_model(
        id=1,
        nombre="Promo Docena",
        descripcion="12 empanadas",
        precio=10000.0,
        productos=[
            build_offer_item_model(id=1, oferta_id=1, cantidad=12, productos=[prod1])
        ]
    )
    
    mock_uow.offer_repo.get_by_id.return_value = oferta_actual
    mock_uow.product_repo.get_by_id.return_value = prod1
    mock_uow.sale_repo.refresh = AsyncMock()
    
    # Act - update should succeed even though productos_seleccionados (6) don't match
    # current offer requirements (12), because we don't validate on update
    result = await service.update(1, request)
    
    # Assert
    assert result.status_code == 200
    assert result.value is not None
    
    # Verify snapshot was captured with current offer name (for reference)
    # but without validating the productos_seleccionados
    updated_sale = sample_sale
    assert len(updated_sale.items) == 1
    assert updated_sale.items[0].item_nombre == "Promo Docena"
    assert updated_sale.items[0].item_categoria == "Ofertas"
    assert updated_sale.items[0].item_descripcion == "12 empanadas"
    assert len(updated_sale.items[0].oferta_productos_snapshot) == 1


@pytest.mark.asyncio
async def test_update_sale_missing_precio_unitario(mock_uow, mock_logger, sample_sale):
    """Test updating sale without precio_unitario fails."""
    # Arrange
    service = SaleService(uow=mock_uow, logger=mock_logger)
    
    from app.presentation.schemas.sale_schemas import SaleUpdateRequest
    
    request = SaleUpdateRequest(
        items=[
            SaleItemRequest(producto_id=1, cantidad=6)  # Missing precio_unitario
        ]
    )
    
    mock_uow.sale_repo.get_by_id.return_value = sample_sale
    
    # Act
    result = await service.update(1, request)
    
    # Assert
    assert result.status_code == 400
    assert "precio_unitario" in result.error
    mock_uow.sale_repo.update.assert_not_called()


@pytest.mark.asyncio
async def test_update_sale_not_found(mock_uow, mock_logger):
    """Test updating non-existent sale fails."""
    # Arrange
    service = SaleService(uow=mock_uow, logger=mock_logger)
    
    from app.presentation.schemas.sale_schemas import SaleUpdateRequest
    
    request = SaleUpdateRequest(
        items=[
            SaleItemRequest(producto_id=1, cantidad=6, precio_unitario=Decimal("1000.00"))
        ]
    )
    
    mock_uow.sale_repo.get_by_id.return_value = None
    
    # Act
    result = await service.update(999, request)
    
    # Assert
    assert result.status_code == 404
    assert "Venta 999 no encontrada" in result.error
    mock_uow.sale_repo.update.assert_not_called()


@pytest.mark.asyncio
async def test_update_sale_product_not_found(mock_uow, mock_logger, sample_sale):
    """Test updating sale with non-existent product fails."""
    # Arrange
    service = SaleService(uow=mock_uow, logger=mock_logger)
    
    from app.presentation.schemas.sale_schemas import SaleUpdateRequest
    
    request = SaleUpdateRequest(
        items=[
            SaleItemRequest(producto_id=999, cantidad=6, precio_unitario=Decimal("1000.00"))
        ]
    )
    
    mock_uow.sale_repo.get_by_id.return_value = sample_sale
    mock_uow.product_repo.get_by_id.return_value = None
    
    # Act
    result = await service.update(1, request)
    
    # Assert
    assert result.status_code == 404
    assert "Producto 999 no encontrado" in result.error
    mock_uow.sale_repo.update.assert_not_called()


@pytest.mark.asyncio
async def test_update_sale_offer_not_found(mock_uow, mock_logger, sample_sale):
    """Test updating sale with non-existent offer fails."""
    # Arrange
    service = SaleService(uow=mock_uow, logger=mock_logger)
    
    from app.presentation.schemas.sale_schemas import SaleUpdateRequest, SelectedProduct
    
    request = SaleUpdateRequest(
        items=[
            SaleItemRequest(
                oferta_id=999,
                cantidad=1,
                precio_unitario=Decimal("8000.00"),
                productos_seleccionados=[SelectedProduct(producto_id=1, cantidad=6)]
            )
        ]
    )
    
    mock_uow.sale_repo.get_by_id.return_value = sample_sale
    mock_uow.offer_repo.get_by_id.return_value = None
    
    # Act
    result = await service.update(1, request)
    
    # Assert
    assert result.status_code == 404
    assert "Oferta 999 no encontrada" in result.error
    mock_uow.sale_repo.update.assert_not_called()
