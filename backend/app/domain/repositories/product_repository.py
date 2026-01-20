from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.models.product import Product
from app.domain.models.product_price import ProductPrice


class AbstractProductRepository(ABC):
    @abstractmethod
    async def add(self, product: Product) -> Product:
        ...

    @abstractmethod
    async def get_by_id(self, producto_id: int) -> Optional[Product]:
        ...

    @abstractmethod
    async def list(
        self,
        categoria_id: Optional[int] = None,
        active: Optional[bool] = None,
    ) -> List[Product]:
        ...

    @abstractmethod
    async def replace_prices(
        self,
        producto_id: int,
        new_prices: List[ProductPrice],
    ) -> None:
        ...

    @abstractmethod
    async def refresh(
        self,
        product: Product,
        attribute_names: Optional[list] = None,
    ) -> None:
        ...