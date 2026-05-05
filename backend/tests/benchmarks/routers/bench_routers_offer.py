"""
bench_routers_offer.py — Benchmarks HTTP del router de ofertas
"""

import pytest


def bench_router_get_ofertas(benchmark, bench_client, run_async):
    """GET /ofertas — listar ofertas."""
    async def call():
        return await bench_client.get("/ofertas")
    benchmark(run_async, call)


def bench_router_get_ofertas_activas(benchmark, bench_client, run_async):
    """GET /ofertas?active=true"""
    async def call():
        return await bench_client.get("/ofertas", params={"active": True})
    benchmark(run_async, call)


def bench_router_get_oferta_by_id(benchmark, bench_client, run_async):
    """GET /ofertas/{id}"""
    async def call():
        return await bench_client.get("/ofertas/1")
    benchmark(run_async, call)


def bench_router_post_oferta_categoria(benchmark, bench_client, run_async):
    """POST /ofertas — por categoría."""
    async def call():
        return await bench_client.post("/ofertas", json={
            "nombre": "Docena Mixta",
            "precio": "12000",
            "productos": [{"categoria_id": 1, "cantidad": 12}],
        })
    benchmark(run_async, call)


def bench_router_post_oferta_opciones(benchmark, bench_client, run_async):
    """POST /ofertas — por lista de opciones."""
    async def call():
        return await bench_client.post("/ofertas", json={
            "nombre": "Combo Variado",
            "precio": "10000",
            "productos": [{"producto_opciones": [1, 2, 3], "cantidad": 6}],
        })
    benchmark(run_async, call)


def bench_router_put_oferta(benchmark, bench_client, run_async):
    """PUT /ofertas/{id} — actualizar precio."""
    async def call():
        return await bench_client.put("/ofertas/1", json={"precio": "13000"})
    benchmark(run_async, call)


def bench_router_patch_desactivar_oferta(benchmark, bench_client, run_async):
    """PATCH /ofertas/{id}/desactivar"""
    async def call():
        return await bench_client.patch("/ofertas/1/desactivar")
    benchmark(run_async, call)
