from __future__ import annotations

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.product_category import ProductCategory
from app.domain.repositories.product_category_repository import AbstractProductCategoryRepository
from app.infrastructure.repositories.base import BaseRepository


class SqlAlchemyProductCategoryRepository(
    BaseRepository[ProductCategory], AbstractProductCategoryRepository
):
    model = ProductCategory

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def list_by_active(self, activo: Optional[bool] = None) -> List[ProductCategory]:
        """Lista categorías de productos con filtro opcional por estado activo."""
        query = select(self.model)
        if activo is not None:
            query = query.where(self.model.activo == activo)
        result = await self.session.execute(query)
        return result.scalars().all()
