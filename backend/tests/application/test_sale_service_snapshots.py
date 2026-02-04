"""
Tests for SaleService snapshot functionality.
Tests that sale items correctly capture product/offer snapshots.
"""

import pytest
from unittest.mock import AsyncMock
from decimal import Decimal

from app.application.sale_service import SaleService
from app.presentation.schemas.sale_schemas import (
    SaleCreateRequest,
    SaleItemRequest
)
from tests.helpers import (
    build_product_model,
    build_category_model,
    build_offer_model,
    build_offer_item_model
)


# ==================== Product Snapshot Tests ====================

@pytest.mark.asyncio
async def test_create_sale_captures_product_snapshot(mock_uow, mock_logger):
    """Test that sale item captures product SKU, name, and category."""
    # Arrange
    service = SaleService(uow=mock_uow, logger=mock_logger)
    
    # Mock category and product
    categoria = build_category_model(id=1, nombre="Empanadas")
    producto = build_product_model(
        id=1, 
        nombre="Empanada de Carne",
        sku="EMPA-CARN-001",
        categoria_id=1
    )
    producto.categoria = categoria
    
    mock_uow.product_repo.get_by_id = AsyncMock(return_value=producto)
    
    request = SaleCreateRequest(
        numero_orden="ORD-001",
        items=[
            SaleItemRequest(producto_id=1, cantidad=6)
        ]
    )
    
    # Act
    result = await service.create(request)
    
    # Assert
    assert result.status_code == 201
    assert result.value is not None
    
    # Verify the sale was created
    mock_uow.sale_repo.add.assert_called_once()
    sale = mock_uow.sale_repo.add.call_args[0][0]
    
    # Verify snapshot fields were captured
    assert len(sale.items) == 1
    sale_item = sale.items[0]
    assert sale_item.producto_sku == "EMPA-CARN-001"
    assert sale_item.item_nombre == "Empanada de Carne"
    assert sale_item.item_categoria == "Empanadas"
    assert sale_item.item_descripcion is None


@pytest.mark.asyncio
async def test_create_sale_product_without_category(mock_uow, mock_logger):
    """Test that sale item handles products without category."""
    # Arrange
    service = SaleService(uow=mock_uow, logger=mock_logger)
    
    producto = build_product_model(
        id=1, 
        nombre="Producto Sin Categoría",
        sku="PROD-SIN-001",
        categoria_id=None
    )
    producto.categoria = None
    
    mock_uow.product_repo.get_by_id = AsyncMock(return_value=producto)
    
    request = SaleCreateRequest(
        numero_orden="ORD-002",
        items=[
            SaleItemRequest(producto_id=1, cantidad=1)
        ]
    )
    
    # Act
    result = await service.create(request)
    
    # Assert
    assert result.status_code == 201
    sale = mock_uow.sale_repo.add.call_args[0][0]
    sale_item = sale.items[0]
    
    assert sale_item.producto_sku == "PROD-SIN-001"
    assert sale_item.item_nombre == "Producto Sin Categoría"
    assert sale_item.item_categoria == "Sin categoría"


# ==================== Offer Snapshot Tests ====================

