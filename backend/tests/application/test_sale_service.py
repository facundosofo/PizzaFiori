"""
Tests for SaleService.
Tests business logic including tiered pricing algorithm with mocked repositories.
"""

import pytest
from unittest.mock import AsyncMock, patch
from decimal import Decimal

from app.application.sale_service import SaleService, ServiceResult
from app.infrastructure.config.settings import settings, StockExtraDeductionRule
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
    build_sale_model,
    build_stock_model
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


def test_get_product_price_fractional_quantity():
    """Test pricing for fractional quantities like 0.25 portions."""
    # Arrange
    service = SaleService(uow=AsyncMock(), logger=AsyncMock())
    
    product = build_product_model(
        id=1,
        nombre="Empanada",
        categoria_id=1,
        precios=[
            build_product_price_model(1, 1, Decimal("0.25"), 250.0),
            build_product_price_model(2, 1, 1, 1200.0)
        ]
    )
    
    # Act - buying 0.25 portion
    result = service._get_product_price(product, Decimal("0.25"))
    
    # Assert - the fractional portion should use the 0.25 tier and return the equivalent unit price
    assert result == Decimal("1000.00")


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
    
    # Assert - should be (10800*2 + 2*1200) / 26 rounded to two decimals
    expected = ((Decimal("21600") + Decimal("2400")) / Decimal("26")).quantize(Decimal("0.01"))
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
async def test_create_sale_with_fractional_product_quantity(mock_uow, mock_logger):
    """Test creating sale with fractional product quantity (porciones)."""
    service = SaleService(uow=mock_uow, logger=mock_logger)

    request = SaleCreateRequest(
        items=[
            SaleItemRequest(producto_id=1, cantidad=Decimal("0.25"))
        ]
    )

    product = build_product_model(
        id=1,
        nombre="Empanada",
        categoria_id=1,
        precios=[
            build_product_price_model(1, 1, Decimal("0.25"), 250.0),
            build_product_price_model(2, 1, 1, 1200.0)
        ]
    )
    product.categoria = build_category_model(id=1, nombre="Empanadas")

    mock_uow.product_repo.get_by_id.return_value = product
    mock_uow.sale_repo.refresh = AsyncMock()

    result = await service.create(request)

    assert result.status_code == 201
    assert result.value is not None
    mock_uow.sale_repo.add.assert_called_once()
    mock_uow.commit.assert_called_once()


@pytest.mark.asyncio
async def test_create_sale_super_milas_adds_papas_stock_deduction(mock_uow, mock_logger):
    """Test selling a Super Milas product also deducts stock from Papas Fritas."""
    service = SaleService(uow=mock_uow, logger=mock_logger)

    papas_category = build_category_model(id=9, nombre="Papas Fritas")
    super_milas_category = build_category_model(id=5, nombre="Super Milas")

    product = build_product_model(
        id=1,
        nombre="Super Mila Napolitana",
        categoria_id=5,
        precios=[build_product_price_model(1, 1, 1, 1200.0)]
    )
    product.categoria = super_milas_category

    mock_uow.product_repo.get_by_id.return_value = product
    mock_uow.product_category_repo.list.return_value = [papas_category, super_milas_category]

    async def mock_get_category_by_id(category_id):
        if category_id == 9:
            return papas_category
        if category_id == 5:
            return super_milas_category
        return None

    mock_uow.product_category_repo.get_by_id = AsyncMock(side_effect=mock_get_category_by_id)
    mock_uow.stock_repo.get_by_categoria_id = AsyncMock(side_effect=lambda categoria_id: build_stock_model(categoria_id=categoria_id))
    mock_uow.sale_repo.refresh = AsyncMock()

    request = SaleCreateRequest(
        items=[
            SaleItemRequest(producto_id=1, cantidad=1)
        ]
    )

    result = await service.create(request)

    assert result.status_code == 201
    assert result.value is not None
    assert any(call.args[0] == 9 for call in mock_uow.product_category_repo.get_by_id.await_args_list)
    assert any(call.args[0] == 9 for call in mock_uow.stock_repo.get_by_categoria_id.await_args_list)


