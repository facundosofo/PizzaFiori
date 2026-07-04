"""
Helper functions and data builders for tests.
Provides reusable functions to create test data objects.
"""

from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Any, Optional
from unittest.mock import MagicMock

# ==================== Category Builders ====================

def build_category_data(
    id: int = 1,
    nombre: str = "Empanadas",
    descripcion: Optional[str] = "Empanadas artesanales"
) -> Dict[str, Any]:
    """Build category data dictionary for testing."""
    return {
        "id": id,
        "nombre": nombre,
        "descripcion": descripcion
    }


def build_category_model(
    id: int = 1,
    nombre: str = "Empanadas",
    descripcion: Optional[str] = "Empanadas artesanales"
) -> MagicMock:
    """Build mock Category model instance."""
    category = MagicMock()
    category.id = id
    category.nombre = nombre
    category.descripcion = descripcion
    category.stock_por_producto = False
    return category


# ==================== Product Builders ====================

def build_product_price_data(
    id: int = 1,
    producto_id: int = 1,
    cantidad: int = 1,
    precio: float = 1200.0
) -> Dict[str, Any]:
    """Build product price data dictionary."""
    return {
        "id": id,
        "producto_id": producto_id,
        "cantidad": Decimal(str(cantidad)),
        "precio": precio
    }


def build_product_data(
    id: int = 1,
    nombre: str = "Empanada de Carne",
    categoria_id: int = 1,
    sku: str = "EMPA-CARN-001",
    imagen: Optional[str] = None,
    activo: bool = True,
    precios: Optional[List[Dict]] = None
) -> Dict[str, Any]:
    """Build product data dictionary for testing."""
    if precios is None:
        precios = [
            {"cantidad": 1, "precio": 1200.0},
            {"cantidad": 6, "precio": 6000.0},
            {"cantidad": 12, "precio": 10800.0}
        ]
    
    return {
        "id": id,
        "sku": sku,
        "nombre": nombre,
        "categoria_id": categoria_id,
        "imagen": imagen,
        "activo": activo,
        "fecha_creacion": datetime.now(),
        "fecha_actualizacion": datetime.now(),
        "precios": precios
    }


def build_product_model(
    id: int = 1,
    nombre: str = "Empanada de Carne",
    categoria_id: int = 1,
    sku: str = "EMPA-CARN-001",
    imagen: Optional[str] = None,
    activo: bool = True,
    precios: Optional[List] = None
) -> MagicMock:
    """Build mock Product model instance."""
    product = MagicMock()
    product.id = id
    product.sku = sku
    product.nombre = nombre
    product.categoria_id = categoria_id
    product.imagen = imagen
    product.activo = activo
    product.fecha_creacion = datetime.now()
    product.fecha_actualizacion = datetime.now()
    
    if precios is None:
        precios = [
            build_product_price_model(1, id, 1, 1200.0),
            build_product_price_model(2, id, 6, 6000.0),
            build_product_price_model(3, id, 12, 10800.0)
        ]
    
    product.precios = precios
    product.categoria = None
    return product


def build_product_price_model(
    id: int = 1,
    producto_id: int = 1,
    cantidad: int = 1,
    precio: float = 1200.0
) -> MagicMock:
    """Build mock ProductPrice model instance."""
    price = MagicMock()
    price.id = id
    price.producto_id = producto_id
    price.cantidad = Decimal(str(cantidad))
    price.precio = Decimal(str(precio))
    price.fecha_creacion = datetime.now()
    price.fecha_actualizacion = datetime.now()
    return price


# ==================== Offer Builders ====================

def build_offer_item_data(
    producto_id: int = 1,
    cantidad: int = 6
) -> Dict[str, Any]:
    """Build offer item data dictionary."""
    return {
        "producto_id": producto_id,
        "cantidad": cantidad
    }


def build_offer_data(
    id: int = 1,
    nombre: str = "Promo Docena",
    descripcion: Optional[str] = "12 empanadas surtidas",
    precio: float = 10000.0,
    activo: bool = True,
    productos: Optional[List[Dict]] = None
) -> Dict[str, Any]:
    """Build offer data dictionary for testing."""
    if productos is None:
        productos = [
            {"producto_id": 1, "cantidad": 6},
            {"producto_id": 2, "cantidad": 6}
        ]
    
    return {
        "id": id,
        "nombre": nombre,
        "descripcion": descripcion,
        "precio": precio,
        "activo": activo,
        "fecha_creacion": datetime.now(),
        "fecha_actualizacion": datetime.now(),
        "productos": productos
    }


