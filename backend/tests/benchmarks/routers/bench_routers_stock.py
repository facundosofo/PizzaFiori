"""
bench_routers_stock.py — Benchmarks HTTP del router de stock
"""

import pytest


def bench_router_get_stock(benchmark, bench_client, run_async):
    """GET /stock — estado de todas las categorías."""
    async def call():
        return await bench_client.get("/stock")
    benchmark(run_async, call)


def bench_router_post_add_stock(benchmark, bench_client, run_async):
    """POST /stock/{categoria_id}/agregar — ingreso."""
    async def call():
        return await bench_client.post("/stock/1/agregar", json={"cantidad": 50})
    benchmark(run_async, call)


def bench_router_post_ajuste_baja(benchmark, bench_client, run_async):
    """POST /stock/{categoria_id}/agregar — ajuste baja."""
    async def call():
        return await bench_client.post("/stock/1/agregar", json={"cantidad": -10})
    benchmark(run_async, call)


def bench_router_put_configure_alerts(benchmark, bench_client, run_async):
    """PUT /stock/{categoria_id}/alertas — configurar umbrales."""
    async def call():
        return await bench_client.put("/stock/1/alertas", json={
            "umbral_amarillo": 30,
            "umbral_rojo": 10,
        })
    benchmark(run_async, call)


def bench_router_get_movimientos(benchmark, bench_client, run_async):
    """GET /stock/{categoria_id}/movimientos"""
    async def call():
        return await bench_client.get("/stock/1/movimientos")
    benchmark(run_async, call)