@pytest.mark.asyncio
async def test_create_sale_sku_rule_adds_half_papas_stock_deduction_from_env_rules(mock_uow, mock_logger):
    """Test that SKU-based rule deducts 0.5 from target stock using env-configured rules."""
    service = SaleService(uow=mock_uow, logger=mock_logger)

    papas_category = build_category_model(id=9, nombre="Papas Fritas")
    empanadas_category = build_category_model(id=1, nombre="Empanadas")

    product = build_product_model(
        id=2,
        nombre="Promo Teque",
        sku="SKU: PIC-TEQNP-95208",
        categoria_id=1,
        precios=[build_product_price_model(1, 2, 1, 2500.0)],
    )
    product.categoria = empanadas_category

    mock_uow.product_repo.get_by_id.return_value = product
    mock_uow.product_category_repo.list.return_value = [papas_category, empanadas_category]

    async def mock_get_category_by_id(category_id):
        if category_id == 9:
            return papas_category
        if category_id == 1:
            return empanadas_category
        return None

    mock_uow.product_category_repo.get_by_id = AsyncMock(side_effect=mock_get_category_by_id)
    mock_uow.stock_repo.get_by_categoria_id = AsyncMock(
        side_effect=lambda categoria_id: build_stock_model(categoria_id=categoria_id, cantidad=10)
    )
    mock_uow.sale_repo.refresh = AsyncMock()

    request = SaleCreateRequest(items=[SaleItemRequest(producto_id=2, cantidad=1)])

    custom_rules = [
        StockExtraDeductionRule(
            categoria=[],
            producto=["PIC-TEQNP-95208"],
            cantidad=Decimal("0.500"),
            producto_a_descontar="Papas Fritas",
        )
    ]

    with patch.object(settings, "stock_extra_deduction_rules", custom_rules):
        result = await service.create(request)

    assert result.status_code == 201
    assert result.value is not None

    papas_stock_updates = [
        call for call in mock_uow.audit_repo.log_action.await_args_list
        if call.kwargs.get("entity_type") == "Stock" and call.kwargs.get("entity_id") == 9
    ]
    assert papas_stock_updates
    assert papas_stock_updates[0].kwargs["changes"]["cantidad_descontada"] == Decimal("0.500")


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
    
    # Act – patch sale_to_snapshot to avoid SQLAlchemy inspect on MagicMock
    with patch('app.application.utils.audit_helpers.sale_to_snapshot', return_value={"id": 1, "items": []}):
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
    with patch('app.application.utils.audit_helpers.sale_to_snapshot', return_value={"id": 1, "items": []}):
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
async def test_update_sale_with_transfer_recargo(mock_uow, mock_logger, sample_sale):
    """Test updating sale with transfer surcharge calculation."""
    service = SaleService(uow=mock_uow, logger=mock_logger)
    from app.presentation.schemas.sale_schemas import SaleUpdateRequest

    request = SaleUpdateRequest(
        items=[
            SaleItemRequest(producto_id=1, cantidad=2, precio_unitario=Decimal("1000.00"))
        ],
        aplicar_recargo=True
    )

    mock_uow.sale_repo.get_by_id.return_value = sample_sale

    category = build_category_model(id=1, nombre="Empanadas")
    product = build_product_model(
        id=1,
        nombre="Empanada Actualizada",
        sku="EMPA-ACT-001",
        categoria_id=1
    )
    product.categoria = category
    mock_uow.product_repo.get_by_id.return_value = product
    mock_uow.app_config_repo.get_by_key.return_value = type("Config", (), {"value": "10"})()
    mock_uow.sale_repo.refresh = AsyncMock()

    with patch('app.application.utils.audit_helpers.sale_to_snapshot', return_value={"id": 1, "items": []}):
        result = await service.update(1, request)

    assert result.status_code == 200
    assert result.value is not None
    assert result.value.porcentaje_recargo == Decimal("10")
    assert result.value.monto_recargo == Decimal("200.00")
    assert result.value.total == Decimal("2200.00")
    mock_uow.sale_repo.update.assert_called_once()
    mock_uow.commit.assert_called_once()


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
    with patch('app.application.utils.audit_helpers.sale_to_snapshot', return_value={"id": 1, "items": []}):
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
    with patch('app.application.utils.audit_helpers.sale_to_snapshot', return_value={"id": 1, "items": []}):
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
    with patch('app.application.utils.audit_helpers.sale_to_snapshot', return_value={"id": 1, "items": []}):
        result = await service.update(1, request)
    
    # Assert
    assert result.status_code == 404
    assert "Oferta 999 no encontrada" in result.error
    mock_uow.sale_repo.update.assert_not_called()


