"""
Tests for ProductService.
Tests business logic with mocked repositories, FileService and UnitOfWork.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import UploadFile
from io import BytesIO

from app.application.product_service import ProductService, ServiceResult
from app.domain.models.product import Product
from app.presentation.schemas.product_schemas import (
    ProductoCreateRequest,
    ProductoUpdateRequest,
    ProductoPrecioRequest
)
from tests.helpers import build_product_model, build_product_price_model, build_category_model
from decimal import Decimal


# ==================== Create Tests ====================

@pytest.mark.asyncio
async def test_create_product_generates_sku(mock_uow, mock_file_service, mock_cache_service, mock_logger):
    """Test that creating a product automatically generates SKU."""
    # Arrange
    service = ProductService(uow=mock_uow, file_service=mock_file_service, cache_service=mock_cache_service, logger=mock_logger)
    
    # Mock category
    categoria = build_category_model(id=1, nombre="Empanadas")
    mock_uow.product_category_repo.get_by_id = AsyncMock(return_value=categoria)
    mock_uow.product_repo.add = AsyncMock(side_effect=lambda p: setattr(p, 'id', 1))
    mock_uow.product_repo.get_by_id.return_value = build_product_model(1, "Empanada de Carne", "EMPA-CARN-001", 1)
    
    request = ProductoCreateRequest(
        nombre="Empanada de Carne",
        categoria_id=1,
        precios=[
            ProductoPrecioRequest(cantidad=1, precio=Decimal("1200.00"))
        ]
    )
    
    # Act
    with patch('app.application.product_service.generar_sku_producto', return_value="EMPA-CARN-001") as mock_sku:
        result = await service.create(request, image=None)
    
    # Assert
    assert result.status_code == 201
    assert result.value is not None
    mock_sku.assert_called_once_with("Empanada de Carne", "Empanadas")
    mock_uow.product_repo.add.assert_called_once()


@pytest.mark.asyncio
async def test_create_product_invalid_category(mock_uow, mock_file_service, mock_cache_service, mock_logger):
    """Test creating product with non-existent category returns 404."""
    # Arrange
    service = ProductService(uow=mock_uow, file_service=mock_file_service, cache_service=mock_cache_service, logger=mock_logger)
    
    # Category doesn't exist
    mock_uow.product_category_repo.get_by_id = AsyncMock(return_value=None)
    
    request = ProductoCreateRequest(
        nombre="Empanada de Carne",
        categoria_id=999,
        precios=[
            ProductoPrecioRequest(cantidad=1, precio=Decimal("1200.00"))
        ]
    )
    
    # Act
    result = await service.create(request, image=None)
    
    # Assert
    assert result.status_code == 404
    assert result.error == "Categoría no encontrada"
    mock_uow.product_repo.add.assert_not_called()


@pytest.mark.asyncio
async def test_create_product_with_image(mock_uow, mock_file_service, mock_cache_service, mock_logger):
    """Test creating product with image."""
    # Arrange
    service = ProductService(uow=mock_uow, file_service=mock_file_service, cache_service=mock_cache_service, logger=mock_logger)
    
    # Mock category
    categoria = build_category_model(id=1, nombre="Empanadas")
    mock_uow.product_category_repo.get_by_id = AsyncMock(return_value=categoria)
    mock_uow.product_repo.add = AsyncMock(side_effect=lambda p: setattr(p, 'id', 1))
    mock_uow.product_repo.get_by_id.return_value = build_product_model(1, "Empanada de Carne", "EMPA-CARN-001", 1)
    
    request = ProductoCreateRequest(
        nombre="Empanada de Carne",
        categoria_id=1,
        precios=[
            ProductoPrecioRequest(cantidad=1, precio=Decimal("1200.00")),
            ProductoPrecioRequest(cantidad=6, precio=Decimal("6000.00"))
        ]
    )
    
    # Mock image file
    image_content = b"fake image content"
    image = UploadFile(filename="empanada.jpg", file=BytesIO(image_content))
    
    mock_file_service.save_file = AsyncMock(return_value="uploads/productos/empanada.jpg")
    
    # Act
    with patch('app.application.product_service.generar_sku_producto', return_value="EMPA-CARN-001"):
        result = await service.create(request, image)
    
    # Assert
    assert result.status_code == 201
    assert result.value is not None
    assert result.error is None
    
    # Verify mock calls — image saved with SKU as filename_base
    mock_file_service.save_file.assert_called_once_with(image, filename_base="EMPA-CARN-001")
    mock_uow.product_repo.add.assert_called_once()
    mock_uow.commit.assert_called_once()


@pytest.mark.asyncio
async def test_create_product_without_image(mock_uow, mock_file_service, mock_cache_service, mock_logger):
    """Test creating product without image."""
    # Arrange
    service = ProductService(uow=mock_uow, file_service=mock_file_service, cache_service=mock_cache_service, logger=mock_logger)
    
    # Mock category
    categoria = build_category_model(id=1, nombre="Empanadas")
    mock_uow.product_category_repo.get_by_id = AsyncMock(return_value=categoria)
    mock_uow.product_repo.add = AsyncMock(side_effect=lambda p: setattr(p, 'id', 1))
    mock_uow.product_repo.get_by_id.return_value = build_product_model(1, "Empanada de Pollo", "EMPA-POLL-001", 1)
    
    request = ProductoCreateRequest(
        nombre="Empanada de Pollo",
        categoria_id=1,
        precios=[
            ProductoPrecioRequest(cantidad=1, precio=Decimal("1200.00"))
        ]
    )
    
    # Act
    with patch('app.application.product_service.generar_sku_producto', return_value="EMPA-POLL-001"):
        result = await service.create(request, image=None)
    
    # Assert
    assert result.status_code == 201
    assert result.value is not None
    
    # Verify file service was not called
    mock_file_service.save_file.assert_not_called()
    mock_uow.product_repo.add.assert_called_once()
    mock_uow.commit.assert_called_once()


@pytest.mark.asyncio
async def test_create_product_rollback_on_error(mock_uow, mock_file_service, mock_cache_service, mock_logger):
    """Test that image is deleted on database error."""
    # Arrange
    service = ProductService(uow=mock_uow, file_service=mock_file_service, cache_service=mock_cache_service, logger=mock_logger)
    
    # Mock category
    categoria = build_category_model(id=1, nombre="Test")
    mock_uow.product_category_repo.get_by_id = AsyncMock(return_value=categoria)
    
    request = ProductoCreateRequest(
        nombre="Test Product",
        categoria_id=1,
        precios=[
            ProductoPrecioRequest(cantidad=1, precio=Decimal("1000.00"))
        ]
    )
    
    image = UploadFile(filename="test.jpg", file=BytesIO(b"test"))
    mock_file_service.save_file = AsyncMock(return_value="uploads/productos/test.jpg")
    mock_uow.product_repo.add.side_effect = Exception("Database error")
    
    # Act
    with patch('app.application.product_service.generar_sku_producto', return_value="TEST-PROD-001"):
        result = await service.create(request, image)
    
    # Assert
    assert result.status_code == 400
    assert result.error == "Database error"
    
    # Verify image was saved with SKU and then deleted on error
    mock_file_service.save_file.assert_called_once_with(image, filename_base="TEST-PROD-001")
    mock_file_service.delete_file.assert_called_once_with("uploads/productos/test.jpg")


@pytest.mark.asyncio
async def test_create_product_with_multiple_prices(mock_uow, mock_file_service, mock_cache_service, mock_logger):
    """Test creating product with tiered pricing."""
    # Arrange
    service = ProductService(uow=mock_uow, file_service=mock_file_service, cache_service=mock_cache_service, logger=mock_logger)
    
    # Mock category
    categoria = build_category_model(id=1, nombre="Empanadas")
    mock_uow.product_category_repo.get_by_id = AsyncMock(return_value=categoria)
    mock_uow.product_repo.add = AsyncMock(side_effect=lambda p: setattr(p, 'id', 1))
    mock_uow.product_repo.get_by_id.return_value = build_product_model(1, "Empanada Premium", "EMPA-PREM-001", 1)
    
    request = ProductoCreateRequest(
        nombre="Empanada Premium",
        categoria_id=1,
        precios=[
            ProductoPrecioRequest(cantidad=1, precio=Decimal("1200.00")),
            ProductoPrecioRequest(cantidad=6, precio=Decimal("6000.00")),
            ProductoPrecioRequest(cantidad=12, precio=Decimal("10800.00"))
        ]
    )
    
    # Act
    with patch('app.application.product_service.generar_sku_producto', return_value="EMPA-PREM-001"):
        result = await service.create(request, image=None)
    
    # Assert
    assert result.status_code == 201
    mock_uow.product_repo.add.assert_called_once()


# ==================== Get All Tests ====================

@pytest.mark.asyncio
async def test_get_all_products(mock_uow, mock_file_service, mock_cache_service, mock_logger, multiple_products):
    """Test getting all products without filters."""
    # Arrange
    service = ProductService(uow=mock_uow, file_service=mock_file_service, cache_service=mock_cache_service, logger=mock_logger)
    mock_uow.product_repo.list.return_value = multiple_products
    
    # Act
    result = await service.get_all()
    
    # Assert
    assert len(result) == 3
    mock_uow.product_repo.list.assert_called_once_with(categoria_id=None, active=None)


@pytest.mark.asyncio
async def test_get_all_products_with_categoria_filter(mock_uow, mock_file_service, mock_cache_service, mock_logger):
    """Test getting products filtered by category."""
    # Arrange
    service = ProductService(uow=mock_uow, file_service=mock_file_service, cache_service=mock_cache_service, logger=mock_logger)
    filtered_products = [build_product_model(1, "Empanada", 1)]
    mock_uow.product_repo.list.return_value = filtered_products
    
    # Act
    result = await service.get_all(categoria_id=1)
    
    # Assert
    assert len(result) == 1
    mock_uow.product_repo.list.assert_called_once_with(categoria_id=1, active=None)


@pytest.mark.asyncio
async def test_get_all_products_with_active_filter(mock_uow, mock_file_service, mock_cache_service, mock_logger):
    """Test getting only active products."""
    # Arrange
    service = ProductService(uow=mock_uow, file_service=mock_file_service, cache_service=mock_cache_service, logger=mock_logger)
    active_products = [
        build_product_model(1, "Product 1", 1, None, True),
        build_product_model(2, "Product 2", 1, None, True)
    ]
    mock_uow.product_repo.list.return_value = active_products
    
    # Act
    result = await service.get_all(active=True)
    
    # Assert
    assert len(result) == 2
    assert all(p.activo for p in result)
    mock_uow.product_repo.list.assert_called_once_with(categoria_id=None, active=True)


@pytest.mark.asyncio
async def test_get_all_products_combined_filters(mock_uow, mock_file_service, mock_cache_service, mock_logger):
    """Test getting products with multiple filters."""
    # Arrange
    service = ProductService(uow=mock_uow, file_service=mock_file_service, cache_service=mock_cache_service, logger=mock_logger)
    mock_uow.product_repo.list.return_value = []
    
    # Act
    result = await service.get_all(categoria_id=1, active=True)
    
    # Assert
    mock_uow.product_repo.list.assert_called_once_with(categoria_id=1, active=True)


# ==================== Get By ID Tests ====================

@pytest.mark.asyncio
async def test_get_by_id_success(mock_uow, mock_file_service, mock_cache_service, mock_logger, sample_product):
    """Test getting product by ID successfully."""
    # Arrange
    service = ProductService(uow=mock_uow, file_service=mock_file_service, cache_service=mock_cache_service, logger=mock_logger)
    mock_uow.product_repo.get_by_id.return_value = sample_product
    
    # Act
    result = await service.get_by_id(1)
    
    # Assert
    assert result.status_code == 200
    assert result.value is not None
    assert result.value.id == 1
    mock_uow.product_repo.get_by_id.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_get_by_id_not_found(mock_uow, mock_file_service, mock_cache_service, mock_logger):
    """Test getting product by ID when it doesn't exist."""
    # Arrange
    service = ProductService(uow=mock_uow, file_service=mock_file_service, cache_service=mock_cache_service, logger=mock_logger)
    mock_uow.product_repo.get_by_id.return_value = None
    
    # Act
    result = await service.get_by_id(999)
    
    # Assert
    assert result.status_code == 404
    assert result.error == "Producto no encontrado"
    mock_uow.product_repo.get_by_id.assert_called_once_with(999)


