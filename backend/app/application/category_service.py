from dataclasses import dataclass
from typing import Optional, List
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
        logger: structlog.BoundLogger | None = None
    ):
        self.uow = uow
        self.cache_service = cache_service
        self.logger = logger or structlog.get_logger(__name__)

    async def create(self, categoria_create: CategoriaCreateRequest) -> ServiceResult:
        try:
            self.logger.debug(
                "Creando categoría",
                categoria_nombre=categoria_create.nombre
            )
            
            async with self.uow as uow:
                categoria = Category(
                    nombre=categoria_create.nombre,
                )

                await uow.category_repo.add(categoria)
                await uow.commit()
                await uow.category_repo.refresh(categoria)

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
    ) -> ServiceResult:
        try:
            async with self.uow as uow:
                categoria = await uow.category_repo.get_by_id(categoria_id)
                if not categoria:
                    return ServiceResult(error="Categoría no encontrada", status_code=404)

                for var, value in vars(categoria_update).items():
                    if value is not None:
                        setattr(categoria, var, value)

                await uow.commit()
                await uow.category_repo.refresh(categoria)
                
                # Invalidate category cache on write (selective)
                self.cache_service.invalidate('categoria_*')
                
                return ServiceResult(value=categoria)
        except Exception as e:
            return ServiceResult(error=str(e), status_code=400)

    async def deactivate(self, categoria_id: int) -> ServiceResult:
        try:
            async with self.uow as uow:
                categoria = await uow.category_repo.get_by_id(categoria_id)
                if not categoria:
                    return ServiceResult(error="Categoría no encontrada", status_code=404)

                # Obtener productos activos de la categoría
                productos = await uow.product_repo.list(categoria_id=categoria_id, active=True)
                producto_ids = [p.id for p in productos]
                
                # Desactivar ofertas que contengan estos productos
                if producto_ids:
                    await uow.offer_repo.deactivate_by_products(producto_ids)
                    
                    # Desactivar productos
                    for producto in productos:
                        producto.activo = False
                
                # Desactivar la categoría
                categoria.activo = False
                await uow.commit()
                await uow.category_repo.refresh(categoria)
                
                self.logger.info(
                    "Categoría desactivada en cascada",
                    categoria_id=categoria_id,
                    productos_desactivados=len(producto_ids)
                )
                
                # Clear cache on write
                self.cache_service.clear_all()
                
                return ServiceResult(value=categoria)
        except Exception as e:
            return ServiceResult(error=str(e), status_code=400)
