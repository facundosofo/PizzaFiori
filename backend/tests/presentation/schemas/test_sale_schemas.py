"""
Tests for sale schemas validation.
Tests Pydantic models for sales including XOR validation for producto_id/oferta_id.
"""

import pytest
from decimal import Decimal
from pydantic import ValidationError

from app.presentation.schemas.sale_schemas import (
    SaleItemRequest,
    SaleCreateRequest,
    SaleResponse
)


# ==================== SaleItemRequest Tests ====================

def test_sale_item_with_product():
    """Test creating sale item with producto_id (happy path)."""
    data = {
        "producto_id": 1,
        "oferta_id": None,
        "cantidad": 6
    }
    
    item = SaleItemRequest(**data)
    
    assert item.producto_id == 1
    assert item.oferta_id is None
    assert item.cantidad == 6


def test_sale_item_with_offer():
    """Test creating sale item with oferta_id (happy path)."""
    data = {
        "producto_id": None,
        "oferta_id": 1,
        "cantidad": 2
    }
    
    item = SaleItemRequest(**data)
    
    assert item.producto_id is None
    assert item.oferta_id == 1
    assert item.cantidad == 2


def test_sale_item_product_only():
    """Test sale item with only producto_id (omitting oferta_id)."""
    data = {
        "producto_id": 5,
        "cantidad": 12
    }
    
    item = SaleItemRequest(**data)
    
    assert item.producto_id == 5
    assert item.oferta_id is None
    assert item.cantidad == 12


def test_sale_item_offer_only():
    """Test sale item with only oferta_id (omitting producto_id)."""
    data = {
        "oferta_id": 3,
        "cantidad": 1
    }
    
    item = SaleItemRequest(**data)
    
    assert item.producto_id is None
    assert item.oferta_id == 3
    assert item.cantidad == 1


def test_sale_item_both_null():
    """Test that both producto_id and oferta_id null is rejected (XOR validation)."""
    data = {
        "producto_id": None,
        "oferta_id": None,
        "cantidad": 5
    }
    
    with pytest.raises(ValidationError) as exc_info:
        SaleItemRequest(**data)
    
    errors = exc_info.value.errors()
    assert len(errors) > 0
    assert any("producto_id o oferta_id" in str(error.get("ctx", {}).get("error", "")).lower() 
               for error in errors)


def test_sale_item_both_present():
    """Test that both producto_id and oferta_id present is rejected (XOR validation)."""
    data = {
        "producto_id": 1,
        "oferta_id": 2,
        "cantidad": 5
    }
    
    with pytest.raises(ValidationError) as exc_info:
        SaleItemRequest(**data)
    
    errors = exc_info.value.errors()
    assert len(errors) > 0
    assert any("mismo tiempo" in str(error.get("ctx", {}).get("error", "")).lower() 
               or "al mismo tiempo" in str(error.get("ctx", {}).get("error", "")).lower()
               for error in errors)


def test_sale_item_invalid_cantidad():
    """Test that zero or negative cantidad is rejected."""
    data = {
        "producto_id": 1,
        "cantidad": 0
    }
    
    with pytest.raises(ValidationError) as exc_info:
        SaleItemRequest(**data)
    
    errors = exc_info.value.errors()
    assert len(errors) > 0


def test_sale_item_missing_cantidad():
    """Test that missing cantidad is rejected."""
    data = {
        "producto_id": 1
    }
    
    with pytest.raises(ValidationError) as exc_info:
        SaleItemRequest(**data)
    
    errors = exc_info.value.errors()
    assert len(errors) > 0
    assert any(error["loc"] == ("cantidad",) for error in errors)


# ==================== SaleCreateRequest Tests ====================

def test_create_sale_valid_with_products():
    """Test creating a valid sale with product items."""
    data = {
        "numero_orden": "ORD-001",
        "items": [
            {"producto_id": 1, "cantidad": 6},
            {"producto_id": 2, "cantidad": 12}
        ]
    }
    
    sale = SaleCreateRequest(**data)
    
    assert sale.numero_orden == "ORD-001"
    assert len(sale.items) == 2
    assert sale.items[0].producto_id == 1
    assert sale.items[1].producto_id == 2


