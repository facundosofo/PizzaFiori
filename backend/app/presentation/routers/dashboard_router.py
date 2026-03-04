from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import Response
from dependency_injector.wiring import inject, Provide
from typing import List
from datetime import date

from app.application.report_service import ReportService
from app.application.sales_analytics_service import SalesAnalyticsService
from app.application.product_analytics_service import ProductAnalyticsService
from app.application.expense_analytics_service import ExpenseAnalyticsService
from app.application.dashboard_service import DashboardService
from app.containers import Container
from app.presentation.schemas.dashboard_schemas import (
    RevenuePorPeriodoResponse,
    ProductoDestacadoResponse,
    VentasPorCategoriaResponse,
    WeekdayRevenueResponse,
    GastosPorMesResponse,
    GastosPorCategoriaResponse,
    GastosPorAnoResponse,
    ResumenGastosPeriodoResponse,
    ResumenProductosResponse,
    TotalSalesKPIResponse,
    TotalExpensesKPIResponse,
    NetProfitKPIResponse,
    NetMarginKPIResponse,
    BalanceMetricsResponse,
    MonthlyBalanceListResponse,
    TipoPeriodo,
    FiltroTiempo,
)
from app.presentation.routers.dependencies import require_admin


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
    dependencies=[Depends(require_admin)],
)


@router.get(
    "/revenue",
    response_model=List[RevenuePorPeriodoResponse],
    summary="Obtener revenue por período",
    description="Devuelve el revenue agrupado por período (daily, monthly, yearly).",
    responses={
        400: {"description": "Período inválido"},
        500: {"description": "Error interno del servidor"},
    },
)
@inject
async def get_revenue(
    period: TipoPeriodo = Query(
        TipoPeriodo.DIARIO,
        description="Tipo de período: daily, monthly, yearly"
    ),
    limit: int = Query(30, ge=1, le=365, description="Cantidad de registros a devolver"),
    service: SalesAnalyticsService = Depends(Provide[Container.sales_analytics_service]),
):
    """
    Obtiene datos de revenue agrupados por el período especificado.
    
    **Períodos disponibles:**
    - `daily`: Últimos 30 días (default)
    - `monthly`: Últimos 12 meses
    - `yearly`: Últimos 5 años
    """
    result = await service.get_revenue_by_period(period=period, limit=limit)
    
    if result.error:
        raise HTTPException(
            status_code=result.status_code,
            detail=result.error
        )
    
    return result.value

@router.get(
    "/revenue/weekday",
    response_model=List[WeekdayRevenueResponse],
    summary="Obtener promedio de ventas por día de semana",
    description="Devuelve el promedio de ingresos y cantidad por día de semana (histórico, con ajuste de horario de negocio 16:00-06:00).",
    responses={
        500: {"description": "Error interno del servidor"},
    },
)
@inject
async def get_weekday_revenue(
    category: str | None = Query(None, description="Filtrar por categoría (opcional)"),
    service: SalesAnalyticsService = Depends(Provide[Container.sales_analytics_service]),
):
    """
    Obtiene promedio de ventas por día de semana ajustado al horario de negocio (datos históricos).
    
    **Horario de negocio:** 16:00 a 06:00  
    Las ventas entre 00:00 y 05:59 se asignan al día anterior (día que abrió a las 16:00).
    
    Retorna 7 registros ordenados de Lunes a Domingo.
    """
    result = await service.get_weekday_revenue(category=category)
    
    if result.error:
        raise HTTPException(
            status_code=result.status_code,
            detail=result.error
        )
    
    return result.value


@router.get(
    "/products/top",
    response_model=List[ProductoDestacadoResponse],
    summary="Obtener productos más o menos vendidos",
    description="Devuelve productos ordenados por cantidad de unidades vendidas.",
    responses={
        500: {"description": "Error interno del servidor"},
    },
)
@inject
async def get_top_products(
    limit: int = Query(10, ge=1, le=100, description="Cantidad máxima de productos"),
    time_filter: FiltroTiempo = Query(
        FiltroTiempo.HISTORICO,
        description="Filtro de tiempo: today (hoy), last_7_days (últimos 7 días), last_month (últimos 30 días), last_year (últimos 12 meses), all_time (histórico)"
    ),
    sort: str = Query("top", description="Orden: 'top' (más vendidos) o 'bottom' (menos vendidos)"),
    category: str | None = Query(None, description="Filtrar por categoría (opcional)"),
    service: ProductAnalyticsService = Depends(Provide[Container.product_analytics_service]),
):
    """
    Obtiene los N productos más o menos vendidos ordenados según el parámetro sort.
    
    Los datos se basan en el historial completo de ventas o según el filtro de tiempo seleccionado.
    """
    result = await service.get_top_products(limit=limit, time_filter=time_filter, sort=sort, category=category)
    
    if result.error:
        raise HTTPException(
            status_code=result.status_code,
            detail=result.error
        )
    
    return result.value


