"""
bench_schemas.py — Benchmarks de validación/serialización Pydantic

Mide el overhead de model_validate, model_dump y la validación de campos
para los schemas más usados en la API.
"""

import pytest
from decimal import Decimal
from datetime import date, datetime, timezone
from typing import Optional

from app.presentation.schemas.sale_schemas import (
    SaleCreateRequest, SaleItemRequest, SaleUpdateRequest, SaleResponse,
    SaleListResponse, SelectedProduct, PizzaMitadMitadRequest,
)
from app.presentation.schemas.product_schemas import (
    ProductoCreateRequest, ProductoUpdateRequest, ProductoPrecioRequest,
    ProductoPrecioResponse, ProductoResponse,
    ActualizarPreciosMasivosRequest,
)
from app.presentation.schemas.offer_schemas import (
    OfferCreateRequest, OfferItemRequest, OfferUpdateRequest, OfferResponse,
    OfferItemResponse, ProductoOpcionSchema,
)
from app.presentation.schemas.expense_schemas import (
    GastoCreateRequest, GastoUpdateRequest, GastoResponse,
)
from app.presentation.schemas.expense_category_schemas import (
    GastoCategoriaCreateRequest, GastoCategoriaUpdateRequest,
    GastoCategoriaResponse,
)
from app.presentation.schemas.product_category_schemas import (
    ProductoCategoriaCreateRequest, ProductoCategoriaUpdateRequest,
    ProductoCategoriaResponse,
)
from app.presentation.schemas.user_schemas import (
    RegisterRequest, UpdateUserRequest, UserResponse, UserDetailResponse,
    UserListResponse,
)
from app.presentation.schemas.stock_schemas import (
    AddStockRequest, ConfigureAlertsRequest, CategoryStockResponse,
)
from app.presentation.schemas.audit_schemas import (
    AuditLogResponse, AuditHistoryResponse,
)


# ──────────────────────────────────────────────────────────────────────────────
# Raw dicts para construir desde dicts (model_validate)
# ──────────────────────────────────────────────────────────────────────────────

_SALE_CREATE_DICT = {
    "items": [
        {"producto_id": 1, "cantidad": 6},
        {"producto_id": 2, "cantidad": 1},
    ]
}

_SALE_PIZZA_MITAD_DICT = {
    "items": [
        {
            "cantidad": 1,
            "pizza_mitad_mitad": {
                "producto_id_izquierda": 1,
                "producto_id_derecha": 2,
                "cantidad": 1,
            },
        }
    ]
}

_PRODUCT_CREATE_DICT = {
    "nombre": "Empanada de Carne",
    "categoria_id": 1,
    "precios": [
        {"cantidad": 1, "precio": "1200"},
        {"cantidad": 6, "precio": "6000"},
        {"cantidad": 12, "precio": "10800"},
    ],
}

_OFFER_BY_CATEGORIA_DICT = {
    "nombre": "Docena Mixta",
    "precio": "12000",
    "productos": [{"categoria_id": 1, "cantidad": 12}],
}

_OFFER_BY_OPCIONES_DICT = {
    "nombre": "Combo Variado",
    "precio": "10000",
    "productos": [{"producto_opciones": [1, 2, 3], "cantidad": 6}],
}

_EXPENSE_CREATE_DICT = {
    "categoria_gasto_id": 1,
    "descripcion": "Compra de harina",
    "monto": 5000.0,
    "fecha_pago": "2026-03-11",
}

_USER_REGISTER_DICT = {
    "username": "newuser",
    "email": "new@example.com",
    "password": "TestPass1",
    "first_name": "Test",
    "last_name": "User",
}

_NOW = datetime.now(timezone.utc)

_PRODUCT_RESPONSE_DICT = {
    "id": 1,
    "sku": "EMP-CARNE-001",
    "nombre": "Empanada de Carne",
    "categoria_id": 1,
    "precios": [{"id": 1, "cantidad": 1, "precio": "1200"}],
    "imagen": None,
    "activo": True,
    "fecha_creacion": _NOW.isoformat(),
}

_SALE_RESPONSE_DICT = {
    "id": 1,
    "numero_venta": "V-0001",
    "total": "6000.00",
    "fecha_creacion": _NOW.isoformat(),
    "items": [
        {
            "id": 1,
            "producto_id": 1,
            "producto_nombre": "Empanada",
            "cantidad": 6,
            "precio_unitario": "1000.00",
            "subtotal": "6000.00",
        }
    ],
}


# ══════════════════════════════════════════════════════════════════════════════
# SaleCreateRequest / SaleItemRequest
# ══════════════════════════════════════════════════════════════════════════════

def bench_schema_sale_create_simple(benchmark):
    """Validar SaleCreateRequest con 1 item producto."""
    benchmark(SaleCreateRequest.model_validate, _SALE_CREATE_DICT)


def bench_schema_sale_create_pizza_mitad(benchmark):
    """Validar SaleCreateRequest con pizza mitad-mitad."""
    benchmark(SaleCreateRequest.model_validate, _SALE_PIZZA_MITAD_DICT)


def bench_schema_sale_create_10_items(benchmark):
    """Validar SaleCreateRequest con 10 items."""
    payload = {"items": [{"producto_id": i, "cantidad": 6} for i in range(1, 11)]}
    benchmark(SaleCreateRequest.model_validate, payload)