def test_create_sale_valid_with_offers():
    """Test creating a valid sale with offer items."""
    data = {
        "numero_orden": "ORD-002",
        "items": [
            {"oferta_id": 1, "cantidad": 2}
        ]
    }
    
    sale = SaleCreateRequest(**data)
    
    assert sale.numero_orden == "ORD-002"
    assert len(sale.items) == 1
    assert sale.items[0].oferta_id == 1


def test_create_sale_valid_mixed_items():
    """Test creating sale with both products and offers."""
    data = {
        "numero_orden": "ORD-003",
        "items": [
            {"producto_id": 1, "cantidad": 6},
            {"oferta_id": 1, "cantidad": 1},
            {"producto_id": 3, "cantidad": 3}
        ]
    }
    
    sale = SaleCreateRequest(**data)
    
    assert len(sale.items) == 3
    assert sale.items[0].producto_id == 1
    assert sale.items[1].oferta_id == 1
    assert sale.items[2].producto_id == 3


def test_create_sale_without_numero_orden():
    """Test creating sale without optional numero_orden."""
    data = {
        "items": [
            {"producto_id": 1, "cantidad": 6}
        ]
    }
    
    sale = SaleCreateRequest(**data)
    
    assert sale.numero_orden is None
    assert len(sale.items) == 1


def test_create_sale_empty_items():
    """Test that empty items list is rejected."""
    data = {
        "numero_orden": "ORD-004",
        "items": []
    }
    
    with pytest.raises(ValidationError) as exc_info:
        SaleCreateRequest(**data)
    
    errors = exc_info.value.errors()
    assert len(errors) > 0


def test_create_sale_missing_items():
    """Test that missing items is rejected."""
    data = {
        "numero_orden": "ORD-005"
    }
    
    with pytest.raises(ValidationError) as exc_info:
        SaleCreateRequest(**data)
    
    errors = exc_info.value.errors()
    assert len(errors) > 0
    assert any(error["loc"] == ("items",) for error in errors)


def test_create_sale_item_xor_validation():
    """Test that XOR validation is applied to items in sale creation."""
    data = {
        "numero_orden": "ORD-006",
        "items": [
            {"producto_id": 1, "oferta_id": 2, "cantidad": 5}  # Ambos presentes
        ]
    }
    
    with pytest.raises(ValidationError) as exc_info:
        SaleCreateRequest(**data)
    
    errors = exc_info.value.errors()
    assert len(errors) > 0


def test_create_sale_long_numero_orden():
    """Test that numero_orden exceeding max length is rejected."""
    data = {
        "numero_orden": "A" * 100,  # Excede max_length=50
        "items": [
            {"producto_id": 1, "cantidad": 6}
        ]
    }
    
    with pytest.raises(ValidationError) as exc_info:
        SaleCreateRequest(**data)
    
    errors = exc_info.value.errors()
    assert len(errors) > 0


# ==================== SaleResponse Tests ====================

def test_sale_response_valid():
    """Test sale response model with valid data."""
    from datetime import datetime
    
    data = {
        "id": 1,
        "numero_orden": "ORD-001",
        "total": Decimal("12000.00"),
        "fecha_creacion": datetime.now(),
        "fecha_actualizacion": datetime.now(),
        "items": [
            {
                "id": 1,
                "producto_id": 1,
                "oferta_id": None,
                "cantidad": 6,
                "precio_unitario": Decimal("1000.00"),
                "subtotal": Decimal("6000.00")
            },
            {
                "id": 2,
                "producto_id": None,
                "oferta_id": 1,
                "cantidad": 1,
                "precio_unitario": Decimal("6000.00"),
                "subtotal": Decimal("6000.00")
            }
        ]
    }
    
    response = SaleResponse(**data)
    
    assert response.id == 1
    assert response.numero_orden == "ORD-001"
    assert response.total == Decimal("12000.00")
    assert len(response.items) == 2


def test_sale_response_without_numero_orden():
    """Test sale response without numero_orden."""
    from datetime import datetime
    
    data = {
        "id": 2,
        "numero_orden": None,
        "total": Decimal("6000.00"),
        "fecha_creacion": datetime.now(),
        "fecha_actualizacion": datetime.now(),
        "items": [
            {
                "id": 1,
                "producto_id": 1,
                "oferta_id": None,
                "cantidad": 6,
                "precio_unitario": Decimal("1000.00"),
                "subtotal": Decimal("6000.00")
            }
        ]
    }
    
    response = SaleResponse(**data)
    
    assert response.id == 2
    assert response.numero_orden is None
    assert len(response.items) == 1
