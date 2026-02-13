from fastapi import APIRouter, Depends, HTTPException, status, Path, Query
from dependency_injector.wiring import inject, Provide
from typing import List

from app.application.sale_service import SaleService, ServiceResult
from app.containers import Container
from app.presentation.schemas.sale_schemas import (
    SaleCreateRequest,
    SaleUpdateRequest,
    SaleResponse,
    SaleFilterParams,
    SaleListResponse,
)
from app.presentation.routers.dependencies import get_current_user, require_admin

router = APIRouter(
    prefix="/ventas",
    tags=["Ventas"],
    dependencies=[Depends(get_current_user)],
)


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
    response_model=SaleListResponse,
    summary="Obtener todas las ventas",
    description="Devuelve la lista de ventas con paginación, filtros de fecha y total count.",
)
@inject
async def get_sales(
    filters: SaleFilterParams = Depends(),
    service: SaleService = Depends(Provide[Container.sale_service]),
):
    if filters.fecha_desde and filters.fecha_hasta and filters.fecha_desde > filters.fecha_hasta:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="fecha_desde debe ser menor o igual a fecha_hasta",
        )

    sales = await service.get_all(
        skip=filters.skip,
        limit=filters.limit,
        fecha_desde=filters.fecha_desde,
        fecha_hasta=filters.fecha_hasta
    )
    total = await service.count_all(
        fecha_desde=filters.fecha_desde,
        fecha_hasta=filters.fecha_hasta
    )
    return {
        "items": sales,
        "total": total,
        "skip": filters.skip,
        "limit": filters.limit
    }


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
        400: {"description": "Datos inválidos - falta precio_unitario en los items"},
        403: {"description": "Admin access required"},
    },
)
@inject
async def update_sale(
    sale_update: SaleUpdateRequest,
    sale_id: int = Path(..., ge=1, description="ID único de la venta"),
    admin_user: dict = Depends(require_admin),
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
    responses={
        404: {"description": "Venta no encontrada"},
        403: {"description": "Admin access required"},
    },
)
@inject
async def delete_sale(
    sale_id: int = Path(..., ge=1, description="ID único de la venta"),
    admin_user: dict = Depends(require_admin),
    service: SaleService = Depends(Provide[Container.sale_service]),
):
    result: ServiceResult = await service.delete(sale_id)

    if result.error:
        raise HTTPException(
            status_code=result.status_code,
            detail=result.error,
        )

    return None
