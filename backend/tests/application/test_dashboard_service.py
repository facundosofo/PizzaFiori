"""
Tests for DashboardService.
Focus on orchestration, time filtering, and response mapping.
"""

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.application.dashboard_service import DashboardService
from app.presentation.schemas.dashboard_schemas import FiltroTiempo, TipoPeriodo


class DummyResult:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return self._rows


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "period, method_name",
    [
        (TipoPeriodo.DIARIO, "_get_daily_revenue"),
        (TipoPeriodo.MENSUAL, "_get_monthly_revenue"),
        (TipoPeriodo.ANUAL, "_get_yearly_revenue"),
    ],
)
async def test_get_revenue_by_period_dispatches(mock_uow, mock_logger, period, method_name):
    service = DashboardService(uow=mock_uow, logger=mock_logger)
    expected = [{"ingresos": 100.0}]

    with patch.object(service, method_name, new=AsyncMock(return_value=expected)) as mock_method:
        result = await service.get_revenue_by_period(period=period, limit=5)

    assert result.value == expected
    assert result.error is None
    mock_method.assert_called_once_with(5)


@pytest.mark.asyncio
async def test_get_revenue_by_period_handles_exception(mock_uow, mock_logger):
    service = DashboardService(uow=mock_uow, logger=mock_logger)

    with patch.object(service, "_get_daily_revenue", new=AsyncMock(side_effect=Exception("boom"))):
        result = await service.get_revenue_by_period(period=TipoPeriodo.DIARIO, limit=5)

    assert result.value is None
    assert result.error is not None
    assert result.status_code == 500


def test_get_start_date_for_time_filter(mock_uow, mock_logger):
    service = DashboardService(uow=mock_uow, logger=mock_logger)
    fixed_now = datetime(2026, 2, 10, 15, 30, 0)

    # Patch in analytics_utils where datetime.now() is actually called
    with patch("app.application.analytics_utils.datetime") as mock_datetime:
        mock_datetime.now.return_value = fixed_now

        start_today = service._get_start_date_for_time_filter(FiltroTiempo.HOY)
        start_7_days = service._get_start_date_for_time_filter(FiltroTiempo.ULTIMOS_7_DIAS)
        start_month = service._get_start_date_for_time_filter(FiltroTiempo.ULTIMO_MES)
        start_year = service._get_start_date_for_time_filter(FiltroTiempo.ULTIMO_ANO)
        start_all = service._get_start_date_for_time_filter(FiltroTiempo.HISTORICO)

    # Calendar-anchored periods (not rolling):
    assert start_today == datetime(2026, 2, 10, 0, 0, 0)          # hoy a las 00:00
    assert start_7_days == datetime(2026, 2, 4, 0, 0, 0)           # hace 6 días a las 00:00
    assert start_month == datetime(2026, 2, 1, 0, 0, 0)            # 1° del mes actual
    assert start_year == datetime(2026, 1, 1, 0, 0, 0)             # 1° de enero del año actual
    assert start_all is None


@pytest.mark.asyncio
async def test_get_top_products_uses_time_filter(mock_uow, mock_logger):
    service = DashboardService(uow=mock_uow, logger=mock_logger)
    expected = [{"nombre": "Muzzarella"}]
    fake_start = datetime(2026, 2, 1, 0, 0, 0)

    with patch.object(service, "_get_start_date_for_time_filter", return_value=fake_start) as mock_start:
        with patch.object(service, "_get_top_products_data", new=AsyncMock(return_value=expected)) as mock_data:
            result = await service.get_top_products(
                limit=3,
                time_filter=FiltroTiempo.ULTIMOS_7_DIAS,
                sort="top",
                category="Pizzas",
            )

    assert result.value == expected
    mock_start.assert_called_once_with(FiltroTiempo.ULTIMOS_7_DIAS)
    mock_data.assert_called_once_with(3, fake_start, sort="top", category="Pizzas")


@pytest.mark.asyncio
async def test_get_sales_by_category_uses_time_filter(mock_uow, mock_logger):
    service = DashboardService(uow=mock_uow, logger=mock_logger)
    expected = [{"categoria": "Pizzas", "cantidad": 10}]
    fake_start = datetime(2026, 2, 1, 0, 0, 0)

    with patch.object(service, "_get_start_date_for_time_filter", return_value=fake_start) as mock_start:
        with patch.object(service, "_get_sales_by_category_data", new=AsyncMock(return_value=expected)) as mock_data:
            result = await service.get_sales_by_category(limit=5, time_filter=FiltroTiempo.ULTIMO_MES)

    assert result.value == expected
    mock_start.assert_called_once_with(FiltroTiempo.ULTIMO_MES)
    mock_data.assert_called_once_with(5, fake_start)


@pytest.mark.asyncio
async def test_get_weekday_revenue_calls_data(mock_uow, mock_logger):
    service = DashboardService(uow=mock_uow, logger=mock_logger)
    expected = [{"dia_semana": "Lunes"}]

    with patch.object(service, "_get_weekday_revenue_data", new=AsyncMock(return_value=expected)) as mock_data:
        result = await service.get_weekday_revenue(category="Pizzas")

    assert result.value == expected
    mock_data.assert_called_once_with(None, None, "Pizzas")


@pytest.mark.asyncio
async def test_get_top_products_data_maps_rows(mock_uow, mock_logger):
    service = DashboardService(uow=mock_uow, logger=mock_logger)
    rows = [
        SimpleNamespace(name="Muzzarella", category="Pizzas", total_quantity=5, price=1200.0),
    ]

    mock_uow.session = AsyncMock()
    mock_uow.session.execute = AsyncMock(return_value=DummyResult(rows))

    result = await service._get_top_products_data(limit=10, start_date=None, sort="top", category=None)

    assert result == [
        {
            "nombre": "Muzzarella",
            "categoria": "Pizzas",
            "cantidad": 5,
            "precio": 1200.0,
            "enStock": True,
        }
    ]


@pytest.mark.asyncio
async def test_get_sales_by_category_data_maps_rows(mock_uow, mock_logger):
    service = DashboardService(uow=mock_uow, logger=mock_logger)
    rows = [
        SimpleNamespace(category="Pizzas", total_quantity=12),
    ]

    mock_uow.session = AsyncMock()
    mock_uow.session.execute = AsyncMock(return_value=DummyResult(rows))

    result = await service._get_sales_by_category_data(limit=None, start_date=None)

    assert result == [
        {
            "categoria": "Pizzas",
            "cantidad": 12,
        }
    ]


@pytest.mark.asyncio
async def test_get_weekday_revenue_data_orders_and_defaults(mock_uow, mock_logger):
    service = DashboardService(uow=mock_uow, logger=mock_logger)
    rows = [
        SimpleNamespace(dow=2, promedio_ingresos=100.0, promedio_pedidos=2.0, promedio_cantidad=10.0),
        SimpleNamespace(dow=4, promedio_ingresos=300.0, promedio_pedidos=3.0, promedio_cantidad=30.0),
    ]

    mock_uow.session = AsyncMock()
    mock_uow.session.execute = AsyncMock(return_value=DummyResult(rows))

    result = await service._get_weekday_revenue_data(start_date=None, end_date=None, category=None)

    assert len(result) == 7
    assert result[0]["dia_semana"] == "Lunes"
    assert result[-1]["dia_semana"] == "Domingo"
    assert result[0]["promedio_ingresos"] == 100.0

    with_value = [
        item
        for item in result
        if item["promedio_ingresos"] == 300.0 and item["promedio_pedidos"] == 3.0
    ]
    assert len(with_value) == 1
    assert result[-1]["promedio_ingresos"] == 0.0
