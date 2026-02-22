from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import date

from app.domain.models.expense import Expense


class AbstractExpenseRepository(ABC):
    @abstractmethod
    async def add(self, expense: Expense) -> Expense:
        ...

    @abstractmethod
    async def get_by_id(self, expense_id: int) -> Optional[Expense]:
        ...

    @abstractmethod
    async def get_by_id_with_category(self, expense_id: int) -> Optional[Expense]:
        ...

    @abstractmethod
    async def list(self) -> List[Expense]:
        ...

    @abstractmethod
    async def list_by_filters(
        self,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
        categoria_gasto_id: Optional[int] = None,
    ) -> List[Expense]:
        """List expenses with optional filters"""
        ...

    @abstractmethod
    async def delete(self, expense: Expense) -> None:
        ...

    @abstractmethod
    async def refresh(
        self,
        expense: Expense,
        attribute_names: Optional[list] = None,
    ) -> None:
        ...
