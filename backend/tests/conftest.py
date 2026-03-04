"""
Pytest configuration and shared fixtures.
Provides common fixtures for all tests including mocks and test clients.
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI

from app.main import app as application, container
from app.containers import Container
from app.presentation.middleware.jwt_middleware import JWTMiddleware
from app.presentation.routers.dependencies import get_current_user, require_admin
from tests.helpers import (
    build_category_model,
    build_product_model,
    build_offer_model,
    build_sale_model,
    build_user_model,
    build_expense_model,
    build_expense_category_model,
    build_audit_log_model,
    build_stock_model,
)
# ==================== Mock Repository Fixtures ====================

@pytest.fixture
def mock_product_category_repo():
    """Mock product category repository with common return values."""
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


@pytest.fixture
def mock_user_repo():
    """Mock user repository with common return values."""
    repo = AsyncMock()
    repo.add = AsyncMock(return_value=None)
    repo.get_by_id = AsyncMock(return_value=None)
    repo.get_by_username = AsyncMock(return_value=None)
    repo.get_by_email = AsyncMock(return_value=None)
    repo.list = AsyncMock(return_value=[])
    repo.list_by_role = AsyncMock(return_value=[])
    repo.update = AsyncMock(return_value=None)
    repo.delete = AsyncMock(return_value=None)
    repo.refresh = AsyncMock(return_value=None)
    return repo


@pytest.fixture
def mock_audit_repo():
    """Mock audit repository with common return values."""
    repo = AsyncMock()
    repo.log_action = AsyncMock(return_value=MagicMock(id=1))
    repo.get_by_date_range = AsyncMock(return_value=[])
    repo.get_by_entity = AsyncMock(return_value=[])
    repo.count = AsyncMock(return_value=0)
    return repo


@pytest.fixture
def mock_expense_category_repo():
    """Mock expense category repository with common return values."""
    repo = AsyncMock()
    repo.add = AsyncMock(return_value=None)
    repo.get_by_id = AsyncMock(return_value=None)
    repo.get_by_id_with_subcategories = AsyncMock(return_value=None)
    repo.list = AsyncMock(return_value=[])
    repo.list_by_active = AsyncMock(return_value=[])
    repo.get_by_parent_id = AsyncMock(return_value=[])
    repo.update = AsyncMock(return_value=None)
    repo.delete = AsyncMock(return_value=None)
    repo.refresh = AsyncMock(return_value=None)
    return repo


@pytest.fixture
def mock_expense_repo():
    """Mock expense repository with common return values."""
    repo = AsyncMock()
    repo.add = AsyncMock(return_value=None)
    repo.get_by_id = AsyncMock(return_value=None)
    repo.get_by_id_with_category = AsyncMock(return_value=None)
    repo.list = AsyncMock(return_value=[])
    repo.list_by_filters = AsyncMock(return_value=[])
    repo.update = AsyncMock(return_value=None)
    repo.delete = AsyncMock(return_value=None)
    repo.refresh = AsyncMock(return_value=None)
    return repo


@pytest.fixture
def mock_stock_repo():
    """Mock stock repository with common return values."""
    repo = AsyncMock()
    repo.get_all = AsyncMock(return_value=[])
    repo.get_by_categoria_id = AsyncMock(return_value=None)
    repo.upsert = AsyncMock(return_value=None)
    return repo


# ==================== Mock Unit of Work Fixture ====================

@pytest.fixture
def mock_uow(
    mock_product_category_repo, mock_product_repo, mock_offer_repo,
    mock_sale_repo, mock_sequence_repo, mock_user_repo, mock_audit_repo,
    mock_expense_category_repo, mock_expense_repo, mock_stock_repo
):
    """
    Mock Unit of Work with all repositories.
    Configured as async context manager.
    """
    uow = AsyncMock()
    
    # Attach repositories
    uow.product_category_repo = mock_product_category_repo
    uow.product_repo = mock_product_repo
    uow.offer_repo = mock_offer_repo
    uow.sale_repo = mock_sale_repo
    uow.sequence_repo = mock_sequence_repo
    uow.users = mock_user_repo
    uow.audit_repo = mock_audit_repo
    uow.expense_category_repo = mock_expense_category_repo
    uow.expense_repo = mock_expense_repo
    uow.stock_repo = mock_stock_repo
    
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
def mock_cache_service():
    """Mock CacheService — always returns None (cache miss) and ignores writes."""
    cache = MagicMock()
    cache.get = MagicMock(return_value=None)   # Always miss — no cached data
    cache.set = MagicMock(return_value=None)
    cache.invalidate = MagicMock(return_value=None)
    return cache


@pytest.fixture
def mock_product_category_service():
    """Mock ProductCategoryService for router tests."""
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
    service.deactivate = AsyncMock(return_value=result)
    
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
def mock_audit_service():
    """Mock AuditService for service unit tests."""
    service = AsyncMock()
    result = MagicMock()
    result.error = None
    result.status_code = 201
    result.value = MagicMock(id=1)
    service.log_creation = AsyncMock(return_value=result)
    service.log_update = AsyncMock(return_value=result)
    service.log_deletion = AsyncMock(return_value=result)
    service.get_by_date_range = AsyncMock(return_value=MagicMock(value={"records": [], "total": 0}, error=None, status_code=200))
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
    service.get_balance_metrics = AsyncMock(return_value=result)
    service.get_monthly_balance_data = AsyncMock(return_value=result)
    
    return service


@pytest.fixture
def mock_user_service():
    """Mock UserService for router tests."""
    service = MagicMock()
    result = MagicMock()
    result.error = None
    result.status_code = 200
    result.value = None
    service.register_user = AsyncMock(return_value=result)
    service.authenticate_user = AsyncMock(return_value=result)
    service.get_user = AsyncMock(return_value=result)
    service.get_all_users = AsyncMock(return_value=result)
    service.update_user = AsyncMock(return_value=result)
    service.change_password = AsyncMock(return_value=result)
    service.delete_user = AsyncMock(return_value=result)
    service.unlock_user_account = AsyncMock(return_value=result)
    return service


@pytest.fixture
def mock_expense_service():
    """Mock ExpenseService for router tests."""
    service = MagicMock()
    result = MagicMock()
    result.error = None
    result.status_code = 200
    result.value = None
    service.create = AsyncMock(return_value=result)
    service.get_by_id = AsyncMock(return_value=result)
    service.list_all = AsyncMock(return_value=result)
    service.list_by_filters = AsyncMock(return_value=result)
    service.update = AsyncMock(return_value=result)
    service.delete = AsyncMock(return_value=result)
    return service


@pytest.fixture
def mock_expense_category_service():
    """Mock ExpenseCategoryService for router tests."""
    service = MagicMock()
    result = MagicMock()
    result.error = None
    result.status_code = 200
    result.value = None
    service.create = AsyncMock(return_value=result)
    service.get_by_id = AsyncMock(return_value=result)
    service.list_all = AsyncMock(return_value=result)
    service.list_by_parent = AsyncMock(return_value=result)
    service.update = AsyncMock(return_value=result)
    service.delete = AsyncMock(return_value=result)
    return service


@pytest.fixture
def mock_stock_service():
    """Mock StockService for router tests."""
    service = MagicMock()
    result = MagicMock()
    result.error = None
    result.status_code = 200
    result.value = None
    service.get_all_stocks = AsyncMock(return_value=result)
    service.add_stock = AsyncMock(return_value=result)
    service.configure_alerts = AsyncMock(return_value=result)
    service.get_movements = AsyncMock(return_value=result)
    return service


@pytest.fixture
def mock_report_service():
    """Mock ReportService for router tests."""
    service = MagicMock()
    service.generate_expense_report = AsyncMock(return_value=b"%PDF-mock")
    # General report returns ServiceResult-like object with pdf_bytes
    general_result = MagicMock()
    general_result.error = None
    general_result.pdf_bytes = b"%PDF-mock-general"
    service.generate_general_report = AsyncMock(return_value=general_result)
    return service


@pytest.fixture
def mock_sales_analytics_service():
    """Mock SalesAnalyticsService for router tests."""
    service = MagicMock()
    result = MagicMock()
    result.error = None
    result.status_code = 200
    result.value = []
    service.get_revenue_by_period = AsyncMock(return_value=result)
    service.get_sales_by_category = AsyncMock(return_value=result)
    service.get_weekday_revenue = AsyncMock(return_value=result)
    service.get_total_sales_with_comparison = AsyncMock(return_value=result)
    return service


@pytest.fixture
def mock_product_analytics_service():
    """Mock ProductAnalyticsService for router tests."""
    service = MagicMock()
    result = MagicMock()
    result.error = None
    result.status_code = 200
    result.value = []
    service.get_top_products = AsyncMock(return_value=result)
    service.get_products_summary = AsyncMock(return_value=result)
    return service


@pytest.fixture
def mock_expense_analytics_service():
    """Mock ExpenseAnalyticsService for router tests."""
    service = MagicMock()
    result = MagicMock()
    result.error = None
    result.status_code = 200
    result.value = []
    service.get_expenses_by_period = AsyncMock(return_value=result)
    service.get_expenses_by_month = AsyncMock(return_value=result)
    service.get_expenses_by_category = AsyncMock(return_value=result)
    service.get_expenses_summary = AsyncMock(return_value=result)
    service.get_total_expenses_with_comparison = AsyncMock(return_value=result)
    return service


# ==================== FastAPI Test Client Fixtures ====================

# ==================== HTTP Client Fixture ====================

@pytest_asyncio.fixture
async def async_client(
    mock_cache_service, mock_product_category_service, mock_product_service,
    mock_offer_service, mock_sale_service, mock_dashboard_service,
    mock_user_service, mock_expense_service, mock_expense_category_service,
    mock_stock_service, mock_report_service, mock_audit_service,
    mock_sales_analytics_service, mock_product_analytics_service,
    mock_expense_analytics_service,
):
    """
    Async HTTP client for testing API endpoints.
    Uses container overrides to inject mocked services.
    Bypasses JWT middleware by mocking it with a test admin user.
    """
    # Mock admin user for all tests
    mock_admin_user = {"id": 1, "username": "admin_test", "role": "ADMIN"}

    async def mock_jwt_dispatch(self, request, call_next):
        """Bypass JWT validation in tests — always authenticate as admin."""
        request.state.current_user = mock_admin_user
        return await call_next(request)

    # Override services in the dependency-injector container
    container.cache_service.override(mock_cache_service)
    container.product_category_service.override(mock_product_category_service)
    container.product_service.override(mock_product_service)
    container.offer_service.override(mock_offer_service)
    container.sale_service.override(mock_sale_service)
    container.dashboard_service.override(mock_dashboard_service)
    container.user_service.override(mock_user_service)
    container.expense_service.override(mock_expense_service)
    container.expense_category_service.override(mock_expense_category_service)
    container.stock_service.override(mock_stock_service)
    container.report_service.override(mock_report_service)
    container.audit_service.override(mock_audit_service)
    container.sales_analytics_service.override(mock_sales_analytics_service)
    container.product_analytics_service.override(mock_product_analytics_service)
    container.expense_analytics_service.override(mock_expense_analytics_service)

    # Override auth dependencies so get_current_user / require_admin always succeed
    application.dependency_overrides[get_current_user] = lambda: mock_admin_user
    application.dependency_overrides[require_admin] = lambda: mock_admin_user

    try:
        with patch.object(JWTMiddleware, 'dispatch', mock_jwt_dispatch):
            transport = ASGITransport(app=application, raise_app_exceptions=False)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                yield client
    finally:
        # Reset overrides after test
        container.cache_service.reset_override()
        container.product_category_service.reset_override()
        container.product_service.reset_override()
        container.offer_service.reset_override()
        container.sale_service.reset_override()
        container.dashboard_service.reset_override()
        container.user_service.reset_override()
        container.expense_service.reset_override()
        container.expense_category_service.reset_override()
        container.stock_service.reset_override()
        container.report_service.reset_override()
        container.audit_service.reset_override()
        container.sales_analytics_service.reset_override()
        container.product_analytics_service.reset_override()
        container.expense_analytics_service.reset_override()
        application.dependency_overrides.clear()


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
