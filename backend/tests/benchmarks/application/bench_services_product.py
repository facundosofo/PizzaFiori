"""
bench_services_product.py — Benchmarks del ProductService y ProductCategoryService

Mide overhead Python: validación, lógica de precios, generación de SKU,
cache invalidation — sin I/O real.
"""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from app.application.product_service import ProductService
from app.application.product_category_service import ProductCategoryService
from app.presentation.schemas.product_schemas import (
    ProductoCreateRequest, ProductoUpdateRequest, ProductoPrecioRequest,
    ActualizarPreciosMasivosRequest,
)
from app.presentation.schemas.product_category_schemas import (
    ProductoCategoriaCreateRequest, ProductoCategoriaUpdateRequest,
)
from tests.helpers import (
    build_product_model, build_category_model, build_product_price_model,
)


# ──────────────────────────────────────────────────────────────────────────────
# UoW helpers
# ──────────────────────────────────────────────────────────────────────────────

def _make_product_uow(product=None, category=None):
    uow = AsyncMock()
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock(return_value=None)
    uow.commit = AsyncMock()
    uow.rollback = AsyncMock()

    cat = category or build_category_model(id=1, nombre="Empanadas")
    uow.product_category_repo.get_by_id = AsyncMock(return_value=cat)
    uow.product_category_repo.list_by_active = AsyncMock(return_value=[cat])
    uow.product_category_repo.list = AsyncMock(return_value=[cat])

    prod = product or build_product_model(
        id=1, nombre="Empanada de Carne", categoria_id=1,
        precios=[
            build_product_price_model(1, 1, 1, 1200.0),
            build_product_price_model(2, 1, 6, 6000.0),
        ],
    )
    uow.product_repo.get_by_id = AsyncMock(return_value=prod)
    uow.product_repo.list = AsyncMock(return_value=[prod])
    uow.product_repo.list_by_categoria = AsyncMock(return_value=[prod])
    uow.product_repo.add = AsyncMock(return_value=None)
    uow.product_repo.update = AsyncMock(return_value=None)
    uow.product_repo.delete = AsyncMock(return_value=None)
    uow.product_repo.get_by_sku = AsyncMock(return_value=None)
    uow.product_repo.replace_prices = AsyncMock(return_value=None)
    uow.product_repo.list_by_categoria_ids = AsyncMock(return_value=[prod])

    uow.offer_repo.get_active_by_product_id = AsyncMock(return_value=[])

    uow.audit_repo.log_action = AsyncMock(return_value=MagicMock(id=1))

    return uow


def _make_category_uow(category=None, products=None):
    uow = AsyncMock()
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock(return_value=None)
    uow.commit = AsyncMock()
    uow.rollback = AsyncMock()

    cat = category or build_category_model(id=1, nombre="Empanadas")
    uow.product_category_repo.get_by_id = AsyncMock(return_value=cat)
    uow.product_category_repo.list = AsyncMock(return_value=[cat])
    uow.product_category_repo.list_by_active = AsyncMock(return_value=[cat])
    uow.product_category_repo.add = AsyncMock(return_value=None)
    uow.product_category_repo.update = AsyncMock(return_value=None)

    uow.product_repo.list_by_categoria = AsyncMock(return_value=products or [])
    uow.offer_repo.get_active_by_product_id = AsyncMock(return_value=[])

    uow.audit_repo.log_action = AsyncMock(return_value=MagicMock(id=1))

    return uow


def _make_product_service(uow=None):
    cache = MagicMock()
    cache.get = MagicMock(return_value=None)
    cache.set = MagicMock()
    cache.invalidate = MagicMock()
    cache.clear_all = MagicMock()

    file_svc = AsyncMock()
    file_svc.save_image = AsyncMock(return_value="products/test.jpg")
    file_svc.delete_file = AsyncMock()

    audit = AsyncMock()
    audit.log_creation = AsyncMock(return_value=MagicMock(error=None))
    audit.log_update = AsyncMock(return_value=MagicMock(error=None))
    audit.log_deletion = AsyncMock(return_value=MagicMock(error=None))

    return ProductService(
        uow=uow or _make_product_uow(),
        file_service=file_svc,
        cache_service=cache,
        audit_service=audit,
        logger=MagicMock(),
    )


def _make_category_service(uow=None):
    cache = MagicMock()
    cache.get = MagicMock(return_value=None)
    cache.set = MagicMock()
    cache.invalidate = MagicMock()
    cache.clear_all = MagicMock()

    audit = AsyncMock()
    audit.log_creation = AsyncMock(return_value=MagicMock(error=None))
    audit.log_update = AsyncMock(return_value=MagicMock(error=None))
    audit.log_deletion = AsyncMock(return_value=MagicMock(error=None))

    return ProductCategoryService(
        uow=uow or _make_category_uow(),
        cache_service=cache,
        audit_service=audit,
        logger=MagicMock(),
    )


# ──────────────────────────────────────────────────────────────────────────────
# Payloads
# ──────────────────────────────────────────────────────────────────────────────

_CREATE_PAYLOAD = ProductoCreateRequest(
    nombre="Empanada de Carne",
    categoria_id=1,
    precios=[
        ProductoPrecioRequest(cantidad=1, precio=Decimal("1200")),
        ProductoPrecioRequest(cantidad=6, precio=Decimal("6000")),
        ProductoPrecioRequest(cantidad=12, precio=Decimal("10800")),
    ],
)

_UPDATE_PAYLOAD = ProductoUpdateRequest(
    nombre="Empanada Criolla",
    precios=[
        ProductoPrecioRequest(id=1, cantidad=1, precio=Decimal("1300")),
        ProductoPrecioRequest(id=2, cantidad=6, precio=Decimal("7000")),
    ],
)

