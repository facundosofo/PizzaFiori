from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.models.product_category import ProductCategory


class AbstractProductCategoryRepository(ABC):
    @abstractmethod
    async def add(self, category: ProductCategory) -> ProductCategory:
        ...

    @abstractmethod
    async def get_by_id(self, category_id: int) -> Optional[ProductCategory]:
        ...

    @abstractmethod
    async def list(self) -> List[ProductCategory]:
        ...

    @abstractmethod
    async def delete(self, category: ProductCategory) -> None:
        ...

    @abstractmethod
    async def refresh(
        self,
        category: ProductCategory,
        attribute_names: Optional[list] = None,
    ) -> None:
        ...