@router.get(
    "/expenses",
    response_model=List[GastosPorMesResponse | GastosPorAnoResponse],
    summary="Obtener gastos por período",
    description="Devuelve gastos agrupados por período (mensual o anual).",
    responses={
        400: {"description": "Período inválido"},
        500: {"description": "Error interno del servidor"},
    },
)
@inject
async def get_expenses(
    period: TipoPeriodo = Query(
        TipoPeriodo.MENSUAL,
        description="Tipo de período: monthly (mensual), yearly (anual)"
    ),
    limit: int = Query(12, ge=1, le=36, description="Cantidad de registros a devolver"),
    category: str | None = Query(None, description="Filtrar por categoría de gasto (opcional)"),
    service: ExpenseAnalyticsService = Depends(Provide[Container.expense_analytics_service]),
):
    """
    Obtiene datos de gastos agrupados por el período especificado.
    
    **Períodos disponibles:**
    - `monthly`: Últimos 12 meses (default)
    - `yearly`: Últimos 5 años
    """
    result = await service.get_expenses_by_period(period=period, limit=limit, category=category)
    
    if result.error:
        raise HTTPException(
            status_code=result.status_code,
            detail=result.error
        )
    
    return result.value


@router.get(
    "/expenses/summary",
    response_model=ResumenGastosPeriodoResponse,
    summary="Obtener resumen de gastos",
    description="Devuelve métricas resumidas de gastos para cards del dashboard.",
    responses={
        500: {"description": "Error interno del servidor"},
    },
)
@inject
async def get_expenses_summary(
    service: ExpenseAnalyticsService = Depends(Provide[Container.expense_analytics_service]),
):
    """Obtiene resumen de gastos para cards del dashboard."""
    result = await service.get_expenses_summary()

    if result.error:
        raise HTTPException(
            status_code=result.status_code,
            detail=result.error
        )

    return result.value


@router.get(
    "/expenses/monthly",
    response_model=List[GastosPorMesResponse],
    summary="Obtener gastos por mes",
    description="Devuelve el monto total de gastos agrupado por mes.",
    responses={
        500: {"description": "Error interno del servidor"},
    },
)
@inject
async def get_expenses_by_month(
    limit: int = Query(12, ge=1, le=36, description="Cantidad de meses a devolver"),
    category: str | None = Query(None, description="Filtrar por categoría de gasto (opcional)"),
    service: ExpenseAnalyticsService = Depends(Provide[Container.expense_analytics_service]),
):
    """
    Obtiene el total de gastos por mes, con filtro opcional por categoría.
    """
    result = await service.get_expenses_by_month(limit=limit, category=category)

    if result.error:
        raise HTTPException(
            status_code=result.status_code,
            detail=result.error
        )

    return result.value


@router.get(
    "/expenses/by-category",
    response_model=List[GastosPorCategoriaResponse],
    summary="Obtener gastos por categoria",
    description="Devuelve el monto total de gastos agrupado por categoria, opcionalmente con subcategorias.",
    responses={
        500: {"description": "Error interno del servidor"},
    },
)
@inject
async def get_expenses_by_category(
    limit: int = Query(8, ge=1, le=50, description="Cantidad maxima de categorias"),
    time_filter: FiltroTiempo = Query(
        FiltroTiempo.ULTIMO_ANO,
        description="Filtro de tiempo: last_month (últimos 30 días), last_year (últimos 12 meses), all_time (histórico)"
    ),
    include_subcategories: bool = Query(
        False,
        description="Incluir subcategorías anidadas en la respuesta"
    ),
    service: ExpenseAnalyticsService = Depends(Provide[Container.expense_analytics_service]),
):
    """
    Obtiene gastos agrupados por categoria (padres incluyen subcategorias en el total).
    Si include_subcategories=true, retorna subcategorías anidadas para tabla expandible.
    """
    result = await service.get_expenses_by_category(
        limit=limit,
        time_filter=time_filter,
        include_subcategories=include_subcategories,
    )

    if result.error:
        raise HTTPException(
            status_code=result.status_code,
            detail=result.error
        )

    return result.value


