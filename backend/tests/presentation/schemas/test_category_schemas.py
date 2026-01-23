"""
Tests for category schemas validation.
Tests Pydantic models for category creation and updates.
"""

import pytest
from pydantic import ValidationError

from app.presentation.schemas.category_schemas import (
    CategoriaCreateRequest,
    CategoriaUpdateRequest,
    CategoriaResponse
)


# ==================== CategoriaCreateRequest Tests ====================

def test_create_categoria_valid():
    """Test creating a valid category with all fields."""
    data = {
        "nombre": "Empanadas",
        "descripcion": "Empanadas artesanales"
    }
    
    categoria = CategoriaCreateRequest(**data)
    
    assert categoria.nombre == "Empanadas"
    assert categoria.descripcion == "Empanadas artesanales"


def test_create_categoria_valid_without_descripcion():
    """Test creating a valid category without optional description."""
    data = {
        "nombre": "Pizzas"
    }
    
    categoria = CategoriaCreateRequest(**data)
    
    assert categoria.nombre == "Pizzas"
    assert categoria.descripcion is None


def test_create_categoria_empty_nombre():
    """Test that empty nombre is rejected."""
    data = {
        "nombre": "",
        "descripcion": "Test"
    }
    
    with pytest.raises(ValidationError) as exc_info:
        CategoriaCreateRequest(**data)
    
    errors = exc_info.value.errors()
    assert len(errors) > 0
    assert any(error["loc"] == ("nombre",) for error in errors)


def test_create_categoria_missing_nombre():
    """Test that missing nombre is rejected."""
    data = {
        "descripcion": "Test"
    }
    
    with pytest.raises(ValidationError) as exc_info:
        CategoriaCreateRequest(**data)
    
    errors = exc_info.value.errors()
    assert len(errors) > 0
    assert any(error["loc"] == ("nombre",) for error in errors)


# ==================== CategoriaUpdateRequest Tests ====================

def test_update_categoria_valid_all_fields():
    """Test updating category with all fields."""
    data = {
        "nombre": "Empanadas Gourmet",
        "descripcion": "Nueva descripción"
    }
    
    categoria = CategoriaUpdateRequest(**data)
    
    assert categoria.nombre == "Empanadas Gourmet"
    assert categoria.descripcion == "Nueva descripción"


def test_update_categoria_valid_partial():
    """Test updating category with only nombre."""
    data = {
        "nombre": "Empanadas Premium"
    }
    
    categoria = CategoriaUpdateRequest(**data)
    
    assert categoria.nombre == "Empanadas Premium"
    assert categoria.descripcion is None


def test_update_categoria_valid_only_descripcion():
    """Test updating category with only descripcion."""
    data = {
        "descripcion": "Descripción actualizada"
    }
    
    categoria = CategoriaUpdateRequest(**data)
    
    assert categoria.nombre is None
    assert categoria.descripcion == "Descripción actualizada"


def test_update_categoria_empty_fields():
    """Test updating category with empty fields (all None)."""
    data = {}
    
    categoria = CategoriaUpdateRequest(**data)
    
    assert categoria.nombre is None
    assert categoria.descripcion is None


def test_update_categoria_empty_nombre():
    """Test that empty nombre string is rejected in update."""
    data = {
        "nombre": ""
    }
    
    with pytest.raises(ValidationError) as exc_info:
        CategoriaUpdateRequest(**data)
    
    errors = exc_info.value.errors()
    assert len(errors) > 0
    assert any(error["loc"] == ("nombre",) for error in errors)


# ==================== CategoriaResponse Tests ====================

def test_categoria_response_valid():
    """Test category response model with valid data."""
    data = {
        "id": 1,
        "nombre": "Empanadas",
        "descripcion": "Empanadas artesanales"
    }
    
    response = CategoriaResponse(**data)
    
    assert response.id == 1
    assert response.nombre == "Empanadas"
    assert response.descripcion == "Empanadas artesanales"


def test_categoria_response_without_descripcion():
    """Test category response without description."""
    data = {
        "id": 1,
        "nombre": "Pizzas",
        "descripcion": None
    }
    
    response = CategoriaResponse(**data)
    
    assert response.id == 1
    assert response.nombre == "Pizzas"
    assert response.descripcion is None


def test_categoria_response_missing_required_fields():
    """Test that missing required fields are rejected."""
    data = {
        "nombre": "Test"
    }
    
    with pytest.raises(ValidationError) as exc_info:
        CategoriaResponse(**data)
    
    errors = exc_info.value.errors()
    assert len(errors) > 0
    assert any(error["loc"] == ("id",) for error in errors)
