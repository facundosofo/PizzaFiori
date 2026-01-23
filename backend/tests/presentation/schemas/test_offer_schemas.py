"""
Tests for offer schemas validation.
Tests Pydantic models for offers including product duplication validation.
"""

import pytest
from decimal import Decimal
from pydantic import ValidationError

from app.presentation.schemas.offer_schemas import (
    OfferItemRequest,
    OfferCreateRequest,
    OfferUpdateRequest,
    OfferResponse
)


# ==================== OfferItemRequest Tests ====================

def test_offer_item_valid():
    """Test creating a valid offer item."""
    data = {
        "producto_id": 1,
        "cantidad": 6
    }
    
    item = OfferItemRequest(**data)
    
    assert item.producto_id == 1
    assert item.cantidad == 6


def test_offer_item_default_cantidad():
    """Test offer item with default cantidad."""
    data = {
        "producto_id": 1
    }
    
    item = OfferItemRequest(**data)
    
    assert item.producto_id == 1
    assert item.cantidad == 1


def test_offer_item_invalid_producto_id():
    """Test that zero or negative producto_id is rejected."""
    data = {
        "producto_id": 0,
        "cantidad": 1
    }
    
    with pytest.raises(ValidationError) as exc_info:
        OfferItemRequest(**data)
    
    errors = exc_info.value.errors()
    assert len(errors) > 0


def test_offer_item_invalid_cantidad():
    """Test that zero or negative cantidad is rejected."""
    data = {
        "producto_id": 1,
        "cantidad": 0
    }
    
    with pytest.raises(ValidationError) as exc_info:
        OfferItemRequest(**data)
    
    errors = exc_info.value.errors()
    assert len(errors) > 0


# ==================== OfferCreateRequest Tests ====================

def test_create_offer_valid():
    """Test creating a valid offer with multiple products."""
    data = {
        "nombre": "Promo Docena",
        "descripcion": "12 empanadas surtidas",
        "precio": Decimal("10000.00"),
        "productos": [
            {"producto_id": 1, "cantidad": 6},
            {"producto_id": 2, "cantidad": 6}
        ]
    }
    
    offer = OfferCreateRequest(**data)
    
    assert offer.nombre == "Promo Docena"
    assert offer.descripcion == "12 empanadas surtidas"
    assert offer.precio == Decimal("10000.00")
    assert len(offer.productos) == 2


def test_create_offer_valid_without_descripcion():
    """Test creating offer without optional description."""
    data = {
        "nombre": "Promo Simple",
        "precio": Decimal("5000.00"),
        "productos": [
            {"producto_id": 1, "cantidad": 6}
        ]
    }
    
    offer = OfferCreateRequest(**data)
    
    assert offer.nombre == "Promo Simple"
    assert offer.descripcion is None
    assert len(offer.productos) == 1


def test_create_offer_single_product():
    """Test creating offer with single product."""
    data = {
        "nombre": "Promo Individual",
        "precio": Decimal("3000.00"),
        "productos": [
            {"producto_id": 1, "cantidad": 3}
        ]
    }
    
    offer = OfferCreateRequest(**data)
    
    assert len(offer.productos) == 1
    assert offer.productos[0].producto_id == 1
    assert offer.productos[0].cantidad == 3


def test_create_offer_duplicate_products():
    """Test that duplicate products are rejected."""
    data = {
        "nombre": "Promo Duplicada",
        "precio": Decimal("8000.00"),
        "productos": [
            {"producto_id": 1, "cantidad": 6},
            {"producto_id": 2, "cantidad": 3},
            {"producto_id": 1, "cantidad": 3}  # Duplicado
        ]
    }
    
    with pytest.raises(ValidationError) as exc_info:
        OfferCreateRequest(**data)
    
    errors = exc_info.value.errors()
    assert len(errors) > 0
    assert any("duplicad" in str(error.get("ctx", {}).get("error", "")).lower() 
               for error in errors)


def test_create_offer_empty_productos():
    """Test that empty productos list is rejected."""
    data = {
        "nombre": "Promo Vacía",
        "precio": Decimal("5000.00"),
        "productos": []
    }
    
    with pytest.raises(ValidationError) as exc_info:
        OfferCreateRequest(**data)
    
    errors = exc_info.value.errors()
    assert len(errors) > 0


