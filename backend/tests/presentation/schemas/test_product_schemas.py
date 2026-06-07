"""
Tests for product schemas validation.
Tests Pydantic models for products including tiered pricing validation.
"""

import pytest
from decimal import Decimal
from pydantic import ValidationError

from app.presentation.schemas.product_schemas import (
    ProductoPrecioRequest,
    ProductoCreateRequest,
    ProductoUpdateRequest,
    ProductoResponse,
    ActualizarPreciosMasivosRequest,
)


# ==================== ProductoPrecioRequest Tests ====================

def test_precio_request_valid():
    """Test creating a valid price tier."""
    data = {
        "cantidad": 6,
        "precio": Decimal("6000.00")
    }
    
    precio = ProductoPrecioRequest(**data)
    
    assert precio.cantidad == 6
    assert precio.precio == Decimal("6000.00")


def test_precio_request_negative_cantidad():
    """Test that negative cantidad is rejected."""
    data = {
        "cantidad": -1,
        "precio": Decimal("1000.00")
    }
    
    with pytest.raises(ValidationError) as exc_info:
        ProductoPrecioRequest(**data)
    
    errors = exc_info.value.errors()
    assert len(errors) > 0


def test_precio_request_zero_cantidad():
    """Test that zero cantidad is rejected."""
    data = {
        "cantidad": 0,
        "precio": Decimal("1000.00")
    }
    
    with pytest.raises(ValidationError) as exc_info:
        ProductoPrecioRequest(**data)
    
    errors = exc_info.value.errors()
    assert len(errors) > 0


def test_precio_request_negative_precio():
    """Test that negative precio is rejected."""
    data = {
        "cantidad": 1,
        "precio": Decimal("-100.00")
    }
    
    with pytest.raises(ValidationError) as exc_info:
        ProductoPrecioRequest(**data)
    
    errors = exc_info.value.errors()
    assert len(errors) > 0


def test_precio_request_zero_precio():
    """Test that zero precio is rejected."""
    data = {
        "cantidad": 1,
        "precio": Decimal("0.00")
    }
    
    with pytest.raises(ValidationError) as exc_info:
        ProductoPrecioRequest(**data)
    
    errors = exc_info.value.errors()
    assert len(errors) > 0


# ==================== ProductoCreateRequest Tests ====================

def test_create_producto_valid():
    """Test creating a valid product with tiered pricing."""
    data = {
        "nombre": "Empanada de Carne",
        "categoria_id": 1,
        "precios": [
            {"cantidad": 1, "precio": Decimal("1200.00")},
            {"cantidad": 6, "precio": Decimal("6000.00")},
            {"cantidad": 12, "precio": Decimal("10800.00")}
        ]
    }
    
    producto = ProductoCreateRequest(**data)
    
    assert producto.nombre == "Empanada de Carne"
    assert producto.categoria_id == 1
    assert len(producto.precios) == 3


def test_create_producto_single_price():
    """Test creating product with only unit price."""
    data = {
        "nombre": "Pizza Muzzarella",
        "categoria_id": 2,
        "precios": [
            {"cantidad": 1, "precio": Decimal("5000.00")}
        ]
    }
    
    producto = ProductoCreateRequest(**data)
    
    assert producto.nombre == "Pizza Muzzarella"
    assert len(producto.precios) == 1
    assert producto.precios[0].cantidad == 1


def test_create_producto_missing_unit_price():
    """Test that product without unit price (cantidad=1) is rejected."""
    data = {
        "nombre": "Empanada",
        "categoria_id": 1,
        "precios": [
            {"cantidad": 6, "precio": Decimal("6000.00")},
            {"cantidad": 12, "precio": Decimal("10800.00")}
        ]
    }
    
    with pytest.raises(ValidationError) as exc_info:
        ProductoCreateRequest(**data)
    
    errors = exc_info.value.errors()
    assert len(errors) > 0
    assert any("precio unitario" in str(error.get("ctx", {}).get("error", "")).lower() 
               for error in errors)