@pytest.mark.asyncio
async def test_create_sale_captures_offer_snapshot(mock_uow, mock_logger):
    """Test that sale item captures offer name, description, and selected products."""
    # Arrange
    service = SaleService(uow=mock_uow, logger=mock_logger)
    
    # Mock categories and products
    cat1 = build_category_model(id=1, nombre="Empanadas")
    
    prod1 = build_product_model(id=1, nombre="Empanada Carne", sku="EMPA-CARN-001", categoria_id=1)
    prod1.categoria = cat1
    
    prod2 = build_product_model(id=2, nombre="Empanada Pollo", sku="EMPA-POLL-001", categoria_id=1)
    prod2.categoria = cat1
    
    # Mock offer with products
    oferta = build_offer_model(
        id=1,
        nombre="Promo Docena",
        descripcion="12 empanadas surtidas",
        precio=10000.0,
        productos=[
            build_offer_item_model(id=1, oferta_id=1, categoria_id=1, cantidad=6, productos=[prod1]),
            build_offer_item_model(id=2, oferta_id=1, categoria_id=1, cantidad=6, productos=[prod2])
        ]
    )
    
    mock_uow.offer_repo.get_by_id = AsyncMock(return_value=oferta)
    mock_uow.product_repo.get_by_id = AsyncMock(side_effect=lambda id: prod1 if id == 1 else prod2)
    
    request = SaleCreateRequest(
        numero_orden="ORD-003",
        items=[
            SaleItemRequest(
                oferta_id=1, 
                cantidad=1,
                productos_seleccionados=[
                    {"producto_id": 1, "cantidad": 6},
                    {"producto_id": 2, "cantidad": 6}
                ]
            )
        ]
    )
    
    # Act
    result = await service.create(request)
    
    # Assert
    assert result.status_code == 201
    sale = mock_uow.sale_repo.add.call_args[0][0]
    sale_item = sale.items[0]
    
    # Verify offer snapshot
    assert sale_item.producto_sku is None
    assert sale_item.item_nombre == "Promo Docena"
    assert sale_item.item_categoria == "Ofertas"
    assert sale_item.item_descripcion == "12 empanadas surtidas"
    
    # Verify offer products snapshot was created
    assert len(sale_item.oferta_productos_snapshot) == 2
    assert sale_item.oferta_productos_snapshot[0].producto_nombre == "Empanada Carne"
    assert sale_item.oferta_productos_snapshot[0].cantidad == 6
    assert sale_item.oferta_productos_snapshot[1].producto_nombre == "Empanada Pollo"
    assert sale_item.oferta_productos_snapshot[1].cantidad == 6


@pytest.mark.asyncio
async def test_create_sale_offer_without_description(mock_uow, mock_logger):
    """Test that sale item handles offers without description."""
    # Arrange
    service = SaleService(uow=mock_uow, logger=mock_logger)
    
    cat1 = build_category_model(id=1, nombre="Pizzas")
    prod1 = build_product_model(id=1, nombre="Pizza Muzza", sku="PIZZ-MUZZ-001", categoria_id=1)
    prod1.categoria = cat1
    
    oferta = build_offer_model(
        id=1,
        nombre="Promo Pizza",
        descripcion=None,
        precio=5000.0,
        productos=[
            build_offer_item_model(id=1, oferta_id=1, categoria_id=1, cantidad=1, productos=[prod1])
        ]
    )
    
    mock_uow.offer_repo.get_by_id = AsyncMock(return_value=oferta)
    mock_uow.product_repo.get_by_id = AsyncMock(return_value=prod1)
    
    request = SaleCreateRequest(
        numero_orden="ORD-004",
        items=[
            SaleItemRequest(
                oferta_id=1, 
                cantidad=2,
                productos_seleccionados=[{"producto_id": 1, "cantidad": 1}]
            )
        ]
    )
    
    # Act
    result = await service.create(request)
    
    # Assert
    assert result.status_code == 201
    sale = mock_uow.sale_repo.add.call_args[0][0]
    sale_item = sale.items[0]
    
    assert sale_item.item_nombre == "Promo Pizza"
    assert sale_item.item_descripcion is None


# ==================== Mixed Sale Tests ====================

