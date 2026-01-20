from fastapi import APIRouter, Depends, HTTPException, status, Path, Query
from dependency_injector.wiring import inject, Provide
from typing import List, Optional

from app.application.offer_service import OfferService, ServiceResult
from app.containers import Container
from app.presentation.schemas.offer_schemas import (
    OfferCreateRequest,
    OfferUpdateRequest,
    OfferResponse,
)


router = APIRouter(prefix="/ofertas", tags=["Ofertas"])


@router.post(
    "/",
    response_model=OfferResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una oferta",
    description="Crea una nueva oferta con sus productos asociados.",
    responses={
        400: {"description": "Datos inválidos de la oferta"},
        404: {"description": "Uno o más productos no encontrados"},
    },
)
@inject
async def create_offer(
    offer: OfferCreateRequest,
    service: OfferService = Depends(Provide[Container.offer_service]),
):
    result: ServiceResult = await service.create(offer)

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
):
    return await service.get_all(active=active)


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
):
    result: ServiceResult = await service.get_by_id(offer_id)

    if result.error:
        raise HTTPException(
            status_code=result.status_code,
            detail=result.error,
        )

    return result.value


@router.put(
    "/{offer_id}",
    response_model=OfferResponse,
    summary="Actualizar una oferta",
    description="Actualiza los datos de una oferta existente.",
    responses={
        404: {"description": "Oferta o producto no encontrado"},
        400: {"description": "Datos inválidos"},
    },
)
@inject
async def update_offer(
    offer_id: int,
    offer_update: OfferUpdateRequest,
    service: OfferService = Depends(Provide[Container.offer_service]),
):
    result: ServiceResult = await service.update(offer_id, offer_update)

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
    responses={404: {"description": "Oferta no encontrada"}},
)
@inject
async def deactivate_offer(
    offer_id: int = Path(..., ge=1, description="ID único de la oferta"),
    service: OfferService = Depends(Provide[Container.offer_service]),
):
    result = await service.update(offer_id, active=False)
    
    if result.error:
        raise HTTPException(
            status_code=result.status_code,
            detail=result.error,
        )
    
    return result.value
