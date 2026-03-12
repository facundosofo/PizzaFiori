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
    StockListResponse,
    ProductStockResponse,
    SaveStockConfigRequest,
)
from app.presentation.routers.dependencies import get_current_user, require_admin

router = APIRouter(
    tags=["Stock"],
    dependencies=[Depends(get_current_user)],
)


@router.get(
    "/stock",
    response_model=StockListResponse,
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


@router.get(
    "/stock/config",
    summary="Obtener configuración de stock por categoría",
    description="Devuelve el flag stock_por_producto de todas las categorías. Solo administradores.",
    responses={403: {"description": "Admin access required"}},
)
@inject
async def get_stock_config(
    admin_user: dict = Depends(require_admin),
    service: StockService = Depends(Provide[Container.stock_service]),
):
    result: StockServiceResult = await service.get_stock_config()
    if result.error:
        raise HTTPException(status_code=result.status_code, detail=result.error)
    return result.value


@router.put(
    "/stock/config",
    summary="Guardar configuración de stock por categoría",
    description="Actualiza stock_por_producto para cada categoría. Solo administradores.",
    responses={403: {"description": "Admin access required"}},
)
@inject
async def save_stock_config(
    body: SaveStockConfigRequest = Body(...),
    admin_user: dict = Depends(require_admin),
    service: StockService = Depends(Provide[Container.stock_service]),
):
    configs = [c.model_dump() for c in body.configs]
    result: StockServiceResult = await service.save_stock_config(
        configs=configs,
        username=admin_user["username"],
    )
    if result.error:
        raise HTTPException(status_code=result.status_code, detail=result.error)
    return result.value


@router.get(
    "/stock/{categoria_id}/productos",
    response_model=List[ProductStockResponse],
    summary="Desglose de stock por producto de una categoría",
    description="Devuelve el stock individual de cada producto activo de la categoría.",
)
@inject
async def get_product_stocks(
    categoria_id: int = Path(..., ge=1),
    service: StockService = Depends(Provide[Container.stock_service]),
):
    result: StockServiceResult = await service.get_product_stocks(categoria_id)
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


@router.post(
    "/stock/productos/{producto_id}/agregar",
    response_model=ProductStockResponse,
    summary="Modificar stock de un producto individual",
    description="Ajusta el stock de un producto (positivo = agregar, negativo = quitar). Solo administradores.",
    responses={403: {"description": "Admin access required"}, 404: {"description": "Producto no encontrado"}},
)
@inject
async def add_product_stock(
    producto_id: int = Path(..., ge=1),
    body: AddStockRequest = Body(...),
    admin_user: dict = Depends(require_admin),
    service: StockService = Depends(Provide[Container.stock_service]),
):
    result: StockServiceResult = await service.add_product_stock(
        producto_id=producto_id,
        cantidad=body.cantidad,
        username=admin_user["username"],
    )
    if result.error:
        raise HTTPException(status_code=result.status_code, detail=result.error)
    return result.value


@router.put(
    "/stock/productos/{producto_id}/alertas",
    response_model=ProductStockResponse,
    summary="Configurar umbrales de alerta para un producto",
    description="Configura los umbrales de alerta para un producto individual. Solo administradores.",
    responses={403: {"description": "Admin access required"}, 404: {"description": "Producto no encontrado"}},
)
@inject
async def configure_product_alerts(
    producto_id: int = Path(..., ge=1),
    body: ConfigureAlertsRequest = Body(...),
    admin_user: dict = Depends(require_admin),
    service: StockService = Depends(Provide[Container.stock_service]),
):
    result: StockServiceResult = await service.configure_product_alerts(
        producto_id=producto_id,
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

