from __future__ import annotations

from typing import List, Optional
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.domain.models.product_stock import ProductStock
from app.domain.models.product import Product
from app.domain.repositories.abstract_product_stock_repository import AbstractProductStockRepository


class SqlAlchemyProductStockRepository(AbstractProductStockRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_producto_id(self, producto_id: int) -> Optional[ProductStock]:
        result = await self.session.execute(
            select(ProductStock).where(ProductStock.producto_id == producto_id)
        )
        return result.scalars().first()

    async def get_by_categoria_id(self, categoria_id: int) -> List[ProductStock]:
        result = await self.session.execute(
            select(ProductStock)
            .join(Product, Product.id == ProductStock.producto_id)
            .where(Product.categoria_id == categoria_id, Product.activo == True)
            .options(joinedload(ProductStock.producto))
        )
        return list(result.scalars().all())

    async def upsert(self, stock: ProductStock) -> ProductStock:
        self.session.add(stock)
        await self.session.flush()
        return stock

    async def get_or_create(self, producto_id: int) -> ProductStock:
        stock = await self.get_by_producto_id(producto_id)
        if stock is None:
            stock = ProductStock(
                producto_id=producto_id,
                cantidad=0,
                fecha_actualizacion=datetime.now(),
            )
            self.session.add(stock)
            await self.session.flush()
        return stock

    async def deduct(self, producto_id: int, cantidad: int) -> Optional[ProductStock]:
        stock = await self.get_by_producto_id(producto_id)
        if stock is None:
            return None
        stock.cantidad = max(0, stock.cantidad - cantidad)
        stock.fecha_actualizacion = datetime.now()
        await self.session.flush()
        return stock