# ==================== Count All Tests ====================

@pytest.mark.asyncio
async def test_count_all_no_filters(mock_uow, mock_logger):
    """count_all sin filtros devuelve el conteo total."""
    service = SaleService(uow=mock_uow, logger=mock_logger)
    mock_uow.sale_repo.count.return_value = 42

    result = await service.count_all()

    assert result == 42
    mock_uow.sale_repo.count.assert_called_once()


@pytest.mark.asyncio
async def test_count_all_with_dates(mock_uow, mock_logger):
    """count_all convierte date a datetime y pasa los filtros."""
    from datetime import date, time

    service = SaleService(uow=mock_uow, logger=mock_logger)
    mock_uow.sale_repo.count.return_value = 10

    result = await service.count_all(
        fecha_desde=date(2026, 1, 1),
        fecha_hasta=date(2026, 1, 31),
    )

    assert result == 10
    call_kwargs = mock_uow.sale_repo.count.call_args[1]
    assert call_kwargs["fecha_desde"].date() == date(2026, 1, 1)
    assert call_kwargs["fecha_hasta"].date() == date(2026, 1, 31)


@pytest.mark.asyncio
async def test_count_all_error(mock_uow, mock_logger):
    """count_all devuelve 0 en caso de error."""
    service = SaleService(uow=mock_uow, logger=mock_logger)
    mock_uow.sale_repo.count.side_effect = Exception("db down")

    result = await service.count_all()

    assert result == 0


# ==================== Get Available Years Tests ====================

@pytest.mark.asyncio
async def test_get_available_years_success(mock_uow, mock_logger):
    """get_available_years devuelve lista de años."""
    service = SaleService(uow=mock_uow, logger=mock_logger)
    mock_uow.sale_repo.get_distinct_years.return_value = [2024, 2025, 2026]

    result = await service.get_available_years()

    assert result == [2024, 2025, 2026]


@pytest.mark.asyncio
async def test_get_available_years_error(mock_uow, mock_logger):
    """get_available_years devuelve lista vacía en caso de error."""
    service = SaleService(uow=mock_uow, logger=mock_logger)
    mock_uow.sale_repo.get_distinct_years.side_effect = Exception("fail")

    result = await service.get_available_years()

    assert result == []


# ==================== Delete Tests ====================

@pytest.mark.asyncio
async def test_delete_sale_success(mock_uow, mock_logger, sample_sale):
    """Eliminar venta exitosamente."""
    service = SaleService(uow=mock_uow, logger=mock_logger)
    mock_uow.sale_repo.get_by_id.return_value = sample_sale

    result = await service.delete(1)

    assert result.status_code == 204
    mock_uow.sale_repo.delete.assert_called_once_with(1)
    mock_uow.commit.assert_called_once()


@pytest.mark.asyncio
async def test_delete_sale_not_found(mock_uow, mock_logger):
    """Eliminar venta que no existe retorna 404."""
    service = SaleService(uow=mock_uow, logger=mock_logger)
    mock_uow.sale_repo.get_by_id.return_value = None

    result = await service.delete(999)

    assert result.status_code == 404
    assert "no encontrada" in result.error


