"""
bench_routers_dashboard.py — Benchmarks HTTP del router de dashboard

Todos los endpoints de analytics están mockeados — miden solo el overhead
de routing, deserialización de query params y serialización de respuesta.
"""

import pytest


# ══════════════════════════════════════════════════════════════════════════════
# Ventas / Ingresos
# ══════════════════════════════════════════════════════════════════════════════

def bench_router_get_revenue_diario(benchmark, bench_client, run_async):
    """GET /dashboard/revenue?period=DIARIO"""
    async def call():
        return await bench_client.get("/dashboard/revenue", params={"period": "DIARIO"})
    benchmark(run_async, call)


def bench_router_get_revenue_mensual(benchmark, bench_client, run_async):
    """GET /dashboard/revenue?period=MENSUAL"""
    async def call():
        return await bench_client.get("/dashboard/revenue", params={"period": "MENSUAL"})
    benchmark(run_async, call)


def bench_router_get_revenue_anual(benchmark, bench_client, run_async):
    """GET /dashboard/revenue?period=ANUAL"""
    async def call():
        return await bench_client.get("/dashboard/revenue", params={"period": "ANUAL"})
    benchmark(run_async, call)


def bench_router_get_weekday_revenue(benchmark, bench_client, run_async):
    """GET /dashboard/revenue/weekday"""
    async def call():
        return await bench_client.get("/dashboard/revenue/weekday")
    benchmark(run_async, call)


def bench_router_get_total_ventas(benchmark, bench_client, run_async):
    """GET /dashboard/sales/total"""
    async def call():
        return await bench_client.get("/dashboard/sales/total")
    benchmark(run_async, call)


def bench_router_get_ventas_by_category(benchmark, bench_client, run_async):
    """GET /dashboard/sales-by-category"""
    async def call():
        return await bench_client.get("/dashboard/sales-by-category")
    benchmark(run_async, call)


# ══════════════════════════════════════════════════════════════════════════════
# Productos
# ══════════════════════════════════════════════════════════════════════════════

def bench_router_get_top_products(benchmark, bench_client, run_async):
    """GET /dashboard/products/top"""
    async def call():
        return await bench_client.get("/dashboard/products/top", params={"limit": 10})
    benchmark(run_async, call)


def bench_router_get_products_summary(benchmark, bench_client, run_async):
    """GET /dashboard/products/summary"""
    async def call():
        return await bench_client.get("/dashboard/products/summary")
    benchmark(run_async, call)


# ══════════════════════════════════════════════════════════════════════════════
# Gastos
# ══════════════════════════════════════════════════════════════════════════════

def bench_router_get_expenses_mensual(benchmark, bench_client, run_async):
    """GET /dashboard/expenses?period=MENSUAL"""
    async def call():
        return await bench_client.get("/dashboard/expenses", params={"period": "MENSUAL"})
    benchmark(run_async, call)


def bench_router_get_expenses_summary(benchmark, bench_client, run_async):
    """GET /dashboard/expenses/summary"""
    async def call():
        return await bench_client.get("/dashboard/expenses/summary")
    benchmark(run_async, call)


def bench_router_get_expenses_monthly(benchmark, bench_client, run_async):
    """GET /dashboard/expenses/monthly"""
    async def call():
        return await bench_client.get("/dashboard/expenses/monthly")
    benchmark(run_async, call)


def bench_router_get_expenses_by_category(benchmark, bench_client, run_async):
    """GET /dashboard/expenses/by-category"""
    async def call():
        return await bench_client.get("/dashboard/expenses/by-category")
    benchmark(run_async, call)


def bench_router_get_total_expenses(benchmark, bench_client, run_async):
    """GET /dashboard/expenses/total"""
    async def call():
        return await bench_client.get("/dashboard/expenses/total")
    benchmark(run_async, call)


# ══════════════════════════════════════════════════════════════════════════════
# Balance
# ══════════════════════════════════════════════════════════════════════════════

def bench_router_get_balance(benchmark, bench_client, run_async):
    """GET /dashboard/balance"""
    async def call():
        return await bench_client.get("/dashboard/balance")
    benchmark(run_async, call)


def bench_router_get_monthly_balance(benchmark, bench_client, run_async):
    """GET /dashboard/balance/monthly"""
    async def call():
        return await bench_client.get("/dashboard/balance/monthly")
    benchmark(run_async, call)
