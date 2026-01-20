from dataclasses import dataclass
from typing import Optional, List
import structlog

from app.domain.models.category import Category
from app.domain.unit_of_work import AbstractUnitOfWork
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
        logger: structlog.BoundLogger | None = None
    ):
        self.uow = uow
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
                    descripcion=categoria_create.descripcion,
                )

                await uow.category_repo.add(categoria)
                await uow.commit()
                await uow.category_repo.refresh(categoria)

                self.logger.debug(
                    "Categoría creada exitosamente",
                    categoria_id=categoria.id,
                    categoria_nombre=categoria.nombre
                )
                
                return ServiceResult(value=categoria, status_code=201)
        except Exception as e:
            self.logger.error(
                "Error al crear categoría",
                error=str(e),
                categoria_nombre=categoria_create.nombre,
                exc_info=True
            )
            return ServiceResult(error=str(e), status_code=400)

    async def get_all(self) -> List[Category]:
        async with self.uow as uow:
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
                return ServiceResult(value=categoria)
        except Exception as e:
            return ServiceResult(error=str(e), status_code=400)

    async def delete(self, categoria_id: int) -> ServiceResult:
        try:
            async with self.uow as uow:
                categoria = await uow.category_repo.get_by_id(categoria_id)
                if not categoria:
                    return ServiceResult(error="Categoría no encontrada", status_code=404)

                await uow.category_repo.delete(categoria)
                await uow.commit()
                return ServiceResult(value=categoria)
        except Exception as e:
            return ServiceResult(error=str(e), status_code=400)
