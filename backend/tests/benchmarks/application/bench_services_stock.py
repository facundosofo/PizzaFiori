"""
bench_services_stock.py — Benchmarks del StockService

StockService gestiona el inventario por categoría de producto.
Mide: get_all_stocks (calcula estado por cada categoría),
add_stock (INGRESO/AJUSTE_BAJA + audit), configure_alerts, get_movements.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.application.stock_service import StockService
from tests.helpers import build_category_model


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _make_stock_entry(categoria_id: int, cantidad: int = 100,
                      umbral_amarillo: int = 20, umbral_rojo: int = 10):
    """Mock de un registro de stock con atributos reales."""
    s = MagicMock()
    s.categoria_id = categoria_id
    s.cantidad = cantidad
    s.umbral_amarillo = umbral_amarillo
    s.umbral_rojo = umbral_rojo
    return s


def _make_uow(categories=None, stock_entries=None, audit_movements=None):
    uow = AsyncMock()
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock(return_value=None)
    uow.commit = AsyncMock()
    uow.rollback = AsyncMock()

    cats = categories or [build_category_model(id=1, nombre="Empanadas")]
    uow.product_category_repo.list_by_active = AsyncMock(return_value=cats)
    uow.product_category_repo.get_by_id = AsyncMock(return_value=cats[0])

    entries = stock_entries or {cat.id: _make_stock_entry(cat.id) for cat in cats}

    async def _get_stock(cat_id):
        return entries.get(cat_id)

    uow.stock_repo.get_by_categoria_id = AsyncMock(side_effect=_get_stock)
    uow.stock_repo.upsert = AsyncMock(return_value=None)
    uow.stock_repo.update = AsyncMock(return_value=None)

    movements = audit_movements or [
        MagicMock(id=i, username="bench_user", action="INGRESO", changes={}) for i in range(1, 6)
    ]
    uow.audit_repo.get_by_entity = AsyncMock(return_value=movements)
    uow.audit_repo.log_action = AsyncMock(return_value=MagicMock(id=1))

    return uow


def _make_service(uow=None):
    return StockService(uow=uow or _make_uow(), logger=MagicMock())


# ══════════════════════════════════════════════════════════════════════════════
# get_all_stocks
# ══════════════════════════════════════════════════════════════════════════════

def bench_stock_get_all_3_categorias(benchmark, run_async):
    """get_all_stocks con 3 categorías (escala pequeña)."""
    cats = [build_category_model(id=i, nombre=f"Cat {i}") for i in range(1, 4)]
    entries = {c.id: _make_stock_entry(c.id, cantidad=100 - i * 10) for i, c in enumerate(cats)}
    service = _make_service(_make_uow(categories=cats, stock_entries=entries))

    async def call():
        return await service.get_all_stocks()

    benchmark(run_async, call)


def bench_stock_get_all_15_categorias(benchmark, run_async):
    """get_all_stocks con 15 categorías (escala típica)."""
    cats = [build_category_model(id=i, nombre=f"Cat {i}") for i in range(1, 16)]
    entries = {c.id: _make_stock_entry(c.id, cantidad=max(0, 200 - i * 10)) for i, c in enumerate(cats)}
    service = _make_service(_make_uow(categories=cats, stock_entries=entries))

    async def call():
        return await service.get_all_stocks()

    benchmark(run_async, call)


def bench_stock_get_all_sin_entrada(benchmark, run_async):
    """get_all_stocks cuando no hay registro aún para una categoría (crea entry vacía)."""
    cats = [build_category_model(id=1, nombre="Nueva Cat")]
    service = _make_service(_make_uow(categories=cats, stock_entries={}))

    async def call():
        return await service.get_all_stocks()

    benchmark(run_async, call)


# ══════════════════════════════════════════════════════════════════════════════
# add_stock
# ══════════════════════════════════════════════════════════════════════════════

def bench_stock_add_ingreso(benchmark, run_async):
    """Registrar ingreso de stock (+50)."""
    service = _make_service()

    async def call():
        return await service.add_stock(categoria_id=1, cantidad=50, username="bench_user")

    benchmark(run_async, call)


def bench_stock_add_ajuste_baja(benchmark, run_async):
    """Registrar ajuste de baja de stock (-10)."""
    service = _make_service()

    async def call():
        return await service.add_stock(categoria_id=1, cantidad=-10, username="bench_user")

    benchmark(run_async, call)


def bench_stock_add_sin_entrada_previa(benchmark, run_async):
    """Registrar stock cuando no hay entrada previa (primera vez)."""
    cats = [build_category_model(id=1, nombre="Nueva Cat")]
    service = _make_service(_make_uow(categories=cats, stock_entries={}))

    async def call():
        return await service.add_stock(categoria_id=1, cantidad=100, username="bench_user")

    benchmark(run_async, call)


# ══════════════════════════════════════════════════════════════════════════════
# configure_alerts
# ══════════════════════════════════════════════════════════════════════════════

def bench_stock_configure_alerts_ambos(benchmark, run_async):
    """Configurar ambos umbrales de alerta."""
    service = _make_service()

    async def call():
        return await service.configure_alerts(
            categoria_id=1, umbral_amarillo=30, umbral_rojo=10, username="bench_user"
        )

    benchmark(run_async, call)


def bench_stock_configure_alerts_solo_rojo(benchmark, run_async):
    """Configurar solo umbral rojo (crítico)."""
    service = _make_service()

    async def call():
        return await service.configure_alerts(
            categoria_id=1, umbral_amarillo=None, umbral_rojo=5, username="bench_user"
        )

    benchmark(run_async, call)


def bench_stock_configure_alerts_reset(benchmark, run_async):
    """Deshabilitar alertas (umbral None → None)."""
    service = _make_service()

    async def call():
        return await service.configure_alerts(
            categoria_id=1, umbral_amarillo=None, umbral_rojo=None, username="bench_user"
        )

    benchmark(run_async, call)


# ══════════════════════════════════════════════════════════════════════════════
# get_movements
# ══════════════════════════════════════════════════════════════════════════════

def bench_stock_get_movements_5(benchmark, run_async):
    """Obtener 5 movimientos de stock."""
    service = _make_service()

    async def call():
        return await service.get_movements(categoria_id=1, limit=5)

    benchmark(run_async, call)


def bench_stock_get_movements_50(benchmark, run_async):
    """Obtener 50 movimientos de stock."""
    movements = [
        MagicMock(id=i, username="bench_user", action="INGRESO", changes={})
        for i in range(50)
    ]
    uow = _make_uow()
    uow.audit_repo.get_by_entity = AsyncMock(return_value=movements)
    service = _make_service(uow)

    async def call():
        return await service.get_movements(categoria_id=1, limit=50)

    benchmark(run_async, call)
