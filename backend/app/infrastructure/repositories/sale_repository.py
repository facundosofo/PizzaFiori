from __future__ import annotations

from typing import List, Optional
from datetime import datetime, timedelta

from sqlalchemy import select, func, text, extract
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
                .selectinload(SaleItem.oferta_productos_snapshot)
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
                .selectinload(SaleItem.oferta_productos_snapshot)
            )
        )

        # Filtros index-friendly: transformar el parámetro en vez de la columna.
        # Equivalencia: CAST(fecha_creacion - '6h' AS DATE) >= fecha_desde
        #               <=> fecha_creacion >= DATE(fecha_desde) + '06:00:00'
        if fecha_desde is not None:
            boundary = datetime(fecha_desde.year, fecha_desde.month, fecha_desde.day, 6, 0, 0)
            query = query.where(Sale.fecha_creacion >= boundary)
        if fecha_hasta is not None:
            boundary = datetime(fecha_hasta.year, fecha_hasta.month, fecha_hasta.day, 6, 0, 0) + timedelta(days=1)
            query = query.where(Sale.fecha_creacion < boundary)

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

        if fecha_desde is not None:
            boundary = datetime(fecha_desde.year, fecha_desde.month, fecha_desde.day, 6, 0, 0)
            query = query.where(Sale.fecha_creacion >= boundary)
        if fecha_hasta is not None:
            boundary = datetime(fecha_hasta.year, fecha_hasta.month, fecha_hasta.day, 6, 0, 0) + timedelta(days=1)
            query = query.where(Sale.fecha_creacion < boundary)

        result = await self.session.execute(query)
        return result.scalar() or 0

    async def get_distinct_years(self) -> List[int]:
        """Retorna los años con ventas registradas, usando la fecha de negocio (-6h)."""
        adjusted_fecha = Sale.fecha_creacion - text("INTERVAL '6 hours'")
        year_expr = extract("year", adjusted_fecha)
        query = (
            select(func.distinct(year_expr))
            .order_by(year_expr.asc())
        )
        result = await self.session.execute(query)
        return [int(r) for r in result.scalars().all()]