_BULK_MONTO_PAYLOAD = ActualizarPreciosMasivosRequest(monto=Decimal("100"))
_BULK_PCT_PAYLOAD = ActualizarPreciosMasivosRequest(porcentaje=Decimal("10"))


# ══════════════════════════════════════════════════════════════════════════════
# ProductService
# ══════════════════════════════════════════════════════════════════════════════

def bench_product_create(benchmark, run_async):
    """Crear producto nuevo (sin imagen)."""
    service = _make_product_service()

    async def call():
        return await service.create(_CREATE_PAYLOAD, image=None, username="bench_user")

    benchmark(run_async, call)


def bench_product_get_all_no_filter(benchmark, run_async):
    """Listar todos los productos activos."""
    service = _make_product_service()

    async def call():
        return await service.get_all()

    benchmark(run_async, call)


def bench_product_get_all_by_categoria(benchmark, run_async):
    """Listar productos filtrando por categoría."""
    service = _make_product_service()

    async def call():
        return await service.get_all(categoria_id=1)

    benchmark(run_async, call)


def bench_product_get_by_id_found(benchmark, run_async):
    """get_by_id cuando el producto existe."""
    service = _make_product_service()

    async def call():
        return await service.get_by_id(1)

    benchmark(run_async, call)


def bench_product_get_by_id_not_found(benchmark, run_async):
    """get_by_id cuando el producto no existe."""
    uow = _make_product_uow()
    uow.product_repo.get_by_id = AsyncMock(return_value=None)
    service = _make_product_service(uow)

    async def call():
        return await service.get_by_id(999)

    benchmark(run_async, call)


def bench_product_update_prices(benchmark, run_async):
    """Actualizar nombre y precios de un producto."""
    service = _make_product_service()

    async def call():
        return await service.update(1, producto_update=_UPDATE_PAYLOAD, username="bench_user")

    benchmark(run_async, call)


def bench_product_deactivate(benchmark, run_async):
    """Desactivar (soft-delete) un producto."""
    service = _make_product_service()

    async def call():
        return await service.update(
            1, active=False, username="bench_user", is_logical_delete=True
        )

    benchmark(run_async, call)


def bench_product_bulk_update_monto(benchmark, run_async):
    """Actualizar precios en masa por monto fijo."""
    uow = _make_product_uow()
    # Devolver 10 productos para simular carga realista
    products = [
        build_product_model(
            id=i, nombre=f"Producto {i}", categoria_id=1,
            precios=[
                build_product_price_model(i * 2 - 1, i, 1, 1200.0),
                build_product_price_model(i * 2, i, 6, 6000.0),
            ],
        )
        for i in range(1, 11)
    ]
    uow.product_repo.list_by_categoria_ids = AsyncMock(return_value=products)
    uow.product_category_repo.list_by_active = AsyncMock(
        return_value=[build_category_model(id=i) for i in range(1, 4)]
    )
    service = _make_product_service(uow)

    async def call():
        return await service.bulk_update_prices(
            monto=Decimal("100"), porcentaje=None, categoria_ids=None, username="bench_user"
        )

    benchmark(run_async, call)


def bench_product_bulk_update_porcentaje(benchmark, run_async):
    """Actualizar precios en masa por porcentaje."""
    uow = _make_product_uow()
    products = [
        build_product_model(
            id=i, nombre=f"Producto {i}", categoria_id=1,
            precios=[build_product_price_model(i, i, 1, 1200.0)],
        )
        for i in range(1, 6)
    ]
    uow.product_repo.list_by_categoria_ids = AsyncMock(return_value=products)
    uow.product_category_repo.list_by_active = AsyncMock(
        return_value=[build_category_model(id=1)]
    )
    service = _make_product_service(uow)

    async def call():
        return await service.bulk_update_prices(
            monto=None, porcentaje=Decimal("10"), categoria_ids=[1], username="bench_user"
        )

    benchmark(run_async, call)


# ══════════════════════════════════════════════════════════════════════════════
# ProductCategoryService
# ══════════════════════════════════════════════════════════════════════════════

def bench_category_create(benchmark, run_async):
    """Crear categoría de producto."""
    service = _make_category_service()
    payload = ProductoCategoriaCreateRequest(nombre="Pizzas")

    async def call():
        return await service.create(payload, username="bench_user")

    benchmark(run_async, call)


def bench_category_get_all(benchmark, run_async):
    """Listar todas las categorías."""
    service = _make_category_service()

    async def call():
        return await service.get_all()

    benchmark(run_async, call)


def bench_category_get_by_id(benchmark, run_async):
    """get_by_id de categoría."""
    service = _make_category_service()

    async def call():
        return await service.get_by_id(1)

    benchmark(run_async, call)


def bench_category_update(benchmark, run_async):
    """Actualizar nombre de categoría."""
    service = _make_category_service()
    payload = ProductoCategoriaUpdateRequest(nombre="Empanadas Regionales")

    async def call():
        return await service.update(1, payload, username="bench_user")

    benchmark(run_async, call)


def bench_category_deactivate_sin_productos(benchmark, run_async):
    """Desactivar categoría vacía (sin productos)."""
    uow = _make_category_uow(products=[])
    service = _make_category_service(uow)

    async def call():
        return await service.deactivate(1, username="bench_user")

    benchmark(run_async, call)


def bench_category_deactivate_con_productos(benchmark, run_async):
    """Desactivar categoría con 5 productos (cascade)."""
    products = [build_product_model(id=i, categoria_id=1) for i in range(1, 6)]
    uow = _make_category_uow(products=products)
    service = _make_category_service(uow)

    async def call():
        return await service.deactivate(1, username="bench_user")

    benchmark(run_async, call)
