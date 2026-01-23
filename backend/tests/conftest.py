"""
Pytest configuration and shared fixtures.
Provides common fixtures for all tests including mocks and test clients.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient
from fastapi import FastAPI

from app.main import app as application
from app.containers import Container
from tests.helpers import (
    build_category_model,
    build_product_model,
    build_offer_model,
    build_sale_model,
)


# ==================== Mock Repository Fixtures ====================

@pytest.fixture
def mock_category_repo():
    """Mock category repository with common return values."""
    repo = AsyncMock()
    
    # Default behaviors
    repo.add = AsyncMock(return_value=None)
    repo.get_all = AsyncMock(return_value=[])
    repo.get_by_id = AsyncMock(return_value=None)
    repo.update = AsyncMock(return_value=None)
    repo.delete = AsyncMock(return_value=None)
    
    return repo


@pytest.fixture
def mock_product_repo():
    """Mock product repository with common return values."""
    repo = AsyncMock()
    
    # Default behaviors
    repo.add = AsyncMock(return_value=None)
    repo.get_all = AsyncMock(return_value=[])
    repo.get_by_id = AsyncMock(return_value=None)
    repo.update = AsyncMock(return_value=None)
    repo.delete = AsyncMock(return_value=None)
    repo.delete_product_prices = AsyncMock(return_value=None)
    
    return repo


@pytest.fixture
def mock_offer_repo():
    """Mock offer repository with common return values."""
    repo = AsyncMock()
    
    # Default behaviors
    repo.add = AsyncMock(return_value=None)
    repo.get_all = AsyncMock(return_value=[])
    repo.get_by_id = AsyncMock(return_value=None)
    repo.update = AsyncMock(return_value=None)
    repo.delete = AsyncMock(return_value=None)
    repo.delete_products_offers = AsyncMock(return_value=None)
    
    return repo


@pytest.fixture
def mock_sale_repo():
    """Mock sale repository with common return values."""
    repo = AsyncMock()
    
    # Default behaviors
    repo.add = AsyncMock(return_value=None)
    repo.get_all = AsyncMock(return_value=[])
    repo.get_by_id = AsyncMock(return_value=None)
    
    return repo


# ==================== Mock Unit of Work Fixture ====================

@pytest.fixture
def mock_uow(mock_category_repo, mock_product_repo, mock_offer_repo, mock_sale_repo):
    """
    Mock Unit of Work with all repositories.
    Configured as async context manager.
    """
    uow = AsyncMock()
    
    # Attach repositories
    uow.category_repo = mock_category_repo
    uow.product_repo = mock_product_repo
    uow.offer_repo = mock_offer_repo
    uow.sale_repo = mock_sale_repo
    
    # Configure async context manager
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock(return_value=None)
    
    # Configure commit and rollback
    uow.commit = AsyncMock(return_value=None)
    uow.rollback = AsyncMock(return_value=None)
    
    return uow


# ==================== Mock Services Fixtures ====================

@pytest.fixture
def mock_file_service():
    """Mock file service for image upload handling."""
    service = MagicMock()
    
    # Default behaviors
    service.save_file = MagicMock(return_value="uploads/productos/test_image.jpg")
    service.delete_file = MagicMock(return_value=None)
    service.validate_file = MagicMock(return_value=True)
    
    return service


@pytest.fixture
def mock_logger():
    """Mock structlog logger."""
    logger = MagicMock()
    
    # Configure logging methods
    logger.debug = MagicMock()
    logger.info = MagicMock()
    logger.warning = MagicMock()
    logger.error = MagicMock()
    logger.bind = MagicMock(return_value=logger)
    
    return logger


# ==================== FastAPI Test Client Fixtures ====================

@pytest.fixture
def test_container():
    """Create a test container with mocked dependencies."""
    container = Container()
    return container


@pytest.fixture
async def async_client(test_container):
    """
    Async HTTP client for testing API endpoints.
    Uses dependency overrides to inject mocked services.
    """
    # Create a fresh app instance for testing
    app = application
    
    # Override container for testing
    # Note: Services will be mocked individually in test files
    # by overriding app.dependency_overrides
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


# ==================== Reusable Model Fixtures ====================

@pytest.fixture
def sample_category():
    """Sample category model for testing."""
    return build_category_model(
        id=1,
        nombre="Empanadas",
        descripcion="Empanadas artesanales"
    )


@pytest.fixture
def sample_product():
    """Sample product model with prices for testing."""
    return build_product_model(
        id=1,
        nombre="Empanada de Carne",
        categoria_id=1,
        imagen="uploads/productos/empanada.jpg",
        activo=True
    )


@pytest.fixture
def sample_product_without_image():
    """Sample product model without image."""
    return build_product_model(
        id=2,
        nombre="Empanada de Pollo",
        categoria_id=1,
        imagen=None,
        activo=True
    )


@pytest.fixture
def sample_offer():
    """Sample offer model with items for testing."""
    return build_offer_model(
        id=1,
        nombre="Promo Docena",
        descripcion="12 empanadas surtidas",
        precio=10000.0,
        activo=True
    )


@pytest.fixture
def sample_sale():
    """Sample sale model with items for testing."""
    return build_sale_model(
        id=1,
        numero_orden="ORD-001",
        total=6000.0
    )


# ==================== Pytest Configuration ====================

@pytest.fixture(autouse=True)
def reset_dependency_overrides():
    """
    Automatically reset FastAPI dependency overrides after each test.
    This ensures test isolation.
    """
    yield
    application.dependency_overrides = {}


# ==================== Helper Fixtures for Common Test Scenarios ====================

@pytest.fixture
def multiple_categories():
    """Multiple category models for list testing."""
    return [
        build_category_model(1, "Empanadas", "Empanadas artesanales"),
        build_category_model(2, "Pizzas", "Pizzas caseras"),
        build_category_model(3, "Bebidas", "Bebidas frías")
    ]


@pytest.fixture
def multiple_products():
    """Multiple product models for list testing."""
    return [
        build_product_model(1, "Empanada de Carne", 1, None, True),
        build_product_model(2, "Empanada de Pollo", 1, None, True),
        build_product_model(3, "Pizza Muzzarella", 2, None, True)
    ]


@pytest.fixture
def inactive_product():
    """Inactive product model for testing filters."""
    return build_product_model(
        id=4,
        nombre="Producto Inactivo",
        categoria_id=1,
        imagen=None,
        activo=False
    )
