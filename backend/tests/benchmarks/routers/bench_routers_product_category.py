"""
bench_routers_product_category.py — Benchmarks HTTP del router de categorías de producto
"""

import pytest


def bench_router_get_categorias(benchmark, bench_client, run_async):
    """GET /productos-categorias"""
    async def call():
        return await bench_client.get("/productos-categorias")
    benchmark(run_async, call)


def bench_router_get_categoria_by_id(benchmark, bench_client, run_async):
    """GET /productos-categorias/{id}"""
    async def call():
        return await bench_client.get("/productos-categorias/1")
    benchmark(run_async, call)


def bench_router_post_categoria(benchmark, bench_client, run_async):
    """POST /productos-categorias"""
    async def call():
        return await bench_client.post("/productos-categorias", json={"nombre": "Pizzas"})
    benchmark(run_async, call)


def bench_router_put_categoria(benchmark, bench_client, run_async):
    """PUT /productos-categorias/{id}"""
    async def call():
        return await bench_client.put("/productos-categorias/1", json={"nombre": "Pizzas Artesanales"})
    benchmark(run_async, call)


def bench_router_patch_desactivar_categoria(benchmark, bench_client, run_async):
    """PATCH /productos-categorias/{id}/desactivar"""
    async def call():
        return await bench_client.patch("/productos-categorias/1/desactivar")
    benchmark(run_async, call)