# ==================== Update Tests ====================

@pytest.mark.asyncio
async def test_update_product_basic_fields(mock_uow, mock_file_service, mock_cache_service, mock_logger, sample_product):
    """Test updating basic product fields."""
    # Arrange
    service = ProductService(uow=mock_uow, file_service=mock_file_service, cache_service=mock_cache_service, logger=mock_logger)
    mock_uow.product_repo.get_by_id.return_value = sample_product
    
    request = ProductoUpdateRequest(
        nombre="Nuevo Nombre",
        categoria_id=2
    )
    
    # Act
    result = await service.update(1, producto_update=request)
    
    # Assert
    assert result.status_code == 200
    assert result.value is not None
    assert mock_uow.product_repo.get_by_id.call_count == 2
    mock_uow.commit.assert_called_once()


@pytest.mark.asyncio
async def test_update_product_replaces_prices(mock_uow, mock_file_service, mock_cache_service, mock_logger, sample_product):
    """Test that updating prices replaces old prices."""
    # Arrange
    service = ProductService(uow=mock_uow, file_service=mock_file_service, cache_service=mock_cache_service, logger=mock_logger)
    mock_uow.product_repo.get_by_id.return_value = sample_product
    mock_uow.product_repo.refresh = AsyncMock()
    mock_uow.session = MagicMock()
    mock_uow.session.flush = AsyncMock()
    
    request = ProductoUpdateRequest(
        precios=[
            ProductoPrecioRequest(cantidad=1, precio=Decimal("1500.00")),
            ProductoPrecioRequest(cantidad=6, precio=Decimal("7500.00"))
        ]
    )
    
    # Act
    result = await service.update(1, producto_update=request)
    
    # Assert
    assert result.status_code == 200
    
    # Verify replace_prices was called
    mock_uow.product_repo.replace_prices.assert_called_once()
    call_args = mock_uow.product_repo.replace_prices.call_args
    assert call_args[0][0] == sample_product.id  # producto_id
    assert len(call_args[0][1]) == 2  # new prices


