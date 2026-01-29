from __future__ import annotations

from typing import List, Optional
from datetime import datetime

from sqlalchemy import select, func
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
        fecha_desde: Optional[datetime] = None,
        fecha_hasta: Optional[datetime] = None,
    ) -> List[Sale]:
        query = (
            select(Sale)
            .options(
                selectinload(Sale.items)
                .selectinload(SaleItem.producto),
                selectinload(Sale.items)
                .selectinload(SaleItem.oferta)
            )
        )
        
        # Aplicar filtros de fecha
        if fecha_desde is not None:
            query = query.where(Sale.fecha_creacion >= fecha_desde)
        if fecha_hasta is not None:
            query = query.where(Sale.fecha_creacion <= fecha_hasta)
        
        query = (
            query
            .order_by(Sale.fecha_creacion.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def count(
        self,
        fecha_desde: Optional[datetime] = None,
        fecha_hasta: Optional[datetime] = None,
    ) -> int:
        """Cuenta el total de ventas con filtros opcionales de fecha."""
        query = select(func.count()).select_from(Sale)
        
        # Aplicar filtros de fecha
        if fecha_desde is not None:
            query = query.where(Sale.fecha_creacion >= fecha_desde)
        if fecha_hasta is not None:
            query = query.where(Sale.fecha_creacion <= fecha_hasta)
        
        result = await self.session.execute(query)
        return result.scalar() or 0
