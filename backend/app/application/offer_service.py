from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime
import structlog

from app.domain.models.offer import Offer
from app.domain.models.offer_item import OfferItem
from app.domain.unit_of_work import AbstractUnitOfWork
from app.presentation.schemas.offer_schemas import (
    OfferCreateRequest,
    OfferUpdateRequest,
)


@dataclass
class ServiceResult:
    value: Optional[Offer | List[Offer]] = None
    error: Optional[str] = None
    status_code: int = 200


class OfferService:

    def __init__(
        self,
        uow: AbstractUnitOfWork,
        logger: structlog.BoundLogger | None = None,
    ):
        self.uow = uow
        self.logger = logger or structlog.get_logger(__name__)

    async def create(self, offer_create: OfferCreateRequest) -> ServiceResult:
        try:
            self.logger.debug(
                "Creando oferta",
                nombre=offer_create.nombre,
                precio=float(offer_create.precio),
                productos_count=len(offer_create.productos),
            )
            #TODO: Analizar performance si es mejor dejar que falle la BD por FK
            async with self.uow as uow:
                # Validar que productos/categorías/opciones existan
                for item in offer_create.productos:
                    if item.producto_id is not None:
                        producto = await uow.product_repo.get_by_id(item.producto_id)
                        if not producto:
                            return ServiceResult(
                                error=f"Producto {item.producto_id} no encontrado",
                                status_code=404,
                            )
                    elif item.categoria_id is not None:
                        categoria = await uow.category_repo.get_by_id(item.categoria_id)
                        if not categoria:
                            return ServiceResult(
                                error=f"Categoría {item.categoria_id} no encontrada",
                                status_code=404,
                            )
                    elif item.producto_opciones is not None:
                        # Validar que todos los productos en opciones existan
                        for producto_id in item.producto_opciones:
                            producto = await uow.product_repo.get_by_id(producto_id)
                            if not producto:
                                return ServiceResult(
                                    error=f"Producto {producto_id} en opciones no encontrado",
                                    status_code=404,
                                )

                # Crear items de oferta
                offer_items = []
                for item in offer_create.productos:
                    # Determinar qué productos asociar
                    productos_asociados = []
                    
                    if item.producto_id is not None:
                        producto = await uow.product_repo.get_by_id(item.producto_id)
                        productos_asociados.append(producto)
                    elif item.producto_opciones is not None:
                        # Obtener objetos Product para las opciones
                        for producto_id in item.producto_opciones:
                            producto = await uow.product_repo.get_by_id(producto_id)
                            productos_asociados.append(producto)
                    
                    # Crear el item (con productos o solo categoría)
                    offer_items.append(OfferItem(
                        categoria_id=item.categoria_id,
                        cantidad=item.cantidad,
                        productos=productos_asociados,
                    ))

                offer = Offer(
                    nombre=offer_create.nombre,
                    descripcion=offer_create.descripcion,
                    precio=offer_create.precio,
                    activo=True,
                    fecha_creacion=datetime.now(),
                    fecha_actualizacion=datetime.now(),
                    productos=offer_items,
                )

                await uow.offer_repo.add(offer)
                await uow.commit()
                offer = await uow.offer_repo.get_by_id(offer.id)

            self.logger.info(
                "Oferta creada exitosamente",
                offer_id=offer.id,
                nombre=offer.nombre,
            )

            return ServiceResult(value=offer, status_code=201)

        except Exception as e:
            self.logger.error(
                "Error al crear oferta",
                error=str(e),
                exc_info=True,
            )
            return ServiceResult(error=str(e), status_code=400)

    async def get_by_id(self, offer_id: int) -> ServiceResult:
        try:
            async with self.uow as uow:
                offer = await uow.offer_repo.get_by_id(offer_id)

            if not offer:
                return ServiceResult(
                    error=f"Oferta {offer_id} no encontrada",
                    status_code=404,
                )

            return ServiceResult(value=offer)

        except Exception as e:
            self.logger.error(
                "Error al obtener oferta",
                offer_id=offer_id,
                error=str(e),
                exc_info=True,
            )
            return ServiceResult(error=str(e), status_code=500)

    async def get_all(
        self,
        active: Optional[bool] = None,
    ) -> List[Offer]:
        try:
            async with self.uow as uow:
                return await uow.offer_repo.list(active=active)
        except Exception as e:
            self.logger.error(
                "Error al listar ofertas",
                error=str(e),
                exc_info=True,
            )
            return []

    async def update(
        self, offer_id: int, offer_update: Optional[OfferUpdateRequest] = None, active: Optional[bool] = None) -> ServiceResult:
        try:
            async with self.uow as uow:
                offer = await uow.offer_repo.get_by_id(offer_id)

                if not offer:
                    return ServiceResult(
                        error=f"Oferta {offer_id} no encontrada",
                        status_code=404,
                    )

                if offer_update is not None:
                    if offer_update.nombre is not None:
                        offer.nombre = offer_update.nombre
                    if offer_update.descripcion is not None:
                        offer.descripcion = offer_update.descripcion
                    if offer_update.precio is not None:
                        offer.precio = offer_update.precio
                if active is not None:
                    offer.activo = active
                    
                #TODO: Analizar performance si es mejor dejar que falle la BD por FK
                if offer_update is not None and offer_update.productos is not None:
                    # Validar que productos/categorías/opciones existan
                    for item in offer_update.productos:
                        if item.producto_id is not None:
                            producto = await uow.product_repo.get_by_id(item.producto_id)
                            if not producto:
                                return ServiceResult(
                                    error=f"Producto {item.producto_id} no encontrado",
                                    status_code=404,
                                )
                        elif item.categoria_id is not None:
                            categoria = await uow.category_repo.get_by_id(item.categoria_id)
                            if not categoria:
                                return ServiceResult(
                                    error=f"Categoría {item.categoria_id} no encontrada",
                                    status_code=404,
                                )
                        elif item.producto_opciones is not None:
                            # Validar que todos los productos en opciones existan
                            for producto_id in item.producto_opciones:
                                producto = await uow.product_repo.get_by_id(producto_id)
                                if not producto:
                                    return ServiceResult(
                                        error=f"Producto {producto_id} en opciones no encontrado",
                                        status_code=404,
                                    )

                    # Crear nuevos items
                    new_items = []
                    for item in offer_update.productos:
                        # Determinar qué productos asociar
                        productos_asociados = []
                        
                        if item.producto_id is not None:
                            producto = await uow.product_repo.get_by_id(item.producto_id)
                            productos_asociados.append(producto)
                        elif item.producto_opciones is not None:
                            # Obtener objetos Product para las opciones
                            for producto_id in item.producto_opciones:
                                producto = await uow.product_repo.get_by_id(producto_id)
                                productos_asociados.append(producto)
                        
                        # Crear el item (con productos o solo categoría)
                        new_items.append(OfferItem(
                            categoria_id=item.categoria_id,
                            cantidad=item.cantidad,
                            productos=productos_asociados,
                        ))
                    
                    from app.infrastructure.repositories.offer_repository import SqlAlchemyOfferRepository
                    if isinstance(uow.offer_repo, SqlAlchemyOfferRepository):
                        await uow.offer_repo.replace_items(offer_id, new_items)

                offer.fecha_actualizacion = datetime.now()

                await uow.offer_repo.update(offer)
                await uow.commit()
                offer = await uow.offer_repo.get_by_id(offer_id)

            self.logger.info("Oferta actualizada", offer_id=offer_id)

            return ServiceResult(value=offer)

        except Exception as e:
            self.logger.error(
                "Error al actualizar oferta",
                offer_id=offer_id,
                error=str(e),
                exc_info=True,
            )
            return ServiceResult(error=str(e), status_code=400)

        try:
            async with self.uow as uow:
                offer = await uow.offer_repo.get_by_id(offer_id)

                if not offer:
                    return ServiceResult(
                        error=f"Oferta {offer_id} no encontrada",
                        status_code=404,
                    )

                deleted = await uow.offer_repo.delete(offer_id)
                
                if not deleted:
                    return ServiceResult(
                        error=f"No se pudo eliminar la oferta {offer_id}",
                        status_code=500,
                    )

                await uow.commit()

            self.logger.info("Oferta eliminada", offer_id=offer_id)

            return ServiceResult(status_code=204)

        except Exception as e:
            self.logger.error(
                "Error al eliminar oferta",
                offer_id=offer_id,
                error=str(e),
                exc_info=True,
            )
            return ServiceResult(error=str(e), status_code=400)
