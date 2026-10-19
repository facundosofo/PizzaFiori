"""
Tests for ProductAnalyticsService.
Tests product analytics operations with mocked session and UnitOfWork.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from app.application.product_analytics_service import ProductAnalyticsService


def _make_row(**kwargs):
    row = MagicMock()
    for k, v in kwargs.items():
        setattr(row, k, v)
    row._mapping = kwargs
    return row


def _mock_result(rows):
    result = MagicMock()
    result.fetchall.return_value = rows
    result.all.return_value = rows
    result.__iter__ = lambda self: iter(rows)
    return result


def _mock_scalar_result(value):
    result = MagicMock()
    result.scalar.return_value = value
    return result


# ==================== get_top_products Tests ====================


@pytest.mark.asyncio
async def test_get_top_products_success(mock_uow, mock_logger):
    """Test getting top products."""
    service = ProductAnalyticsService(uow=mock_uow, logger=mock_logger)

    rows = [
        _make_row(nombre="Pizza Grande", categoria="Pizzas", cantidad=100, precio=1500.0, en_stock=True),
        _make_row(nombre="Empanada", categoria="Empanadas", cantidad=50, precio=500.0, en_stock=True),
    ]
    mock_uow.session.execute = AsyncMock(return_value=_mock_result(rows))

    result = await service.get_top_products(limit=10)

    assert result.status_code == 200


@pytest.mark.asyncio
async def test_get_top_products_with_category_filter(mock_uow, mock_logger):
    """Test getting top products filtered by category."""
    service = ProductAnalyticsService(uow=mock_uow, logger=mock_logger)

    rows = [
        _make_row(nombre="Pizza Grande", categoria="Pizzas", cantidad=100, precio=1500.0, en_stock=True),
    ]
    mock_uow.session.execute = AsyncMock(return_value=_mock_result(rows))

    result = await service.get_top_products(limit=5, category="Pizzas")

    assert result.status_code == 200


@pytest.mark.asyncio
async def test_get_top_products_error(mock_uow, mock_logger):
    """Test top products error handling."""
    service = ProductAnalyticsService(uow=mock_uow, logger=mock_logger)
    mock_uow.session.execute = AsyncMock(side_effect=Exception("DB error"))

    result = await service.get_top_products()

    assert result.status_code == 500
    assert result.error is not None


# ==================== get_products_summary Tests ====================


@pytest.mark.asyncio
async def test_get_products_summary_success(mock_uow, mock_logger):
    """Test getting products summary."""
    service = ProductAnalyticsService(uow=mock_uow, logger=mock_logger)

    product_row = _make_row(nombre="Pizza Grande", cantidad=200)
    offer_row = _make_row(nombre="Combo Familiar", cantidad=50)

    call_count = 0
    async def _side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            # First two calls: most sold product queries
            return _mock_result([product_row])
        else:
            # Later calls: most sold offer queries
            return _mock_result([offer_row])

    mock_uow.session.execute = AsyncMock(side_effect=_side_effect)

    result = await service.get_products_summary()

    assert result.status_code == 200


@pytest.mark.asyncio
async def test_get_products_summary_does_not_fall_back_to_historical_sales(mock_uow, mock_logger):
    service = ProductAnalyticsService(uow=mock_uow, logger=mock_logger)
    start_date = datetime(2026, 10, 1)
    get_product = AsyncMock(return_value=None)
    get_offer = AsyncMock(return_value={"nombre": "Combo", "cantidad": 2})

    with patch.object(service, "_get_start_date_for_time_filter", return_value=start_date):
        with patch.object(service, "_get_most_sold_product", new=get_product):
            with patch.object(service, "_get_most_sold_offer", new=get_offer):
                result = await service.get_products_summary(time_filter="last_month")

    assert result.status_code == 200
    assert result.value["producto_mas_vendido"] == "Sin datos"
    assert result.value["cantidad_mas_vendida"] == 0
    assert result.value["promocion_mas_vendida"] == "Combo"
    assert result.value["cantidad_promocion"] == 2
    get_product.assert_awaited_once_with(start_date)
    get_offer.assert_awaited_once_with(start_date)


@pytest.mark.asyncio
async def test_get_products_summary_error(mock_uow, mock_logger):
    """Test products summary error handling."""
    service = ProductAnalyticsService(uow=mock_uow, logger=mock_logger)
    mock_uow.session.execute = AsyncMock(side_effect=Exception("DB error"))

    result = await service.get_products_summary()

    assert result.status_code == 500
