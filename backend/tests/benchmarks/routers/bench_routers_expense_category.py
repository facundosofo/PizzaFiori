"""
bench_routers_expense_category.py — Benchmarks HTTP del router de categorías de gastos
"""

import pytest


def bench_router_get_gastos_categorias(benchmark, bench_client, run_async):
    """GET /gastos-categorias — listar."""
    async def call():
        return await bench_client.get("/gastos-categorias")
    benchmark(run_async, call)


def bench_router_get_gasto_categoria_by_id(benchmark, bench_client, run_async):
    """GET /gastos-categorias/{id}"""
    async def call():
        return await bench_client.get("/gastos-categorias/1")
    benchmark(run_async, call)


def bench_router_post_gasto_categoria_raiz(benchmark, bench_client, run_async):
    """POST /gastos-categorias — categoría raíz."""
    async def call():
        return await bench_client.post("/gastos-categorias", json={"nombre": "Ingredientes"})
    benchmark(run_async, call)


def bench_router_post_gasto_categoria_sub(benchmark, bench_client, run_async):
    """POST /gastos-categorias — subcategoría con padre_id."""
    async def call():
        return await bench_client.post("/gastos-categorias", json={
            "nombre": "Lácteos",
            "padre_id": 1,
        })
    benchmark(run_async, call)


def bench_router_put_gasto_categoria(benchmark, bench_client, run_async):
    """PUT /gastos-categorias/{id}"""
    async def call():
        return await bench_client.put("/gastos-categorias/1", json={"nombre": "Ingredientes Base"})
    benchmark(run_async, call)


def bench_router_patch_desactivar_gasto_categoria(benchmark, bench_client, run_async):
    """PATCH /gastos-categorias/{id}/desactivar"""
    async def call():
        return await bench_client.patch("/gastos-categorias/1/desactivar")
    benchmark(run_async, call)
