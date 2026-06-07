"""
bench_routers_audit.py — Benchmarks HTTP del router de auditoría
"""

import pytest


def bench_router_get_audit_search(benchmark, bench_client, run_async):
    """GET /audit/search — sin filtros (devuelve logs vacíos mockeados)."""
    async def call():
        return await bench_client.get("/audit/search")
    benchmark(run_async, call)


def bench_router_get_audit_search_con_filtros(benchmark, bench_client, run_async):
    """GET /audit/search?entity_type=Product&action=UPDATE"""
    async def call():
        return await bench_client.get("/audit/search", params={
            "entity_type": "Product",
            "action": "UPDATE",
            "start_date": "2026-01-01",
            "end_date": "2026-03-11",
            "limit": 100,
            "offset": 0,
        })
    benchmark(run_async, call)


def bench_router_get_audit_search_paginado(benchmark, bench_client, run_async):
    """GET /audit/search?limit=50&offset=100 — segunda página."""
    async def call():
        return await bench_client.get("/audit/search", params={"limit": 50, "offset": 100})
    benchmark(run_async, call)
