from fastapi import APIRouter, Depends, HTTPException, status, Path, Query, Request
from dependency_injector.wiring import inject, Provide
from typing import List, Optional

from app.application.offer_service import OfferService, ServiceResult
from app.infrastructure.cache.cache_service import CacheService
from app.containers import Container
from app.presentation.schemas.offer_schemas import (
    OfferCreateRequest,
    OfferUpdateRequest,
    OfferResponse,
)
from app.presentation.routers.dependencies import get_current_user, require_admin


router = APIRouter(
    prefix="/ofertas",
    tags=["Ofertas"],
    dependencies=[Depends(get_current_user)],
)


@router.post(
    "/",
    response_model=OfferResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una oferta",
    description="Crea una nueva oferta con sus productos asociados.",
    responses={
        400: {"description": "Datos inválidos de la oferta"},
        404: {"description": "Uno o más productos no encontrados"},
        403: {"description": "Admin access required"},
    },
)
@inject
async def create_offer(
    request: Request,
    offer: OfferCreateRequest,
    admin_user: dict = Depends(require_admin),
    service: OfferService = Depends(Provide[Container.offer_service]),
):
    result: ServiceResult = await service.create(
        offer,
        username=admin_user["username"],
    )

    if result.error:
        raise HTTPException(
            status_code=result.status_code,
            detail=result.error,
        )

    return result.value


@router.get(
    "/",
    response_model=List[OfferResponse],
    summary="Obtener todas las ofertas",
    description="Devuelve la lista de ofertas con filtros opcionales.",
)
@inject
async def get_offers(
    active: Optional[bool] = Query(
        None, description="Filtrar por estado activo/inactivo"
    ),
    service: OfferService = Depends(Provide[Container.offer_service]),
    cache_service: CacheService = Depends(Provide[Container.cache_service]),
):
    # Generate cache key based on query parameters
    cache_key = f"oferta_list_act_{active}"
    
    # Try to get from cache
    cached = cache_service.get(cache_key)
    if cached is not None:
        return cached.copy()
    
    # If not cached, fetch from database with parameters
    ofertas = await service.get_all(active=active)
    
    # Convert ORM objects to Pydantic schemas and cache
    response_data = [OfferResponse.model_validate(o) for o in ofertas]
    cache_service.set(cache_key, response_data)
    
    return response_data


@router.get(
    "/{offer_id}",
    response_model=OfferResponse,
    summary="Obtener una oferta por ID",
    description="Devuelve una oferta específica por su ID con todos sus productos.",
    responses={404: {"description": "Oferta no encontrada"}},
)
@inject
async def get_offer(
    offer_id: int = Path(..., ge=1, description="ID único de la oferta"),
    service: OfferService = Depends(Provide[Container.offer_service]),
    cache_service: CacheService = Depends(Provide[Container.cache_service]),
):
    # Generate cache key based on offer ID
    cache_key = f"oferta_{offer_id}"
    
    # Try to get from cache
    cached = cache_service.get(cache_key)
    if cached is not None:
        return cached.copy() if isinstance(cached, dict) else cached
    
    # If not cached, fetch from database
    result: ServiceResult = await service.get_by_id(offer_id)
    
    if result.error:
        raise HTTPException(
            status_code=result.status_code,
            detail=result.error,
        )
    
    # Convert ORM object to Pydantic schema and cache
    response_data = OfferResponse.model_validate(result.value)
    cache_service.set(cache_key, response_data)
    
    return response_data


@router.put(
    "/{offer_id}",
    response_model=OfferResponse,
    summary="Actualizar una oferta",
    description="Actualiza los datos de una oferta existente.",
    responses={
        404: {"description": "Oferta o producto no encontrado"},
        400: {"description": "Datos inválidos"},
        403: {"description": "Admin access required"},
    },
)
@inject
async def update_offer(
    request: Request,
    offer_id: int,
    offer_update: OfferUpdateRequest,
    admin_user: dict = Depends(require_admin),
    service: OfferService = Depends(Provide[Container.offer_service]),
):
    result: ServiceResult = await service.update(
        offer_id, 
        offer_update,
        username=admin_user["username"],
    )

    if result.error:
        raise HTTPException(
            status_code=result.status_code,
            detail=result.error,
        )

    return result.value


@router.patch(
    "/{offer_id}/desactivar",
    response_model=OfferResponse,
    summary="Desactivar una oferta",
    description="Cambia el estado activo de una oferta.",
    responses={
        404: {"description": "Oferta no encontrada"},
        403: {"description": "Admin access required"},
    },
)
@inject
async def deactivate_offer(
    request: Request,
    offer_id: int = Path(..., ge=1, description="ID único de la oferta"),
    admin_user: dict = Depends(require_admin),
    service: OfferService = Depends(Provide[Container.offer_service]),
):
    result = await service.update(
        offer_id, 
        active=False,
        username=admin_user["username"],
        is_logical_delete=True,
    )
    
    if result.error:
        raise HTTPException(
            status_code=result.status_code,
            detail=result.error,
        )
    
    return result.value
