"""
bench_services_sale.py — Benchmarks del SaleService (async, repos mockeados)

Mide el overhead Python del servicio: validaciones, construcción de modelos,
lógica de negocio y llamadas al UoW — sin latencia de BD real.
"""

import pytest
import asyncio
from decimal import Decimal
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

from app.application.sale_service import SaleService
from app.presentation.schemas.sale_schemas import (
    SaleCreateRequest, SaleItemRequest, SaleUpdateRequest,
    SelectedProduct, PizzaMitadMitadRequest,
)
from tests.helpers import (
    build_product_model, build_offer_model, build_sale_model,
    build_sale_item_model, build_product_price_model,
)


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _make_uow(product=None, offer=None, sale=None, sequence_value=1):
    """Construye un UoW mock con repos pre-configurados."""
    uow = AsyncMock()
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock(return_value=None)
    uow.commit = AsyncMock()
    uow.rollback = AsyncMock()

    # Producto por defecto con precios
    default_product = product or build_product_model(
        id=1, nombre="Empanada de Carne", categoria_id=1,
        precios=[
            build_product_price_model(1, 1, 1, 1200.0),
            build_product_price_model(2, 1, 6, 6000.0),
            build_product_price_model(3, 1, 12, 10800.0),
        ]
    )
    uow.product_repo.get_by_id = AsyncMock(return_value=default_product)
    uow.product_repo.get_by_ids = AsyncMock(return_value=[default_product])

    # Ofertas
    default_offer = offer or build_offer_model(id=1, precio=10000.0)
    uow.offer_repo.get_by_id = AsyncMock(return_value=default_offer)

    # Ventas
    default_sale = sale or build_sale_model(id=1, total=6000.0)
    uow.sale_repo.get_by_id = AsyncMock(return_value=default_sale)
    uow.sale_repo.add = AsyncMock(return_value=None)
    uow.sale_repo.update = AsyncMock(return_value=None)
    uow.sale_repo.delete = AsyncMock(return_value=None)
    uow.sale_repo.list = AsyncMock(return_value=[default_sale])
    uow.sale_repo.count = AsyncMock(return_value=1)
    uow.sale_repo.get_distinct_years = AsyncMock(return_value=[2025, 2026])

    # Sequence
    seq = MagicMock()
    seq.last_value = sequence_value
    uow.sequence_repo.get_for_update = AsyncMock(return_value=seq)
    uow.sequence_repo.create = AsyncMock(return_value=None)
    uow.sequence_repo.update = AsyncMock(return_value=None)

    # Audit repo
    uow.audit_repo.log_action = AsyncMock(return_value=MagicMock(id=1))

    # Stock repo
    uow.stock_repo.get_by_categoria_id = AsyncMock(return_value=None)
    uow.stock_repo.upsert = AsyncMock(return_value=None)

    # Product category
    cat = MagicMock()
    cat.id = 1
    cat.nombre = "Empanadas"
    uow.product_category_repo.get_by_id = AsyncMock(return_value=cat)
    uow.product_category_repo.list_by_active = AsyncMock(return_value=[cat])

    return uow


def _make_service(uow=None):
    audit = AsyncMock()
    audit.log_creation = AsyncMock(return_value=MagicMock(error=None))
    audit.log_update = AsyncMock(return_value=MagicMock(error=None))
    audit.log_deletion = AsyncMock(return_value=MagicMock(error=None))
    return SaleService(uow=uow or _make_uow(), audit_service=audit, logger=MagicMock())


# ──────────────────────────────────────────────────────────────────────────────
# Payloads
# ──────────────────────────────────────────────────────────────────────────────

_PAYLOAD_SOLO_PRODUCTO = SaleCreateRequest(
    items=[SaleItemRequest(producto_id=1, cantidad=6)]
)

_PAYLOAD_CON_OFERTA = SaleCreateRequest(
    items=[SaleItemRequest(
        oferta_id=1, cantidad=1,
        productos_seleccionados=[
            SelectedProduct(producto_id=1, cantidad=6),
            SelectedProduct(producto_id=2, cantidad=6),
        ]
    )]
)

_PAYLOAD_PIZZA_MITAD = SaleCreateRequest(
    items=[SaleItemRequest(
        cantidad=1,
        pizza_mitad_mitad=PizzaMitadMitadRequest(
            producto_id_izquierda=1, producto_id_derecha=2, cantidad=1
        ),
    )]
)

_PAYLOAD_UPDATE = SaleUpdateRequest(
    items=[SaleItemRequest(producto_id=1, cantidad=6, precio_unitario=Decimal("1000.00"))]
)


