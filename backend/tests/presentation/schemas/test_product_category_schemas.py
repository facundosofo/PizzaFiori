"""
Tests for product category schemas validation.
Tests Pydantic models for product category creation, updates and responses.
"""

import pytest
from pydantic import ValidationError

from app.presentation.schemas.product_category_schemas import (
    ProductoCategoriaCreateRequest,
    ProductoCategoriaUpdateRequest,
    ProductoCategoriaResponse,
)


# ==================== ProductoCategoriaCreateRequest Tests ====================

def test_create_producto_categoria_valid():
    """Test creating a valid product category."""
    data = {"nombre": "Empanadas"}
    categoria = ProductoCategoriaCreateRequest(**data)
    assert categoria.nombre == "Empanadas"


def test_create_producto_categoria_empty_nombre():
    """Test that empty nombre is rejected."""
    with pytest.raises(ValidationError) as exc_info:
        ProductoCategoriaCreateRequest(nombre="")
    errors = exc_info.value.errors()
    assert any(error["loc"] == ("nombre",) for error in errors)


def test_create_producto_categoria_missing_nombre():
    """Test that missing nombre is rejected."""
    with pytest.raises(ValidationError) as exc_info:
        ProductoCategoriaCreateRequest()
    errors = exc_info.value.errors()
    assert any(error["loc"] == ("nombre",) for error in errors)


def test_create_producto_categoria_nombre_too_long():
    """Test that nombre > 50 chars is rejected."""
    with pytest.raises(ValidationError) as exc_info:
        ProductoCategoriaCreateRequest(nombre="A" * 51)
    errors = exc_info.value.errors()
    assert any(error["loc"] == ("nombre",) for error in errors)


def test_create_producto_categoria_nombre_max_length():
    """Test that nombre of exactly 50 chars is accepted."""
    categoria = ProductoCategoriaCreateRequest(nombre="A" * 50)
    assert len(categoria.nombre) == 50


# ==================== ProductoCategoriaUpdateRequest Tests ====================

def test_update_producto_categoria_valid_nombre():
    """Test updating product category with valid nombre."""
    categoria = ProductoCategoriaUpdateRequest(nombre="Pizzas")
    assert categoria.nombre == "Pizzas"


def test_update_producto_categoria_all_none():
    """Test updating product category with no fields (all optional)."""
    categoria = ProductoCategoriaUpdateRequest()
    assert categoria.nombre is None


def test_update_producto_categoria_empty_nombre():
    """Test that empty nombre string is rejected in update."""
    with pytest.raises(ValidationError) as exc_info:
        ProductoCategoriaUpdateRequest(nombre="")
    errors = exc_info.value.errors()
    assert any(error["loc"] == ("nombre",) for error in errors)


def test_update_producto_categoria_nombre_too_long():
    """Test that nombre > 50 chars is rejected in update."""
    with pytest.raises(ValidationError) as exc_info:
        ProductoCategoriaUpdateRequest(nombre="B" * 51)
    errors = exc_info.value.errors()
    assert any(error["loc"] == ("nombre",) for error in errors)


# ==================== ProductoCategoriaResponse Tests ====================

def test_producto_categoria_response_valid():
    """Test product category response model with valid data."""
    response = ProductoCategoriaResponse(id=1, nombre="Empanadas", activo=True)
    assert response.id == 1
    assert response.nombre == "Empanadas"
    assert response.activo is True


def test_producto_categoria_response_inactive():
    """Test product category response with activo=False."""
    response = ProductoCategoriaResponse(id=2, nombre="Bebidas", activo=False)
    assert response.activo is False


def test_producto_categoria_response_missing_id():
    """Test that missing id is rejected."""
    with pytest.raises(ValidationError) as exc_info:
        ProductoCategoriaResponse(nombre="Test", activo=True)
    errors = exc_info.value.errors()
    assert any(error["loc"] == ("id",) for error in errors)


def test_producto_categoria_response_missing_nombre():
    """Test that missing nombre is rejected."""
    with pytest.raises(ValidationError) as exc_info:
        ProductoCategoriaResponse(id=1, activo=True)
    errors = exc_info.value.errors()
    assert any(error["loc"] == ("nombre",) for error in errors)
