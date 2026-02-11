from __future__ import annotations

from datetime import date
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.order_daily_sequence import OrderDailySequence
from app.domain.repositories.sequence_repository import AbstractSequenceRepository


class SqlAlchemySequenceRepository(AbstractSequenceRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_for_update(self, business_date: date) -> Optional[OrderDailySequence]:
        query = select(OrderDailySequence).where(OrderDailySequence.business_date == business_date).with_for_update()
        result = await self.session.execute(query)
        return result.scalars().first()

    async def create(self, business_date: date, last_value: int) -> OrderDailySequence:
        seq = OrderDailySequence(business_date=business_date, last_value=last_value)
        self.session.add(seq)
        await self.session.flush()
        return seq

    async def update(self, sequence: OrderDailySequence) -> OrderDailySequence:
        await self.session.flush()
        return sequence