# ══════════════════════════════════════════════════════════════════════════════
# create
# ══════════════════════════════════════════════════════════════════════════════

def bench_sale_create_solo_producto(benchmark, run_async):
    """Crear venta con un producto individual."""
    service = _make_service()

    async def call():
        return await service.create(_PAYLOAD_SOLO_PRODUCTO, username="bench_user")

    benchmark(run_async, call)


def bench_sale_create_multiple_productos(benchmark, run_async):
    """Crear venta con 3 productos distintos."""
    service = _make_service()
    payload = SaleCreateRequest(items=[
        SaleItemRequest(producto_id=1, cantidad=6),
        SaleItemRequest(producto_id=1, cantidad=12),
        SaleItemRequest(producto_id=1, cantidad=1),
    ])

    async def call():
        return await service.create(payload, username="bench_user")

    benchmark(run_async, call)


def bench_sale_create_con_oferta(benchmark, run_async):
    """Crear venta con una oferta (valida productos_seleccionados)."""
    service = _make_service()

    async def call():
        return await service.create(_PAYLOAD_CON_OFERTA, username="bench_user")

    benchmark(run_async, call)


def bench_sale_create_pizza_mitad_mitad(benchmark, run_async):
    """Crear venta con pizza mitad-mitad."""
    service = _make_service()
    # Para pizza mitad-mitad necesitamos dos productos distintos con precios
    p2 = build_product_model(
        id=2, nombre="Pizza Napolitana", categoria_id=1,
        precios=[build_product_price_model(1, 2, 1, 1200.0)]
    )
    uow = _make_uow()
    uow.product_repo.get_by_ids = AsyncMock(return_value=[
        build_product_model(id=1, precios=[build_product_price_model(1, 1, 1, 1200.0)]),
        p2,
    ])
    service = _make_service(uow)

    async def call():
        return await service.create(_PAYLOAD_PIZZA_MITAD, username="bench_user")

    benchmark(run_async, call)


# ══════════════════════════════════════════════════════════════════════════════
# get_by_id
# ══════════════════════════════════════════════════════════════════════════════

def bench_sale_get_by_id_found(benchmark, run_async):
    """get_by_id() cuando la venta existe."""
    service = _make_service()

    async def call():
        return await service.get_by_id(1)

    benchmark(run_async, call)


def bench_sale_get_by_id_not_found(benchmark, run_async):
    """get_by_id() cuando la venta no existe (retorna 404)."""
    uow = _make_uow()
    uow.sale_repo.get_by_id = AsyncMock(return_value=None)
    service = _make_service(uow)

    async def call():
        return await service.get_by_id(999)

    benchmark(run_async, call)


# ══════════════════════════════════════════════════════════════════════════════
# get_all / count_all
# ══════════════════════════════════════════════════════════════════════════════

def bench_sale_get_all_no_filter(benchmark, run_async):
    """Listar ventas sin filtros de fecha."""
    service = _make_service()

    async def call():
        return await service.get_all(skip=0, limit=100)

    benchmark(run_async, call)


def bench_sale_get_all_date_filter(benchmark, run_async):
    """Listar ventas con rango de fechas."""
    service = _make_service()
    desde = date(2026, 1, 1)
    hasta = date(2026, 3, 11)

    async def call():
        return await service.get_all(skip=0, limit=100, fecha_desde=desde, fecha_hasta=hasta)

    benchmark(run_async, call)


def bench_sale_count_all(benchmark, run_async):
    """Contar ventas sin filtro."""
    service = _make_service()

    async def call():
        return await service.count_all()

    benchmark(run_async, call)


def bench_sale_get_available_years(benchmark, run_async):
    """Obtener años disponibles."""
    service = _make_service()

    async def call():
        return await service.get_available_years()

    benchmark(run_async, call)


# ══════════════════════════════════════════════════════════════════════════════
# update / delete
# ══════════════════════════════════════════════════════════════════════════════

def bench_sale_update(benchmark, run_async):
    """Actualizar venta existente."""
    service = _make_service()

    async def call():
        return await service.update(1, _PAYLOAD_UPDATE, username="bench_user")

    benchmark(run_async, call)


def bench_sale_delete(benchmark, run_async):
    """Eliminar venta."""
    service = _make_service()

    async def call():
        return await service.delete(1, username="bench_user")

    benchmark(run_async, call)


def bench_sale_delete_not_found(benchmark, run_async):
    """Eliminar venta inexistente (retorna 404)."""
    uow = _make_uow()
    uow.sale_repo.get_by_id = AsyncMock(return_value=None)
    service = _make_service(uow)

    async def call():
        return await service.delete(999, username="bench_user")

    benchmark(run_async, call)