def build_offer_model(
    id: int = 1,
    nombre: str = "Promo Docena",
    descripcion: Optional[str] = "12 empanadas surtidas",
    precio: float = 10000.0,
    activo: bool = True,
    productos: Optional[List] = None
) -> MagicMock:
    """Build mock Offer model instance."""
    offer = MagicMock()
    offer.id = id
    offer.nombre = nombre
    offer.descripcion = descripcion
    offer.precio = Decimal(str(precio))
    offer.activo = activo
    offer.fecha_creacion = datetime.now()
    offer.fecha_actualizacion = datetime.now()
    
    if productos is None:
        productos = [
            build_offer_item_model(id=1, oferta_id=id, productos=[build_product_model(id=1)], cantidad=6),
            build_offer_item_model(id=2, oferta_id=id, productos=[build_product_model(id=2)], cantidad=6)
        ]
    
    offer.productos = productos
    return offer


def build_offer_item_model(
    id: int = 1,
    oferta_id: int = 1,
    categoria_id: Optional[int] = None,
    cantidad: int = 6,
    categoria_nombre: Optional[str] = None,
    productos: Optional[List] = None
) -> MagicMock:
    """Build mock OfferItem model instance."""
    item = MagicMock()
    item.id = id
    item.oferta_id = oferta_id
    item.categoria_id = categoria_id
    item.cantidad = cantidad
    item.categoria_nombre = categoria_nombre
    item.productos = productos or []
    return item


# ==================== Sale Builders ====================

def build_sale_item_data(
    producto_id: Optional[int] = 1,
    oferta_id: Optional[int] = None,
    cantidad: int = 6,
    precio_unitario: float = 1000.0,
    subtotal: float = 6000.0
) -> Dict[str, Any]:
    """Build sale item data dictionary."""
    return {
        "producto_id": producto_id,
        "oferta_id": oferta_id,
        "cantidad": cantidad,
        "precio_unitario": precio_unitario,
        "subtotal": subtotal
    }


def build_sale_data(
    id: int = 1,
    numero_orden: Optional[str] = "ORD-001",
    total: float = 6000.0,
    items: Optional[List[Dict]] = None
) -> Dict[str, Any]:
    """Build sale data dictionary for testing."""
    if items is None:
        items = [
            {
                "producto_id": 1,
                "oferta_id": None,
                "cantidad": 6,
                "precio_unitario": 1000.0,
                "subtotal": 6000.0
            }
        ]
    
    return {
        "id": id,
        "numero_orden": numero_orden,
        "total": total,
        "fecha_creacion": datetime.now(),
        "fecha_actualizacion": datetime.now(),
        "items": items
    }


def build_sale_model(
    id: int = 1,
    numero_orden: Optional[str] = "ORD-001",
    total: float = 6000.0,
    items: Optional[List] = None
) -> MagicMock:
    """Build mock Sale model instance."""
    sale = MagicMock()
    sale.id = id
    sale.numero_orden = numero_orden
    sale.total = Decimal(str(total))
    sale.fecha_creacion = datetime.now()
    sale.fecha_actualizacion = datetime.now()
    
    if items is None:
        items = [
            build_sale_item_model(1, id, 1, None, 6, 1000.0, 6000.0)
        ]
    
    sale.items = items
    sale.porcentaje_recargo = None
    sale.monto_recargo = None
    sale.total_items = sum((getattr(item, 'cantidad', 0) or 0) for item in items)
    return sale


def build_sale_item_model(
    id: int = 1,
    venta_id: int = 1,
    producto_id: Optional[int] = 1,
    oferta_id: Optional[int] = None,
    cantidad: int = 6,
    precio_unitario: float = 1000.0,
    subtotal: float = 6000.0,
    producto_sku: Optional[str] = "EMPA-CARN-001",
    item_nombre: str = "Empanada de Carne",
    item_categoria: str = "Empanadas",
    item_descripcion: Optional[str] = None,
    oferta_productos_snapshot: Optional[List] = None
) -> MagicMock:
    """Build mock SaleItem model instance."""
    item = MagicMock()
    item.id = id
    item.venta_id = venta_id
    item.producto_id = producto_id
    item.oferta_id = oferta_id
    item.cantidad = cantidad
    item.precio_unitario = Decimal(str(precio_unitario))
    item.subtotal = Decimal(str(subtotal))
    item.producto_sku = producto_sku
    item.item_nombre = item_nombre
    item.item_categoria = item_categoria
    item.item_descripcion = item_descripcion
    item.oferta_productos_snapshot = oferta_productos_snapshot or []
    return item


def build_sale_item_offer_product_model(
    id: int = 1,
    venta_item_id: int = 1,
    producto_id: Optional[int] = 1,
    producto_nombre: str = "Empanada de Carne",
    categoria_nombre: Optional[str] = "Empanadas",
    cantidad: int = 6
) -> MagicMock:
    """Build mock SaleItemOfferProduct model instance."""
    snapshot = MagicMock()
    snapshot.id = id
    snapshot.venta_item_id = venta_item_id
    snapshot.producto_id = producto_id
    snapshot.producto_nombre = producto_nombre
    snapshot.categoria_nombre = categoria_nombre
    snapshot.cantidad = cantidad
    return snapshot


# ==================== Assertion Helpers ====================

