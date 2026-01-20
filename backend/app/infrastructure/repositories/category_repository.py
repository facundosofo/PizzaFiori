from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.category import Category
from app.domain.repositories.category_repository import AbstractCategoryRepository
from app.infrastructure.repositories.base import BaseRepository


class SqlAlchemyCategoryRepository(
    BaseRepository[Category], AbstractCategoryRepository
):
    model = Category

    def __init__(self, session: AsyncSession):
        super().__init__(session)
