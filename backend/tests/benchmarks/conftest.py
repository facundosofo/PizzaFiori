"""
Shared fixtures for all benchmark modules.

- run_async: runs async callables in a module-scoped event loop (no per-call loop creation overhead)
- bench_client: httpx AsyncClient with all services mocked and JWT bypassed (scope=module)
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport

from app.main import app as application, container
from app.presentation.middleware.jwt_middleware import JWTMiddleware
from app.presentation.routers.dependencies import get_current_user, require_admin


# ──────────────────────────────────────────────────────────────────────────────
# Event loop & async runner
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def event_loop():
    """Module-scoped event loop — reused across every benchmark in the module."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
def run_async(event_loop):
    """
    Helper that runs an async callable synchronously using the module event loop.

    Usage in benchmarks:
        async def _call():
            return await service.some_method()
        benchmark(run_async, _call)
    """
    def _run(async_fn, *args, **kwargs):
        return event_loop.run_until_complete(async_fn(*args, **kwargs))
    return _run


# ──────────────────────────────────────────────────────────────────────────────
# Mock service builders (mirrors tests/conftest.py, but plain functions not fixtures)
# ──────────────────────────────────────────────────────────────────────────────

def _make_service_result(value=None, status_code=200):
    result = MagicMock()
    result.error = None
    result.status_code = status_code
    result.value = value if value is not None else []
    return result


def _make_cache_service():
    cache = MagicMock()
    cache.get = MagicMock(return_value=None)
    cache.set = MagicMock(return_value=None)
    cache.invalidate = MagicMock(return_value=None)
    cache.clear_all = MagicMock(return_value=None)
    return cache


def _make_product_category_service():
    s = MagicMock()
    r = _make_service_result()
    s.create = AsyncMock(return_value=r)
    s.get_all = AsyncMock(return_value=[])
    s.get_by_id = AsyncMock(return_value=r)
    s.update = AsyncMock(return_value=r)
    s.deactivate = AsyncMock(return_value=r)
    return s


def _make_product_service():
    s = MagicMock()
    r = _make_service_result()
    s.create = AsyncMock(return_value=r)
    s.get_all = AsyncMock(return_value=[])
    s.get_by_id = AsyncMock(return_value=r)
    s.update = AsyncMock(return_value=r)
    s.bulk_update_prices = AsyncMock(return_value=r)
    return s


def _make_offer_service():
    s = MagicMock()
    r = _make_service_result()
    s.create = AsyncMock(return_value=r)
    s.get_all = AsyncMock(return_value=[])
    s.get_by_id = AsyncMock(return_value=r)
    s.update = AsyncMock(return_value=r)
    s.deactivate = AsyncMock(return_value=r)
    s.deactivate_by_product = AsyncMock(return_value=[])
    return s


def _make_sale_service():
    s = MagicMock()
    r = _make_service_result()
    s.create = AsyncMock(return_value=r)
    s.get_all = AsyncMock(return_value=[])
    s.count_all = AsyncMock(return_value=0)
    s.get_by_id = AsyncMock(return_value=r)
    s.update = AsyncMock(return_value=r)
    s.delete = AsyncMock(return_value=r)
    s.get_available_years = AsyncMock(return_value=[2025, 2026])
    return s


def _make_dashboard_service():
    s = MagicMock()
    r = _make_service_result()
    s.get_revenue_by_period = AsyncMock(return_value=r)
    s.get_weekday_revenue = AsyncMock(return_value=r)
    s.get_top_products = AsyncMock(return_value=r)
    s.get_sales_by_category = AsyncMock(return_value=r)
    s.get_balance_metrics = AsyncMock(return_value=r)
    s.get_monthly_balance_data = AsyncMock(return_value=r)
    return s


def _make_user_service():
    s = MagicMock()
    r = _make_service_result()
    s.register_user = AsyncMock(return_value=r)
    s.authenticate_user = AsyncMock(return_value=r)
    s.get_user = AsyncMock(return_value=r)
    s.get_all_users = AsyncMock(return_value=r)
    s.update_user = AsyncMock(return_value=r)
    s.change_password = AsyncMock(return_value=r)
    s.delete_user = AsyncMock(return_value=r)
    s.unlock_user_account = AsyncMock(return_value=r)
    return s


def _make_expense_service():
    s = MagicMock()
    r = _make_service_result()
    s.create = AsyncMock(return_value=r)
    s.get_by_id = AsyncMock(return_value=r)
    s.list_all = AsyncMock(return_value=r)
    s.list_by_filters = AsyncMock(return_value=r)
    s.update = AsyncMock(return_value=r)
    s.delete = AsyncMock(return_value=r)
    return s


def _make_expense_category_service():
    s = MagicMock()
    r = _make_service_result()
    s.create = AsyncMock(return_value=r)
    s.get_by_id = AsyncMock(return_value=r)
    s.list_all = AsyncMock(return_value=r)
    s.list_by_parent = AsyncMock(return_value=r)
    s.update = AsyncMock(return_value=r)
    s.delete = AsyncMock(return_value=r)
    return s


