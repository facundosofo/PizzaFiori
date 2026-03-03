from __future__ import annotations

from typing import List, Optional
from datetime import date
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.expense import Expense
from app.domain.models.expense_category import ExpenseCategory
from app.domain.repositories.expense_repository import AbstractExpenseRepository
from app.infrastructure.repositories.base import BaseRepository


class SqlAlchemyExpenseRepository(
    BaseRepository[Expense], AbstractExpenseRepository
):
    model = Expense

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def list_by_filters(
        self,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
        categoria_gasto_ids: Optional[List[int]] = None,
    ) -> List[Expense]:
        """List expenses with optional filters"""
        query = select(self.model).where(self.model.activo.is_(True))

        fecha_pago = func.date(self.model.fecha_pago)

        if fecha_desde is not None:
            query = query.where(fecha_pago >= fecha_desde)

        if fecha_hasta is not None:
            query = query.where(fecha_pago <= fecha_hasta)

        if categoria_gasto_ids:
            query = query.where(self.model.categoria_gasto_id.in_(categoria_gasto_ids))

        query = query.order_by(self.model.fecha_pago.desc(), self.model.id.desc())

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_by_id_with_category(self, expense_id: int) -> Optional[Expense]:
        query = (
            select(self.model)
            .where(self.model.id == expense_id)
            .options(selectinload(self.model.categoria_gasto))
        )
        result = await self.session.execute(query)
        return result.scalars().first()

    async def list_by_active(self, activo: Optional[bool] = None) -> List[Expense]:
        """List expenses with optional filter by active status."""
        query = select(self.model)
        if activo is not None:
            query = query.where(self.model.activo == activo)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def list_for_report(
        self,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
    ) -> List[Expense]:
        """Lista gastos con categoría eager-loaded para generación de reportes."""
        query = (
            select(self.model)
            .where(self.model.activo.is_(True))
            .options(
                selectinload(self.model.categoria_gasto)
                .selectinload(ExpenseCategory.padre_categoria)
            )
        )
        fecha_pago = func.date(self.model.fecha_pago)
        if fecha_desde is not None:
            query = query.where(fecha_pago >= fecha_desde)
        if fecha_hasta is not None:
            query = query.where(fecha_pago <= fecha_hasta)
        query = query.order_by(self.model.fecha_pago.asc(), self.model.id.asc())
        result = await self.session.execute(query)
        return result.scalars().all()
