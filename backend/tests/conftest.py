"""
Pytest configuration and shared fixtures.
Provides common fixtures for all tests including mocks and test clients.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI

from app.main import app as application, container
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


@pytest.fixture
def mock_sequence_repo():
    """Mock sequence repository for order number generation."""
    repo = AsyncMock()
    
    # Default behaviors
    repo.get_for_update = AsyncMock(return_value=None)
    repo.create = AsyncMock(return_value=None)
    repo.update = AsyncMock(return_value=None)
    
    return repo


# ==================== Mock Unit of Work Fixture ====================

@pytest.fixture
def mock_uow(mock_category_repo, mock_product_repo, mock_offer_repo, mock_sale_repo, mock_sequence_repo):
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
    uow.sequence_repo = mock_sequence_repo
    
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


# ==================== Mock Application Service Fixtures ====================

@pytest.fixture
def mock_category_service():
    """Mock CategoryService for router tests."""
    service = MagicMock()
    
    # ServiceResult mock with default values
    result = MagicMock()
    result.error = None
    result.status_code = 200
    result.value = None
    
    service.create = AsyncMock(return_value=result)
    service.get_all = AsyncMock(return_value=[])
    service.get_by_id = AsyncMock(return_value=result)
    service.update = AsyncMock(return_value=result)
    service.delete = AsyncMock(return_value=result)
    
    return service


@pytest.fixture
def mock_product_service():
    """Mock ProductService for router tests."""
    service = MagicMock()
    
    # ServiceResult mock with default values
    result = MagicMock()
    result.error = None
    result.status_code = 200
    result.value = None
    
    service.create = AsyncMock(return_value=result)
    service.get_all = AsyncMock(return_value=[])
    service.get_by_id = AsyncMock(return_value=result)
    service.update = AsyncMock(return_value=result)
    
    return service


@pytest.fixture
def mock_offer_service():
    """Mock OfferService for router tests."""
    service = MagicMock()
    
    # ServiceResult mock with default values
    result = MagicMock()
    result.error = None
    result.status_code = 200
    result.value = None
    
    service.create = AsyncMock(return_value=result)
    service.get_all = AsyncMock(return_value=[])
    service.get_by_id = AsyncMock(return_value=result)
    service.update = AsyncMock(return_value=result)
    
    return service


@pytest.fixture
def mock_sale_service():
    """Mock SaleService for router tests."""
    service = MagicMock()
    
    # ServiceResult mock with default values
    result = MagicMock()
    result.error = None
    result.status_code = 200
    result.value = None
    
    service.create = AsyncMock(return_value=result)
    service.get_all = AsyncMock(return_value=[])
    service.count_all = AsyncMock(return_value=0)
    service.get_by_id = AsyncMock(return_value=result)
    service.update = AsyncMock(return_value=result)
    service.delete = AsyncMock(return_value=result)
    
    return service


@pytest.fixture
def mock_dashboard_service():
    """Mock DashboardService for router tests."""
    service = MagicMock()
    
    # ServiceResult mock with default values
    result = MagicMock()
    result.error = None
    result.status_code = 200
    result.value = []
    
    service.get_revenue_by_period = AsyncMock(return_value=result)
    service.get_weekday_revenue = AsyncMock(return_value=result)
    service.get_top_products = AsyncMock(return_value=result)
    service.get_sales_by_category = AsyncMock(return_value=result)
    
    return service


# ==================== FastAPI Test Client Fixtures ====================

# ==================== HTTP Client Fixture ====================

@pytest.fixture
async def async_client(mock_category_service, mock_product_service, mock_offer_service, mock_sale_service, mock_dashboard_service):
    """
    Async HTTP client for testing API endpoints.
    Uses container overrides to inject mocked services.
    """
    # Override services in the dependency-injector container
    container.category_service.override(mock_category_service)
    container.product_service.override(mock_product_service)
    container.offer_service.override(mock_offer_service)
    container.sale_service.override(mock_sale_service)
    container.dashboard_service.override(mock_dashboard_service)
    
    try:
        transport = ASGITransport(app=application, raise_app_exceptions=False)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client
    finally:
        # Reset overrides after test
        container.category_service.reset_override()
        container.product_service.reset_override()
        container.offer_service.reset_override()
        container.sale_service.reset_override()
        container.dashboard_service.reset_override()


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
