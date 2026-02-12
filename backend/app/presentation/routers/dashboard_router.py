from fastapi import APIRouter, Depends, HTTPException, status, Query
from dependency_injector.wiring import inject, Provide
from typing import List

from app.application.dashboard_service import DashboardService
from app.containers import Container
from app.presentation.schemas.dashboard_schemas import (
    RevenuePorPeriodoResponse,
    ProductoDestacadoResponse,
    VentasPorCategoriaResponse,
    WeekdayRevenueResponse,
    TipoPeriodo,
    FiltroTiempo,
)
from app.presentation.routers.dependencies import get_current_user


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
    dependencies=[Depends(get_current_user)],
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
    service: DashboardService = Depends(Provide[Container.dashboard_service]),
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
    service: DashboardService = Depends(Provide[Container.dashboard_service]),
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
    service: DashboardService = Depends(Provide[Container.dashboard_service]),
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
    service: DashboardService = Depends(Provide[Container.dashboard_service]),
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
