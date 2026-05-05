"""
bench_services_analytics.py — Benchmarks de los tres servicios de analytics

SalesAnalyticsService, ProductAnalyticsService, ExpenseAnalyticsService
se apoyan directamente en uow.session.execute(query) + result.fetchall().
Mock: uow.session.execute = AsyncMock(return_value=<mock_result>)
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.application.sales_analytics_service import SalesAnalyticsService
from app.application.product_analytics_service import ProductAnalyticsService
from app.application.expense_analytics_service import ExpenseAnalyticsService
from app.presentation.schemas.dashboard_schemas import TipoPeriodo, FiltroTiempo


# ──────────────────────────────────────────────────────────────────────────────
# Helpers genéricos
# ──────────────────────────────────────────────────────────────────────────────

def _make_analytics_uow(rows=None):
    """UoW con session.execute que devuelve rows (lista de mock rows)."""
    uow = AsyncMock()
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock(return_value=None)
    uow.commit = AsyncMock()
    uow.rollback = AsyncMock()

    result = MagicMock()
    result.fetchall.return_value = rows or []
    result.first.return_value = (rows[0] if rows else None)
    result.fetchone.return_value = (rows[0] if rows else None)

    uow.session.execute = AsyncMock(return_value=result)

    return uow


def _make_daily_rows(n: int = 30):
    """Mock de N filas como devuelve _get_daily_revenue."""
    from datetime import date, timedelta
    rows = []
    base = date(2026, 1, 1)
    for i in range(n):
        r = MagicMock()
        r.date = base + timedelta(days=i)
        r.revenue = float(5000 + i * 100)
        r.pedidos = 5 + i
        r.cantidad = 30 + i
        rows.append(r)
    return rows


def _make_monthly_rows(n: int = 12):
    rows = []
    for i in range(n):
        r = MagicMock()
        r.year = 2025 + i // 12
        r.month = (i % 12) + 1
        r.revenue = float(50000 + i * 5000)
        r.pedidos = 50 + i * 5
        r.cantidad = 300 + i * 30
        rows.append(r)
    return rows


def _make_yearly_rows(n: int = 3):
    rows = []
    for i in range(n):
        r = MagicMock()
        r.year = 2024 + i
        r.revenue = float(500000 + i * 100000)
        r.pedidos = 500 + i * 100
        r.cantidad = 3000 + i * 500
        rows.append(r)
    return rows


def _make_category_rows(n: int = 8):
    rows = []
    cats = ["Empanadas", "Pizzas", "Bebidas", "Postres", "Combos", "Tartas", "Sopas", "Extras"]
    for i in range(n):
        r = MagicMock()
        r.category = cats[i % len(cats)]
        r.total_quantity = 100 + i * 10
        rows.append(r)
    return rows


def _make_weekday_rows():
    rows = []
    days = ["Dom", "Lun", "Mar", "Mié", "Jue", "Vie", "Sáb"]
    for i, d in enumerate(days, start=1):
        r = MagicMock()
        r.dow = i
        r.promedio_ingresos = float(3000 + i * 200)
        r.promedio_pedidos = float(30 + i * 2)
        r.promedio_cantidad = float(150 + i * 10)
        rows.append(r)
    return rows


def _make_product_rows(n: int = 10):
    rows = []
    for i in range(n):
        r = MagicMock()
        r.name = f"Producto {i+1}"
        r.category = "Empanadas"
        r.total_quantity = 100 - i * 5
        r.price = float(1200 + i * 50)
        rows.append(r)
    return rows


def _make_expense_monthly_rows(n: int = 12):
    rows = []
    for i in range(n):
        r = MagicMock()
        r.year = 2025 + i // 12
        r.month = (i % 12) + 1
        r.total_gastos = float(20000 + i * 2000)
        rows.append(r)
    return rows


def _make_expense_category_rows(n: int = 6):
    rows = []
    cats = ["Ingredientes", "Servicios", "Alquileres", "Personal", "Impuestos", "Varios"]
    for i in range(n):
        r = MagicMock()
        r.categoria = cats[i % len(cats)]
        r.total_gastos = float(10000 + i * 5000)
        rows.append(r)
    return rows


# ══════════════════════════════════════════════════════════════════════════════
# SalesAnalyticsService
# ══════════════════════════════════════════════════════════════════════════════

def bench_sales_revenue_daily_30(benchmark, run_async):
    """get_revenue_by_period DIARIO con 30 días."""
    uow = _make_analytics_uow(_make_daily_rows(30))
    svc = SalesAnalyticsService(uow=uow, logger=MagicMock())

    async def call():
        return await svc.get_revenue_by_period(TipoPeriodo.DIARIO, limit=30)

    benchmark(run_async, call)


def bench_sales_revenue_monthly_12(benchmark, run_async):
    """get_revenue_by_period MENSUAL con 12 meses."""
    uow = _make_analytics_uow(_make_monthly_rows(12))
    svc = SalesAnalyticsService(uow=uow, logger=MagicMock())

    async def call():
        return await svc.get_revenue_by_period(TipoPeriodo.MENSUAL, limit=12)

    benchmark(run_async, call)


def bench_sales_revenue_yearly(benchmark, run_async):
    """get_revenue_by_period ANUAL."""
    uow = _make_analytics_uow(_make_yearly_rows(3))
    svc = SalesAnalyticsService(uow=uow, logger=MagicMock())

    async def call():
        return await svc.get_revenue_by_period(TipoPeriodo.ANUAL, limit=5)

    benchmark(run_async, call)


def bench_sales_by_category_historico(benchmark, run_async):
    """get_sales_by_category con filtro HISTORICO."""
    uow = _make_analytics_uow(_make_category_rows(8))
    svc = SalesAnalyticsService(uow=uow, logger=MagicMock())

    async def call():
        return await svc.get_sales_by_category(time_filter=FiltroTiempo.HISTORICO)

    benchmark(run_async, call)


def bench_sales_weekday_revenue(benchmark, run_async):
    """get_weekday_revenue sin filtro de categoría."""
    uow = _make_analytics_uow(_make_weekday_rows())
    svc = SalesAnalyticsService(uow=uow, logger=MagicMock())

    async def call():
        return await svc.get_weekday_revenue()

    benchmark(run_async, call)


def bench_sales_total_comparison(benchmark, run_async):
    """get_total_sales_with_comparison (30 días)."""
    # Devuelve una fila con los totales del período actual y anterior
    r = MagicMock()
    r.current_total = 150000.0
    r.previous_total = 120000.0
    uow = _make_analytics_uow([r])
    svc = SalesAnalyticsService(uow=uow, logger=MagicMock())

    async def call():
        return await svc.get_total_sales_with_comparison(days_in_period=30)

    benchmark(run_async, call)


def bench_sales_revenue_empty_result(benchmark, run_async):
    """get_revenue_by_period con BD sin datos (array vacío)."""
    uow = _make_analytics_uow([])
    svc = SalesAnalyticsService(uow=uow, logger=MagicMock())

    async def call():
        return await svc.get_revenue_by_period(TipoPeriodo.DIARIO, limit=30)

    benchmark(run_async, call)


# ══════════════════════════════════════════════════════════════════════════════
# ProductAnalyticsService
# ══════════════════════════════════════════════════════════════════════════════

def bench_products_top_10(benchmark, run_async):
    """get_top_products top 10, HISTORICO."""
    uow = _make_analytics_uow(_make_product_rows(10))
    svc = ProductAnalyticsService(uow=uow, logger=MagicMock())

    async def call():
        return await svc.get_top_products(limit=10, time_filter=FiltroTiempo.HISTORICO)

    benchmark(run_async, call)


def bench_products_top_10_ultimo_mes(benchmark, run_async):
    """get_top_products top 10, ULTIMO_MES."""
    uow = _make_analytics_uow(_make_product_rows(10))
    svc = ProductAnalyticsService(uow=uow, logger=MagicMock())

    async def call():
        return await svc.get_top_products(limit=10, time_filter=FiltroTiempo.ULTIMO_MES)

    benchmark(run_async, call)


def bench_products_summary(benchmark, run_async):
    """get_products_summary — múltiples queries internas."""
    # Se llaman 3-4 queries internas: top product, category, offer, highest revenue
    rows = _make_product_rows(1)
    rows[0].total_revenue = 50000.0

    uow = _make_analytics_uow(rows)
    svc = ProductAnalyticsService(uow=uow, logger=MagicMock())

    async def call():
        return await svc.get_products_summary()

    benchmark(run_async, call)


def bench_products_summary_empty(benchmark, run_async):
    """get_products_summary sin datos."""
    uow = _make_analytics_uow([])
    svc = ProductAnalyticsService(uow=uow, logger=MagicMock())

    async def call():
        return await svc.get_products_summary()

    benchmark(run_async, call)


# ══════════════════════════════════════════════════════════════════════════════
# ExpenseAnalyticsService
# ══════════════════════════════════════════════════════════════════════════════

def bench_expenses_by_period_mensual(benchmark, run_async):
    """get_expenses_by_period MENSUAL."""
    uow = _make_analytics_uow(_make_expense_monthly_rows(12))
    svc = ExpenseAnalyticsService(uow=uow, logger=MagicMock())

    async def call():
        return await svc.get_expenses_by_period(TipoPeriodo.MENSUAL, limit=12)

    benchmark(run_async, call)


def bench_expenses_by_category(benchmark, run_async):
    """get_expenses_by_category ULTIMO_ANO."""
    uow = _make_analytics_uow(_make_expense_category_rows(6))
    svc = ExpenseAnalyticsService(uow=uow, logger=MagicMock())

    async def call():
        return await svc.get_expenses_by_category(
            limit=8, time_filter=FiltroTiempo.ULTIMO_ANO
        )

    benchmark(run_async, call)


def bench_expenses_summary(benchmark, run_async):
    """get_expenses_summary — KPIs MTD/YTD."""
    r_monthly = MagicMock()
    r_monthly.year = 2026
    r_monthly.month = 3
    r_monthly.total_gastos = 35000.0

    uow = _make_analytics_uow([r_monthly])
    svc = ExpenseAnalyticsService(uow=uow, logger=MagicMock())

    async def call():
        return await svc.get_expenses_summary()

    benchmark(run_async, call)


def bench_expenses_total_comparison(benchmark, run_async):
    """get_total_expenses_with_comparison."""
    r = MagicMock()
    r.current_total = 35000.0
    r.previous_total = 28000.0
    uow = _make_analytics_uow([r])
    svc = ExpenseAnalyticsService(uow=uow, logger=MagicMock())

    async def call():
        return await svc.get_total_expenses_with_comparison(days_in_period=30)

    benchmark(run_async, call)
