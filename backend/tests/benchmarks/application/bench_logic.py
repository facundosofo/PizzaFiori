"""
bench_logic.py — Benchmarks de lógica pura (sync, sin DB, sin async)

Cubre:
  - SaleService: pricing tiers, limpiar_nombre_pizza, _get_offer_price
  - StockService: _compute_estado
  - analytics_utils: get_start_date_for_time_filter (5 filtros)
  - audit_helpers: compute_entity_diff, compute_sale_diff
"""

import pytest
from decimal import Decimal
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from app.application.sale_service import SaleService
from app.application.stock_service import _compute_estado
from app.application.analytics_utils import get_start_date_for_time_filter
from app.presentation.schemas.dashboard_schemas import FiltroTiempo

# audit_helpers usa sqlalchemy.inspect → necesita instancias reales de modelos SA
from app.domain.models.product import Product
from app.domain.models.product_category import ProductCategory
from app.domain.models.expense import Expense
from app.domain.models.sale import Sale
from app.domain.models.sale_item import SaleItem
from app.application.utils.audit_helpers import compute_entity_diff, compute_sale_diff


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _make_service():
    return SaleService(uow=AsyncMock(), logger=MagicMock())


def _make_product_with_prices(precios: list) -> MagicMock:
    """Mock de producto con lista de precios (MagicMock para evitar acceso a BD)."""
    product = MagicMock()
    product.activo = True
    price_mocks = []
    for cantidad, precio in precios:
        p = MagicMock()
        p.cantidad = cantidad
        p.precio = Decimal(str(precio))
        price_mocks.append(p)
    product.precios = price_mocks
    return product


def _make_offer_mock(precio: float = 10000.0, activo: bool = True) -> MagicMock:
    oferta = MagicMock()
    oferta.activo = activo
    oferta.precio = Decimal(str(precio))
    return oferta


# Producto con 3 rangos de precio —————————
PRODUCT_3_TIERS = _make_product_with_prices([(1, 1200), (6, 6000), (12, 10800)])

# Entidades SQLAlchemy reales para compute_entity_diff
_OLD_PRODUCT = Product(
    id=1, sku="PIZZA-MUZZA-001", nombre="Pizza Muzzarella",
    categoria_id=1, activo=True,
    fecha_creacion=datetime(2026, 1, 1), fecha_actualizacion=datetime(2026, 1, 1),
)
_NEW_PRODUCT = Product(
    id=1, sku="PIZZA-MUZZA-001", nombre="Pizza Muzzarella ESPECIAL",
    categoria_id=2, activo=True,
    fecha_creacion=datetime(2026, 1, 1), fecha_actualizacion=datetime(2026, 3, 11),
)
_SAME_PRODUCT = Product(
    id=1, sku="PIZZA-MUZZA-001", nombre="Pizza Muzzarella",
    categoria_id=1, activo=True,
    fecha_creacion=datetime(2026, 1, 1), fecha_actualizacion=datetime(2026, 1, 1),
)


# ══════════════════════════════════════════════════════════════════════════════
# Pricing tiers — _get_product_price
# ══════════════════════════════════════════════════════════════════════════════

def bench_pricing_single_unit(benchmark):
    """Calcular precio para 1 unidad (aplica solo el rango mínimo)."""
    service = _make_service()
    benchmark(service._get_product_price, PRODUCT_3_TIERS, 1)


def bench_pricing_exact_tier(benchmark):
    """Calcular precio para 6 unidades (exact match del rango intermedio)."""
    service = _make_service()
    benchmark(service._get_product_price, PRODUCT_3_TIERS, 6)


def bench_pricing_exact_top_tier(benchmark):
    """Calcular precio para 12 unidades (exact match del rango mayor)."""
    service = _make_service()
    benchmark(service._get_product_price, PRODUCT_3_TIERS, 12)


def bench_pricing_mixed_tiers(benchmark):
    """Calcular precio para 13 = 12+1 (usa dos rangos)."""
    service = _make_service()
    benchmark(service._get_product_price, PRODUCT_3_TIERS, 13)


def bench_pricing_large_quantity(benchmark):
    """Calcular precio para 37 = 3×12+1 (múltiples aplicaciones del rango mayor)."""
    service = _make_service()
    benchmark(service._get_product_price, PRODUCT_3_TIERS, 37)


def bench_pricing_no_prices(benchmark):
    """Producto sin precios configurados → retorna None rápido."""
    service = _make_service()
    product = MagicMock()
    product.activo = True
    product.precios = []
    benchmark(service._get_product_price, product, 6)


def bench_pricing_inactive_product(benchmark):
    """Producto inactivo → retorna None rápido (early exit)."""
    service = _make_service()
    product = MagicMock()
    product.activo = False
    benchmark(service._get_product_price, product, 6)


# ══════════════════════════════════════════════════════════════════════════════
# limpiar_nombre_pizza
# ══════════════════════════════════════════════════════════════════════════════

def bench_pizza_name_with_prefix_pizza(benchmark):
    """Eliminar prefijo 'Pizza ' — caso más común."""
    service = _make_service()
    benchmark(service.limpiar_nombre_pizza, "Pizza Muzzarella")


def bench_pizza_name_with_prefix_pizza_de(benchmark):
    """Eliminar prefijo 'Pizza de '."""
    service = _make_service()
    benchmark(service.limpiar_nombre_pizza, "Pizza de Anchoas")


def bench_pizza_name_with_prefix_pizza_con(benchmark):
    """Eliminar prefijo 'Pizza con '."""
    service = _make_service()
    benchmark(service.limpiar_nombre_pizza, "Pizza con Rúcula y Crudo")