def test_create_producto_duplicate_quantities():
    """Test that duplicate quantities are rejected."""
    data = {
        "nombre": "Empanada",
        "categoria_id": 1,
        "precios": [
            {"cantidad": 1, "precio": Decimal("1200.00")},
            {"cantidad": 6, "precio": Decimal("6000.00")},
            {"cantidad": 6, "precio": Decimal("6500.00")}  # Duplicado
        ]
    }
    
    with pytest.raises(ValidationError) as exc_info:
        ProductoCreateRequest(**data)
    
    errors = exc_info.value.errors()
    assert len(errors) > 0
    assert any("duplicad" in str(error.get("ctx", {}).get("error", "")).lower() 
               for error in errors)


def test_create_producto_empty_precios():
    """Test that empty precios list is rejected."""
    data = {
        "nombre": "Empanada",
        "categoria_id": 1,
        "precios": []
    }
    
    with pytest.raises(ValidationError) as exc_info:
        ProductoCreateRequest(**data)
    
    errors = exc_info.value.errors()
    assert len(errors) > 0


def test_create_producto_missing_precios():
    """Test that missing precios is rejected."""
    data = {
        "nombre": "Empanada",
        "categoria_id": 1
    }
    
    with pytest.raises(ValidationError) as exc_info:
        ProductoCreateRequest(**data)
    
    errors = exc_info.value.errors()
    assert len(errors) > 0
    assert any(error["loc"] == ("precios",) for error in errors)


def test_create_producto_empty_nombre():
    """Test that empty nombre is rejected."""
    data = {
        "nombre": "",
        "categoria_id": 1,
        "precios": [
            {"cantidad": 1, "precio": Decimal("1200.00")}
        ]
    }
    
    with pytest.raises(ValidationError) as exc_info:
        ProductoCreateRequest(**data)
    
    errors = exc_info.value.errors()
    assert len(errors) > 0


def test_create_producto_invalid_categoria_id():
    """Test that zero or negative categoria_id is rejected."""
    data = {
        "nombre": "Empanada",
        "categoria_id": 0,
        "precios": [
            {"cantidad": 1, "precio": Decimal("1200.00")}
        ]
    }
    
    with pytest.raises(ValidationError) as exc_info:
        ProductoCreateRequest(**data)
    
    errors = exc_info.value.errors()
    assert len(errors) > 0


# ==================== ProductoUpdateRequest Tests ====================

def test_update_producto_valid_all_fields():
    """Test updating product with all fields."""
    data = {
        "nombre": "Empanada Premium",
        "categoria_id": 2,
        "precios": [
            {"cantidad": 1, "precio": Decimal("1500.00")},
            {"cantidad": 6, "precio": Decimal("7000.00")}
        ]
    }
    
    producto = ProductoUpdateRequest(**data)
    
    assert producto.nombre == "Empanada Premium"
    assert producto.categoria_id == 2
    assert len(producto.precios) == 2


def test_update_producto_partial_nombre():
    """Test updating only nombre."""
    data = {
        "nombre": "Nuevo Nombre"
    }
    
    producto = ProductoUpdateRequest(**data)
    
    assert producto.nombre == "Nuevo Nombre"
    assert producto.categoria_id is None
    assert producto.precios is None


def test_update_producto_partial_categoria():
    """Test updating only categoria_id."""
    data = {
        "categoria_id": 3
    }
    
    producto = ProductoUpdateRequest(**data)
    
    assert producto.nombre is None
    assert producto.categoria_id == 3
    assert producto.precios is None


def test_update_producto_empty_precios():
    """Test that empty precios list is rejected in update."""
    data = {
        "precios": []
    }
    
    with pytest.raises(ValidationError) as exc_info:
        ProductoUpdateRequest(**data)
    
    errors = exc_info.value.errors()
    assert len(errors) > 0


def test_update_producto_missing_unit_price():
    """Test that update without unit price is rejected."""
    data = {
        "precios": [
            {"cantidad": 6, "precio": Decimal("6000.00")},
            {"cantidad": 12, "precio": Decimal("10800.00")}
        ]
    }
    
    with pytest.raises(ValidationError) as exc_info:
        ProductoUpdateRequest(**data)
    
    errors = exc_info.value.errors()
    assert len(errors) > 0