@pytest.mark.asyncio
async def test_delete_sale_with_audit(mock_uow, mock_logger, sample_sale):
    """Eliminar venta con auditoría llama audit_service.log_deletion."""
    mock_audit = AsyncMock()
    service = SaleService(uow=mock_uow, audit_service=mock_audit, logger=mock_logger)
    mock_uow.sale_repo.get_by_id.return_value = sample_sale

    result = await service.delete(1, username="admin")

    assert result.status_code == 204
    mock_audit.log_deletion.assert_called_once()


@pytest.mark.asyncio
async def test_delete_sale_error(mock_uow, mock_logger, sample_sale):
    """Error al eliminar venta retorna 400."""
    service = SaleService(uow=mock_uow, logger=mock_logger)
    mock_uow.sale_repo.get_by_id.return_value = sample_sale
    mock_uow.sale_repo.delete.side_effect = Exception("fk constraint")

    result = await service.delete(1)

    assert result.status_code == 400


# ==================== Pizza Helper Tests ====================

def test_es_pizza_by_category():
    """_es_pizza detecta pizza por categoría."""
    service = SaleService(uow=AsyncMock(), logger=AsyncMock())
    producto = build_product_model(
        id=1, nombre="Muzzarella", categoria_id=1,
        precios=[build_product_price_model(1, 1, 1, 1500.0)]
    )
    producto.categoria = build_category_model(id=1, nombre="Pizzas")

    assert service._es_pizza(producto) is True


def test_es_pizza_by_name():
    """_es_pizza detecta pizza por nombre."""
    service = SaleService(uow=AsyncMock(), logger=AsyncMock())
    producto = build_product_model(
        id=1, nombre="Pizza Napolitana", categoria_id=1,
        precios=[build_product_price_model(1, 1, 1, 1500.0)]
    )
    producto.categoria = None

    assert service._es_pizza(producto) is True


def test_es_pizza_not_pizza():
    """_es_pizza retorna False para no-pizza."""
    service = SaleService(uow=AsyncMock(), logger=AsyncMock())
    producto = build_product_model(
        id=1, nombre="Empanada", categoria_id=2,
        precios=[build_product_price_model(1, 1, 1, 1200.0)]
    )
    producto.categoria = build_category_model(id=2, nombre="Empanadas")

    assert service._es_pizza(producto) is False


def test_get_pizza_mitad_mitad_price():
    """_get_pizza_mitad_mitad_price retorna el precio de la más cara."""
    service = SaleService(uow=AsyncMock(), logger=AsyncMock())
    p1 = build_product_model(
        id=1, nombre="Muzzarella", categoria_id=1,
        precios=[build_product_price_model(1, 1, 1, 1500.0)]
    )
    p2 = build_product_model(
        id=2, nombre="Napolitana", categoria_id=1,
        precios=[build_product_price_model(2, 2, 1, 1800.0)]
    )

    result = service._get_pizza_mitad_mitad_price(p1, p2)

    assert result == Decimal("1800.00")


def test_get_pizza_mitad_mitad_price_no_prices():
    """_get_pizza_mitad_mitad_price retorna None si falta precio."""
    service = SaleService(uow=AsyncMock(), logger=AsyncMock())
    p1 = build_product_model(id=1, nombre="Muzzarella", categoria_id=1, precios=[])
    p2 = build_product_model(
        id=2, nombre="Napolitana", categoria_id=1,
        precios=[build_product_price_model(2, 2, 1, 1800.0)]
    )

    result = service._get_pizza_mitad_mitad_price(p1, p2)

    assert result is None


@pytest.mark.asyncio
async def test_validate_pizza_mitad_mitad_success(mock_uow, mock_logger):
    """_validate_pizza_mitad_mitad retorna None si todo es válido."""
    from types import SimpleNamespace

    service = SaleService(uow=mock_uow, logger=mock_logger)
    p1 = build_product_model(
        id=1, nombre="Muzzarella", categoria_id=1,
        precios=[build_product_price_model(1, 1, 1, 1500.0)]
    )
    p1.categoria = build_category_model(id=1, nombre="Pizzas")
    p1.activo = True

    p2 = build_product_model(
        id=2, nombre="Napolitana", categoria_id=1,
        precios=[build_product_price_model(2, 2, 1, 1800.0)]
    )
    p2.categoria = build_category_model(id=1, nombre="Pizzas")
    p2.activo = True

    mock_uow.product_repo.get_by_id.side_effect = lambda pid: {1: p1, 2: p2}[pid]

    pizza_mm = SimpleNamespace(producto_id_izquierda=1, producto_id_derecha=2)
    result = await service._validate_pizza_mitad_mitad(pizza_mm, mock_uow)

    assert result is None  # None means validation passed


