"""Tests para schemas de pizzas mitad-mitad."""

import pytest
from decimal import Decimal
from pydantic import ValidationError

from app.presentation.schemas.sale_schemas import (
    PizzaMitadMitadRequest,
    SaleItemRequest
)


class TestPizzaMitadMitadRequest:
    """Tests para PizzaMitadMitadRequest."""

    def test_pizza_mitad_mitad_valid(self):
        """Test creating a valid pizza mitad-mitad request."""
        data = {
            "producto_id_izquierda": 1,
            "producto_id_derecha": 2,
            "cantidad": 2
        }
        
        pizza = PizzaMitadMitadRequest(**data)
        
        assert pizza.producto_id_izquierda == 1
        assert pizza.producto_id_derecha == 2
        assert pizza.cantidad == 2

    def test_pizza_mitad_mitad_same_products_invalid(self):
        """Test that same products are rejected."""
        data = {
            "producto_id_izquierda": 1,
            "producto_id_derecha": 1,  # Same product
            "cantidad": 1
        }
        
        with pytest.raises(ValidationError) as exc_info:
            PizzaMitadMitadRequest(**data)
        
        errors = exc_info.value.errors()
        assert len(errors) > 0
        assert any("diferentes" in error["msg"].lower() for error in errors)

    def test_pizza_mitad_mitad_invalid_ids(self):
        """Test that invalid product IDs are rejected."""
        data = {
            "producto_id_izquierda": 0,  # Invalid
            "producto_id_derecha": 2,
            "cantidad": 1
        }
        
        with pytest.raises(ValidationError) as exc_info:
            PizzaMitadMitadRequest(**data)
        
        errors = exc_info.value.errors()
        assert len(errors) > 0

    def test_pizza_mitad_mitad_invalid_quantity(self):
        """Test that invalid quantities are rejected."""
        data = {
            "producto_id_izquierda": 1,
            "producto_id_derecha": 2,
            "cantidad": 0  # Invalid
        }
        
        with pytest.raises(ValidationError) as exc_info:
            PizzaMitadMitadRequest(**data)
        
        errors = exc_info.value.errors()
        assert len(errors) > 0


class TestSaleItemRequestWithPizzaMitadMitad:
    """Tests para SaleItemRequest con pizzas mitad-mitad."""

    def test_sale_item_pizza_mitad_mitad_valid(self):
        """Test creating a valid sale item with pizza mitad-mitad."""
        data = {
            "cantidad": 2,
            "pizza_mitad_mitad": {
                "producto_id_izquierda": 1,
                "producto_id_derecha": 2,
                "cantidad": 2
            }
        }
        
        item = SaleItemRequest(**data)
        
        assert item.cantidad == 2
        assert item.pizza_mitad_mitad is not None
        assert item.pizza_mitad_mitad.producto_id_izquierda == 1
        assert item.pizza_mitad_mitad.producto_id_derecha == 2
        assert item.pizza_mitad_mitad.cantidad == 2
        assert item.producto_id is None
        assert item.oferta_id is None

    def test_sale_item_pizza_mitad_mitad_with_producto_id_invalid(self):
        """Test that pizza_mitad_mitad with producto_id is rejected."""
        data = {
            "producto_id": 1,
            "cantidad": 2,
            "pizza_mitad_mitad": {
                "producto_id_izquierda": 1,
                "producto_id_derecha": 2,
                "cantidad": 2
            }
        }
        
        with pytest.raises(ValidationError) as exc_info:
            SaleItemRequest(**data)
        
        errors = exc_info.value.errors()
        assert len(errors) > 0
        assert any("uno de" in error["msg"] for error in errors)

    def test_sale_item_pizza_mitad_mitad_with_oferta_id_invalid(self):
        """Test that pizza_mitad_mitad with oferta_id is rejected."""
        data = {
            "oferta_id": 1,
            "cantidad": 2,
            "pizza_mitad_mitad": {
                "producto_id_izquierda": 1,
                "producto_id_derecha": 2,
                "cantidad": 2
            }
        }
        
        with pytest.raises(ValidationError) as exc_info:
            SaleItemRequest(**data)
        
        errors = exc_info.value.errors()
        assert len(errors) > 0
        assert any("uno de" in error["msg"] for error in errors)

    def test_sale_item_pizza_mitad_mitad_with_productos_seleccionados_invalid(self):
        """Test that pizza_mitad_mitad with productos_seleccionados is rejected."""
        data = {
            "cantidad": 2,
            "pizza_mitad_mitad": {
                "producto_id_izquierda": 1,
                "producto_id_derecha": 2,
                "cantidad": 2
            },
            "productos_seleccionados": [
                {"producto_id": 1, "cantidad": 1}
            ]
        }
        
        with pytest.raises(ValidationError) as exc_info:
            SaleItemRequest(**data)
        
        errors = exc_info.value.errors()
        assert len(errors) > 0
        assert any("productos_seleccionados" in error["msg"] for error in errors)

    def test_sale_item_no_type_specified_invalid(self):
        """Test that sale item without any type is rejected."""
        data = {
            "cantidad": 2
        }
        
        with pytest.raises(ValidationError) as exc_info:
            SaleItemRequest(**data)
        
        errors = exc_info.value.errors()
        assert len(errors) > 0
        assert any("producto_id" in error["msg"] and "oferta_id" in error["msg"] and "pizza_mitad_mitad" in error["msg"] for error in errors)

    def test_sale_item_all_types_specified_invalid(self):
        """Test that sale item with all types specified is rejected."""
        data = {
            "producto_id": 1,
            "oferta_id": 1,
            "cantidad": 2,
            "pizza_mitad_mitad": {
                "producto_id_izquierda": 1,
                "producto_id_derecha": 2,
                "cantidad": 2
            }
        }
        
        with pytest.raises(ValidationError) as exc_info:
            SaleItemRequest(**data)
        
        errors = exc_info.value.errors()
        assert len(errors) > 0
        assert any("uno de" in error["msg"] for error in errors)