def test_create_offer_missing_productos():
    """Test that missing productos is rejected."""
    data = {
        "nombre": "Promo Sin Productos",
        "precio": Decimal("5000.00")
    }
    
    with pytest.raises(ValidationError) as exc_info:
        OfferCreateRequest(**data)
    
    errors = exc_info.value.errors()
    assert len(errors) > 0
    assert any(error["loc"] == ("productos",) for error in errors)


def test_create_offer_empty_nombre():
    """Test that empty nombre is rejected."""
    data = {
        "nombre": "",
        "precio": Decimal("5000.00"),
        "productos": [
            {"producto_id": 1, "cantidad": 6}
        ]
    }
    
    with pytest.raises(ValidationError) as exc_info:
        OfferCreateRequest(**data)
    
    errors = exc_info.value.errors()
    assert len(errors) > 0


def test_create_offer_negative_precio():
    """Test that negative precio is rejected."""
    data = {
        "nombre": "Promo",
        "precio": Decimal("-100.00"),
        "productos": [
            {"producto_id": 1, "cantidad": 6}
        ]
    }
    
    with pytest.raises(ValidationError) as exc_info:
        OfferCreateRequest(**data)
    
    errors = exc_info.value.errors()
    assert len(errors) > 0


def test_create_offer_zero_precio():
    """Test that zero precio is rejected."""
    data = {
        "nombre": "Promo",
        "precio": Decimal("0.00"),
        "productos": [
            {"producto_id": 1, "cantidad": 6}
        ]
    }
    
    with pytest.raises(ValidationError) as exc_info:
        OfferCreateRequest(**data)
    
    errors = exc_info.value.errors()
    assert len(errors) > 0


# ==================== OfferUpdateRequest Tests ====================

def test_update_offer_valid_all_fields():
    """Test updating offer with all fields."""
    data = {
        "nombre": "Promo Actualizada",
        "descripcion": "Nueva descripción",
        "precio": Decimal("12000.00"),
        "productos": [
            {"producto_id": 3, "cantidad": 6},
            {"producto_id": 4, "cantidad": 6}
        ]
    }
    
    offer = OfferUpdateRequest(**data)
    
    assert offer.nombre == "Promo Actualizada"
    assert offer.descripcion == "Nueva descripción"
    assert offer.precio == Decimal("12000.00")
    assert len(offer.productos) == 2


def test_update_offer_partial_nombre():
    """Test updating only nombre."""
    data = {
        "nombre": "Nuevo Nombre"
    }
    
    offer = OfferUpdateRequest(**data)
    
    assert offer.nombre == "Nuevo Nombre"
    assert offer.descripcion is None
    assert offer.precio is None
    assert offer.productos is None


def test_update_offer_partial_precio():
    """Test updating only precio."""
    data = {
        "precio": Decimal("15000.00")
    }
    
    offer = OfferUpdateRequest(**data)
    
    assert offer.nombre is None
    assert offer.precio == Decimal("15000.00")
    assert offer.productos is None


def test_update_offer_empty_productos():
    """Test that empty productos list is rejected in update."""
    data = {
        "productos": []
    }
    
    with pytest.raises(ValidationError) as exc_info:
        OfferUpdateRequest(**data)
    
    errors = exc_info.value.errors()
    assert len(errors) > 0


def test_update_offer_duplicate_products():
    """Test that duplicate products are rejected in update."""
    data = {
        "productos": [
            {"producto_id": 1, "cantidad": 6},
            {"producto_id": 2, "cantidad": 3},
            {"producto_id": 1, "cantidad": 2}  # Duplicado
        ]
    }
    
    with pytest.raises(ValidationError) as exc_info:
        OfferUpdateRequest(**data)
    
    errors = exc_info.value.errors()
    assert len(errors) > 0


def test_update_offer_none_values():
    """Test that all None values is valid for partial update."""
    data = {}
    
    offer = OfferUpdateRequest(**data)
    
    assert offer.nombre is None
    assert offer.descripcion is None
    assert offer.precio is None
    assert offer.productos is None
