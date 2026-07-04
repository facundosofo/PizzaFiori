"""
Tests for ExpenseAnalyticsService.
Tests expense analytics operations with mocked session and UnitOfWork.
"""

import pytest
from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock, patch

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
async def test_get_expenses_by_period_daily(mock_uow, mock_logger):
    """Test getting daily expense periods."""
    service = ExpenseAnalyticsService(uow=mock_uow, logger=mock_logger)

    rows = [
        _make_row(fecha=date(2026, 6, 1), total_gastos=4200.0),
        _make_row(fecha=date(2026, 6, 2), total_gastos=3800.0),
    ]
    mock_uow.session.execute = AsyncMock(return_value=_mock_result(rows))

    fixed_now = datetime(2026, 6, 15, 12, 0, 0)
    with patch("app.application.expense_analytics_service.datetime") as mock_datetime:
        mock_datetime.now.return_value = fixed_now
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

        result = await service.get_expenses_by_period(period="daily", limit=15)

    assert result.status_code == 200
    assert len(result.value) == 15
    assert {"fecha": "2026-06-01", "gastos": 4200.0} in result.value
    assert {"fecha": "2026-06-02", "gastos": 3800.0} in result.value


@pytest.mark.asyncio
async def test_get_expenses_by_period_weekly(mock_uow, mock_logger):
    """Test getting weekly expense periods."""
    service = ExpenseAnalyticsService(uow=mock_uow, logger=mock_logger)

    rows = [
        _make_row(iso_year=2026, iso_week=22, total_gastos=25000.0),
        _make_row(iso_year=2026, iso_week=23, total_gastos=27000.0),
    ]
    mock_uow.session.execute = AsyncMock(return_value=_mock_result(rows))

    result = await service.get_expenses_by_period(period="weekly", limit=12)

    assert result.status_code == 200
    assert len(result.value) == 12
    assert any(item["gastos"] == 25000.0 for item in result.value)
    assert any(item["gastos"] == 27000.0 for item in result.value)


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
