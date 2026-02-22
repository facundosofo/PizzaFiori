from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime
import structlog

from app.domain.models.expense_category import ExpenseCategory
from app.domain.unit_of_work import AbstractUnitOfWork
from app.infrastructure.cache.cache_service import CacheService
from app.presentation.schemas.expense_category_schemas import (
    GastoCategoriaCreateRequest,
    GastoCategoriaUpdateRequest,
)


@dataclass
class ServiceResult:
    value: Optional[ExpenseCategory] = None
    error: Optional[str] = None
    status_code: int = 200


class ExpenseCategoryService:
    def __init__(
        self,
        uow: AbstractUnitOfWork,
        cache_service: CacheService,
        audit_service=None,
        logger: structlog.BoundLogger | None = None,
    ):
        self.uow = uow
        self.cache_service = cache_service
        self.audit_service = audit_service
        self.logger = logger or structlog.get_logger(__name__)

    async def create(
        self,
        categoria_create: GastoCategoriaCreateRequest,
        username: str,
    ) -> ServiceResult:
        try:
            self.logger.debug(
                "Creando categoría de gasto",
                categoria_nombre=categoria_create.nombre,
            )

            async with self.uow as uow:
                # Validar que categoría padre existe si se proporciona padre_id
                if categoria_create.padre_id is not None:
                    padre = await uow.expense_category_repo.get_by_id(
                        categoria_create.padre_id
                    )
                    if not padre:
                        return ServiceResult(
                            error="Categoría padre no encontrada", status_code=404
                        )

                categoria = ExpenseCategory(
                    nombre=categoria_create.nombre,
                    descripcion=categoria_create.descripcion,
                    padre_id=categoria_create.padre_id,
                    activo=True,
                    fecha_creacion=datetime.now(),
                    fecha_actualizacion=datetime.now(),
                )

                await uow.expense_category_repo.add(categoria)
                await uow.commit()
                await uow.expense_category_repo.refresh(categoria)

                # Auditar creación
                if self.audit_service:
                    await self.audit_service.log_creation(
                        username=username,
                        entity_type="ExpenseCategory",
                        entity=categoria,
                    )

                self.logger.debug(
                    "Categoría de gasto creada exitosamente",
                    categoria_id=categoria.id,
                    categoria_nombre=categoria.nombre,
                )

                # Invalidate cache on write
                self.cache_service.invalidate("gasto_categoria*")

                return ServiceResult(value=categoria, status_code=201)
        except Exception as e:
            self.logger.error(
                "Error al crear categoría de gasto",
                error=str(e),
                categoria_nombre=categoria_create.nombre,
                exc_info=True,
            )
            return ServiceResult(error=str(e), status_code=400)

    async def get_by_id(self, categoria_id: int) -> ServiceResult:
        cache_key = f"gasto_categoria:{categoria_id}"
        
        # Try cache first
        cached = self.cache_service.get(cache_key)
        if cached:
            return ServiceResult(value=cached)

        async with self.uow as uow:
            categoria = await uow.expense_category_repo.get_by_id_with_subcategories(
                categoria_id
            )
            if not categoria:
                return ServiceResult(
                    error="Categoría de gasto no encontrada", status_code=404
                )

            # Store in cache
            self.cache_service.set(cache_key, categoria)
            return ServiceResult(value=categoria)

    async def list_all(self) -> ServiceResult:
        cache_key = "gasto_categorias:all"
        
        # Try cache first
        cached = self.cache_service.get(cache_key)
        if cached:
            return ServiceResult(value=cached)

        async with self.uow as uow:
            categorias = await uow.expense_category_repo.list()
            
            # Store in cache
            self.cache_service.set(cache_key, categorias)
            return ServiceResult(value=categorias)

    async def list_by_parent(self, parent_id: Optional[int] = None) -> ServiceResult:
        cache_key = f"gasto_categorias:parent:{parent_id}"
        
        # Try cache first
        cached = self.cache_service.get(cache_key)
        if cached:
            return ServiceResult(value=cached)

        async with self.uow as uow:
            categorias = await uow.expense_category_repo.get_by_parent_id(parent_id)
            
            # Store in cache
            self.cache_service.set(cache_key, categorias)
            return ServiceResult(value=categorias)

    async def update(
        self,
        categoria_id: int,
        categoria_update: GastoCategoriaUpdateRequest,
        username: str,
    ) -> ServiceResult:
        try:
            async with self.uow as uow:
                categoria = await uow.expense_category_repo.get_by_id(categoria_id)
                if not categoria:
                    return ServiceResult(
                        error="Categoría de gasto no encontrada", status_code=404
                    )

                # Capturar estado anterior para auditoría
                old_categoria_dict = {
                    "id": categoria.id,
                    "nombre": categoria.nombre,
                    "descripcion": categoria.descripcion,
                    "padre_id": categoria.padre_id,
                    "activo": categoria.activo,
                }

                # Validar padre si se actualiza
                if (
                    categoria_update.padre_id is not None
                    and categoria_update.padre_id != categoria.padre_id
                ):
                    padre = await uow.expense_category_repo.get_by_id(
                        categoria_update.padre_id
                    )
                    if not padre:
                        return ServiceResult(
                            error="Categoría padre no encontrada", status_code=404
                        )

                for var, value in vars(categoria_update).items():
                    if value is not None:
                        setattr(categoria, var, value)

                categoria.fecha_actualizacion = datetime.now()
                await uow.commit()
                await uow.expense_category_repo.refresh(categoria)

                # Auditar actualización
                if self.audit_service:
                    old_cat = ExpenseCategory(**old_categoria_dict)
                    await self.audit_service.log_update(
                        username=username,
                        entity_type="ExpenseCategory",
                        old_entity=old_cat,
                        new_entity=categoria,
                    )

                # Invalidate cache on write
                self.cache_service.invalidate("gasto_categoria*")

                return ServiceResult(value=categoria)
        except Exception as e:
            self.logger.error(
                "Error al actualizar categoría de gasto",
                error=str(e),
                categoria_id=categoria_id,
                exc_info=True,
            )
            return ServiceResult(error=str(e), status_code=400)

    async def delete(
        self,
        categoria_id: int,
        username: str,
    ) -> ServiceResult:
        try:
            async with self.uow as uow:
                categoria = await uow.expense_category_repo.get_by_id(categoria_id)
                if not categoria:
                    return ServiceResult(
                        error="Categoría de gasto no encontrada", status_code=404
                    )

                # Soft delete
                categoria.activo = False
                categoria.fecha_actualizacion = datetime.now()
                await uow.commit()

                # Auditar eliminación
                if self.audit_service:
                    await self.audit_service.log_deletion(
                        username=username,
                        entity_type="ExpenseCategory",
                        entity=categoria,
                    )

                # Invalidate cache on write
                self.cache_service.invalidate("gasto_categoria*")

                self.logger.debug(
                    "Categoría de gasto eliminada (soft delete)",
                    categoria_id=categoria_id,
                )

                return ServiceResult(value=categoria, status_code=204)
        except Exception as e:
            self.logger.error(
                "Error al eliminar categoría de gasto",
                error=str(e),
                categoria_id=categoria_id,
                exc_info=True,
            )
            return ServiceResult(error=str(e), status_code=400)
