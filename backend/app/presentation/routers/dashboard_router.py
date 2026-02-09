from fastapi import APIRouter, Depends, HTTPException, status, Query
from dependency_injector.wiring import inject, Provide
from typing import List

from app.application.dashboard_service import DashboardService
from app.containers import Container
from app.presentation.schemas.dashboard_schemas import (
    RevenuePorPeriodoResponse,
    RevenueEn12MesesResponse,
    ProductoDestacadoResponse,
    VentasPorCategoriaResponse,
    MetricasDashboardResponse,
    TipoPeriodo,
)


router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get(
    "/revenue",
    response_model=List[dict],
    summary="Obtener revenue por período",
    description="Devuelve el revenue agrupado por período (daily, weekly, monthly, yearly).",
    responses={
        400: {"description": "Período inválido"},
        500: {"description": "Error interno del servidor"},
    },
)
@inject
async def get_revenue(
    period: TipoPeriodo = Query(
        TipoPeriodo.DIARIO,
        description="Tipo de período: daily, weekly, monthly, yearly"
    ),
    limit: int = Query(30, ge=1, le=365, description="Cantidad de registros a devolver"),
    service: DashboardService = Depends(Provide[Container.dashboard_service]),
):
    """
    Obtiene datos de revenue agrupados por el período especificado.
    
    **Períodos disponibles:**
    - `daily`: Últimos 30 días (default)
    - `weekly`: Últimas 12 semanas
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
    "/revenue/monthly",
    response_model=List[RevenueEn12MesesResponse],
    summary="Obtener distribución mensuales (12 meses)",
    description="Devuelve el revenue para cada mes del año actual.",
    responses={
        500: {"description": "Error interno del servidor"},
    },
)
@inject
async def get_monthly_revenue(
    service: DashboardService = Depends(Provide[Container.dashboard_service]),
):
    """
    Obtiene datos de revenue distribuidos para cada mes del año actual.
    
    Retorna exactamente 12 registros (Ene a Dic) incluidos los meses con 0 órdenes.
    """
    result = await service.get_monthly_revenue()
    
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
    period: TipoPeriodo = Query(
        TipoPeriodo.ANUAL,
        description="Tipo de período: daily, weekly, monthly, yearly"
    ),
    sort: str = Query("top", description="Orden: 'top' (más vendidos) o 'bottom' (menos vendidos)"),
    category: str | None = Query(None, description="Filtrar por categoría (opcional)"),
    service: DashboardService = Depends(Provide[Container.dashboard_service]),
):
    """
    Obtiene los N productos más o menos vendidos ordenados según el parámetro sort.
    
    Los datos se basan en el historial completo de ventas.
    """
    result = await service.get_top_products(limit=limit, period=period, sort=sort, category=category)
    
    if result.error:
        raise HTTPException(
            status_code=result.status_code,
            detail=result.error
        )
    
    return result.value


@router.get(
    "/metrics",
    response_model=MetricasDashboardResponse,
    summary="Obtener métricas generales",
    description="Devuelve métricas consolidadas del dashboard.",
    responses={
        500: {"description": "Error interno del servidor"},
    },
)
@inject
async def get_metrics(
    service: DashboardService = Depends(Provide[Container.dashboard_service]),
):
    """
    Obtiene métricas generales del dashboard:
    - Revenue total de todos los tiempos
    - Cantidad total de órdenes realizadas
    """
    result = await service.get_metrics()
    
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
    period: TipoPeriodo = Query(
        TipoPeriodo.ANUAL,
        description="Tipo de período: daily, weekly, monthly, yearly"
    ),
    service: DashboardService = Depends(Provide[Container.dashboard_service]),
):
    """
    Obtiene cantidad vendida por categoria.

    Se incluyen productos directos y productos de ofertas.
    """
    result = await service.get_sales_by_category(limit=limit, period=period)

    if result.error:
        raise HTTPException(
            status_code=result.status_code,
            detail=result.error
        )

    return result.value
