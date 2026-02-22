from fastapi import APIRouter, Depends, HTTPException, status, Path, Body, Query
from dependency_injector.wiring import inject, Provide
from typing import List, Optional

from app.application.expense_category_service import ExpenseCategoryService, ServiceResult as ExpenseCategoryServiceResult
from app.containers import Container
from app.presentation.schemas.expense_category_schemas import (
    GastoCategoriaCreateRequest,
    GastoCategoriaUpdateRequest,
    GastoCategoriaResponse,
    GastoCategoriaDetailResponse,
)
from app.presentation.routers.dependencies import get_current_user, require_admin

router = APIRouter(
    prefix="/api",
    tags=["Gastos Categorias"],
    dependencies=[Depends(get_current_user)],
)


@router.post(
    "/gastos-categorias",
    response_model=GastoCategoriaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una categoria de gasto",
    description="Crea una nueva categoria de gasto jerarquica.",
    responses={400: {"description": "Datos invalidos"}, 403: {"description": "Admin access required"}},
)
@inject
async def create_gasto_categoria(
    categoria: GastoCategoriaCreateRequest = Body(...),
    admin_user: dict = Depends(require_admin),
    service: ExpenseCategoryService = Depends(Provide[Container.expense_category_service]),
):
    result: ExpenseCategoryServiceResult = await service.create(
        categoria,
        username=admin_user["username"],
    )
    if result.error:
        raise HTTPException(status_code=result.status_code, detail=result.error)
    return result.value


@router.get(
    "/gastos-categorias",
    response_model=List[GastoCategoriaResponse],
    summary="Obtener todas las categorias de gastos",
    description="Devuelve todas las categorias de gastos, opcionalmente filtradas por categoria padre.",
)
@inject
async def get_gastos_categorias(
    padre_id: Optional[int] = Query(None, description="Filtrar por ID de categoria padre"),
    service: ExpenseCategoryService = Depends(Provide[Container.expense_category_service]),
):
    if padre_id is not None:
        result: ExpenseCategoryServiceResult = await service.list_by_parent(padre_id)
    else:
        result: ExpenseCategoryServiceResult = await service.list_all()

    if result.error:
        raise HTTPException(status_code=result.status_code, detail=result.error)
    return result.value


@router.get(
    "/gastos-categorias/{categoria_id}",
    response_model=GastoCategoriaDetailResponse,
    summary="Obtener una categoria de gasto por ID",
    description="Devuelve una categoria de gasto especifica con sus subcategorias.",
    responses={404: {"description": "Categoria no encontrada"}},
)
@inject
async def get_gasto_categoria(
    categoria_id: int = Path(..., ge=1),
    service: ExpenseCategoryService = Depends(Provide[Container.expense_category_service]),
):
    result: ExpenseCategoryServiceResult = await service.get_by_id(categoria_id)
    if result.error:
        raise HTTPException(status_code=result.status_code, detail=result.error)
    return result.value


@router.put(
    "/gastos-categorias/{categoria_id}",
    response_model=GastoCategoriaResponse,
    summary="Actualizar una categoria de gasto",
    description="Actualiza los datos de una categoria de gasto.",
    responses={404: {"description": "Categoria no encontrada"}, 403: {"description": "Admin access required"}},
)
@inject
async def update_gasto_categoria(
    categoria_id: int = Path(..., ge=1),
    categoria: GastoCategoriaUpdateRequest = Body(...),
    admin_user: dict = Depends(require_admin),
    service: ExpenseCategoryService = Depends(Provide[Container.expense_category_service]),
):
    result: ExpenseCategoryServiceResult = await service.update(
        categoria_id,
        categoria,
        username=admin_user["username"],
    )
    if result.error:
        raise HTTPException(status_code=result.status_code, detail=result.error)
    return result.value


@router.patch(
    "/gastos-categorias/{categoria_id}/desactivar",
    response_model=GastoCategoriaResponse,
    summary="Desactivar una categoria de gasto",
    description="Desactiva (soft delete) una categoria de gasto.",
    responses={404: {"description": "Categoria no encontrada"}, 403: {"description": "Admin access required"}},
)
@inject
async def deactivate_gasto_categoria(
    categoria_id: int = Path(..., ge=1),
    admin_user: dict = Depends(require_admin),
    service: ExpenseCategoryService = Depends(Provide[Container.expense_category_service]),
):
    result: ExpenseCategoryServiceResult = await service.delete(
        categoria_id,
        username=admin_user["username"],
    )
    if result.error:
        raise HTTPException(status_code=result.status_code, detail=result.error)
    return result.value
