from dataclasses import dataclass
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.domain.category import Category
from app.presentation.schemas.category_schemas import CategoriaCreateRequest, CategoriaUpdateRequest

@dataclass
class ServiceResult:
    value: Optional[Category] = None
    error: Optional[str] = None
    status_code: int = 200

class CategoryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, categoria_create: CategoriaCreateRequest) -> ServiceResult:
        try:
            categoria = Category(
                nombre=categoria_create.nombre,
                descripcion=categoria_create.descripcion
            )
            self.db.add(categoria)
            await self.db.commit()
            await self.db.refresh(categoria)
            return ServiceResult(value=categoria, status_code=201)
        except Exception as e:
            await self.db.rollback()
            return ServiceResult(error=str(e), status_code=400)

    async def get_all(self) -> List[Category]:
        result = await self.db.execute(select(Category))
        return result.scalars().all()

    async def get_by_id(self, categoria_id: int) -> ServiceResult:
        result = await self.db.execute(
            select(Category).where(Category.id == categoria_id)
        )
        categoria = result.scalars().first()
        if not categoria:
            return ServiceResult(error="Categoría no encontrada", status_code=404)
        return ServiceResult(value=categoria)

    async def update(self, categoria_id: int, categoria_update: CategoriaUpdateRequest) -> ServiceResult:
        result = await self.db.execute(
            select(Category).where(Category.id == categoria_id)
        )
        categoria = result.scalars().first()
        if not categoria:
            return ServiceResult(error="Categoría no encontrada", status_code=404)

        for var, value in vars(categoria_update).items():
            if value is not None:
                setattr(categoria, var, value)

        await self.db.commit()
        await self.db.refresh(categoria)
        return ServiceResult(value=categoria)

    async def delete(self, categoria_id: int) -> ServiceResult:
        result = await self.db.execute(
            select(Category).where(Category.id == categoria_id)
        )
        categoria = result.scalars().first()
        if not categoria:
            return ServiceResult(error="Categoría no encontrada", status_code=404)

        await self.db.delete(categoria)
        await self.db.commit()
        return ServiceResult(value=categoria)