@pytest.mark.asyncio
async def test_update_product_with_new_image_different_extension(mock_uow, mock_file_service, mock_cache_service, mock_logger, sample_product):
    """Test updating product image with different extension: old file is deleted, new saved with SKU."""
    # Arrange
    service = ProductService(uow=mock_uow, file_service=mock_file_service, cache_service=mock_cache_service, logger=mock_logger)
    sample_product.sku = "EMP-CARNE-12345"
    sample_product.imagen = "uploads/productos/EMP-CARNE-12345.jpg"
    mock_uow.product_repo.get_by_id.return_value = sample_product
    
    # Different extension: .jpg -> .png
    new_image = UploadFile(filename="new.png", file=BytesIO(b"new"))
    mock_file_service.save_file = AsyncMock(return_value="uploads/productos/EMP-CARNE-12345.png")
    
    # Act
    result = await service.update(1, image=new_image)
    
    # Assert
    assert result.status_code == 200
    
    # Verify new image was saved with SKU as filename_base
    mock_file_service.save_file.assert_called_once_with(new_image, filename_base="EMP-CARNE-12345")
    
    # Old path differs from new path -> old file should be deleted
    mock_file_service.delete_file.assert_called_once_with("uploads/productos/EMP-CARNE-12345.jpg")


@pytest.mark.asyncio
async def test_update_product_with_new_image_same_extension(mock_uow, mock_file_service, mock_cache_service, mock_logger, sample_product):
    """Test updating product image with same extension: file is overwritten, delete_file NOT called."""
    # Arrange
    service = ProductService(uow=mock_uow, file_service=mock_file_service, cache_service=mock_cache_service, logger=mock_logger)
    sample_product.sku = "EMP-CARNE-12345"
    sample_product.imagen = "uploads/productos/EMP-CARNE-12345.jpg"
    mock_uow.product_repo.get_by_id.return_value = sample_product
    
    # Same extension: .jpg -> .jpg (overwrite)
    new_image = UploadFile(filename="new.jpg", file=BytesIO(b"new"))
    mock_file_service.save_file = AsyncMock(return_value="uploads/productos/EMP-CARNE-12345.jpg")
    
    # Act
    result = await service.update(1, image=new_image)
    
    # Assert
    assert result.status_code == 200
    
    # Verify new image was saved with SKU as filename_base
    mock_file_service.save_file.assert_called_once_with(new_image, filename_base="EMP-CARNE-12345")
    
    # Same path -> delete_file must NOT be called (file was overwritten in place)
    mock_file_service.delete_file.assert_not_called()