def _make_stock_service():
    s = MagicMock()
    r = _make_service_result()
    s.get_all_stocks = AsyncMock(return_value=r)
    s.add_stock = AsyncMock(return_value=r)
    s.configure_alerts = AsyncMock(return_value=r)
    s.get_movements = AsyncMock(return_value=r)
    return s


def _make_report_service():
    s = MagicMock()
    s.generate_expense_report = AsyncMock(return_value=b"%PDF-mock")
    report_result = MagicMock()
    report_result.error = None
    report_result.pdf_bytes = b"%PDF-mock-general"
    s.generate_general_report = AsyncMock(return_value=report_result)
    return s


def _make_audit_service():
    s = AsyncMock()
    r = MagicMock()
    r.error = None
    r.status_code = 201
    r.value = MagicMock(id=1)
    s.log_creation = AsyncMock(return_value=r)
    s.log_update = AsyncMock(return_value=r)
    s.log_deletion = AsyncMock(return_value=r)
    list_result = MagicMock()
    list_result.error = None
    list_result.status_code = 200
    list_result.value = {"records": [], "total": 0}
    s.get_by_date_range = AsyncMock(return_value=list_result)
    return s


def _make_sales_analytics_service():
    s = MagicMock()
    r = _make_service_result()
    s.get_revenue_by_period = AsyncMock(return_value=r)
    s.get_sales_by_category = AsyncMock(return_value=r)
    s.get_weekday_revenue = AsyncMock(return_value=r)
    s.get_total_sales_with_comparison = AsyncMock(return_value=r)
    return s


def _make_product_analytics_service():
    s = MagicMock()
    r = _make_service_result()
    s.get_top_products = AsyncMock(return_value=r)
    s.get_products_summary = AsyncMock(return_value=r)
    return s


def _make_expense_analytics_service():
    s = MagicMock()
    r = _make_service_result()
    s.get_expenses_by_period = AsyncMock(return_value=r)
    s.get_expenses_by_month = AsyncMock(return_value=r)
    s.get_expenses_by_category = AsyncMock(return_value=r)
    s.get_expenses_summary = AsyncMock(return_value=r)
    s.get_total_expenses_with_comparison = AsyncMock(return_value=r)
    return s


# ──────────────────────────────────────────────────────────────────────────────
# HTTP client fixture
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def bench_client(event_loop):
    """
    Module-scoped httpx AsyncClient.
    All services are mocked and JWT is bypassed (admin user).
    Reused across every HTTP benchmark in the module — no overhead per benchmark call.
    """
    mock_admin = {"id": 1, "username": "bench_admin", "role": "ADMIN"}

    # Build fresh mock services
    mock_cache = _make_cache_service()
    mock_product_cat = _make_product_category_service()
    mock_product = _make_product_service()
    mock_offer = _make_offer_service()
    mock_sale = _make_sale_service()
    mock_dashboard = _make_dashboard_service()
    mock_user = _make_user_service()
    mock_expense = _make_expense_service()
    mock_expense_cat = _make_expense_category_service()
    mock_stock = _make_stock_service()
    mock_report = _make_report_service()
    mock_audit = _make_audit_service()
    mock_sales_analytics = _make_sales_analytics_service()
    mock_product_analytics = _make_product_analytics_service()
    mock_expense_analytics = _make_expense_analytics_service()

    # Override DI container
    container.cache_service.override(mock_cache)
    container.product_category_service.override(mock_product_cat)
    container.product_service.override(mock_product)
    container.offer_service.override(mock_offer)
    container.sale_service.override(mock_sale)
    container.dashboard_service.override(mock_dashboard)
    container.user_service.override(mock_user)
    container.expense_service.override(mock_expense)
    container.expense_category_service.override(mock_expense_cat)
    container.stock_service.override(mock_stock)
    container.report_service.override(mock_report)
    container.audit_service.override(mock_audit)
    container.sales_analytics_service.override(mock_sales_analytics)
    container.product_analytics_service.override(mock_product_analytics)
    container.expense_analytics_service.override(mock_expense_analytics)

    # Override auth dependencies
    application.dependency_overrides[get_current_user] = lambda: mock_admin
    application.dependency_overrides[require_admin] = lambda: mock_admin

    async def _jwt_bypass(self, request, call_next):
        request.state.current_user = mock_admin
        return await call_next(request)

    async def _setup():
        transport = ASGITransport(app=application, raise_app_exceptions=False)
        client = AsyncClient(transport=transport, base_url="http://test", follow_redirects=True)
        await client.__aenter__()
        return client

    async def _teardown(client):
        await client.__aexit__(None, None, None)

    with patch.object(JWTMiddleware, "dispatch", _jwt_bypass):
        client = event_loop.run_until_complete(_setup())
        yield client
        event_loop.run_until_complete(_teardown(client))

    # Reset overrides
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