def test_update_producto_duplicate_quantities():
    """Test that duplicate quantities are rejected in update."""
    data = {
        "precios": [
            {"cantidad": 1, "precio": Decimal("1200.00")},
            {"cantidad": 6, "precio": Decimal("6000.00")},
            {"cantidad": 6, "precio": Decimal("6500.00")}
        ]
    }
    
    with pytest.raises(ValidationError) as exc_info:
        ProductoUpdateRequest(**data)
    
    errors = exc_info.value.errors()
    assert len(errors) > 0


def test_update_producto_none_values():
    """Test that all None values is valid for partial update."""
    data = {}
    
    producto = ProductoUpdateRequest(**data)
    
    assert producto.nombre is None
    assert producto.categoria_id is None
    assert producto.precios is None


# ==================== ActualizarPreciosMasivosRequest Tests ====================

def test_bulk_update_con_monto_valido():
    """Test bulk update with valid fixed amount."""
    data = {"monto": Decimal("200")}
    request = ActualizarPreciosMasivosRequest(**data)
    assert request.monto == Decimal("200")
    assert request.porcentaje is None
    assert request.categoria_ids is None


def test_bulk_update_con_porcentaje_valido():
    """Test bulk update with valid percentage."""
    data = {"porcentaje": Decimal("10")}
    request = ActualizarPreciosMasivosRequest(**data)
    assert request.porcentaje == Decimal("10")
    assert request.monto is None


def test_bulk_update_con_categoria():
    """Test bulk update with category filter."""
    data = {"monto": Decimal("100"), "categoria_ids": [5, 3]}
    request = ActualizarPreciosMasivosRequest(**data)
    assert request.monto == Decimal("100")
    assert request.categoria_ids == [5, 3]


def test_bulk_update_monto_negativo():
    """Test bulk update with negative amount (decrease)."""
    data = {"monto": Decimal("-100")}
    request = ActualizarPreciosMasivosRequest(**data)
    assert request.monto == Decimal("-100")


def test_bulk_update_porcentaje_negativo():
    """Test bulk update with negative percentage (decrease)."""
    data = {"porcentaje": Decimal("-5")}
    request = ActualizarPreciosMasivosRequest(**data)
    assert request.porcentaje == Decimal("-5")


def test_bulk_update_sin_monto_ni_porcentaje_falla():
    """Test that missing both monto and porcentaje raises error."""
    data = {}
    with pytest.raises(ValidationError) as exc_info:
        ActualizarPreciosMasivosRequest(**data)
    errors = exc_info.value.errors()
    assert any("monto" in str(e).lower() or "porcentaje" in str(e).lower() for e in errors)


def test_bulk_update_con_ambos_monto_y_porcentaje_falla():
    """Test that providing both monto and porcentaje raises error."""
    data = {"monto": Decimal("200"), "porcentaje": Decimal("10")}
    with pytest.raises(ValidationError) as exc_info:
        ActualizarPreciosMasivosRequest(**data)
    errors = exc_info.value.errors()
    assert len(errors) > 0


def test_bulk_update_porcentaje_menos_100_falla():
    """Test that percentage <= -100 is rejected."""
    data = {"porcentaje": Decimal("-100")}
    with pytest.raises(ValidationError) as exc_info:
        ActualizarPreciosMasivosRequest(**data)
    errors = exc_info.value.errors()
    assert len(errors) > 0


def test_bulk_update_porcentaje_menos_150_falla():
    """Test that percentage < -100 is rejected."""
    data = {"porcentaje": Decimal("-150")}
    with pytest.raises(ValidationError) as exc_info:
        ActualizarPreciosMasivosRequest(**data)
    errors = exc_info.value.errors()
    assert len(errors) > 0


def test_bulk_update_categoria_ids_negativa_falla():
    """Test that negative categoria_ids values are rejected."""
    data = {"monto": Decimal("100"), "categoria_ids": [-1, 2]}
    with pytest.raises(ValidationError) as exc_info:
        ActualizarPreciosMasivosRequest(**data)
    errors = exc_info.value.errors()
    assert len(errors) > 0


def test_bulk_update_categoria_ids_vacia_falla():
    """Test that empty categoria_ids list is rejected."""
    data = {"monto": Decimal("100"), "categoria_ids": []}
    with pytest.raises(ValidationError) as exc_info:
        ActualizarPreciosMasivosRequest(**data)
    errors = exc_info.value.errors()
    assert len(errors) > 0