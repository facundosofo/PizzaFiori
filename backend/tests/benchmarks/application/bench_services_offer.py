"""
bench_services_offer.py — Benchmarks del OfferService
"""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

from app.application.offer_service import OfferService
from app.presentation.schemas.offer_schemas import (
    OfferCreateRequest, OfferItemRequest, OfferUpdateRequest,
)
from tests.helpers import (
    build_product_model, build_offer_model, build_offer_item_model,
    build_category_model, build_product_price_model,
)


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _make_uow(offer=None, products=None, category=None):
    uow = AsyncMock()
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock(return_value=None)
    uow.commit = AsyncMock()
    uow.rollback = AsyncMock()

    prods = products or [
        build_product_model(
            id=1, nombre="Empanada de Carne", categoria_id=1,
            precios=[build_product_price_model(1, 1, 1, 1200.0)],
        ),
        build_product_model(
            id=2, nombre="Empanada de Pollo", categoria_id=1,
            precios=[build_product_price_model(2, 2, 1, 1200.0)],
        ),
    ]
    cat = category or build_category_model(id=1, nombre="Empanadas")

    uow.product_repo.get_by_id = AsyncMock(side_effect=lambda pid: next(
        (p for p in prods if p.id == pid), prods[0]
    ))
    uow.product_repo.list_by_categoria = AsyncMock(return_value=prods)
    uow.product_category_repo.get_by_id = AsyncMock(return_value=cat)

    default_offer = offer or build_offer_model(id=1, precio=10000.0)
    uow.offer_repo.get_by_id = AsyncMock(return_value=default_offer)
    uow.offer_repo.list = AsyncMock(return_value=[default_offer])
    uow.offer_repo.list_by_active = AsyncMock(return_value=[default_offer])
    uow.offer_repo.add = AsyncMock(return_value=None)
    uow.offer_repo.update = AsyncMock(return_value=None)
    uow.offer_repo.delete = AsyncMock(return_value=None)
    uow.offer_repo.replace_items = AsyncMock(return_value=None)
    uow.offer_repo.get_active_by_product_id = AsyncMock(return_value=[default_offer])
    uow.offer_repo.deactivate_by_product = AsyncMock(return_value=None)

    uow.audit_repo.log_action = AsyncMock(return_value=MagicMock(id=1))

    return uow


def _make_service(uow=None):
    cache = MagicMock()
    cache.get = MagicMock(return_value=None)
    cache.set = MagicMock()
    cache.invalidate = MagicMock()
    cache.clear_all = MagicMock()

    audit = AsyncMock()
    audit.log_creation = AsyncMock(return_value=MagicMock(error=None))
    audit.log_update = AsyncMock(return_value=MagicMock(error=None))
    audit.log_deletion = AsyncMock(return_value=MagicMock(error=None))

    return OfferService(
        uow=uow or _make_uow(),
        cache_service=cache,
        audit_service=audit,
        logger=MagicMock(),
    )


# Payloads ────────────────────────────────────────────────────────────────────

_CREATE_BY_CATEGORIA = OfferCreateRequest(
    nombre="Docena de Empanadas",
    descripcion="12 empanadas a elección",
    precio=Decimal("12000"),
    productos=[OfferItemRequest(categoria_id=1, cantidad=12)],
)

_CREATE_BY_PRODUCTOS = OfferCreateRequest(
    nombre="Combo Variado",
    precio=Decimal("10000"),
    productos=[
        OfferItemRequest(
            producto_opciones=[1, 2],
            cantidad=6,
        )
    ],
)

_CREATE_BY_PRODUCTO_ID = OfferCreateRequest(
    nombre="Media Docena",
    precio=Decimal("7000"),
    productos=[OfferItemRequest(producto_id=1, cantidad=6)],
)

_UPDATE_PRECIO = OfferUpdateRequest(precio=Decimal("13000"))
_UPDATE_NOMBRE = OfferUpdateRequest(nombre="Docena Premium")


# ══════════════════════════════════════════════════════════════════════════════
# create
# ══════════════════════════════════════════════════════════════════════════════

def bench_offer_create_by_categoria(benchmark, run_async):
    """Crear oferta especificando categoría (expande a productos)."""
    service = _make_service()

    async def call():
        return await service.create(_CREATE_BY_CATEGORIA, username="bench_user")

    benchmark(run_async, call)


def bench_offer_create_by_producto_id(benchmark, run_async):
    """Crear oferta con producto_id fijo."""
    service = _make_service()

    async def call():
        return await service.create(_CREATE_BY_PRODUCTO_ID, username="bench_user")

    benchmark(run_async, call)


def bench_offer_create_by_opciones(benchmark, run_async):
    """Crear oferta con lista de opciones de productos."""
    service = _make_service()

    async def call():
        return await service.create(_CREATE_BY_PRODUCTOS, username="bench_user")

    benchmark(run_async, call)


# ══════════════════════════════════════════════════════════════════════════════
# read
# ══════════════════════════════════════════════════════════════════════════════

def bench_offer_get_by_id_found(benchmark, run_async):
    """get_by_id cuando la oferta existe."""
    service = _make_service()

    async def call():
        return await service.get_by_id(1)

    benchmark(run_async, call)


def bench_offer_get_by_id_not_found(benchmark, run_async):
    """get_by_id cuando la oferta no existe."""
    uow = _make_uow()
    uow.offer_repo.get_by_id = AsyncMock(return_value=None)
    service = _make_service(uow)

    async def call():
        return await service.get_by_id(999)

    benchmark(run_async, call)


def bench_offer_get_all(benchmark, run_async):
    """Listar todas las ofertas."""
    service = _make_service()

    async def call():
        return await service.get_all()

    benchmark(run_async, call)


def bench_offer_get_all_active(benchmark, run_async):
    """Listar solo las ofertas activas."""
    service = _make_service()

    async def call():
        return await service.get_all(active=True)

    benchmark(run_async, call)


# ══════════════════════════════════════════════════════════════════════════════
# update / deactivate / delete
# ══════════════════════════════════════════════════════════════════════════════

def bench_offer_update_precio(benchmark, run_async):
    """Actualizar solo el precio de una oferta."""
    service = _make_service()

    async def call():
        return await service.update(1, offer_update=_UPDATE_PRECIO, username="bench_user")

    benchmark(run_async, call)


def bench_offer_deactivate(benchmark, run_async):
    """Desactivar una oferta (logical delete)."""
    service = _make_service()

    async def call():
        return await service.update(
            1, active=False, username="bench_user", is_logical_delete=True
        )

    benchmark(run_async, call)


def bench_offer_delete(benchmark, run_async):
    """Eliminar una oferta (hard delete)."""
    service = _make_service()

    async def call():
        return await service.delete(1)

    benchmark(run_async, call)


def bench_offer_deactivate_by_product(benchmark, run_async):
    """Desactivar todas las ofertas que incluyen un producto."""
    service = _make_service()

    async def call():
        return await service.deactivate_by_product(1, username="bench_user")

    benchmark(run_async, call)
