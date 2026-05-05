"""
bench_routers_sale.py — Benchmarks HTTP del router de ventas

Mide la latencia completa del ciclo HTTP:
    routing → deserialización → servicio mock → serialización → respuesta
"""

import json
import pytest
from httpx import AsyncClient


# ══════════════════════════════════════════════════════════════════════════════
# GET
# ══════════════════════════════════════════════════════════════════════════════

def bench_router_get_ventas(benchmark, bench_client, run_async):
    """GET /ventas — listar ventas sin filtros."""
    async def call():
        return await bench_client.get("/ventas")
    benchmark(run_async, call)


def bench_router_get_ventas_con_fecha(benchmark, bench_client, run_async):
    """GET /ventas?fecha_desde=2026-01-01&fecha_hasta=2026-03-11"""
    async def call():
        return await bench_client.get("/ventas", params={
            "fecha_desde": "2026-01-01",
            "fecha_hasta": "2026-03-11",
        })
    benchmark(run_async, call)


def bench_router_get_venta_by_id(benchmark, bench_client, run_async):
    """GET /ventas/{id}"""
    async def call():
        return await bench_client.get("/ventas/1")
    benchmark(run_async, call)


def bench_router_get_anios_disponibles(benchmark, bench_client, run_async):
    """GET /ventas/anios-disponibles"""
    async def call():
        return await bench_client.get("/ventas/anios-disponibles")
    benchmark(run_async, call)


# ══════════════════════════════════════════════════════════════════════════════
# POST
# ══════════════════════════════════════════════════════════════════════════════

def bench_router_post_venta_simple(benchmark, bench_client, run_async):
    """POST /ventas — venta con 1 item producto."""
    payload = {"items": [{"producto_id": 1, "cantidad": 6}]}
    async def call():
        return await bench_client.post("/ventas", json=payload)
    benchmark(run_async, call)


def bench_router_post_venta_3_items(benchmark, bench_client, run_async):
    """POST /ventas — venta con 3 items."""
    payload = {"items": [
        {"producto_id": 1, "cantidad": 6},
        {"producto_id": 2, "cantidad": 1},
        {"producto_id": 3, "cantidad": 12},
    ]}
    async def call():
        return await bench_client.post("/ventas", json=payload)
    benchmark(run_async, call)


def bench_router_post_venta_oferta(benchmark, bench_client, run_async):
    """POST /ventas — venta con oferta."""
    payload = {"items": [{"oferta_id": 1, "cantidad": 1, "productos_seleccionados": [
        {"producto_id": 1, "cantidad": 12}
    ]}]}
    async def call():
        return await bench_client.post("/ventas", json=payload)
    benchmark(run_async, call)


# ══════════════════════════════════════════════════════════════════════════════
# PUT / DELETE
# ══════════════════════════════════════════════════════════════════════════════

def bench_router_put_venta(benchmark, bench_client, run_async):
    """PUT /ventas/{id} — actualizar venta."""
    payload = {"items": [{"producto_id": 1, "cantidad": 6, "precio_unitario": "1000.00"}]}
    async def call():
        return await bench_client.put("/ventas/1", json=payload)
    benchmark(run_async, call)


def bench_router_delete_venta(benchmark, bench_client, run_async):
    """DELETE /ventas/{id}"""
    async def call():
        return await bench_client.delete("/ventas/1")
    benchmark(run_async, call)