def bench_pizza_name_no_prefix(benchmark):
    """Nombre sin prefijo — regex.sub igual se ejecuta."""
    service = _make_service()
    benchmark(service.limpiar_nombre_pizza, "Empanada de Carne")


def bench_pizza_name_empty(benchmark):
    """String vacío — early exit."""
    service = _make_service()
    benchmark(service.limpiar_nombre_pizza, "")


# ══════════════════════════════════════════════════════════════════════════════
# _get_offer_price
# ══════════════════════════════════════════════════════════════════════════════

def bench_offer_price_active(benchmark):
    service = _make_service()
    oferta = _make_offer_mock(precio=10000.0, activo=True)
    benchmark(service._get_offer_price, oferta)


def bench_offer_price_inactive(benchmark):
    service = _make_service()
    oferta = _make_offer_mock(precio=10000.0, activo=False)
    benchmark(service._get_offer_price, oferta)


# ══════════════════════════════════════════════════════════════════════════════
# _compute_estado (StockService)
# ══════════════════════════════════════════════════════════════════════════════

def bench_compute_estado_ok(benchmark):
    benchmark(_compute_estado, 100, 10, 5)


def bench_compute_estado_warning(benchmark):
    benchmark(_compute_estado, 8, 10, 5)


def bench_compute_estado_critical(benchmark):
    benchmark(_compute_estado, 3, 10, 5)


def bench_compute_estado_sin_stock(benchmark):
    benchmark(_compute_estado, 0, 10, 5)


def bench_compute_estado_no_thresholds(benchmark):
    """Estado sin umbrales configurados (umbral_amarillo=None)."""
    benchmark(_compute_estado, 50, None, None)


# ══════════════════════════════════════════════════════════════════════════════
# analytics_utils — get_start_date_for_time_filter
# ══════════════════════════════════════════════════════════════════════════════

def bench_time_filter_hoy(benchmark):
    benchmark(get_start_date_for_time_filter, FiltroTiempo.HOY)


def bench_time_filter_7_dias(benchmark):
    benchmark(get_start_date_for_time_filter, FiltroTiempo.ULTIMOS_7_DIAS)


def bench_time_filter_ultimo_mes(benchmark):
    benchmark(get_start_date_for_time_filter, FiltroTiempo.ULTIMO_MES)


def bench_time_filter_ultimo_ano(benchmark):
    benchmark(get_start_date_for_time_filter, FiltroTiempo.ULTIMO_ANO)


def bench_time_filter_historico(benchmark):
    """HISTORICO retorna None sin calculo — debería ser el más rápido."""
    benchmark(get_start_date_for_time_filter, FiltroTiempo.HISTORICO)


# ══════════════════════════════════════════════════════════════════════════════
# audit_helpers — compute_entity_diff
# ══════════════════════════════════════════════════════════════════════════════

def bench_entity_diff_with_changes(benchmark):
    """Diff de Product con 2 campos cambiados (nombre + categoria_id)."""
    benchmark(compute_entity_diff, _OLD_PRODUCT, _NEW_PRODUCT)


def bench_entity_diff_no_changes(benchmark):
    """Diff de Product idéntico — iterar todas las columnas sin encontrar diferencias."""
    benchmark(compute_entity_diff, _OLD_PRODUCT, _SAME_PRODUCT)


def bench_entity_diff_expense(benchmark):
    """Diff de Expense — entidad con menos columnas."""
    old = Expense(
        id=1, categoria_gasto_id=1, descripcion="Harina",
        monto=Decimal("5000.00"), activo=True,
    )
    new = Expense(
        id=1, categoria_gasto_id=2, descripcion="Harina premium",
        monto=Decimal("6500.00"), activo=True,
    )
    benchmark(compute_entity_diff, old, new)


def bench_entity_diff_with_exclude(benchmark):
    """Diff con campos excluidos explícitamente."""
    benchmark(compute_entity_diff, _OLD_PRODUCT, _NEW_PRODUCT, {"id", "sku"})


# ══════════════════════════════════════════════════════════════════════════════
# audit_helpers — compute_sale_diff
# ══════════════════════════════════════════════════════════════════════════════

def _make_sale_with_items(n_items: int) -> Sale:
    """Crea un objeto Sale con N SaleItems usando constructores SA."""
    sale = Sale(id=1, numero_orden="2026-0001", total=Decimal("12000.00"))
    sale.items = [
        SaleItem(
            id=i,
            venta_id=1,
            producto_id=i,
            cantidad=6,
            precio_unitario=Decimal("1000.00"),
            subtotal=Decimal("6000.00"),
            item_nombre=f"Producto {i}",
            item_categoria="Empanadas",
        )
        for i in range(1, n_items + 1)
    ]
    return sale


def bench_sale_diff_same(benchmark):
    """Diff de venta idéntica — útil como baseline."""
    old = _make_sale_with_items(3)
    new = _make_sale_with_items(3)
    benchmark(compute_sale_diff, old, new)


def bench_sale_diff_3_items(benchmark):
    """Diff de venta con 3 items, total cambia."""
    old = _make_sale_with_items(3)
    new = _make_sale_with_items(3)
    new.total = Decimal("15000.00")
    benchmark(compute_sale_diff, old, new)


def bench_sale_diff_10_items(benchmark):
    """Diff de venta con 10 items — mide costo de recorrer más items."""
    old = _make_sale_with_items(10)
    new = _make_sale_with_items(10)
    new.total = Decimal("50000.00")
    benchmark(compute_sale_diff, old, new)
