from fastapi import APIRouter, Depends, HTTPException, status, Path, Body, Query
from dependency_injector.wiring import inject, Provide
from typing import List

from app.application.stock_service import StockService, ServiceResult as StockServiceResult
from app.containers import Container
from app.presentation.schemas.stock_schemas import (
    AddStockRequest,
    ConfigureAlertsRequest,
    CategoryStockResponse,
    StockMovementResponse,
)
from app.presentation.routers.dependencies import get_current_user, require_admin

router = APIRouter(
    tags=["Stock"],
    dependencies=[Depends(get_current_user)],
)


@router.get(
    "/stock",
    response_model=List[CategoryStockResponse],
    summary="Obtener stock actual por categoría",
    description="Devuelve el stock actual de todas las categorías activas.",
)
@inject
async def get_all_stocks(
    service: StockService = Depends(Provide[Container.stock_service]),
):
    result: StockServiceResult = await service.get_all_stocks()
    if result.error:
        raise HTTPException(status_code=result.status_code, detail=result.error)
    return result.value


@router.post(
    "/stock/{categoria_id}/agregar",
    response_model=CategoryStockResponse,
    summary="Agregar stock a una categoría",
    description="Incrementa el stock de una categoría. Solo administradores.",
    responses={
        403: {"description": "Admin access required"},
        404: {"description": "Categoría no encontrada"},
    },
)
@inject
async def add_stock(
    categoria_id: int = Path(..., ge=1),
    body: AddStockRequest = Body(...),
    admin_user: dict = Depends(require_admin),
    service: StockService = Depends(Provide[Container.stock_service]),
):
    result: StockServiceResult = await service.add_stock(
        categoria_id=categoria_id,
        cantidad=body.cantidad,
        username=admin_user["username"],
    )
    if result.error:
        raise HTTPException(status_code=result.status_code, detail=result.error)
    return result.value


@router.put(
    "/stock/{categoria_id}/alertas",
    response_model=CategoryStockResponse,
    summary="Configurar umbrales de alerta de stock",
    description="Configura los umbrales de alerta amarilla y roja para una categoría. Solo administradores.",
    responses={
        403: {"description": "Admin access required"},
        404: {"description": "Categoría no encontrada"},
    },
)
@inject
async def configure_alerts(
    categoria_id: int = Path(..., ge=1),
    body: ConfigureAlertsRequest = Body(...),
    admin_user: dict = Depends(require_admin),
    service: StockService = Depends(Provide[Container.stock_service]),
):
    result: StockServiceResult = await service.configure_alerts(
        categoria_id=categoria_id,
        umbral_amarillo=body.umbral_amarillo,
        umbral_rojo=body.umbral_rojo,
        username=admin_user["username"],
    )
    if result.error:
        raise HTTPException(status_code=result.status_code, detail=result.error)
    return result.value


@router.get(
    "/stock/{categoria_id}/movimientos",
    response_model=List[StockMovementResponse],
    summary="Historial de movimientos de stock",
    description="Devuelve el historial de movimientos de stock para una categoría. Solo administradores.",
    responses={403: {"description": "Admin access required"}},
)
@inject
async def get_movements(
    categoria_id: int = Path(..., ge=1),
    limit: int = Query(50, ge=1, le=200),
    admin_user: dict = Depends(require_admin),
    service: StockService = Depends(Provide[Container.stock_service]),
):
    result: StockServiceResult = await service.get_movements(
        categoria_id=categoria_id,
        limit=limit,
    )
    if result.error:
        raise HTTPException(status_code=result.status_code, detail=result.error)
    return result.value