@pytest.mark.asyncio
async def test_validate_pizza_mitad_mitad_product_not_found(mock_uow, mock_logger):
    """_validate_pizza_mitad_mitad retorna error si producto no existe."""
    from types import SimpleNamespace

    service = SaleService(uow=mock_uow, logger=mock_logger)
    mock_uow.product_repo.get_by_id.return_value = None

    pizza_mm = SimpleNamespace(producto_id_izquierda=99, producto_id_derecha=100)
    result = await service._validate_pizza_mitad_mitad(pizza_mm, mock_uow)

    assert result is not None
    assert result.status_code == 404


@pytest.mark.asyncio
async def test_validate_pizza_mitad_mitad_inactive(mock_uow, mock_logger):
    """_validate_pizza_mitad_mitad retorna error si producto inactivo."""
    from types import SimpleNamespace

    service = SaleService(uow=mock_uow, logger=mock_logger)
    p1 = build_product_model(id=1, nombre="Muzzarella", categoria_id=1, precios=[])
    p1.categoria = build_category_model(id=1, nombre="Pizzas")
    p1.activo = True

    p2 = build_product_model(id=2, nombre="Napolitana", categoria_id=1, precios=[])
    p2.categoria = build_category_model(id=1, nombre="Pizzas")
    p2.activo = False

    mock_uow.product_repo.get_by_id.side_effect = lambda pid: {1: p1, 2: p2}[pid]

    pizza_mm = SimpleNamespace(producto_id_izquierda=1, producto_id_derecha=2)
    result = await service._validate_pizza_mitad_mitad(pizza_mm, mock_uow)

    assert result is not None
    assert result.status_code == 400
    assert "activos" in result.error


@pytest.mark.asyncio
async def test_validate_pizza_mitad_mitad_not_pizza(mock_uow, mock_logger):
    """_validate_pizza_mitad_mitad retorna error si producto no es pizza."""
    from types import SimpleNamespace

    service = SaleService(uow=mock_uow, logger=mock_logger)
    p1 = build_product_model(id=1, nombre="Empanada", categoria_id=2, precios=[])
    p1.categoria = build_category_model(id=2, nombre="Empanadas")
    p1.activo = True

    p2 = build_product_model(id=2, nombre="Napolitana", categoria_id=1, precios=[])
    p2.categoria = build_category_model(id=1, nombre="Pizzas")
    p2.activo = True

    mock_uow.product_repo.get_by_id.side_effect = lambda pid: {1: p1, 2: p2}[pid]

    pizza_mm = SimpleNamespace(producto_id_izquierda=1, producto_id_derecha=2)
    result = await service._validate_pizza_mitad_mitad(pizza_mm, mock_uow)

    assert result is not None
    assert result.status_code == 400
    assert "pizzas" in result.error


@pytest.mark.asyncio
async def test_validate_pizza_mitad_mitad_same_product(mock_uow, mock_logger):
    """_validate_pizza_mitad_mitad retorna error si son el mismo producto."""
    from types import SimpleNamespace

    service = SaleService(uow=mock_uow, logger=mock_logger)
    p1 = build_product_model(id=1, nombre="Muzzarella", categoria_id=1, precios=[])
    p1.categoria = build_category_model(id=1, nombre="Pizzas")
    p1.activo = True

    mock_uow.product_repo.get_by_id.return_value = p1

    pizza_mm = SimpleNamespace(producto_id_izquierda=1, producto_id_derecha=1)
    result = await service._validate_pizza_mitad_mitad(pizza_mm, mock_uow)

    assert result is not None
    assert result.status_code == 400
    assert "diferentes" in result.error
