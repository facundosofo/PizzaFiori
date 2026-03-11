"""
bench_routers_product.py — Benchmarks HTTP del router de productos
"""

import pytest


# ══════════════════════════════════════════════════════════════════════════════
# GET
# ══════════════════════════════════════════════════════════════════════════════

def bench_router_get_productos(benchmark, bench_client, run_async):
    """GET /productos — listar todos."""
    async def call():
        return await bench_client.get("/productos")
    benchmark(run_async, call)


def bench_router_get_productos_por_categoria(benchmark, bench_client, run_async):
    """GET /productos?categoria_id=1"""
    async def call():
        return await bench_client.get("/productos", params={"categoria_id": 1})
    benchmark(run_async, call)


def bench_router_get_producto_by_id(benchmark, bench_client, run_async):
    """GET /productos/{id}"""
    async def call():
        return await bench_client.get("/productos/1")
    benchmark(run_async, call)


# ══════════════════════════════════════════════════════════════════════════════
# POST / PATCH
# ══════════════════════════════════════════════════════════════════════════════

def bench_router_post_producto(benchmark, bench_client, run_async):
    """POST /productos — crear producto (multipart form, sin imagen)."""
    import json
    form_data = {
        "nombre": "Empanada de Carne",
        "categoria_id": "1",
        "precios": json.dumps([
            {"cantidad": 1, "precio": "1200"},
            {"cantidad": 6, "precio": "6000"},
        ]),
    }
    async def call():
        return await bench_client.post("/productos", data=form_data)
    benchmark(run_async, call)


def bench_router_patch_bulk_update_prices_monto(benchmark, bench_client, run_async):
    """PATCH /productos/actualizar-precios — incremento por monto fijo."""
    async def call():
        return await bench_client.patch(
            "/productos/actualizar-precios",
            json={"monto": "100"},
        )
    benchmark(run_async, call)


def bench_router_patch_bulk_update_prices_porcentaje(benchmark, bench_client, run_async):
    """PATCH /productos/actualizar-precios — incremento por porcentaje."""
    async def call():
        return await bench_client.patch(
            "/productos/actualizar-precios",
            json={"porcentaje": "10", "categoria_ids": [1, 2]},
        )
    benchmark(run_async, call)


# ══════════════════════════════════════════════════════════════════════════════
# PUT / PATCH (individual)
# ══════════════════════════════════════════════════════════════════════════════

def bench_router_put_producto(benchmark, bench_client, run_async):
    """PUT /productos/{id} — actualizar producto (multipart form)."""
    import json
    form_data = {
        "nombre": "Empanada Criolla",
        "precios": json.dumps([{"id": 1, "cantidad": 1, "precio": "1300"}]),
    }
    async def call():
        return await bench_client.put("/productos/1", data=form_data)
    benchmark(run_async, call)


def bench_router_patch_desactivar_producto(benchmark, bench_client, run_async):
    """PATCH /productos/{id}/desactivar"""
    async def call():
        return await bench_client.patch("/productos/1/desactivar")
    benchmark(run_async, call)
