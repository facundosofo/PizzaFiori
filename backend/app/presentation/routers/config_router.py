from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import Any

from app.infrastructure.unit_of_work import get_uow
from app.presentation.routers.dependencies import get_current_user, require_admin
from app.presentation.schemas.config_schemas import (
    RecargoConfigResponse,
    RecargoConfigUpdateRequest,
)

router = APIRouter(
    prefix="/config",
    tags=["Configuración"],
    dependencies=[Depends(get_current_user)],
)

DEFAULT_RECARGO_PERCENTAGE = 10
RECARGO_KEY = "recargo_transferencia"


@router.get(
    "/recargo",
    response_model=RecargoConfigResponse,
    summary="Obtener porcentaje de recargo para transferencia/débito",
    description="Obtiene el porcentaje de recargo configurado para pagos por transferencia o débito.",
)
async def get_recargo_config(
    request: Request,
    uow=Depends(get_uow),
):
    async with uow as unit:
        config = await unit.app_config_repo.get_by_key(RECARGO_KEY)
        if config is None:
            return RecargoConfigResponse(porcentaje_recargo=DEFAULT_RECARGO_PERCENTAGE)

        try:
            porcentaje = float(config.value)
        except (ValueError, TypeError):
            porcentaje = DEFAULT_RECARGO_PERCENTAGE

        return RecargoConfigResponse(porcentaje_recargo=porcentaje)


@router.put(
    "/recargo",
    response_model=RecargoConfigResponse,
    summary="Actualizar porcentaje de recargo para transferencia/débito",
    description="Actualiza el porcentaje de recargo que se aplica a los pagos por transferencia o débito.",
    responses={
        403: {"description": "Admin access required"},
    },
)
async def update_recargo_config(
    request: Request,
    body: RecargoConfigUpdateRequest,
    _admin: dict = Depends(require_admin),
    uow=Depends(get_uow),
):
    async with uow as unit:
        config = await unit.app_config_repo.set_value(RECARGO_KEY, str(body.porcentaje_recargo))
        await unit.commit()
        return RecargoConfigResponse(porcentaje_recargo=float(config.value))
