"""
bench_services_expense.py — Benchmarks del ExpenseService y ExpenseCategoryService
"""

import pytest
from datetime import date
from unittest.mock import AsyncMock, MagicMock

from app.application.expense_service import ExpenseService
from app.application.expense_category_service import ExpenseCategoryService
from app.presentation.schemas.expense_schemas import (
    GastoCreateRequest, GastoUpdateRequest,
)
from app.presentation.schemas.expense_category_schemas import (
    GastoCategoriaCreateRequest, GastoCategoriaUpdateRequest,
)
from tests.helpers import (
    build_expense_model, build_expense_category_model,
)


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _make_expense_uow(expense=None, category=None):
    uow = AsyncMock()
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock(return_value=None)
    uow.commit = AsyncMock()
    uow.rollback = AsyncMock()

    cat = category or build_expense_category_model(id=1, nombre="Ingredientes")
    uow.expense_category_repo.get_by_id = AsyncMock(return_value=cat)
    uow.expense_category_repo.get_subtree_ids = AsyncMock(return_value=[1])

    exp = expense or build_expense_model(id=1, categoria_gasto_id=1, monto=5000.0)
    uow.expense_repo.get_by_id = AsyncMock(return_value=exp)
    uow.expense_repo.get_by_id_with_category = AsyncMock(return_value=exp)
    uow.expense_repo.list = AsyncMock(return_value=[exp])
    uow.expense_repo.list_by_filters = AsyncMock(return_value=[exp])
    uow.expense_repo.add = AsyncMock(return_value=None)
    uow.expense_repo.update = AsyncMock(return_value=None)
    uow.expense_repo.delete = AsyncMock(return_value=None)

    uow.audit_repo.log_action = AsyncMock(return_value=MagicMock(id=1))

    return uow


def _make_expense_category_uow(category=None):
    uow = AsyncMock()
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock(return_value=None)
    uow.commit = AsyncMock()
    uow.rollback = AsyncMock()

    cat = category or build_expense_category_model(id=1, nombre="Ingredientes")
    uow.expense_category_repo.get_by_id = AsyncMock(return_value=cat)
    uow.expense_category_repo.get_by_id_with_subcategories = AsyncMock(return_value=cat)
    uow.expense_category_repo.list = AsyncMock(return_value=[cat])
    uow.expense_category_repo.list_active = AsyncMock(return_value=[cat])
    uow.expense_category_repo.get_by_parent_id = AsyncMock(return_value=[cat])
    uow.expense_category_repo.add = AsyncMock(return_value=None)
    uow.expense_category_repo.update = AsyncMock(return_value=None)
    uow.expense_category_repo.delete = AsyncMock(return_value=None)

    uow.audit_repo.log_action = AsyncMock(return_value=MagicMock(id=1))

    return uow


def _make_expense_service(uow=None):
    cache = MagicMock()
    cache.get = MagicMock(return_value=None)
    cache.set = MagicMock()
    cache.invalidate = MagicMock()
    cache.clear_all = MagicMock()

    audit = AsyncMock()
    audit.log_creation = AsyncMock(return_value=MagicMock(error=None))
    audit.log_update = AsyncMock(return_value=MagicMock(error=None))
    audit.log_deletion = AsyncMock(return_value=MagicMock(error=None))

    return ExpenseService(
        uow=uow or _make_expense_uow(),
        cache_service=cache,
        audit_service=audit,
        logger=MagicMock(),
    )


def _make_expense_category_service(uow=None):
    cache = MagicMock()
    cache.get = MagicMock(return_value=None)
    cache.set = MagicMock()
    cache.invalidate = MagicMock()
    cache.clear_all = MagicMock()

    audit = AsyncMock()
    audit.log_creation = AsyncMock(return_value=MagicMock(error=None))
    audit.log_update = AsyncMock(return_value=MagicMock(error=None))
    audit.log_deletion = AsyncMock(return_value=MagicMock(error=None))

    return ExpenseCategoryService(
        uow=uow or _make_expense_category_uow(),
        cache_service=cache,
        audit_service=audit,
        logger=MagicMock(),
    )


# Payloads ────────────────────────────────────────────────────────────────────

_CREATE_EXPENSE = GastoCreateRequest(
    categoria_gasto_id=1,
    descripcion="Compra de harina",
    monto=5000.0,
    fecha_pago=date(2026, 3, 11),
)

_UPDATE_EXPENSE = GastoUpdateRequest(monto=5500.0, descripcion="Harina + levadura")

_CREATE_CATEGORY = GastoCategoriaCreateRequest(nombre="Ingredientes")

_CREATE_SUBCATEGORY = GastoCategoriaCreateRequest(nombre="Lácteos", padre_id=1)

