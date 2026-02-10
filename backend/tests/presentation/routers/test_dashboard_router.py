"""
Tests para los endpoints de dashboard.
Enfocados en verificar respuestas HTTP correctas con diferentes params.
"""
import pytest
from httpx import AsyncClient


# --- Tests GET /dashboard/revenue ---

@pytest.mark.asyncio
async def test_get_revenue_daily_default(async_client: AsyncClient, mock_dashboard_service):
    """Obtener revenue diario con parámetros default retorna 200"""
    mock_dashboard_service.get_revenue_by_period.return_value.value = [
        {"fecha": "2026-02-10", "ingresos": 10000.0, "pedidos": 5, "cantidad": 20}
    ]
    
    response = await async_client.get("/dashboard/revenue")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["fecha"] == "2026-02-10"


@pytest.mark.asyncio
async def test_get_revenue_monthly(async_client: AsyncClient, mock_dashboard_service):
    """Obtener revenue mensual retorna 200"""
    mock_dashboard_service.get_revenue_by_period.return_value.value = [
        {"mes": "Ene 2026", "ingresos": 150000.0, "pedidos": 120, "cantidad": 600}
    ]
    
    response = await async_client.get("/dashboard/revenue?period=monthly&limit=12")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["mes"] == "Ene 2026"


@pytest.mark.asyncio
async def test_get_revenue_yearly(async_client: AsyncClient, mock_dashboard_service):
    """Obtener revenue anual retorna 200"""
    mock_dashboard_service.get_revenue_by_period.return_value.value = [
        {"año": "2026", "ingresos": 1800000.0, "pedidos": 1200, "cantidad": 5000}
    ]
    
    response = await async_client.get("/dashboard/revenue?period=yearly&limit=5")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["año"] == "2026"


@pytest.mark.asyncio
async def test_get_revenue_limit_validation(async_client: AsyncClient):
    """Límite fuera de rango retorna 422"""
    response = await async_client.get("/dashboard/revenue?limit=500")
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_revenue_service_error(async_client: AsyncClient, mock_dashboard_service):
    """Error del servicio retorna 500"""
    mock_dashboard_service.get_revenue_by_period.return_value.error = "Database error"
    mock_dashboard_service.get_revenue_by_period.return_value.status_code = 500
    
    response = await async_client.get("/dashboard/revenue")
    
    assert response.status_code == 500


# --- Tests GET /dashboard/revenue/weekday ---

@pytest.mark.asyncio
async def test_get_weekday_revenue_sin_filtro(async_client: AsyncClient, mock_dashboard_service):
    """Obtener revenue por día de semana sin filtro retorna 200"""
    mock_dashboard_service.get_weekday_revenue.return_value.value = [
        {"dia_semana": "Lunes", "promedio_ingresos": 8000.0, "promedio_pedidos": 4.5, "promedio_cantidad": 25.0},
        {"dia_semana": "Martes", "promedio_ingresos": 7500.0, "promedio_pedidos": 4.0, "promedio_cantidad": 22.0},
    ]
    
    response = await async_client.get("/dashboard/revenue/weekday")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["dia_semana"] == "Lunes"


@pytest.mark.asyncio
async def test_get_weekday_revenue_con_categoria(async_client: AsyncClient, mock_dashboard_service):
    """Obtener revenue por día filtrado por categoría retorna 200"""
    mock_dashboard_service.get_weekday_revenue.return_value.value = [
        {"dia_semana": "Viernes", "promedio_ingresos": 12000.0, "promedio_pedidos": 6.0, "promedio_cantidad": 35.0},
    ]
    
    response = await async_client.get("/dashboard/revenue/weekday?category=Pizzas")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1


@pytest.mark.asyncio
async def test_get_weekday_revenue_service_error(async_client: AsyncClient, mock_dashboard_service):
    """Error del servicio retorna 500"""
    mock_dashboard_service.get_weekday_revenue.return_value.error = "Query failed"
    mock_dashboard_service.get_weekday_revenue.return_value.status_code = 500
    
    response = await async_client.get("/dashboard/revenue/weekday")
    
    assert response.status_code == 500


# --- Tests GET /dashboard/products/top ---

