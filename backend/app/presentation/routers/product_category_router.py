from fastapi import APIRouter, Depends, HTTPException, status, Path, Body, Query, Request
from dependency_injector.wiring import inject, Provide
from typing import List, Optional

from app.application.product_category_service import ProductCategoryService, ServiceResult
from app.infrastructure.cache.cache_service import CacheService
from app.containers import Container
from app.presentation.schemas.product_category_schemas import (
    ProductoCategoriaCreateRequest,
    ProductoCategoriaUpdateRequest,
    ProductoCategoriaResponse,
)
from app.presentation.routers.dependencies import get_current_user, require_admin

router = APIRouter(
    prefix="/productos-categorias",
    tags=["Productos Categorias"],
    dependencies=[Depends(get_current_user)],
)


@router.post(
    "/",
    response_model=ProductoCategoriaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una categoría de producto",
    description="Crea una nueva categoría de productos.",
    responses={400: {"description": "Datos inválidos"}, 403: {"description": "Admin access required"}}
)
@inject
async def create_producto_categoria(
    request: Request,
    categoria: ProductoCategoriaCreateRequest = Body(..., description="Datos de la categoría a crear"),
    admin_user: dict = Depends(require_admin),
    service: ProductCategoryService = Depends(Provide[Container.product_category_service])
):
    result: ServiceResult = await service.create(
        categoria,
        username=admin_user["username"],
    )
    if result.error:
        raise HTTPException(status_code=result.status_code, detail=result.error)
    return result.value


@router.get(
    "/",
    response_model=List[ProductoCategoriaResponse],
    summary="Obtener todas las categorías de productos",
    description="Devuelve la lista de todas las categorías con filtro opcional por estado activo.",
)
@inject
async def get_productos_categorias(
    activo: Optional[bool] = Query(None, description="Filtrar por estado activo (true/false). Si no se especifica, devuelve todas."),
    service: ProductCategoryService = Depends(Provide[Container.product_category_service]),
    cache_service: CacheService = Depends(Provide[Container.cache_service])
):
    cache_key = f"producto_categoria_list_act_{activo}"

    cached = cache_service.get(cache_key)
    if cached is not None:
        return cached.copy()

    categorias = await service.get_all(activo=activo)

    response_data = [ProductoCategoriaResponse.model_validate(c) for c in categorias]
    cache_service.set(cache_key, response_data)

    return response_data


@router.get(
    "/{categoria_id}",
    response_model=ProductoCategoriaResponse,
    summary="Obtener una categoría de producto por ID",
    description="Devuelve una categoría específica por su ID.",
    responses={404: {"description": "Categoría no encontrada"}}
)
@inject
async def get_producto_categoria(
    categoria_id: int = Path(..., ge=1, description="ID único de la categoría"),
    service: ProductCategoryService = Depends(Provide[Container.product_category_service]),
    cache_service: CacheService = Depends(Provide[Container.cache_service])
):
    cache_key = f"producto_categoria_{categoria_id}"

    cached = cache_service.get(cache_key)
    if cached is not None:
        return cached.copy() if isinstance(cached, dict) else cached

    result: ServiceResult = await service.get_by_id(categoria_id)
    if result.error:
        raise HTTPException(status_code=result.status_code, detail=result.error)

    response_data = ProductoCategoriaResponse.model_validate(result.value)
    cache_service.set(cache_key, response_data)

    return response_data


@router.put(
    "/{categoria_id}",
    response_model=ProductoCategoriaResponse,
    summary="Actualizar una categoría de producto",
    description="Actualiza los campos de una categoría existente.",
    responses={404: {"description": "Categoría no encontrada"}, 403: {"description": "Admin access required"}}
)
@inject
async def update_producto_categoria(
    request: Request,
    categoria_id: int = Path(..., ge=1, description="ID de la categoría a actualizar"),
    categoria: ProductoCategoriaUpdateRequest = Body(..., description="Campos a actualizar"),
    admin_user: dict = Depends(require_admin),
    service: ProductCategoryService = Depends(Provide[Container.product_category_service])
):
    result: ServiceResult = await service.update(
        categoria_id,
        categoria,
        username=admin_user["username"]
    )
    if result.error:
        raise HTTPException(status_code=result.status_code, detail=result.error)
    return result.value


@router.patch(
    "/{categoria_id}/desactivar",
    response_model=ProductoCategoriaResponse,
    summary="Desactivar una categoría de producto",
    description="Desactiva la categoría y sus productos/ofertas asociados en cascada.",
    responses={
        404: {"description": "Categoría no encontrada"},
        403: {"description": "Admin access required"}
    }
)
@inject
async def deactivate_producto_categoria(
    request: Request,
    categoria_id: int = Path(..., ge=1, description="ID único de la categoría"),
    admin_user: dict = Depends(require_admin),
    service: ProductCategoryService = Depends(Provide[Container.product_category_service])
):
    result: ServiceResult = await service.deactivate(
        categoria_id,
        username=admin_user["username"]
    )
    if result.error:
        raise HTTPException(status_code=result.status_code, detail=result.error)
    return result.value
