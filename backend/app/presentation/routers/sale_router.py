from fastapi import APIRouter, Depends, HTTPException, status, Path, Query
from dependency_injector.wiring import inject, Provide
from typing import List

from app.application.sale_service import SaleService, ServiceResult
from app.containers import Container
from app.presentation.schemas.sale_schemas import (
    SaleCreateRequest,
    SaleUpdateRequest,
    SaleResponse,
)

router = APIRouter(prefix="/ventas", tags=["Ventas"])


@router.post(
    "/",
    response_model=SaleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una venta",
    description="Crea una nueva venta con productos y/o ofertas.",
)
@inject
async def create_sale(
    sale: SaleCreateRequest,
    service: SaleService = Depends(Provide[Container.sale_service]),
):
    result: ServiceResult = await service.create(sale)

    if result.error:
        raise HTTPException(
            status_code=result.status_code,
            detail=result.error,
        )

    return result.value


@router.get(
    "/",
    response_model=List[SaleResponse],
    summary="Obtener todas las ventas",
    description="Devuelve la lista de ventas con paginación.",
)
@inject
async def get_sales(
    skip: int = Query(0, ge=0, description="Número de registros a omitir"),
    limit: int = Query(100, ge=1, le=1000, description="Límite de registros"),
    service: SaleService = Depends(Provide[Container.sale_service]),
):
    return await service.get_all(skip=skip, limit=limit)


@router.get(
    "/{sale_id}",
    response_model=SaleResponse,
    summary="Obtener una venta por ID",
    description="Devuelve una venta específica por su ID con nombres de productos/ofertas.",
    responses={404: {"description": "Venta no encontrada"}},
)
@inject
async def get_sale(
    sale_id: int = Path(..., ge=1, description="ID único de la venta"),
    service: SaleService = Depends(Provide[Container.sale_service]),
):
    result: ServiceResult = await service.get_by_id(sale_id)

    if result.error:
        raise HTTPException(
            status_code=result.status_code,
            detail=result.error,
        )

    return result.value


@router.put(
    "/{sale_id}",
    response_model=SaleResponse,
    summary="Actualizar una venta",
    description="Actualiza una venta existente. Requiere precio_unitario para cada item.",
    responses={
        404: {"description": "Venta no encontrada"},
        400: {"description": "Datos inválidos - falta precio_unitario en los items"}
    },
)
@inject
async def update_sale(
    sale_update: SaleUpdateRequest,
    sale_id: int = Path(..., ge=1, description="ID único de la venta"),
    service: SaleService = Depends(Provide[Container.sale_service]),
):
    result: ServiceResult = await service.update(sale_id, sale_update)

    if result.error:
        raise HTTPException(
            status_code=result.status_code,
            detail=result.error,
        )

    return result.value


@router.delete(
    "/{sale_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar una venta",
    description="Elimina una venta existente.",
    responses={404: {"description": "Venta no encontrada"}},
)
@inject
async def delete_sale(
    sale_id: int = Path(..., ge=1, description="ID único de la venta"),
    service: SaleService = Depends(Provide[Container.sale_service]),
):
    result: ServiceResult = await service.delete(sale_id)

    if result.error:
        raise HTTPException(
            status_code=result.status_code,
            detail=result.error,
        )

    return None
