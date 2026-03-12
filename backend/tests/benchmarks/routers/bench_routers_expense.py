"""
bench_routers_expense.py — Benchmarks HTTP del router de gastos
"""

import pytest


def bench_router_get_gastos(benchmark, bench_client, run_async):
    """GET /gastos — listar gastos."""
    async def call():
        return await bench_client.get("/gastos")
    benchmark(run_async, call)


def bench_router_get_gastos_filtro_fecha(benchmark, bench_client, run_async):
    """GET /gastos?fecha_desde=&fecha_hasta="""
    async def call():
        return await bench_client.get("/gastos", params={
            "fecha_desde": "2026-01-01",
            "fecha_hasta": "2026-03-11",
        })
    benchmark(run_async, call)


def bench_router_get_gasto_by_id(benchmark, bench_client, run_async):
    """GET /gastos/{id}"""
    async def call():
        return await bench_client.get("/gastos/1")
    benchmark(run_async, call)


def bench_router_post_gasto(benchmark, bench_client, run_async):
    """POST /gastos — crear gasto."""
    async def call():
        return await bench_client.post("/gastos", json={
            "categoria_gasto_id": 1,
            "descripcion": "Compra de harina",
            "monto": 5000.0,
            "fecha_pago": "2026-03-11",
        })
    benchmark(run_async, call)


def bench_router_put_gasto(benchmark, bench_client, run_async):
    """PUT /gastos/{id} — actualizar gasto."""
    async def call():
        return await bench_client.put("/gastos/1", json={
            "monto": 5500.0,
            "descripcion": "Harina + levadura",
        })
    benchmark(run_async, call)


def bench_router_delete_gasto(benchmark, bench_client, run_async):
    """DELETE /gastos/{id}"""
    async def call():
        return await bench_client.delete("/gastos/1")
    benchmark(run_async, call)
