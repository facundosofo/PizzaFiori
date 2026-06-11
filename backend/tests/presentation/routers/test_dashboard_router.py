"""
Tests para los endpoints de dashboard.
Enfocados en verificar respuestas HTTP correctas con diferentes params.
"""
import pytest
from httpx import AsyncClient


# --- Tests GET /dashboard/revenue ---
# This endpoint uses SalesAnalyticsService (not DashboardService)

@pytest.mark.asyncio
async def test_get_revenue_daily_default(async_client: AsyncClient, mock_sales_analytics_service):
    """Obtener revenue diario con parámetros default retorna 200"""
    mock_sales_analytics_service.get_revenue_by_period.return_value.value = [
        {"fecha": "2026-02-10", "ingresos": 10000.0, "pedidos": 5, "cantidad": 20}
    ]
    
    response = await async_client.get("/dashboard/revenue")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["fecha"] == "2026-02-10"


@pytest.mark.asyncio
async def test_get_revenue_monthly(async_client: AsyncClient, mock_sales_analytics_service):
    """Obtener revenue mensual retorna 200"""
    mock_sales_analytics_service.get_revenue_by_period.return_value.value = [
        {"mes": "Ene 2026", "ingresos": 150000.0, "pedidos": 120, "cantidad": 600}
    ]
    
    response = await async_client.get("/dashboard/revenue?period=monthly&limit=12")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["mes"] == "Ene 2026"


@pytest.mark.asyncio
async def test_get_revenue_yearly(async_client: AsyncClient, mock_sales_analytics_service):
    """Obtener revenue anual retorna 200"""
    mock_sales_analytics_service.get_revenue_by_period.return_value.value = [
        {"año": "2026", "ingresos": 1800000.0, "pedidos": 1200, "cantidad": 5000}
    ]
    
    response = await async_client.get("/dashboard/revenue?period=yearly&limit=5")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["año"] == "2026"


@pytest.mark.asyncio
async def test_get_revenue_weekly(async_client: AsyncClient, mock_sales_analytics_service):
    """Obtener revenue semanal retorna 200"""
    mock_sales_analytics_service.get_revenue_by_period.return_value.value = [
        {"semana": "01-07 Feb", "ingresos": 95000.0, "pedidos": 320, "cantidad": 780}
    ]

    response = await async_client.get("/dashboard/revenue?period=weekly&limit=12")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["semana"] == "01-07 Feb"


@pytest.mark.asyncio
async def test_get_revenue_limit_validation(async_client: AsyncClient):
    """Límite fuera de rango retorna 422"""
    response = await async_client.get("/dashboard/revenue?limit=500")
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_revenue_service_error(async_client: AsyncClient, mock_sales_analytics_service):
    """Error del servicio retorna 500"""
    mock_sales_analytics_service.get_revenue_by_period.return_value.error = "Database error"
    mock_sales_analytics_service.get_revenue_by_period.return_value.status_code = 500
    
    response = await async_client.get("/dashboard/revenue")
    
    assert response.status_code == 500


# --- Tests GET /dashboard/revenue/weekday ---
# This endpoint uses SalesAnalyticsService

