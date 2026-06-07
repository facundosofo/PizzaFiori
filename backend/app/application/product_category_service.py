from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime
import structlog

from app.domain.models.product_category import ProductCategory
from app.domain.unit_of_work import AbstractUnitOfWork
from app.infrastructure.cache.cache_service import CacheService
from app.presentation.schemas.product_category_schemas import (
    ProductoCategoriaCreateRequest,
    ProductoCategoriaUpdateRequest,
)

@dataclass
class ServiceResult:
    value: Optional[ProductCategory] = None
    error: Optional[str] = None
    status_code: int = 200

class ProductCategoryService:
    def __init__(
        self,
        uow: AbstractUnitOfWork,
        cache_service: CacheService,
        audit_service=None,
        logger: structlog.BoundLogger | None = None
    ):
        self.uow = uow
        self.cache_service = cache_service
        self.audit_service = audit_service
        self.logger = logger or structlog.get_logger(__name__)

    async def create(
        self,
        categoria_create: ProductoCategoriaCreateRequest,
        username: str,
    ) -> ServiceResult:
        try:
            self.logger.debug(
                "Creando categoría de producto",
                categoria_nombre=categoria_create.nombre
            )

            async with self.uow as uow:
                categoria = ProductCategory(
                    nombre=categoria_create.nombre,
                    fecha_creacion=datetime.now(),
                    fecha_actualizacion=datetime.now(),
                )

                await uow.product_category_repo.add(categoria)
                await uow.commit()
                await uow.product_category_repo.refresh(categoria)

                if self.audit_service:
                    await self.audit_service.log_creation(
                        username=username,
                        entity_type="ProductCategory",
                        entity=categoria,
                    )

                self.logger.debug(
                    "Categoría de producto creada exitosamente",
                    categoria_id=categoria.id,
                    categoria_nombre=categoria.nombre
                )

                self.cache_service.clear_all()

                return ServiceResult(value=categoria, status_code=201)
        except Exception as e:
            self.logger.error(
                "Error al crear categoría de producto",
                error=str(e),
                categoria_nombre=categoria_create.nombre,
                exc_info=True
            )
            return ServiceResult(error=str(e), status_code=400)

    async def get_all(self, activo: Optional[bool] = None) -> List[ProductCategory]:
        """Obtiene todas las categorías de productos con filtro opcional por estado activo."""
        async with self.uow as uow:
            if activo is not None:
                return await uow.product_category_repo.list_by_active(activo)
            return await uow.product_category_repo.list()

    async def get_by_id(self, categoria_id: int) -> ServiceResult:
        async with self.uow as uow:
            categoria = await uow.product_category_repo.get_by_id(categoria_id)
            if not categoria:
                return ServiceResult(error="Categoría no encontrada", status_code=404)
            return ServiceResult(value=categoria)

    async def update(
        self,
        categoria_id: int,
        categoria_update: ProductoCategoriaUpdateRequest,
        username: str,
    ) -> ServiceResult:
        try:
            async with self.uow as uow:
                categoria = await uow.product_category_repo.get_by_id(categoria_id)
                if not categoria:
                    return ServiceResult(error="Categoría no encontrada", status_code=404)

                from copy import deepcopy
                old_categoria_dict = {
                    'id': categoria.id,
                    'nombre': categoria.nombre,
                    'activo': categoria.activo,
                }

                for var, value in vars(categoria_update).items():
                    if value is not None:
                        setattr(categoria, var, value)

                categoria.fecha_actualizacion = datetime.now()
                await uow.commit()
                await uow.product_category_repo.refresh(categoria)

                if self.audit_service:
                    from app.domain.models.product_category import ProductCategory as ProductCategoryModel
                    old_cat = ProductCategoryModel(**old_categoria_dict)

                    await self.audit_service.log_update(
                        username=username,
                        entity_type="ProductCategory",
                        old_entity=old_cat,
                        new_entity=categoria,
                    )

                self.cache_service.invalidate('producto_categoria_*')

                return ServiceResult(value=categoria)
        except Exception as e:
            return ServiceResult(error=str(e), status_code=400)

    async def deactivate(
        self,
        categoria_id: int,
        username: str
    ) -> ServiceResult:
        try:
            async with self.uow as uow:
                categoria = await uow.product_category_repo.get_by_id(categoria_id)
                if not categoria:
                    return ServiceResult(error="Categoría no encontrada", status_code=404)

                old_activo = categoria.activo

                productos = await uow.product_repo.list(categoria_id=categoria_id, active=True)
                producto_ids = [p.id for p in productos]

                ofertas_a_desactivar = []
                if producto_ids:
                    ofertas_a_desactivar = await uow.offer_repo.get_by_products(producto_ids)

                for producto in productos:
                    producto.activo = False

                if producto_ids:
                    await uow.offer_repo.deactivate_by_products(producto_ids)

                categoria.activo = False
                categoria.fecha_actualizacion = datetime.now()
                await uow.commit()
                await uow.product_category_repo.refresh(categoria)

                if self.audit_service:
                    for producto in productos:
                        await self.audit_service.log_deletion(
                            username=username,
                            entity_type="Product",
                            entity=producto,
                        )

                    for oferta in ofertas_a_desactivar:
                        await self.audit_service.log_deletion(
                            username=username,
                            entity_type="Offer",
                            entity=oferta,
                        )

                    if old_activo != categoria.activo:
                        await self.audit_service.log_deletion(
                            username=username,
                            entity_type="ProductCategory",
                            entity=categoria,
                        )

                self.logger.info(
                    "Categoría de producto desactivada en cascada",
                    categoria_id=categoria_id,
                    productos_desactivados=len(producto_ids),
                    ofertas_desactivadas=len(ofertas_a_desactivar)
                )

                self.cache_service.clear_all()

                return ServiceResult(value=categoria)
        except Exception as e:
            return ServiceResult(error=str(e), status_code=400)
