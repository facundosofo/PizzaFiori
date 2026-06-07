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
    SaleResponse,
    SaleUpdateRequest,
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
        "cantidad": 2,
        "productos_seleccionados": [
            {"producto_id": 5, "cantidad": 12}
        ]
    }
    
    item = SaleItemRequest(**data)
    
    assert item.producto_id is None
    assert item.oferta_id == 1
    assert item.cantidad == 2
    assert len(item.productos_seleccionados) == 1


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
    """Test sale item with only oferta_id and productos_seleccionados."""
    data = {
        "oferta_id": 3,
        "cantidad": 1,
        "productos_seleccionados": [
            {"producto_id": 1, "cantidad": 1},
            {"producto_id": 2, "cantidad": 6}
        ]
    }
    
    item = SaleItemRequest(**data)
    
    assert item.producto_id is None
    assert item.oferta_id == 3
    assert item.cantidad == 1
    assert len(item.productos_seleccionados) == 2


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
    assert any("producto_id" in str(error.get("ctx", {}).get("error", "")).lower()
               or "debe especificar" in str(error.get("ctx", {}).get("error", "")).lower()
               for error in errors)


def test_sale_item_both_present():
    """Test that both producto_id and oferta_id present is rejected (XOR validation)."""
    data = {
        "producto_id": 1,
        "oferta_id": 2,
        "cantidad": 5,
        "productos_seleccionados": [{"producto_id": 3, "cantidad": 1}]
    }
    
    with pytest.raises(ValidationError) as exc_info:
        SaleItemRequest(**data)
    
    errors = exc_info.value.errors()
    assert len(errors) > 0
    assert any("solo se puede especificar uno" in str(error.get("ctx", {}).get("error", "")).lower()
               or "solo uno" in str(error.get("ctx", {}).get("error", "")).lower()
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


def test_sale_item_offer_without_productos_seleccionados():
    """Test that oferta_id requires productos_seleccionados."""
    data = {
        "oferta_id": 1,
        "cantidad": 1
    }
    
    with pytest.raises(ValidationError) as exc_info:
        SaleItemRequest(**data)
    
    errors = exc_info.value.errors()
    assert len(errors) > 0
    assert any("productos_seleccionados" in str(error.get("ctx", {}).get("error", "")).lower()
               for error in errors)


def test_sale_item_offer_with_empty_productos_seleccionados():
    """Test that oferta_id with empty productos_seleccionados is rejected."""
    data = {
        "oferta_id": 1,
        "cantidad": 1,
        "productos_seleccionados": []
    }
    
    with pytest.raises(ValidationError) as exc_info:
        SaleItemRequest(**data)
    
    errors = exc_info.value.errors()
    assert len(errors) > 0


def test_sale_item_product_with_productos_seleccionados():
    """Test that producto_id cannot have productos_seleccionados."""
    data = {
        "producto_id": 1,
        "cantidad": 6,
        "productos_seleccionados": [{"producto_id": 2, "cantidad": 3}]
    }
    
    with pytest.raises(ValidationError) as exc_info:
        SaleItemRequest(**data)
    
    errors = exc_info.value.errors()
    assert len(errors) > 0
    assert any("productos_seleccionados" in str(error.get("ctx", {}).get("error", "")).lower()
               for error in errors)


# ==================== SaleCreateRequest Tests ====================

def test_create_sale_valid_with_products():
    """Test creating a valid sale with product items."""
    data = {
        "items": [
            {"producto_id": 1, "cantidad": 6},
            {"producto_id": 2, "cantidad": 12}
        ]
    }
    
    sale = SaleCreateRequest(**data)
    
    assert len(sale.items) == 2
    assert sale.items[0].producto_id == 1
    assert sale.items[1].producto_id == 2


def test_create_sale_valid_with_offers():
    """Test creating a valid sale with offer items."""
    data = {
        "items": [
            {
                "oferta_id": 1, 
                "cantidad": 2,
                "productos_seleccionados": [
                    {"producto_id": 1, "cantidad": 6},
                    {"producto_id": 2, "cantidad": 6}
                ]
            }
        ]
    }
    
    sale = SaleCreateRequest(**data)
    
    assert len(sale.items) == 1
    assert sale.items[0].oferta_id == 1
    assert len(sale.items[0].productos_seleccionados) == 2


def test_update_sale_request_accepts_aplicar_recargo():
    """Test that SaleUpdateRequest allows aplicar_recargo flag."""
    data = {
        "items": [
            {"producto_id": 1, "cantidad": 1, "precio_unitario": "1200.00"}
        ],
        "aplicar_recargo": True
    }

    sale = SaleUpdateRequest(**data)

    assert sale.aplicar_recargo is True


def test_create_sale_valid_mixed_items():
    """Test creating sale with both products and offers."""
    data = {
        "items": [
            {"producto_id": 1, "cantidad": 6},
            {
                "oferta_id": 1, 
                "cantidad": 1,
                "productos_seleccionados": [{"producto_id": 5, "cantidad": 12}]
            },
            {"producto_id": 3, "cantidad": 3}
        ]
    }
    
    sale = SaleCreateRequest(**data)
    
    assert len(sale.items) == 3
    assert sale.items[0].producto_id == 1
    assert sale.items[1].oferta_id == 1
    assert sale.items[2].producto_id == 3


def test_create_sale_numero_orden_auto_generated():
    """Test that numero_orden is auto-generated and cannot be provided in request."""
    # El numero_orden ya no es aceptado en SaleCreateRequest
    data = {
        "items": [
            {"producto_id": 1, "cantidad": 6}
        ]
    }
    
    sale = SaleCreateRequest(**data)
    
    # Verified that numero_orden is not part of the request
    assert not hasattr(sale, 'numero_orden') or sale.numero_orden is None
    assert len(sale.items) == 1


def test_create_sale_empty_items():
    """Test that empty items list is rejected."""
    data = {
        "items": []
    }
    
    with pytest.raises(ValidationError) as exc_info:
        SaleCreateRequest(**data)
    
    errors = exc_info.value.errors()
    assert len(errors) > 0


def test_create_sale_missing_items():
    """Test that missing items is rejected."""
    data = {}
    
    with pytest.raises(ValidationError) as exc_info:
        SaleCreateRequest(**data)
    
    errors = exc_info.value.errors()
    assert len(errors) > 0
    assert any(error["loc"] == ("items",) for error in errors)


def test_create_sale_item_xor_validation():
    """Test that XOR validation is applied to items in sale creation."""
    data = {
        "items": [
            {"producto_id": 1, "oferta_id": 2, "cantidad": 5}  # Ambos presentes
        ]
    }
    
    with pytest.raises(ValidationError) as exc_info:
        SaleCreateRequest(**data)
    
    errors = exc_info.value.errors()
    assert len(errors) > 0


def test_create_sale_numero_orden_not_allowed():
    """Test that numero_orden is not accepted in SaleCreateRequest.
    
    The numero_orden is auto-generated by the service and cannot be provided
    by the client. Extra fields are ignored by Pydantic by default.
    """
    data = {
        "numero_orden": "ORD-CUSTOM",
        "items": [
            {"producto_id": 1, "cantidad": 6}
        ]
    }
    
    # Pydantic ignores extra fields by default, so this should work
    # but numero_orden should not be set
    sale = SaleCreateRequest(**data)
    
    assert not hasattr(sale, 'numero_orden')
    assert len(sale.items) == 1


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
                "subtotal": Decimal("6000.00"),
                "producto_sku": "EMPA-CARN-001",
                "item_nombre": "Empanada de Carne",
                "item_categoria": "Empanadas",
                "item_descripcion": None,
                "oferta_productos_snapshot": None
            },
            {
                "id": 2,
                "producto_id": None,
                "oferta_id": 1,
                "cantidad": 1,
                "precio_unitario": Decimal("6000.00"),
                "subtotal": Decimal("6000.00"),
                "producto_sku": None,
                "item_nombre": "Promo Docena",
                "item_categoria": "Ofertas",
                "item_descripcion": "12 empanadas surtidas",
                "oferta_productos_snapshot": []
            }
        ]
    }
    
    response = SaleResponse(**data)
    
    assert response.id == 1
    assert response.numero_orden == "ORD-001"  # Can have any generated format
    assert response.total == Decimal("12000.00")
    assert len(response.items) == 2


# ================================================================================