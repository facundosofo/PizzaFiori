from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional
from decimal import Decimal

from app.domain.models.product_stock import ProductStock


class AbstractProductStockRepository(ABC):
    @abstractmethod
    async def get_by_producto_id(self, producto_id: int) -> Optional[ProductStock]:
        ...

    @abstractmethod
    async def get_by_categoria_id(self, categoria_id: int) -> List[ProductStock]:
        """Returns all product stocks for products belonging to the given category."""
        ...

    @abstractmethod
    async def upsert(self, stock: ProductStock) -> ProductStock:
        ...

    @abstractmethod
    async def get_or_create(self, producto_id: int) -> ProductStock:
        """Returns existing stock or creates a new one with cantidad=0."""
        ...

    @abstractmethod
    async def deduct(self, producto_id: int, cantidad: Decimal) -> Optional[ProductStock]:
        """Subtracts cantidad from product stock (min 0). Returns updated stock or None if not found."""
        ...
