from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

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
        fecha_desde: Optional[datetime] = None,
        fecha_hasta: Optional[datetime] = None,
    ) -> List[Sale]:
        ...

    @abstractmethod
    async def count(
        self,
        fecha_desde: Optional[datetime] = None,
        fecha_hasta: Optional[datetime] = None,
    ) -> int:
        ...

    @abstractmethod
    async def refresh(
        self,
        sale: Sale,
        attribute_names: Optional[list] = None,
    ) -> None:
        ...

    @abstractmethod
    async def get_distinct_years(self) -> List[int]:
        ...
