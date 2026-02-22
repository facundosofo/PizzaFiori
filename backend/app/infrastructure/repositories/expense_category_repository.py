from __future__ import annotations

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.expense_category import ExpenseCategory
from app.domain.repositories.expense_category_repository import AbstractExpenseCategoryRepository
from app.infrastructure.repositories.base import BaseRepository


class SqlAlchemyExpenseCategoryRepository(
    BaseRepository[ExpenseCategory], AbstractExpenseCategoryRepository
):
    model = ExpenseCategory

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def get_by_parent_id(self, parent_id: Optional[int]) -> List[ExpenseCategory]:
        """Get all categories with given parent_id (None for root categories)"""
        query = select(self.model).where(self.model.padre_id == parent_id)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_by_id_with_subcategories(
        self,
        category_id: int,
    ) -> Optional[ExpenseCategory]:
        query = (
            select(self.model)
            .where(self.model.id == category_id)
            .options(selectinload(self.model.subcategorias))
        )
        result = await self.session.execute(query)
        return result.scalars().first()

    async def list_by_active(self, activo: Optional[bool] = None) -> List[ExpenseCategory]:
        """List categories with optional filter by active status."""
        query = select(self.model)
        if activo is not None:
            query = query.where(self.model.activo == activo)
        result = await self.session.execute(query)
        return result.scalars().all()