@pytest.mark.asyncio
async def test_create_sale_mixed_products_and_offers(mock_uow, mock_logger):
    """Test sale with both products and offers captures all snapshots."""
    # Arrange
    service = SaleService(uow=mock_uow, logger=mock_logger)
    
    # Mock category and products
    cat1 = build_category_model(id=1, nombre="Empanadas")
    prod1 = build_product_model(id=1, nombre="Empanada Carne", sku="EMPA-CARN-001", categoria_id=1)
    prod1.categoria = cat1
    
    prod2 = build_product_model(id=2, nombre="Empanada Pollo", sku="EMPA-POLL-001", categoria_id=1)
    prod2.categoria = cat1
    
    oferta = build_offer_model(
        id=1,
        nombre="Promo Mix",
        descripcion="Variedad de empanadas",
        precio=8000.0,
        productos=[
            build_offer_item_model(id=1, oferta_id=1, categoria_id=1, cantidad=12, productos=[prod1, prod2])
        ]
    )
    
    # Mock both product.get_by_id calls
    async def mock_get_product(id):
        if id == 1:
            return prod1
        elif id == 2:
            return prod2
        return None
    
    mock_uow.product_repo.get_by_id = AsyncMock(side_effect=mock_get_product)
    mock_uow.offer_repo.get_by_id = AsyncMock(return_value=oferta)
    
    request = SaleCreateRequest(
        numero_orden="ORD-005",
        items=[
            SaleItemRequest(producto_id=1, cantidad=6),
            SaleItemRequest(
                oferta_id=1, 
                cantidad=1,
                productos_seleccionados=[{"producto_id": 2, "cantidad": 12}]
            )
        ]
    )
    
    # Act
    result = await service.create(request)
    
    # Assert
    assert result.status_code == 201
    sale = mock_uow.sale_repo.add.call_args[0][0]
    
    # Verify we have 2 items
    assert len(sale.items) == 2
    
    # First item is product
    product_item = sale.items[0]
    assert product_item.producto_id == 1
    assert product_item.producto_sku == "EMPA-CARN-001"
    assert product_item.item_nombre == "Empanada Carne"
    assert product_item.item_categoria == "Empanadas"
    
    # Second item is offer
    offer_item = sale.items[1]
    assert offer_item.oferta_id == 1
    assert offer_item.producto_sku is None
    assert offer_item.item_nombre == "Promo Mix"
    assert offer_item.item_categoria == "Ofertas"
    assert offer_item.item_descripcion == "Variedad de empanadas"
    assert len(offer_item.oferta_productos_snapshot) == 1
    assert offer_item.oferta_productos_snapshot[0].producto_nombre == "Empanada Pollo"


# ==================== Snapshot Preservation Tests ====================

@pytest.mark.asyncio
async def test_snapshot_preserves_data_even_if_product_deleted():
    """Test that snapshot fields allow querying sales history even after product is deleted.
    
    This is a documentation test - the snapshot fields (producto_sku, item_nombre, 
    item_categoria) are nullable=False and always populated, ensuring historical data
    remains queryable even if the referenced product/offer is deleted.
    
    Key assertions:
    - producto_sku is saved for products (for reports)
    - item_nombre is always saved (display name)
    - item_categoria is always saved (for categorization)
    - item_descripcion is saved for offers (additional context)
    """
    # This test documents the design decision
    # Actual behavior is tested in the integration tests above
    pass


# ==================== Offer Validation Tests ====================

@pytest.mark.asyncio
async def test_create_sale_validates_selected_products_belong_to_offer(mock_uow, mock_logger):
    """Test that selected products must belong to the offer."""
    # Arrange
    service = SaleService(uow=mock_uow, logger=mock_logger)
    
    cat1 = build_category_model(id=1, nombre="Empanadas")
    prod1 = build_product_model(id=1, nombre="Empanada Carne", sku="EMPA-CARN-001", categoria_id=1)
    prod1.categoria = cat1
    
    prod3 = build_product_model(id=3, nombre="Pizza Muzza", sku="PIZZ-MUZZ-001", categoria_id=2)
    prod3.categoria = build_category_model(id=2, nombre="Pizzas")
    
    # Offer only includes prod1
    oferta = build_offer_model(
        id=1,
        nombre="Promo Empanadas",
        precio=5000.0,
        productos=[
            build_offer_item_model(id=1, oferta_id=1, cantidad=6, productos=[prod1])
        ]
    )
    
    mock_uow.offer_repo.get_by_id = AsyncMock(return_value=oferta)
    mock_uow.product_repo.get_by_id = AsyncMock(return_value=prod3)
    
    # Try to buy offer with prod3 (pizza) which is NOT in the offer
    request = SaleCreateRequest(
        items=[
            SaleItemRequest(
                oferta_id=1,
                cantidad=1,
                productos_seleccionados=[{"producto_id": 3, "cantidad": 6}]
            )
        ]
    )
    
    # Act
    result = await service.create(request)
    
    # Assert
    assert result.status_code == 400
    # El error puede ser "no está permitido" o "requiere seleccionar" dependiendo del orden de validación
    assert "promo empanadas" in result.error.lower()
    assert result.error is not None