@router.get(
    "/sales-by-category",
    response_model=List[VentasPorCategoriaResponse],
    summary="Obtener ventas por categoria",
    description="Devuelve la cantidad de ventas agrupadas por categoria.",
    responses={
        500: {"description": "Error interno del servidor"},
    },
)
@inject
async def get_sales_by_category(
    limit: int | None = Query(None, ge=1, le=100, description="Maximo de categorias"),
    time_filter: FiltroTiempo = Query(
        FiltroTiempo.HISTORICO,
        description="Filtro de tiempo: today (hoy), last_7_days (últimos 7 días), last_month (últimos 30 días), last_year (últimos 12 meses), all_time (histórico)"
    ),
    service: SalesAnalyticsService = Depends(Provide[Container.sales_analytics_service]),
):
    """
    Obtiene cantidad vendida por categoria.

    Se incluyen productos directos y productos de ofertas.
    """
    result = await service.get_sales_by_category(limit=limit, time_filter=time_filter)

    if result.error:
        raise HTTPException(
            status_code=result.status_code,
            detail=result.error
        )

    return result.value


@router.get(
    "/products/summary",
    response_model=ResumenProductosResponse,
    summary="Obtener resumen de productos destacados",
    description="Retorna el producto más vendido y el que genera mayor ingreso.",
    responses={
        500: {"description": "Error interno del servidor"},
    },
)
@inject
async def get_products_summary(
    time_filter: FiltroTiempo = Query(
        FiltroTiempo.HISTORICO,
        description="Filtro de tiempo: today, last_7_days, last_month, last_year, all_time"
    ),
    service: ProductAnalyticsService = Depends(Provide[Container.product_analytics_service]),
):
    """
    Obtiene dos productos destacados para mostrar en cards:
    - Producto más vendido: el que tiene mayor cantidad de unidades vendidas
    - Producto con mayor ingreso: el que genera mayor ingresos (precio x cantidad)
    """
    result = await service.get_products_summary(time_filter=time_filter)

    if result.error:
        raise HTTPException(
            status_code=result.status_code,
            detail=result.error
        )

    return result.value


@router.get(
    "/sales/total",
    response_model=TotalSalesKPIResponse,
    summary="Obtener ventas totales con comparativa",
    description="Retorna el total de ventas del mes actual (1° hasta hoy) con comparativa contra el mismo período del mes anterior.",
    responses={
        500: {"description": "Error interno del servidor"},
    },
)
@inject
async def get_total_sales(
    days: int = Query(30, ge=1, le=365, description="Ignorado (mantenido por compatibilidad)"),
    service: SalesAnalyticsService = Depends(Provide[Container.sales_analytics_service]),
):
    """
    Obtiene el total de ventas del mes calendario actual con comparativa.
    
    **Lógica de comparativa:**
    - Período actual: 1° del mes actual hasta hoy
    - Período anterior: 1° del mes anterior hasta el mismo día del mes anterior (o último día si mes anterior tiene menos días)
    
    **Parámetros:**
    - `days`: Ignorado (parámetro mantenido por compatibilidad con clientes anteriores)
    """
    result = await service.get_total_sales_with_comparison(days_in_period=days)

    if result.error:
        raise HTTPException(
            status_code=result.status_code,
            detail=result.error
        )

    return result.value


@router.get(
    "/expenses/total",
    response_model=TotalExpensesKPIResponse,
    summary="Obtener gastos totales con comparativa",
    description="Retorna el total de gastos del mes actual (1° hasta hoy) con comparativa contra el mismo período del mes anterior.",
    responses={
        500: {"description": "Error interno del servidor"},
    },
)
@inject
async def get_total_expenses(
    days: int = Query(30, ge=1, le=365, description="Ignorado (mantenido por compatibilidad)"),
    service: ExpenseAnalyticsService = Depends(Provide[Container.expense_analytics_service]),
):
    """
    Obtiene el total de gastos del mes calendario actual con comparativa.
    
    **Lógica de comparativa:**
    - Período actual: 1° del mes actual hasta hoy
    - Período anterior: 1° del mes anterior hasta el mismo día del mes anterior (o último día si mes anterior tiene menos días)
    
    **Parámetros:**
    - `days`: Ignorado (parámetro mantenido por compatibilidad con clientes anteriores)
    """
    result = await service.get_total_expenses_with_comparison(days_in_period=days)

    if result.error:
        raise HTTPException(
            status_code=result.status_code,
            detail=result.error
        )

    return result.value