def bench_schema_sale_create_dump(benchmark):
    """model_dump de SaleCreateRequest."""
    obj = SaleCreateRequest.model_validate(_SALE_CREATE_DICT)
    benchmark(obj.model_dump)


# ══════════════════════════════════════════════════════════════════════════════
# ProductoCreateRequest
# ══════════════════════════════════════════════════════════════════════════════

def bench_schema_product_create(benchmark):
    """Validar ProductoCreateRequest con 3 precios."""
    benchmark(ProductoCreateRequest.model_validate, _PRODUCT_CREATE_DICT)


def bench_schema_product_create_dump(benchmark):
    """model_dump de ProductoCreateRequest."""
    obj = ProductoCreateRequest.model_validate(_PRODUCT_CREATE_DICT)
    benchmark(obj.model_dump)


def bench_schema_product_create_10_precios(benchmark):
    """Validar ProductoCreateRequest con 10 tramos de precio (edge case)."""
    payload = {
        "nombre": "Empanada Multitramo",
        "categoria_id": 1,
        "precios": [
            {"cantidad": 2 ** i, "precio": str(1200 * 2 ** i)}
            for i in range(10)
        ],
    }
    benchmark(ProductoCreateRequest.model_validate, payload)


# ══════════════════════════════════════════════════════════════════════════════
# ActualizarPreciosMasivosRequest
# ══════════════════════════════════════════════════════════════════════════════

def bench_schema_bulk_prices_monto(benchmark):
    """Validar ActualizarPreciosMasivosRequest con monto."""
    benchmark(ActualizarPreciosMasivosRequest.model_validate, {"monto": "100"})


def bench_schema_bulk_prices_porcentaje(benchmark):
    """Validar ActualizarPreciosMasivosRequest con porcentaje."""
    benchmark(
        ActualizarPreciosMasivosRequest.model_validate,
        {"porcentaje": "10", "categoria_ids": [1, 2, 3]},
    )


# ══════════════════════════════════════════════════════════════════════════════
# OfferCreateRequest
# ══════════════════════════════════════════════════════════════════════════════

def bench_schema_offer_create_categoria(benchmark):
    """Validar OfferCreateRequest por categoría."""
    benchmark(OfferCreateRequest.model_validate, _OFFER_BY_CATEGORIA_DICT)


def bench_schema_offer_create_opciones(benchmark):
    """Validar OfferCreateRequest por opciones de productos."""
    benchmark(OfferCreateRequest.model_validate, _OFFER_BY_OPCIONES_DICT)


# ══════════════════════════════════════════════════════════════════════════════
# GastoCreateRequest
# ══════════════════════════════════════════════════════════════════════════════

def bench_schema_expense_create(benchmark):
    """Validar GastoCreateRequest."""
    benchmark(GastoCreateRequest.model_validate, _EXPENSE_CREATE_DICT)


# ══════════════════════════════════════════════════════════════════════════════
# RegisterRequest (usuario)
# ══════════════════════════════════════════════════════════════════════════════

def bench_schema_user_register(benchmark):
    """Validar RegisterRequest."""
    benchmark(RegisterRequest.model_validate, _USER_REGISTER_DICT)


def bench_schema_user_update(benchmark):
    """Validar UpdateUserRequest (campos opcionales)."""
    benchmark(
        UpdateUserRequest.model_validate,
        {"first_name": "Nuevo", "last_name": "Apellido"},
    )


# ══════════════════════════════════════════════════════════════════════════════
# Stock schemas
# ══════════════════════════════════════════════════════════════════════════════

def bench_schema_add_stock(benchmark):
    """Validar AddStockRequest."""
    benchmark(AddStockRequest.model_validate, {"cantidad": 50})


def bench_schema_configure_alerts(benchmark):
    """Validar ConfigureAlertsRequest."""
    benchmark(
        ConfigureAlertsRequest.model_validate,
        {"umbral_amarillo": 30, "umbral_rojo": 10},
    )


# ══════════════════════════════════════════════════════════════════════════════
# AuditLogResponse (respuestas de solo lectura)
# ══════════════════════════════════════════════════════════════════════════════

def bench_schema_audit_log_response(benchmark):
    """Validar AuditLogResponse."""
    benchmark(
        AuditLogResponse.model_validate,
        {
            "id": 1,
            "timestamp": _NOW.isoformat(),
            "username": "admin",
            "entity_type": "Product",
            "entity_id": 1,
            "action": "UPDATE",
            "changes": {"nombre": {"old": "A", "new": "B"}},
        },
    )


def bench_schema_audit_history_response_100(benchmark):
    """Serializar AuditHistoryResponse con 100 registros."""
    records = [
        {
            "id": i,
            "timestamp": _NOW.isoformat(),
            "username": "admin",
            "entity_type": "Product",
            "entity_id": i,
            "action": "UPDATE",
            "changes": {"nombre": {"old": f"A{i}", "new": f"B{i}"}},
        }
        for i in range(100)
    ]
    benchmark(AuditHistoryResponse.model_validate, {"total": 100, "limit": 100, "offset": 0, "records": records})
