from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.models.category_stock import CategoryStock


class AbstractCategoryStockRepository(ABC):
    @abstractmethod
    async def get_by_categoria_id(self, categoria_id: int) -> Optional[CategoryStock]:
        ...

    @abstractmethod
    async def get_all(self) -> List[CategoryStock]:
        ...

    @abstractmethod
    async def upsert(self, stock: CategoryStock) -> CategoryStock:
        """Agrega o actualiza un registro de stock (flush sin commit)."""
        ...