@pytest.mark.asyncio
async def test_get_weekday_revenue_sin_filtro(async_client: AsyncClient, mock_sales_analytics_service):
    """Obtener revenue por día de semana sin filtro retorna 200"""
    mock_sales_analytics_service.get_weekday_revenue.return_value.value = [
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
async def test_get_weekday_revenue_con_categoria(async_client: AsyncClient, mock_sales_analytics_service):
    """Obtener revenue por día filtrado por categoría retorna 200"""
    mock_sales_analytics_service.get_weekday_revenue.return_value.value = [
        {"dia_semana": "Viernes", "promedio_ingresos": 12000.0, "promedio_pedidos": 6.0, "promedio_cantidad": 35.0},
    ]
    
    response = await async_client.get("/dashboard/revenue/weekday?category=Pizzas")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1


@pytest.mark.asyncio
async def test_get_weekday_revenue_service_error(async_client: AsyncClient, mock_sales_analytics_service):
    """Error del servicio retorna 500"""
    mock_sales_analytics_service.get_weekday_revenue.return_value.error = "Query failed"
    mock_sales_analytics_service.get_weekday_revenue.return_value.status_code = 500
    
    response = await async_client.get("/dashboard/revenue/weekday")
    
    assert response.status_code == 500


# --- Tests GET /dashboard/products/top ---
# This endpoint uses ProductAnalyticsService

@pytest.mark.asyncio
async def test_get_top_products_default(async_client: AsyncClient, mock_product_analytics_service):
    """Obtener top productos con parámetros default retorna 200"""
    mock_product_analytics_service.get_top_products.return_value.value = [
        {"nombre": "Muzzarella", "categoria": "Pizzas", "cantidad": 50, "precio": 1200.0, "enStock": True},
    ]
    
    response = await async_client.get("/dashboard/products/top")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["nombre"] == "Muzzarella"


@pytest.mark.asyncio
async def test_get_top_products_bottom(async_client: AsyncClient, mock_product_analytics_service):
    """Obtener productos menos vendidos retorna 200"""
    mock_product_analytics_service.get_top_products.return_value.value = [
        {"nombre": "Fugazzeta", "categoria": "Pizzas", "cantidad": 2, "precio": 1500.0, "enStock": True},
    ]
    
    response = await async_client.get("/dashboard/products/top?sort=bottom&limit=5")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1


@pytest.mark.asyncio
async def test_get_top_products_con_filtros(async_client: AsyncClient, mock_product_analytics_service):
    """Obtener top productos con filtro de tiempo y categoría retorna 200"""
    mock_product_analytics_service.get_top_products.return_value.value = [
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
async def test_get_top_products_service_error(async_client: AsyncClient, mock_product_analytics_service):
    """Error del servicio retorna 500"""
    mock_product_analytics_service.get_top_products.return_value.error = "Timeout"
    mock_product_analytics_service.get_top_products.return_value.status_code = 500
    
    response = await async_client.get("/dashboard/products/top")
    
    assert response.status_code == 500


# --- Tests GET /dashboard/sales-by-category ---
# This endpoint uses SalesAnalyticsService

@pytest.mark.asyncio
async def test_get_sales_by_category_sin_limite(async_client: AsyncClient, mock_sales_analytics_service):
    """Obtener ventas por categoría sin límite retorna 200"""
    mock_sales_analytics_service.get_sales_by_category.return_value.value = [
        {"categoria": "Pizzas", "cantidad": 120},
        {"categoria": "Empanadas", "cantidad": 80},
    ]
    
    response = await async_client.get("/dashboard/sales-by-category")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["categoria"] == "Pizzas"


@pytest.mark.asyncio
async def test_get_sales_by_category_con_limite(async_client: AsyncClient, mock_sales_analytics_service):
    """Obtener top 5 categorías por ventas retorna 200"""
    mock_sales_analytics_service.get_sales_by_category.return_value.value = [
        {"categoria": "Pizzas", "cantidad": 120},
    ]
    
    response = await async_client.get("/dashboard/sales-by-category?limit=5")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1


@pytest.mark.asyncio
async def test_get_sales_by_category_con_time_filter(async_client: AsyncClient, mock_sales_analytics_service):
    """Obtener ventas por categoría filtrado por tiempo retorna 200"""
    mock_sales_analytics_service.get_sales_by_category.return_value.value = [
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
async def test_get_sales_by_category_service_error(async_client: AsyncClient, mock_sales_analytics_service):
    """Error del servicio retorna 500"""
    mock_sales_analytics_service.get_sales_by_category.return_value.error = "Connection lost"
    mock_sales_analytics_service.get_sales_by_category.return_value.status_code = 500
    
    response = await async_client.get("/dashboard/sales-by-category")
    
    assert response.status_code == 500


# --- Tests GET /dashboard/expenses ---
# This endpoint uses ExpenseAnalyticsService

@pytest.mark.asyncio
async def test_get_expenses_default(async_client: AsyncClient, mock_expense_analytics_service):
    """Obtener gastos mensuales con parámetros default retorna 200"""
    mock_expense_analytics_service.get_expenses_by_period.return_value.value = [
        {"mes": "Feb 2026", "gastos": 50000.0}
    ]
    
    response = await async_client.get("/dashboard/expenses")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1


@pytest.mark.asyncio
async def test_get_expenses_service_error(async_client: AsyncClient, mock_expense_analytics_service):
    """Error del servicio de gastos retorna 500"""
    mock_expense_analytics_service.get_expenses_by_period.return_value.error = "DB error"
    mock_expense_analytics_service.get_expenses_by_period.return_value.status_code = 500
    
    response = await async_client.get("/dashboard/expenses")
    
    assert response.status_code == 500


# --- Tests GET /dashboard/expenses/summary ---

@pytest.mark.asyncio
async def test_get_expenses_summary(async_client: AsyncClient, mock_expense_analytics_service):
    """Obtener resumen de gastos retorna 200"""
    mock_expense_analytics_service.get_expenses_summary.return_value.value = {
        "resultado_mensual": 80000.0, "variacion_mensual_pct": 6.67,
        "comparacion_mes": "Enero", "resultado_anual": 960000.0,
        "variacion_anual_pct": 3.5, "comparacion_ano": 2025,
        "categoria_mayor_crecimiento": None,
    }
    
    response = await async_client.get("/dashboard/expenses/summary")
    
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_expenses_summary_error(async_client: AsyncClient, mock_expense_analytics_service):
    """Error en resumen de gastos retorna 500"""
    mock_expense_analytics_service.get_expenses_summary.return_value.error = "fail"
    mock_expense_analytics_service.get_expenses_summary.return_value.status_code = 500
    
    response = await async_client.get("/dashboard/expenses/summary")
    
    assert response.status_code == 500


# --- Tests GET /dashboard/expenses/monthly ---

@pytest.mark.asyncio
async def test_get_expenses_monthly(async_client: AsyncClient, mock_expense_analytics_service):
    """Obtener gastos mensuales retorna 200"""
    mock_expense_analytics_service.get_expenses_by_month.return_value.value = [
        {"mes": "Ene 2026", "gastos": 45000.0}
    ]
    
    response = await async_client.get("/dashboard/expenses/monthly")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1


# --- Tests GET /dashboard/expenses/by-category ---

@pytest.mark.asyncio
async def test_get_expenses_by_category(async_client: AsyncClient, mock_expense_analytics_service):
    """Obtener gastos por categoría retorna 200"""
    mock_expense_analytics_service.get_expenses_by_category.return_value.value = [
        {"categoria": "Insumos", "gastos": 30000.0}
    ]
    
    response = await async_client.get("/dashboard/expenses/by-category")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1


@pytest.mark.asyncio
async def test_get_expenses_by_category_error(async_client: AsyncClient, mock_expense_analytics_service):
    """Error en gastos por categoría retorna 500"""
    mock_expense_analytics_service.get_expenses_by_category.return_value.error = "fail"
    mock_expense_analytics_service.get_expenses_by_category.return_value.status_code = 500
    
    response = await async_client.get("/dashboard/expenses/by-category")
    
    assert response.status_code == 500


# --- Tests GET /dashboard/products/summary ---
# This endpoint uses ProductAnalyticsService

@pytest.mark.asyncio
async def test_get_products_summary(async_client: AsyncClient, mock_product_analytics_service):
    """Obtener resumen de productos retorna 200"""
    mock_product_analytics_service.get_products_summary.return_value.value = {
        "producto_mas_vendido": "Muzzarella",
        "cantidad_mas_vendida": 120,
        "promocion_mas_vendida": None,
        "cantidad_promocion": 0,
        "mes_actual": "Marzo 2026",
    }
    
    response = await async_client.get("/dashboard/products/summary")
    
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_products_summary_error(async_client: AsyncClient, mock_product_analytics_service):
    """Error en resumen de productos retorna 500"""
    mock_product_analytics_service.get_products_summary.return_value.error = "fail"
    mock_product_analytics_service.get_products_summary.return_value.status_code = 500
    
    response = await async_client.get("/dashboard/products/summary")
    
    assert response.status_code == 500


# --- Tests GET /dashboard/sales/total ---
# This endpoint uses SalesAnalyticsService

@pytest.mark.asyncio
async def test_get_total_sales(async_client: AsyncClient, mock_sales_analytics_service):
    """Obtener ventas totales con comparativa retorna 200"""
    mock_sales_analytics_service.get_total_sales_with_comparison.return_value.value = {
        "current": 250000.0, "previous": 230000.0, "comparison_type": "MoM",
    }
    
    response = await async_client.get("/dashboard/sales/total")
    
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_total_sales_error(async_client: AsyncClient, mock_sales_analytics_service):
    """Error en ventas totales retorna 500"""
    mock_sales_analytics_service.get_total_sales_with_comparison.return_value.error = "fail"
    mock_sales_analytics_service.get_total_sales_with_comparison.return_value.status_code = 500
    
    response = await async_client.get("/dashboard/sales/total")
    
    assert response.status_code == 500


# --- Tests GET /dashboard/expenses/total ---
# This endpoint uses ExpenseAnalyticsService

@pytest.mark.asyncio
async def test_get_total_expenses(async_client: AsyncClient, mock_expense_analytics_service):
    """Obtener gastos totales con comparativa retorna 200"""
    mock_expense_analytics_service.get_total_expenses_with_comparison.return_value.value = {
        "current": 95000.0, "previous": 88000.0, "comparison_type": "MoM",
    }
    
    response = await async_client.get("/dashboard/expenses/total")
    
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_total_expenses_error(async_client: AsyncClient, mock_expense_analytics_service):
    """Error en gastos totales retorna 500"""
    mock_expense_analytics_service.get_total_expenses_with_comparison.return_value.error = "fail"
    mock_expense_analytics_service.get_total_expenses_with_comparison.return_value.status_code = 500
    
    response = await async_client.get("/dashboard/expenses/total")
    
    assert response.status_code == 500


# --- Tests GET /dashboard/general/reporte/pdf ---

@pytest.mark.asyncio
async def test_generate_general_report_pdf(async_client: AsyncClient, mock_report_service):
    """Generar reporte general PDF retorna 200"""
    response = await async_client.get("/dashboard/general/reporte/pdf")
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"


@pytest.mark.asyncio
async def test_generate_general_report_invalid_dates(async_client: AsyncClient, mock_report_service):
    """Fechas invertidas retorna 422"""
    response = await async_client.get(
        "/dashboard/general/reporte/pdf?fecha_desde=2026-03-01&fecha_hasta=2026-01-01"
    )
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_generate_general_report_error(async_client: AsyncClient, mock_report_service):
    """Error al generar reporte retorna 500"""
    mock_report_service.generate_general_report.return_value.error = "PDF generation failed"
    mock_report_service.generate_general_report.return_value.status_code = 500
    
    response = await async_client.get("/dashboard/general/reporte/pdf")
    
    assert response.status_code == 500


# --- Tests GET /dashboard/balance ---
# This endpoint uses DashboardService

@pytest.mark.asyncio
async def test_get_balance_metrics(async_client: AsyncClient, mock_dashboard_service):
    """Obtener métricas de balance retorna 200"""
    mock_dashboard_service.get_balance_metrics.return_value.value = {
        "sales": {"current": 250000.0, "previous": 230000.0, "comparison_type": "MoM"},
        "expenses": {"current": 95000.0, "previous": 88000.0, "comparison_type": "MoM"},
        "net_profit": {"sales": 250000.0, "expenses": 95000.0, "net_profit": 155000.0, "previous_net": 142000.0, "comparison_type": "MoM"},
        "net_margin": {"sales": 250000.0, "expenses": 95000.0, "margin": 62.0, "previous_margin": 61.7, "comparison_type": "MoM"},
    }
    
    response = await async_client.get("/dashboard/balance")
    
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_balance_metrics_error(async_client: AsyncClient, mock_dashboard_service):
    """Error en balance retorna 500"""
    mock_dashboard_service.get_balance_metrics.return_value.error = "fail"
    mock_dashboard_service.get_balance_metrics.return_value.status_code = 500
    
    response = await async_client.get("/dashboard/balance")
    
    assert response.status_code == 500


# --- Tests GET /dashboard/balance/monthly ---
# This endpoint uses DashboardService

@pytest.mark.asyncio
async def test_get_monthly_balance_data(async_client: AsyncClient, mock_dashboard_service):
    """Obtener datos mensuales de balance retorna 200"""
    mock_dashboard_service.get_monthly_balance_data.return_value.value = {
        "data": [{"month": "Ene", "sales": 100000.0, "expenses": 60000.0}],
        "current_month": "Mar",
    }
    
    response = await async_client.get("/dashboard/balance/monthly")
    
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_monthly_balance_yearly(async_client: AsyncClient, mock_dashboard_service):
    """Obtener datos anuales de balance retorna 200"""
    mock_dashboard_service.get_monthly_balance_data.return_value.value = {
        "data": [{"month": "2025", "sales": 1200000.0, "expenses": 800000.0}],
        "current_month": "2026",
    }
    
    response = await async_client.get("/dashboard/balance/monthly?period=yearly")
    
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_monthly_balance_error(async_client: AsyncClient, mock_dashboard_service):
    """Error en balance mensual retorna 500"""
    mock_dashboard_service.get_monthly_balance_data.return_value.error = "fail"
    mock_dashboard_service.get_monthly_balance_data.return_value.status_code = 500
    
    response = await async_client.get("/dashboard/balance/monthly")
    
    assert response.status_code == 500
