"""
bench_routers_auth.py — Benchmarks HTTP del router de autenticación

NOTA: El endpoint /auth/login llama a UserService.authenticate_user() que está
mockeado en bench_client — NO ejecuta bcrypt real.
"""

import pytest


def bench_router_post_login_success(benchmark, bench_client, run_async):
    """POST /auth/login — login válido (servicio mockeado)."""
    async def call():
        return await bench_client.post("/auth/login", json={
            "username": "bench_admin",
            "password": "TestPass1",
        })
    benchmark(run_async, call)


def bench_router_post_logout(benchmark, bench_client, run_async):
    """POST /auth/logout"""
    async def call():
        return await bench_client.post("/auth/logout")
    benchmark(run_async, call)
