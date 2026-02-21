from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime
import structlog

from app.domain.models.category import Category
from app.domain.unit_of_work import AbstractUnitOfWork
from app.infrastructure.cache.cache_service import CacheService
from app.presentation.schemas.category_schemas import (
    CategoriaCreateRequest,
    CategoriaUpdateRequest,
)

@dataclass
class ServiceResult:
    value: Optional[Category] = None
    error: Optional[str] = None
    status_code: int = 200

class CategoryService:
    def __init__(
        self, 
        uow: AbstractUnitOfWork,
        cache_service: CacheService,
        audit_service=None,  # Optional for backward compatibility
        logger: structlog.BoundLogger | None = None
    ):
        self.uow = uow
        self.cache_service = cache_service
        self.audit_service = audit_service
        self.logger = logger or structlog.get_logger(__name__)

    async def create(
        self,
        categoria_create: CategoriaCreateRequest,
        user_id: int,
        username: str,
        correlation_id: Optional[str] = None,
    ) -> ServiceResult:
        try:
            self.logger.debug(
                "Creando categoría",
                categoria_nombre=categoria_create.nombre,
                user_id=user_id,
            )
            
            async with self.uow as uow:
                categoria = Category(
                    nombre=categoria_create.nombre,
                    fecha_creacion=datetime.now(),
                    fecha_actualizacion=datetime.now(),
                )

                await uow.category_repo.add(categoria)
                await uow.commit()
                await uow.category_repo.refresh(categoria)

                # Auditar creación
                if self.audit_service:
                    await self.audit_service.log_creation(
                        username=username,
                        entity_type="Category",
                        entity=categoria,
                    )

                self.logger.debug(
                    "Categoría creada exitosamente",
                    categoria_id=categoria.id,
                    categoria_nombre=categoria.nombre
                )
                
                # Clear cache on write
                self.cache_service.clear_all()
                
                return ServiceResult(value=categoria, status_code=201)
        except Exception as e:
            self.logger.error(
                "Error al crear categoría",
                error=str(e),
                categoria_nombre=categoria_create.nombre,
                exc_info=True
            )
            return ServiceResult(error=str(e), status_code=400)

    async def get_all(self, activo: Optional[bool] = None) -> List[Category]:
        """Obtiene todas las categorías con filtro opcional por estado activo."""
        async with self.uow as uow:
            if activo is not None:
                return await uow.category_repo.list_by_active(activo)
            return await uow.category_repo.list()

    async def get_by_id(self, categoria_id: int) -> ServiceResult:
        async with self.uow as uow:
            categoria = await uow.category_repo.get_by_id(categoria_id)
            if not categoria:
                return ServiceResult(error="Categoría no encontrada", status_code=404)
            return ServiceResult(value=categoria)

    async def update(
        self,
        categoria_id: int,
        categoria_update: CategoriaUpdateRequest,
        user_id: int,
        username: str,
        correlation_id: Optional[str] = None,
    ) -> ServiceResult:
        try:
            async with self.uow as uow:
                categoria = await uow.category_repo.get_by_id(categoria_id)
                if not categoria:
                    return ServiceResult(error="Categoría no encontrada", status_code=404)

                # Capturar estado anterior para auditoría
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
                await uow.category_repo.refresh(categoria)

                # Auditar actualización
                if self.audit_service:
                    # Crear objeto temporal para el diff
                    from app.domain.models.category import Category as CategoryModel
                    old_cat = CategoryModel(**old_categoria_dict)
                    
                    await self.audit_service.log_update(
                        username=username,
                        entity_type="Category",
                        old_entity=old_cat,
                        new_entity=categoria,
                    )
                
                # Invalidate category cache on write (selective)
                self.cache_service.invalidate('categoria_*')
                
                return ServiceResult(value=categoria)
        except Exception as e:
            return ServiceResult(error=str(e), status_code=400)

    async def deactivate(
        self,
        categoria_id: int,
        user_id: int,
        username: str,
        correlation_id: Optional[str] = None,
    ) -> ServiceResult:
        try:
            async with self.uow as uow:
                categoria = await uow.category_repo.get_by_id(categoria_id)
                if not categoria:
                    return ServiceResult(error="Categoría no encontrada", status_code=404)

                # Capturar estado anterior
                old_activo = categoria.activo

                # Obtener productos activos de la categoría
                productos = await uow.product_repo.list(categoria_id=categoria_id, active=True)
                producto_ids = [p.id for p in productos]
                
                # Obtener todas las ofertas que contengan estos productos ANTES de desactivar
                ofertas_a_desactivar = []
                if producto_ids:
                    ofertas_a_desactivar = await uow.offer_repo.get_by_products(producto_ids)
                
                # Desactivar productos
                for producto in productos:
                    producto.activo = False
                
                # Desactivar ofertas
                if producto_ids:
                    await uow.offer_repo.deactivate_by_products(producto_ids)
                
                # Desactivar la categoría
                categoria.activo = False
                categoria.fecha_actualizacion = datetime.now()
                await uow.commit()
                await uow.category_repo.refresh(categoria)

                # Auditar cada acción en cascada
                if self.audit_service:
                    # 1. Auditar cada producto desactivado
                    for producto in productos:
                        await self.audit_service.log_deletion(
                            username=username,
                            entity_type="Product",
                            entity=producto,
                        )
                    
                    # 2. Auditar cada oferta desactivada
                    for oferta in ofertas_a_desactivar:
                        await self.audit_service.log_deletion(
                            username=username,
                            entity_type="Offer",
                            entity=oferta,
                        )
                    
                    # 3. Auditar desactivación de la categoría
                    if old_activo != categoria.activo:
                        await self.audit_service.log_deletion(
                            username=username,
                            entity_type="Category",
                            entity=categoria,
                        )
                
                self.logger.info(
                    "Categoría desactivada en cascada",
                    categoria_id=categoria_id,
                    productos_desactivados=len(producto_ids),
                    ofertas_desactivadas=len(ofertas_a_desactivar)
                )
                
                # Clear cache on write
                self.cache_service.clear_all()
                
                return ServiceResult(value=categoria)
        except Exception as e:
            return ServiceResult(error=str(e), status_code=400)
