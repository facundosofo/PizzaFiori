"""
bench_cache.py — Benchmarks del CacheService (in-memory, sync, sin DB)

Cubre:
  - get: cache miss y hit
  - set: payloads pequeño y grande
  - invalidate: con 10 / 100 / 500 keys en cache (benchmark.pedantic + setup)
  - get_stats / clear_all con cache poblada
"""

import pytest
from app.infrastructure.cache.cache_service import CacheService


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

_SMALL_PAYLOAD = {"id": 1, "nombre": "Pizza Muzzarella", "precio": 1200.0}

_LARGE_PAYLOAD = [
    {"id": i, "nombre": f"Producto {i}", "precio": float(i * 100), "activo": True}
    for i in range(100)
]


def _fill_cache(cache: CacheService, n: int, prefix: str = "item") -> None:
    """Llena el cache con N entradas con claves tipo 'producto_N'."""
    for i in range(n):
        cache.set(f"{prefix}_{i}", {"id": i, "value": f"data_{i}"})


# ══════════════════════════════════════════════════════════════════════════════
# GET
# ══════════════════════════════════════════════════════════════════════════════

def bench_cache_get_miss(benchmark):
    """get() sobre key inexistente — retorna None inmediatamente."""
    cache = CacheService()
    benchmark(cache.get, "nonexistent_key_12345")


def bench_cache_get_hit(benchmark):
    """get() sobre key existente — recupera del TTLCache."""
    cache = CacheService()
    cache.set("producto_1", _SMALL_PAYLOAD)
    benchmark(cache.get, "producto_1")


def bench_cache_get_hit_large_payload(benchmark):
    """get() de payload grande (lista de 100 items)."""
    cache = CacheService()
    cache.set("producto_list", _LARGE_PAYLOAD)
    benchmark(cache.get, "producto_list")


# ══════════════════════════════════════════════════════════════════════════════
# SET
# ══════════════════════════════════════════════════════════════════════════════

def bench_cache_set_small(benchmark):
    """set() de payload pequeño (dict de 3 keys)."""
    cache = CacheService()
    benchmark(cache.set, "producto_1", _SMALL_PAYLOAD)


def bench_cache_set_large(benchmark):
    """set() de payload grande (lista de 100 dicts)."""
    cache = CacheService()
    benchmark(cache.set, "producto_list_all", _LARGE_PAYLOAD)


def bench_cache_set_overwrite(benchmark):
    """set() sobre key existente — sobreescribir en TTLCache."""
    cache = CacheService()
    cache.set("producto_1", _SMALL_PAYLOAD)
    benchmark(cache.set, "producto_1", {"id": 1, "nombre": "Actualizado"})


# ══════════════════════════════════════════════════════════════════════════════
# INVALIDATE
# ══════════════════════════════════════════════════════════════════════════════

def bench_cache_invalidate_10_keys(benchmark):
    """invalidate() con 10 keys en cache, patron 'producto_*' matchea 5."""
    cache = CacheService()

    def setup():
        cache.cache.clear()
        for i in range(5):
            cache.set(f"producto_{i}", {"id": i})
        for i in range(5):
            cache.set(f"oferta_{i}", {"id": i})

    benchmark.pedantic(lambda: cache.invalidate("producto_*"), setup=setup, iterations=1, rounds=200)


def bench_cache_invalidate_100_keys(benchmark):
    """invalidate() con 100 keys en cache, patron 'producto_*' matchea 50."""
    cache = CacheService()

    def setup():
        cache.cache.clear()
        for i in range(50):
            cache.set(f"producto_{i}", {"id": i})
        for i in range(50):
            cache.set(f"gasto_{i}", {"id": i})

    benchmark.pedantic(lambda: cache.invalidate("producto_*"), setup=setup, iterations=1, rounds=100)


def bench_cache_invalidate_500_keys(benchmark):
    """invalidate() con 500 keys (cerca del límite MAX_SIZE=1000), patron matchea mitad."""
    cache = CacheService()

    def setup():
        cache.cache.clear()
        for i in range(250):
            cache.set(f"producto_{i}", {"id": i})
        for i in range(250):
            cache.set(f"venta_{i}", {"id": i})

    benchmark.pedantic(lambda: cache.invalidate("producto_*"), setup=setup, iterations=1, rounds=50)


def bench_cache_invalidate_no_match(benchmark):
    """invalidate() cuando ninguna key matchea el patrón — itera todo sin borrar."""
    cache = CacheService()
    _fill_cache(cache, 100, prefix="venta")
    benchmark(cache.invalidate, "producto_*")


def bench_cache_invalidate_all_match(benchmark):
    """invalidate() cuando todas las keys matchean — elimina todo el cache."""
    cache = CacheService()

    def setup():
        cache.cache.clear()
        _fill_cache(cache, 100, prefix="producto")

    benchmark.pedantic(lambda: cache.invalidate("producto_*"), setup=setup, iterations=1, rounds=100)


# ══════════════════════════════════════════════════════════════════════════════
# GET_STATS
# ══════════════════════════════════════════════════════════════════════════════

def bench_cache_get_stats_empty(benchmark):
    """get_stats() con cache vacío."""
    cache = CacheService()
    benchmark(cache.get_stats)


def bench_cache_get_stats_100_items(benchmark):
    """get_stats() con 100 keys — construye la lista de keys."""
    cache = CacheService()
    _fill_cache(cache, 100)
    benchmark(cache.get_stats)


# ══════════════════════════════════════════════════════════════════════════════
# CLEAR_ALL
# ══════════════════════════════════════════════════════════════════════════════

def bench_cache_clear_all_empty(benchmark):
    """clear_all() sobre cache vacío — O(1)."""
    cache = CacheService()
    benchmark(cache.clear_all)


def bench_cache_clear_all_100_items(benchmark):
    """clear_all() con 100 items — debe ser O(1) independientemente del tamaño."""
    cache = CacheService()

    def setup():
        cache.cache.clear()
        _fill_cache(cache, 100)

    benchmark.pedantic(cache.clear_all, setup=setup, iterations=1, rounds=200)
