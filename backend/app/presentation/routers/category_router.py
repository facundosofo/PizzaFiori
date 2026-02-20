from fastapi import APIRouter, Depends, HTTPException, status, Path, Body, Query
from dependency_injector.wiring import inject, Provide
from typing import List, Optional

from app.application.category_service import CategoryService, ServiceResult
from app.infrastructure.cache.cache_service import CacheService
from app.containers import Container
from app.presentation.schemas.category_schemas import CategoriaCreateRequest, CategoriaUpdateRequest, CategoriaResponse
from app.presentation.routers.dependencies import get_current_user, require_admin

router = APIRouter(
    prefix="/categorias",
    tags=["Categorías"],
    dependencies=[Depends(get_current_user)],
)


@router.post(
    "/",
    response_model=CategoriaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una categoría",
    description="Crea una nueva categoría de productos.",
    responses={400: {"description": "Datos inválidos de la categoría"}, 403: {"description": "Admin access required"}}
)
@inject
async def create_categoria(
    categoria: CategoriaCreateRequest = Body(..., description="Datos de la categoría a crear"),
    admin_user: dict = Depends(require_admin),
    service: CategoryService = Depends(Provide[Container.category_service])
):
    result: ServiceResult = await service.create(categoria)
    if result.error:
        raise HTTPException(status_code=result.status_code, detail=result.error)
    return result.value


@router.get(
    "/",
    response_model=List[CategoriaResponse],
    summary="Obtener todas las categorías",
    description="Devuelve la lista de todas las categorías con filtro opcional por estado activo.",
)
@inject
async def get_categorias(
    activo: Optional[bool] = Query(None, description="Filtrar por estado activo (true/false). Si no se especifica, devuelve todas."),
    service: CategoryService = Depends(Provide[Container.category_service]),
    cache_service: CacheService = Depends(Provide[Container.cache_service])
):
    # Generate cache key based on query parameters
    cache_key = f"categoria_list_act_{activo}"
    
    # Try to get from cache
    cached = cache_service.get(cache_key)
    if cached is not None:
        return cached.copy()
    
    # If not cached, fetch from database with parameters
    categorias = await service.get_all(activo=activo)
    
    # Convert ORM objects to Pydantic schemas and cache
    response_data = [CategoriaResponse.model_validate(c) for c in categorias]
    cache_service.set(cache_key, response_data)
    
    return response_data


@router.get(
    "/{categoria_id}",
    response_model=CategoriaResponse,
    summary="Obtener una categoría por ID",
    description="Devuelve una categoría específica por su ID.",
    responses={404: {"description": "Categoría no encontrada"}}
)
@inject
async def get_categoria(
    categoria_id: int = Path(..., ge=1, description="ID único de la categoría"),
    service: CategoryService = Depends(Provide[Container.category_service]),
    cache_service: CacheService = Depends(Provide[Container.cache_service])
):
    # Generate cache key based on category ID
    cache_key = f"categoria_{categoria_id}"
    
    # Try to get from cache
    cached = cache_service.get(cache_key)
    if cached is not None:
        return cached.copy() if isinstance(cached, dict) else cached
    
    # If not cached, fetch from database
    result: ServiceResult = await service.get_by_id(categoria_id)
    if result.error:
        raise HTTPException(status_code=result.status_code, detail=result.error)
    
    # Convert ORM object to Pydantic schema and cache
    response_data = CategoriaResponse.model_validate(result.value)
    cache_service.set(cache_key, response_data)
    
    return response_data


@router.put(
    "/{categoria_id}",
    response_model=CategoriaResponse,
    summary="Actualizar una categoría",
    description="Actualiza los campos de una categoría existente.",
    responses={404: {"description": "Categoría no encontrada"}, 403: {"description": "Admin access required"}}
)
@inject
async def update_categoria(
    categoria_id: int = Path(..., ge=1, description="ID de la categoría a actualizar"),
    categoria: CategoriaUpdateRequest = Body(..., description="Campos a actualizar"),
    admin_user: dict = Depends(require_admin),
    service: CategoryService = Depends(Provide[Container.category_service])
):
    result: ServiceResult = await service.update(categoria_id, categoria)
    if result.error:
        raise HTTPException(status_code=result.status_code, detail=result.error)
    return result.value


@router.patch(
    "/{categoria_id}/desactivar",
    response_model=CategoriaResponse,
    summary="Desactivar una categoría",
    description="Cambia el estado activo de una categoría.",
    responses={
        404: {"description": "Categoría no encontrada"},
        403: {"description": "Admin access required"}
    }
)
@inject
async def deactivate_categoria(
    categoria_id: int = Path(..., ge=1, description="ID único de la categoría"),
    admin_user: dict = Depends(require_admin),
    service: CategoryService = Depends(Provide[Container.category_service])
):
    result: ServiceResult = await service.deactivate(categoria_id)
    if result.error:
        raise HTTPException(status_code=result.status_code, detail=result.error)
    return result.value
