"""
Tests for ExpenseAnalyticsService.
Tests expense analytics operations with mocked session and UnitOfWork.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.application.expense_analytics_service import ExpenseAnalyticsService


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


# ==================== get_expenses_by_period Tests ====================


@pytest.mark.asyncio
async def test_get_expenses_by_period_monthly(mock_uow, mock_logger):
    """Test getting monthly expense periods."""
    service = ExpenseAnalyticsService(uow=mock_uow, logger=mock_logger)

    rows = [
        _make_row(año=2024, mes=1, gastos=50000.0),
        _make_row(año=2024, mes=2, gastos=45000.0),
    ]
    mock_uow.session.execute = AsyncMock(return_value=_mock_result(rows))

    result = await service.get_expenses_by_period(period="monthly", limit=12)

    assert result.status_code == 200


@pytest.mark.asyncio
async def test_get_expenses_by_period_yearly(mock_uow, mock_logger):
    """Test getting yearly expense periods."""
    service = ExpenseAnalyticsService(uow=mock_uow, logger=mock_logger)

    rows = [_make_row(año=2024, gastos=600000.0)]
    mock_uow.session.execute = AsyncMock(return_value=_mock_result(rows))

    result = await service.get_expenses_by_period(period="yearly", limit=5)

    assert result.status_code == 200


@pytest.mark.asyncio
async def test_get_expenses_by_period_error(mock_uow, mock_logger):
    """Test expense period error handling."""
    service = ExpenseAnalyticsService(uow=mock_uow, logger=mock_logger)
    mock_uow.session.execute = AsyncMock(side_effect=Exception("DB error"))

    result = await service.get_expenses_by_period(period="monthly")

    assert result.status_code == 500


# ==================== get_expenses_by_category Tests ====================


@pytest.mark.asyncio
async def test_get_expenses_by_category_success(mock_uow, mock_logger):
    """Test getting expenses by category."""
    service = ExpenseAnalyticsService(uow=mock_uow, logger=mock_logger)

    rows = [
        _make_row(categoria="Insumos", gastos=30000.0),
        _make_row(categoria="Servicios", gastos=20000.0),
    ]
    mock_uow.session.execute = AsyncMock(return_value=_mock_result(rows))

    result = await service.get_expenses_by_category(limit=8)

    assert result.status_code == 200


@pytest.mark.asyncio
async def test_get_expenses_by_category_error(mock_uow, mock_logger):
    """Test expenses by category error handling."""
    service = ExpenseAnalyticsService(uow=mock_uow, logger=mock_logger)
    mock_uow.session.execute = AsyncMock(side_effect=Exception("DB error"))

    result = await service.get_expenses_by_category()

    assert result.status_code == 500


# ==================== get_expenses_summary Tests ====================


@pytest.mark.asyncio
async def test_get_expenses_summary_success(mock_uow, mock_logger):
    """Test getting expense summary with comparisons."""
    service = ExpenseAnalyticsService(uow=mock_uow, logger=mock_logger)

    # Mock multiple execute calls for MTD, previous month, YTD, etc.
    mock_uow.session.execute = AsyncMock(
        return_value=_mock_scalar_result(50000.0)
    )

    result = await service.get_expenses_summary()

    assert result.status_code == 200
    assert result.value is not None


@pytest.mark.asyncio
async def test_get_expenses_summary_error(mock_uow, mock_logger):
    """Test expense summary error handling."""
    service = ExpenseAnalyticsService(uow=mock_uow, logger=mock_logger)
    mock_uow.session.execute = AsyncMock(side_effect=Exception("DB error"))

    result = await service.get_expenses_summary()

    assert result.status_code == 500


# ==================== get_total_expenses_with_comparison Tests ====================


@pytest.mark.asyncio
async def test_get_total_expenses_comparison_success(mock_uow, mock_logger):
    """Test total expenses with MTD comparison."""
    service = ExpenseAnalyticsService(uow=mock_uow, logger=mock_logger)

    mock_uow.session.execute = AsyncMock(
        return_value=_mock_scalar_result(25000.0)
    )

    result = await service.get_total_expenses_with_comparison(days_in_period=30)

    assert result.status_code == 200
    assert result.value is not None


@pytest.mark.asyncio
async def test_get_total_expenses_comparison_error(mock_uow, mock_logger):
    """Test total expenses comparison error handling."""
    service = ExpenseAnalyticsService(uow=mock_uow, logger=mock_logger)
    mock_uow.session.execute = AsyncMock(side_effect=Exception("DB fail"))

    result = await service.get_total_expenses_with_comparison()

    assert result.status_code == 500


# ==================== get_expenses_by_month Tests ====================


@pytest.mark.asyncio
async def test_get_expenses_by_month_success(mock_uow, mock_logger):
    """Test getting monthly expenses."""
    service = ExpenseAnalyticsService(uow=mock_uow, logger=mock_logger)

    rows = [
        _make_row(año=2024, mes=6, gastos=40000.0),
    ]
    mock_uow.session.execute = AsyncMock(return_value=_mock_result(rows))

    result = await service.get_expenses_by_month(limit=12)

    assert result.status_code == 200
