from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.models.expense_category import ExpenseCategory


class AbstractExpenseCategoryRepository(ABC):
    @abstractmethod
    async def add(self, category: ExpenseCategory) -> ExpenseCategory:
        ...

    @abstractmethod
    async def get_by_id(self, category_id: int) -> Optional[ExpenseCategory]:
        ...

    @abstractmethod
    async def get_by_id_with_subcategories(
        self,
        category_id: int,
    ) -> Optional[ExpenseCategory]:
        ...

    @abstractmethod
    async def get_by_parent_id(self, parent_id: Optional[int]) -> List[ExpenseCategory]:
        """Get all categories with given parent_id (None for root categories)"""
        ...

    @abstractmethod
    async def list(self) -> List[ExpenseCategory]:
        ...

    @abstractmethod
    async def delete(self, category: ExpenseCategory) -> None:
        ...

    @abstractmethod
    async def refresh(
        self,
        category: ExpenseCategory,
        attribute_names: Optional[list] = None,
    ) -> None:
        ...