@pytest.mark.asyncio
async def test_get_top_products_default(async_client: AsyncClient, mock_dashboard_service):
    """Obtener top productos con parámetros default retorna 200"""
    mock_dashboard_service.get_top_products.return_value.value = [
        {"nombre": "Muzzarella", "categoria": "Pizzas", "cantidad": 50, "precio": 1200.0, "enStock": True},
    ]
    
    response = await async_client.get("/dashboard/products/top")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["nombre"] == "Muzzarella"


@pytest.mark.asyncio
async def test_get_top_products_bottom(async_client: AsyncClient, mock_dashboard_service):
    """Obtener productos menos vendidos retorna 200"""
    mock_dashboard_service.get_top_products.return_value.value = [
        {"nombre": "Fugazzeta", "categoria": "Pizzas", "cantidad": 2, "precio": 1500.0, "enStock": True},
    ]
    
    response = await async_client.get("/dashboard/products/top?sort=bottom&limit=5")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1


@pytest.mark.asyncio
async def test_get_top_products_con_filtros(async_client: AsyncClient, mock_dashboard_service):
    """Obtener top productos con filtro de tiempo y categoría retorna 200"""
    mock_dashboard_service.get_top_products.return_value.value = [
        {"nombre": "Napolitana", "categoria": "Pizzas", "cantidad": 15, "precio": 1300.0, "enStock": True},
    ]
    
    response = await async_client.get("/dashboard/products/top?time_filter=last_7_days&category=Pizzas")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["categoria"] == "Pizzas"


@pytest.mark.asyncio
async def test_get_top_products_limit_validation(async_client: AsyncClient):
    """Límite inválido retorna 422"""
    response = await async_client.get("/dashboard/products/top?limit=200")
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_top_products_service_error(async_client: AsyncClient, mock_dashboard_service):
    """Error del servicio retorna 500"""
    mock_dashboard_service.get_top_products.return_value.error = "Timeout"
    mock_dashboard_service.get_top_products.return_value.status_code = 500
    
    response = await async_client.get("/dashboard/products/top")
    
    assert response.status_code == 500


# --- Tests GET /dashboard/sales-by-category ---

@pytest.mark.asyncio
async def test_get_sales_by_category_sin_limite(async_client: AsyncClient, mock_dashboard_service):
    """Obtener ventas por categoría sin límite retorna 200"""
    mock_dashboard_service.get_sales_by_category.return_value.value = [
        {"categoria": "Pizzas", "cantidad": 120},
        {"categoria": "Empanadas", "cantidad": 80},
    ]
    
    response = await async_client.get("/dashboard/sales-by-category")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["categoria"] == "Pizzas"


@pytest.mark.asyncio
async def test_get_sales_by_category_con_limite(async_client: AsyncClient, mock_dashboard_service):
    """Obtener top 5 categorías por ventas retorna 200"""
    mock_dashboard_service.get_sales_by_category.return_value.value = [
        {"categoria": "Pizzas", "cantidad": 120},
    ]
    
    response = await async_client.get("/dashboard/sales-by-category?limit=5")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1


@pytest.mark.asyncio
async def test_get_sales_by_category_con_time_filter(async_client: AsyncClient, mock_dashboard_service):
    """Obtener ventas por categoría filtrado por tiempo retorna 200"""
    mock_dashboard_service.get_sales_by_category.return_value.value = [
        {"categoria": "Bebidas", "cantidad": 45},
    ]
    
    response = await async_client.get("/dashboard/sales-by-category?time_filter=today")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["categoria"] == "Bebidas"


@pytest.mark.asyncio
async def test_get_sales_by_category_limit_validation(async_client: AsyncClient):
    """Límite inválido retorna 422"""
    response = await async_client.get("/dashboard/sales-by-category?limit=150")
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_sales_by_category_service_error(async_client: AsyncClient, mock_dashboard_service):
    """Error del servicio retorna 500"""
    mock_dashboard_service.get_sales_by_category.return_value.error = "Connection lost"
    mock_dashboard_service.get_sales_by_category.return_value.status_code = 500
    
    response = await async_client.get("/dashboard/sales-by-category")
    
    assert response.status_code == 500
