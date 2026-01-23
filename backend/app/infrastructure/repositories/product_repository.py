from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.models.product import Product
from app.domain.models.product_price import ProductPrice
from app.domain.repositories.product_repository import AbstractProductRepository
from app.infrastructure.repositories.base import BaseRepository


class SqlAlchemyProductRepository(
    BaseRepository[Product], AbstractProductRepository
):
    model = Product

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def get_by_id(self, producto_id: int) -> Optional[Product]:
        query = (
            select(Product)
            .where(Product.id == producto_id)
            .options(selectinload(Product.precios))
        )
        result = await self.session.execute(query)
        return result.scalars().first()

    async def list(
        self,
        categoria_id: Optional[int] = None,
        active: Optional[bool] = None,
    ) -> List[Product]:
        query = (
            select(Product)
            .options(selectinload(Product.precios))
            .order_by(Product.id.desc())
        )

        conditions = []
        if active is not None:
            conditions.append(Product.activo == active)
        if categoria_id is not None:
            conditions.append(Product.categoria_id == categoria_id)

        if conditions:
            query = query.where(*conditions)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def replace_prices(
        self,
        producto_id: int,
        new_prices: List[ProductPrice],
    ) -> None:
        await self.session.execute(
            ProductPrice.__table__.delete().where(
                ProductPrice.producto_id == producto_id
            )
        )
        for price in new_prices:
            price.producto_id = producto_id
            self.session.add(price)