@router.get(
    "/general/reporte/pdf",
    summary="Generar reporte general en PDF",
    description="Genera un reporte PDF con el balance de ingresos y gastos en el rango seleccionado.",
    responses={
        200: {"description": "PDF generado", "content": {"application/pdf": {"schema": {"type": "string", "format": "binary"}}}},
        404: {"description": "No hay datos en el período seleccionado"},
        500: {"description": "Error al generar el reporte"},
    },
)
@inject
async def generate_general_report(
    fecha_desde: date | None = Query(None, description="Fecha inicial (YYYY-MM-DD)"),
    fecha_hasta: date | None = Query(None, description="Fecha final (YYYY-MM-DD)"),
    modo: str = Query("light", description="Modo de color: 'dark' o 'light'"),
    mostrar_resumen_periodo: bool = Query(True),
    mostrar_resumen_mes: bool = Query(False),
    mostrar_resumen_categoria_ventas: bool = Query(True),
    mostrar_resumen_productos: bool = Query(True),
    mostrar_resumen_categoria_costos: bool = Query(True),
    report_service: ReportService = Depends(Provide[Container.report_service]),
):
    if fecha_desde and fecha_hasta and fecha_desde > fecha_hasta:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="fecha_desde debe ser menor o igual a fecha_hasta",
        )
    result = await report_service.generate_general_report(
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        modo=modo,
        mostrar_resumen_periodo=mostrar_resumen_periodo,
        mostrar_resumen_mes=mostrar_resumen_mes,
        mostrar_resumen_categoria_ventas=mostrar_resumen_categoria_ventas,
        mostrar_resumen_productos=mostrar_resumen_productos,
        mostrar_resumen_categoria_costos=mostrar_resumen_categoria_costos,
    )
    if result.error:
        raise HTTPException(status_code=result.status_code, detail=result.error)

    if fecha_desde and fecha_hasta:
        filename = f"reporte_general_{fecha_desde}_{fecha_hasta}.pdf"
    elif fecha_desde:
        filename = f"reporte_general_desde_{fecha_desde}.pdf"
    elif fecha_hasta:
        filename = f"reporte_general_hasta_{fecha_hasta}.pdf"
    else:
        filename = "reporte_general.pdf"

    return Response(
        content=result.pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/balance",
    response_model=BalanceMetricsResponse,
    summary="Obtener métricas de balance completas",
    description="Retorna todas las métricas de balance del mes actual (1° hasta hoy): ventas totales, gastos totales, resultado neto y margen neto con comparativas contra el mes anterior.",
    responses={
        500: {"description": "Error interno del servidor"},
    },
)
@inject
async def get_balance_metrics(
    days: int = Query(30, ge=1, le=365, description="Ignorado (mantenido por compatibilidad)"),
    service: DashboardService = Depends(Provide[Container.dashboard_service]),
):
    """
    Obtiene todas las métricas de balance del mes calendario actual.
    
    **Métricas incluidas:**
    - Ventas totales (con comparativa MoM mes calendario)
    - Gastos totales (con comparativa MoM mes calendario)
    - Resultado neto: ventas - gastos (con comparativa)
    - Margen neto: (ventas - gastos) / ventas * 100 (con diferencia en puntos porcentuales)
    
    **Lógica de comparativa:**
    - Período actual: 1° del mes actual hasta hoy
    - Período anterior: 1° del mes anterior hasta el mismo día del mes anterior (o último día si mes anterior tiene menos días)
    
    **Parámetros:**
    - `days`: Ignorado (parámetro mantenido por compatibilidad con clientes anteriores)
    """
    result = await service.get_balance_metrics(days_in_period=days)

    if result.error:
        raise HTTPException(
            status_code=result.status_code,
            detail=result.error
        )

    return result.value


@router.get(
    "/balance/monthly",
    response_model=MonthlyBalanceListResponse,
    summary="Obtener datos mensuales de balance (últimos 12 meses)",
    description="Retorna datos mensuales de ventas y gastos para los últimos 12 meses dinámicos, útil para gráficos de balance.",
    responses={
        500: {"description": "Error interno del servidor"},
    },
)
@inject
async def get_monthly_balance_data(
    period: str = Query("monthly", description="Período de agrupación: 'monthly' (últimos 12 meses) o 'yearly' (últimos 5 años)"),
    service: DashboardService = Depends(Provide[Container.dashboard_service]),
):
    """
    Obtiene datos de ventas y gastos agrupados por período para gráficos de balance.

    **Parámetros:**
    - `period`: `monthly` (últimos 12 meses) | `yearly` (últimos 5 años)

    **Formato de datos:**
    ```json
    {
      "data": [
        { "month": "Mar", "sales": 150000.0, "expenses": 95000.0 }
      ],
      "current_month": "Feb"
    }
    ```
    """
    result = await service.get_monthly_balance_data(period=period)

    if result.error:
        raise HTTPException(
            status_code=result.status_code,
            detail=result.error
        )

    return result.value
