"""
bench_routers_user.py — Benchmarks HTTP del router de usuarios
"""

import pytest


def bench_router_get_me(benchmark, bench_client, run_async):
    """GET /users/me"""
    async def call():
        return await bench_client.get("/users/me")
    benchmark(run_async, call)


def bench_router_get_users(benchmark, bench_client, run_async):
    """GET /users — listar usuarios (admin)."""
    async def call():
        return await bench_client.get("/users")
    benchmark(run_async, call)


def bench_router_get_user_by_id(benchmark, bench_client, run_async):
    """GET /users/{id}"""
    async def call():
        return await bench_client.get("/users/1")
    benchmark(run_async, call)


def bench_router_post_register(benchmark, bench_client, run_async):
    """POST /users — registrar usuario nuevo."""
    async def call():
        return await bench_client.post("/users", json={
            "username": "newuser",
            "email": "new@example.com",
            "password": "TestPass1",
            "first_name": "Test",
            "last_name": "User",
        })
    benchmark(run_async, call)


def bench_router_put_update_user(benchmark, bench_client, run_async):
    """PUT /users/{id} — actualizar datos."""
    async def call():
        return await bench_client.put("/users/1", json={
            "first_name": "Nuevo",
            "last_name": "Apellido",
        })
    benchmark(run_async, call)


def bench_router_post_change_password(benchmark, bench_client, run_async):
    """POST /users/me/change-password"""
    async def call():
        return await bench_client.post("/users/me/change-password", json={
            "old_password": "TestPass1",
            "new_password": "NewPass2",
        })
    benchmark(run_async, call)


def bench_router_delete_user(benchmark, bench_client, run_async):
    """DELETE /users/{id}"""
    async def call():
        return await bench_client.delete("/users/1")
    benchmark(run_async, call)


def bench_router_post_unlock_user(benchmark, bench_client, run_async):
    """POST /users/{id}/unlock"""
    async def call():
        return await bench_client.post("/users/1/unlock")
    benchmark(run_async, call)