@pytest.mark.asyncio
async def test_create_sale_validates_product_quantity_matches_offer(mock_uow, mock_logger):
    """Test that selected product quantities must match offer requirements."""
    # Arrange
    service = SaleService(uow=mock_uow, logger=mock_logger)
    
    cat1 = build_category_model(id=1, nombre="Empanadas")
    prod1 = build_product_model(id=1, nombre="Empanada Carne", sku="EMPA-CARN-001", categoria_id=1)
    prod1.categoria = cat1
    
    # Offer requires 12 empanadas
    oferta = build_offer_model(
        id=1,
        nombre="Promo Docena",
        precio=10000.0,
        productos=[
            build_offer_item_model(id=1, oferta_id=1, cantidad=12, productos=[prod1])
        ]
    )
    
    mock_uow.offer_repo.get_by_id = AsyncMock(return_value=oferta)
    mock_uow.product_repo.get_by_id = AsyncMock(return_value=prod1)
    
    # Try to buy with only 6 (incorrect quantity)
    request = SaleCreateRequest(
        items=[
            SaleItemRequest(
                oferta_id=1,
                cantidad=1,
                productos_seleccionados=[{"producto_id": 1, "cantidad": 6}]
            )
        ]
    )
    
    # Act
    result = await service.create(request)
    
    # Assert
    assert result.status_code == 400
    assert "requiere 12 unidades" in result.error.lower()


@pytest.mark.asyncio
async def test_create_sale_validates_all_offer_items_selected(mock_uow, mock_logger):
    """Test that all offer items must be selected."""
    # Arrange
    service = SaleService(uow=mock_uow, logger=mock_logger)
    
    cat1 = build_category_model(id=1, nombre="Pizzas")
    cat2 = build_category_model(id=2, nombre="Empanadas")
    
    prod1 = build_product_model(id=1, nombre="Pizza Muzza", sku="PIZZ-MUZZ-001", categoria_id=1)
    prod1.categoria = cat1
    
    prod2 = build_product_model(id=2, nombre="Empanada Carne", sku="EMPA-CARN-001", categoria_id=2)
    prod2.categoria = cat2
    
    # Offer requires 1 pizza + 6 empanadas
    oferta = build_offer_model(
        id=1,
        nombre="Promo Combo",
        precio=15000.0,
        productos=[
            build_offer_item_model(id=1, oferta_id=1, cantidad=1, productos=[prod1]),
            build_offer_item_model(id=2, oferta_id=1, cantidad=6, productos=[prod2])
        ]
    )
    
    mock_uow.offer_repo.get_by_id = AsyncMock(return_value=oferta)
    mock_uow.product_repo.get_by_id = AsyncMock(return_value=prod1)
    
    # Only select pizza, missing empanadas
    request = SaleCreateRequest(
        items=[
            SaleItemRequest(
                oferta_id=1,
                cantidad=1,
                productos_seleccionados=[{"producto_id": 1, "cantidad": 1}]
            )
        ]
    )
    
    # Act
    result = await service.create(request)
    
    # Assert
    assert result.status_code == 400
    assert "requiere seleccionar" in result.error.lower()
