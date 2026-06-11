"""
Tests for SalesAnalyticsService.
Tests sales analytics operations with mocked session and UnitOfWork.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, date

from app.application.sales_analytics_service import SalesAnalyticsService


def _make_row(**kwargs):
    """Create a mock row with attribute and index access."""
    row = MagicMock()
    for k, v in kwargs.items():
        setattr(row, k, v)
    row._mapping = kwargs
    return row


def _mock_scalars_result(rows):
    """Create a mock for session.execute().scalars().all()."""
    result = MagicMock()
    result.scalars.return_value.all.return_value = rows
    return result


def _mock_result(rows):
    """Create a mock for session.execute() that returns rows."""
    result = MagicMock()
    result.fetchall.return_value = rows
    result.all.return_value = rows
    result.__iter__ = lambda self: iter(rows)
    return result


def _mock_scalar_result(value):
    """Create a mock for session.execute().scalar()."""
    result = MagicMock()
    result.scalar.return_value = value
    return result


# ==================== get_revenue_by_period Tests ====================


@pytest.mark.asyncio
async def test_get_revenue_daily_success(mock_uow, mock_logger):
    """Test getting daily revenue."""
    service = SalesAnalyticsService(uow=mock_uow, logger=mock_logger)

    rows = [
        _make_row(fecha=date(2024, 1, 1), ingresos=1500.0, pedidos=10, cantidad=25),
        _make_row(fecha=date(2024, 1, 2), ingresos=2000.0, pedidos=15, cantidad=30),
    ]
    mock_uow.session.execute = AsyncMock(return_value=_mock_result(rows))

    result = await service.get_revenue_by_period(period="daily", limit=30)

    assert result.status_code == 200
    assert result.value is not None


@pytest.mark.asyncio
async def test_get_revenue_monthly_success(mock_uow, mock_logger):
    """Test getting monthly revenue."""
    service = SalesAnalyticsService(uow=mock_uow, logger=mock_logger)

    rows = [
        _make_row(año=2024, mes=1, ingresos=45000.0, pedidos=300, cantidad=750),
    ]
    mock_uow.session.execute = AsyncMock(return_value=_mock_result(rows))

    result = await service.get_revenue_by_period(period="monthly", limit=12)

    assert result.status_code == 200


@pytest.mark.asyncio
async def test_get_revenue_weekly_success(mock_uow, mock_logger):
    """Test getting weekly revenue."""
    service = SalesAnalyticsService(uow=mock_uow, logger=mock_logger)

    rows = [
        _make_row(iso_year=2026, iso_week=6, ingresos=75000.0, pedidos=200, cantidad=450),
    ]
    mock_uow.session.execute = AsyncMock(return_value=_mock_result(rows))

    result = await service.get_revenue_by_period(period="weekly", limit=12)

    assert result.status_code == 200
    assert result.value is not None
    assert result.value[0]["semana"] is not None


@pytest.mark.asyncio
async def test_get_revenue_error(mock_uow, mock_logger):
    """Test revenue query error handling."""
    service = SalesAnalyticsService(uow=mock_uow, logger=mock_logger)
    mock_uow.session.execute = AsyncMock(side_effect=Exception("DB fail"))

    result = await service.get_revenue_by_period(period="daily")

    assert result.status_code == 500
    assert result.error is not None


# ==================== get_sales_by_category Tests ====================


@pytest.mark.asyncio
async def test_get_sales_by_category_success(mock_uow, mock_logger):
    """Test getting sales grouped by category."""
    service = SalesAnalyticsService(uow=mock_uow, logger=mock_logger)

    rows = [
        _make_row(categoria="Pizzas", cantidad=100),
        _make_row(categoria="Empanadas", cantidad=50),
    ]
    mock_uow.session.execute = AsyncMock(return_value=_mock_result(rows))

    result = await service.get_sales_by_category(limit=10)

    assert result.status_code == 200


@pytest.mark.asyncio
async def test_get_sales_by_category_error(mock_uow, mock_logger):
    """Test sales by category error handling."""
    service = SalesAnalyticsService(uow=mock_uow, logger=mock_logger)
    mock_uow.session.execute = AsyncMock(side_effect=Exception("DB error"))

    result = await service.get_sales_by_category()

    assert result.status_code == 500


# ==================== get_total_sales_with_comparison Tests ====================


@pytest.mark.asyncio
async def test_get_total_sales_comparison_success(mock_uow, mock_logger):
    """Test total sales with MTD comparison."""
    service = SalesAnalyticsService(uow=mock_uow, logger=mock_logger)

    mock_uow.session.execute = AsyncMock(
        return_value=_mock_scalar_result(50000.0)
    )

    result = await service.get_total_sales_with_comparison(days_in_period=30)

    assert result.status_code == 200
    assert result.value is not None


@pytest.mark.asyncio
async def test_get_total_sales_comparison_error(mock_uow, mock_logger):
    """Test total sales comparison error handling."""
    service = SalesAnalyticsService(uow=mock_uow, logger=mock_logger)
    mock_uow.session.execute = AsyncMock(side_effect=Exception("DB fail"))

    result = await service.get_total_sales_with_comparison()

    assert result.status_code == 500


# ==================== get_weekday_revenue Tests ====================


@pytest.mark.asyncio
async def test_get_weekday_revenue_success(mock_uow, mock_logger):
    """Test getting revenue by day of week."""
    service = SalesAnalyticsService(uow=mock_uow, logger=mock_logger)

    rows = [
        _make_row(business_date=date(2024, 1, 1), daily_total=1500.0, daily_orders=10, daily_quantity=25),
    ]
    mock_uow.session.execute = AsyncMock(return_value=_mock_result(rows))

    result = await service.get_weekday_revenue()

    assert result.status_code == 200


@pytest.mark.asyncio
async def test_get_weekday_revenue_error(mock_uow, mock_logger):
    """Test weekday revenue error handling."""
    service = SalesAnalyticsService(uow=mock_uow, logger=mock_logger)
    mock_uow.session.execute = AsyncMock(side_effect=Exception("DB fail"))

    result = await service.get_weekday_revenue()

    assert result.status_code == 500
