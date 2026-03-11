"""
bench_services_audit.py — Benchmarks del AuditService

AuditService maneja log_creation, log_update (con diff), log_deletion,
y get_by_date_range. El diff de entidades involucra inspect() de SQLAlchemy.
"""

import pytest
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock

from app.application.audit_service import AuditService
from app.domain.models.product import Product
from app.domain.models.expense import Expense
from app.domain.models.sale import Sale
from app.domain.models.sale_item import SaleItem
from tests.helpers import (
    build_product_model, build_expense_model, build_sale_model,
    build_sale_item_model, build_product_price_model,
)


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _make_uow(log_count: int = 10):
    uow = AsyncMock()
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock(return_value=None)
    uow.commit = AsyncMock()
    uow.rollback = AsyncMock()

    uow.audit_repo.log_action = AsyncMock(return_value=MagicMock(id=1))

    logs = [
        MagicMock(
            id=i,
            username="bench_user",
            entity_type="Product",
            entity_id=i,
            action="UPDATE",
            timestamp=datetime.now(timezone.utc),
            changes={"field": {"old": "a", "new": "b"}},
        )
        for i in range(1, log_count + 1)
    ]
    uow.audit_repo.get_by_filters = AsyncMock(return_value=(logs, log_count))

    return uow


def _make_service(uow=None):
    return AuditService(uow=uow or _make_uow(), logger=MagicMock())


# ══════════════════════════════════════════════════════════════════════════════
# log_creation
# ══════════════════════════════════════════════════════════════════════════════

def bench_audit_log_creation_product(benchmark, run_async):
    """Registrar creación de un producto."""
    service = _make_service()
    product = build_product_model(
        id=1, nombre="Empanada", categoria_id=1,
        precios=[build_product_price_model(1, 1, 1, 1200.0)],
    )

    async def call():
        return await service.log_creation("bench_user", "Product", product)

    benchmark(run_async, call)


def bench_audit_log_creation_sale(benchmark, run_async):
    """Registrar creación de una venta."""
    service = _make_service()
    sale = build_sale_model(id=1, total=6000.0)

    async def call():
        return await service.log_creation("bench_user", "Sale", sale)

    benchmark(run_async, call)


# ══════════════════════════════════════════════════════════════════════════════
# log_update
# ══════════════════════════════════════════════════════════════════════════════

def bench_audit_log_update_product_no_diff(benchmark, run_async):
    """log_update sin cambios (debe ser no-op)."""
    service = _make_service()
    product = build_product_model(id=1, nombre="Empanada", categoria_id=1)
    # Mismo objeto → diff vacío → no-op
    same = build_product_model(id=1, nombre="Empanada", categoria_id=1)

    async def call():
        return await service.log_update("bench_user", "Product", product, same)

    benchmark(run_async, call)


def bench_audit_log_update_product_con_cambios(benchmark, run_async):
    """log_update con nombre cambiado."""
    service = _make_service()
    old = build_product_model(id=1, nombre="Empanada Carne", categoria_id=1)
    new = build_product_model(id=1, nombre="Empanada Criolla", categoria_id=1)

    async def call():
        return await service.log_update("bench_user", "Product", old, new)

    benchmark(run_async, call)


def bench_audit_log_update_expense(benchmark, run_async):
    """log_update de un gasto (monto cambiado)."""
    service = _make_service()
    old = build_expense_model(id=1, monto=5000.0, categoria_gasto_id=1)
    new = build_expense_model(id=1, monto=5500.0, categoria_gasto_id=1)

    async def call():
        return await service.log_update("bench_user", "Expense", old, new)

    benchmark(run_async, call)


def bench_audit_log_update_sale_no_diff(benchmark, run_async):
    """log_update de venta sin cambios (sale_diff no-op)."""
    service = _make_service()
    sale = build_sale_model(id=1, total=6000.0)
    same = build_sale_model(id=1, total=6000.0)

    async def call():
        return await service.log_update("bench_user", "Sale", sale, same)

    benchmark(run_async, call)


def bench_audit_log_update_sale_con_items(benchmark, run_async):
    """log_update de venta con items cambiados."""
    service = _make_service()
    old = build_sale_model(id=1, total=6000.0)
    new = build_sale_model(id=1, total=7200.0)

    async def call():
        return await service.log_update("bench_user", "Sale", old, new)

    benchmark(run_async, call)


# ══════════════════════════════════════════════════════════════════════════════
# log_deletion
# ══════════════════════════════════════════════════════════════════════════════

def bench_audit_log_deletion_product(benchmark, run_async):
    """Registrar eliminación de un producto."""
    service = _make_service()
    product = build_product_model(id=1, nombre="Empanada", categoria_id=1)

    async def call():
        return await service.log_deletion("bench_user", "Product", product)

    benchmark(run_async, call)


def bench_audit_log_deletion_sale(benchmark, run_async):
    """Registrar eliminación de una venta."""
    service = _make_service()
    sale = build_sale_model(id=1, total=6000.0)

    async def call():
        return await service.log_deletion("bench_user", "Sale", sale)

    benchmark(run_async, call)


# ══════════════════════════════════════════════════════════════════════════════
# get_by_date_range
# ══════════════════════════════════════════════════════════════════════════════

def bench_audit_get_by_date_range_10(benchmark, run_async):
    """Buscar 10 registros de auditoría por rango de fechas."""
    service = _make_service(_make_uow(log_count=10))

    async def call():
        return await service.get_by_date_range(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 3, 11),
            limit=10,
            offset=0,
        )

    benchmark(run_async, call)


def bench_audit_get_by_date_range_100(benchmark, run_async):
    """Buscar 100 registros de auditoría."""
    service = _make_service(_make_uow(log_count=100))

    async def call():
        return await service.get_by_date_range(
            start_date=date(2025, 1, 1),
            end_date=date(2026, 3, 11),
            limit=100,
            offset=0,
        )

    benchmark(run_async, call)


def bench_audit_get_by_date_range_con_filtros(benchmark, run_async):
    """Buscar con filtro de entity_type y action."""
    service = _make_service(_make_uow(log_count=20))

    async def call():
        return await service.get_by_date_range(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 3, 11),
            entity_type="Product",
            action="UPDATE",
            limit=20,
            offset=0,
        )

    benchmark(run_async, call)