_UPDATE_CATEGORY = GastoCategoriaUpdateRequest(nombre="Ingredientes Base")


# ══════════════════════════════════════════════════════════════════════════════
# ExpenseService
# ══════════════════════════════════════════════════════════════════════════════

def bench_expense_create(benchmark, run_async):
    """Crear un gasto nuevo."""
    service = _make_expense_service()

    async def call():
        return await service.create(_CREATE_EXPENSE, username="bench_user")

    benchmark(run_async, call)


def bench_expense_get_by_id_cache_miss(benchmark, run_async):
    """get_by_id en caché fría."""
    service = _make_expense_service()

    async def call():
        return await service.get_by_id(1)

    benchmark(run_async, call)


def bench_expense_get_by_id_cache_hit(benchmark, run_async):
    """get_by_id con resultado en caché."""
    cached_value = build_expense_model(id=1)
    cache = MagicMock()
    cache.get = MagicMock(return_value=cached_value)

    audit = AsyncMock()
    service = ExpenseService(
        uow=_make_expense_uow(),
        cache_service=cache,
        audit_service=audit,
        logger=MagicMock(),
    )

    async def call():
        return await service.get_by_id(1)

    benchmark(run_async, call)


def bench_expense_list_all(benchmark, run_async):
    """Listar todos los gastos (sin caché)."""
    service = _make_expense_service()

    async def call():
        return await service.list_all()

    benchmark(run_async, call)


def bench_expense_list_by_filters_fecha(benchmark, run_async):
    """Filtrar gastos por rango de fechas."""
    service = _make_expense_service()
    desde = date(2026, 1, 1)
    hasta = date(2026, 3, 11)

    async def call():
        return await service.list_by_filters(fecha_desde=desde, fecha_hasta=hasta)

    benchmark(run_async, call)


def bench_expense_list_by_filters_categoria_raiz(benchmark, run_async):
    """Filtrar por categoría raíz (expande a subcategorías)."""
    uow = _make_expense_uow()
    # Con padre_id=None → es raíz → expandir subcategorías
    cat = build_expense_category_model(id=1, nombre="Ingredientes", padre_id=None)
    uow.expense_category_repo.get_by_id = AsyncMock(return_value=cat)
    uow.expense_category_repo.get_subtree_ids = AsyncMock(return_value=[1, 2, 3])
    service = _make_expense_service(uow)

    async def call():
        return await service.list_by_filters(categoria_gasto_id=1)

    benchmark(run_async, call)


def bench_expense_update(benchmark, run_async):
    """Actualizar monto y descripción de un gasto."""
    service = _make_expense_service()

    async def call():
        return await service.update(1, _UPDATE_EXPENSE, username="bench_user")

    benchmark(run_async, call)


def bench_expense_delete(benchmark, run_async):
    """Soft delete de un gasto."""
    service = _make_expense_service()

    async def call():
        return await service.delete(1, username="bench_user")

    benchmark(run_async, call)


# ══════════════════════════════════════════════════════════════════════════════
# ExpenseCategoryService
# ══════════════════════════════════════════════════════════════════════════════

def bench_expense_category_create_root(benchmark, run_async):
    """Crear categoría raíz de gastos."""
    service = _make_expense_category_service()

    async def call():
        return await service.create(_CREATE_CATEGORY, username="bench_user")

    benchmark(run_async, call)


def bench_expense_category_create_sub(benchmark, run_async):
    """Crear subcategoría (con padre_id validado)."""
    service = _make_expense_category_service()

    async def call():
        return await service.create(_CREATE_SUBCATEGORY, username="bench_user")

    benchmark(run_async, call)


def bench_expense_category_get_by_id(benchmark, run_async):
    """get_by_id de categoría."""
    service = _make_expense_category_service()

    async def call():
        return await service.get_by_id(1)

    benchmark(run_async, call)


def bench_expense_category_list_all(benchmark, run_async):
    """Listar todas las categorías de gasto."""
    service = _make_expense_category_service()

    async def call():
        return await service.list_all()

    benchmark(run_async, call)


def bench_expense_category_list_by_parent(benchmark, run_async):
    """Listar subcategorías de una categoría padre."""
    service = _make_expense_category_service()

    async def call():
        return await service.list_by_parent(parent_id=1)

    benchmark(run_async, call)


def bench_expense_category_update(benchmark, run_async):
    """Actualizar nombre de categoría de gasto."""
    service = _make_expense_category_service()

    async def call():
        return await service.update(1, _UPDATE_CATEGORY, username="bench_user")

    benchmark(run_async, call)


def bench_expense_category_delete(benchmark, run_async):
    """Soft delete de categoría de gasto."""
    service = _make_expense_category_service()

    async def call():
        return await service.delete(1, username="bench_user")

    benchmark(run_async, call)
