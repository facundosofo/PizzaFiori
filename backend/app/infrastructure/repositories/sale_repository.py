from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.models.sale import Sale
from app.domain.models.sale_item import SaleItem
from app.domain.repositories.sale_repository import AbstractSaleRepository
from app.infrastructure.repositories.base import BaseRepository


class SqlAlchemySaleRepository(
    BaseRepository[Sale], AbstractSaleRepository
):
    model = Sale

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def get_by_id(self, sale_id: int) -> Optional[Sale]:
        query = (
            select(Sale)
            .where(Sale.id == sale_id)
            .options(
                selectinload(Sale.items)
                .selectinload(SaleItem.producto),
                selectinload(Sale.items)
                .selectinload(SaleItem.oferta)
            )
        )
        result = await self.session.execute(query)
        return result.scalars().first()

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Sale]:
        query = (
            select(Sale)
            .options(
                selectinload(Sale.items)
                .selectinload(SaleItem.producto),
                selectinload(Sale.items)
                .selectinload(SaleItem.oferta)
            )
            .order_by(Sale.fecha_creacion.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return result.scalars().all()
