from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional
from datetime import date

from app.domain.models.order_daily_sequence import OrderDailySequence


class AbstractSequenceRepository(ABC):
    @abstractmethod
    async def get_for_update(self, business_date: date) -> Optional[OrderDailySequence]:
        ...

    @abstractmethod
    async def create(self, business_date: date, last_value: int) -> OrderDailySequence:
        ...

    @abstractmethod
    async def update(self, sequence: OrderDailySequence) -> OrderDailySequence:
        ...
