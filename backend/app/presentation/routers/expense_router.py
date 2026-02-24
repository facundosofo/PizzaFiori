from fastapi import APIRouter, Depends, HTTPException, status, Path, Body, Query
from dependency_injector.wiring import inject, Provide
from typing import List, Optional
from datetime import date

from app.application.expense_service import ExpenseService, ServiceResult as ExpenseServiceResult
from app.containers import Container
from app.presentation.schemas.expense_schemas import (
    GastoCreateRequest,
    GastoUpdateRequest,
    GastoResponse,
    GastoDetailResponse,
)
from app.presentation.routers.dependencies import get_current_user, require_admin

router = APIRouter(
    tags=["Gastos"],
    dependencies=[Depends(get_current_user)],
)


@router.post(
    "/gastos",
    response_model=GastoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un gasto",
    description="Registra un nuevo gasto operativo.",
    responses={400: {"description": "Datos inválidos"}, 403: {"description": "Admin access required"}},
)
@inject
async def create_gasto(
    gasto: GastoCreateRequest = Body(...),
    admin_user: dict = Depends(require_admin),
    service: ExpenseService = Depends(Provide[Container.expense_service]),
):
    result: ExpenseServiceResult = await service.create(
        gasto,
        username=admin_user["username"],
    )
    if result.error:
        raise HTTPException(status_code=result.status_code, detail=result.error)
    return result.value


@router.get(
    "/gastos",
    response_model=List[GastoResponse],
    summary="Obtener gastos",
    description="Devuelve gastos con filtros opcionales por fecha y categoría.",
)
@inject
async def get_gastos(
    fecha_desde: Optional[date] = Query(None, description="Fecha desde (YYYY-MM-DD)"),
    fecha_hasta: Optional[date] = Query(None, description="Fecha hasta (YYYY-MM-DD)"),
    categoria_gasto_id: Optional[int] = Query(None, description="Filtrar por categoría de gasto"),
    service: ExpenseService = Depends(Provide[Container.expense_service]),
):
    result: ExpenseServiceResult = await service.list_by_filters(
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        categoria_gasto_id=categoria_gasto_id,
    )

    if result.error:
        raise HTTPException(status_code=result.status_code, detail=result.error)
    return result.value


@router.get(
    "/gastos/{gasto_id}",
    response_model=GastoDetailResponse,
    summary="Obtener un gasto por ID",
    description="Devuelve un gasto específico con información de su categoría.",
    responses={404: {"description": "Gasto no encontrado"}},
)
@inject
async def get_gasto(
    gasto_id: int = Path(..., ge=1),
    service: ExpenseService = Depends(Provide[Container.expense_service]),
):
    result: ExpenseServiceResult = await service.get_by_id(gasto_id)
    if result.error:
        raise HTTPException(status_code=result.status_code, detail=result.error)
    return result.value


@router.put(
    "/gastos/{gasto_id}",
    response_model=GastoResponse,
    summary="Actualizar un gasto",
    description="Actualiza los datos de un gasto existente.",
    responses={404: {"description": "Gasto no encontrado"}, 403: {"description": "Admin access required"}},
)
@inject
async def update_gasto(
    gasto_id: int = Path(..., ge=1),
    gasto: GastoUpdateRequest = Body(...),
    admin_user: dict = Depends(require_admin),
    service: ExpenseService = Depends(Provide[Container.expense_service]),
):
    result: ExpenseServiceResult = await service.update(
        gasto_id,
        gasto,
        username=admin_user["username"],
    )
    if result.error:
        raise HTTPException(status_code=result.status_code, detail=result.error)
    return result.value


@router.delete(
    "/gastos/{gasto_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un gasto",
    description="Elimina (soft delete) un gasto.",
    responses={404: {"description": "Gasto no encontrado"}, 403: {"description": "Admin access required"}},
)
@inject
async def delete_gasto(
    gasto_id: int = Path(..., ge=1),
    admin_user: dict = Depends(require_admin),
    service: ExpenseService = Depends(Provide[Container.expense_service]),
):
    result: ExpenseServiceResult = await service.delete(
        gasto_id,
        username=admin_user["username"],
    )
    if result.error:
        raise HTTPException(status_code=result.status_code, detail=result.error)
    return None