def assert_service_result(result, expected_status: int, expected_data: Any = None):
    """Assert that a ServiceResult has the expected status and data."""
    assert result.status_code == expected_status, \
        f"Expected status {expected_status}, got {result.status_code}"
    
    if expected_data is not None:
        assert result.data == expected_data, \
            f"Expected data {expected_data}, got {result.data}"


def assert_mock_called_once(mock, method_name: str):
    """Assert that a mock method was called exactly once."""
    method = getattr(mock, method_name)
    assert method.call_count == 1, \
        f"Expected {method_name} to be called once, but was called {method.call_count} times"


# ==================== User Builders ====================

def build_user_data(
    id: int = 1,
    username: str = "testuser",
    email: str = "test@example.com",
    first_name: str = "Test",
    last_name: str = "User",
    role: str = "USER",
) -> Dict[str, Any]:
    """Build user data dictionary for testing."""
    return {
        "id": id,
        "username": username,
        "email": email,
        "first_name": first_name,
        "last_name": last_name,
        "role": role,
    }


def build_user_model(
    id: int = 1,
    username: str = "testuser",
    email: str = "test@example.com",
    password_hash: str = "$2b$12$fakehash",
    first_name: str = "Test",
    last_name: str = "User",
    role: str = "USER",
    failed_login_attempts: int = 0,
    locked_until: Optional[Any] = None,
) -> MagicMock:
    """Build mock User model instance."""
    user = MagicMock()
    user.id = id
    user.username = username
    user.email = email
    user.password_hash = password_hash
    user.first_name = first_name
    user.last_name = last_name
    user.role = role
    user.failed_login_attempts = failed_login_attempts
    user.locked_until = locked_until
    user.created_at = datetime.now()
    user.updated_at = datetime.now()
    return user


# ==================== Expense Builders ====================

def build_expense_data(
    id: int = 1,
    categoria_gasto_id: int = 1,
    descripcion: str = "Compra de harina",
    monto: float = 5000.0,
    fecha_pago: Optional[Any] = None,
) -> Dict[str, Any]:
    """Build expense data dictionary for testing."""
    from datetime import date as date_type
    return {
        "id": id,
        "categoria_gasto_id": categoria_gasto_id,
        "descripcion": descripcion,
        "monto": monto,
        "fecha_pago": fecha_pago or date_type.today(),
    }


def build_expense_model(
    id: int = 1,
    categoria_gasto_id: int = 1,
    descripcion: str = "Compra de harina",
    monto: float = 5000.0,
    fecha_pago: Optional[Any] = None,
    activo: bool = True,
) -> MagicMock:
    """Build mock Expense model instance."""
    from datetime import date as date_type
    expense = MagicMock()
    expense.id = id
    expense.categoria_gasto_id = categoria_gasto_id
    expense.descripcion = descripcion
    expense.monto = Decimal(str(monto))
    expense.fecha_pago = fecha_pago or date_type.today()
    expense.activo = activo
    expense.fecha_creacion = datetime.now()
    expense.fecha_actualizacion = datetime.now()
    expense.categoria_gasto = None
    return expense


# ==================== Expense Category Builders ====================

def build_expense_category_data(
    id: int = 1,
    nombre: str = "Insumos",
    padre_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Build expense category data dictionary for testing."""
    return {
        "id": id,
        "nombre": nombre,
        "padre_id": padre_id,
    }


def build_expense_category_model(
    id: int = 1,
    nombre: str = "Insumos",
    padre_id: Optional[int] = None,
    activo: bool = True,
) -> MagicMock:
    """Build mock ExpenseCategory model instance."""
    cat = MagicMock()
    cat.id = id
    cat.nombre = nombre
    cat.padre_id = padre_id
    cat.activo = activo
    cat.fecha_creacion = datetime.now()
    cat.fecha_actualizacion = datetime.now()
    cat.subcategorias = []
    cat.gastos = []
    return cat


# ==================== Audit Log Builders ====================

def build_audit_log_model(
    id: int = 1,
    username: str = "admin",
    entity_type: str = "Product",
    entity_id: int = 1,
    action: str = "CREATE",
    changes: Optional[Dict] = None,
) -> MagicMock:
    """Build mock AuditLog model instance."""
    log = MagicMock()
    log.id = id
    log.timestamp = datetime.now()
    log.username = username
    log.entity_type = entity_type
    log.entity_id = entity_id
    log.action = action
    log.changes = changes or {"new": {"id": entity_id}}
    return log


# ==================== Stock Builders ====================

def build_stock_model(
    categoria_id: int = 1,
    cantidad: int = 50,
    umbral_amarillo: Optional[int] = 10,
    umbral_rojo: Optional[int] = 5,
) -> MagicMock:
    """Build mock CategoryStock model instance."""
    stock = MagicMock()
    stock.categoria_id = categoria_id
    stock.cantidad = cantidad
    stock.umbral_amarillo = umbral_amarillo
    stock.umbral_rojo = umbral_rojo
    stock.fecha_actualizacion = datetime.now()
    return stock
