from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import Any

from app.infrastructure.unit_of_work import get_uow
from app.presentation.routers.dependencies import get_current_user, require_admin
from app.presentation.schemas.config_schemas import (
    RecargoConfigResponse,
    RecargoConfigUpdateRequest,
)
from app.application.public_catalog_service import (
    CATALOG_PUBLISHED_AT_KEY,
    DEFAULT_RECARGO_PERCENTAGE,
    PublicCatalogService,
    RECARGO_KEY,
    decode_publish_timestamp,
)
from app.infrastructure.r2_catalog_storage import (
    CatalogStorageConfigurationError,
    CatalogStorageError,
)
from app.infrastructure.logging import get_logger
from app.presentation.schemas.public_catalog_schemas import (
    PublicCatalogPublishResponse,
    PublicCatalogPublishStatus,
)

router = APIRouter(
    prefix="/config",
    tags=["Configuración"],
    dependencies=[Depends(get_current_user)],
)

catalog_logger = get_logger("catalog.publish")


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


@router.get(
    "/catalog/status",
    response_model=PublicCatalogPublishStatus,
    summary="Consultar el estado de publicación del catálogo",
)
async def get_catalog_publish_status(
    _admin: dict = Depends(require_admin),
    uow=Depends(get_uow),
):
    config = await uow.app_config_repo.get_by_key(CATALOG_PUBLISHED_AT_KEY)
    return PublicCatalogPublishStatus(
        publicado_en=decode_publish_timestamp(config.value if config else None)
    )


@router.post(
    "/catalog/publish",
    response_model=PublicCatalogPublishResponse,
    summary="Publicar el catálogo público en Cloudflare R2",
    responses={
        409: {"description": "Falta una imagen local o no se puede publicar"},
        502: {"description": "Error al publicar los objetos en R2"},
        503: {"description": "R2 no está configurado"},
    },
)
async def publish_public_catalog(
    _admin: dict = Depends(require_admin),
    uow=Depends(get_uow),
):
    try:
        return await PublicCatalogService().publish(uow)
    except CatalogStorageConfigurationError as exc:
        catalog_logger.error("Configuración de publicación del catálogo incompleta", error=str(exc))
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        catalog_logger.error("No se pudo encontrar una imagen del catálogo", error=str(exc))
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except CatalogStorageError as exc:
        catalog_logger.error("No se pudo publicar el catálogo", error=str(exc))
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