@pytest.mark.asyncio
async def test_update_product_deactivate(mock_uow, mock_file_service, mock_cache_service, mock_logger, sample_product):
    """Test deactivating product."""
    # Arrange
    service = ProductService(uow=mock_uow, file_service=mock_file_service, cache_service=mock_cache_service, logger=mock_logger)
    mock_uow.product_repo.get_by_id.return_value = sample_product
    
    # Act
    result = await service.update(1, active=False)
    
    # Assert
    assert result.status_code == 200
    mock_uow.commit.assert_called_once()


@pytest.mark.asyncio
async def test_update_product_not_found(mock_uow, mock_file_service, mock_cache_service, mock_logger):
    """Test updating product that doesn't exist."""
    # Arrange
    service = ProductService(uow=mock_uow, file_service=mock_file_service, cache_service=mock_cache_service, logger=mock_logger)
    mock_uow.product_repo.get_by_id.return_value = None
    
    request = ProductoUpdateRequest(nombre="Test")
    
    # Act
    result = await service.update(999, producto_update=request)
    
    # Assert
    assert result.status_code == 404
    assert result.error == "Producto no encontrado"
    mock_uow.commit.assert_not_called()


@pytest.mark.asyncio
async def test_update_product_error_rollback_image(mock_uow, mock_file_service, mock_cache_service, mock_logger, sample_product):
    """Test that new image is deleted on update error."""
    # Arrange
    service = ProductService(uow=mock_uow, file_service=mock_file_service, cache_service=mock_cache_service, logger=mock_logger)
    mock_uow.product_repo.get_by_id.return_value = sample_product
    
    new_image = UploadFile(filename="new.jpg", file=BytesIO(b"new"))
    mock_file_service.save_file = AsyncMock(return_value="uploads/productos/EMP-TEST-00001.jpg")
    mock_uow.commit.side_effect = Exception("Database error")
    
    # Act
    result = await service.update(1, image=new_image)
    
    # Assert
    assert result.status_code == 400
    
    # Verify new image (SKU-named) was deleted on error
    assert mock_file_service.delete_file.call_count == 1
    mock_file_service.delete_file.assert_called_with("uploads/productos/EMP-TEST-00001.jpg")
