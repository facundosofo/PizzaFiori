"""
Tests for ProductAnalyticsService.
Tests product analytics operations with mocked session and UnitOfWork.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

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
async def test_get_products_summary_error(mock_uow, mock_logger):
    """Test products summary error handling."""
    service = ProductAnalyticsService(uow=mock_uow, logger=mock_logger)
    mock_uow.session.execute = AsyncMock(side_effect=Exception("DB error"))

    result = await service.get_products_summary()

    assert result.status_code == 500
