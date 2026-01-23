from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.models.sale import Sale


class AbstractSaleRepository(ABC):
    @abstractmethod
    async def add(self, sale: Sale) -> Sale:
        ...

    @abstractmethod
    async def get_by_id(self, sale_id: int) -> Optional[Sale]:
        ...

    @abstractmethod
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Sale]:
        ...

    @abstractmethod
    async def refresh(
        self,
        sale: Sale,
        attribute_names: Optional[list] = None,
    ) -> None:
        ...
