from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.models.category import Category


class AbstractCategoryRepository(ABC):
    @abstractmethod
    async def add(self, category: Category) -> Category:
        ...

    @abstractmethod
    async def get_by_id(self, category_id: int) -> Optional[Category]:
        ...

    @abstractmethod
    async def list(self) -> List[Category]:
        ...

    @abstractmethod
    async def delete(self, category: Category) -> None:
        ...

    @abstractmethod
    async def refresh(
        self,
        category: Category,
        attribute_names: Optional[list] = None,
    ) -> None:
        ...
