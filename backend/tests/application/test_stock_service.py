"""
Tests for StockService.
Tests stock management operations with mocked repositories and UnitOfWork.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.application.stock_service import StockService, ServiceResult, _compute_estado
from tests.helpers import build_stock_model


# ==================== _compute_estado Tests ====================


def test_compute_estado_sin_stock():
    assert _compute_estado(0, 10, 5) == "sin_stock"


def test_compute_estado_critical():
    assert _compute_estado(3, 10, 5) == "critical"


def test_compute_estado_warning():
    assert _compute_estado(7, 10, 5) == "warning"


def test_compute_estado_ok():
    assert _compute_estado(20, 10, 5) == "ok"


def test_compute_estado_no_thresholds():
    assert _compute_estado(5, None, None) == "ok"


def test_compute_estado_zero_is_sin_stock_even_without_thresholds():
    assert _compute_estado(0, None, None) == "sin_stock"


# ==================== get_all_stocks Tests ====================


@pytest.mark.asyncio
async def test_get_all_stocks_success(mock_uow, mock_logger):
    """Test getting all stocks with categories."""
    service = StockService(uow=mock_uow, logger=mock_logger)

    cat1 = MagicMock(id=1, nombre="Pizza", stock_visible=True, stock_por_producto=False)
    cat2 = MagicMock(id=2, nombre="Empanadas", stock_visible=True, stock_por_producto=False)
    mock_uow.product_category_repo.list_by_active.return_value = [cat1, cat2]

    stock1 = build_stock_model(categoria_id=1, cantidad=50, umbral_amarillo=10, umbral_rojo=5)
    mock_uow.stock_repo.get_all.return_value = [stock1]

    result = await service.get_all_stocks()

    assert result.status_code == 200
    categorias = result.value["categorias"]
    assert len(categorias) == 2
    # cat1 has stock
    assert categorias[0]["categoria_id"] == 1
    assert categorias[0]["cantidad"] == 50
    assert categorias[0]["estado"] == "ok"
    # cat2 has no stock
    assert categorias[1]["categoria_id"] == 2
    assert categorias[1]["cantidad"] == 0
    assert categorias[1]["estado"] == "sin_stock"


@pytest.mark.asyncio
async def test_get_all_stocks_empty(mock_uow, mock_logger):
    """Test getting stocks when no categories exist."""
    service = StockService(uow=mock_uow, logger=mock_logger)
    mock_uow.product_category_repo.list_by_active.return_value = []
    mock_uow.stock_repo.get_all.return_value = []

    result = await service.get_all_stocks()

    assert result.status_code == 200
    assert result.value["categorias"] == []


# ==================== add_stock Tests ====================


@pytest.mark.asyncio
async def test_add_stock_success(mock_uow, mock_logger):
    """Test successfully adding stock to a category."""
    service = StockService(uow=mock_uow, logger=mock_logger)

    cat = MagicMock(id=1, nombre="Pizza", stock_por_producto=False)
    mock_uow.product_category_repo.get_by_id.return_value = cat

    stock = build_stock_model(categoria_id=1, cantidad=10)
    mock_uow.stock_repo.get_by_categoria_id.return_value = stock

    result = await service.add_stock(categoria_id=1, cantidad=5, username="admin")

    assert result.status_code == 200
    assert result.value["cantidad"] == 15  # 10 + 5
    mock_uow.audit_repo.log_action.assert_called_once()
    mock_uow.commit.assert_called_once()


@pytest.mark.asyncio
async def test_add_stock_zero_quantity(mock_uow, mock_logger):
    """Test adding zero stock returns error."""
    service = StockService(uow=mock_uow, logger=mock_logger)

    result = await service.add_stock(categoria_id=1, cantidad=0, username="admin")

    assert result.status_code == 400
    assert "cero" in result.error


@pytest.mark.asyncio
async def test_add_stock_category_not_found(mock_uow, mock_logger):
    """Test adding stock to non-existent category."""
    service = StockService(uow=mock_uow, logger=mock_logger)
    mock_uow.product_category_repo.get_by_id.return_value = None

    result = await service.add_stock(categoria_id=999, cantidad=5, username="admin")

    assert result.status_code == 404
    assert "Categoría no encontrada" in result.error


@pytest.mark.asyncio
async def test_add_stock_creates_stock_if_none(mock_uow, mock_logger):
    """Test adding stock when no stock record exists (upsert)."""
    service = StockService(uow=mock_uow, logger=mock_logger)

    cat = MagicMock(id=1, nombre="Pizza", stock_por_producto=False)
    mock_uow.product_category_repo.get_by_id.return_value = cat
    mock_uow.stock_repo.get_by_categoria_id.return_value = None

    result = await service.add_stock(categoria_id=1, cantidad=10, username="admin")

    assert result.status_code == 200
    mock_uow.stock_repo.upsert.assert_called_once()


@pytest.mark.asyncio
async def test_add_stock_negative_clamps_to_zero(mock_uow, mock_logger):
    """Test that removing more stock than available clamps to 0."""
    service = StockService(uow=mock_uow, logger=mock_logger)

    cat = MagicMock(id=1, nombre="Pizza", stock_por_producto=False)
    mock_uow.product_category_repo.get_by_id.return_value = cat

    stock = build_stock_model(categoria_id=1, cantidad=3)
    mock_uow.stock_repo.get_by_categoria_id.return_value = stock

    result = await service.add_stock(categoria_id=1, cantidad=-10, username="admin")

    assert result.status_code == 200
    assert result.value["cantidad"] == 0  # max(0, 3 + (-10)) = 0


# ==================== configure_alerts Tests ====================


@pytest.mark.asyncio
async def test_configure_alerts_success(mock_uow, mock_logger):
    """Test configuring stock alert thresholds."""
    service = StockService(uow=mock_uow, logger=mock_logger)

    cat = MagicMock(id=1, nombre="Pizza", stock_por_producto=False)
    mock_uow.product_category_repo.get_by_id.return_value = cat

    stock = build_stock_model(categoria_id=1, cantidad=50)
    mock_uow.stock_repo.get_by_categoria_id.return_value = stock

    result = await service.configure_alerts(
        categoria_id=1, umbral_amarillo=15, umbral_rojo=5, username="admin"
    )

    assert result.status_code == 200
    assert result.value["umbral_amarillo"] == 15
    assert result.value["umbral_rojo"] == 5
    mock_uow.audit_repo.log_action.assert_called_once()


@pytest.mark.asyncio
async def test_configure_alerts_category_not_found(mock_uow, mock_logger):
    """Test configuring alerts for non-existent category."""
    service = StockService(uow=mock_uow, logger=mock_logger)
    mock_uow.product_category_repo.get_by_id.return_value = None

    result = await service.configure_alerts(
        categoria_id=999, umbral_amarillo=10, umbral_rojo=5, username="admin"
    )

    assert result.status_code == 404


@pytest.mark.asyncio
async def test_configure_alerts_creates_stock_if_none(mock_uow, mock_logger):
    """Test configuring alerts creates stock record if none exists."""
    service = StockService(uow=mock_uow, logger=mock_logger)

    cat = MagicMock(id=1, nombre="Pizza", stock_por_producto=False)
    mock_uow.product_category_repo.get_by_id.return_value = cat
    mock_uow.stock_repo.get_by_categoria_id.return_value = None

    result = await service.configure_alerts(
        categoria_id=1, umbral_amarillo=10, umbral_rojo=5, username="admin"
    )

    assert result.status_code == 200
    mock_uow.stock_repo.upsert.assert_called_once()


# ==================== get_movements Tests ====================


@pytest.mark.asyncio
async def test_get_movements_success(mock_uow, mock_logger):
    """Test getting stock movements history."""
    service = StockService(uow=mock_uow, logger=mock_logger)

    m1 = MagicMock(id=1, timestamp="2024-01-01", username="admin", action="UPDATE", changes={"tipo": "INGRESO"})
    m2 = MagicMock(id=2, timestamp="2024-01-02", username="admin", action="UPDATE", changes={"tipo": "AJUSTE_BAJA"})
    mock_uow.audit_repo.get_by_entity.return_value = [m1, m2]

    result = await service.get_movements(categoria_id=1, limit=50)

    assert result.status_code == 200
    assert len(result.value) == 2
    mock_uow.audit_repo.get_by_entity.assert_called_once_with(
        entity_type="Stock", entity_id=1, limit=50
    )


@pytest.mark.asyncio
async def test_get_movements_empty(mock_uow, mock_logger):
    """Test getting movements when none exist."""
    service = StockService(uow=mock_uow, logger=mock_logger)
    mock_uow.audit_repo.get_by_entity.return_value = []

    result = await service.get_movements(categoria_id=1)

    assert result.status_code == 200
    assert result.value == []


# ==================== get_product_stocks Tests ====================


@pytest.mark.asyncio
async def test_get_product_stocks_sorted_like_products(mock_uow, mock_logger):
    """Product stock breakdown should be sorted by product id (same as productos list)."""
    service = StockService(uow=mock_uow, logger=mock_logger)

    cat = MagicMock(id=1, nombre="Pizza", stock_por_producto=True)
    mock_uow.product_category_repo.get_by_id.return_value = cat

    p1 = MagicMock(id=1)
    p2 = MagicMock(id=2)
    p3 = MagicMock(id=3)
    mock_uow.product_repo.list.return_value = [p1, p2, p3]

    mock_uow.product_stock_repo = AsyncMock()
    mock_uow.product_stock_repo.get_or_create = AsyncMock(return_value=None)

    ps3 = MagicMock(producto_id=3, cantidad=4, umbral_amarillo=8, umbral_rojo=2, producto=MagicMock(nombre="C"))
    ps1 = MagicMock(producto_id=1, cantidad=10, umbral_amarillo=5, umbral_rojo=2, producto=MagicMock(nombre="A"))
    ps2 = MagicMock(producto_id=2, cantidad=0, umbral_amarillo=5, umbral_rojo=2, producto=MagicMock(nombre="B"))
    mock_uow.product_stock_repo.get_by_categoria_id.return_value = [ps3, ps1, ps2]

    result = await service.get_product_stocks(categoria_id=1)

    assert result.status_code == 200
    assert [item["producto_id"] for item in result.value] == [1, 2, 3]
    assert mock_uow.product_stock_repo.get_or_create.await_count == 3


@pytest.mark.asyncio
async def test_get_product_stocks_category_not_found(mock_uow, mock_logger):
    service = StockService(uow=mock_uow, logger=mock_logger)
    mock_uow.product_category_repo.get_by_id.return_value = None

    result = await service.get_product_stocks(categoria_id=999)

    assert result.status_code == 404
    assert "Categoría no encontrada" in result.error


@pytest.mark.asyncio
async def test_get_product_stocks_requires_per_product_enabled(mock_uow, mock_logger):
    service = StockService(uow=mock_uow, logger=mock_logger)
    mock_uow.product_category_repo.get_by_id.return_value = MagicMock(id=1, stock_por_producto=False)

    result = await service.get_product_stocks(categoria_id=1)

    assert result.status_code == 400
    assert "stock por producto" in result.error
