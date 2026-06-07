from __future__ import annotations

from typing import List, Optional
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.category_stock import CategoryStock
from app.domain.repositories.abstract_category_stock_repository import AbstractCategoryStockRepository


class SqlAlchemyCategoryStockRepository(AbstractCategoryStockRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_categoria_id(self, categoria_id: int) -> Optional[CategoryStock]:
        result = await self.session.execute(
            select(CategoryStock).where(CategoryStock.categoria_id == categoria_id)
        )
        return result.scalars().first()

    async def get_all(self) -> List[CategoryStock]:
        result = await self.session.execute(select(CategoryStock))
        return result.scalars().all()

    async def deduct(self, categoria_id: int, cantidad: int) -> Optional[CategoryStock]:
        stock = await self.get_by_categoria_id(categoria_id)
        if stock is None:
            return None
        stock.cantidad = max(0, stock.cantidad - cantidad)
        stock.fecha_actualizacion = datetime.now()
        await self.session.flush()
        return stock

    async def upsert(self, stock: CategoryStock) -> CategoryStock:
        """Agrega o actualiza un registro de stock (flush sin commit)."""
        self.session.add(stock)
        await self.session.flush()
        return stock
